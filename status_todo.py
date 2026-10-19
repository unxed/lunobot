#!/usr/bin/env python3
"""Исполнимый остаток многошаговых тикетов: что осталось в `projects/<проект>/status/<N>.md`.

§ 5 п. 5 отправляет на тикеты в состоянии `свободен`, но многошаговая работа живёт в status-файлах,
в разделах «Осталось» / «Дальше» (§ 5.1, правило многочастных тикетов), а большинство этих разделов
— «Ничего обязательного». Скрипт читает только файлы клона (сети нет) и печатает по каждому
status-файлу с исполнимым остатком: тикет, приоритет и состояние из `TRIAGE.md`, первую строку остатка.

Использование:
    python3 status_todo.py <проект>
    python3 status_todo.py --all

Пропускаются: остаток, начинающийся с «Ничего обязательного» / «Ничего исполнимого» /
«Исполнимых частей нет» / «необязательно», раздел с пометкой «после ответа автора» / «только после
файлов» / «до ответа не брать»; последний остаток, ждущий рутину («после освобождения слота», «часть N
приземлена … попадёт в main через поезд»), заменяется остатком первой секции; тикеты в состояниях `ждёт ответа` и `спор`; тикеты, которых нет
в `TRIAGE.md` (закрыты); тикеты, занятые в `DISPATCH.md` проекта; сделанные пункты (`✓`,
«(сделано …)») в начале списка. Порядок вывода: приоритет (меньше — раньше), проект, номер.

Коды возврата: 0 — проверка выполнена (в том числе когда печатать нечего), 2 — не удалось
(нет проекта, нет TRIAGE.md, неверные аргументы).
"""
import re
import sys
from pathlib import Path

import check_dispatch
import check_triage

ROOT = Path(__file__).resolve().parent
WIDTH = 160
SKIP_STATES = ("ждёт ответа", "спор")
HEADING = re.compile(r"^(?:#{1,6}\s*)?(Осталось|Дальше)\b(?:/(?:Осталось|Дальше)\b)?(.*)$")
NEXT_HEADING = re.compile(r"^#{1,6}\s")
MARKER = re.compile(r"^(?:\d+[а-яa-z]?[.)]|[-*•])\s+")
# Раздел или остаток без исполнимой части либо с условием, которого ещё нет. Заголовок проверяется
# по вхождению («Осталось (после ответа автора; до ответа не брать)»), первая строка остатка — по
# началу (середина длинной строки не повод пропускать часть). Всё строчными: сравнение через lower().
NOT_EXECUTABLE = (
    "ничего обязательного", "ничего исполнимого", "исполнимых частей нет", "необязательн",
    "после ответа автора", "только после файлов", "до ответа не брать",
)
NOT_EXECUTABLE_START = re.compile(
    r"^[\s`«\"'*_]*(?:ничего|нечего|планового остатка нет|закрывающих частей нет|исполнимых частей нет"
    r"|ждём|только при желании|только по желанию|по желанию автора|необязательн|после ответа автора"
    r"|только после файлов|до ответа не брать"
    # «Пробуйте!» и «после поезда» — рутина § 7.2 п. 4, а не часть работы
    r"|пробуйте!|после (?:зел[её]ного |влития )?поезда)")


# Последний остаток — ожидание рутины § 7.2/§ 7.3 (свободный слот CI, поезд), а не работа: он ничего не
# говорит о частях тикета, поэтому остаток берётся из первой («общей») секции status-файла, а не пропадает
# и не подменяет её. «Ничего обязательного» и прочие NOT_EXECUTABLE_START сюда не относятся: они закрывают тикет.
ROUTINE_WAIT_START = re.compile(
    r"^[\s`«\"'*_]*(?:после освобождения (?:общего |свободного )?слота"
    r"|часть\s+\S+\s+приземлена\b[^.;]*;\s*(?:она|оно)\s+попад[её]т\s+в\s+main)")


def is_done(item):
    """Пункт уже сделан: `✓` в начале или «(сделано …)»."""
    return "✓" in item[:10] or bool(re.match(r"[(~]*\s*сделано", item, re.IGNORECASE))


def sections(text):
    """[(строка заголовка, [строки раздела])] для каждого «Осталось»/«Дальше» в тексте."""
    lines = text.splitlines()
    found = []
    for index, line in enumerate(lines):
        match = HEADING.match(line.strip())
        if not match:
            continue
        body = []
        inline = match.group(2).strip()
        # «Осталось: текст» — остаток в той же строке; «Осталось (условие):» — только условие
        colon = re.match(r"^(?:\([^)]*\)\s*)?:\s*(.*)$", inline)
        if colon and colon.group(1).strip():
            body.append(colon.group(1).strip())
        for follow in lines[index + 1:]:
            if NEXT_HEADING.match(follow):
                break
            body.append(follow)
        found.append((line.strip(), body))
    return found


