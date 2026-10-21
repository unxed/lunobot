#!/usr/bin/env python3
"""Кандидаты на закрытие по правилу двух недель (LUNOBOT.md § 4 п. 2а), только чтение.

Отбор делает скрипт по данным GitHub, а не воркер по памяти: берёт строки TRIAGE.md в
состоянии «проверяют»/«решён» и оставляет тикеты с меткой `bug`, у которых нет ни
одного комментария человека (не бот-аккаунт, не владелец репозитория) за последние
14 суток и есть комментарий с «Пробуйте!»/«Try it»/«Итог:», которому тоже не меньше 14 суток
(автору нужно время проверить; условие (а) п. 2а: без него
работа не объявлена завершённой — тикет-заметка владельца вроде «держим открытым для
мониторинга» иначе попадал в список на каждом круге). Запросы-возможности
(`enhancement`) и тикеты без метки `bug` не выводятся никогда. Вывод — только список
«может быть завершён»: завершена ли работа (влитый PR, нет незавершённых частей),
решает читающий тикет.

Использование:
    python3 tools/close_candidates.py f4 [--repo unxed/f4] [--days 14]

Коды возврата: 0 — отработал (список может быть пустым), 2 — ошибка запроса.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import check_try

ROOT = Path(__file__).resolve().parent.parent  # the clone of the accounting repository (the scripts are in tools/)
ROW = re.compile(
    r"^\|\s*(?P<number>\d+)\s*\|\s*(?P<priority>[^|]+?)\s*\|"
    r"\s*(?P<state>[^|]+?)\s*\|\s*(?P<comments>\d+)\s*\|"
    r"\s*(?P<updated>[^|]+?)\s*\|\s*$"
)
STATES = ("проверяют", "решён")


def api(path):
    """Все страницы через явный page=N (облачный прокси, § 13.2)."""
    items, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        r = subprocess.run(["gh", "api", f"{path}{sep}per_page=100&page={page}"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"gh api {path} page={page}: {r.stderr.strip()}")
        chunk = json.loads(r.stdout)
        items.extend(chunk)
        if len(chunk) < 100:
            return items
        page += 1


def parse_time(text):
    return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def triage_rows(project):
    rows = []
    for line in (ROOT / "projects" / project / "TRIAGE.md").read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m and m["state"] in STATES:
            rows.append(m.groupdict())
    return rows


def default_repo(project):
    text = (ROOT / "projects" / project / "PROJECT.md").read_text(encoding="utf-8")
    m = re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", text)
    return m.group(1) if m else f"unxed/{project}"


def candidates(rows, repo, days, now=None, bug_issues=None):
    """`bug_issues` — {номер: тикет} из одного списка открытых тикетов с меткой bug: строки вне него
    пропускаются без запроса (иначе по запросу на каждую строку TRIAGE, у f4 дольше 100 с)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    owner = repo.split("/")[0].lower()
    out, skipped = [], []
    for row in rows:
        n = int(row["number"])
        if bug_issues is not None and n not in bug_issues:
            skipped.append((n, "нет метки bug: нет среди открытых тикетов с этой меткой"))
            continue
        issue = bug_issues[n] if bug_issues is not None else api_issue(repo, n)
        labels = {l["name"] for l in issue["labels"]}
        if "bug" not in labels:
            skipped.append((n, "нет метки bug: " + (",".join(sorted(labels)) or "без меток")))
            continue
        comments = api(f"repos/{repo}/issues/{n}/comments")
        last_human = None
        author = issue["user"]
        if author["type"] != "Bot" and author["login"].lower() != owner:
            last_human = parse_time(issue["created_at"])  # текст тикета от человека — тоже сообщение
        last_any = parse_time(issue["created_at"])
        for c in comments:
            last_any = max(last_any, parse_time(c["created_at"]))
            user = c["user"]
            if user["type"] == "Bot" or user["login"].lower() == owner:
                continue
            t = parse_time(c["created_at"])
            if last_human is None or t > last_human:
                last_human = t
        if last_human is not None and (now - last_human).days < days:
            skipped.append((n, f"комментарий человека {last_human:%d-%m-%Y} моложе {days} суток"))
            continue
        tries = [parse_time(c["created_at"]) for c in comments if check_try.TRY.search(c.get("body") or "")]
        if not tries:
            skipped.append((n, "нет «Пробуйте!»/«Итог:»: завершение работы не подтверждено"))
            continue
        # Автору нужно время проверить: срок отсчитывается и от последнего «Пробуйте!»/«Итог:» (16-10-2026
        # f4#1792: исправление и «Пробуйте!» в тот же день, а сообщение автора старше 14 суток).
        if (now - max(tries)).days < days:
            skipped.append((n, f"«Пробуйте!»/«Итог:» от {max(tries):%d-%m-%Y} моложе {days} суток: автор ещё не успел проверить"))
            continue
        out.append((n, row["state"], last_human, last_any))
    return out, skipped


def api_issue(repo, n):
    r = subprocess.run(["gh", "api", f"repos/{repo}/issues/{n}"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"gh api issue {n}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("project")
    p.add_argument("--repo")
    p.add_argument("--days", type=int, default=14)
    a = p.parse_args(argv)
    repo = a.repo or default_repo(a.project)
    try:
        bugs = {i["number"]: i for i in api(f"repos/{repo}/issues?state=open&labels=bug")
                if "pull_request" not in i}
        out, skipped = candidates(triage_rows(a.project), repo, a.days, bug_issues=bugs)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2
    for n, why in skipped:
        print(f"пропущен {repo}#{n}: {why}")
    for n, state, last, last_any in out:
        since = f"последнее сообщение человека {last:%d-%m-%Y}" if last else "сообщений человека нет"
        print(f"кандидат {repo}#{n} ({state}): {since}, последний комментарий любого автора {last_any:%d-%m-%Y}; "
              "проверь, что работа завершена (влитый PR, нет незавершённых частей)")
    print(f"итого кандидатов: {len(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
