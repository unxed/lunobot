#!/usr/bin/env python3
"""Линтер CI.md.

Файл — очередь передачи PR, ждущих результата прогона (§ 8 инструкции): одна строка
на PR/прогон. У DISPATCH.md формат защищает `check_dispatch.py` — у CI.md аналогичного
гейта не было вообще, и минимум два субагента подряд, независимо друг от друга,
переписали `CI.md` в свой произвольный scratch-формат (markdown-заголовки вида
«# zipper #17 - CI tracking» с bullet-list вместо простых временных строк), разрушив
структуру файла, и ни одна проверка перед пушем это не поймала. Этот гейт — прямой
ответ на тот инцидент.

В отличие от DISPATCH.md, запись CI.md — ровно одна строка (не абзац из нескольких
строк): разбор реальных `projects/*/CI.md` показал, что записи разделены пустой
строкой, как в DISPATCH.md, но каждая запись сама по себе всегда одна физическая
строка, без переноса. Тело записи (что после метки времени) в реальной практике
свободный текст — не жёсткая схема «PR, коммит, прогон» из примера § 8: строки
CI.md описывают и ожидание прогона, и находки по PR, и перебазирование веток. Поэтому
этот гейт проверяет структуру файла (заголовок, метки времени, отсутствие
markdown-заголовков и списков — см. ниже), а не содержимое отдельной записи.

Проверки:
1. Первая строка файла — заголовок `# CI — <проект>`, не тронутый.
2. Каждая непустая строка данных начинается с метки времени `ДД-ММ-ГГГГ ЧЧ:ММ:СС`
   (как в DISPATCH.md). Преамбула до первой такой строки (пояснительный абзац под
   заголовком) в счёт не идёт; но после первой валидной записи любая непустая строка
   без метки времени — нарушение формата.
3. Никаких markdown-заголовков (`#`, `##` и т. п.) в теле файла, кроме самой первой
   строки файла.
4. Никаких маркеров списка (`-`, `*` в начале строки) — CI.md это временные строки,
   не список.
5. Между двумя записями данных обязана быть пустая строка (иначе они «слиплись» —
   как в check_dispatch.py).

Использование:
    python3 check_ci.py <проект>
    python3 check_ci.py projects/<проект>/CI.md

Коды возврата: 0 — нарушений нет, 1 — есть, 2 — файл не найден/аргумент не указан.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TS = re.compile(r"^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\b")
HEADER = re.compile(r"^#{1,6}\s")
BULLET = re.compile(r"^\s*[-*]\s")


def resolve_path(arg):
    """Bare имя проекта или путь к файлу — как у check_triage.py/check_branches.py
    (принимают имя проекта) и check_dispatch.py (принимает путь) одновременно."""
    p = Path(arg)
    if p.suffix.lower() == ".md" or "/" in arg or "\\" in arg:
        return p
    return ROOT / "projects" / arg / "CI.md"


def project_name_from_path(path):
    path = Path(path).resolve()
    if path.parent.parent.name == "projects":
        return path.parent.name
    return None


def check(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    problems = []
    data_count = 0
    in_data = False
    project = project_name_from_path(path)

    for n, line in enumerate(lines, 1):
        if n == 1:
            expected = f"# CI — {project}" if project else None
            if not HEADER.match(line):
                problems.append(("заголовок", n,
                                 f"первая строка файла должна быть заголовком "
                                 f"«# CI — <проект>»: {line!r}"))
            elif expected and line != expected:
                problems.append(("заголовок", n,
                                 f"заголовок не совпадает с ожидаемым «{expected}»: {line!r}"))
            continue

        if not line.strip():
            continue  # пустая строка — разделитель записей, это ожидаемо

        if HEADER.match(line):
            problems.append(("markdown-заголовок", n,
                             f"markdown-заголовок внутри файла — заголовок допустим только "
                             f"на первой строке: {line!r}"))
            continue

        if BULLET.match(line):
            problems.append(("bullet-list", n,
                             f"маркер списка в начале строки — CI.md это временные строки, "
                             f"не список: {line!r}"))
            continue

        if not TS.match(line):
            if in_data:
                problems.append(("формат", n,
                                 f"строка после начала записей без метки времени в начале "
                                 f"(ДД-ММ-ГГГГ ЧЧ:ММ:СС): {line!r}"))
            # до первой валидной записи — это преамбула/пояснение под заголовком, не ошибка
            continue

        # валидная строка данных
        if in_data and n >= 2 and lines[n - 2].strip():
            problems.append(("слиплось", n,
                             "между записями нужна пустая строка — эта прилипла к предыдущей"))
        in_data = True
        data_count += 1

    return data_count, problems


def main():
    if len(sys.argv) < 2:
        print("использование: python3 check_ci.py <проект> | projects/<проект>/CI.md",
              file=sys.stderr)
        return 2
    path = resolve_path(sys.argv[1])
    if not path.exists():
        print(f"файл не найден: {path}", file=sys.stderr)
        return 2

    data_count, problems = check(path)
    print(f"записей данных разобрано: {data_count}")
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
