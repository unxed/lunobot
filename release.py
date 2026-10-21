#!/usr/bin/env python3
"""Снять все захваты своего id одним коммитом (§ 1, § 11, § 13.2 «Срок процесса под раннером»).

    python3 release.py --number <N> [--reason "<причина>"] [--dry-run]

Раннер (`runners/lunobot-round*.sh`) вызывает его после каждого круга и при остановке (Ctrl+C,
SIGTERM): круг — это сессия, и после неё в учёте не остаётся захватов. Незаконченный шаг живёт не
в захвате и не в /tmp, а в запушенной ветке и `status/<N>.md` (§ 7.5) — его подхватит любой бот.
До этого скрипта убитый раннер оставлял захваты висеть до `janitor.py` (до 240 минут, пока узел
жив: живость он считал по узлу, а на узле работал второй раннер).

Снимает:
  refs/claims/*/*        — все захваты id «Лунобот-<N> (node <узел>; …)», с суффиксом воркера и без
                           (одним атомарным пушем удалений с lease, claims.py);
  projects/*/DISPATCH.md — то же в файле, пока учёт не переведён на ref (представление не трогает);
  OWNER_QUEUE.md         — «Состояние: взял в работу — <этот id>…» → «Состояние: свободно» и строка
                           «Прогресс <UTC> (<id>): захват снят — <причина>» под ней.
Чужие номера и узлы не трогает. Берёт файлы из свежего origin/main (рабочую копию не трогает),
один коммит с трейлером `Lunobot-Instance:`, пуш с повтором до 3 раз. Узел — `node.py`.
Коды: 0 — снято или снимать нечего, 1 — пуш не прошёл, 2 — ошибка вызова.
"""
import argparse
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import claims  # noqa: E402
from acct_line import git  # noqa: E402

RECORD = re.compile(r"\d\d-\d\d-\d{4} \d\d:\d\d:\d\d ")
QUEUE = "OWNER_QUEUE.md"
TRACE = re.compile(r"^(Прогресс|Доп\. проверка|Доп\. шаг)\b")


def platform_code(name=None):
    name = name or sys.platform
    if name.startswith("win"):
        return "MSW"
    if name == "darwin":
        return "DAR"
    if "bsd" in name or name.startswith("dragonfly"):
        return "BSD"
    return "LNX"


def owner(number, node):
    """Регулярка id этого владельца: номер и узел, платформа и суффикс воркера — любые."""
    return re.compile(rf"Лунобот-{number} \((?:instance|node) {node}; [A-Z]{{3}}(?:; [^)]*)?\)")


def collapse(lines):
    """Без пустых строк подряд и в начале/конце хвоста: одна запись — один абзац (§ 8)."""
    out = []
    for line in lines:
        if line == "" and (not out or out[-1] == ""):
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def release_dispatch(text, who):
    """(новый текст, снятые строки): убраны все записи с меткой времени и этим id."""
    kept, gone = [], []
    for line in text.split("\n"):
        (gone if RECORD.match(line) and who.search(line) else kept).append(line)
    return (collapse(kept) if gone else text), gone


def release_queue(text, who, trace):
    """(новый текст, id блоков): «взял в работу» этого id → «свободно» + строка следа под ним."""
    lines, freed, block = text.split("\n"), [], None
    out = []
    for line in lines:
        m = re.match(r"## (\S+)", line)
        if m:
            block = m.group(1)
        if line.startswith("Состояние:") and re.match(r"Состояние:\s*взял в работу", line) and who.search(line):
            out += ["Состояние: свободно", trace]
            freed.append(block or "?")
            continue
        out.append(line)
    if not freed:
        return text, freed
    # в блоке остаётся одна строка следа — новая (check_owner_queue.py, п. 5); история — в тикете поручения
    res, block = [], None
    for line in out:
        m = re.match(r"## (\S+)", line)
        if m:
            block = m.group(1)
        elif line == "--":
            block = None
        elif block in freed and TRACE.match(line) and line != trace:
            continue
        res.append(line)
    return "\n".join(res), freed


