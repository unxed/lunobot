#!/usr/bin/env python3
"""Release threshold check of LUNOBOT.md § 7.7 «Когда», read only, exit code 0 always.

For every project of projects/INDEX.md whose PROJECT.md has a line `- Релизы:` (not «нет»):
the last version tag (git ls-remote --tags --refs --sort=-v:refname, floating tags like nightly skipped),
the number of commits with a `Touch:` trailer in compare <tag>...main and the age of the tag.
Prints «кандидат на релиз» by threshold (б): >= 20 Touch commits, or >= 14 days and >= 1 Touch commit.
The list of releases is not the list of tags (zipper 21-10-2026: releases?per_page=10 gave v0.1.167, the tag was v0.1.178).
usage: python3 release_due.py [project ...]
"""
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION_TAG = re.compile(r"^v\d+(\.\d+)*(-[0-9A-Za-z.]+)?$")
TOUCH = re.compile(r"(?m)^Touch:")
MIN_TOUCH = 20
MAX_AGE_DAYS = 14


def projects():
    out = []
    with open(os.path.join(ROOT, "projects", "INDEX.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\d+\. \[([^\]]+)\]", line)
            if m:
                out.append(m.group(1))
    return out


def passport(project):
    """(owner/repo, releases line) from PROJECT.md, or (None, None)."""
    path = os.path.join(ROOT, "projects", project, "PROJECT.md")
    repo = rel = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^- Код: https://github\.com/([\w.-]+/[\w.-]+)", line)
                if m and repo is None:
                    repo = m.group(1)
                if line.startswith("- Релизы:") and rel is None:
                    rel = line[len("- Релизы:"):].strip()
    except FileNotFoundError:
        pass
    return repo, rel


def has_releases(rel):
    return bool(rel) and not re.match(r"^нет\b", rel)


def last_version_tag(refs):
    """refs: lines of `git ls-remote --tags --refs --sort=-v:refname` (newest first). The first version tag."""
    for line in refs:
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/tags/"):
            continue
        tag = parts[1][len("refs/tags/"):]
        if VERSION_TAG.match(tag):
            return tag
    return None


def due(touch, age_days):
    """Threshold (б) of § 7.7."""
    return touch >= MIN_TOUCH or (age_days >= MAX_AGE_DAYS and touch >= 1)


def gh_json(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def count_touch(repo, tag):
    n = total = 0
    page = 1
    while True:
        data = gh_json(f"repos/{repo}/compare/{tag}...main?per_page=100&page={page}")
        commits = data.get("commits", [])
        total = data.get("total_commits", total)
        n += sum(1 for c in commits if TOUCH.search(c["commit"]["message"]))
        if len(commits) < 100:
            return n, total
        page += 1


def tag_age_days(repo, tag, now):
    date = gh_json(f"repos/{repo}/commits/{tag}")["commit"]["committer"]["date"]
    t = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return (now - t).total_seconds() / 86400


def main(argv):
    now = datetime.datetime.now(datetime.timezone.utc)
    names = argv or projects()
    for p in names:
        repo, rel = passport(p)
        if repo is None or not has_releases(rel):
            continue
        try:
            refs = subprocess.check_output(
                ["git", "ls-remote", "--tags", "--refs", "--sort=-v:refname", f"https://github.com/{repo}"],
                text=True).splitlines()
            tag = last_version_tag(refs)
            if tag is None:
                print(f"{p} ({repo}): тегов версий нет — первый релиз по § 7.7")
                continue
            touch, total = count_touch(repo, tag)
            age = tag_age_days(repo, tag, now)
        except (subprocess.CalledProcessError, KeyError, ValueError) as e:
            print(f"{p} ({repo}): ошибка: {e}")
            continue
        verdict = "кандидат на релиз" if due(touch, age) else "рано"
        print(f"{p} ({repo}): последний тег {tag}, {age:.1f} сут, коммитов в main после него {total}, "
              f"с Touch: {touch} — {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
