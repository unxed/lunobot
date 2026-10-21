#!/usr/bin/env python3
"""Гейт PR людей (§ 4 п. 2, § 6; модуль merge «PR людей»): кто ждёт нас. Только чтение.

    python3 check_prs.py <проект>

Строки вывода — работа уровня § 5 п. 3:
  [ждёт ответа] — автор PR (или другой человек) написал, ответил на ревью или запушил ПОСЛЕ нашего последнего
                  ответа: ответь по существу в этом же круге (влей, доработай, отзыв — модуль merge);
  [отстал от main] — все проверки PR зелёные, но ветка позади `main`: догнать `main` — наша работа, а не автора
                  (`update-branch` или sync-ветка `lunobot/urgent/<N>-sync`, модуль merge); просить автора обновить
                  ветку ещё раз нельзя;
  [запрет устарел] — PR из строки «PR не трогать» паспорта уже не открыт: убери строку из `PROJECT.md`.
Справочная строка (не работа, на код возврата не влияет):
  [не трогать] — владелец велел PR не трогать (строка `- PR не трогать: #N — <ссылка на слово владельца>` в
                  `projects/<проект>/PROJECT.md`); остальные строки по этому PR не печатаются.
Код 1 — есть строки работы (не повод останавливать круг), 0 — нет, 2 — ошибка доступа.

«Мы» — логин аккаунта `gh`, под которым пишут боты и владелец (`gh api user`), и коммиты с личностью бота
(`lunobot@users.noreply.github.com`, § 2), а не владелец репозитория из паспорта: у проекта с чужим upstream
(mcommander — blue-panels/mcommander) владелец репозитория — мейнтейнер upstream, то есть «люди».

Зачем: 20–21-10-2026 автор unxed/f4#2098 обновил ветку по просьбе бота и отписался, а бот почти сутки молчал —
гейт `check_triage.py` смотрит только тикеты, строки `CI.md` есть только у PR ботов, и ответ автора в PR не
был работой ни для одного шага. Тем временем `main` ушёл на 48 коммитов, и правило «вливать только не
отставшую ветку» снова требовало от автора обновления — порочный круг. Жалоба не первая.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BOTS = re.compile(r"\[bot\]$")
BOT_EMAIL = "lunobot@users.noreply.github.com"
HOLD = re.compile(r"^\s*-\s*PR не трогать:\s*#(\d+)\b(.*)$", re.M)


def api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"gh api {path}: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)


def passport(project):
    with open(os.path.join(HERE, "projects", project, "PROJECT.md"), encoding="utf-8") as f:
        return f.read()


def repo_of(text):
    """Первая ссылка на репозиторий в паспорте — там, где живут PR (mcommander: upstream)."""
    return re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", text).group(1)


def holds(text):
    """{номер PR: остаток строки со ссылкой на слово владельца} из строк «- PR не трогать: #N — …»."""
    return {int(n): rest.strip(" —-") for n, rest in HOLD.findall(text)}


def events(pr, comments, review_comments, reviews, commits, us):
    """[(ts, кто: «мы»|«люди»)] — мы: аккаунт `gh` ботов и владельца и коммиты с личностью бота; боты-сервисы не
    считаются."""
    out = []
    for c in comments + review_comments:
        login = c["user"]["login"]
        if BOTS.search(login):
            continue
        out.append((c["created_at"], "мы" if login == us else "люди"))
    for r in reviews:
        if r.get("submitted_at") and not BOTS.search(r["user"]["login"]):
            out.append((r["submitted_at"], "мы" if r["user"]["login"] == us else "люди"))
    for c in commits:
        author = (c.get("author") or {}).get("login") or ""
        email = ((c.get("commit") or {}).get("author") or {}).get("email") or ""
        if author == us or email == BOT_EMAIL:
            out.append((c["commit"]["committer"]["date"], "мы"))
        elif author:
            out.append((c["commit"]["committer"]["date"], "люди"))
    out.append((pr["created_at"], "люди"))
    return sorted(out)


def waiting(evs):
    """Ts последнего события людей после нашего последнего ответа, иначе None."""
    ours = max((t for t, who in evs if who == "мы"), default="")
    theirs = max((t for t, who in evs if who == "люди"), default="")
    return theirs if theirs > ours else None


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    try:
        text = passport(argv[0])
        repo = repo_of(text)
        held = holds(text)
        us = api("user")["login"]
        all_open = api(f"repos/{repo}/pulls?state=open&per_page=100")
        prs = [p for p in all_open if not p["head"]["ref"].startswith("lunobot/") and not p.get("draft")]
        found = 0
        now = datetime.now(timezone.utc)
        open_numbers = {p["number"] for p in all_open}
        for n in sorted(set(held) - open_numbers):
            print(f"[запрет устарел] {repo}#{n} не открыт — убери строку «PR не трогать: #{n}» из "
                  f"projects/{argv[0]}/PROJECT.md")
            found += 1
        for p in prs:
            n = p["number"]
            if n in held:
                print(f"[не трогать] {repo}#{n} — слово владельца: {held[n] or 'ссылки нет'}")
                continue
            evs = events(p, api(f"repos/{repo}/issues/{n}/comments?per_page=100"),
                         api(f"repos/{repo}/pulls/{n}/comments?per_page=100"),
                         api(f"repos/{repo}/pulls/{n}/reviews?per_page=100"),
                         api(f"repos/{repo}/pulls/{n}/commits?per_page=100"), us)
            ts = waiting(evs)
            if ts:
                h = (now - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds() / 3600
                print(f"[ждёт ответа] {repo}#{n} «{p['title'][:60]}» — люди писали/пушили {ts} ({h:.0f} ч назад) "
                      "после нашего последнего ответа")
                found += 1
            head = p["head"]["sha"]
            runs = api(f"repos/{repo}/commits/{head}/check-runs?per_page=100")["check_runs"]
            if runs and all(r["status"] == "completed" and r["conclusion"] in ("success", "skipped", "neutral")
                            for r in runs):
                behind = api(f"repos/{repo}/compare/{p['base']['ref']}...{head}")["behind_by"]
                if behind:
                    print(f"[отстал от main] {repo}#{n} — проверки зелёные, позади `{p['base']['ref']}` на {behind}: "
                          f"догнать сами (update-branch или sync-ветка `lunobot/urgent/{n}-sync`, модуль merge), "
                          "автора не просить")
                    found += 1
        print(f"PR людей: {len(prs)}, строк: {found}")
        return 1 if found else 0
    except (RuntimeError, OSError, KeyError, ValueError, AttributeError) as e:
        print(f"check_prs: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
