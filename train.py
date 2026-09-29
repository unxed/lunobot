#!/usr/bin/env python3
"""Staging и поезда (§ 7.2 инструкции): единственный путь рутинной работы в main.

    train.py land [--fix-staging]      в рабочем клоне, на своей ветке поверх lunobot/staging
    train.py tick-all --sign "<подпись § 9>"   tick по всем проектам INDEX.md со staging
    train.py tick  <owner/repo> --sign "<подпись § 9>"
    train.py health <owner/repo>
    train.py eject <owner/repo> <sha>... --reason "<ссылка на упавший job>"
    train.py covered <owner/repo> <sha>
    train.py bisect <owner/repo> --os <раннер> --cmd "<команда песочницы>"
    train.py close-train <owner/repo> <PR> [--reason "<текст>"]

land  — переносит твои коммиты (origin/lunobot/staging..HEAD) на вершину staging и пушит,
        с повторами при гонке. PR не открывает никогда. Staging красный (последний
        завершённый quick упал и починки после него нет) — ОТКАЗЫВАЕТ: конвейер стоит, пока
        его не починят (§ 7.2 п. 0). Починка — с --fix-staging и трейлером `Fixes-Staging:`.
health — только чтение: состояние staging и сколько часов main не двигался; для ретро круга.
        Плюс предупреждение (код не меняет): тикеты `в пути` в TRIAGE.md, чьи `Touch:` уже в main.
covered — быстрый ответ автору после land: зелёный/красный/ещё едет — по первому завершённому
        quick на его коммите или потомке (quick на staging не отменяется, каждый прогон доезжает).
tick  — идемпотентный шаг проводника; запускай в начале каждого круга. Сначала лечит staging:
        красный quick — один перезапуск, снова красный — откатывает виновника (коммиты между
        последним зелёным и первым красным quick, не больше трёх; больше — срочная задача).
        Поезд в пути: зелёный — вливает (fast-forward main, иначе merge-коммит) и, если tick
        запущен из учётного клона, сам правит в TRIAGE.md `в пути` → `проверяют` по `Touch:`
        коммитов поезда (коммит+пуш с `Lunobot-Instance:`); красный — бисект и выкидывание; поезда нет — режет новый поезд ТОЛЬКО до последнего коммита
        staging с зелёным quick и не режет, пока после него в staging есть коммит-починка
        (Fixes-Staging:/Staging-Revert:) — ждёт зелёного quick вершины. Печатает, сколько часов main не двигался; больше двух —
        ИНЦИДЕНТ ПРОЦЕССА, код 1.
bisect — вручную, когда падение платформенное/узкое и автоматический бисект (команда по ИМЕНИ
        упавшего шага упавшего job'а, таблица STEP_CMDS; неизвестный шаг — бисекта нет, сразу
        § 5 п. 2 с диагностикой) его не ловит: свой раннер и своя команда. Результат разбирает tick.
close-train — закрыть поезд БЕЗ выброса коммитов (база красная, fix-forward не вошёл, безнадёжный
        поезд): закрывает PR, удаляет ветку поезда и bisect/<N>/*, отменяет идущие прогоны.
eject — ревертит в staging коммиты-виновники красного поезда и закрывает его PR; следующий
        tick сразу режет новый поезд без них.

Коды возврата: 0 — всё штатно (в т.ч. «поезд ещё едет»), 1 — нужна работа человека/бота
(конфликт, красный поезд без выкидывания), 2 — ошибка использования.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

STAGING = "lunobot/staging"
# Явный refspec со знаком +: single-branch клон (gh repo clone --depth=N) не содержит staging в
# remote.origin.fetch, и голый `git fetch origin lunobot/staging` не обновляет origin/lunobot/staging.
STAGING_REFSPEC = f"+refs/heads/{STAGING}:refs/remotes/origin/{STAGING}"
# Попытки push в land(): при 6-8 параллельных ботах 6 попыток (~57 с backoff) исчерпывались раньше,
# чем освобождалось окно (starvation); 12 попыток с backoff 2+3*n — около 4 минут.
LAND_ATTEMPTS = 12
TRAIN_PREFIX = "lunobot/train/"
MIN_COMMITS = 5
MAX_AGE_MIN = 30
# Прогоны main здесь не отменяются никогда — решение владельца («Preserve every main run»).
PRESERVE_MAIN = {"unxed/vtui"}
# Зависимости f4, которые f4 подтягивает через go.mod: после мержа поезда в main — следующий
# тег vX.Y.Z (projects/<проект>/PROJECT.md, «Релизы»). Без тега исправление не доедет до f4
# (28-09-2026 поезд vtui #166 влит, тег никто не поставил, #1571 в f4 проверить было нельзя).
TAG_AFTER_MERGE = {"unxed/vtui"}
TRAILER = re.compile(r"^(Touch|Lunobot-Task):\s*(.+)$", re.M)
CHECK = re.compile(r"^Проверить:\s*\n(.*?)(?:\n\s*\n[A-Z][\w-]+:|\Z)", re.M | re.S)
# Коммит, чинящий красный staging: ручная починка (land --fix-staging) или автооткат tick'а.
HEAL = re.compile(r"^(Fixes-Staging|Staging-Revert):", re.M)
# Больше стольких коммитов между последним зелёным и первым красным quick — откатывать
# вслепую нельзя (заденет чужую работу), нужен бот: срочная задача § 5 п. 2.
MAX_AUTO_REVERT = 3
# Сколько минут tick ждёт зелёного quick на вершине staging, когда после последнего зелёного
# лежит коммит-починка (cut). Дольше — выход в § 5 п. 2: quick мог не запуститься вовсе
# (paths-ignore `**.md`/`docs/**` в quick.yml, отмена), и ждать вечно нельзя.
HEAL_WAIT_MIN = 45
# main стоит дольше этого при непустом staging — процесс не работает (инцидент 28-09-2026:
# десять поездов подряд красные, main стоял 9.5 ч, пока флот продолжал приземлять).
STUCK_HOURS = 2
# Учётный клон — каталог, где лежит сам train.py (его запускают оттуда, § 7.2 п. 3).
ACCOUNTING = os.path.dirname(os.path.abspath(__file__))
IN_TRANSIT = re.compile(r"^(\|\s*(\d+)\s*\|[^|]*\|\s*)в пути(\s*\|)", re.M)
# Окно сверки «в пути» с Touch: коммитов main (см. transit_warn).
TRANSIT_WINDOW_H = 24


def run(*cmd, check=True, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and p.returncode:
        sys.exit(f"{' '.join(cmd)}: {p.stderr.strip() or p.stdout.strip()}")
    return p


def api(path, *args, check=True):
    p = run("gh", "api", path, *args, check=check)
    return json.loads(p.stdout) if p.stdout.strip() else None


def origin_repo():
    url = run("git", "remote", "get-url", "origin", check=False).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else None


def quick_runs(repo):
    """Завершённые (не отменённые) прогоны quick на staging, новые первыми."""
    rs = api(f"repos/{repo}/actions/workflows/quick.yml/runs?branch={STAGING}&per_page=60")
    rs = [r for r in rs["workflow_runs"] if r["status"] == "completed"
          and r["conclusion"] not in ("cancelled", "skipped")]
    return sorted(rs, key=lambda r: r["created_at"], reverse=True)


def staging_health(repo):
    """green | pending | healing | red, и подробности.

    red — последний завершённый quick на staging упал, и после его вершины в staging нет
    ни одного коммита-починки (трейлер Fixes-Staging:/Staging-Revert:). Всё, что приземлено
    поверх красного без починки, красное вслепую: его quick ничего не говорит о нём самом."""
    tip = api(f"repos/{repo}/branches/{STAGING}")["commit"]["sha"]
    runs = quick_runs(repo)
    info = {"tip": tip, "last": runs[0] if runs else None,
            "green": next((r for r in runs if r["conclusion"] == "success"), None)}
    if not runs:
        return "pending", info
    last = runs[0]
    if last["conclusion"] == "success":
        return ("green" if last["head_sha"] == tip else "pending"), info
    if last["head_sha"] != tip:
        after = compare(repo, last["head_sha"], tip)["commits"]
        if any(HEAL.search(c["commit"]["message"]) for c in after):
            return "healing", info
    return "red", info


def red_range(repo, info):
    """Коммиты-кандидаты в виновники: от последнего зелёного quick до первого красного."""
    runs = quick_runs(repo)
    green = info["green"]
    base = green["head_sha"] if green else api(f"repos/{repo}/branches/main")["commit"]["sha"]
    newer = [r for r in runs if not green or r["created_at"] > green["created_at"]]
    first_red = min(newer, key=lambda r: r["created_at"]) if newer else info["last"]
    commits = compare(repo, base, first_red["head_sha"])["commits"]
    return first_red, [c for c in commits if len(c["parents"]) == 1
                       and not HEAL.search(c["commit"]["message"])]


def who(c):
    msg = c["commit"]["message"]
    keys = [v.strip() for _, v in TRAILER.findall(msg)]
    return f"{c['sha'][:9]} {msg.splitlines()[0][:70]} [{', '.join(keys) or 'без трейлера'}]"


def land(fix=False):
    run("git", "fetch", "-q", "origin", STAGING_REFSPEC)
    commits = run("git", "log", "--format=%H%x00%B%x01", f"origin/{STAGING}..HEAD").stdout
    msgs = [c.split("\0", 1) for c in commits.split("\x01") if c.strip()]
    if not msgs:
        sys.exit("нечего приземлять: HEAD не впереди origin/lunobot/staging")
    bad = [sha[:9] for sha, body in msgs if not TRAILER.search(body)]
    if bad:
        sys.exit(f"коммиты без трейлера Touch:/Lunobot-Task: {', '.join(bad)} — проводник не "
                 "сможет разнести «Пробуйте!» по тикетам; допиши трейлер (git commit --amend)")
    if fix and not any(re.search(r"^Fixes-Staging:", body, re.M) for _, body in msgs):
        sys.exit("--fix-staging: хотя бы один коммит обязан нести трейлер "
                 "`Fixes-Staging: <ссылка на красный quick>` — по нему остальные поймут, что "
                 "staging лечится, и снова смогут приземлять")
    repo = origin_repo()
    if repo and not fix:
        state, info = staging_health(repo)
        if state == "red":
            last = info["last"]
            sys.exit(
                f"staging КРАСНЫЙ: {last['html_url']} (вершина {last['head_sha'][:9]}). Конвейер "
                "стоит — поверх красного не приземляют (§ 7.2 п. 0). Твои коммиты целы в клоне.\n"
                "Сейчас у тебя § 5 п. 2: запусти `train.py tick " + repo + " --sign ...` (он "
                "перезапустит quick или откатит однозначного виновника) либо почини причину "
                "сам и приземли с `land --fix-staging` (трейлер `Fixes-Staging: <ссылка>`). "
                "Потом повтори land.")
    for attempt in range(LAND_ATTEMPTS):
        if run("git", "rebase", "-q", f"origin/{STAGING}", check=False).returncode:
            run("git", "rebase", "--abort", check=False)
            sys.exit("конфликт при переносе на staging — разреши его сам (git rebase "
                     "origin/lunobot/staging), это твой код, и запусти land снова")
        if run("git", "push", "-q", "origin", f"HEAD:{STAGING}", check=False).returncode == 0:
            head = run('git', 'rev-parse', 'HEAD').stdout.strip()
            print(f"приземлено в {STAGING}: {len(msgs)} коммит(ов), вершина {head}\n"
                  f"результат quick позже: train.py covered <owner/repo> {head}")
            return 0
        time.sleep(2 + 3 * attempt)
        run("git", "fetch", "-q", "origin", STAGING_REFSPEC)
    sys.exit(f"staging {LAND_ATTEMPTS} раз подряд ушёл вперёд — повтори land чуть позже")


def train_pr(repo):
    prs = api(f"repos/{repo}/pulls?state=open&per_page=100")
    trains = [p for p in prs if p["head"]["ref"].startswith(TRAIN_PREFIX)]
    return trains[0] if trains else None


def rollup(repo, number):
    out = run("gh", "pr", "view", str(number), "--repo", repo,
              "--json", "statusCheckRollup").stdout
    checks = json.loads(out)["statusCheckRollup"]
    pending = [c for c in checks if c.get("status", "COMPLETED") != "COMPLETED"
               or c.get("state") == "PENDING"]
    failed = [c for c in checks if (c.get("conclusion") or c.get("state"))
              in ("FAILURE", "TIMED_OUT", "STARTUP_FAILURE", "ERROR", "ACTION_REQUIRED")]
    cancelled = [c for c in checks if c.get("conclusion") == "CANCELLED"]
    return checks, pending, failed, cancelled


def compare(repo, base, head):
    return api(f"repos/{repo}/compare/{base}...{head}")


def tickets(repo, commits):
    """{ключ: [тексты «Проверить»]} по трейлерам коммитов поезда."""
    out = {}
    for c in commits:
        msg = c["commit"]["message"]
        if len(c.get("parents", [])) > 1:
            continue
        chk = CHECK.search(msg)
        for kind, val in TRAILER.findall(msg):
            key = val.strip()
            if kind == "Touch" and key.startswith("#"):
                key = f"{repo}{key}"
            out.setdefault(key, [])
            if chk:
                out[key].append(chk.group(1).strip())
    return out


def cut(repo, sign):
    main_sha = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    staging = api(f"repos/{repo}/branches/{STAGING}", check=False)
    if not staging or "commit" not in staging:
        sys.exit(f"нет ветки {STAGING} в {repo}")
    cmp = compare(repo, main_sha, staging["commit"]["sha"])
    if cmp["behind_by"]:
        r = run("gh", "api", f"repos/{repo}/merges", "-f", f"base={STAGING}", "-f", "head=main",
                "-f", "commit_message=Merge main into lunobot/staging", check=False)
        if r.returncode:
            print(f"main не вливается в staging без конфликта — срочная работа (§ 5 п. 2): "
                  f"разреши вручную в клоне и запушь в {STAGING}\n{r.stderr.strip()}")
            return 1
        print("влил main в staging (там были коммиты мимо поезда)")
        return train_step(repo, sign)
    # Поезд режется только до последнего коммита staging с зелёным quick: красный кусок
    # staging в поезд не едет никогда. Иначе поезд заведомо красный, а бисект по нему ищет
    # виновника в «базе, которая сама красная» (инцидент 28-09-2026, #1611–#1620).
    green = next((r for r in quick_runs(repo) if r["conclusion"] == "success"
                  and compare(repo, main_sha, r["head_sha"]).get("ahead_by", 0) > 0
                  and compare(repo, r["head_sha"], staging["commit"]["sha"])["status"]
                  in ("ahead", "identical")), None)
    if not green:
        print("в staging нет ни одного коммита впереди main с зелёным quick — поезд не режется; "
              "если staging красный, это § 5 п. 2 (см. выше)")
        return 0
    cut_sha = green["head_sha"]
    heal_wait = [c for c in compare(repo, cut_sha, staging["commit"]["sha"])["commits"]
                 if HEAL.search(c["commit"]["message"])]
    if heal_wait:
        # Зелёный quick мог пройти НА ломающем коммите (quick не проверяет всего): починка лежит
        # после него, и резать «до зелёного» значит везти поломку без починки (28-09-2026,
        # поезд unxed/f4#1643: 2b085791 без 2243f78f). Ждём зелёного quick вершины.
        tip_date = datetime.fromisoformat(
            staging["commit"]["commit"]["committer"]["date"].replace("Z", "+00:00"))
        wait = (datetime.now(timezone.utc) - tip_date).total_seconds() / 60
        print("поезд не режу: после последнего зелёного quick "
              f"({cut_sha[:9]}) в staging есть коммит-починка ({who(heal_wait[0])}"
              f"{' и ещё ' + str(len(heal_wait) - 1) if len(heal_wait) > 1 else ''}) — жду "
              f"зелёного quick на вершине staging ({wait:.0f} мин с её коммита)")
        if wait > HEAL_WAIT_MIN:
            print(f"ИНЦИДЕНТ: зелёного quick на вершине staging нет уже {wait:.0f} мин "
                  f"(> {HEAL_WAIT_MIN}). СРОЧНО (§ 5 п. 2): «красный staging» — quick на вершине "
                  "не запускался (вершина трогает только *.md/docs/**, paths-ignore) или "
                  "отменён; приземли `land` коммит, трогающий не-doc файл, либо проверь "
                  "вершину в песочнице и разбери вручную")
            return 1
        return 0
    cmp = compare(repo, main_sha, cut_sha)
    own = [c for c in cmp["commits"] if len(c["parents"]) == 1]
    if not own:
        print("staging не впереди main — резать нечего")
        return 0
    oldest = min(datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
                 for c in own)
    age = (datetime.now(timezone.utc) - oldest).total_seconds() / 60
    if len(own) < MIN_COMMITS and age < MAX_AGE_MIN:
        print(f"staging: {len(own)} коммит(ов), старшему {age:.0f} мин — поезд ещё не созрел "
              f"(порог {MIN_COMMITS} коммитов или {MAX_AGE_MIN} мин)")
        return 0
    stamp = datetime.now(timezone.utc).strftime("%y%m%d-%H%M")
    project = repo.split("/")[1]
    branch = f"{TRAIN_PREFIX}{project}/{stamp}"
    # Several tick processes can pass train_pr() before the first one creates
    # the branch.  A duplicate ref is the expected result of that race, not a
    # process failure: reuse it when it points at the same cut, and use the
    # cut SHA to disambiguate an unlikely same-minute second cut.
    ref_path = f"repos/{repo}/git/ref/heads/{branch}"
    existing = api(ref_path, check=False)
    if existing and existing.get("object", {}).get("sha") != cut_sha:
        branch = f"{branch}-{cut_sha[:9]}"
        ref_path = f"repos/{repo}/git/ref/heads/{branch}"
        existing = api(ref_path, check=False)
    if not existing:
        created = api(f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{branch}",
                      "-f", f"sha={cut_sha}", check=False)
        if created is None:
            existing = api(ref_path, check=False)
            if not existing:
                sys.exit(f"не удалось создать ветку поезда {branch}")
    tk = tickets(repo, own)
    short = [k.replace(f"{repo}#", "#") for k in tk]
    title = f"Поезд {project} {stamp}: " + (", ".join(short) if short else f"{len(own)} коммитов")
    body = [f"Поезд из `{STAGING}` до `{cut_sha[:9]}` — последнего коммита с зелёным quick "
            f"({green['html_url']}); {len(own)} коммитов. Собран `train.py` — отдельных "
            "бот-PR больше нет, всё рутинное едет так (LUNOBOT.md § 7.2).", ""]
    for key, texts in tk.items():
        body.append(f"### {key}")
        body += texts or ["(автор не оставил блока «Проверить:»)"]
        if key.startswith(f"{repo}#"):
            body.append(f"\nTouch #{key.split('#')[1]}")
        elif "#" in key:
            body.append(f"\nTouch {key}")
        body.append("")
    body.append(sign)
    body.append("\n🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("\n".join(body)[:65000])
    open_pr = next((p for p in api(f"repos/{repo}/pulls?state=open&per_page=100")
                    if p["head"]["ref"] == branch), None)
    if open_pr:
        print(f"поезд уже отправлен: {open_pr['html_url']} ({len(own)} коммитов, {len(tk)} тикетов/задач)")
        return 0
    created_pr = run("gh", "pr", "create", "--repo", repo, "--base", "main", "--head", branch,
                     "--title", title[:250], "--body-file", f.name, check=False)
    if created_pr.returncode:
        # The other tick may have created the PR between the check above and
        # this command.  Treat that race exactly like the duplicate ref.
        open_pr = next((p for p in api(f"repos/{repo}/pulls?state=open&per_page=100")
                        if p["head"]["ref"] == branch), None)
        if open_pr:
            print(f"поезд уже отправлен: {open_pr['html_url']} ({len(own)} коммитов, {len(tk)} тикетов/задач)")
            return 0
        sys.exit(f"не удалось открыть PR поезда {branch}: "
                 f"{created_pr.stderr.strip() or created_pr.stdout.strip()}")
    url = created_pr.stdout.strip()
    print(f"поезд отправлен: {url} ({len(own)} коммитов, {len(tk)} тикетов/задач)")
    return 0


def train_commits(repo, pr):
    return [c for c in compare(repo, pr["base"]["sha"], pr["head"]["sha"])["commits"]
            if len(c["parents"]) == 1]


def guess_os(name):
    n = (name or "").lower()
    if "windows" in n:
        return "windows-11-arm" if "arm64" in n else "windows-latest"
    if "darwin" in n or "macos" in n:
        return "macos-15-intel" if "amd64" in n else "macos-latest"
    if "arm64" in n:
        return "ubuntu-24.04-arm"
    return "ubuntu-latest"


def sandbox_cmd(repo, ref, os_label, script):
    """Команда для sandbox.yml с учётом того, КАК версия workflow на этом ref её исполняет
    (workflow_dispatch берёт sandbox.yml с той ветки, на которой запускается):
    - новая версия (`bash -c "$SANDBOX_COMMAND"`, f4 с 28-09-2026) — скрипт как есть;
    - старая (`run: $SANDBOX_COMMAND`, без разбора shell) — `&&`, `|` без обёртки ушли бы
      аргументами в go и сделали бы красным КАЖДЫЙ префикс бисекта; поэтому один токен
      `bash -c` с ${IFS} вместо пробелов. Для старой версии обёртка обязательна, для новой —
      запрещена (там ${IFS} раскрылся бы внешним bash, и выполнилось бы одно `go`).
    pwsh (Windows) понимает `&&` в обеих версиях."""
    if os_label.startswith("windows"):
        return script
    wf = api(f"repos/{repo}/contents/.github/workflows/sandbox.yml?ref={ref}", check=False) or {}
    import base64
    text = base64.b64decode(wf.get("content", "")).decode("utf-8", "replace")
    if 'bash -c "$SANDBOX_COMMAND"' in text:
        return script
    return "bash -c " + script.replace(" ", "${IFS}")


# Команда бисекта по ИМЕНИ упавшего шага упавшего job'а (имена — из build.yml f4). Бисект обязан
# воспроизводить именно упавший шаг: gofmt+vet «по умолчанию» не воспроизводил langfmt и давал
# ложный вердикт (28-09-2026, поезда unxed/f4#1642 и unxed/f4#1643). Шага нет в таблице — бисект
# вслепую не запускается (см. pick_target_steps). None вместо ОС — ОС берётся из имени job'а.
STEP_CMDS = [
    (r"^Check formatting$", 'test -z "$(gofmt -s -l .)"'),
    (r"^Check language file formatting$", "go run ./tools/langfmt -check internal/i18n/lang/*.lng"),
    (r"^Run go vet\b", "go vet ./..."),
    (r"^Run Tests$", "go test -count=1 ./..."),
    (r"^Run race detector$", "go test -race -count=1 ./..."),
    # vtui (ci.yml): шаг «Test» job'а Test (<цель>), безымянный шаг job'а Race (авто-имя GitHub).
    (r"^Test$", "go test -count=1 -timeout 4m ./..."),
    (r"^Run go test -race\b", "go test -race -count=1 -timeout 15m ./..."),
]
# Job'ы, чей упавший шаг ОДНОЙ командой на одной ОС не воспроизвести: `Vet (<цели>)` f4 гоняет
# go vet под несколькими GOOS/GOARCH (freebsd, illumos...), песочница проверила бы не то.
UNREPRODUCIBLE_JOBS = re.compile(r"^Vet \(")


def failed_steps(failed):
    """[(имя job'а, имя упавшего шага или None)] по упавшим проверкам поезда (API job'а)."""
    out = []
    for c in failed:
        step = None
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/\d+/job/(\d+)",
                      c.get("detailsUrl") or "")
        if m:
            job = api(f"repos/{m.group(1)}/actions/jobs/{m.group(2)}", check=False) or {}
            step = next((s.get("name") for s in job.get("steps", [])
                         if s.get("conclusion") == "failure"), None)
        out.append((c.get("name") or c.get("context") or "", step))
    return out


def pick_target_steps(steps):
    """(ОС, команда) для бисекта по упавшим шагам, либо None, если хоть один шаг неизвестен:
    бисект чужой командой даёт ложный «зелёный на всех префиксах» и перезапуски по кругу.
    Команды одной ОС склеиваются через &&; несколько ОС — берётся первая не-linux (остальное
    вскроет следующий поезд после выброса)."""
    per_os = {}
    for job, step in steps:
        cmd = next((c for rx, c in STEP_CMDS if step and re.search(rx, step)), None)
        if UNREPRODUCIBLE_JOBS.search(job or ""):
            cmd = None
        if not cmd:
            return None
        os_label = "ubuntu-latest" if step == "Run race detector" else guess_os(job)
        if cmd not in per_os.setdefault(os_label, []):
            per_os[os_label].append(cmd)
    if not per_os:
        return None
    os_label = next((o for o in per_os if o != "ubuntu-latest"), next(iter(per_os)))
    return os_label, " && ".join(per_os[os_label])


BISECT_ROUND = 12  # прогонов песочницы за раунд: пул аккаунта — 20 job'ов на всех


def sample(lo, hi, k):
    """До k индексов строго между lo и hi, равномерно."""
    inner = list(range(lo + 1, hi))
    if len(inner) <= k:
        return inner
    return sorted({inner[round(j * (len(inner) - 1) / (k - 1))] for j in range(k)})


def bisect(repo, pr, os_label, cmd, good=-1, bad=None):
    """Бисект раундами. Раунд — параллельные прогоны песочницы на префиксах поезда внутри окна
    (good, bad]: оба конца окна (для самодостаточного вердикта) и до BISECT_ROUND точек между
    ними. Первый раунд — ещё и контроль на базе поезда (main): без него красная база делает
    «виновником» первый же коммит поезда (трижды — невиновный 6f8fffd9, #1611/#1612/#1620).
    Раньше гонялся КАЖДЫЙ префикс сразу — на поезде из сотни коммитов это сотня прогонов."""
    commits = train_commits(repo, pr)
    bad = len(commits) - 1 if bad is None else bad
    idx = sorted({i for i in [good, bad] if i >= 0} | set(sample(good, bad, BISECT_ROUND)))
    refs = [(f"bisect/{pr['number']}/{i:03d}-{commits[i]['sha'][:9]}", commits[i]["sha"])
            for i in idx]
    if good < 0:
        refs.insert(0, (f"bisect/{pr['number']}/base-{pr['base']['sha'][:9]}", pr["base"]["sha"]))
    for ref, sha in refs:
        api(f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{ref}", "-f", f"sha={sha}",
            check=False)
        run("gh", "workflow", "run", "sandbox.yml", "--repo", repo, "--ref", ref,
            "-f", f"os={os_label}", "-f", f"command={sandbox_cmd(repo, ref, os_label, cmd)}")
    print(f"бисект: окно ({good}, {bad}] из {len(commits)} коммитов, {len(refs)} прогонов "
          f"({os_label}, `{cmd}`) — результат разберёт следующий tick")


def bisect_refs(repo, n):
    refs = api(f"repos/{repo}/git/matching-refs/heads/bisect/{n}/") or []
    return sorted(r["ref"].removeprefix("refs/heads/") for r in refs)


def drop_bisect(repo, refs):
    for ref in refs:
        api(f"repos/{repo}/git/refs/heads/{ref}", "-X", "DELETE", check=False)


def close_train(repo, pr, comment):
    """Закрыть поезд целиком: комментарий и закрытие PR, удаление ветки поезда и bisect/<N>/*,
    отмена идущих прогонов (поезда и бисекта) — чтобы это не делалось руками и не сжигало раннеры."""
    n = pr["number"]
    branches = [pr["head"]["ref"]] + bisect_refs(repo, n)
    if comment:  # None — PR уже закрыт, только уборка
        run("gh", "pr", "close", str(n), "--repo", repo, "--comment", comment, check=False)
    for br in branches:
        for st in ("in_progress", "queued"):
            runs = api(f"repos/{repo}/actions/runs?branch={br}&status={st}&per_page=100",
                       check=False) or {}
            for r in runs.get("workflow_runs", []):
                run("gh", "run", "cancel", str(r["id"]), "--repo", repo, check=False)
    drop_bisect(repo, branches)  # и ветка поезда: DELETE refs/heads/<ref> одинаков для всех


def close_train_cmd(repo, number, reason):
    pr = api(f"repos/{repo}/pulls/{number}")
    if not pr["head"]["ref"].startswith(TRAIN_PREFIX) or pr.get("merged"):
        sys.exit(f"#{number}: не поезд ({TRAIN_PREFIX}*) или уже влит — не трогаю")
    if pr["state"] != "open":
        # Повторный вызов: PR уже закрыт (в том числе прошлым close-train, упавшим на середине) —
        # дочищаем то, что могло остаться (ветки, идущие прогоны), без нового комментария.
        close_train(repo, pr, None)
        print(f"поезд #{number} уже закрыт: дочистил ветку поезда, bisect/{number}/*, прогоны")
        return 0
    close_train(repo, pr, reason or "Поезд закрыт без выброса коммитов (`train.py close-train`); "
                "следующий режется из актуального staging.")
    print(f"поезд #{number} закрыт: PR, ветка, bisect/{number}/*, идущие прогоны")
    return 0


def red(repo, pr, failed):
    """Красный поезд. Виновника определяет механика, не суждение бота:
    1) один перезапуск упавших job'ов — флейк отсеивается сам;
    2) снова красный — параллельный бисект песочницей по префиксам поезда;
    3) первый падающий префикс — виновник, выкидывается автоматически;
    4) бисект ничего не воспроизвёл — ещё один полный перезапуск; красный и после него —
       срочная задача одному боту (§ 5 п. 2), staging при этом не замораживается."""
    n = pr["number"]
    steps = failed_steps(failed)
    print(f"поезд #{n} КРАСНЫЙ: " + ", ".join(f"{j} / шаг «{st or '?'}»" for j, st in steps))
    refs = bisect_refs(repo, n)
    if refs:
        verdict = []
        for ref in refs:
            runs = api(f"repos/{repo}/actions/runs?branch={ref}&event=workflow_dispatch")["workflow_runs"]
            verdict.append((ref, runs[0] if runs else None))
        if any(r is None or r["status"] != "completed" for _, r in verdict):
            print("бисект ещё идёт")
            return 0
        base = [(ref, r) for ref, r in verdict if "/base-" in ref]
        if base and base[0][1]["conclusion"] != "success":
            close_train(repo, pr,
                        f"Контрольный прогон бисекта на БАЗЕ поезда (main) тоже красный: "
                        f"{base[0][1]['html_url']}. Виноват не поезд — сломан main; это § 5 п. 2 "
                        "(красный main). Поезд закрыт, следующий режется после починки main.")
            print(f"бисект: база поезда (main) сама красная — {base[0][1]['html_url']}. "
                  "Коммиты поезда НЕ выкидываются. СРОЧНО (§ 5 п. 2): красный main")
            return 1
        res = {int(ref.rsplit("/", 1)[1].split("-")[0]): r["conclusion"] == "success"
               for ref, r in verdict if "/base-" not in ref}
        bads = [i for i, ok in res.items() if not ok]
        if bads:
            i_bad = min(bads)
            i_good = max([i for i, ok in res.items() if ok and i < i_bad], default=-1)
            commits = train_commits(repo, pr)
            if i_bad - i_good > 1:
                drop_bisect(repo, refs)
                print(f"бисект: падает с префикса {i_bad}, зелёный до {i_good} — сужаю окно")
                target = pick_target_steps(steps)
                if not target:
                    return unknown_step(repo, pr, steps)
                bisect(repo, pr, *target, good=i_good, bad=i_bad)
                return 0
            sha = commits[i_bad]["sha"]
            print(f"бисект: первый падающий префикс {i_bad} — виновник {sha[:9]}")
            # Ветки бисекта удаляет eject только при успехе: если откат не лёг, следующий
            # tick увидит тот же готовый вердикт, а не запустит бисект заново по кругу.
            return eject(repo, [sha], f"бисект по {pr['html_url']}, первым падает {sha[:9]}")
        drop_bisect(repo, refs)
        attempt = attempts(failed)
        if attempt < 3:
            rerun(failed)
            print("бисект не воспроизвёл падение ни на одном префиксе — похоже на флейк/"
                  "платформу; поезд перезапущен ещё раз")
            return 0
        print("красный и после бисекта и двух перезапусков — срочная задача одному боту "
              "(§ 5 п. 2): разобрать падение; остальные продолжают приземлять в staging")
        return 1
    if attempts(failed) < 2:
        rerun(failed)
        print("первый перезапуск упавших job'ов — отсеиваем флейк")
        return 0
    target = pick_target_steps(steps)
    if not target:
        return unknown_step(repo, pr, steps)
    bisect(repo, pr, *target)
    return 0


def unknown_step(repo, pr, steps):
    """Упавший шаг не в STEP_CMDS: воспроизвести его бисектом нечем, вслепую не гоняем."""
    drop_bisect(repo, bisect_refs(repo, pr["number"]))
    print("бисект НЕ запускаю: упавший шаг не в таблице STEP_CMDS, чужая команда дала бы ложный "
          "вердикт. Упавшее: " + "; ".join(f"{j} / «{st or 'шаг неизвестен'}»" for j, st in steps))
    print(f"коммиты поезда #{pr['number']}:")
    for c in train_commits(repo, pr):
        print(f"    {who(c)}")
    print("СРОЧНО (§ 5 п. 2): «красный поезд» — прочитать лог упавшего шага, найти виновника, "
          "`train.py eject` (выкинуть) или `train.py bisect --os --cmd` (своя команда); поезд "
          "безнадёжен — `train.py close-train`. Шаг — добавить в STEP_CMDS.")
    return 1


def attempts(failed):
    out = 1
    for c in failed:
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", c.get("detailsUrl") or "")
        if m:
            r = api(f"repos/{m.group(1)}/actions/runs/{m.group(2)}", check=False)
            if r:
                out = max(out, r.get("run_attempt", 1))
    return out


def rerun(failed):
    for c in failed:
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", c.get("detailsUrl") or "")
        if m:
            run("gh", "run", "rerun", m.group(2), "--failed", "--repo", m.group(1), check=False)


def covered(repo, sha):
    """Результат quick для коммита в staging: первый завершённый прогон на нём или потомке."""
    runs = api(f"repos/{repo}/actions/workflows/quick.yml/runs?branch={STAGING}&per_page=30")
    for r in sorted(runs["workflow_runs"], key=lambda r: r["created_at"]):
        if r["status"] != "completed" or r["conclusion"] in ("cancelled", "skipped"):
            continue
        cmp = api(f"repos/{repo}/compare/{sha}...{r['head_sha']}", check=False)
        if cmp and cmp.get("status") in ("ahead", "identical"):
            verdict = "зелёный" if r["conclusion"] == "success" else "КРАСНЫЙ"
            print(f"{verdict}: {r['html_url']} (прогон на {r['head_sha'][:9]})")
            return 0 if r["conclusion"] == "success" else 1
    print("ещё едет: завершённого quick на этом коммите или его потомке пока нет")
    return 0


def heal(repo):
    """Красный staging лечится раньше всего остального: пока он красный, land отказывает,
    а поезд не режется. Шаги механические, как и у красного поезда:
    1) один перезапуск упавшего quick (флейк);
    2) снова красный, кандидатов в виновники ≤ MAX_AUTO_REVERT — откат их всех одним пушем
       с трейлером Staging-Revert (авторы приземлят исправленное заново как новую работу);
    3) кандидатов больше — срочная задача боту (§ 5 п. 2) с их списком."""
    state, info = staging_health(repo)
    if state == "healing":
        print("staging: после красного quick приземлена починка — ждём её quick (не ты)")
    if state != "red":
        return 0
    last = info["last"]
    print(f"staging КРАСНЫЙ: {last['html_url']} (вершина {last['head_sha'][:9]})")
    if last.get("run_attempt", 1) < 2:
        run("gh", "run", "rerun", str(last["id"]), "--failed", "--repo", repo, check=False)
        print("  перезапустил упавший quick — отсеиваем флейк")
        return 0
    first_red, culprits = red_range(repo, info)
    print(f"  первый красный quick: {first_red['html_url']}; кандидаты в виновники "
          f"(после последнего зелёного {'quick ' + info['green']['head_sha'][:9] if info['green'] else 'main'}):")
    for c in culprits:
        print(f"    {who(c)}")
    if not culprits or len(culprits) > MAX_AUTO_REVERT:
        print(f"  кандидатов {len(culprits)} — вслепую не откатываю. СРОЧНО (§ 5 п. 2): "
              "«красный staging» — прочитать лог, починить причину, land --fix-staging")
        return 1
    with tempfile.TemporaryDirectory() as d:
        run("git", "clone", "-q", "--filter=blob:none", "--branch", STAGING,
            f"https://github.com/{repo}.git", d)
        run("git", "config", "user.name", "unxed", cwd=d)
        run("git", "config", "user.email", "1151423+unxed@users.noreply.github.com", cwd=d)
        for c in reversed(culprits):
            r = run("git", "revert", "--no-edit", c["sha"], cwd=d, check=False)
            if r.returncode:
                print(f"  откат {c['sha'][:9]} не лёг чисто — СРОЧНО (§ 5 п. 2): «красный "
                      "staging», чинить вперёд, land --fix-staging")
                return 1
            msg = run("git", "log", "-1", "--format=%B", cwd=d).stdout
            run("git", "commit", "-q", "--amend", "-m",
                f"{msg.rstrip()}\n\nStaging-Revert: {first_red['html_url']}", cwd=d)
        if run("git", "push", "-q", "origin", f"HEAD:{STAGING}", cwd=d, check=False).returncode:
            print("  staging ушёл вперёд во время отката — следующий tick повторит")
            return 0
    print(f"  откатил {len(culprits)} коммит(ов) из staging. Авторам (по трейлерам выше): "
          "починить и приземлить заново — это обычная новая работа, тикет снова «свободен»")
    return 0


def stuck(repo):
    """Метрика результата, а не активности: как долго УЖЕ ПРИЗЕМЛЁННАЯ работа ждёт main.
    Флот может выглядеть очень занятым (десятки land, поезд за поездом) и при этом не
    доставлять ничего — именно так прошли 9.5 часов 28-09-2026.

    Меряется возраст самого старого коммита staging, которого нет в main (дата коммиттера —
    это момент land: land переносит коммиты rebase'ом). Не возраст вершины main: поезд
    вливается fast-forward'ом, коммиты сохраняют старые даты, и «main стоит N часов»
    показывало бы застой сразу после мержа; а в проекте, где main долго не нужен был, один
    свежий коммит в staging поднимал бы ложный инцидент."""
    main = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    staging = api(f"repos/{repo}/branches/{STAGING}")["commit"]["sha"]
    own = [c for c in compare(repo, main, staging)["commits"] if len(c["parents"]) == 1]
    if not own:
        print("staging не впереди main — приземлённая работа вся в main")
        return 0
    oldest = min(datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
                 for c in own)
    hours = (datetime.now(timezone.utc) - oldest).total_seconds() / 3600
    print(f"в staging {len(own)} коммит(ов) ждут main; старший — {hours:.1f} ч")
    if hours > STUCK_HOURS:
        print(f"ИНЦИДЕНТ ПРОЦЕССА: приземлённая работа ждёт main дольше {STUCK_HOURS} ч. "
              "§ 4 «ретро круга»: найти, почему не едет поезд, починить конвейер и "
              "зафиксировать правкой LUNOBOT.md/train.py (§ 12)")
        return 1
    return 0


def main_ci(repo):
    """Последний прогон полной матрицы на вершине main. После мержа мимо поезда (владелец
    влил staging руками, merge-коммит поезда, срочный PR) это ПЕРВАЯ проверка комбинации
    на всех ОС — её результат должен увидеть следующий же круг, а не случайный бот."""
    head = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    runs = api(f"repos/{repo}/actions/runs?branch=main&event=push&head_sha={head}&per_page=20")
    runs = [r for r in runs["workflow_runs"] if r["name"] not in ("quick", "sandbox")]
    if not runs:
        print(f"main {head[:9]}: прогона полной матрицы нет")
        return 0
    r = max(runs, key=lambda r: r["created_at"])
    if r["status"] != "completed":
        # Упавший job виден задолго до конца матрицы (28-09-2026: семь групп падений были
        # видны через ~20 минут, а прогон шёл ещё полчаса) — починку начинаем сразу.
        jobs = api(f"repos/{repo}/actions/runs/{r['id']}/jobs?per_page=100", check=False) or {}
        bad = [j["name"] for j in jobs.get("jobs", []) if j.get("conclusion") == "failure"]
        if bad:
            print(f"main {head[:9]}: полная матрица ещё идёт, но уже КРАСНАЯ ({len(bad)}: "
                  f"{', '.join(bad[:6])}{' …' if len(bad) > 6 else ''}) — {r['html_url']}. "
                  "СРОЧНО (§ 5 п. 2): красный main, не ждать конца прогона")
            return 1
        print(f"main {head[:9]}: полная матрица идёт — {r['html_url']} (строка в CI.md, § 7.3)")
        return 0
    if r["conclusion"] in ("success", "skipped", "cancelled"):
        print(f"main {head[:9]}: {r['conclusion']} — {r['html_url']}")
        return 0
    print(f"main {head[:9]}: КРАСНЫЙ — {r['html_url']}. СРОЧНО (§ 5 п. 2): красный main")
    return 1


def health(repo):
    state, info = staging_health(repo)
    last = info["last"]
    print(f"staging: {state}" + (f" — {last['html_url']}" if last else ""))
    rc = max(stuck(repo), main_ci(repo), 1 if state == "red" else 0)
    transit_warn(repo)
    return rc


def tick(repo, sign):
    rc = max(stuck(repo), main_ci(repo), heal(repo))
    rc = max(rc, train_step(repo, sign))
    transit_warn(repo)
    return rc


def own_numbers(repo, commits):
    """Номера тикетов самого repo из `Touch:` коммитов (Touch: #N и Touch: <repo>#N)."""
    return {int(k.split("#")[1]) for k in tickets(repo, commits) if k.startswith(f"{repo}#")}


def triage_path(repo):
    return os.path.join(ACCOUNTING, "projects", repo.split("/")[1], "TRIAGE.md")


def mark_checking(repo, nums, sign):
    """После вливания поезда: `в пути` → `проверяют` в TRIAGE.md учётного клона (§ 5.1).
    Раньше tick это только печатал, и без ручной правки тикеты висели `в пути` вечно
    (28-09-2026: f4 #659, #1604, #1606). Нет клона/файла, не main, любые незакоммиченные правки в клоне, нет id в
    --sign — только сообщение: правь руками. В коммит идёт только TRIAGE.md (по имени). Комментарии и updatedAt не трогаются."""
    path = triage_path(repo)
    if not nums:
        return
    if not os.path.isdir(os.path.join(ACCOUNTING, ".git")) or not os.path.exists(path):
        print("TRIAGE не правлю (нет учётного клона проекта рядом с train.py): "
              "`в пути` → `проверяют` руками")
        return
    rel = os.path.relpath(path, ACCOUNTING)
    git = lambda *a: run("git", "-c", "user.name=unxed", "-c",
                         "user.email=1151423+unxed@users.noreply.github.com", *a,
                         cwd=ACCOUNTING, check=False)
    if git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != "main":
        print("TRIAGE не правлю: учётный клон не на main — `в пути` → `проверяют` руками")
        return
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        print("TRIAGE не правлю: в учётном клоне есть незакоммиченные правки (чужие не трогаю, "
              "в коммит идёт только TRIAGE.md) — `в пути` → `проверяют` руками")
        return
    m = re.search(r"((?:Лунобот|Lunobot)-\d+ \(node [0-9a-f]+; \w+)", sign or "")
    if not m:
        print("TRIAGE не правлю: в --sign нет id вида `Лунобот-N (node …; ПЛАТФОРМА)` для "
              "трейлера Lunobot-Instance — `в пути` → `проверяют` руками")
        return
    inst = m.group(1) + ")"
    tags = ""
    subject = ""
    for attempt in range(3):  # гонка с другим ботом/менеджером: pull --rebase и повтор
        if git("pull", "--rebase", "-q", "origin", "main").returncode:
            git("rebase", "--abort")
            break
        if not subject:  # правку делаем и коммитим один раз; повторы — только rebase и push
            text = open(path, encoding="utf-8").read()
            done = []

            def fix(mo):
                if int(mo.group(2)) in nums:
                    done.append(int(mo.group(2)))
                    return mo.group(1) + "проверяют" + mo.group(3)
                return mo.group(0)
            new = IN_TRANSIT.sub(fix, text)
            if not done:
                print("TRIAGE: тикетов поезда в состоянии `в пути` нет — править нечего")
                return
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            tags = ", ".join(f"#{n}" for n in sorted(done))
            subject = f"{repo.split('/')[1]}: поезд влит, TRIAGE в пути → проверяют ({tags})"
            git("add", "--", rel)
            if git("commit", "-q", "-m", f"{subject}\n\nLunobot-Instance: {inst}\n", "--", rel).returncode:
                git("checkout", "--", rel)
                break
        if git("push", "-q", "origin", "HEAD:main").returncode == 0:
            print(f"TRIAGE: в пути → проверяют для {tags} (закоммитил и запушил)")
            return
    if subject and git("log", "-1", "--format=%s").stdout.strip() == subject:
        git("reset", "-q", "--hard", "HEAD~1")  # свой непушнутый коммит не оставляем в клоне
    print("TRIAGE: не удалось запушить правку `в пути` → `проверяют` (сеть/гонка) — сделай руками")


def transit_warn(repo):
    """Предупреждение (не ошибка): тикет `в пути` в TRIAGE.md, а его `Touch:` уже в main за
    последние TRANSIT_WINDOW_H ч — «Пробуйте!» не разнесён, состояние не сдвинулось.
    Коммиты без Touch: (эпоха PR) этим не видны — их состояние ведёт автор вручную."""
    try:
        text = open(triage_path(repo), encoding="utf-8").read()
    except OSError:
        return
    transit = {int(m.group(2)) for m in IN_TRANSIT.finditer(text)}
    if not transit:
        return
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - TRANSIT_WINDOW_H * 3600))
    commits = api(f"repos/{repo}/commits?sha=main&since={since}&per_page=100", check=False) or []
    stale = sorted(transit & own_numbers(repo, commits))
    if stale:
        print(f"ПРЕДУПРЕЖДЕНИЕ: `в пути`, но коммиты уже в main (за {TRANSIT_WINDOW_H} ч) — "
              f"нет «Пробуйте!»: {', '.join(f'#{n}' for n in stale)}. Разнеси «Пробуйте!» "
              "(§ 7.2 п. 4) и поставь `проверяют`")


def train_step(repo, sign):
    pr = train_pr(repo)
    if not pr:
        return cut(repo, sign)
    n, head = pr["number"], pr["head"]["sha"]
    checks, pending, failed, cancelled = rollup(repo, n)
    if failed:
        return red(repo, pr, failed)
    if pending:
        print(f"поезд #{n} в пути: {len(pending)} из {len(checks)} проверок ещё идут")
        return 0
    if cancelled:
        runs = {re.search(r"/runs/(\d+)", c.get("detailsUrl", "") or "") for c in cancelled}
        for m in runs - {None}:
            run("gh", "run", "rerun", m.group(1), "--failed", "--repo", repo, check=False)
        print(f"поезд #{n}: {len(cancelled)} проверок отменены (не упали) — перезапустил")
        return 0
    ff = run("gh", "api", "-X", "PATCH", f"repos/{repo}/git/refs/heads/main",
             "-f", f"sha={head}", "-F", "force=false", check=False)
    if ff.returncode == 0:
        how = "fast-forward"
        if repo not in PRESERVE_MAIN:
            time.sleep(5)
            for r in api(f"repos/{repo}/actions/runs?branch=main&head_sha={head}")["workflow_runs"]:
                if r["event"] == "push" and r["status"] != "completed":
                    run("gh", "run", "cancel", str(r["id"]), "--repo", repo, check=False)
        api(f"repos/{repo}/git/refs/heads/{pr['head']['ref']}", "-X", "DELETE", check=False)
    else:
        run("gh", "pr", "merge", str(n), "--repo", repo, "--merge", "--delete-branch")
        how = "merge-коммит (main ушёл вперёд — прогон main не отменять, § 7.3)"
    if repo in TAG_AFTER_MERGE:
        tag_next(repo)
    print(f"поезд #{n} ВЛИТ ({how}). Теперь по каждому тикету — «Пробуйте!» с текстом ниже "
          "и подписью (§ 7.3, § 9); TRIAGE → проверяют tick ставит сам, ниже итог:")
    commits = compare(repo, pr["base"]["sha"], head)["commits"]
    for key, texts in tickets(repo, commits).items():
        print(f"--- {key}")
        for t in texts:
            print(t)
    mark_checking(repo, own_numbers(repo, commits), sign)
    return 0


def tag_next(repo):
    """Следующий последовательный тег vX.Y.Z на вершине main (если она ещё без тега)."""
    head = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    tags = api(f"repos/{repo}/tags?per_page=100") or []
    if any(t["commit"]["sha"] == head for t in tags):
        return
    vers = [tuple(map(int, m.groups())) for t in tags
            if (m := re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", t["name"]))]
    if not vers:
        print(f"{repo}: нет тегов vX.Y.Z — тег не ставлю, реши вручную")
        return
    a, b, c = max(vers)
    tag = f"v{a}.{b}.{c + 1}"
    r = run("gh", "api", f"repos/{repo}/git/refs", "-f", f"ref=refs/tags/{tag}", "-f",
            f"sha={head}", check=False)
    print(f"{repo}: тег {tag} на {head[:9]}" if r.returncode == 0 else
          f"{repo}: тег {tag} не создан: {r.stderr.strip()}")


def eject(repo, shas, reason):
    pr = train_pr(repo)
    with tempfile.TemporaryDirectory() as d:
        run("git", "clone", "-q", "--filter=blob:none", "--branch", STAGING,
            f"https://github.com/{repo}.git", d)
        for sha in shas:
            r = run("git", "revert", "--no-edit", sha, cwd=d, check=False)
            if r.returncode:
                print(f"revert {sha[:9]} не лёг чисто — СРОЧНО (§ 5 п. 2): откатить руками в "
                      f"клоне staging или починить вперёд ({reason}). Вердикт бисекта сохранён, "
                      "повторного бисекта не будет.")
                return 1
            msg = run("git", "log", "-1", "--format=%B", cwd=d).stdout
            run("git", "commit", "-q", "--amend", "-m",
                f"{msg.rstrip()}\n\nВыкинут из поезда: {reason}", cwd=d)
        run("git", "push", "-q", "origin", f"HEAD:{STAGING}", cwd=d)
    if pr:
        close_train(repo, pr, f"Красный поезд; выкинуты из staging: "
                    f"{', '.join(s[:9] for s in shas)} ({reason}). Следующий поезд режется без них.")
    print("выкинуто; авторам — вернуть тикет в работу с этой ссылкой (§ 7.2)")
    return 0


def staged_repos():
    """Репозитории проектов из projects/INDEX.md (в порядке приоритета), у которых есть staging.
    Раньше tick звали по одному проекту руками — и vtui 28-09-2026 простоял 7 часов с
    необработанным поездом, потому что координатор помнил только про f4."""
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")
    out = []
    for name in re.findall(r"^\d+\.\s*\[([^\]]+)\]", open(os.path.join(root, "INDEX.md"),
                                                         encoding="utf-8").read(), re.M):
        try:
            text = open(os.path.join(root, name, "PROJECT.md"), encoding="utf-8").read()
        except OSError:
            continue
        m = re.search(r"^- Код: https://github\.com/([^/\s]+/[^/\s]+)", text, re.M)
        if m and "commit" in (api(f"repos/{m.group(1)}/branches/{STAGING}", check=False) or {}):
            out.append(m.group(1))
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    opt = lambda k: rest[rest.index(k) + 1] if k in rest else None
    if cmd == "land":
        return land(fix="--fix-staging" in rest)
    if cmd == "tick-all" and opt("--sign"):
        rc = 0
        for repo in staged_repos():
            print(f"=== {repo}")
            rc = max(rc, tick(repo, opt("--sign")))
        return rc
    if cmd == "health" and len(rest) == 1:
        return health(rest[0])
    if cmd == "covered" and len(rest) == 2:
        return covered(rest[0], rest[1])
    if cmd == "tick" and rest and opt("--sign"):
        return tick(rest[0], opt("--sign"))
    if cmd == "bisect" and rest and opt("--os") and opt("--cmd"):
        pr = train_pr(rest[0])
        if not pr:
            sys.exit("поезда в пути нет")
        bisect(rest[0], pr, opt("--os"), opt("--cmd"))
        return 0
    if cmd == "close-train" and len(rest) >= 2 and rest[1].isdigit():
        return close_train_cmd(rest[0], int(rest[1]), opt("--reason"))
    if cmd == "eject" and len(rest) >= 2 and opt("--reason"):
        shas = [a for a in rest[1:rest.index("--reason")]]
        return eject(rest[0], shas, opt("--reason"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
