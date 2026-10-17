#!/usr/bin/env python3
"""Метки времени «ДД-ММ-ГГГГ ЧЧ:ММ[:СС] UTC» в записях status/*.md не должны быть позже текущего UTC.

Метку берут из `date -u` в момент записи, а не «на глаз» (§ 8): запись с 14:40, сделанная в 14:30,
сдвигает хронологию и ломает проверки возраста. Для DISPATCH.md то же ловит check_dispatch.py
(ошибка «время»); status-файлы раньше не проверял никто.

  check_status_times.py              только строки, добавленные последним коммитом (как --added-only у check_dispatch.py)
  check_status_times.py --all        все строки всех projects/*/status/*.md
Код возврата 1 — есть метка позже текущего UTC (допуск 60 с на разницу часов).
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAMP = re.compile(r"\b(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2})(?::(\d{2}))?\s+UTC\b")
SLACK = timedelta(seconds=60)


def future_stamps(text: str, now: datetime) -> list[str]:
    """Метки из text, которые позже now (+ допуск)."""
    result = []
    for match in STAMP.finditer(text):
        day, month, year, hour, minute, second = match.groups()
        try:
            stamp = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second or 0), tzinfo=timezone.utc)
        except ValueError:
            continue
        if stamp > now + SLACK:
            result.append(match.group(0))
    return result


def added_lines(root: Path) -> list[tuple[str, str]]:
    """(файл, строка) для строк status/*.md, добавленных последним коммитом."""
    diff = subprocess.run(
        ["git", "-C", str(root), "diff", "--unified=0", "HEAD~1", "HEAD", "--", "projects/*/status/*.md"],
        capture_output=True, text=True, check=True).stdout
    lines, current = [], ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            lines.append((current, line[1:]))
    return lines


def main() -> int:
    root = Path(__file__).resolve().parent
    now = datetime.now(timezone.utc)
    if "--all" in sys.argv[1:]:
        lines = [(str(path.relative_to(root)), line)
                 for path in sorted(root.glob("projects/*/status/*.md"))
                 for line in path.read_text(encoding="utf-8").splitlines()]
    else:
        lines = added_lines(root)
    bad = 0
    for name, line in lines:
        for stamp in future_stamps(line, now):
            print(f"ГЕЙТ [время] {name}: метка {stamp} позже текущего UTC {now:%d-%m-%Y %H:%M:%S}: {line[:90]}")
            bad += 1
    print(f"проверено строк: {len(lines)}, меток из будущего: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
