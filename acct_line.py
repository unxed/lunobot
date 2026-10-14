#!/usr/bin/env python3
"""Одна строка учёта без конфликтов rebase (§ 8).

    python3 acct_line.py add    projects/f4/DISPATCH.md "<строка>"   -m "<сообщение>" --sign "<id>"
    python3 acct_line.py remove projects/f4/DISPATCH.md "<подстрока>" -m "<сообщение>" --sign "<id>"

Берёт файл из свежего origin/main (не из рабочей копии), добавляет абзац в конец файла или
удаляет единственную строку с подстрокой-ключом, проверяет добавленную строку гейтом
(`check_dispatch.py` для DISPATCH.md, `check_ci.py` для CI.md), собирает коммит только с этим
файлом и трейлером `Lunobot-Instance:` поверх origin/main и пушит; гонка — заново с fetch,
до 3 попыток. Рабочая копия и индекс клона не трогаются, поэтому конфликтов rebase нет
(14-10-2026: за один круг пять ручных «возьми origin и внеси строку заново»).
Коды: 0 — запушено (или удалять нечего), 1 — гейт или пуш не прошли, 2 — ошибка вызова.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def git(repo, *args, data=None, env=None, check=True):
    # байты, а не text=True: в текстовом режиме stdin переводит "\n" в os.linesep, и в Windows
    # в blob учётного файла ушли бы CRLF (§ 3 п. 11: только LF)
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=env,
                       input=None if data is None else data.encode("utf-8"))
    r.stdout = r.stdout.decode("utf-8")
    r.stderr = r.stderr.decode("utf-8", "replace")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def add_paragraph(text, line):
    body = text.rstrip("\n")
    return (body + "\n\n" if body else "") + line.strip("\n") + "\n"


RECORD = re.compile(r"\d\d-\d\d-\d{4} \d\d:\d\d:\d\d ")
RECORD_FILES = ("DISPATCH.md", "CI.md", "BRANCHES.md")


def remove_line(text, key, records_only=False):
    """Новый текст без единственной строки с key; None — такой строки нет; ValueError — их несколько.
    records_only: искать только среди записей с меткой времени, чтобы ключ не снёс шапку файла."""
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines)
            if key in l and (not records_only or RECORD.match(l))]
    if not hits:
        return None
    if len(hits) > 1:
        raise ValueError(f"подстрока {key!r} есть в {len(hits)} строках — уточни ключ")
    i = hits[0]
    del lines[i]
    # строка была абзацем: убрать лишнюю пустую строку, чтобы не осталось двух подряд
    if i < len(lines) and lines[i] == "" and (i == 0 or lines[i - 1] == ""):
        del lines[i]
    elif i == len(lines) and i > 0 and lines[i - 1] == "":
        del lines[i - 1]
    return "\n".join(lines)


def gate(relpath, text, added_line_no):
    """Претензии гейта к добавленной строке (номер с 1) или пустой список."""
    name = os.path.basename(relpath)
    if name not in ("DISPATCH.md", "CI.md") or added_line_no is None:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        if name == "DISPATCH.md":
            import check_dispatch
            _, problems = check_dispatch.check(path, 45)
            problems = [p for p in problems if p[0] != "протух"]
        else:
            import check_ci
            _, problems = check_ci.check(path)
    return [p for p in problems if p[1] == added_line_no]


def attempt(repo, remote, branch, op, relpath, arg, message, sign):
    git(repo, "fetch", "-q", remote, branch)
    base = git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()
    old = git(repo, "show", f"{base}:{relpath}", check=False)
    if old.returncode:
        raise RuntimeError(f"{relpath} нет в {remote}/{branch}")
    added = None
    if op == "add":
        new = add_paragraph(old.stdout, arg)
        added = len(new.rstrip("\n").split("\n"))
    else:
        new = remove_line(old.stdout, arg, os.path.basename(relpath) in RECORD_FILES)
        if new is None:
            print(f"в {relpath} нет строки с {arg!r} — удалять нечего")
            return "noop"
    problems = gate(relpath, new, added)
    if problems:
        for kind, n, msg in problems:
            print(f"ГЕЙТ [{kind}] строка {n}: {msg}")
        return "gate"
    blob = git(repo, "hash-object", "-w", "--stdin", data=new).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        git(repo, "read-tree", base, env=env)
        git(repo, "update-index", "--cacheinfo", f"100644,{blob},{relpath}", env=env)
        tree = git(repo, "write-tree", env=env).stdout.strip()
    msg = f"{message}\n\nLunobot-Instance: {sign}\n"
    commit = git(repo, "commit-tree", tree, "-p", base, data=msg).stdout.strip()
    push = git(repo, "push", "-q", remote, f"{commit}:refs/heads/{branch}", check=False)
    if push.returncode:
        print(f"пуш отклонён (гонка?): {push.stderr.strip()}")
        return "race"
    print(f"запушено {commit[:7]} в {remote}/{branch}: {message}")
    # рабочая копия на этой ветке и чистая — подтянуть её, иначе оставить как есть
    head = git(repo, "symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.strip()
    if head == branch and not git(repo, "status", "--porcelain", "-uno").stdout.strip():
        git(repo, "fetch", "-q", remote, branch, check=False)
        git(repo, "merge", "-q", "--ff-only", commit, check=False)
    return "ok"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("op", choices=["add", "remove"])
    ap.add_argument("file", help="путь от корня учётного репозитория")
    ap.add_argument("text", help="add: строка целиком; remove: подстрока-ключ")
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--sign", required=True, help="id инстанса, как в подписи (§ 1)")
    ap.add_argument("--repo", default=HERE, help="клон учёта (по умолчанию каталог скрипта)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="main")
    a = ap.parse_args(argv)
    if "(node " not in a.sign:
        print("--sign: нужен полный id с узлом, например «Лунобот-1 (node …; LNX)»", file=sys.stderr)
        return 2
    relpath = a.file.replace("\\", "/")
    try:
        for _ in range(3):
            r = attempt(a.repo, a.remote, a.branch, a.op, relpath, a.text, a.message, a.sign)
            if r in ("ok", "noop"):
                return 0
            if r == "gate":
                return 1
    except (RuntimeError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    print("пуш не прошёл за 3 попытки — повтори позже", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