def changes(repo, base, who, trace):
    """{путь: новый текст} и человекочитаемый отчёт по снятому."""
    files = git(repo, "ls-tree", "-r", "--name-only", base, "projects", QUEUE).stdout.split("\n")
    out, report = {}, []
    for path in files:
        if not (path == QUEUE or re.fullmatch(r"projects/[^/]+/DISPATCH\.md", path)):
            continue
        old = git(repo, "show", f"{base}:{path}").stdout
        if path == QUEUE:
            new, freed = release_queue(old, who, trace)
            report += [f"{QUEUE}: блок {b} — свободно" for b in freed]
        elif claims.MARKER in old:
            continue  # представление refs/claims: его перепишет janitor.py
        else:
            new, gone = release_dispatch(old, who)
            report += [f"{path}: {g[:110]}" for g in gone]
        if new != old:
            out[path] = new
    return out, report


def release_refs(repo, who, dry):
    """Удалить свои refs/claims (номер+узел в строке захвата) одним атомарным пушем с lease.
    Возвращает число снятых захватов или None, если удаление не прошло (кто-то продлил/снял
    между чтением и удалением — ещё круг)."""
    claims._fetched.pop((repo, "origin"), None)
    claims.fetch(repo)
    mine = [c for c in claims.refs(repo) if who.search(c["line"])]
    seen = set()
    for c in mine:
        if c["sha"] not in seen:
            seen.add(c["sha"])
            print(("сниму " if dry else "снял ") + f"refs/claims/{c['project']}/{c['key']}: {c['line'][:110]}")
    if not mine or dry:
        return len(seen)
    ok, rejected, net = claims._push_retry(repo, "origin", [(c["ref"], None, c["sha"]) for c in mine])
    if ok:
        return len(seen)
    print("удаление ref не прошло: " + (", ".join(rejected) if rejected else "сеть"))
    return None


def attempt(repo, number, node, sign, reason, dry):
    n_refs = release_refs(repo, owner(number, node), dry)
    if n_refs is None:
        return "race"
    git(repo, "fetch", "-q", "origin", "main")
    base = git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()
    stamp = datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")
    trace = f"Прогресс {stamp} UTC ({sign}): захват снят — {reason}; продолжать по тикету поручения и status/."
    new, report = changes(repo, base, owner(number, node), trace)
    for r in report:
        print(("сниму " if dry else "снял ") + r)
    if not new:
        if not n_refs:
            print(f"захватов {sign} нет — снимать нечего")
        return "ok"
    if dry:
        return "ok"
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        git(repo, "read-tree", base, env=env)
        for path, text in new.items():
            blob = git(repo, "hash-object", "-w", "--stdin", data=text).stdout.strip()
            git(repo, "update-index", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git(repo, "write-tree", env=env).stdout.strip()
    msg = f"захваты {sign} сняты: {reason}\n\nLunobot-Instance: {sign}\n"
    commit = git(repo, "commit-tree", tree, "-p", base, data=msg).stdout.strip()
    push = git(repo, "push", "-q", "origin", f"{commit}:refs/heads/main", check=False)
    if push.returncode:
        print(f"пуш отклонён (гонка?): {push.stderr.strip()}")
        return "race"
    print(f"запушено {commit[:7]}: сняты захваты {sign} ({len(report)})")
    return "ok"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--number", required=True, type=int)
    ap.add_argument("--node", help="24 hex; по умолчанию — node.py этого узла")
    ap.add_argument("--platform", help="MSW|LNX|DAR|BSD; по умолчанию — по ОС")
    ap.add_argument("--reason", default="сессия завершена")
    ap.add_argument("--repo", default=HERE, help="клон учёта (по умолчанию каталог скрипта)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.node:
            node = a.node
        else:
            import node as node_mod
            node = node_mod.identify()
    except (OSError, ValueError, RuntimeError) as e:
        print(f"узел не определён: {e}", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[0-9a-f]{24}", node):
        print(f"--node: нужен 24-значный hex, получено {node!r}", file=sys.stderr)
        return 2
    sign = f"Лунобот-{a.number} (node {node}; {a.platform or platform_code()})"
    if not a.dry_run:
        # конец круга: уборка и пульс не ждут cron (janitor_kick.py, unxed/lunobot#230)
        import janitor_kick
        janitor_kick.spawn(a.repo)
    try:
        for _ in range(3):
            if attempt(a.repo, a.number, node, sign, a.reason, a.dry_run) == "ok":
                return 0
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2
    print("пуш не прошёл за 3 попытки — захваты снимет janitor.py", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
