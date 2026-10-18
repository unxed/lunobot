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
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gh_post import check_text

ROOT = Path(__file__).resolve().parent
SILENT_MIN = 90
# Строка захвата, которую никто не продлевал дольше этого срока, снимается и на живом узле:
# живость узла (ниже) не отличает бота от воркера, умершего давно (16-10-2026: четыре строки
# 3–6 часов висели, пока на узле работал другой бот).
HARD_SILENT_MIN = 240
# Срочный захват по § 5 п. 2 («красный staging», «красный main», «застой main») держит весь конвейер, поэтому его срок короче: 18-10-2026
# захват «красный staging f4» воркера, умершего в 18:31, жил бы до 22:31 (узел живой), хотя причина — одна строка — была известна в 19:11,
# а порог инцидента процесса — два часа. Воркер, который чинит дольше, продлевает строку keepalive («работаю над …», § 8).
URGENT_SILENT_MIN = 45
URGENT_MARK = "по § 5 п. 2"
TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
WHO = r"Лунобот-(\d+) \((?:instance|node) ([0-9a-f]+); ([A-Z]{3})(?:; [^)]*)?\)"
DRY = "--dry-run" in sys.argv


def gh(path):
    if shutil.which("gh"):
        try:
            result = subprocess.run(["gh", "api", path], capture_output=True, text=True,
                                    timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
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


def gh_all(path):
    """Все страницы списка; None означает ошибку доступа, а не пустой список."""
    if shutil.which("gh"):
        try:
            result = subprocess.run(["gh", "api", "--paginate", "--slurp", path],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return [item for page in json.loads(result.stdout) for item in page]
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    items = []
    for page in range(1, 100):
        separator = "&" if "?" in path else "?"
        batch = gh(f"{path}{separator}page={page}")
        if not isinstance(batch, list):
            return None
        items.extend(batch)
        if len(batch) < 100:
            return items
    return None


def last_seen():
    """Когда каждый инстанс последний раз что-либо коммитил."""
    recent = subprocess.run(
        ["git", "log", "--since=12 hours ago",
         "--format=@@LUNOBOT-COMMIT@@%ct%x09%(trailers:key=Lunobot-Instance,valueonly)"],
        cwd=ROOT, capture_output=True, text=True).stdout
    legacy = subprocess.run(
        ["git", "log", "--since=12 hours ago",
         "--format=@@LUNOBOT-COMMIT@@%ct%x09%(trailers:key=Lunobot-Instance,valueonly)",
         "-p", "--", "projects"],
        cwd=ROOT, capture_output=True, text=True).stdout
    seen, when, explicit_actor = {}, None, False
    for line in recent.splitlines():
        marker = re.match(r"@@LUNOBOT-COMMIT@@(\d+)\t(.*)", line)
        if not marker:
            continue
        actor = re.search(WHO, marker.group(2))
        if actor:
            key = (actor.group(1), actor.group(2))
            seen[key] = max(seen.get(key, 0), int(marker.group(1)))
    for line in legacy.splitlines():
        marker = re.match(r"@@LUNOBOT-COMMIT@@(\d+)\t(.*)", line)
        if marker:
            when = int(marker.group(1))
            actor = re.search(WHO, marker.group(2))
            explicit_actor = actor is not None
            if actor:
                key = (actor.group(1), actor.group(2))
                seen[key] = max(seen.get(key, 0), when)
            continue
        if not when or explicit_actor or not line.startswith("+") or line.startswith("+++"):
            continue
        m = re.search(WHO, line)
        if m:
            key = (m.group(1), m.group(2))
            seen[key] = max(seen.get(key, 0), when)
    return seen


def branch_activity(repo, branches):
    """Последний пуш в каждую ветку lunobot/* — второй источник живости: бот, который пишет
    код, пушит в свою ветку постоянно, даже если учёт не трогает."""
    out = {}
    for b in branches:
        name = b["name"]
        if not name.startswith("lunobot/"):
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


def row_key(block):
    """Ключ захвата: ссылка на тикет/PR либо описание кастомной задачи в «ёлочках»."""
    m = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", block) or \
        re.search(r"«[^»]+»", block)
    return m.group(0) if m else None


def hard_stale(blocks_, now):
    """Блоки захватов, чей ключ не продлевался дольше HARD_SILENT_MIN минут (метки — UTC, § 8);
    для срочных по § 5 п. 2 — дольше URGENT_SILENT_MIN.
    Продление — любая более поздняя строка с тем же ключом (keepalive «работаю над …»)."""
    latest = {}
    urgent = set()
    for b in blocks_:
        ts_m = re.match(TS, b.strip())
        key = row_key(b)
        if not ts_m or not key:
            continue
        ts = datetime.strptime(ts_m.group(1), "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=timezone.utc).timestamp()
        latest[key] = max(latest.get(key, 0), ts)
        if URGENT_MARK in b:
            urgent.add(key)
    def limit(key):
        return URGENT_SILENT_MIN if key in urgent else HARD_SILENT_MIN

    # строка с припаркованным коммитом (§ 1) живёт, пока коммит не приземлят
    return [b for b in blocks_
            if re.search(WHO, b) and "припаркован" not in b and row_key(b) in latest
            and (now - latest[row_key(b)]) / 60 > limit(row_key(b))]


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

    index = (ROOT / "projects" / "INDEX.md").read_text(encoding="utf-8")
    for name in re.findall(r"^\d+\.\s*\[([^\]]+)\]", index, re.M):
        d = ROOT / "projects" / name
        repo = repo_of(d)
        if not repo:
            continue
        remote_branches = gh_all(f"/repos/{repo}/branches?per_page=100")
        if remote_branches is None:
            print(f"{repo}: нет доступа к веткам, уборка проекта пропущена", file=sys.stderr)
            continue
        alive = dict(seen)
        for k, ts in branch_activity(repo, remote_branches).items():
            alive[k] = max(alive.get(k, 0), ts)

        # 1. захваты замолчавших инстансов
        f = d / "DISPATCH.md"
        if f.exists():
            kept, gone = [], []
            all_blocks = blocks(f.read_text(encoding="utf-8"))
            stale = hard_stale(all_blocks, now)
            for b in all_blocks:
                m = re.search(WHO, b)
                if not m or not re.match(TS, b.strip()):
                    kept.append(b)
                    continue
                if any(b is s_ for s_ in stale):
                    gone.append(b)
                    continue
                # живость — по узлу, а не по номеру: при смене номера (= смене модели, § 4)
                # захваты узла переписываются под новый id, и старый номер не значит «мёртв»
                ts = max((t for (num_, node_), t in alive.items() if node_ == m.group(2)),
                         default=None)
                silent = (now - ts) / 60 if ts else SILENT_MIN + 1
                (gone if silent > SILENT_MIN else kept).append(b)
            total += save(f, kept, gone, f"владелец молчит дольше {SILENT_MIN} мин или строку не "
                          f"продлевали дольше {HARD_SILENT_MIN} мин ({URGENT_SILENT_MIN} мин у срочных по § 5 п. 2)")

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
            live = {b["name"] for b in remote_branches}
            kept, gone = [], []
            for b in blocks(f.read_text(encoding="utf-8")):
                m = re.search(r"`([^`]+)`", b)
                if not m or not re.match(TS, b.strip()):
                    kept.append(b)
                    continue
                (kept if m.group(1) in live else gone).append(b)
            total += save(f, kept, gone, "ветки больше нет")

        # 4. комментарии, дошедшие до GitHub кашей из «?» (кодировка сломалась по дороге)
        mojibake(d, repo)

    print("нечего убирать" if not total else f"итого убрано записей: {total}")
    return 0


MOJIBAKE_DAYS = 7


def trusted_author():
    """Логин, под которым боты пишут на GitHub: строка «Автор доверенных тикетов» в OWNER_QUEUE.md.

    Править можно только свои тексты: текст человека («???????» в тикете о порче кодировки,
    unxed/f4#2057, 18-10-2026) исказили не боты, и чинить его нельзя. Нет файла или строки — None
    (фильтра нет)."""
    try:
        text = (Path(__file__).resolve().parent / "OWNER_QUEUE.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^Автор доверенных тикетов:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def body_rows(repo, since, author=None):
    """Испорченные тела тикетов и PR, обновлённых за окно (`issues` отдаёт и PR).

    Тело тикета или PR портится тем же путём, что и комментарий (однобайтовая кодовая
    страница, «?» вместо букв), а сканировались только комментарии. Ловится только то, что
    ловит `check_text`. Повод — описание PR unxed/goWidgets#15, но испорчено оно иначе:
    shell подставил содержимое обратных кавычек (на их месте пустые места), а не «?»; такой
    сбой эта проверка НЕ находит — от него защищает отправка через `gh_post.py` (сверка с файлом).
    """
    items = gh_all(f"/repos/{repo}/issues?state=all&since={since}&per_page=100")
    if items is None:
        print(f"{repo}: нет доступа к тикетам, проверка тел пропущена", file=sys.stderr)
        return []
    rows = []
    for it in items:
        if it.get("user", {}).get("type") == "Bot":
            continue
        if author and it.get("user", {}).get("login") != author:
            continue
        reason = check_text(it.get("body") or "")
        if not reason or reason == "текст пуст":
            continue
        if "pull_request" in it:
            fix = f"`gh_post.py pr-body {repo} {it['number']} <файл>`"
        else:
            fix = f"`gh_post.py issue-body {repo} {it['number']} <файл>`"
        rows.append(f"- {it['html_url']} (#{it['number']}, тело тикета/PR, "
                    f"{it['user']['login']}, {it.get('updated_at')}): {reason}; чинить: {fix}")
    return rows


def mojibake(project_dir, repo):
    """Свежие комментарии, которые гейт gh_post.py отклонил бы, — в MOJIBAKE.md проекта.

    Файл переписывается целиком на каждом проходе: восстановил комментарий правкой
    (`gh_post.py edit`) — на следующем проходе строка пропала, пропали все — пропал файл.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=MOJIBAKE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    comments = gh_all(f"/repos/{repo}/issues/comments?since={since}&per_page=100")
    if comments is None:
        print(f"{repo}: нет доступа к комментариям, проверка кодировки пропущена", file=sys.stderr)
        return
    author = trusted_author()
    rows = []
    for c in comments:
        if c.get("user", {}).get("type") == "Bot":
            continue
        if author and c.get("user", {}).get("login") != author:
            continue
        reason = check_text(c.get("body") or "")
        if reason and reason != "текст пуст":
            rows.append(f"- {c['html_url']} (id {c['id']}, {c['user']['login']}, "
                        f"{c['created_at']}): {reason}")
    rows += body_rows(repo, since, author)
    f = project_dir / "MOJIBAKE.md"
    if not rows:
        if f.exists():
            f.unlink()
            print(f"{f.name}: испорченных комментариев больше нет, файл убран")
        return
    text = (f"# Испорченные комментарии в {repo}\n\n"
            "Пишет janitor (`janitor.py`, шаг 4). Эти комментарии дошли до GitHub с «?» на месте "
            "букв. Восстанови текст правкой того же комментария через `gh_post.py edit "
            f"{repo} <id> <файл>`, а строки «тело тикета/PR» — через `gh_post.py pr-body` "
            "или `gh_post.py issue-body` (команда указана в строке), по ASCII-остову, "
            "соседним сообщениям и учёту — "
            "строка пропадёт на следующем проходе janitor. LUNOBOT.md § 2.\n\n"
            + "\n".join(rows) + "\n")
    if not f.exists() or f.read_text(encoding="utf-8") != text:
        f.write_text(text, encoding="utf-8")
        print(f"{f.name}: испорченных комментариев {len(rows)}")


if __name__ == "__main__":
    sys.exit(main())
