#!/usr/bin/env python3
"""Линтер DISPATCH.md.

Файл протокола содержит только действующие захваты (§ 14.1 инструкции). Проверяется
формат строк, отсутствие записей о законченной работе, повторные захваты одного шага,
keepalive без захвата и протухшие захваты.

Использование:
    python3 check_dispatch.py projects/f4/DISPATCH.md [--timeout-min 45] [--since ДД-ММ-ГГГГ]

Коды возврата: 0 — нарушений нет, 1 — есть.
"""
import re
import sys
from datetime import datetime, timedelta

TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
ID = r"Я Лунобот-(?P<num>\d+) \((?:instance|node) (?P<node>[0-9a-f]{6,24}); (?P<plt>[A-Z]{3})\)"
LIVE = ("взял", "работаю")
CLOSED = ("закончил", "освобождаю", "разблокировано по таймауту")
FINAL = ("считаю цель", "прекращаю работу")


def parse(path):
    entries, malformed = [], []
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
            custom = re.search(r"кастомную задачу,\s*([^(]+)", body)
            key = custom.group(1).strip() if custom else None
        part = re.search(r"\(часть (\d+) из (\d+)\)", line)
        if not (ts and who and verb and key and part):
            malformed.append((n, line[:110], {
                "нет метки времени": not ts,
                "id не по формату": not who,
                "нет глагола состояния": not verb,
                "нет ключа задачи": not key,
                "не указана часть": not part,
            }))
            continue
        entries.append({"line": n, "ts": datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S"),
                        "who": who.group(0), "verb": verb,
                        "key": f"{key}#{part.group(1)}/{part.group(2)}"})
    return entries, malformed


def check(path, timeout_min, since=None):
    entries, malformed = parse(path)
    if since:
        entries = [e for e in entries if e["ts"] >= since]
        kept = []
        for n, text, flags in malformed:
            m = re.match(r"(\d{2}-\d{2}-\d{4})", text)
            if m and datetime.strptime(m.group(1), "%d-%m-%Y") < since:
                continue
            kept.append((n, text, flags))
        malformed = kept

    problems = []
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


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "DISPATCH.md"
    timeout = 45
    if "--timeout-min" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout-min") + 1])
    since = None
    if "--since" in sys.argv:
        since = datetime.strptime(sys.argv[sys.argv.index("--since") + 1], "%d-%m-%Y")
    entries, problems = check(path, timeout, since)
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
