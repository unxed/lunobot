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
        print(f"GitHub недоступен: {e}", file=sys.stderr)
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


def effective_now(marks, scope="projects"):
    """Сейчас — в тех же часах, в которых пишут боты.

    Боты пишут время в своих поясах, поэтому сравнивать их метки с UTC нельзя.
    Перекос считаем по последнему коммиту учётного репозитория: его реальное время
    известно, а самая свежая метка в файлах ему примерно соответствует.
    """
    if not marks:
        return datetime.now()
    newest = max(marks)
    try:
        # ориентируемся на последний коммит именно ботов: правки инструкции
        # в счёт не идут, иначе перекос обнулится от любого патча
        ct = int(subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(scope)],
                                cwd=ROOT, capture_output=True, text=True,
                                timeout=30).stdout.strip())
        elapsed = datetime.now(timezone.utc).timestamp() - ct
    except Exception:
        elapsed = 0
    return newest + timedelta(seconds=max(elapsed, 0))


def read_lines(path):
    """Строки файла. Боты иногда пишут литеральный \n вместо перевода строки — разрезаем и его."""
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").replace("\\n", "\n")
    return [l.strip() for l in raw.splitlines() if l.strip()]


def active_claims(project_dir):
    """Кто что держит прямо сейчас, по DISPATCH.md."""
    holders = {}
    for line in read_lines(project_dir / "DISPATCH.md"):
        ts = re.match(TS, line)
        who = re.search(r"Лунобот-(\d+) \((?:instance|node) ([0-9a-f]+); ([A-Z]{3})\)", line)
        if not (ts and who) or not re.search(r"взял|работаю", line):
            continue
        key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", line)
        key = key.group(0) if key else None
        if not key:
            custom = re.search(r"«([^»]+)»", line) or re.search(
                r"кастомную задачу,\s*([^(]+)", line)
            key = f"«{custom.group(1).strip()}»" if custom else line[:40]
        part = re.search(r"часть (\d+) из (\d+)", line)
        part_txt = ""
        if part and part.group(2) != "1":
            part_txt = f"часть {part.group(1)} из {part.group(2)}"
        full = key + (part.group(0) if part else "")
        stamp = datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S")
        prev = holders.get(full)
        if not prev or stamp > prev[0]:
            origin = re.search(r"по (§ ?[\d. п]*\d)", line)
            holders[full] = (stamp,
                             f"Лунобот-{who.group(1)} ({who.group(2)[:8]}…; {who.group(3)})",
                             origin.group(1).strip() if origin else "", part_txt, key)
    return [(k, *v) for k, v in holders.items()]


RUN_NUMBERS = {}

# PR, которые правили только служебные записи бота в репозитории проекта. Их вообще
# не должно было быть (§ 14.4), они остались от старых правил — и это чистый инфошум.
SERVICE_PR = re.compile(
    r"(?i)^(docs?|chore)\s*:\s*(record|track|refresh|finalize|reconcile|correct|update)\b"
    r"|branch inventory|lunobot (branch|slice)|^record .*\bstatus\b")


def shorten(text, repo):
    """Длинные ссылки и хеши → короткие подписи со ссылками."""
    if not repo:
        return text
    r = re.escape(repo)

    def run_no(run_id):
        if run_id not in RUN_NUMBERS:
            data = gh_json(f"/repos/{repo}/actions/runs/{run_id}") or {}
            RUN_NUMBERS[run_id] = data.get("run_number") or run_id
        return RUN_NUMBERS[run_id]

    text = re.sub(rf"https://github\.com/{r}/commit/([0-9a-f]{{7,40}})",
                  lambda m: f"[`{m.group(1)[:7]}`]({m.group(0)})", text)
    text = re.sub(rf"https://github\.com/{r}/issues/(\d+)",
                  lambda m: f"[#{m.group(1)}]({m.group(0)})", text)
    text = re.sub(rf"https://github\.com/{r}/pull/(\d+)",
                  lambda m: f"[PR #{m.group(1)}]({m.group(0)})", text)
    text = re.sub(rf"https://github\.com/{r}/actions/runs/(\d+)",
                  lambda m: f"[прогон #{run_no(m.group(1))}]({m.group(0)})", text)
    text = re.sub(r"\b(?:GitHub Actions\s+)?run\s+(\d{6,})\b",
                  lambda m: f"[прогон #{run_no(m.group(1))}]"
                            f"(https://github.com/{repo}/actions/runs/{m.group(1)})", text)
    text = re.sub(r"\b([0-9a-f]{40})\b",
                  lambda m: f"[`{m.group(1)[:7]}`](https://github.com/{repo}/commit/{m.group(1)})", text)
    text = re.sub(r"[:,]?\s*(запущен|GitHub Actions)[^.]*результат не проверен\.?", "", text)
    text = re.sub(r"\bPR\s+(\[PR #)", r"\1", text)          # «PR [PR #1008]» → «[PR #1008]»
    text = re.sub(r"\b(?:commit|коммит)\s+(\[`)", r"коммит \1", text)
    return re.sub(r"\s+,", ",", text).strip()


