#!/usr/bin/env python3
"""Уведомить владельца о вопросе в тикете проекта.

Боты пишут от аккаунта владельца, поэтому GitHub его о вопросе не уведомляет. Скрипт
запускает workflow `owner-question` учётного репозитория (github-actions[bot] оставляет в
тикете «Вопросы владельцу» комментарий с @unxed и ссылкой на вопрос).

    python3 notify_owner.py <ссылка на комментарий-вопрос> [--ticket unxed/f4#410] --text "<один вопрос, до 400 символов, заканчивается «?»>" [--repo unxed/lunobot]

Ссылка — на сам комментарий с вопросом (`https://github.com/unxed/f4/issues/410#issuecomment-…`).
Гейт: в уведомления пишутся только вопросы (`owner_questions.check_question`); иначе код 2 и
ничего не отправляется. Повторный вызов с той же ссылкой заменяет запись. Записи убирает scheduled-проход
`owner-question-sweep` (ответ, закрытие тикета, снятие `ждёт ответа`, срок).
"""
import re
import subprocess
import sys

from owner_questions import GATE_MESSAGE, check_question


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--") or not re.match(r"https://github\.com/[\w.-]+/[\w.-]+/(issues|pull)/\d+", args[0]):
        print(__doc__)
        return 2
    url, opts = args[0], {}
    for i, a in enumerate(args[1:], 1):
        if a.startswith("--") and i + 1 < len(args):
            opts[a[2:]] = args[i + 1]
    reason = check_question(opts.get("text", ""))
    if reason:
        print(f"отклонено: {reason}. {GATE_MESSAGE}", file=sys.stderr)
        return 2
    ticket = opts.get("ticket") or "/".join(url.split("/")[3:5]) + "#" + url.split("/")[6].split("#")[0]
    repo = opts.get("repo", "unxed/lunobot")
    cmd = ["gh", "workflow", "run", "owner-question.yml", "-R", repo,
           "-f", f"url={url}", "-f", f"ticket={ticket}", "-f", f"text={opts.get('text', '')}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "GraphQL" in (result.stderr or ""):
        # Облачные сессии закрывают GraphQL, а `gh workflow run` его просит (ищет ветку по умолчанию):
        # тот же запуск через REST, ветку называем сами.
        cmd = ["gh", "api", "-X", "POST", f"repos/{repo}/actions/workflows/owner-question.yml/dispatches",
               "-f", "ref=main", "-f", f"inputs[url]={url}", "-f", f"inputs[ticket]={ticket}",
               "-f", f"inputs[text]={opts.get('text', '')}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
    print((result.stdout or result.stderr or "отправлено").strip())
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
