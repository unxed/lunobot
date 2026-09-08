#!/usr/bin/env python3
"""Пульт управления флотом Луноботов.

Ничего не хранит и ничего не коммитит. Собирает картину на лету из двух источников:
GitHub (что сделано, что открыто, какие ветки висят) и DISPATCH.md (что делается прямо сейчас).
Второго источника истины не появляется — отчёт живёт ровно до закрытия терминала.

Использование:
    python3 status.py                 отчёт по всем проектам из projects/INDEX.md
    python3 status.py f4              только по одному проекту
    python3 status.py --hours 48      окно «что сделано» вместо суток

Данные GitHub берутся через `gh api`, если он есть и авторизован, иначе через
неавторизованный HTTP (60 запросов в час). В CI подхватывается GITHUB_TOKEN.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
STALE_MIN = 45


def gh_json(path):
    """GET к GitHub API. Возвращает разобранный JSON или None."""
    if shutil.which("gh"):
        try:
            out = subprocess.run(["gh", "api", path], capture_output=True, timeout=30)
            if out.returncode == 0:
                return json.loads(out.stdout)
        except Exception:
            pass
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  _(GitHub недоступен: {e})_")
        return None


def projects(only=None):
    """Проекты и их репозитории — из паспортов, а не из отдельного списка."""
    for d in sorted((ROOT / "projects").iterdir()):
        if not d.is_dir() or (only and d.name != only):
            continue
        passport = (d / "PROJECT.md")
        if not passport.exists():
            continue
        m = re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", passport.read_text())
        yield d.name, (m.group(1) if m else None), d


def active_claims(project_dir):
    """Кто что держит прямо сейчас, по DISPATCH.md."""
    f = project_dir / "DISPATCH.md"
    if not f.exists():
        return []
    holders = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        ts = re.match(TS, line)
        who = re.search(r"Лунобот-\d+ \((?:instance|node) [0-9a-f]+; [A-Z]{3}\)", line)
        if not (ts and who) or not re.search(r"взял|работаю", line):
            continue
        key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", line)
        key = key.group(0) if key else None
        if not key:
            custom = re.search(r"«([^»]+)»", line) or re.search(
                r"кастомную задачу,\s*([^(]+)", line)
            key = f"«{custom.group(1).strip()}»" if custom else line[:40]
        part = re.search(r"\(часть \d+ из \d+\)", line)
        full = key + (" " + part.group(0) if part else "")
        stamp = datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S")
        prev = holders.get(full)
        if not prev or stamp > prev[0]:
            origin = re.search(r"по (§ ?[\d.]+[^(]*)", line)
            holders[full] = (stamp, who.group(0), origin.group(1).strip() if origin else "")
    return [(k, *v) for k, v in holders.items()]


def report(name, repo, d, hours):
    print(f"\n## {name}\n")

    claims = active_claims(d)
    print("### В работе\n")
    if not claims:
        print("Никто ничего не держит.\n")
    else:
        # боты пишут время в своих часовых поясах: отсчитываем от самой свежей записи,
        # а не от часов машины, где запущен пульт
        now = max([c[1] for c in claims] + [datetime.now()])
        for key, stamp, who, origin in sorted(claims, key=lambda c: c[1]):
            age = int((now - stamp).total_seconds() // 60)
            mark = "  ⚠ протух" if age > STALE_MIN else ""
            tail = f" — {origin}" if origin else ""
            print(f"- {key}{tail} — {who}, {age} мин{mark}")
        print()

    ci = d / "CI.md"
    pending = [l for l in ci.read_text(encoding="utf-8").splitlines() if "http" in l] if ci.exists() else []
    if pending:
        print(f"### Непроверенные прогоны CI: {len(pending)}\n")
        for l in pending[:10]:
            print(f"- {l.strip()}")
        print()

    if not repo:
        print("_В паспорте проекта нет ссылки на репозиторий — данные GitHub пропущены._")
        return

    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    done = gh_json(f"/search/issues?q=repo:{repo}+is:pr+is:merged+merged:>={since}&per_page=50")
    print(f"### Сделано за {hours} ч\n")
    if done and done.get("items"):
        for pr in done["items"]:
            issues = ", ".join("#" + n for n in re.findall(r"#(\d+)", pr["title"]))
            print(f"- [#{pr['number']}]({pr['html_url']}) {pr['title'][:70]}"
                  + (f" → тикет {issues}" if issues else ""))
    elif done:
        print("Ничего не влито.")
    print()

    counts = gh_json(f"/search/issues?q=repo:{repo}+is:issue+is:open&per_page=1")
    if counts:
        print(f"### Открытых тикетов: {counts.get('total_count', '?')}\n")

    branches = gh_json(f"/repos/{repo}/branches?per_page=100")
    prs = gh_json(f"/repos/{repo}/pulls?state=open&per_page=100")
    if branches is not None and prs is not None:
        with_pr = {p["head"]["ref"] for p in prs}
        held = " ".join(c[0] for c in claims)
        junk = [b["name"] for b in branches
                if b["name"] not in ("main", "master") and b["name"] not in with_pr
                and not any(n in held for n in re.findall(r"\d+", b["name"]))]
        if junk:
            print(f"### Ветки без PR и без захвата: {len(junk)}\n")
            for b in junk[:15]:
                print(f"- `{b}`")
            if len(junk) > 15:
                print(f"- … ещё {len(junk) - 15}")
            print()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hours = 24
    if "--hours" in sys.argv:
        hours = int(sys.argv[sys.argv.index("--hours") + 1])
    only = args[0] if args else None
    print(f"# Пульт Луноботов — {datetime.now():%d-%m-%Y %H:%M}")
    for name, repo, d in projects(only):
        report(name, repo, d, hours)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
