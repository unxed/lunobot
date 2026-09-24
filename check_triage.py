#!/usr/bin/env python3
"""Проверка полноты и свежести TRIAGE.md.

TRIAGE — кэш GitHub, а не источник истины. Этот гейт ловит именно тот случай,
когда новый открытый тикет не попал в кэш или строка осталась со старыми
счётчиком комментариев и updatedAt.

Использование:
    python3 check_triage.py f4 [--repo unxed/f4]

Коды возврата: 0 — кэш полностью совпадает с GitHub, 1 — есть расхождения.
"""
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROW = re.compile(
    r"^\|\s*(?P<number>\d+)\s*\|\s*(?P<priority>[^|]+?)\s*\|"
    r"\s*(?P<state>[^|]+?)\s*\|\s*(?P<comments>\d+)\s*\|"
    r"\s*(?P<updated>[^|]+?)\s*\|\s*$"
)


def gh_pages(path):
    """Получить все страницы endpoint через gh или обычный HTTP."""
    if shutil.which("gh"):
        result = subprocess.run(
            ["gh", "api", path, "--paginate", "--slurp"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            pages = json.loads(result.stdout)
            if not pages:
                return []
            if isinstance(pages[0], list):
                return [item for page in pages for item in page]
            return pages
        raise RuntimeError(result.stderr.strip() or "gh api завершился с ошибкой")

    items = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        url = f"https://api.github.com{path}{separator}page={page}"
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.loads(response.read())
        if not isinstance(batch, list):
            return batch
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def gh_one(path):
    """Получить один JSON-документ."""
    if shutil.which("gh"):
        result = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise RuntimeError(result.stderr.strip() or "gh api завершился с ошибкой")
    url = "https://api.github.com" + path
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def repository(project, explicit):
    if explicit:
        return explicit
    passport = ROOT / "projects" / project / "PROJECT.md"
    if not passport.exists():
        raise RuntimeError(f"не найден паспорт проекта: {passport}")
    match = re.search(r"https://github\.com/([\w.-]+/[\w.-]+)", passport.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(f"в паспорте нет ссылки на GitHub: {passport}")
    return match.group(1)


def read_triage(project):
    path = ROOT / "projects" / project / "TRIAGE.md"
    rows = {}
    malformed = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|") or line.startswith("| тикет") or set(line.strip()) <= {"|", "-", " ", ":"}:
            continue
        match = ROW.match(line)
        if not match:
            malformed.append(line_number)
            continue
        number = int(match.group("number"))
        if number in rows:
            malformed.append(line_number)
            continue
        rows[number] = {
            "priority": match.group("priority").strip(),
            "state": match.group("state").strip(),
            "comments": int(match.group("comments")),
            "updated": match.group("updated").strip(),
            "line": line_number,
        }
    return rows, malformed


def main():
    positional = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    project = positional[0] if positional else "f4"
    explicit = None
    if "--repo" in sys.argv:
        explicit = sys.argv[sys.argv.index("--repo") + 1]
    repo = repository(project, explicit)
    rows, malformed = read_triage(project)

    issues = gh_pages(f"/repos/{repo}/issues?state=open&per_page=100")
    open_issues = {item["number"]: item for item in issues if "pull_request" not in item}
    count = gh_one(f"/search/issues?q={urllib.parse.quote(f'repo:{repo} is:issue is:open')}&per_page=1")["total_count"]

    problems = []
    if count != len(open_issues):
        problems.append(f"список GitHub неполный: API вернул {len(open_issues)}, search насчитал {count}")
    for line in malformed:
        problems.append(f"TRIAGE.md:{line}: строка таблицы не распознана или повторяется")

    open_numbers = set(open_issues)
    recorded_numbers = set(rows)
    for number in sorted(open_numbers - recorded_numbers):
        issue = open_issues[number]
        problems.append(f"пропущен открытый тикет #{number}: {issue['title']}")
    for number in sorted(recorded_numbers - open_numbers):
        problems.append(f"в TRIAGE остался закрытый тикет #{number}")

    for number in sorted(open_numbers & recorded_numbers):
        issue = open_issues[number]
        row = rows[number]
        if row["comments"] != issue["comments"]:
            problems.append(
                f"#{number}: комментариев в TRIAGE {row['comments']}, GitHub сообщает {issue['comments']}"
            )
        if row["updated"] != issue["updated_at"]:
            problems.append(
                f"#{number}: updatedAt в TRIAGE {row['updated']}, GitHub сообщает {issue['updated_at']}"
            )

    print(f"{project}: открытых тикетов {len(open_issues)}, строк TRIAGE {len(rows)}")
    if not problems:
        print("TRIAGE полностью совпадает с GitHub")
        return 0
    for problem in problems:
        print(f"[расхождение] {problem}")
    print("Сначала исправьте/оцените эти тикеты по § 5.4; кэш нельзя считать снимком состояния.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"проверить TRIAGE не удалось: {error}", file=sys.stderr)
        sys.exit(2)
