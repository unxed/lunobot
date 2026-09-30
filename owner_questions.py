#!/usr/bin/env python3
"""Вопросы владельцу: уведомление через единственный тикет «Вопросы владельцу».

Боты пишут в тикеты проектов от аккаунта владельца, а GitHub не уведомляет автора о
его собственных комментариях, поэтому вопрос владельцу там остаётся незамеченным.
Этот скрипт работает в Actions (GITHUB_TOKEN, github-actions[bot]) и оставляет в
одном постоянном тикете учётного репозитория комментарий с упоминанием @unxed и
ссылкой на сам вопрос. Комментарий — одна запись: `<!-- oq:<ссылка> -->` в первой строке.

    python3 owner_questions.py post --url <ссылка> --ticket <проект#N> --text <кратко>
    python3 owner_questions.py sweep [--dry-run]

post  — повторный вопрос по той же ссылке заменяет прежнюю запись (новый комментарий
        уведомляет снова); тикет создаётся, если его ещё нет.
sweep — периодическая уборка, единственный способ сократить список: убирает запись, только
        когда вопрос реально снят — тикет закрыт; после вопроса написал кто-то, кроме бота
        (подпись «*Лунобот-N (…)*» — бот, даже под аккаунтом владельца); в TRIAGE учётного
        репозитория состояние уже не «ждёт ответа»/«спор». Ни срока, ни лимита числа записей
        нет: неотвеченный вопрос не пропадает никогда. Приватные и недоступные тикеты не
        трогаются.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = "unxed"


MAX_TEXT = 400
REPORT_START = re.compile(
    r"^\W*(готов[оаы]?|сделан[оаы]?|обновлен[оаы]?|обновил[аи]?|исправлен[оаы]?|добавлен[оаы]?|"
    r"выполнен[оаы]?|закончен[оаы]?|завершен[оаы]?|залит[оаы]?|влит[оаы]?|итог|отчёт|отчет|"
    r"done|fixed|updated|added|finished|completed|ready)\s*([:.,!;\u2014\u2013-]|$)", re.IGNORECASE)
GATE_MESSAGE = (
    "в уведомления пишутся только вопросы к владельцу; отчёт оставь в учёте/тикете-источнике. "
    "Правило: --text непустой, не длиннее %d символов, один вопрос (ровно один «?», он последний "
    "символ), не начинается с отчёта («Готово:», «Сделано.», «Обновлено —», …)." % MAX_TEXT)


def check_question(text):
    """None, если text — вопрос, пригодный для уведомления владельца; иначе причина отказа."""
    text = " ".join((text or "").split())
    if not text:
        return "пустой текст"
    if len(text) > MAX_TEXT:
        return f"текст длиннее {MAX_TEXT} символов ({len(text)})"
    if REPORT_START.match(text):
        return "текст начинается как отчёт"
    bare = re.sub(r"https?://\S+", "", text).rstrip(" \t\"'»)]}*_")
    if not bare.endswith("?"):
        return "текст не заканчивается знаком «?»"
    if bare.count("?") != 1:
        return "в тексте не один вопрос (один вопрос — одно уведомление)"
    return None
TITLE = "Вопросы владельцу"
MARK = re.compile(r"<!--\s*oq:(\S+)\s*-->")
URL = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(?:issues|pull)/(\d+)(?:#issuecomment-(\d+))?")
BOT_SIGNATURE = re.compile(r"\*\s*(?:Лунобот|Lunobot)-\d+ \(")
WAITING = ("ждёт ответа", "спор")
DRY = "--dry-run" in sys.argv


def repo():
    return os.environ.get("GITHUB_REPOSITORY", "unxed/lunobot")


def gh(*args, check=True):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        if check:
            raise RuntimeError(f"gh {' '.join(args[:3])}: {out.stderr.strip()[:300]}")
        return None
    return out.stdout


def api_json(path, check=True):
    out = gh("api", "--paginate", "--slurp", path, check=check)
    if out is None:
        return None
    data = json.loads(out)
    if data and isinstance(data[0], list):
        return [item for page in data for item in page]
    return data


def find_issue(create):
    for issue in api_json(f"repos/{repo()}/issues?state=all&per_page=100&creator={OWNER}") or []:
        if issue.get("title") == TITLE and "pull_request" not in issue:
            if issue["state"] == "closed" and create and not DRY:
                gh("api", "-X", "PATCH", f"repos/{repo()}/issues/{issue['number']}", "-f", "state=open")
            return issue["number"]
    for issue in api_json(f"repos/{repo()}/issues?state=all&per_page=100") or []:
        if issue.get("title") == TITLE and "pull_request" not in issue:
            return issue["number"]
    if not create:
        return None
    body = ("Единственный тикет для вопросов владельцу: боты добавляют сюда комментарий со ссылкой на "
            "вопрос и упоминанием @" + OWNER + ", потому что GitHub не уведомляет о комментариях, оставленных "
            "от собственного аккаунта. Ответ пишите в самом тикете проекта по ссылке. Записи убирает "
            "`owner_questions.py sweep`, только когда вопрос снят (тикет закрыт, ответ дан, состояние в "
            "TRIAGE сменилось); срока и лимита нет. Держите тикет открытым.")
    out = gh("api", f"repos/{repo()}/issues", "-f", f"title={TITLE}", "-f", f"body={body}")
    return json.loads(out)["number"]


def entries(number):
    found = []
    for c in api_json(f"repos/{repo()}/issues/{number}/comments?per_page=100") or []:
        m = MARK.search(c.get("body") or "")
        if m:
            found.append({"id": c["id"], "url": m.group(1), "created": c["created_at"], "body": c["body"]})
    return found


def delete_comment(cid):
    print(f"убираю запись {cid}")
    if not DRY:
        gh("api", "-X", "DELETE", f"repos/{repo()}/issues/comments/{cid}", check=False)


def post(url, ticket, text):
    number = find_issue(create=True)
    for e in entries(number):
        if e["url"] == url:
            delete_comment(e["id"])
    text = " ".join(text.split())
    body = f"<!-- oq:{url} -->\n@{OWNER} вопрос владельцу — {ticket}: {text}\n\n{url}"
    print(f"тикет #{number}: новая запись по {url}")
    if not DRY:
        gh("api", f"repos/{repo()}/issues/{number}/comments", "-f", f"body={body}")


def triage_state(target_repo, num):
    """Состояние строки TRIAGE.md проекта, чей репозиторий target_repo; None — строки нет."""
    for project in (ROOT / "projects").glob("*/PROJECT.md"):
        if f"github.com/{target_repo}" not in project.read_text(encoding="utf-8", errors="ignore"):
            continue
        triage = project.parent / "TRIAGE.md"
        if not triage.exists():
            return None
        for line in triage.read_text(encoding="utf-8").splitlines():
            m = re.match(rf"\|\s*{num}\s*\|[^|]*\|\s*([^|]+?)\s*\|", line)
            if m:
                return m.group(1)
    return None


def obsolete(entry):
    """Причина убрать запись (вопрос снят) или None. Возраст записи причиной не бывает."""
    m = URL.search(entry["url"])
    if not m:
        return "ссылка не разобрана"
    target, num, cid = m.group(1), m.group(2), m.group(3)
    issue = api_json(f"repos/{target}/issues/{num}", check=False)
    if not isinstance(issue, dict):
        return None  # закрытый или недоступный репозиторий — не трогаем
    if issue.get("state") == "closed":
        return "тикет закрыт"
    for c in api_json(f"repos/{target}/issues/{num}/comments?per_page=100", check=False) or []:
        after = c["id"] > int(cid) if cid else c["created_at"] > entry["created"]
        if not after:
            continue
        if c["user"]["login"] != OWNER or not BOT_SIGNATURE.search(c.get("body") or ""):
            if c["user"]["login"] == OWNER or c["user"]["type"] != "Bot":
                return "владелец или человек ответил"
    state = triage_state(target, num)
    if state is not None and state not in WAITING:
        return f"в TRIAGE состояние «{state}»"
    return None


def sweep():
    number = find_issue(create=False)
    if number is None:
        print("тикета «Вопросы владельцу» ещё нет")
        return
    kept = []
    for e in entries(number):
        reason = obsolete(e)
        if reason:
            print(f"{e['url']}: {reason}")
            delete_comment(e["id"])
        else:
            kept.append(e)
    print(f"записей осталось: {len(kept)}")


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    opts = {}
    for i, a in enumerate(args):
        if a.startswith("--") and i + 1 < len(args):
            opts[a[2:]] = args[i + 1]
    if args and args[0] == "post":
        if not URL.search(opts.get("url", "")):
            print("нужна ссылка на вопрос: --url https://github.com/<владелец>/<репозиторий>/issues/N[#issuecomment-ID]")
            return 2
        reason = check_question(opts.get("text", ""))
        if reason:
            print(f"отклонено: {reason}. {GATE_MESSAGE}")
            return 2
        post(opts["url"], opts.get("ticket", ""), opts.get("text", ""))
        return 0
    if args and args[0] == "sweep":
        sweep()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
