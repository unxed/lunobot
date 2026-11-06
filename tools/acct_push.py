#!/usr/bin/env python3
"""Пуш уже сделанного коммита в учёт с повтором при гонке (§ 8).

    python3 tools/acct_push.py [--repo <клон учёта>] [--tries N]

Для правок, которые `acct_line.py` и `claims.py` не покрывают (`status/<N>.md`, `TRIAGE.md`,
`OWNER_QUEUE.md`, `HEALTH`-записи): после `git commit` вместо ручного «push отклонён —
pull --rebase — push». Каждая попытка: `git pull --rebase -q`, затем `git push -q`; отказ
из-за ушедшего вперёд `origin/main` — следующая попытка (до N, по умолчанию 5, пауза растёт).
Конфликт rebase не разрешается молча: rebase прерывается (`--abort`), код 1 и подсказка из § 8
(«возьми версию origin целиком и внеси правку заново»). Ничего, кроме rebase и push, скрипт
не делает: рабочее дерево должно быть чистым, а коммит — готовым (трейлер `Lunobot-Instance:`).
Перед пушем гоняется `check_owner_queue.py`, если среди коммитов, которые уйдут, есть
`OWNER_QUEUE.md` (§ 8: гейт после `pull --rebase` и до `push`).
Коды: 0 — запушено (или пушить нечего), 1 — конфликт rebase или все попытки отклонены, 2 — ошибка вызова.

Зачем: за 05-11-2026 три записи `push-race` в журнале (отказ пуша из-за параллельного коммита в
учёт, ручной повтор) подняли тревогу `friction-repeats`; повтор механический и не требует суждения.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    r.stdout = r.stdout.decode("utf-8", "replace")
    r.stderr = r.stderr.decode("utf-8", "replace")
    return r


def outgoing_files(repo):
    """Файлы коммитов, которые ещё не в origin/main."""
    r = git(repo, "diff", "--name-only", "origin/main...HEAD")
    return r.stdout.split() if r.returncode == 0 else []


def push_with_retry(repo, tries=5, sleep=time.sleep, log=print):
    for attempt in range(1, tries + 1):
        r = git(repo, "pull", "--rebase", "-q")
        if r.returncode:
            git(repo, "rebase", "--abort")
            log("конфликт rebase: " + (r.stderr.strip() or r.stdout.strip()).splitlines()[-1]
                + "\nвозьми версию origin целиком (git reset --hard origin/main) и внеси правку заново (§ 8)")
            return 1
        if "OWNER_QUEUE.md" in outgoing_files(repo):
            g = subprocess.run([sys.executable, os.path.join(HERE, "check_owner_queue.py")],
                               cwd=repo, capture_output=True)
            if g.returncode:
                log("check_owner_queue.py:\n" + g.stdout.decode("utf-8", "replace") + g.stderr.decode("utf-8", "replace"))
                return 1
        r = git(repo, "push", "-q")
        if r.returncode == 0:
            log(f"запушено (попытка {attempt})")
            return 0
        log(f"push отклонён (попытка {attempt}/{tries}): {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '?'}")
        sleep(min(2 * attempt, 10))
    log("все попытки отклонены — повтори позже")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=ROOT)
    ap.add_argument("--tries", type=int, default=5)
    a = ap.parse_args(argv)
    if a.tries < 1:
        ap.error("--tries >= 1")
    if git(a.repo, "rev-parse", "--git-dir").returncode:
        print(f"{a.repo}: не клон git", file=sys.stderr)
        return 2
    if git(a.repo, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        print("рабочее дерево не чистое: закоммить правку (с трейлером Lunobot-Instance:) и повтори", file=sys.stderr)
        return 2
    return push_with_retry(a.repo, a.tries)


if __name__ == "__main__":
    sys.exit(main())
