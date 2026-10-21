#!/usr/bin/env python3
"""Захваты на git-ref учётного репозитория (§ 3 п. 12, § 8 «DISPATCH.md»).

    python3 claims.py take      <проект> "<строка захвата>"                  [--repo DIR]
    python3 claims.py keepalive <проект> "<ключ|подстрока>"   --sign "<id>"  [--repo DIR]
    python3 claims.py drop      <проект> "<ключ|подстрока>"   --sign "<id>"  [--all] [--foreign]
    python3 claims.py list      [<проект>]
    python3 claims.py keys      "<строка захвата>"                          # только показать ключи
    python3 claims.py migrate   [--apply]                                   # разовый перенос DISPATCH.md

Захват — ref `refs/claims/<проект>/<ключ>` на коммит с пустым деревом, чьё сообщение — та же
строка, что раньше писалась в DISPATCH.md («ДД-ММ-ГГГГ ЧЧ:ММ:СС Я Лунобот-N (node …; LNX[; воркер …]),
взял … [маршрут]»). Создание — один `git push --atomic` с `--force-with-lease=<ref>:` («ref не должен
существовать»): сервер сравнивает и меняет ref атомарно, поэтому два бота не возьмут одно и то же, а
захваты РАЗНЫХ задач друг с другом не конкурируют вовсе (раньше любые две записи гонялись за один
`main`: 21-10-2026 — 1241 коммит учёта за 48 ч, десятки отказов пуша). Тикет целиком
(`<o>-<r>-<N>`) и его часть (`<o>-<r>-<N>/part-<P>`) не уживаются: git не даёт завести ref и
каталог ref с одним именем, и сервер отклоняет второй («directory file conflict») — это и есть
правило «та же часть или без части». Разные части одного тикета живут рядом.

Ключи строки: каждая ссылка тикета/PR (`check_dispatch.refs`) с частью строки; «красный поезд #N» →
`train-N`; «красный main <sha>» → `main-<sha7>`; «красный staging» → `staging`; «застой main» →
`stall-main`; поручение `OWNER_QUEUE.md` («<id блока>: …», блок существует) → только `queue-<id>`;
кастомная задача без ссылок → `custom-<12 hex sha1 текста>`; «объявляю заморозку land проекта» →
`freeze`; «прекращаю работу»/«считаю цель» → `note-<N>-<узел>` (своя, перезаписывается).

Продление — новый коммит с родителем-прежним и свежей датой коммиттера; живость захвата —
дата коммиттера ref-коммита. `DISPATCH.md` больше не источник правды, а представление, которое
пишет `janitor.py`. Читатели берут записи через `records()`/`dispatch_text()` (после `fetch()`).
Коды: 0 — сделано (или уже твоё), 1 — занято/гейт/нечего снимать, 2 — ошибка вызова или сети.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_dispatch  # noqa: E402

NS = "refs/claims"            # локальные ref в клоне
# На GitHub захваты лежат ВЕТКАМИ: прокси облачных сессий Claude Code отвечает 403 на push любых ref вне
# refs/heads (21-10-2026, узел 801452e4: refs/claims и теги), а ветки пушит. Workflows эти ветки
# пропускают (branches-ignore: claims/**), sweep.py их не перечисляет.
REMOTE_NS = "refs/heads/claims"


def remote_ref(ref):
    return REMOTE_NS + ref[len(NS):] if ref.startswith(NS + "/") else ref


def local_ref(ref):
    return NS + ref[len(REMOTE_NS):] if ref.startswith(REMOTE_NS + "/") else ref
TS = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}) ")
SIGN = re.compile(r"(?:Лунобот|Lunobot)-(\d+) \((?:node|instance) ([0-9a-f]{6,24}); ([A-Z]{3})")
WORKER = re.compile(r"воркер\s+([0-9a-f]{6,})")
CUSTOM = re.compile(r"кастомн\w+ задач\w+\s*«([^»]+)»")
FREEZE = "объявляю заморозку land проекта"
NOTES = ("прекращаю работу", "считаю цель")
TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                    "a b v g d e e zh z i y k l m n o p r s t u f h c ch sh sch _ y _ e yu ya".split()))
HEADER = ("Представление: генерируется janitor.py из refs/claims учётного репозитория; вручную не "
          "править.\nЗахват и снятие — python3 claims.py take|keepalive|drop (§ 8 инструкции).")


def git(repo, *args, data=None, env=None, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=env,
                       input=None if data is None else data.encode("utf-8"))
    r.stdout = r.stdout.decode("utf-8", "replace")
    r.stderr = r.stderr.decode("utf-8", "replace")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def slug(text):
    out = []
    for ch in text.lower():
        if re.match(r"[a-z0-9._/-]", ch):
            out.append(ch)
        elif ch in TRANSLIT:
            out.append(TRANSLIT[ch].strip("_"))
        else:
            out.append("-")
    return re.sub(r"-{2,}", "-", "".join(out)).strip("-/")


def owner(line):
    """(номер, узел, воркер|None) из строки или подписи; None — id не распознан."""
    m = SIGN.search(line)
    if not m:
        return None
    close = line.find(")", m.end())
    w = WORKER.search(line[m.start():close + 1 if close >= 0 else len(line)])
    return m.group(1), m.group(2), (w.group(1) if w else None)


def sign_of(line):
    m = SIGN.search(line)
    return f"Лунобот-{m.group(1)} (node {m.group(2)}; {m.group(3)})" if m else None


def keys(line, queue_ids=()):
    """Ключи ref строки захвата (без префикса refs/claims/<проект>/), отсортированные."""
    body = re.sub(r"\]\(https?://[^)]+\)", "]", line)
    if FREEZE in body:
        return ["freeze"]
    if any(n in body for n in NOTES):
        o = owner(body)
        return [f"note-{o[0]}-{o[1]}"] if o else []
    custom = CUSTOM.search(body)
    custom = custom.group(1).strip() if custom else None
    if custom:
        qid = re.match(r"([\w.-]+)\s*:", custom)
        if qid and qid.group(1) in queue_ids:
            return [slug(f"queue-{qid.group(1)}")]
    part = check_dispatch.part_id(body)
    out = set()
    for r in check_dispatch.refs(body):
        if r.startswith("поезд#"):
            out.add(f"train-{r[6:]}")
        elif r.startswith("main@"):
            out.add(f"main-{r[5:]}")
        elif r == "staging":
            out.add("staging")
        elif r == "застой-main":
            out.add("stall-main")
        else:
            o_r, n = r.split("#")
            o, rep = o_r.split("/")
            out.add(slug(f"{o}-{rep}-{n}") + (f"/part-{slug(part)}" if part else ""))
    if not out and custom:
        norm = re.sub(r"\s+", " ", custom.lower()).strip()
        out.add("custom-" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12])
    return sorted(out)


def queue_ids(repo, base):
    r = git(repo, "show", f"{base}:OWNER_QUEUE.md", check=False)
    return set(re.findall(r"^## (\S+)", r.stdout, re.M)) if r.returncode == 0 else set()


# ── чтение ──────────────────────────────────────────────────────────────────────────────────

_fetched = {}


def fetch(root=HERE, remote="origin"):
    """Обновить локальные refs/claims/* из origin (с --prune). True — удалось. Один раз на процесс."""
    if (root, remote) in _fetched:
        return _fetched[(root, remote)]
    ok = False
    for _ in range(3):
        r = git(root, "fetch", "-q", remote, f"+{REMOTE_NS}/*:{NS}/*", "--prune", check=False)
        if r.returncode == 0:
            ok = True
            break
        if not re.search(r"unable to access|Could not resolve|timed out|Connection|early EOF|HTTP 5\d\d",
                         r.stderr):
            break  # не сеть (нет origin, не репозиторий) — повтор не поможет
        time.sleep(1)
    _fetched[(root, remote)] = ok
    return ok


def refs(root=HERE, project=None):
    """[{ref, project, key, sha, ts(unix), line, parent}] локальных refs/claims."""
    prefix = f"{NS}/{project}/" if project else f"{NS}/"
    r = git(root, "for-each-ref", prefix,
            "--format=%(refname)%00%(objectname)%00%(committerdate:unix)%00%(subject)%00%(parent)",
            check=False)
    out = []
    for row in r.stdout.splitlines():
        if not row:
            continue
        ref, sha, ts, subject, parent = row.split("\0")
        rest = ref[len(NS) + 1:]
        proj, _, key = rest.partition("/")
        out.append({"ref": ref, "project": proj, "key": key, "sha": sha, "ts": int(ts),
                    "line": subject, "parent": parent})
    return out


def _stamp(unix):
    return datetime.fromtimestamp(unix, timezone.utc).strftime("%d-%m-%Y %H:%M:%S")


def keepalive_line(line, unix):
    """Строка продления в старом формате DISPATCH.md: её читают подсчёт слотов и fleet_watch."""
    who = re.search(check_dispatch.ID, line)
    url = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", line)
    custom = CUSTOM.search(line)
    if not who or not (url or custom):
        return None
    what = f"задачей {url.group(0)}" if url else f"кастомной задачей «{custom.group(1)}»"
    return f"{_stamp(unix)} {who.group(0)}, работаю над {what}"


def records(root=HERE, project=None):
    """Строки захватов в формате DISPATCH.md по времени; несколько ref одного захвата — одна
    строка; продлённый захват — его строка и строка «работаю над» с датой продления."""
    seen, out = set(), []
    for c in refs(root, project):
        if c["sha"] in seen:
            continue
        seen.add(c["sha"])
        m = TS.match(c["line"])
        out.append((m.group(1) if m else _stamp(c["ts"]), c["line"]))
        base = datetime.strptime(m.group(1), "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=timezone.utc).timestamp() if m else c["ts"]
        if c["ts"] - base > 60:
            ka = keepalive_line(c["line"], c["ts"])
            if ka:
                out.append((_stamp(c["ts"]), ka))
    out.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y %H:%M:%S"))
    return [line for _, line in out]


MARKER = "генерируется janitor.py из refs/claims"


def ref_mode(root=HERE):
    """Учёт уже переведён на ref: есть хоть один refs/claims или хоть один DISPATCH.md —
    представление (шапка с MARKER). До перевода (`claims.py migrate --apply`) всё работает по файлам."""
    if refs(root):
        return True
    base = os.path.join(root, "projects")
    for name in (os.listdir(base) if os.path.isdir(base) else []):
        try:
            with open(os.path.join(base, name, "DISPATCH.md"), encoding="utf-8") as f:
                if MARKER in f.read():
                    return True
        except OSError:
            continue
    return False


def dispatch_text(root=HERE, project=None, path=None):
    """Текст записей проекта для читателей DISPATCH.md: после fetch() — из refs/claims; до
    перевода учёта на ref — из файла `path` (по умолчанию projects/<проект>/DISPATCH.md)."""
    fetch(root)
    if ref_mode(root):
        return "\n\n".join(records(root, project)) + "\n"
    path = path or os.path.join(root, "projects", project or "", "DISPATCH.md")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def render_view(project, lines):
    body = "\n\n".join(lines)
    return f"# DISPATCH — {project}\n\n{HEADER}\n" + (f"\n{body}\n" if body else "")


# ── запись ──────────────────────────────────────────────────────────────────────────────────

def _commit(repo, line, sign, parent=None, unix=None):
    tree = git(repo, "hash-object", "-w", "-t", "tree", "--stdin", data="").stdout.strip()
    env = dict(os.environ)
    if unix is not None:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"{int(unix)} +0000"
    args = ["commit-tree", tree] + (["-p", parent] if parent else [])
    msg = f"{line}\n\nLunobot-Instance: {sign}\n" if sign else f"{line}\n"
    return git(repo, *args, data=msg, env=env).stdout.strip()


def _push(repo, remote, specs):
    """specs: [(ref, new_sha|None для удаления, expected_sha|'' для «не существует»)].
    Возвращает (ok, отклонённые ref, сетевой_сбой)."""
    args = ["push", "--atomic", "--porcelain", remote]
    for ref, _, exp in specs:
        args.append(f"--force-with-lease={remote_ref(ref)}:{exp}")
    for ref, new, _ in specs:
        args.append(f"{new}:{remote_ref(ref)}" if new else f":{remote_ref(ref)}")
    r = git(repo, *args, check=False)
    rejected = [local_ref(l.split("\t")[1].split(":", 1)[1]) for l in r.stdout.splitlines()
                if l.startswith("!\t") and "\t" in l]
    rejected = [x for x in rejected if x]
    if r.returncode == 0:
        return True, [], False
    return False, rejected, not rejected


def _push_retry(repo, remote, specs):
    for attempt in range(3):
        ok, rejected, net = _push(repo, remote, specs)
        if ok or not net:
            return ok, rejected, net
        time.sleep(1 + attempt)
    return False, [], True


def _holders(repo, project, wanted):
    """Записи, мешающие ключам wanted: тот же ключ, ключ-«каталог» над ним или под ним."""
    _fetched.pop((repo, "origin"), None)
    fetch(repo)
    out = []
    for c in refs(repo, project):
        for k in wanted:
            if c["key"] == k or k.startswith(c["key"] + "/") or c["key"].startswith(k + "/"):
                out.append(c)
                break
    return out


def validate(repo, project, line, base):
    """Претензии гейта check_dispatch к строке (формат, маршрут, время, «уже в CI.md»)."""
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "projects", project)
        os.makedirs(d)
        ci = git(repo, "show", f"{base}:projects/{project}/CI.md", check=False)
        with open(os.path.join(d, "CI.md"), "w", encoding="utf-8") as f:
            f.write(ci.stdout if ci.returncode == 0 else "")
        path = os.path.join(d, "DISPATCH.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# DISPATCH — {project}\n\n{line}\n")
        entries, problems = check_dispatch.check(path, 45)
        problems = [p for p in problems if p[0] != "протух"]
        if not entries and not any(x in line for x in check_dispatch.FINAL):
            problems.append(("формат", 3, "строка не распознана как захват (нужны метка времени, "
                                          "id «Я Лунобот-N (node …; ПЛАТФОРМА)», «взял» и ключ задачи)"))
    return problems


def take(repo, project, line, remote="origin", unix=None, check=True):
    """Захватить. 0 — взято (или уже держит тот же владелец), 1 — занято/гейт, 2 — сеть."""
    line = line.strip()
    if "\n" in line:
        print("ОТКАЗ: захват — ровно одна строка")
        return 1
    git(repo, "fetch", "-q", remote, "main", check=False)
    base = "FETCH_HEAD" if git(repo, "rev-parse", "-q", "--verify", "FETCH_HEAD",
                               check=False).returncode == 0 else "HEAD"
    if check:
        problems = validate(repo, project, line, base)
        if problems:
            for kind, _, msg in problems:
                print(f"ГЕЙТ [{kind}]: {msg}")
            return 1
    ks = keys(line, queue_ids(repo, base))
    if not ks:
        print("ОТКАЗ: у строки нет ключа захвата (ссылка на тикет/PR, «кастомная задача» или инцидент)")
        return 1
    me = owner(line)
    sign = sign_of(line)
    if unix is None and TS.match(line):
        # дата коммиттера — метка строки (её взяли из date -u в момент записи, § 8): живость считают от неё
        unix = datetime.strptime(TS.match(line).group(1), "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=timezone.utc).timestamp()
    commit = _commit(repo, line, sign, unix=unix)
    notes = [k for k in ks if k.startswith("note-")]
    if notes:
        fetch(repo, remote)
    for _ in range(3):
        current = {c["key"]: c["sha"] for c in refs(repo, project)} if notes else {}
        specs = [(f"{NS}/{project}/{k}", commit, current.get(k, "") if k in notes else "") for k in ks]
        ok, rejected, net = _push_retry(repo, remote, specs)
        if ok:
            print("взято: " + ", ".join(project + "/" + k for k in ks))
            if check:  # не перенос migrate: событие в журнал инстанса (история захватов, journal.py)
                import journal
                journal.try_add(repo, sign, {"kind": "claim", "event": "take", "project": project,
                                             "keys": ks, "line": line}, remote)
            return 0
        if net:
            print("сеть: пуш ref не прошёл за 3 попытки", file=sys.stderr)
            return 2
        holders = _holders(repo, project, ks)
        if notes and not holders:
            continue  # своя заметка поменялась между чтением и пушем — ещё раз
        foreign = [h for h in holders if owner(h["line"]) != me]
        if foreign:
            seen = set()
            for h in foreign:
                if h["sha"] not in seen:
                    seen.add(h["sha"])
                    print(f"занято ({project}/{h['key']}): {h['line']}")
            return 1
        mine = {h["key"] for h in holders}
        ks = [k for k in ks if k not in mine]
        if not ks:
            print("уже твоё: захват держит тот же владелец")
            return 0
    return 1


def _match(cs, needle):
    if not needle:
        return cs
    exact = [c for c in cs if c["key"] == needle]
    return exact or [c for c in cs if needle in c["line"] or needle == f"{c['project']}/{c['key']}"]


def _same(sign, line):
    a, b = owner(sign), owner(line)
    return bool(a and b and a[:2] == b[:2])


def keepalive(repo, project, needle, sign, remote="origin"):
    fetch(repo, remote)
    cs = [c for c in _match(refs(repo, project), needle) if _same(sign, c["line"])]
    if not cs:
        print(f"у {sign} нет захвата {project} с «{needle}»")
        return 1
    by_sha = {}
    for c in cs:
        by_sha.setdefault(c["sha"], []).append(c)
    specs = []
    for sha, group in by_sha.items():
        new = _commit(repo, group[0]["line"], sign_of(group[0]["line"]), parent=sha)
        specs += [(c["ref"], new, sha) for c in group]
    ok, rejected, net = _push_retry(repo, remote, specs)
    if ok:
        print("продлено: " + ", ".join(c["key"] for c in cs))
        return 0
    print("продление не прошло: " + (", ".join(rejected) if rejected else "сеть"))
    return 2 if net else 1


NOTHING = 3  # drop: снимать нечего (CLI отдаёт 1)
FOREIGN_MIN = 90  # § 6: чужой захват брошен, если молчит дольше 90 минут


def drop(repo, project, needle, sign=None, remote="origin", all_=False, foreign=False, quiet=False):
    """Снять захват(ы) по ключу/подстроке. Только свои (номер+узел подписи); --foreign — чужой
    брошенный (старше FOREIGN_MIN минут без продления, § 6). sign=None — без проверки (janitor)."""
    fetch(repo, remote)
    cs = _match(refs(repo, project), needle)
    if sign is not None:
        mine = [c for c in cs if _same(sign, c["line"])]
        if foreign:
            age = time.time() - FOREIGN_MIN * 60
            mine += [c for c in cs if not _same(sign, c["line"]) and c["ts"] < age]
        cs = mine
    if not cs:
        if not quiet:
            print(f"в {project} нет {'' if sign is None else 'своего '}захвата с «{needle}» — снимать нечего")
        return NOTHING
    if len({c["sha"] for c in cs}) > 1 and not all_:
        print(f"«{needle}» подходит к {len({c['sha'] for c in cs})} захватам — уточни ключ или добавь --all")
        for c in cs:
            print(f"   {c['key']}: {c['line'][:100]}")
        return 1
    ok, rejected, net = _push_retry(repo, remote, [(c["ref"], None, c["sha"]) for c in cs])
    if ok:
        if not quiet:
            print("снято: " + ", ".join(project + "/" + c["key"] for c in cs))
        if sign is not None:  # бот, а не janitor: сколько держали — в журнал инстанса (journal.py)
            import journal
            first = {}
            for c in cs:
                first.setdefault(c["sha"], c)
            for c in first.values():
                held = time.time() - _taken_at(repo, c)
                journal.try_add(repo, sign, {"kind": "claim", "event": "drop", "project": project,
                                             "line": c["line"], "foreign": foreign and not _same(sign, c["line"]),
                                             "held_min": round(held / 60)}, remote)
        return 0
    print("снятие не прошло: " + (", ".join(rejected) + " (захват продлён или уже снят)" if rejected else "сеть"))
    return 2 if net else 1


def _taken_at(repo, c):
    """Время взятия захвата: метка строки (продления двигают дату коммиттера, но не метку)."""
    m = TS.match(c["line"])
    if m:
        return datetime.strptime(m.group(1), "%d-%m-%Y %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    return c["ts"]


# ── разовый перенос ────────────────────────────────────────────────────────────────────────

def migrate(repo, apply=False, remote="origin"):
    """DISPATCH.md всех проектов → refs/claims (метка строки — дата коммиттера, продление —
    дата последней «работаю над» того же ключа), файлы → представление. Возвращает число захватов."""
    import janitor
    n = 0
    for name in sorted(os.listdir(os.path.join(repo, "projects"))):
        path = os.path.join(repo, "projects", name, "DISPATCH.md")
        if not os.path.isfile(path):
            continue
        entries, _ = check_dispatch.check(path, 10 ** 6)
        latest = {}
        for e in entries:
            if e["verb"] == "работаю":
                latest[e["key"]] = max(latest.get(e["key"], e["ts"]), e["ts"])
        with open(path, encoding="utf-8") as f:
            freezes = [l.strip() for l in f if FREEZE in l and TS.match(l)]
        todo = [(e["text"], e["ts"], latest.get(e["key"])) for e in entries if e["verb"] == "взял"]
        todo += [(l, datetime.strptime(TS.match(l).group(1), "%d-%m-%Y %H:%M:%S"), None) for l in freezes]
        for text, ts, ka in todo:
            n += 1
            # продление — дата коммиттера: records() покажет его строкой «работаю над»
            unix = max(ts, ka or ts).replace(tzinfo=timezone.utc).timestamp()
            print(f"{name}: {'перенёс' if apply else 'перенесу'} {keys(text)} ← {text[:90]}")
            if apply:
                take(repo, name, text, remote, unix=unix, check=False)
    if apply:
        _fetched.pop((repo, remote), None)
        fetch(repo, remote)
        janitor.write_views(repo)
    return n


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("op", choices=["take", "keepalive", "drop", "list", "keys", "migrate"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--sign", help="id инстанса, как в подписи (§ 1)")
    ap.add_argument("--repo", default=HERE, help="клон учёта (по умолчанию каталог скрипта)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--foreign", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.op == "keys":
            print("\n".join(keys(a.args[0])))
            return 0
        if a.op == "list":
            fetch(a.repo, a.remote)
            for line in records(a.repo, a.args[0] if a.args else None):
                print(line)
            return 0
        if a.op == "migrate":
            migrate(a.repo, a.apply, a.remote)
            return 0
        if len(a.args) != 2:
            print(f"{a.op}: нужны <проект> и строка/ключ", file=sys.stderr)
            return 2
        project, text = a.args
        # каждый захват и снятие пинают janitor.yml, если тот давно не шёл (janitor_kick.py, unxed/lunobot#230)
        import janitor_kick
        janitor_kick.spawn(a.repo)
        if a.op == "take":
            return take(a.repo, project, text, a.remote)
        if not a.sign or not SIGN.search(a.sign):
            print("--sign: нужен полный id, например «Лунобот-1 (node a721a6d1487257292ae00780; LNX)»",
                  file=sys.stderr)
            return 2
        if a.op == "keepalive":
            return keepalive(a.repo, project, text, a.sign, a.remote)
        code = drop(a.repo, project, text, a.sign, a.remote, a.all, a.foreign)
        return 1 if code == NOTHING else code
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
