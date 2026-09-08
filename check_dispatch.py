#!/usr/bin/env python3
"""Линтер DISPATCH.md.

Проверяет ровно то, что можно проверить механически: формат записей, парность
захватов и завершений, отсутствие двойных закрытий, просроченные захваты.

Использование:
    python3 check_dispatch.py projects/f4/DISPATCH.md [--timeout-min 45]

Коды возврата: 0 — нарушений нет, 1 — есть.
"""
import re
import sys
from datetime import datetime, timedelta

TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
ID = r"Я Лунобот-(?P<num>\d+) \(instance (?P<inst>[0-9a-f]{6,24}); (?P<plt>[A-Z]{3})\)"
VERBS = ("взял", "закончил", "освобождаю", "разблокировано по таймауту", "работаю")


def parse(path):
    entries, malformed = [], []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip()
        if "Лунобот" not in line:
            continue
        ts = re.match(TS, line)
        who = re.search(ID, line)
        verb = next((v for v in VERBS if v in line), None)
        # ссылка-цель markdown-ссылки (например в «[закончил](...PR)») ключом не является:
        # ключ шага — тот, по которому он был захвачен
        body = re.sub(r"\]\(https?://[^)]+\)", "]", line)
        key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", body)
        if not key:
            custom = re.search(r"кастомную задачу,\s*([^(]+)", body)
            key = custom.group(1).strip() if custom else None
        else:
            key = key.group(0)
        part = re.search(r"\(часть (\d+) из (\d+)\)", line)
        if not (ts and who and verb and key):
            malformed.append((n, line[:110], {
                "нет метки времени": not ts,
                "id не по формату": not who,
                "нет глагола состояния": not verb,
                "нет ключа задачи": not key,
            }))
            continue
        entries.append({
            "line": n,
            "ts": datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S"),
            "who": who.group(0),
            "verb": verb,
            "key": key + (f"#{part.group(1)}/{part.group(2)}" if part else ""),
        })
    return entries, malformed


def check(path, timeout_min):
    entries, malformed = parse(path)
    problems = []

    for n, text, flags in malformed:
        why = ", ".join(k for k, v in flags.items() if v)
        problems.append(("формат", n, f"{why}: {text}"))

    state = {}
    for e in entries:
        st = state.get(e["key"])
        if e["verb"] == "взял":
            if st and st["verb"] in ("взял", "работаю"):
                problems.append(("гонка", e["line"],
                                 f"повторный захват {e['key']}, прошлый не закрыт "
                                 f"(строка {st['line']})"))
            state[e["key"]] = e
        elif e["verb"] == "работаю":
            if not st or st["verb"] not in ("взял", "работаю"):
                problems.append(("состояние", e["line"],
                                 f"keepalive по незахваченному шагу {e['key']}"))
            else:
                state[e["key"]] = e
        else:  # закончил / освобождаю / разблокировано
            if not st:
                problems.append(("состояние", e["line"],
                                 f"«{e['verb']}» без парного «взял»: {e['key']}"))
            elif st["verb"] == "закончил":
                problems.append(("двойное закрытие", e["line"],
                                 f"{e['key']} уже закрыт в строке {st['line']}"))
            elif e["verb"] == "закончил" and st["who"] != e["who"]:
                problems.append(("изоляция", e["line"],
                                 f"{e['key']} закрывает не тот, кто брал (строка {st['line']})"))
            state[e["key"]] = e

    if entries:
        now = max(e["ts"] for e in entries)
        for key, st in state.items():
            if st["verb"] in ("взял", "работаю"):
                age = now - st["ts"]
                if age > timedelta(minutes=timeout_min):
                    problems.append(("протух", st["line"],
                                     f"{key} захвачен {int(age.total_seconds() // 60)} мин назад "
                                     f"и не закрыт"))

    return entries, problems


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "DISPATCH.md"
    timeout = 45
    if "--timeout-min" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout-min") + 1])
    entries, problems = check(path, timeout)
    print(f"разобрано корректных записей: {len(entries)}")
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
    sys.exit(main())
