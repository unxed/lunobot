#!/usr/bin/env python3
"""Линтер DISPATCH.md.

Файл протокола содержит только действующие захваты (§ 14.1 инструкции). Проверяется
формат строк, отсутствие записей о законченной работе, повторные захваты одного шага,
keepalive без захвата и протухшие захваты.

Использование:
    python3 check_dispatch.py projects/f4/DISPATCH.md [--timeout-min 45] [--since ДД-ММ-ГГГГ]
    python3 check_dispatch.py projects/f4/DISPATCH.md --added-only [--base <коммит>]

`--added-only` оставляет только претензии к строкам, добавленным последним коммитом.
Так проверка отвечает на вопрос «правильно ли записал именно ты», а не «какое сейчас
состояние флота»: состояние почти всегда ненулевое, и гейт из него горел бы всегда.

Коды возврата: 0 — нарушений нет, 1 — есть.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
ID = r"Я Лунобот-(?P<num>\d+) \((?:instance|node) (?P<node>[0-9a-f]{6,24}); (?P<plt>[A-Z]{3})\)"
LIVE = ("взял", "работаю")
CLOSED = ("закончил", "освобождаю", "разблокировано по таймауту")
FINAL = ("считаю цель", "прекращаю работу")


def parse(path):
    entries, malformed, no_origin = [], [], []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip()
        if "Лунобот" not in line:
            continue
        if any(f in line for f in FINAL):
            continue  # записи о завершении сессии — законное исключение
        ts, who = re.match(TS, line), re.search(ID, line)
        verb = next((v for v in LIVE + CLOSED if v in line), None)
        body = re.sub(r"\]\(https?://[^)]+\)", "]", line)
        key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", body)
        if key:
            key = key.group(0)
        else:
            # «взял кастомную задачу «X»» и «работаю над кастомной задачей «X»» — один шаг
            custom = re.search(r"кастомн\w+ задач\w+\s*«([^»]+)»", body)
            if not custom:
                custom = re.search(r"кастомную задачу,\s*([^(]+)", body)
            key = custom.group(1).strip() if custom else None
            if key and "взял" in line and "по §" not in body:
                no_origin.append((n, line[:110]))
        part = re.search(r"\(часть (\d+) из (\d+)\)", line)
        if not (ts and who and verb and key):
            malformed.append((n, line[:110], {
                "нет метки времени": not ts,
                "id не по формату": not who,
                "нет глагола состояния": not verb,
                "нет ключа задачи": not key,
                "не указана часть": not part,
            }))
            continue
        # часть не указана — значит единственная
        part_key = f"{part.group(1)}/{part.group(2)}" if part else "1/1"
        entries.append({"line": n, "ts": datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S"),
                        "who": who.group(0), "verb": verb, "key": f"{key}#{part_key}"})
    return entries, malformed, no_origin


def check(path, timeout_min, since=None):
    entries, malformed, no_origin = parse(path)
    if since:
        entries = [e for e in entries if e["ts"] >= since]
        def fresh(text):
            m = re.match(r"(\d{2}-\d{2}-\d{4})", text)
            return not (m and datetime.strptime(m.group(1), "%d-%m-%Y") < since)
        malformed = [x for x in malformed if fresh(x[1])]
        no_origin = [x for x in no_origin if fresh(x[1])]

    problems = []
    for n, text in no_origin:
        problems.append(("нет повода", n,
                         "кастомная задача без указания, откуда взялась "
                         f"(нужно «по § …»): {text}"))
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if len(re.findall(TS, line)) > 1:
            if since:
                m = re.match(r"(\d{2}-\d{2}-\d{4})", line)
                if m and datetime.strptime(m.group(1), "%d-%m-%Y") < since:
                    continue
            problems.append(("слиплось", n,
                             "в одной строке несколько записей — между ними нужна пустая строка"))
    for n, text, flags in malformed:
        problems.append(("формат", n, ", ".join(k for k, v in flags.items() if v) + f": {text}"))

    holders = {}
    for e in entries:
        if e["verb"] in CLOSED:
            problems.append(("мусор", e["line"],
                             f"«{e['verb']}» — записей о законченном в файле быть не должно, "
                             f"строки по закрытому шагу удаляются: {e['key']}"))
            continue
        prev = holders.get(e["key"])
        if e["verb"] == "взял" and prev and prev["who"] != e["who"]:
            problems.append(("гонка", e["line"],
                             f"{e['key']} уже захвачен другим (строка {prev['line']})"))
        if e["verb"] == "работаю" and not prev:
            problems.append(("состояние", e["line"], f"keepalive без захвата: {e['key']}"))
        if not prev or e["ts"] >= prev["ts"]:
            holders[e["key"]] = e

    if entries:
        now = max(e["ts"] for e in entries)
        for key, h in holders.items():
            age = now - h["ts"]
            if age > timedelta(minutes=timeout_min):
                problems.append(("протух", h["line"],
                                 f"{key} держится {int(age.total_seconds() // 60)} мин без отметки"))
    return entries, problems


def added_lines(path, base=None):
    """Номера строк, добавленных последним коммитом."""
    import subprocess
    base = base or "HEAD~1"
    try:
        diff = subprocess.run(["git", "diff", "--unified=0", base, "HEAD", "--", path],
                              capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    lines, cur = set(), 0
    for l in diff.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", l)
        if m:
            cur = int(m.group(1))
            continue
        if l.startswith("+") and not l.startswith("+++"):
            lines.add(cur)
            cur += 1
        elif not l.startswith("-"):
            cur += 1
    return lines


def wrong_place(path):
    """Проверяет, что файл учёта — тот самый, а не одноимённый в чужом репозитории.

    Живой случай: бот вёл учёт в клоне проекта, в DISPATCH.md в его корне. Записи
    делались исправно и коммитились, но пульт и линтер читают учётный репозиторий,
    поэтому инстанса не было видно пять часов. Ни одна проверка формата такого не
    ловит: содержимое файла было безупречным, неверным было его место.
    """
    real = os.path.abspath(path)
    if os.sep + "projects" + os.sep not in real:
        return (f"файл учёта должен лежать в projects/<проект>/, а лежит здесь: {real}. "
                "Похоже, это клон проекта, а не учётного репозитория")
    try:
        origin = subprocess.run(
            ["git", "-C", os.path.dirname(real) or ".", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return None  # не в git — не наше дело, формат проверим как обычно
    if origin and "lunobot" not in origin:
        return (f"учёт ведётся в чужом репозитории: origin = {origin}. "
                "Записи туда никто не читает — пиши в клон unxed/lunobot")
    return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "DISPATCH.md"
    if misplaced := wrong_place(path):
        print(f"НЕ ТОТ РЕПОЗИТОРИЙ: {misplaced}")
        return 1
    timeout = 45
    if "--timeout-min" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout-min") + 1])
    since = None
    if "--since" in sys.argv:
        since = datetime.strptime(sys.argv[sys.argv.index("--since") + 1], "%d-%m-%Y")
    entries, problems = check(path, timeout, since)
    if "--added-only" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
        added = added_lines(path, base)
        if added is not None:
            # протухшие захваты — состояние, а не ошибка записи: в гейт не попадают
            problems = [p for p in problems if p[1] in added and p[0] != "протух"]
    print(f"действующих записей разобрано: {len(entries)}")
    if not problems:
        print("нарушений нет")
        return 0
    by_kind = {}
    for kind, line, msg in problems:
        by_kind.setdefault(kind, []).append((line, msg))
    for kind in sorted(by_kind, key=lambda k: -len(by_kind[k])):
        items = by_kind[kind]
        print(f"\n[{kind}] {len(items)}")
        for line, msg in items[:8]:
            print(f"  строка {line}: {msg}")
        if len(items) > 8:
            print(f"  ... ещё {len(items) - 8}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # вывод обрезан через | head
        sys.exit(0)
