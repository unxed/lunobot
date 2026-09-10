#!/usr/bin/env python3
"""Подметальщик учёта.

Делает механическую часть ритуала, которую раньше делали боты: снимает захваты
инстансов, замолчавших дольше срока, выбрасывает из очереди CI строки по уже влитым
или закрытым PR и убирает записи о ветках, которых больше нет.

Живость инстанса берётся из git-истории учётного репозитория: если инстанс что-то
коммитил, он жив, и отдельный keepalive для этого не нужен.

Запуск:
    python3 janitor.py            # разобрать и записать изменения
    python3 janitor.py --dry-run  # только показать, что сделал бы
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SILENT_MIN = 90
TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
WHO = r"Лунобот-(\d+) \((?:instance|node) ([0-9a-f]+); ([A-Z]{3})\)"
DRY = "--dry-run" in sys.argv


def gh(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return None


def last_seen():
    """Когда каждый инстанс последний раз что-либо коммитил."""
    out = subprocess.run(["git", "log", "--since=12 hours ago", "--format=%n@%ct", "-p",
                          "--", "projects"], cwd=ROOT, capture_output=True, text=True).stdout
    seen, when = {}, None
    for line in out.splitlines():
        if line.startswith("@") and line[1:].isdigit():
            when = int(line[1:])
            continue
        m = re.search(WHO, line)
        if m and when:
            key = (m.group(1), m.group(2))
            seen[key] = max(seen.get(key, 0), when)
    return seen


def branch_activity(repo):
    """Последний пуш в каждую ветку codex/* — второй источник живости: бот, который пишет
    код, пушит в свою ветку постоянно, даже если учёт не трогает."""
    out = {}
    for b in gh(f"/repos/{repo}/branches?per_page=100") or []:
        name = b["name"]
        if not name.startswith("codex/"):
            continue
        parts = name.split("/")
        if len(parts) < 4 or not parts[2].startswith("lunobot-"):
            continue
        node, num = parts[1], parts[2].split("-", 1)[1]
        c = gh(f"/repos/{repo}/commits/{b['commit']['sha']}") or {}
        date = (c.get("commit") or {}).get("committer", {}).get("date")
        if date:
            ts = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            out[(num, node)] = max(out.get((num, node), 0), ts)
    return out


def blocks(text):
    """Файл как список абзацев: одна запись — один абзац."""
    return [b for b in re.split(r"\n\s*\n", text) if b.strip()]


def save(path, kept, removed, what):
    if not removed:
        return 0
    print(f"{path.name}: убрано {len(removed)} — {what}")
    for r in removed:
        print("   ", r.strip().splitlines()[0][:100])
    if not DRY:
        path.write_text("\n\n".join(kept) + "\n", encoding="utf-8")
    return len(removed)


def repo_of(project_dir):
    p = project_dir / "PROJECT.md"
    m = re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", p.read_text(encoding="utf-8")) if p.exists() else None
    return m.group(1) if m else None


def main():
    seen = last_seen()
    now = datetime.now(timezone.utc).timestamp()
    total = 0

    for d in sorted((ROOT / "projects").iterdir()):
        if not d.is_dir():
            continue
        repo = repo_of(d)
        alive = dict(seen)
        if repo:
            for k, ts in branch_activity(repo).items():
                alive[k] = max(alive.get(k, 0), ts)

        # 1. захваты замолчавших инстансов
        f = d / "DISPATCH.md"
        if f.exists():
            kept, gone = [], []
            for b in blocks(f.read_text(encoding="utf-8")):
                m = re.search(WHO, b)
                if not m or not re.match(TS, b.strip()):
                    kept.append(b)
                    continue
                ts = alive.get((m.group(1), m.group(2)))
                silent = (now - ts) / 60 if ts else SILENT_MIN + 1
                (gone if silent > SILENT_MIN else kept).append(b)
            total += save(f, kept, gone, f"владелец молчит дольше {SILENT_MIN} мин")

        # 2. очередь CI: PR уже влит или закрыт
        f = d / "CI.md"
        if f.exists() and repo:
            kept, gone = [], []
            for b in blocks(f.read_text(encoding="utf-8")):
                m = re.search(r"/pull/(\d+)|PR #(\d+)", b)
                ts_m = re.match(TS, b.strip())
                if not ts_m:
                    kept.append(b)
                    continue
                if not m:
                    # строка про main: живёт не дольше трёх часов — прогон давно завершён
                    stamp = datetime.strptime(ts_m.group(1), "%d-%m-%Y %H:%M:%S")
                    age_h = (datetime.now() - stamp).total_seconds() / 3600
                    (gone if age_h > 3 else kept).append(b)
                    continue
                pr = gh(f"/repos/{repo}/pulls/{m.group(1) or m.group(2)}")
                (gone if pr and pr.get("state") == "closed" else kept).append(b)
            total += save(f, kept, gone, "PR уже влит или закрыт")

        # 3. журнал веток: ветки больше нет
        f = d / "BRANCHES.md"
        if f.exists() and repo:
            live = {b["name"] for b in (gh(f"/repos/{repo}/branches?per_page=100") or [])}
            kept, gone = [], []
            for b in blocks(f.read_text(encoding="utf-8")):
                m = re.search(r"`([^`]+)`", b)
                if not m or not re.match(TS, b.strip()):
                    kept.append(b)
                    continue
                (kept if m.group(1) in live else gone).append(b)
            total += save(f, kept, gone, "ветки больше нет")

    print("нечего убирать" if not total else f"итого убрано записей: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
