#!/usr/bin/env python3
"""Уборка мусора (LUNOBOT.md § 8, «Уборка мусора»): без --apply только показывает.

    sweep.py --number <N> [--apply]

Убирает только то, что по правилам можно убрать, не мешая другим:

  локально  — только своё: /tmp/lunobot-<N>/work/* старше 6 ч, на которые не ссылается ни
              один захват (DISPATCH.md) и ни один status-файл (припаркованный коммит), и
              бесхозные /tmp/lunobot-<N>-* вне /tmp/lunobot-<N>/ (старый образец). Чужие
              /tmp/lunobot-<M> и служебные каталоги агентной среды (у Claude Code —
              /tmp/claude-*, у других сред — свои) не трогает никогда.
  ветки     — в репозиториях проектов из INDEX.md и в учётном: временные по имени
              (tmp/*, а также старые образцы probe/*, sandbox*, *-sandbox, tmp-*,
              lunobot/*-probe-*) старше 24 ч без открытого PR; ветку, чьё имя есть в захвате или
              status-файле (ветка парковки, LUNOBOT.md § 7.5), не трогает; bisect/<n>/* закрытого поезда;
              complaint/*, lunobot/urgent/* и lunobot/pr/* с закрытым или влитым PR;
              lunobot/train/* влитого или закрытого поезда старше 24 ч. Прочие
              ветки (claude/*, человеческие) не трогает — только перечисляет.
  PR        — не закрывает; перечисляет открытые lunobot/urgent/* и lunobot/pr/* без захвата
              старше 24 ч (их берут по § 5 п. 3).

Пороги больше самого долгого шага, поэтому живую работу другого бота скрипт не заденет, а
удаление ветки перепроверяет открытые PR и возраст прямо перед удалением.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_AGE = timedelta(hours=6)
BRANCH_AGE = timedelta(hours=24)
# Ветки своих PR бота: срочные (режим поездов) и обычные (режим публикации PR), § 7.2.
OWN_PR = ("lunobot/urgent/", "lunobot/pr/")
TEMP = re.compile(r"^(tmp/|tmp-|probe/|sandbox|[^/]*-sandbox$|lunobot/[^/]*-probe-)")


def gh(path, *args):
    p = subprocess.run(["gh", "api", path, *args], capture_output=True, text=True)
    if p.returncode:
        return None
    return json.loads(p.stdout) if p.stdout.strip() else {}


def gh_all(path):
    try:
        p = subprocess.run(["gh", "api", "--paginate", path], capture_output=True,
                           text=True, timeout=60)
        if p.returncode == 0 and p.stdout.strip():
            pages = json.loads(p.stdout.replace("][", ","))
            if isinstance(pages, list):
                return pages
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass

    # gh --paginate follows GitHub's Link header, which some proxies rewrite to
    # unsupported numeric repository paths. Request each page explicitly instead.
    items = []
    for page in range(1, 101):
        separator = "&" if "?" in path else "?"
        try:
            p = subprocess.run(["gh", "api", f"{path}{separator}page={page}"],
                               capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if p.returncode != 0:
            return None
        try:
            batch = json.loads(p.stdout)
        except ValueError:
            return None
        if not isinstance(batch, list):
            return None
        items.extend(batch)
        if len(batch) < 100:
            return items
    return None


def repos():
    remote = subprocess.run(["git", "-C", ROOT, "remote", "get-url", "origin"],
                            capture_output=True, text=True).stdout.strip()
    account = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"([^/\s]+/[^/\s]+?)(?:\.git)?/?", remote)
    if not account:
        raise ValueError("не удалось определить учётный репозиторий по origin")
    out = [account.group(1)]
    with open(os.path.join(ROOT, "projects", "INDEX.md"), encoding="utf-8") as source:
        text = source.read()
    for name in re.findall(r"^\d+\.\s*\[([^\]]+)\]", text, re.M):
        try:
            with open(os.path.join(ROOT, "projects", name, "PROJECT.md"),
                      encoding="utf-8") as source:
                p = source.read()
        except OSError:
            continue
        m = re.search(r"^- Код: https://github\.com/([^/\s]+/[^/\s]+)", p, re.M)
        if m:
            out.append(m.group(1))
    return out


def references():
    """Всё, что упомянуто в живых захватах и status-файлах: пути клонов и имена веток."""
    text = []
    for dirpath, _, files in os.walk(os.path.join(ROOT, "projects")):
        for f in files:
            if f == "DISPATCH.md" or os.path.basename(dirpath) == "status":
                with open(os.path.join(dirpath, f), encoding="utf-8") as fh:
                    text.append(fh.read())
    return "\n".join(text)


def local(number, refs, apply):
    now = time.time()
    work = f"/tmp/lunobot-{number}/work"
    victims = []
    if os.path.isdir(work):
        for name in sorted(os.listdir(work)):
            path = os.path.join(work, name)
            age = now - os.path.getmtime(path)
            if age > LOCAL_AGE.total_seconds() and path not in refs and name not in refs:
                victims.append(path)
    for name in sorted(os.listdir("/tmp")):
        if name.startswith(f"lunobot-{number}-"):
            path = os.path.join("/tmp", name)
            if now - os.path.getmtime(path) > LOCAL_AGE.total_seconds() and path not in refs:
                victims.append(path)
    for path in victims:
        print(f"local  {'удалил' if apply else 'удалю'} {path}")
        if apply:
            shutil.rmtree(path, ignore_errors=True) if os.path.isdir(path) else os.remove(path)
    return len(victims)


def age_of(repo, sha):
    c = gh(f"repos/{repo}/commits/{sha}")
    if not c:
        return timedelta(0)
    d = datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - d


def pr_state(repo, branch):
    owner = repo.split("/")[0]
    prs = gh(f"repos/{repo}/pulls?state=all&head={owner}:{branch}&per_page=5")
    if prs is None:
        # Отказ API — не «PR нет»: иначе --apply удалил бы временную ветку с открытым PR.
        return "unknown"
    if any(p["state"] == "open" for p in prs):
        return "open"
    return "closed" if prs else "none"


def branches(apply, refs, repo_names):
    n = 0
    for repo in repo_names:
        listed = gh_all(f"repos/{repo}/branches?per_page=100")
        if listed is None:
            # Сессия без доступа к одному проекту не должна оставлять неубранными все следующие.
            print(f"branch {repo}: список веток недоступен — пропускаю", file=sys.stderr)
            continue
        for b in listed:
            name, sha = b["name"], b["commit"]["sha"]
            reason = None
            if name in ("main", "master", "lunobot/staging"):
                continue
            if name in refs:
                continue
            m = re.match(r"^bisect/(\d+)/", name)
            if m:
                pr = gh(f"repos/{repo}/pulls/{m.group(1)}")
                if pr and pr.get("state") == "closed":
                    reason = f"бисект закрытого поезда #{m.group(1)}"
            elif name.startswith(("complaint/",) + OWN_PR):
                if pr_state(repo, name) == "closed":
                    reason = "PR закрыт или влит"
            elif name.startswith("lunobot/train/"):
                # fast-forward-мерж поезда ветку не удаляет: без этого их копились десятки (15-10-2026: 76 в f4).
                # Ветка без PR — поезд режется прямо сейчас, открытый PR — в пути: обе остаются.
                if pr_state(repo, name) == "closed" and age_of(repo, sha) > BRANCH_AGE:
                    reason = "поезд влит или закрыт, старше 24 ч"
            elif TEMP.match(name):
                if age_of(repo, sha) > BRANCH_AGE and pr_state(repo, name) == "none":
                    reason = "временная, старше 24 ч, PR нет"
            else:
                print(f"branch {repo} {name}: не временная — не трогаю (если брошена — скажи "
                      "владельцу)")
                continue
            if not reason:
                continue
            n += 1
            print(f"branch {'удалил' if apply else 'удалю'} {repo} {name} ({reason})")
            if apply:
                gh(f"repos/{repo}/git/refs/heads/{name}", "-X", "DELETE")
    return n


def stale_prs(refs, repo_names):
    for repo in repo_names:
        listed = gh_all(f"repos/{repo}/pulls?state=open&per_page=100")
        if listed is None:
            print(f"pr     {repo}: список PR недоступен — пропускаю", file=sys.stderr)
            continue
        for p in listed:
            head = p["head"]["ref"]
            upd = datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00"))
            if (head.startswith(OWN_PR) and head not in refs
                    and datetime.now(timezone.utc) - upd > BRANCH_AGE):
                print(f"pr     {repo}#{p['number']} {head}: без захвата и активности >24 ч — "
                      "это § 5 п. 3, возьми")


def main(argv):
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    number = opt("--number")
    if not number:
        print(__doc__)
        return 2
    apply = "--apply" in argv
    try:
        repo_names = repos()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    subprocess.run(["git", "-C", ROOT, "fetch", "-q", "origin", "main"], capture_output=True)
    refs = references()
    n = local(number, refs, apply) + branches(apply, refs, repo_names)
    stale_prs(refs, repo_names)
    print(f"итого: {n} {'удалено' if apply else 'к удалению (запусти с --apply)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
