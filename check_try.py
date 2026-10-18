#!/usr/bin/env python3
"""Проверка: у тикета в состоянии «проверяют» есть «Пробуйте!».

Состояние `проверяют` (§ 5.1) значит «последнее сообщение — «Пробуйте!»».
Откат коммита из staging, ручная правка или сбой разноса (§ 7.2 п. 4) оставляют
тикет в этом состоянии без единого «Пробуйте!»: автор ничего не знает, а бот
считает работу сданной (16-10-2026: f4#1783 и f4#1792 так простояли неделю после
влития исправления в main). Скрипт только читает GitHub.

Использование:
    python3 check_try.py <проект> [--repo owner/repo]

Вторая проверка — «Пробуйте!», обещанное раньше времени: в комментарии названа
ссылка или sha коммита, которого нет в `main` (поезд не влит) или нет вовсе. 16-10-2026
на f4#1976 «Пробуйте!» вышло на коммит из staging с чужим sha (`9effe76` — это другая
правка): автор проверил сборку без исправления и ответил, что не работает. Смотрятся
тикеты, обновлённые за последние трое суток, в любом состоянии, кроме `в пути`
(именно в него тикет и возвращают).

Коды возврата: 0 — всё в порядке, 1 — есть тикеты `проверяют` без «Пробуйте!» или
«Пробуйте!» на коммит вне `main` (список в выводе), 2 — не удалось проверить.
"""
import datetime
import json
import re
import sys

import check_triage

# «Пробуйте!» (не в кавычках «…»: так он назван в комментарии «войдёт в main со следующим
# поездом; «Пробуйте!» будет отдельным», § 9 — это обещание, а не разнос), английские
# «Try it»/«Please try …» (язык комментария — язык автора, § 9) и «Итог:» — итог вместо
# «Пробуйте!», который § 4 п. 2а считает завершением работы.
TRY = re.compile(r"(?<![«\"])пробуйте!|проверяем!|\btry it\b|\bplease try\b|^\s*итог:",
                 re.IGNORECASE | re.MULTILINE)


def tickets_without_try(rows, fetch_comments):
    """Номера тикетов `проверяют`, в комментариях которых нет «Пробуйте!»."""
    missing = []
    for number in sorted(rows):
        if rows[number]["state"] != "проверяют":
            continue
        if not any(TRY.search(c.get("body") or "") for c in fetch_comments(number)):
            missing.append(number)
    return missing


# sha коммита в тексте — только ссылка …/commit/<sha>: так бот называет коммит с исправлением.
# Голые hex-слова и sha в обратных кавычках не берём: id узла в подписи (24 hex), версия сборки
# автора («Version: 44c61e9») и числа дали бы ложные срабатывания на реальных тикетах.
COMMIT_REF = re.compile(r"(?:github\.com/([\w.-]+/[\w.-]+))?/commit/([0-9a-f]{7,40})\b")
RECENT_DAYS = 3


def commit_refs(body, repo=None):
    """sha коммитов, названных в тексте комментария.

    Если задан repo, ссылки на коммиты других репозиториев (…/unxed/wayland/commit/…: исправление
    лежит в зависимости, у которой своя ветка и свои сообщения) пропускаются: их нельзя проверить
    по main и сообщениям этого репозитория, а запрос к нему дал бы «такого коммита нет».
    """
    return [sha for owner_repo, sha in COMMIT_REF.findall(body or "")
            if not (repo and owner_repo and owner_repo.lower() != repo.lower())]


