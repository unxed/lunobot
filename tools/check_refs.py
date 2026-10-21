#!/usr/bin/env python3
"""Гейт ссылок на параграфы инструкции в шапках учётных файлов.

Шапки `DISPATCH.md`/`CI.md`/`BRANCHES.md` проектов ссылаются на `§ N` или `§ N.M`
инструкции. Если такого раздела в `LUNOBOT.md` нет, ссылка ведёт в никуда
(14-10-2026 девятнадцать шапок отсылали к несуществующим § 14.1/§ 14.2/§ 14.3 —
формат записей описан в § 8). Проверяются только первые HEAD_LINES строк каждого файла:
записи ниже шапки ссылки на разделы могут нести как угодно.

    python3 tools/check_refs.py              # все projects/*/{DISPATCH,CI,BRANCHES}.md
    python3 tools/check_refs.py <файл>...    # только указанные

Код возврата 1 — есть ссылка на несуществующий раздел.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))  # tools/: the scripts
ROOT = os.path.dirname(HERE)  # the clone of the accounting repository
HEAD_LINES = 6
REF = re.compile(r"§\s*(\d+(?:\.\d+)?)")
SECTION = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)?)\.?\s", re.M)


def sections(text):
    return set(SECTION.findall(text))


def check(path, known):
    problems = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if n > HEAD_LINES:
                break
            for ref in REF.findall(line):
                if ref not in known:
                    problems.append((n, ref))
    return problems


def main(argv):
    known = set()
    # разделы живут в ядре и в модулях (modules/*.md, решение 21-10-2026 — EVOLUTION.md)
    for doc in [os.path.join(ROOT, "LUNOBOT.md")] + sorted(glob.glob(os.path.join(ROOT, "modules", "*.md"))):
        with open(doc, encoding="utf-8") as f:
            known |= sections(f.read())
    files = argv or sorted(
        p for name in ("DISPATCH", "CI", "BRANCHES")
        for p in glob.glob(os.path.join(ROOT, "projects", "*", name + ".md")))
    bad = 0
    for path in files:
        for n, ref in check(path, known):
            print(f"{os.path.relpath(path, ROOT)}:{n}: ссылка на несуществующий раздел § {ref}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
