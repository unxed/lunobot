#!/usr/bin/env python3
"""Лог прогона песочницы/CI без управляющих последовательностей и меток времени (§ 7.5).

    python3 tools/run_log.py <owner/repo> <id прогона> [--job <подстрока имени>] [--grep <regex>] [--tail N]

`gh api .../jobs/<id>/logs` без `--allow-escape-sequences` отказывается печатать лог
(«the response contains terminal escape sequences»), а `gh run view --log` кладёт перед каждой
строкой «job<TAB>шаг<TAB>время»: пробы Wine/XDND (f4#566) три раза за круг чистились руками `sed`.
"""
import argparse
import re
import subprocess
import sys

ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
STAMP = re.compile(r"^﻿?\d{4}-\d\d-\d\dT[\d:.]+Z ?")


def clean(text):
    """Строки лога без ESC-последовательностей, BOM и метки времени GitHub."""
    return [STAMP.sub("", ESC.sub("", line)) for line in text.splitlines()]


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def job_text(repo, job_id):
    for flags in (["--allow-escape-sequences"], []):
        rc, out, err = gh("api", *flags, f"repos/{repo}/actions/jobs/{job_id}/logs")
        if rc == 0:
            return out
        if "escape" not in err and "unknown flag" not in err:
            break
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("run", type=int)
    ap.add_argument("--job", default="", help="подстрока имени job'а")
    ap.add_argument("--grep", default="", help="только строки, подходящие под regex")
    ap.add_argument("--tail", type=int, default=0, help="последние N строк")
    a = ap.parse_args(argv)
    rc, out, err = gh("api", f"repos/{a.repo}/actions/runs/{a.run}/jobs?per_page=100",
                      "--jq", r'.jobs[]|[.id,.name]|@tsv')
    if rc:
        sys.exit(f"jobs: {err.strip()}")
    pat = re.compile(a.grep) if a.grep else None
    for row in out.splitlines():
        job_id, name = row.split("\t", 1)
        if a.job not in name:
            continue
        text = job_text(a.repo, job_id)
        if text is None:
            print(f"== {name} ({job_id}): лог недоступен", file=sys.stderr)
            continue
        lines = [l for l in clean(text) if not pat or pat.search(l)]
        print(f"== {name} ({job_id})")
        print("\n".join(lines[-a.tail:] if a.tail else lines))


if __name__ == "__main__":
    main()
