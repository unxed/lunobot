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

После перевода учёта на ref (`claims.py migrate --apply`) `add|remove projects/<p>/DISPATCH.md`
делегируется в `claims.py`: «взял …» — take, «работаю над …» — keepalive, remove — drop своего.
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
LEGACY_BRANCH_DATE = re.compile(r"\d\d-\d\d-\d{4} (?:Лунобот|Lunobot)-\d+[^\n]*?, ветка ")
RECORD_FILES = ("DISPATCH.md", "CI.md", "BRANCHES.md")


def remove_line(text, key, records_only=False, remove_all=False, legacy_branch_records=False):
    """Новый текст без единственной строки с key; None — такой строки нет; ValueError — их несколько.
    records_only: искать только среди записей с меткой времени, чтобы ключ не снёс шапку файла.
    legacy_branch_records: также разрешает старые BRANCHES-записи с датой без времени.
    remove_all: убрать все строки с key одним проходом (пять строк прогонов одного main — один коммит)."""
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines)
            if key in l and (not records_only or RECORD.match(l)
                             or (legacy_branch_records and LEGACY_BRANCH_DATE.match(l)))]
    if not hits:
        return None
    if len(hits) > 1 and not remove_all:
        raise ValueError(f"подстрока {key!r} есть в {len(hits)} строках — уточни ключ или добавь --all")
    for i in reversed(hits):
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


def unrecorded_hits(text, key):
    """Номера строк (с 1) с key, которые не запись с меткой времени и не заголовок: remove их не снимает (records_only),
    а «нет строки» при этом вводит в заблуждение (круг 19-10-2026: строка CI.md с меткой без секунд)."""
    return [i + 1 for i, l in enumerate(text.split("\n"))
            if key in l and l.strip() and not l.startswith("#") and not RECORD.match(l)]


def attempt(repo, remote, branch, op, relpath, arg, message, sign, remove_all=False):
    git(repo, "fetch", "-q", remote, branch)
    base = git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()
    old = git(repo, "show", f"{base}:{relpath}", check=False)
    if old.returncode:
        raise RuntimeError(f"{relpath} нет в {remote}/{branch}")
    added = None
    if op == "add":
        if os.path.basename(relpath) in RECORD_FILES:
            import check_dispatch
            if "\n" in arg.strip("\n") or not check_dispatch.is_record_line(arg.strip("\n")):
                print(f"ОТКАЗ: запись {os.path.basename(relpath)} — ровно одна строка, начинающаяся с метки времени "
                      f"ДД-ММ-ГГГГ ЧЧ:ММ:СС (§ 8); получено: {arg[:80]!r}. Ключ или обрывок текста сюда не пишут.")
                return "gate"
        new = add_paragraph(old.stdout, arg)
        added = len(new.rstrip("\n").split("\n"))
    else:
        new = remove_line(old.stdout, arg, os.path.basename(relpath) in RECORD_FILES, remove_all,
                          legacy_branch_records=os.path.basename(relpath) == "BRANCHES.md")
        if new is None:
            print(f"в {relpath} нет строки с {arg!r} — удалять нечего")
            if os.path.basename(relpath) in RECORD_FILES:
                bad = unrecorded_hits(old.stdout, arg)
                if bad:
                    print(f"ВНИМАНИЕ: ключ есть в строках {bad}, но они без метки ДД-ММ-ГГГГ ЧЧ:ММ:СС — это не запись, "
                          f"remove их не трогает. Убери строку правкой файла и `git commit` (после — `check_ci.py`/`check_dispatch.py`).")
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


def claims_route(repo, remote, branch, op, relpath, text, sign, remove_all):
    """DISPATCH.md после перевода учёта на ref (claims.py): захват — ref, а не строка файла.
    None — учёт ещё на файлах, работать по-старому; иначе код возврата."""
    m = re.fullmatch(r"projects/([^/]+)/DISPATCH\.md", relpath)
    if not m:
        return None
    import claims
    claims.fetch(repo, remote)
    if not claims.refs(repo):
        git(repo, "fetch", "-q", remote, branch, check=False)
        cur = git(repo, "show", f"FETCH_HEAD:{relpath}", check=False)
        if cur.returncode or claims.MARKER not in cur.stdout:
            return None
    project = m.group(1)
    if op == "remove":
        code = claims.drop(repo, project, text, sign, remote, remove_all)
        return 0 if code in (0, claims.NOTHING) else code
    if ", работаю над " in text:
        key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", text) or re.search(r"«([^»]+)»", text)
        needle = key.group(1) if key and key.re.groups else (key.group(0) if key else text)
        return claims.keepalive(repo, project, needle, sign, remote)
    return claims.take(repo, project, text, remote)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("op", choices=["add", "remove"])
    ap.add_argument("file", help="путь от корня учётного репозитория")
    ap.add_argument("text", help="add: строка целиком; remove: подстрока-ключ (несколько строк — с --all)")
    ap.add_argument("--all", action="store_true", help="remove: убрать все строки с ключом одним коммитом")
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--sign", required=True, help="id инстанса, как в подписи (§ 1)")
    ap.add_argument("--repo", default=HERE, help="клон учёта (по умолчанию каталог скрипта)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="main")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"(?:Лунобот|Lunobot)-\d+ \(node [0-9a-f]{24}; (?:MSW|LNX|DAR|BSD)\)", a.sign):
        print("--sign: нужен полный id с номером, 24-значным узлом и платформой, например «Лунобот-1 (node a721a6d1487257292ae00780; LNX)»", file=sys.stderr)
        return 2
    relpath = a.file.replace("\\", "/")
    try:
        routed = claims_route(a.repo, a.remote, a.branch, a.op, relpath, a.text, a.sign, a.all)
        if routed is not None:
            return routed
        for _ in range(3):
            r = attempt(a.repo, a.remote, a.branch, a.op, relpath, a.text, a.message, a.sign, a.all)
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
