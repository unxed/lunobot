#!/usr/bin/env python3
"""Проверка полноты и свежести TRIAGE.md.

TRIAGE — кэш GitHub, а не источник истины. Этот гейт ловит именно тот случай,
когда новый открытый тикет не попал в кэш или строка осталась со старыми
счётчиком комментариев и updatedAt.

Использование:
    python3 tools/check_triage.py f4 [--repo unxed/f4]

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

ROOT = Path(__file__).resolve().parent.parent  # the clone of the accounting repository (the scripts are in tools/)
ROW = re.compile(
    r"^\|\s*(?P<number>\d+)\s*\|\s*(?P<priority>[^|]+?)\s*\|"
    r"\s*(?P<state>[^|]+?)\s*\|\s*(?P<comments>\d+)\s*\|"
    r"\s*(?P<updated>[^|]+?)\s*\|\s*$"
)


GH_ATTEMPTS = 3
# Временные сетевые отказы gh: код возврата не нулевой, а stderr — сообщение Go-клиента.
TRANSIENT_GH_ERRORS = re.compile(
    r"TLS handshake timeout|i/o timeout|connection reset|unexpected EOF|"
    r"HTTP 50[234]|temporary failure in name resolution",
    re.IGNORECASE,
)


def run_gh(command, attempts=GH_ATTEMPTS, timeout=60):
    """subprocess.run для gh с повтором при тайм-ауте и временном сетевом отказе: один запрос не должен валить весь гейт.

    Гейты по всем проектам идут параллельно (§ 4 п. 2), и при нагрузке одиночный запрос gh
    может не уложиться в минуту (17-10-2026: check_try.py f4 упал на одном комментарии из 82)
    или получить `TLS handshake timeout` с кодом возврата 1 (круг 17-10-2026, check_try.py f4:
    тот же гейт отвечал «не удалось проверить» вместо результата).
    """
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            if attempt == attempts:
                raise
            continue
        if result.returncode != 0 and attempt < attempts and TRANSIENT_GH_ERRORS.search(result.stderr or ""):
            continue
        return result
    raise AssertionError("недостижимо")


def gh_pages_by_number(path, expected_count=None):
    """Все страницы через gh api с явным page=N, не доверяя заголовку Link."""
    items = []
    page = 1
    empty_attempts = 0
    while True:
        parts = urllib.parse.urlsplit(path)
        query = [(key, value) for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                 if key != "page"]
        query.append(("page", str(page)))
        page_path = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path,
                                             urllib.parse.urlencode(query), parts.fragment))
        result = run_gh(["gh", "api", page_path])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "gh api завершился с ошибкой")
        batch = json.loads(result.stdout)
        if not isinstance(batch, list):
            return batch
        if not batch:
            if expected_count is not None and len(items) < expected_count and empty_attempts < GH_ATTEMPTS - 1:
                empty_attempts += 1
                continue
            return items
        items.extend(batch)
        empty_attempts = 0
        if expected_count is not None and len(items) >= expected_count:
            return items
        page += 1


def gh_pages(path, expected_count=None):
    """Получить все страницы endpoint через gh или обычный HTTP."""
    if shutil.which("gh"):
        result = run_gh(["gh", "api", path, "--paginate", "--slurp"])
        if result.returncode == 0:
            pages = json.loads(result.stdout)
            if not pages:
                return gh_pages_by_number(path, expected_count) if expected_count else []
            if all(isinstance(page, list) for page in pages):
                # GitHub CLI can follow a cursor URL that returns an empty page even
                # though explicit numeric pages still contain results. Never accept
                # an empty page after data as proof that pagination is complete.
                if any(not page for page in pages[1:]):
                    return gh_pages_by_number(path, expected_count)
                items = [item for page in pages for item in page]
                if expected_count is not None and len(items) != expected_count:
                    return gh_pages_by_number(path, expected_count)
                return items
            return pages
        # Прокси некоторых сред (Claude Code в облаке) запрещает числовые пути
        # repositories/{id}, на которые gh --paginate переходит по заголовку
        # Link. Тогда страницы берём по одной, без заголовка.
        if "repositories/" in result.stderr or "proxy" in result.stderr:
            return gh_pages_by_number(path, expected_count)
        raise RuntimeError(result.stderr.strip() or "gh api завершился с ошибкой")

    items = []
    page = 1
    empty_attempts = 0
    while True:
        parts = urllib.parse.urlsplit(path)
        query = [(key, value) for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                 if key != "page"]
        query.append(("page", str(page)))
        url = urllib.parse.urlunsplit(("https", "api.github.com", parts.path,
                                       urllib.parse.urlencode(query), parts.fragment))
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.loads(response.read())
        if not isinstance(batch, list):
            return batch
        if not batch:
            if expected_count is not None and len(items) < expected_count and empty_attempts < GH_ATTEMPTS - 1:
                empty_attempts += 1
                continue
            return items
        items.extend(batch)
        empty_attempts = 0
        if expected_count is not None and len(items) >= expected_count:
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


def open_issues_snapshot(repo, path):
    """Read a complete issues endpoint, cross-checking both GitHub totals.

    The repository counter includes open PRs, as does /issues; Search counts only
    issues. If either check disagrees, retry with numeric pages and fail closed if
    the discrepancy remains, so an unavailable page cannot mark TRIAGE rows closed.
    """
    repository_count = gh_one(f"/repos/{repo}")["open_issues_count"]
    issues = gh_pages(path, expected_count=repository_count)
    try:
        search_count = gh_one(
            f"/search/issues?q={urllib.parse.quote(f'repo:{repo} is:issue is:open')}&per_page=1"
        )["total_count"]
    except RuntimeError as error:
        # Search API can be unavailable behind some proxies; repository metadata
        # plus the complete /issues list still provide an independent check.
        if not re.search(r"proxy|repositories/", str(error), re.IGNORECASE):
            raise
        search_count = None

    if not isinstance(issues, list):
        raise RuntimeError("GitHub issues endpoint returned a non-list response")
    open_issues = {item["number"]: item for item in issues if "pull_request" not in item}

    if (len(issues) != repository_count or len({item["number"] for item in issues}) != repository_count
            or (search_count is not None and len(open_issues) != search_count)):
        issues = gh_pages_by_number(path, expected_count=repository_count)
        if not isinstance(issues, list):
            raise RuntimeError("numeric issue pages returned a non-list response")
        open_issues = {item["number"]: item for item in issues if "pull_request" not in item}
        if (len(issues) != repository_count
                or len({item["number"] for item in issues}) != repository_count):
            raise RuntimeError(
                f"неполный список issues: репозиторий сообщает {repository_count}, "
                f"явные страницы вернули {len(issues)}"
            )
    return open_issues


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

    issues_path = f"/repos/{repo}/issues?state=open&per_page=100"
    open_issues = open_issues_snapshot(repo, issues_path)

    problems = []
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
    print("Сначала исправьте/оцените эти тикеты по § 5 п. 4; кэш нельзя считать снимком состояния.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"проверить TRIAGE не удалось: {error}", file=sys.stderr)
        sys.exit(2)
