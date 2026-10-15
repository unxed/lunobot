#!/usr/bin/env python3
"""Обновить строку тикета в TRIAGE.md по данным GitHub (§ 5.1).

После своего комментария в тикете число комментариев и updatedAt в строке
устаревают, и check_triage.py краснеет. Вместо правки `sed` — одна команда:

    python3 triage_touch.py f4 1729                  # комментарии и updatedAt с GitHub
    python3 triage_touch.py f4 1729 --state проверяют  # и состояние

Правит только файл `projects/<проект>/TRIAGE.md` в клоне, ничего не коммитит
и не пушит (коммит — `git add` этого файла по имени и `git commit`, § 8).
Приоритет не трогает (в том числе помеченный владельцем `2!`).
Коды возврата: 0 — строка обновлена или уже верна, 2 — ошибка.
"""
import re
import subprocess
import sys
from pathlib import Path

import check_triage

STATES = ("свободен", "ждёт ответа", "спор", "в пути", "проверяют", "решён")


def touch_row(text, number, comments, updated, state=None):
    """Вернуть (новый_текст, изменилась_ли_строка); строки других тикетов не меняются."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        match = check_triage.ROW.match(line)
        if not match or int(match.group("number")) != number:
            continue
        new = "| {} | {} | {} | {} | {} |".format(
            number, match.group("priority"), state or match.group("state"), comments, updated
        )
        lines[i] = new
        return "\n".join(lines), new != line
    raise ValueError(f"в TRIAGE нет строки тикета #{number}")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    state = None
    if "--state" in argv:
        state = argv[argv.index("--state") + 1]
        args.remove(state)
        if state not in STATES:
            raise ValueError("состояние должно быть одним из: " + ", ".join(STATES))
    if len(args) != 2 or not args[1].isdigit():
        raise ValueError("использование: triage_touch.py <проект> <номер> [--state <состояние>]")
    project, number = args[0], int(args[1])
    issue = check_triage.gh_one(f"/repos/{check_triage.repository(project, None)}/issues/{number}")
    path = check_triage.ROOT / "projects" / project / "TRIAGE.md"
    text, changed = touch_row(path.read_text(encoding="utf-8"), number, issue["comments"], issue["updated_at"], state)
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
