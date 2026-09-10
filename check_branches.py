#!/usr/bin/env python3
"""Сверка журнала веток с GitHub.

Ветка под codex/ без записи в BRANCHES.md — утечка: кто-то завёл её мимо § 8.
Запись без ветки — незавершённая уборка. Ветки, названные иначе, заводит человек,
их проверка не касается.

Использование:
    python3 check_branches.py f4 [--repo unxed/f4]

Репозиторий берётся из projects/<проект>/PROJECT.md, если не задан явно.
Коды возврата: 0 — сходится, 1 — расхождения.
"""
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def gh_json(path):
    if shutil.which("gh"):
        out = subprocess.run(["gh", "api", path], capture_output=True, timeout=30)
        if out.returncode == 0:
            return json.loads(out.stdout)
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    project = args[0] if args else "f4"
    d = ROOT / "projects" / project
    repo = None
    if "--repo" in sys.argv:
        repo = sys.argv[sys.argv.index("--repo") + 1]
    elif (d / "PROJECT.md").exists():
        m = re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", (d / "PROJECT.md").read_text())
        repo = m.group(1) if m else None
    if not repo:
        print(f"не нашёл репозиторий проекта {project}")
        return 1

    journal = (d / "BRANCHES.md").read_text(encoding="utf-8") if (d / "BRANCHES.md").exists() else ""
    recorded = set(re.findall(r"`([^`]+)`", journal))
    real = {b["name"] for b in gh_json(f"/repos/{repo}/branches?per_page=100")
            if b["name"].startswith("codex/")}

    # ветка с открытым PR — не мусор: её доводят вместе с PR (§ 6)
    try:
        with_pr = {p["head"]["ref"] for p in gh_json(f"/repos/{repo}/pulls?state=open&per_page=100")}
    except Exception:
        with_pr = set()
    leaks, ghosts = sorted(real - recorded), sorted(recorded - real)
    if not leaks and not ghosts:
        print(f"{project}: веток Луноботов {len(real)}, все записаны")
        return 0
    for b in leaks:
        print(f"[утечка] ветка есть, записи нет: {b}")
        if b in with_pr:
            print("         с неё открыт PR — не удалять: доводится вместе с PR (§ 6).")
        else:
            print("         запись делается ДО создания ветки (§ 8). Твоя — допиши сейчас;")
            print("         чужая и при молчании владельца дольше 90 минут без PR — удаляй, владелец не вернётся.")
    for b in ghosts:
        print(f"[хвост]  запись есть, ветки нет: {b}")
        print("         ветку удалили — удали и запись; не дошёл до создания — доведи.")
        print("         запись при молчании владельца дольше 90 минут — мертва в любом случае, убирай.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"проверить не удалось: {e}")
        sys.exit(0)
