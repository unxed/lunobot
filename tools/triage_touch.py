#!/usr/bin/env python3
"""Обновить строку тикета в TRIAGE.md по данным GitHub (§ 5.1).

После своего комментария в тикете число комментариев и updatedAt в строке
устаревают, и check_triage.py краснеет. Вместо правки `sed` — одна команда:

    python3 tools/triage_touch.py f4 1729                  # комментарии и updatedAt с GitHub
    python3 tools/triage_touch.py f4 1729 --state проверяют  # и состояние
    python3 tools/triage_touch.py f4 1960 --priority 3     # новая строка для тикета, которого в TRIAGE ещё нет

Правит только файл `projects/<проект>/TRIAGE.md` в клоне, ничего не коммитит
и не пушит (коммит — `git add` этого файла по имени и `git commit`, § 8).
Приоритет существующей строки не трогает (в том числе помеченный владельцем `2!`);
`--priority N` (1-5) нужен только для тикета без строки (например, заведённого самим
ботом): строка добавляется в конец таблицы, состояние по умолчанию — `свободен`.
Коды возврата: 0 — строка обновлена или уже верна, 2 — ошибка.
"""
import re
import subprocess
import sys
from pathlib import Path

import check_triage

STATES = ("свободен", "ждёт ответа", "спор", "в пути", "проверяют", "решён")


def touch_row(text, number, comments, updated, state=None, priority=None):
    """Вернуть (новый_текст, изменилась_ли_строка); строки других тикетов не меняются.

    Тикета нет в таблице: с `priority` строка добавляется после последней строки данных
    (в пустой таблице - после шапки), без него - ошибка."""
    lines = text.split("\n")
    last = -1
    head = -1
    for i, line in enumerate(lines):
        match = check_triage.ROW.match(line)
        if match:
            last = i
        elif line.startswith("|"):
            head = i
        if not match or int(match.group("number")) != number:
            continue
        new = "| {} | {} | {} | {} | {} |".format(
            number, match.group("priority"), state or match.group("state"), comments, updated
        )
        lines[i] = new
        return "\n".join(lines), new != line
    if last < 0:
        last = head
    if priority is None or last < 0:
        raise ValueError(f"в TRIAGE нет строки тикета #{number}" + ("" if priority is not None else " (новая строка: --priority N)"))
    lines.insert(last + 1, f"| {number} | {priority} | {state or 'свободен'} | {comments} | {updated} |")
    return "\n".join(lines), True


def main(argv):
    args = list(argv)
    state = None
    if "--state" in args:
        at = args.index("--state")
        if at + 1 >= len(args):
            raise ValueError("после --state нужно состояние: " + ", ".join(STATES))
        state = args[at + 1]
        del args[at : at + 2]
        if state not in STATES:
            raise ValueError("состояние должно быть одним из: " + ", ".join(STATES))
    priority = None
    if "--priority" in args:
        at = args.index("--priority")
        if at + 1 >= len(args) or args[at + 1] not in ("1", "2", "3", "4", "5"):
            raise ValueError("после --priority нужна цифра 1-5")
        priority = args[at + 1]
        del args[at : at + 2]
    if any(a.startswith("--") for a in args):
        raise ValueError("неизвестный параметр: " + next(a for a in args if a.startswith("--")))
    if len(args) != 2 or not args[1].isdigit():
        raise ValueError("использование: triage_touch.py <проект> <номер> [--state <состояние>] [--priority N]")
    project, number = args[0], int(args[1])
    issue = check_triage.gh_one(f"/repos/{check_triage.repository(project, None)}/issues/{number}")
    path = check_triage.ROOT / "projects" / project / "TRIAGE.md"
    text, changed = touch_row(path.read_text(encoding="utf-8"), number, issue["comments"], issue["updated_at"], state, priority)
    if changed:
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"#{number}: комментариев {issue['comments']}, updatedAt {issue['updated_at']}" + ("" if changed else " (без изменений)"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"triage_touch: {error}", file=sys.stderr)
        sys.exit(2)