def premature_tries(rows, fetch_comments, in_main, about=None, now=None, days=RECENT_DAYS, repo=None):
    """[(номер, sha, причина)]: «Пробуйте!» последних дней на коммит, который не тот или не в `main`.

    in_main(sha) -> True / False / None (None — такого коммита в репозитории нет);
    about(sha, номер) -> True / False: в сообщении коммита назван этот тикет. Проверка срабатывает,
    только если тикет не назван ни в одном из коммитов комментария (шаг из нескольких коммитов
    называет их все, тикет — в одном).
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    found = []
    for number in sorted(rows):
        updated = datetime.datetime.fromisoformat(rows[number]["updated"].replace("Z", "+00:00"))
        if now - updated > datetime.timedelta(days=days) or rows[number]["state"] == "в пути":
            continue  # `в пути` — уже исправленное состояние: «Пробуйте!» ждёт влития поезда
        tries = [c for c in fetch_comments(number) if TRY.search(c.get("body") or "")]
        if not tries:
            continue
        shas = list(dict.fromkeys(commit_refs(tries[-1].get("body"), repo)))
        states = {sha: in_main(sha) for sha in shas}
        broken = False
        for sha in shas:
            if states[sha] is None:
                found.append((number, sha, "такого коммита нет в репозитории"))
                broken = True
            elif not states[sha]:
                found.append((number, sha, "коммит ещё не в main"))
                broken = True
        # Шаг из двух коммитов (первый — «данные» с `Lunobot-Task:`, второй — с `Touch: #N`)
        # легитимно называет оба. Чужой sha (f4#1976) — когда тикет не назван НИ В ОДНОМ из
        # коммитов комментария; ошибки «нет в main» выше важнее и этой проверки не требуют.
        if about is None or broken:
            continue
        if shas and not any(about(sha, number) for sha in shas):
            found.extend((number, sha, "ни в одном из названных коммитов нет этого тикета (чужой коммит?)")
                         for sha in shas)
    return found


def commit_mentions_ticket(message, repo, number):
    """В сообщении коммита назван тикет: `Touch: #N`, `owner/repo#N`, `#N` или ссылка …/issues/N."""
    pattern = rf"(?<![\w/]){re.escape(repo)}#{number}\b|(?<![\w/])#{number}\b|/issues/{number}\b"
    return bool(re.search(pattern, message or ""))


def commit_in_main(repo, sha):
    """True — коммит достижим из main или его PR влит в main, False — нет, None — коммита нет (404).

    Проекты со squash/rebase-мержем (dn, tv3, bp) не содержат head-sha влитого PR среди предков
    main, поэтому «не предок» проверяется ещё и влитым в main PR этого коммита.
    """
    try:
        data = check_triage.gh_one(f"/repos/{repo}/compare/{sha}...main")
    except RuntimeError as error:
        if "404" in str(error) or "No commit found" in str(error) or "Not Found" in str(error):
            return None
        raise
    # compare/<sha>...main описывает main относительно sha: «ahead» — main впереди, то есть
    # sha — предок main.
    if data.get("status") in ("ahead", "identical"):
        return True
    pulls = check_triage.gh_one(f"/repos/{repo}/commits/{sha}/pulls")
    return any(p.get("merged_at") and p.get("base", {}).get("ref") == "main" for p in pulls)


def main():
    positional = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    project = positional[0] if positional else "f4"
    explicit = sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else None
    repo = check_triage.repository(project, explicit)
    rows, _ = check_triage.read_triage(project)
    missing = tickets_without_try(
        rows, lambda n: check_triage.gh_pages(f"/repos/{repo}/issues/{n}/comments?per_page=100"))
    print(f"{project}: тикетов `проверяют` {sum(1 for r in rows.values() if r['state'] == 'проверяют')}, без «Пробуйте!» {len(missing)}")
    for number in missing:
        print(f"[нет «Пробуйте!»] {repo}#{number}: исправлено ли в main? да — разнеси «Пробуйте!» (§ 7.2 п. 4); нет — верни `свободен`")
    premature = premature_tries(
        rows, lambda n: check_triage.gh_pages(f"/repos/{repo}/issues/{n}/comments?per_page=100"),
        lambda sha: commit_in_main(repo, sha),
        lambda sha, number: commit_mentions_ticket(
            check_triage.gh_one(f"/repos/{repo}/commits/{sha}")["commit"]["message"], repo, number),
        repo=repo)
    for number, sha, reason in premature:
        print(f"[преждевременное «Пробуйте!»] {repo}#{number}: коммит {sha} — {reason}; "
              "верни `в пути` и поправь комментарий (§ 9), «Пробуйте!» — только когда исправление уже в main")
    return 1 if missing or premature else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"проверить «Пробуйте!» не удалось: {error}", file=sys.stderr)
        sys.exit(2)
