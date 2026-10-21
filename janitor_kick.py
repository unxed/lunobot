#!/usr/bin/env python3
"""Пинок janitor.yml: запустить уборку и пульс, если они давно не шли (EVOLUTION.md, 21-10-2026, «janitor
по пинку флота»; unxed/lunobot#230).

    python3 janitor_kick.py [--repo DIR] [--min-age MIN] [--dry-run]

`cron: '*/10 * * * *'` в janitor.yml GitHub исполняет как попало: 17–21-10-2026 прогоны шли раз в 2–5 часов,
а после перевода захватов на ref (13:03Z) и пульса (13:43Z) — ни одного за три часа. Пока janitor стоит,
протухшие захваты держат задачи, а `HEALTH.md` не пишется. Поэтому каждый работающий бот пинает его сам:
`claims.py take|drop` и `release.py` вызывают этот скрипт фоном. Пинок — `workflow_dispatch`, только если
последний прогон janitor.yml начался больше `--min-age` минут назад (10) и не идёт сейчас: не чаще шести
прогонов в час на весь флот (лимит `GITHUB_TOKEN` — 1000 запросов в час на репозиторий). Писатель учёта
остаётся один — Actions; cron остаётся страховкой на время, когда ботов нет.

Тихо ничего не делает, если `LUNOBOT_NO_KICK=1`, `origin` — не GitHub (тесты, локальные bare-репозитории),
нет `gh` или GitHub ответил ошибкой (например, прокси облачной сессии): пинок — не шаг бота и не должен его
ломать. Код возврата всегда 0.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKFLOW = "janitor.yml"
MIN_AGE = 10


def slug(repo):
    """owner/name учётного репозитория по `origin`, или None (не GitHub)."""
    r = subprocess.run(["git", "-C", repo, "remote", "get-url", "origin"], capture_output=True, text=True)
    m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?/?$", r.stdout.strip()) if r.returncode == 0 else None
    return m.group(1) if m else None


def due(runs, now, min_age=MIN_AGE):
    """Нужен ли пинок: нет прогонов или последний начался давно и уже завершён."""
    if not runs:
        return True
    last = runs[0]
    if last.get("status") != "completed":
        return False
    started = datetime.strptime(last["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (now - started).total_seconds() / 60 >= min_age


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)


def kick(repo=HERE, min_age=MIN_AGE, dry=False, now=None):
    """Пнуть janitor.yml, если пора. Возвращает строку о том, что сделано (для лога)."""
    if os.environ.get("LUNOBOT_NO_KICK") == "1":
        return "выключено LUNOBOT_NO_KICK"
    name = slug(repo)
    if not name:
        return "origin — не GitHub"
    try:
        r = gh("api", f"repos/{name}/actions/workflows/{WORKFLOW}/runs?per_page=1")
        if r.returncode:
            return f"не прочитать прогоны: {r.stderr.strip()[:120]}"
        runs = json.loads(r.stdout).get("workflow_runs", [])
        if not due(runs, now or datetime.now(timezone.utc), min_age):
            return "рано: последний прогон свежий или идёт"
        if dry:
            return "пнул бы"
        r = gh("api", "-X", "POST", f"repos/{name}/actions/workflows/{WORKFLOW}/dispatches", "-f", "ref=main")
        return "пнул" if r.returncode == 0 else f"пинок отклонён: {r.stderr.strip()[:120]}"
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        return f"сбой: {e}"


def spawn(repo=HERE):
    """Пнуть фоном, не задерживая вызвавший скрипт (claims.py, release.py)."""
    if os.environ.get("LUNOBOT_NO_KICK") == "1" or not slug(repo):
        return
    try:
        subprocess.Popen([sys.executable, os.path.join(HERE, "janitor_kick.py"), "--repo", repo],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError:
        pass


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=HERE, help="клон учёта (по умолчанию каталог скрипта)")
    ap.add_argument("--min-age", type=int, default=MIN_AGE, help="минут с начала последнего прогона")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    print("janitor_kick:", kick(a.repo, a.min_age, a.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
