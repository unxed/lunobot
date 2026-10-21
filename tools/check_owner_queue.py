#!/usr/bin/env python3
"""Линтер OWNER_QUEUE.md.

Файл читают первой операцией каждого круга (§ 4 п. 1, § 8), но формата у него не
защищал ни один гейт: 15-10-2026 бот дописал строку прогресса в начало файла без
перевода строки, и заголовок `# Очередь поручений владельца` оказался хвостом этой
строки. Файл так и пролежал около 12 часов, через него прошло несколько кругов, и
ни один не заметил, что шапки (со строкой `Автор доверенных тикетов`, от которой
зависит исполнение тикетов) в начале файла нет.

Проверки (структура, а не содержание заметок: свободные заметки владельца — любой
текст):
1. Первая строка файла — ровно `# Очередь поручений владельца`.
2. Строка `Автор доверенных тикетов: <login>` есть ровно один раз и стоит до первой
   строки-разделителя `--`.
3. Идентификатор блока `## <id>` не повторяется.
4. В файле нет символа CR (только LF, § 3 п. 11) и U+FFFD.
5. В блоке `## <id>` не больше одной строки следа (`Прогресс`/`Доп. проверка`/`Доп. шаг`): файл — рабочий
   блокнот, история поручения — комментариями в его тикете (решение владельца 21-10-2026: к тому дню журналы
   прогресса раздули файл до 52 КБ, 25 из них — в двух блоках).

Состав полей блока намеренно не проверяется: формальные блоки старого образца
(`Адресат:`, без `Заметка владельца:`/`Критерий:`) в истории файла встречаются, и
проверка полей давала ложные срабатывания на 31 из 200 его версий.

Использование:
    python3 tools/check_owner_queue.py [путь к OWNER_QUEUE.md]

Коды возврата: 0 — нарушений нет, 1 — есть, 2 — файл не найден.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the clone of the accounting repository (the scripts are in tools/)
TITLE = "# Очередь поручений владельца"
TRACE = re.compile(r"^(Прогресс|Доп\. проверка|Доп\. шаг)\b")
AUTHOR = re.compile(r"^Автор доверенных тикетов:\s*\S+")


def check(text):
    """Возвращает список описаний нарушений (пустой — всё в порядке)."""
    problems = []
    if "\r" in text:
        problems.append("в файле есть CR: допустим только LF")
    if "�" in text:
        problems.append("в файле есть U+FFFD: текст испорчен кодировкой")
    lines = text.split("\n")
    if not lines or lines[0] != TITLE:
        problems.append(
            f"строка 1 должна быть ровно «{TITLE}», а там: «{(lines[0] if lines else '')[:60]}»"
        )

    first_sep = next((i for i, l in enumerate(lines) if l == "--"), len(lines))
    authors = [i for i, l in enumerate(lines) if AUTHOR.match(l)]
    if len(authors) != 1:
        problems.append(f"строка «Автор доверенных тикетов: <login>» нужна ровно одна, найдено {len(authors)}")
    elif authors[0] > first_sep:
        problems.append("«Автор доверенных тикетов» стоит после первого разделителя `--`, а должен быть в шапке")

    seen, block, traces = {}, None, {}
    for i, line in enumerate(lines):
        if line.startswith("## "):
            name = line[3:].strip()
            if name in seen:
                problems.append(f"блок «{name}» (строка {i + 1}) повторяет блок со строки {seen[name] + 1}")
            seen[name] = i
            block = name
        elif line == "--":
            block = None
        elif block and TRACE.match(line):
            traces[block] = traces.get(block, 0) + 1
    for name, n in traces.items():
        if n > 1:
            problems.append(f"в блоке «{name}» {n} строк следа (Прогресс/Доп.): оставь одну последнюю, "
                            "историю — комментарием в тикете поручения (§ 8, модуль round)")
    return problems


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "OWNER_QUEUE.md"
    if not path.is_file():
        print(f"нет файла: {path}", file=sys.stderr)
        return 2
    with open(path, encoding="utf-8", newline="") as fh:
        problems = check(fh.read())
    for p in problems:
        print(f"[OWNER_QUEUE] {p}")
    print(f"{path.name}: нарушений {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