def instances(hours=24, silent_min=30):
    """Кто из инстансов когда в последний раз наследил в учётном репозитории.

    Отдельного heartbeat не заводим: каждый коммит бота содержит его id, поэтому
    «последний раз отвечал» берётся из git-истории. Инстанс, замолчавший надолго,
    виден, даже когда за ним не числится ни одного захвата, — а это как раз тот
    промежуток между шагами, в котором он до сих пор был невидим.
    """
    try:
        out = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--format=%n@%ct", "-p", "--", "projects"],
            cwd=ROOT, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return []
    seen, when = {}, None
    for line in out.splitlines():
        if line.startswith("@") and line[1:].isdigit():
            when = int(line[1:])
            continue
        m = re.search(r"Лунобот-(\d+) \((?:instance|node) ([0-9a-f]{6,}); ([A-Z]{3})\)", line)
        if m and when:
            who = f"Лунобот-{m.group(1)} ({m.group(2)[:8]}…; {m.group(3)})"
            seen[who] = max(seen.get(who, 0), when)
    now = datetime.now(timezone.utc).timestamp()
    out = []
    for who, ts in sorted(seen.items(), key=lambda x: -x[1]):
        node = re.search(r"\(([0-9a-f]+)…", who)
        out.append({"who": who, "node": node.group(1) if node else "",
                    "mins": int((now - ts) // 60)})
    return out


def pending_nodes():
    """Узлы, за которыми ещё что-то числится в учёте."""
    text = ""
    for p in (ROOT / "projects").glob("*/*.md"):
        text += p.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"[0-9a-f]{24}", text))


def instances_block(silent_min=30, forget_min=180):
    """Живые инстансы и те, за кем остался хвост.

    Мёртвый инстанс, за которым ничего не числится, показывать незачем: он бы висел
    в списке сутками и превращал предупреждение в фон.
    """
    pending = pending_nodes()
    items = []
    for i in instances():
        has_tail = any(n.startswith(i["node"].rstrip("…")) for n in pending)
        if i["mins"] >= forget_min and not has_tail:
            continue
        if i["mins"] < silent_min:
            items.append(f"{i['who']} — последний след {i['mins']} мин назад")
        elif has_tail:
            items.append(f"{i['who']} — молчит {i['mins']} мин, и за ним ещё числится работа")
        else:
            items.append(f"{i['who']} — молчит {i['mins']} мин, хвостов не осталось")
    return items


def fleet_line(silent_min=30):
    inst = [i for i in instances() if i["mins"] < 180]
    if not inst:
        return ""
    alive = [i for i in inst if i["mins"] < silent_min]
    if not alive:
        return (f"Флот стоит: молчат все {len(inst)} инстансов. "
                "Перезапусти воркеров — брошенные шаги они подберут сами по таймауту.")
    return f"Флот: работают {len(alive)} из {len(inst)}."


def ci_line(raw, repo, now=None):
    """Запись о прогоне — к одному виду, что бы бот туда ни написал."""
    stamp = re.search(r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})", raw)
    abandoned = ""
    if stamp and now:
        age = int((now - datetime.strptime(stamp.group(1), "%d-%m-%Y %H:%M:%S")).total_seconds() // 60)
        if age >= STALE_MIN:
            abandoned = f"  ⚠ брошен {age} мин назад"
    # id узла выкидываем до разбора, иначе он сойдёт за хеш коммита
    raw = re.sub(r"\(?(?:node|instance) [0-9a-f]{6,}; [A-Z]{3}\)?", "", raw)
    raw = re.sub(r"Я Лунобот-\d+\s*,?", "", raw)
    time = re.search(r"\d{2}-\d{2}-\d{4} (\d{2}:\d{2})", raw)
    pr = re.search(r"/pull/(\d+)", raw) or re.search(r"PR #(\d+)", raw)
    sha = re.search(r"комм(?:ит|ита)\s*`?([0-9a-f]{7,40})`?", raw) or \
        re.search(r"\b([0-9a-f]{7,40})\b", raw)
    run = re.search(r"/actions/runs/(\d+)|\brun (\d{6,})\b", raw)
    run_no = re.search(r"прогон #(\d+)", raw)
    if not (pr and (run or run_no)):
        # не разобрали — хотя бы уберём длинный id узла, он тут ни к чему
        return re.sub(r"\(node ([0-9a-f]{8})[0-9a-f]+; ([A-Z]{3})\)", r"(\1…; \2)",
                      shorten(raw, repo)) + abandoned
    run_id = (run.group(1) or run.group(2)) if run else None
    parts = [time.group(1) if time else "",
             f"[PR #{pr.group(1)}](https://github.com/{repo}/pull/{pr.group(1)})"]
    if sha:
        parts.append(f"[`{sha.group(1)[:7]}`](https://github.com/{repo}/commit/{sha.group(1)})")
    parts.append(shorten(f"run {run_id}", repo) if run_id
                 else f"[прогон #{run_no.group(1)}](https://github.com/{repo}/actions)")
    return " · ".join(p for p in parts if p) + abandoned


def report(name, repo, d, hours):
    """Возвращает список блоков (заголовок, строки) — рендер отдельно."""
    blocks = []

    claims = active_claims(d)
    items = []
    if not claims:
        items.append("Никто ничего не держит.")
    else:
        now = effective_now([c[1] for c in claims], d.relative_to(ROOT) if str(d).startswith(str(ROOT)) else "projects")
        for _full, stamp, who, origin, part_txt, key in sorted(claims, key=lambda c: c[1]):
            age = int((now - stamp).total_seconds() // 60)
            mark = "  ⚠ протух" if age > STALE_MIN else ""
            head = " · ".join(x for x in (shorten(key, repo), part_txt, origin) if x)
            items.append(f"{head} — {who}, {age} мин{mark}")
    stale = [i for i in items if "протух" in i]
    blocks.append(("В работе", items,
                   "Протухший захват освободится сам: его снимет любой бот в начале круга. "
                   "Если стоит весь флот — перезапусти воркеров, руками чистить нечего."
                   if stale else ""))

    pending = [l for l in read_lines(d / "CI.md") if "http" in l or "run " in l]
    # время берём из самой свежей записи учёта: боты пишут в своих часовых поясах
    marks = [datetime.strptime(m.group(1), "%d-%m-%Y %H:%M:%S")
             for m in (re.search(r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})", l) for l in
                       read_lines(d / "DISPATCH.md") + pending) if m]
    ci_now = effective_now(marks, d.relative_to(ROOT) if str(d).startswith(str(ROOT)) else "projects")
    if pending:
        ci_items = [ci_line(l, repo, ci_now) for l in pending[:10]]
        blocks.append((f"Непроверенные прогоны CI: {len(pending)}", ci_items,
                       "Брошенный прогон разбирает любой бот (§ 14.2): зелёный — довести шаг "
                       "и влить PR, красный — в очередь. Самому посмотреть: `gh run view <номер>`."
                       if any("брошен" in i for i in ci_items) else ""))

    if not repo:
        blocks.append(("GitHub", ["В паспорте проекта нет ссылки на репозиторий."]))
        return blocks

    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    done = gh_json(f"/search/issues?q=repo:{repo}+is:pr+is:merged+merged:>={since}&per_page=50")
    groups, loose, hidden = {}, [], 0
    if done and done.get("items"):
        for pr in done["items"]:
            if SERVICE_PR.search(pr["title"]):
                hidden += 1
                continue
            found = re.findall(r"#(\d+)", pr["title"] + " " + (pr.get("body") or "")[:400])
            issues = [n for n in dict.fromkeys(found) if n != str(pr["number"])]
            entry = (pr["number"], pr["html_url"], pr["title"][:70])
            if issues:
                groups.setdefault(issues[0], []).append(entry)
            else:
                loose.append(entry)

    items = []
    # ключ строки — тикет, по нему и сортируем: от новых номеров к старым
    for issue, prs in sorted(groups.items(), key=lambda g: -int(g[0])):
        prs.sort(key=lambda p: -p[0])
        head = f"[#{issue}](https://github.com/{repo}/issues/{issue})"
        # номер тикета уже стоит слева — из заголовка PR его убираем
        title = re.sub(rf"\s*\(#{issue}\)|^#{issue}\s+", "", prs[0][2]).strip()
        first = f"[PR #{prs[0][0]}]({prs[0][1]}) {title}"
        line = f"{head} → {first}"
        if len(prs) > 1:
            rest = ", ".join(f"[PR #{n}]({u})" for n, u, _ in prs[1:])
            line += f" · ещё: {rest}"
        items.append(line)
    for n, u, t in sorted(loose, key=lambda p: -p[0]):
        items.append(f"[PR #{n}]({u}) {t}")
    if hidden:
        items.append(f"скрыто служебных записей бота: {hidden}")
    blocks.append((f"Сделано за {hours} ч — влитые PR", items))

    counts = gh_json(f"/search/issues?q=repo:{repo}+is:issue+is:open&per_page=1")
    if counts:
        blocks.append((f"Открытых тикетов: {counts.get('total_count', '?')}", []))

    prs = gh_json(f"/repos/{repo}/pulls?state=open&per_page=100")
    if prs:
        silent = {i["node"]: i["mins"] for i in instances() if i["mins"] >= 30}
        orphan = []
        for p in prs:
            ref = p["head"]["ref"]
            if not ref.startswith("codex/"):
                continue
            node = ref.split("/")[1] if ref.count("/") >= 3 else ""
            mins = next((m for n, m in silent.items() if node.startswith(n.rstrip("…"))), None)
            if mins is None and node:
                continue
            orphan.append(f"[PR #{p['number']}]({p['html_url']}) {p['title'][:60]}"
                          + (f" — владелец молчит {mins} мин" if mins else " — владельца не определить"))
        if orphan:
            blocks.append((f"PR без владельца: {len(orphan)}", orphan,
                           "Работа сделана, но не влита. Перезапущенный бот подберёт её вместе "
                           "с шагом (§ 6.3). Если ждать некогда — `gh pr merge <номер>` "
                           "после зелёного CI."))

    # сверка веток: журнал намерений против реальности на GitHub (§ 14.3)
    branches = gh_json(f"/repos/{repo}/branches?per_page=100")
    if branches is not None:
        # сверяем только территорию Луноботов: всё остальное завёл человек
        real = {b["name"] for b in branches if b["name"].startswith("codex/")}
        f = d / "BRANCHES.md"
        recorded = set(re.findall(r"`([^`]+)`", f.read_text(encoding="utf-8"))) if f.exists() else set()
        leaks = sorted(real - recorded)
        ghosts = sorted(recorded - real)
        if leaks:
            items = [f"`{b}`" for b in leaks[:15]]
            if len(leaks) > 15:
                items.append(f"… ещё {len(leaks) - 15}")
            blocks.append((f"Утечки: ветка есть, записи нет — {len(leaks)}", items,
                           "Владелец жив — допишет запись сам. Молчит дольше 45 минут и PR "
                           "с ветки нет — её удалит любой бот в начале круга (§ 14.3). "
                           f"Не дожидаясь: `git push origin --delete <ветка>` в {repo}."))
        if ghosts:
            blocks.append((f"Записи без веток: {len(ghosts)}", [f"`{b}`" for b in ghosts[:15]],
                           "Ветку уже удалили, а строка осталась. Строка старше 45 минут "
                           "мертва, её уберёт любой бот в начале круга (§ 14.3); если флот "
                           "стоит — удали её из BRANCHES.md сам."))
        if not leaks and not ghosts:
            blocks.append((f"Ветки сходятся с журналом: {len(real)}", []))
    return blocks


LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def unpack(block):
    """Блок — (заголовок, строки) или (заголовок, строки, подсказка что делать)."""
    return block if len(block) == 3 else (block[0], block[1], "")


def render_text(report_blocks):
    print(f"# Пульт Луноботов — {datetime.now():%d-%m-%Y %H:%M}")
    inst = instances_block()
    if inst:
        print("\n## Инстансы\n")
        for i in inst:
            print(f"- {i}")
    for name, blocks in report_blocks:
        print(f"\n## {name}\n")
        for block in blocks:
            title, items, hint = unpack(block)
            print(f"### {title}\n")
            if hint:
                print(f"  {hint}\n")
            for i in items:
                print(f"- {i}")
            print()


def render_html(report_blocks):
    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def line(t):
        # готовые ссылки прячем в заглушки, иначе следующая замена залезет внутрь href
        done = []

        def stash(html):
            done.append(html)
            return f"\x00{len(done) - 1}\x00"

        t = LINK.sub(lambda m: stash(f'<a href="{esc(m.group(2))}">{esc(m.group(1))}</a>'), t)
        t = re.sub(r'https://[^\s<>"]*[^\s<>",.;:)\]]',
                   lambda m: stash(f'<a href="{esc(m.group(0))}">{esc(m.group(0))}</a>'), t)
        t = esc(t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = t.replace("⚠ протух", '<b class="stale">протух</b>')
        return re.sub(r"\x00(\d+)\x00", lambda m: done[int(m.group(1))], t)

    out = ['<!doctype html><html lang="ru"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           '<meta http-equiv="refresh" content="120">',
           "<title>Пульт Луноботов</title><style>",
           "body{font:15px/1.5 system-ui,sans-serif;margin:0 auto;padding:1.5rem;max-width:60rem;",
           "background:#0d1117;color:#c9d1d9}h1{font-size:1.3rem}h2{font-size:1.1rem;",
           "border-bottom:1px solid #30363d;padding-bottom:.3rem;margin-top:2rem}",
           "h3{font-size:.95rem;color:#8b949e;margin:1.2rem 0 .4rem}",
           "ul{margin:0;padding-left:1.2rem}li{margin:.25rem 0}",
           "a{color:#58a6ff;text-decoration:none}a:hover{text-decoration:underline}",
           "code{background:#161b22;padding:.1rem .35rem;border-radius:4px;font-size:.85em}",
           ".stale{color:#f85149}.upd{color:#8b949e;font-size:.85rem}</style></head><body>",
           "<h1>Пульт Луноботов</h1>",
           f'<p class="upd">Обновлено {datetime.now(timezone.utc):%d-%m-%Y %H:%M} UTC. '
           "Страница перезагружается сама раз в две минуты.</p>",
           f'<p>{line(fleet_line())}</p>']
    inst = instances_block()
    if inst:
        out.append("<h2>Инстансы</h2><ul>"
                   + "".join(f"<li>{line(i)}</li>" for i in inst) + "</ul>")
    for name, blocks in report_blocks:
        out.append(f"<h2>{esc(name)}</h2>")
        for block in blocks:
            title, items, hint = unpack(block)
            out.append(f"<h3>{esc(title)}</h3>")
            if hint:
                out.append(f'<p class="upd">{line(hint)}</p>')
            if items:
                out.append("<ul>" + "".join(f"<li>{line(i)}</li>" for i in items) + "</ul>")
    out.append("</body></html>")
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hours = 24
    if "--hours" in sys.argv:
        hours = int(sys.argv[sys.argv.index("--hours") + 1])
    only = args[0] if args else None
    report_blocks = [(name, report(name, repo, d, hours) or [])
                     for name, repo, d in projects(only)]
    if "--html" in sys.argv:
        print(render_html(report_blocks))
    else:
        render_text(report_blocks)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
