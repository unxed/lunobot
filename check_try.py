#!/usr/bin/env python3
"""Проверка: у тикета в состоянии «проверяют» есть «Пробуйте!».

Состояние `проверяют` (§ 5.1) значит «последнее сообщение — «Пробуйте!»».
Откат коммита из staging, ручная правка или сбой разноса (§ 7.2 п. 4) оставляют
тикет в этом состоянии без единого «Пробуйте!»: автор ничего не знает, а бот
считает работу сданной (16-10-2026: f4#1783 и f4#1792 так простояли неделю после
влития исправления в main). Скрипт только читает GitHub.

Использование:
    python3 check_try.py <проект> [--repo owner/repo]

Коды возврата: 0 — у каждого тикета `проверяют` есть «Пробуйте!», 1 — есть
тикеты без него (список в выводе), 2 — не удалось проверить.
"""
import json
import re
import sys

import check_triage

# «Пробуйте!» (не в кавычках «…»: так он назван в комментарии «войдёт в main со следующим
# поездом; «Пробуйте!» будет отдельным», § 9 — это обещание, а не разнос), английские
# «Try it»/«Please try …» (язык комментария — язык автора, § 9) и «Итог:» — итог вместо
# «Пробуйте!», который § 4 п. 2а считает завершением работы.
TRY = re.compile(r"(?<![«\"])пробуйте!|проверяем!|\btry it\b|\bplease try\b|^\s*итог:",
                 re.IGNORECASE | re.MULTILINE)


def tickets_without_try(rows, fetch_comments):
    """Номера тикетов `проверяют`, в комментариях которых нет «Пробуйте!»."""
    missing = []
    for number in sorted(rows):
        if rows[number]["state"] != "проверяют":
            continue
        if not any(TRY.search(c.get("body") or "") for c in fetch_comments(number)):
            missing.append(number)
    return missing


def main():
    positional = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    project = positional[0] if positional else "f4"
    explicit = sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else None
    repo = check_triage.repository(project, explicit)
    rows, _ = check_triage.read_triage(project)
    missing = tickets_without_try(
        rows, lambda n: check_triage.gh_pages(f"/repos/{repo}/issues/{n}/comments?per_page=100"))
    print(f"{project}: тикетов `проверяют` {sum(1 for r in rows.values() if r['state'] == 'проверяют')}, без «Пробуйте!» {len(missing)}")
    for number in missing:
        print(f"[нет «Пробуйте!»] {repo}#{number}: исправлено ли в main? да — разнеси «Пробуйте!» (§ 7.2 п. 4); нет — верни `свободен`")
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"проверить «Пробуйте!» не удалось: {error}", file=sys.stderr)
        sys.exit(2)