def first_item(body):
    """Первая строка остатка без маркера списка, пропуская пустые и сделанные пункты; None — пусто."""
    for line in body:
        item = MARKER.sub("", line.strip(), count=1).strip()
        if item and not is_done(item):
            return item
    return None


def executable_item(heading, body):
    """(строка остатка или None, рутина ли ожидания) для одной секции «Осталось»/«Дальше»."""
    item = first_item(body)
    if item is None:
        return None, False
    if any(phrase in heading.lower() for phrase in NOT_EXECUTABLE) or NOT_EXECUTABLE_START.match(item.lower()):
        return None, False
    return item, bool(ROUTINE_WAIT_START.match(item.lower()))


# Последняя запись status-файла — датированный абзац, который в конце закрывает тикет:
# «18-10-2026 15:18 UTC (…): … Осталось: ничего по коду; …». Заголовком секции такая строка не
# считается (середина строки), и более ранний «Осталось: …» оставался бы в списке (unxed/zipper#32).
DATED_CLOSING = re.compile(r"^\d{2}-\d{2}-\d{4}\b.*\b(?:Осталось|Дальше)\b\s*:\s*(.*)$")


def closed_by_last_entry(text):
    """Последняя непустая строка — датированная запись с «Осталось: ничего …» (не исполнимый остаток)."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    match = DATED_CLOSING.match(lines[-1]) if lines else None
    if not match:
        return False
    item, _ = executable_item("Осталось", [match.group(1)])
    return item is None


def remainder(text):
    """Первая строка исполнимого остатка status-файла или None (нет раздела / нечего делать).

    Берётся последняя секция; если она лишь ждёт рутину (свободный слот CI, поезд — ROUTINE_WAIT_START),
    остаток читается из первой секции (unxed/dn#80, unxed/f4#1998). Датированная последняя запись
    «… Осталось: ничего …» закрывает остаток целиком."""
    if closed_by_last_entry(text):
        return None
    found = sections(text)
    if not found:
        return None
    item, waiting = executable_item(*found[-1])
    if waiting:
        item, _ = executable_item(*found[0]) if len(found) > 1 else (None, False)
    return item


def short(text, width=WIDTH):
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width - 1].rstrip() + "…"


def priority_key(value):
    match = re.match(r"\d+", value)
    return int(match.group(0)) if match else 99


def occupied(project):
    """Ссылки `владелец/репозиторий#N` из DISPATCH.md проекта (в файле только действующие захваты)."""
    path = ROOT / "projects" / project / "DISPATCH.md"
    if not path.exists():
        return set()
    found = set()
    for entry in check_dispatch.parse(str(path))[0]:
        if entry["verb"] in check_dispatch.LIVE:
            found |= entry["refs"]
    return found


def project_names():
    return sorted(p.name for p in (ROOT / "projects").iterdir() if (p / "TRIAGE.md").exists())


def todo(project):
    """[(приоритет, проект, номер, ссылка, состояние, строка остатка)] одного проекта."""
    rows, _ = check_triage.read_triage(project)
    try:
        repo = check_triage.repository(project, None)
    except RuntimeError:
        repo = project
    busy = occupied(project)
    result = []
    status_dir = ROOT / "projects" / project / "status"
    for path in sorted(status_dir.glob("*.md")) if status_dir.is_dir() else []:
        if not path.stem.isdigit():
            continue  # status без номера тикета (задача учёта, не тикет проекта)
        number = int(path.stem)
        row = rows.get(number)
        if row is None or row["state"] in SKIP_STATES or f"{repo}#{number}".lower() in busy:
            continue
        item = remainder(path.read_text(encoding="utf-8"))
        if item is not None:
            result.append((priority_key(row["priority"]), project, number, f"{repo}#{number}",
                           f"{row['priority']}, {row['state']}", item))
    return result


def main(argv):
    args = [a for a in argv if a != "--all"]
    if len(args) + (1 if "--all" in argv else 0) != 1 or any(a.startswith("-") for a in args):
        print(__doc__.split("Использование:")[1].split("Пропускаются")[0].strip(), file=sys.stderr)
        return 2
    names = project_names() if "--all" in argv else args
    items = []
    for name in names:
        if not (ROOT / "projects" / name / "TRIAGE.md").exists():
            print(f"нет projects/{name}/TRIAGE.md", file=sys.stderr)
            return 2
        items += todo(name)
    for _, _, _, ref, state, item in sorted(items):
        print(f"{ref} [{state}] {short(item)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
