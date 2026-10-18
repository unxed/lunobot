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

land  — коммит, правящий go.mod/go.sum (bump зависимости), приземляется только с трейлером
        `Sandbox-Full: <ссылка на зелёный прогон sandbox.yml>` на коммите с тем же патчем
        (полный `go vet ./... && go test ./...`, § 7.2). При свежей строке «объявляю заморозку land проекта …» в DISPATCH.md учёта (≤ 25 минут,
        § 7.2 п. 0) отказывает: коммит паркуется. Иначе переносит твои коммиты (origin/lunobot/staging..HEAD) на вершину staging и пушит,
        с повторами при гонке. PR не открывает никогда. Staging красный (последний
        завершённый quick упал и починки после него нет) — ОТКАЗЫВАЕТ: конвейер стоит, пока
        его не починят (§ 7.2 п. 0). Починка — с --fix-staging и трейлером `Fixes-Staging:`.
health — только чтение: состояние staging и сколько часов main не двигался; для ретро круга.
        Плюс предупреждение (код не меняет): тикеты `в пути` в TRIAGE.md, чьи `Touch:` уже в main.
        И (здесь же и в tick-all) предупреждение о нарушениях формата в любом projects/*/DISPATCH.md:
        полный check_dispatch без --added-only, без протухания; код возврата не меняет.
covered — быстрый ответ автору после land: зелёный/красный/ещё едет — по первому завершённому
        quick на его коммите или потомке (quick на staging не отменяется, каждый прогон доезжает).
tick  — идемпотентный шаг проводника; запускай в начале каждого круга. Сначала лечит staging:
        красный quick — один перезапуск, снова красный — откатывает виновника (коммиты между
        последним зелёным и первым красным quick, не больше трёх; больше — срочная задача).
        Поезд в пути: зелёный — вливает (fast-forward main, иначе merge-коммит; прогон main после
        fast-forward отменяет, кроме PRESERVE_MAIN и f4 при устаревшем nightly) и, если tick
        запущен из учётного клона, сам правит в TRIAGE.md `в пути` → `проверяют` по `Touch:`
        коммитов поезда (коммит+пуш с `Lunobot-Instance:`), кроме тикетов, чей `Touch:`-коммит
        ещё в staging впереди влитой головы (они остаются `в пути`, tick их называет); красный — бисект и выкидывание; поезда нет — режет новый поезд ТОЛЬКО до последнего коммита
        staging с зелёным quick и не режет, пока после него в staging есть коммит-починка
        (Fixes-Staging:/Staging-Revert:) — ждёт зелёного quick вершины. Печатает, сколько часов main не двигался; больше двух —
        ИНЦИДЕНТ ПРОЦЕССА, код 1.
bisect — вручную, когда падение платформенное/узкое и автоматический бисект (команда по ИМЕНИ
        упавшего шага упавшего job'а, таблица STEP_CMDS; для тестов f4 — с seed и пакетом из лога; неизвестный шаг — бисекта нет, сразу
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
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit

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
# «Проверить:» — текст для автора тикета, его поезд кладёт в «Пробуйте!» (§ 7.2 п. 1). Текст
# допустим и в той же строке, и со следующей: до 13-10-2026 CHECK понимал только второй вид и
# молча терял первый (из 300 коммитов main f4 — 57 нормальных текстов и 21 команда go test, в
# том числе оба коммита поезда unxed/f4#1889), а пустую секцию перед трейлерами читал как текст
# «Lunobot-Instance: … Co-Authored-By: …». Конец секции — пустая строка перед трейлером.
CHECK = re.compile(r"^Проверить:[ \t]*(.*?)(?=\n\s*\n(?:[A-Z][\w-]+|Проблема|Исправление):|\Z)",
                   re.M | re.S)
# Команда вместо текста: пользователю в «Пробуйте!» она ни к чему, land такой коммит не пускает.
CHECK_COMMAND = re.compile(r"^\s*(\$ |go (test|vet|build|run)\b|(make|python3?|bash|sh|npm|cargo)\s|\./)", re.M)


def check_text(body):
    """Текст секции «Проверить:» (может быть пустым) или None, если секции нет."""
    m = CHECK.search(body)
    return m.group(1).strip() if m else None


def check_section_problem(body):
    """Почему секция «Проверить:» коммита не годится для «Пробуйте!», или None.

    Секция обязательна у коммита с Touch: (у него есть автор тикета); у коммита только с
    Lunobot-Task: её может не быть (кастомная задача без пользовательской стороны)."""
    touch = any(kind == "Touch" for kind, _ in TRAILER.findall(body))
    text = check_text(body)
    if not text:
        return "нет текста «Проверить:» для автора тикета" if touch else None
    if CHECK_COMMAND.search(text):
        return ("в «Проверить:» команда, а не текст для автора тикета: напиши 1–3 предложения "
                "на его языке — что и где проверить в программе (команды тестов — в тело "
                "коммита выше, не в эту секцию)")
    return None


# Коммит, меняющий зависимости модуля (go.mod/go.sum корня: bump vtui и др.), ломает пакеты,
# которых автор не трогал: 15-10-2026 f4 `26918fda` (bump vtui v0.1.405) прошёл песочницу с
# lint и `go test ./cmd/f4/`, а `internal/settings` (TestSettingsSidebarSearchAndContentSurface)
# покраснел, и staging с `land` стояли весь флот. Такой коммит перед `land` проходит ПОЛНЫЙ
# `go vet ./... && go test ./...` в песочнице, ссылка на прогон — трейлер `Sandbox-Full:`.
DEPS_FILES = ("go.mod", "go.sum")
SANDBOX_FULL = re.compile(
    r"^Sandbox-Full:\s*https://github\.com/([\w.-]+/[\w.-]+)/actions/runs/(\d+)\s*$", re.M)


def touches_deps(files):
    """Правит ли список файлов зависимости корневого модуля (вложенные модули — свои go.mod)."""
    return any(f in DEPS_FILES for f in files)


def patch_id(sha):
    """Стабильный patch-id коммита (не зависит от сообщения и от базы после rebase)."""
    # Байты, а не текст: патч с кириллицей не должен падать на кодировке консоли (Windows), а
    # diff-tree (plumbing) не знает внешних diff-драйверов, цвета и переименований из конфигурации.
    show = subprocess.run(["git", "diff-tree", "-p", "--root", sha], capture_output=True)
    if show.returncode:
        return None
    p = subprocess.run(["git", "patch-id", "--stable"], input=show.stdout, capture_output=True)
    out = p.stdout.decode("ascii", "replace").split()
    return out[0] if p.returncode == 0 and out else None


def deps_sandbox_problem(repo, sha, body):
    """Почему коммит, правящий go.mod/go.sum, нельзя приземлять, или None.

    Нужен трейлер `Sandbox-Full: <ссылка на прогон sandbox.yml>`: прогон этого репозитория,
    workflow_dispatch, завершён успешно, на коммите с тем же патчем (patch-id), что и приземляемый.
    Что именно гонялось в прогоне, API не отдаёт — команда `go vet ./... && go test ./...`
    закреплена в LUNOBOT.md § 7.2 и проверяется ревью, но чужой или устаревший прогон гейт ловит."""
    m = SANDBOX_FULL.search(body)
    if not m:
        return ("коммит правит go.mod/go.sum: нужен трейлер `Sandbox-Full: <ссылка на прогон "
                "sandbox.yml>` с полным `go vet ./... && go test ./...` (§ 7.2) — зависимость "
                "ломает пакеты, которых автор не трогал")
    run_repo, run_id = m.group(1), m.group(2)
    if run_repo.lower() != repo.lower():
        return f"Sandbox-Full: прогон чужого репозитория {run_repo}, нужен {repo}"
    r = api(f"repos/{repo}/actions/runs/{run_id}", check=False)
    if not isinstance(r, dict) or "status" not in r:
        return f"Sandbox-Full: прогон {run_id} не найден"
    if r.get("event") != "workflow_dispatch" or not str(r.get("path", "")).endswith("sandbox.yml"):
        return f"Sandbox-Full: прогон {run_id} — не sandbox.yml через workflow_dispatch"
    if r.get("status") != "completed" or r.get("conclusion") != "success":
        return (f"Sandbox-Full: прогон {run_id} не зелёный "
                f"({r.get('status')}/{r.get('conclusion')})")
    tested = r.get("head_sha") or ""
    if run("git", "fetch", "-q", "origin", tested, check=False).returncode:
        return f"Sandbox-Full: не удалось получить коммит {tested[:9]} прогона {run_id}"
    mine, theirs = patch_id(sha), patch_id(tested)
    if not mine or mine != theirs:
        return (f"Sandbox-Full: прогон {run_id} шёл на коммите {tested[:9]} с другим патчем — "
                "повтори полный прогон на приземляемом коде")
    return None


# Очень короткая сводка для тела PR поезда: «Проблема:» и «Исправление:» в сообщении коммита,
# по одной строке каждая (LUNOBOT.md § 7.2 п. 1). Без них в тело идёт заголовок коммита.
SUMMARY_LEN = 200
PROBLEM = re.compile(r"^Проблема:[ \t]*(.+)$", re.M)
FIXED = re.compile(r"^Исправление:[ \t]*(.+)$", re.M)
# Коммит, чинящий красный staging: ручная починка (land --fix-staging) или автооткат tick'а.
HEAL = re.compile(r"^(Fixes-Staging|Staging-Revert):", re.M)
# Автокоммит бота с новым vendorHash в flake.nix (workflow nix-vendor-hash): несёт Fixes-Staging,
# но правит один flake.nix, а quick его не проверяет.
VENDOR_SYNC = re.compile(r"^Lunobot-Task: vendorhash-autosync\s*$", re.M)
# Больше стольких коммитов между последним зелёным и первым красным quick — откатывать
# вслепую нельзя (заденет чужую работу), нужен бот: срочная задача § 5 п. 2.
MAX_AUTO_REVERT = 3
# Сколько минут tick ждёт зелёного quick на вершине staging, когда после последнего зелёного
# лежит коммит-починка (cut). Дольше — выход в § 5 п. 2: quick мог не запуститься вовсе
# (paths-ignore `**.md`/`docs/**` в quick.yml, отмена), и ждать вечно нельзя.
HEAL_WAIT_MIN = 45
MAIN_FLAKE_MAX_JOBS = 2  # упало не больше стольких job'ов на первой попытке — один перезапуск
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


API_RETRIES = 3
# Обрыв связи посреди ответа (мобильный интернет): `gh` печатает эти тексты в stderr, повтор обычно проходит.
# `": EOF` — голый EOF Go-клиента (`Get "https://…": EOF`), без слов «unexpected» (18-10-2026, `tick unxed/f4`).
# `HTTP 502/503/504` — шлюз GitHub не ответил вовремя (18-10-2026, `tick-all` остановил vtui на `504`: «We couldn't respond to your request in time»).
API_TRANSIENT = ("unexpected end of JSON input", "unexpected EOF", "stream error", "i/o timeout",
                 "TLS handshake timeout", "connection reset by peer", '": EOF',
                 "HTTP 502", "HTTP 503", "HTTP 504")


def api_transient(p):
    return any(t in (p.stderr or "") for t in API_TRANSIENT)


def api_is_read(cmd):
    """Запрос ничего не меняет: GET без полей (`-f`/`-F`/`--input` делают его POST) — только такой повторяют."""
    for i, a in enumerate(cmd):
        if a in ("-X", "--method") and i + 1 < len(cmd):
            return cmd[i + 1].upper() == "GET"
    return not any(a in ("-f", "-F", "--field", "--raw-field", "--input") for a in cmd)


def api(path, *args, check=True):
    # gh api on Windows does not reliably interpret a slash-containing query value
    # when it is embedded in the endpoint string (for example
    # `?branch=lunobot/staging`).  Pass query parameters as explicit GET fields so
    # staging health and train selection inspect the actual branch instead of an
    # unrelated page of workflow runs.
    parsed = urlsplit(path)
    cmd = list(args)
    if parsed.query:
        if not any(arg in ("-X", "--method") for arg in cmd):
            cmd[:0] = ["-X", "GET"]
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            cmd.extend(["-f", f"{key}={value}"])
    argv = ("gh", "api", parsed.path, *cmd)
    for attempt in range(API_RETRIES):
        p = run(*argv, check=False)
        if p.returncode == 0 or not api_transient(p) or not api_is_read(cmd):
            break
        if attempt + 1 < API_RETRIES:
            time.sleep(2 * (attempt + 1))
    if check and p.returncode:
        sys.exit(f"{' '.join(argv)}: {p.stderr.strip() or p.stdout.strip()}")
    return json.loads(p.stdout) if p.stdout.strip() else None


def api_list(path, *args):
    """Список из ответа API. Тело ошибки GitHub (`{"message": …}`, лимит запросов, 5xx) или пустой
    ответ — пустой список: `api(..., check=False) or []` пропускает словарь, а перебор словаря
    даёт строки и роняет круг на `c.get` (14-10-2026 тот же класс ошибки уже ронял `tick-all`
    в `ensure_quick_on_tip`, KeyError 'commit')."""
    data = api(path, *args, check=False)
    return data if isinstance(data, list) else []


def push_ref(repo, branch, sha):
    """Создать или продвинуть ветку git push-ем (не force: только вперёд), когда REST
    закрыт для записи ссылок (прокси облачных сессий Claude Code отвечает 403 на
    git/refs). Коммит берётся в объекты учётного клона мелким fetch по SHA; ответ
    в форме REST, чтобы его понял ref_created."""
    url = f"https://github.com/{repo}"
    if run("git", "fetch", "-q", "--depth=1", url, sha, check=False).returncode:
        return None
    if run("git", "push", "-q", url, f"{sha}:refs/heads/{branch}", check=False).returncode:
        return None
    return {"ref": f"refs/heads/{branch}", "object": {"sha": sha}}


def existing_ref(path):
    """Ответ git/ref, если ветка есть, иначе None. `gh api` при 404 печатает в stdout JSON
    `{"message": "Not Found", ...}`, и api() его разбирает: такой словарь не ссылка на ветку.
    Ссылкой считается только ответ с object.sha (иначе поезд никогда не создавался,
    а `gh pr create` падал «Head sha can't be blank»)."""
    r = api(path, check=False)
    if isinstance(r, dict) and isinstance(r.get("object"), dict) and r["object"].get("sha"):
        return r
    return None


def ref_created(resp):
    """Ответ POST git/refs — успех, только если в нём есть созданная ссылка."""
    return isinstance(resp, dict) and bool(resp.get("ref") or resp.get("object"))


def origin_repo():
    url = run("git", "remote", "get-url", "origin", check=False).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else None


def quick_runs(repo):
    """Завершённые (не отменённые) прогоны quick на staging, новые первыми."""
    # Передача branch=lunobot/staging через `gh api -f` на Windows иногда возвращает
    # старую страницу runs. Берём свежую страницу без slash-фильтра и фильтруем branch
    # локально, чтобы не принять зелёный quick чужой ветки за проверку staging.
    rs = api(f"repos/{repo}/actions/workflows/quick.yml/runs?per_page=100")
    rs = [r for r in rs["workflow_runs"] if r.get("head_branch") == STAGING
          and r["status"] == "completed"
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
        # blocks_cut, не голый HEAL: автокоммит vendorHash несёт Fixes-Staging, но ничего не
        # чинит (правит один flake.nix). Иначе после красного quick один такой коммит давал
        # «healing» и land поверх красного, хотя красное осталось.
        if any(blocks_cut(c) for c in after):
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


def blocks_cut(c):
    """Коммит-починка, из-за которого поезд ждёт зелёного quick на вершине staging.
    Автокоммит vendorHash (VENDOR_SYNC) не в счёт: он правит только flake.nix, а quick
    не проверяет ни его, ни Nix; ждать нового зелёного quick после него нечего, и каждый
    такой коммит после очередного land сдвигал вершину и не давал поезду нарезаться."""
    msg = c["commit"]["message"]
    return bool(HEAL.search(msg)) and not VENDOR_SYNC.search(msg)


def extend_over_vendorhash(cut_sha, after):
    """Поезд режется по коммиту с зелёным quick; сразу за ним подряд лежащие автокоммиты
    vendorHash (after — коммиты staging после него, старые первыми) едут в поезде тоже:
    иначе main получит go.mod без своего хэша до следующего поезда."""
    for c in after:
        if len(c["parents"]) == 1 and VENDOR_SYNC.search(c["commit"]["message"]):
            cut_sha = c["sha"]
        else:
            break
    return cut_sha


def vendorsync_to_revert(after, culprit_shas, gomod_shas):
    """Автокоммиты vendorHash (VENDOR_SYNC), которые heal обязан откатить вместе с виновниками.
    after — коммиты staging начиная с первого виновника, старые первыми; culprit_shas —
    откатываемые коммиты; gomod_shas — коммиты из after, правившие go.mod/go.sum. Откат
    виновника, правившего go.mod, возвращает go.mod/go.sum, а vendorHash в flake.nix остаётся
    от откатанного набора зависимостей: nix-проверки красные (поезд #1968, 15-10-2026).
    Если после первого виновника go.mod правил ещё кто-то не откатываемый, правильный хэш
    теперь другой и откатом его не вернуть — тогда пусто (хэш пересчитает автокоммит).
    Возвращает sha, новые первыми (порядок отката)."""
    if not set(gomod_shas) & set(culprit_shas):
        return []
    if set(gomod_shas) - set(culprit_shas):
        return []
    sync = [c["sha"] for c in after
            if len(c["parents"]) == 1 and VENDOR_SYNC.search(c["commit"]["message"])
            and c["sha"] not in culprit_shas]
    return sync[::-1]


def who(c):
    msg = c["commit"]["message"]
    keys = [v.strip() for _, v in TRAILER.findall(msg)]
    return f"{c['sha'][:9]} {msg.splitlines()[0][:70]} [{', '.join(keys) or 'без трейлера'}]"


FREEZE_RE = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}) .*объявляю заморозку land проекта (\S+)", re.M)
FREEZE_MIN = 25


def active_freeze(text, project, now=None):
    """Свежая строка «объявляю заморозку land проекта <проект>» в тексте DISPATCH.md
    (LUNOBOT.md § 7.2, п. 0): не старше FREEZE_MIN минут, время в UTC. Иначе None."""
    now = now or datetime.now(timezone.utc)
    for stamp, name in FREEZE_RE.findall(text):
        if name.rstrip(".,;") != project:
            continue
        try:
            ts = datetime.strptime(stamp, "%d-%m-%Y %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue  # невозможная дата в строке — не заморозка, но и не повод ронять land
        if timedelta(0) <= now - ts < timedelta(minutes=FREEZE_MIN):
            return stamp
    return None


def freeze_stamp(repo):
    """Метка времени свежей заморозки проекта в учёте (origin/main), либо None. Учёт
    недоступен — заморозки нет: land не должен падать из-за сети к учёту."""
    if not os.path.isdir(os.path.join(ACCOUNTING, ".git")):
        return None
    project = repo.split("/")[1]
    run("git", "-C", ACCOUNTING, "fetch", "-q", "origin", "main", check=False)
    p = run("git", "-C", ACCOUNTING, "show", f"origin/main:projects/{project}/DISPATCH.md",
            check=False)
    return active_freeze(p.stdout, project) if p.returncode == 0 else None


def parse_land_commits(output):
    """Parse git log records; git inserts a newline before later format records."""
    parsed = []
    for record in output.split("\x01"):
        if not record.strip():
            continue
        sha, body = record.split("\0", 1)
        parsed.append((sha.strip(), body))
    return parsed


def healed_by_revert(fix_bodies, staging_bodies):
    """Ссылка из `Fixes-Staging:` в коммитах приземляемой починки, на которую в staging уже есть
    `Staging-Revert:` (tick откатил виновного раньше), либо None. Починка вперёд, приземлённая
    после такого отката, чинит то, чего в staging уже нет, и сама его ломает."""
    fixed = {m.group(1) for body in fix_bodies
             for m in re.finditer(r"^Fixes-Staging:\s*(\S+)", body, re.M)}
    for body in staging_bodies:
        for m in re.finditer(r"^Staging-Revert:\s*(\S+)", body, re.M):
            if m.group(1) in fixed:
                return m.group(1)
    return None


def land(fix=False):
    run("git", "fetch", "-q", "origin", STAGING_REFSPEC)
    commits = run("git", "log", "--format=%H%x00%B%x01", f"origin/{STAGING}..HEAD").stdout
    msgs = parse_land_commits(commits)
    if not msgs:
        sys.exit("нечего приземлять: HEAD не впереди origin/lunobot/staging")
    bad = [sha[:9] for sha, body in msgs if not TRAILER.search(body)]
    if bad:
        sys.exit(f"коммиты без трейлера Touch:/Lunobot-Task: {', '.join(bad)} — проводник не "
                 "сможет разнести «Пробуйте!» по тикетам; допиши трейлер (git commit --amend)")
    bad = [f"{sha[:9]}: {why}" for sha, body in msgs if (why := check_section_problem(body))]
    if bad:
        sys.exit("секция «Проверить:» не годится (§ 7.2 п. 1), поправь (git commit --amend / "
                 "rebase -i):\n  " + "\n  ".join(bad))
    repo = origin_repo()
    if repo:
        bad = []
        for sha, body in msgs:
            files = run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha).stdout.split()
            if touches_deps(files) and (why := deps_sandbox_problem(repo, sha, body)):
                bad.append(f"{sha[:9]}: {why}")
        if bad:
            sys.exit("коммит с изменением зависимостей без полного прогона (§ 7.2), поправь:\n  "
                     + "\n  ".join(bad))
    if fix and not any(re.search(r"^Fixes-Staging:", body, re.M) for _, body in msgs):
        sys.exit("--fix-staging: хотя бы один коммит обязан нести трейлер "
                 "`Fixes-Staging: <ссылка на красный quick>` — по нему остальные поймут, что "
                 "staging лечится, и снова смогут приземлять")
    if fix:
        log = run("git", "log", "-50", "--format=%B%x01", f"origin/{STAGING}").stdout
        healed = healed_by_revert([body for _, body in msgs], log.split("\x01"))
        if healed:
            sys.exit(f"--fix-staging: красный {healed} уже вылечен откатом (`Staging-Revert:` на "
                     "эту же ссылку лежит в staging), починка вперёд поверх отката ломает "
                     "согласованность: код откачен, а правка тестов/ожиданий ждёт его "
                     "(16-10-2026..17-10-2026, f4#1148). Приземли код и правку ВМЕСТЕ как обычную "
                     "работу (`land` без флага, песочница на точном коде), а не как починку.")
    if repo and not fix:
        frozen = freeze_stamp(repo)
        if frozen:
            sys.exit(f"ЗАМОРОЗКА land проекта {repo.split('/')[1]} (строка от {frozen} UTC в "
                     "DISPATCH.md учёта, § 7.2 п. 0): поезд ждёт нарезки. Не приземляй — "
                     "запаркуй коммит в клоне (§ 5 п. 2), работа и песочница продолжаются; "
                     f"заморозка истекает через {FREEZE_MIN} минут после метки.")
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


def rollup_rest(repo, number):
    """statusCheckRollup через REST: в облачных сессиях Claude Code GraphQL закрыт прокси
    (`gh pr view --json` отвечает 403), а tick без него не может разобрать поезд.
    Приводит check-runs и commit statuses к виду, который отдаёт GraphQL."""
    head = api(f"repos/{repo}/pulls/{number}")["head"]
    sha, ref = head["sha"], head.get("ref")
    # Прогоны того же коммита с ДРУГИХ веток — не проверки поезда: песочница бота
    # (sandbox.yml, workflow_dispatch на tmp/<узел>/...) на вершине поезда падала и делала
    # поезд «красным», tick перезапускал её и шёл бы в бисект (14-10-2026, unxed/vtui#216).
    suites = api(f"repos/{repo}/commits/{sha}/check-suites?per_page=100", check=False) or {}
    foreign = {st["id"] for st in suites.get("check_suites", [])
               if ref and st.get("head_branch") not in (None, ref)}
    checks = []
    for page in range(1, 11):
        runs = api(f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page={page}")
        for r in runs.get("check_runs", []):
            if (r.get("check_suite") or {}).get("id") in foreign:
                continue
            checks.append({
                "name": r["name"],
                "status": (r.get("status") or "completed").upper(),
                "conclusion": (r.get("conclusion") or "").upper() or None,
                # rerun() берёт id прогона отсюда; без этого поля tick в облаке писал
                # «перезапуск», а перезапуска не было (09-10-2026, поезд #1843).
                "detailsUrl": r.get("details_url") or r.get("html_url") or "",
            })
        if len(runs.get("check_runs", [])) < 100:
            break
    for st in api(f"repos/{repo}/commits/{sha}/status").get("statuses", []):
        checks.append({"name": st.get("context", ""), "state": st["state"].upper()})
    return checks


def green_train_covering(repo, staging_sha):
    """Return an open train whose green checks already cover the staging tip.

    A train in this state is the normal last step before main: its staging
    commits are not missing from main because the merge is still pending.  It
    must not make ``stuck`` report an incident based on the age of the oldest
    commit.  Pending, failed, cancelled, or empty rollups deliberately do not
    suppress the incident.
    """
    pr = train_pr(repo)
    if not pr or pr["head"]["sha"] != staging_sha:
        return None
    checks, pending, failed, cancelled = rollup(repo, pr["number"])
    if checks and not pending and not failed and not cancelled:
        return pr
    return None


def rollup(repo, number):
    p = run("gh", "pr", "view", str(number), "--repo", repo,
            "--json", "statusCheckRollup", check=False)
    if p.returncode == 0:
        checks = json.loads(p.stdout)["statusCheckRollup"]
    else:
        checks = rollup_rest(repo, number)
    # codecov/* — informational (f4/vtui PROJECT.md): ждут вечно и блокируют tick
    # (05-10-2026 поезд unxed/f4#1756: staging 12 ч, main стоял на codecov/project).
    material = [c for c in checks
                if not (c.get("name") or "").lower().startswith("codecov/")]
    pending = [c for c in material if c.get("status", "COMPLETED") != "COMPLETED"
               or c.get("state") == "PENDING"]
    failed = [c for c in material if (c.get("conclusion") or c.get("state"))
              in ("FAILURE", "TIMED_OUT", "STARTUP_FAILURE", "ERROR", "ACTION_REQUIRED")]
    cancelled = [c for c in material if c.get("conclusion") == "CANCELLED"]
    return checks, pending, failed, cancelled


def compare(repo, base, head):
    return api(f"repos/{repo}/compare/{base}...{head}")


REVERTS = re.compile(r"^This reverts commit ([0-9a-f]{7,40})\.", re.M)


def live(commits):
    """Коммиты поезда без откатанных в нём же: коммит, чей откат (`git revert`, «This reverts
    commit <sha>.») едет в том же поезде, и сам этот откат в main ничего не приносят —
    «Пробуйте!» по ним не пишется и тикет не уходит в «проверяют» (13-10-2026 поезд
    unxed/f4#1907 вёз 2fe2ef8 вместе с откатом cfaec5c, а tick разнёс «Пробуйте!» для f4#912).
    Откат коммита, который уже был в main до поезда, остаётся: это настоящее изменение."""
    shas = [c.get("sha") or "" for c in commits]

    def in_train(ref):
        return next((sha for sha in shas if sha and (sha.startswith(ref) or ref.startswith(sha))), None)

    drop = set()
    for c in commits:
        for ref in REVERTS.findall(c["commit"]["message"]):
            target = in_train(ref)
            if target and c.get("sha"):
                drop.update((target, c["sha"]))
    return [c for c in commits if (c.get("sha") or "") not in drop]


def exclude_reverted(commits):
    """Exclude commits whose changes are reverted by a later commit in this history.

    Unlike ``live()``, retain the revert commit itself: its age is the age of the
    latest change to the staging history and it must still count toward ``stuck``.
    """
    shas = [c.get("sha") or "" for c in commits]
    reverted = set()
    for c in commits:
        for ref in REVERTS.findall(c["commit"]["message"]):
            target = next((sha for sha in shas if sha and
                           (sha.startswith(ref) or ref.startswith(sha))), None)
            if target:
                reverted.add(target)
    return [c for c in commits if (c.get("sha") or "") not in reverted]


def tickets(repo, commits):
    """{ключ: [тексты «Проверить»]} по трейлерам коммитов поезда (без откатанных в нём же)."""
    out = {}
    for c in live(commits):
        msg = c["commit"]["message"]
        if len(c.get("parents", [])) > 1:
            continue
        chk = check_text(msg)
        if chk and CHECK_COMMAND.search(chk):
            chk = None  # приземлён до проверки в land: команду пользователю не отдаём
        for kind, val in TRAILER.findall(msg):
            key = val.strip()
            if kind == "Touch" and key.startswith("#"):
                key = f"{repo}{key}"
            out.setdefault(key, [])
            if chk:
                out[key].append(chk)
    return out


def _short(text):
    text = " ".join(text.split())
    return text if len(text) <= SUMMARY_LEN else text[:SUMMARY_LEN - 1].rstrip() + "…"


def summaries(repo, commits):
    """{ключ: {"problem": [..], "fix": [..]}} для тела PR поезда: очень короткая сводка
    проблемы и очень короткая сводка исправления из секций «Проблема:»/«Исправление:» сообщения
    коммита; нет секции исправления — заголовок коммита. Повторы убираются."""
    out = {}
    for c in live(commits):
        msg = c["commit"]["message"]
        if len(c.get("parents", [])) > 1:
            continue
        found = TRAILER.findall(msg)
        if not found:
            continue
        subject = msg.splitlines()[0].strip() if msg.strip() else ""
        problem = PROBLEM.search(msg)
        fixed = FIXED.search(msg)
        for kind, val in found:
            key = val.strip()
            if kind == "Touch" and key.startswith("#"):
                key = f"{repo}{key}"
            entry = out.setdefault(key, {"problem": [], "fix": []})
            if problem and _short(problem.group(1)) not in entry["problem"]:
                entry["problem"].append(_short(problem.group(1)))
            fix = _short(fixed.group(1)) if fixed else _short(subject)
            if fix and fix not in entry["fix"]:
                entry["fix"].append(fix)
    return out


def pick_green(repo, main_sha, staging_sha, runs):
    """Последний коммит staging с зелёным quick, до которого можно резать поезд: впереди main,
    предок вершины staging и СОДЕРЖИТ текущий main (behind_by == 0). Коммит до слияния main в
    staging конфликтует с main, поезд не получает прогона (01-10-2026 поезда unxed/f4#1717 и
    #1718 были порезаны от такого коммита и закрыты)."""
    for r in runs:
        if r["conclusion"] != "success":
            continue
        c = compare(repo, main_sha, r["head_sha"])
        if c.get("ahead_by", 0) > 0 and c.get("behind_by", 0) == 0 \
                and compare(repo, r["head_sha"], staging_sha)["status"] in ("ahead", "identical"):
            return r
    return None


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
            if "not permitted through this proxy" in (r.stderr or "") + (r.stdout or ""):
                # Облачная сессия: REST `merges` закрыт прокси (403), конфликта может и не быть.
                print(f"слияние main в {STAGING} через REST закрыто прокси (облачная сессия) — "
                      f"слей в клоне: `git fetch origin main {STAGING}; git checkout -B w-merge origin/{STAGING}; "
                      f"git merge origin/main` (при конфликте в go.mod/go.sum/flake.nix — рецепт в PROJECT.md "
                      f"проекта) и `git push origin w-merge:{STAGING}`")
                return 1
            print(f"main не вливается в staging без конфликта — срочная работа (§ 5 п. 2): "
                  f"разреши вручную в клоне и запушь в {STAGING}\n{r.stderr.strip()}")
            return 1
        print("влил main в staging (там были коммиты мимо поезда)")
        return train_step(repo, sign)
    # Поезд режется только до последнего коммита staging с зелёным quick: красный кусок
    # staging в поезд не едет никогда. Иначе поезд заведомо красный, а бисект по нему ищет
    # виновника в «базе, которая сама красная» (инцидент 28-09-2026, #1611–#1620).
    green = pick_green(repo, main_sha, staging["commit"]["sha"], quick_runs(repo))
    if not green:
        print("в staging нет ни одного коммита впереди main с зелёным quick — поезд не режется; "
              "если staging красный, это § 5 п. 2 (см. выше)")
        return 0
    cut_sha = green["head_sha"]
    after_green = compare(repo, cut_sha, staging["commit"]["sha"])["commits"]
    heal_wait = [c for c in after_green if blocks_cut(c)]
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
    cut_sha = extend_over_vendorhash(cut_sha, after_green)
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
    existing = existing_ref(ref_path)
    if existing and existing["object"]["sha"] != cut_sha:
        branch = f"{branch}-{cut_sha[:9]}"
        ref_path = f"repos/{repo}/git/ref/heads/{branch}"
        existing = existing_ref(ref_path)
    if not existing:
        created = api(f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{branch}",
                      "-f", f"sha={cut_sha}", check=False)
        if not ref_created(created):
            created = push_ref(repo, branch, cut_sha) or created
        if not ref_created(created):
            # Ошибка (422 и т. п.) приходит JSON-ом с `message`, а не None: успехом
            # считается только ответ с ref/object. Ветку мог создать параллельный tick.
            existing = existing_ref(ref_path)
            if not existing:
                why = created.get("message") if isinstance(created, dict) else None
                sys.exit(f"не удалось создать ветку поезда {branch}" + (f": {why}" if why else ""))
    tk = tickets(repo, own)
    short = [k.replace(f"{repo}#", "#") for k in tk]
    title = f"Поезд {project} {stamp}: " + (", ".join(short) if short else f"{len(own)} коммитов")
    body = [f"Поезд из `{STAGING}` до `{cut_sha[:9]}` — последнего коммита с зелёным quick "
            f"({green['html_url']}); {len(own)} коммитов. Собран `train.py` — отдельных "
            "бот-PR больше нет, всё рутинное едет так (LUNOBOT.md § 7.2).", ""]
    sm = summaries(repo, own)
    for key in tk:
        body.append(f"### {key}")
        entry = sm.get(key, {"problem": [], "fix": []})
        if entry["problem"]:
            body.append("**Проблема:** " + "; ".join(entry["problem"]))
        body.append("**Исправление:** " + ("; ".join(entry["fix"]) or "(нет описания в коммите)"))
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
        # Облачные сессии Claude Code закрывают GraphQL, на котором стоит `gh pr create`;
        # REST-эндпоинт PR там открыт.
        rest = api(f"repos/{repo}/pulls", "-f", f"title={title[:250]}", "-f", f"head={branch}",
                   "-f", "base=main", "-F", f"body=@{f.name}", check=False)
        if isinstance(rest, dict) and rest.get("html_url"):
            created_pr = subprocess.CompletedProcess(created_pr.args, 0, rest["html_url"] + "\n", "")
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


def reverted_later_in_train(commits, i):
    """sha коммита поезда ПОСЛЕ commits[i], который откатывает commits[i] («This reverts commit <sha>.»
    от `git revert`, как в live()), либо None. Поезд «шаг → откат → повторное применение» бисектом не
    судится: префиксы после отката зелёные, и виновным выходит первый коммит шага (unxed/f4#2029, 17-10-2026)."""
    sha = commits[i]["sha"]
    for c in commits[i + 1:]:
        for ref in REVERTS.findall((c.get("commit") or {}).get("message", "")):
            if sha.startswith(ref) or ref.startswith(sha):
                return c["sha"]
    return None


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
# Шаги тестов f4 гоняют `-shuffle=on`: падение зависит от порядка тестов, а seed у каждого прогона
# новый, поэтому `go test ./...` в бисекте его не воспроизводит (16-10-2026: unxed/f4#1995 и
# unxed/f4#1996, семь зелёных прогонов песочницы на ровно том коде, что упал). Для этих шагов
# команда строится из лога упавшего job'а: seed и пакет (см. failed_seeds). vtui без shuffle —
# в логе seed нет, команда остаётся из STEP_CMDS.
SEEDED_STEPS = {
    r"^Run Tests$": "go test -count=1",
    r"^Run race detector$": "go test -race -count=1",
}
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


_LOG_PREFIX = re.compile(r"^(?:[^\t]*\t[^\t]*\t(?=\d{4}-\d\d-\d\dT))?(?:\d{4}-\d\d-\d\dT[\d:.]+Z )?")
_ANSI = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\][^\x07]*\x07)")


def failed_seeds(log, repo):
    """[(путь пакета относительно модуля, seed)] по логу упавшего job'а тестов, либо [], если
    хоть у одного упавшего пакета seed или путь не найден (тогда команда остаётся прежней).
    go test при -shuffle печатает `-test.shuffle <seed>` в вывод пакета, а вывод пакета выходит
    в лог целиком только у упавшего (у зелёного — одна строка `ok`), поэтому seed — последняя
    такая строка после результата предыдущего пакета (`ok`/`?`/`FAIL\t<пакет>`), до `FAIL\t<пакет>`.
    Формат — сырой лог API (`<метка времени>Z <текст>`); префикс `gh run view --log`
    (`<job>\t<шаг>\t<метка времени>Z …`) и управляющие последовательности терминала снимаются."""
    prefix = f"github.com/{repo}"
    out, seed = [], None
    for raw in log.splitlines():
        line = _ANSI.sub("", _LOG_PREFIX.sub("", raw, count=1)).rstrip()
        m = re.match(r"-test\.shuffle (\d+)$", line)
        if m:
            seed = m.group(1)
            continue
        m = re.match(r"(ok|FAIL|\?)\s*\t(\S+)", line)
        if not m:
            continue
        if m.group(1) == "FAIL":
            pkg = m.group(2)
            if seed is None or not (pkg == prefix or pkg.startswith(prefix + "/")):
                return []
            out.append(("." if pkg == prefix else "./" + pkg[len(prefix) + 1:], seed))
        seed = None
    return out


_TEST_SKIP = re.compile(r"-skip '([\w^$|.()-]+)'")
_TEST_TIMEOUT = re.compile(r"-timeout (\d+[smh])\b")


def log_test_flags(log):
    """Флаги `-timeout`/`-skip` из строки `go test … -shuffle=…`, которую шаг печатает в начале
    лога (`run:` скрипт). Seed выбирает перестановку ВСЕХ тестов пакета, а `-skip` лишь не даёт
    части из них выполниться: без него песочница запустила бы тест, который CI сознательно
    исключает (f4: `TestAllDialogs_LayoutValidation` гоняется отдельно с GOMAXPROCS=1, у него
    чужая гонка; `TestSeedSweep` в race), и бисект поймал бы не то падение. Берутся только
    безопасные для shell (в т. ч. при замене пробелов на ${IFS} в старом sandbox.yml) значения.
    Строки нет — пусто."""
    for raw in log.splitlines():
        line = _ANSI.sub("", _LOG_PREFIX.sub("", raw, count=1))
        if "go test" in line and "-shuffle=" in line:
            flags = []
            t = _TEST_TIMEOUT.search(line)
            if t:
                flags.append(f"-timeout {t.group(1)}")
            k = _TEST_SKIP.search(line)
            if k:
                flags.append(f"-skip '{k.group(1)}'")
            return " ".join(flags)
    return ""


def job_log(repo, job_id):
    """Сырой лог job'а (REST, без префиксов `gh run view --log`) либо None. Свежий `gh api`
    отказывается печатать ответ с управляющими последовательностями терминала без
    `--allow-escape-sequences`, старый такого флага не знает — пробуем оба."""
    for flags in (["--allow-escape-sequences"], []):
        p = run("gh", "api", *flags, f"repos/{repo}/actions/jobs/{job_id}/logs", check=False)
        if p.returncode == 0:
            return p.stdout
        if "escape" not in (p.stderr or "") and "unknown flag" not in (p.stderr or ""):
            break
    return None


def bisect_seeds(repo, failed, steps):
    """{имя job'а: [(пакет, seed)]} для упавших шагов из SEEDED_STEPS: лог job'а читается только
    у них. Нет лога, seed или пакета — job в словарь не попадает, бисект идёт прежней командой."""
    out = {}
    for c, (job, step) in zip(failed, steps):
        if not step or not any(re.search(rx, step) for rx in SEEDED_STEPS):
            continue
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/\d+/job/(\d+)",
                      c.get("detailsUrl") or "")
        log = job_log(m.group(1), m.group(2)) if m else None
        pairs = failed_seeds(log, repo) if log else []
        if pairs:
            extra = log_test_flags(log)
            out[job] = [(pkg, seed, extra) if extra else (pkg, seed) for pkg, seed in pairs]
    return out


def seeded_cmd(step, pairs):
    """`go test -count=1 [-timeout …] [-skip …] -shuffle=<seed> <пакет>` по команде на упавший пакет (seed у них разные);
    None, если шаг не из SEEDED_STEPS."""
    base = next((c for rx, c in SEEDED_STEPS.items() if re.search(rx, step or "")), None)
    if not base:
        return None
    # пара — (пакет, seed) либо (пакет, seed, доп. флаги CI-шага из log_test_flags)
    return " && ".join(" ".join([base, *p[2:], f"-shuffle={p[1]}", p[0]]) for p in pairs)


def pick_target_steps(steps, seeds=None):
    """(ОС, команда) для бисекта по упавшим шагам, либо None, если хоть один шаг неизвестен:
    бисект чужой командой даёт ложный «зелёный на всех префиксах» и перезапуски по кругу.
    Команды одной ОС склеиваются через &&; несколько ОС — берётся первая не-linux (остальное
    вскроет следующий поезд после выброса). seeds — {job: [(пакет, seed)]} из bisect_seeds:
    тест, зависящий от порядка, воспроизводится только тем же seed (STEP_CMDS даёт `./...`)."""
    per_os = {}
    for job, step in steps:
        cmd = next((c for rx, c in STEP_CMDS if step and re.search(rx, step)), None)
        if cmd and (seeds or {}).get(job):
            cmd = seeded_cmd(step, seeds[job]) or cmd
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
        command = sandbox_cmd(repo, ref, os_label, cmd)
        dispatched = run("gh", "workflow", "run", "sandbox.yml", "--repo", repo, "--ref", ref,
                         "-f", f"os={os_label}", "-f", f"command={command}", check=False)
        if dispatched.returncode:
            dispatched = run("gh", "api", "-X", "POST",
                             f"repos/{repo}/actions/workflows/sandbox.yml/dispatches",
                             "-f", f"ref={ref}", "-f", f"inputs[os]={os_label}",
                             "-f", f"inputs[command]={command}", check=False)
            if dispatched.returncode:
                error = (dispatched.stderr or dispatched.stdout).strip()
                sys.exit(f"не удалось запустить sandbox.yml для {ref}: "
                         f"{error or 'код ' + str(dispatched.returncode)}")
    print(f"бисект: окно ({good}, {bad}] из {len(commits)} коммитов, {len(refs)} прогонов "
          f"({os_label}, `{cmd}`) — результат разберёт следующий tick")


def bisect_refs(repo, n):
    # Прокси облачной сессии отвечает 400 («path could not be canonicalized») на путь с
    # завершающим «/», поэтому спрашиваем префикс без него и отбираем «bisect/<N>/…» сами
    # (иначе под префикс bisect/17 попали бы и bisect/170/…).
    refs = api(f"repos/{repo}/git/matching-refs/heads/bisect/{n}") or []
    prefix = f"refs/heads/bisect/{n}/"
    return sorted(r["ref"].removeprefix("refs/heads/") for r in refs if r["ref"].startswith(prefix))


def drop_bisect(repo, refs):
    for ref in refs:
        api(f"repos/{repo}/git/refs/heads/{ref}", "-X", "DELETE", check=False)


def cancel_run(repo, run_id):
    """Cancel an Actions run through REST; `gh run cancel` is unreliable in Claude Code cloud."""
    try:
        return api(f"repos/{repo}/actions/runs/{run_id}/cancel", "-X", "POST")
    except SystemExit as error:
        # The run can finish after the caller's in_progress snapshot but before
        # this request reaches Actions. GitHub answers 409 in that race; there is
        # nothing left to cancel, and it must not fail the whole tick.
        message = str(error)
        if "HTTP 409" in message and "run that is completed" in message:
            print(f"прогон #{run_id} уже завершён до отмены — пропускаю")
            return None
        raise


def close_train(repo, pr, comment):
    """Закрыть поезд целиком: комментарий и закрытие PR, удаление ветки поезда и bisect/<N>/*,
    отмена идущих прогонов (поезда и бисекта) — чтобы это не делалось руками и не сжигало раннеры."""
    n = pr["number"]
    branches = [pr["head"]["ref"]] + bisect_refs(repo, n)
    if comment:  # None — PR уже закрыт, только уборка
        closed = run("gh", "pr", "close", str(n), "--repo", repo, "--comment", comment, check=False)
        if closed.returncode:
            api(f"repos/{repo}/issues/{n}/comments", "-f", f"body={comment}", check=False)
            api(f"repos/{repo}/pulls/{n}", "-X", "PATCH", "-f", "state=closed", check=False)
    for br in branches:
        for st in ("in_progress", "queued"):
            runs = api(f"repos/{repo}/actions/runs?branch={br}&status={st}&per_page=100",
                       check=False) or {}
            for r in runs.get("workflow_runs", []):
                cancel_run(repo, r["id"])
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
                target = pick_target_steps(steps, bisect_seeds(repo, failed, steps))
                if not target:
                    return unknown_step(repo, pr, steps)
                bisect(repo, pr, *target, good=i_good, bad=i_bad)
                return 0
            sha = commits[i_bad]["sha"]
            print(f"бисект: первый падающий префикс {i_bad} — виновник {sha[:9]}")
            undone = reverted_later_in_train(commits, i_bad)
            if undone:
                # Откат гасит изменение на промежуточных префиксах, и бисект называет виновным
                # первый коммит шага, хотя падает итог «шаг + откат + повторное применение» (§ 7.2 п. 5).
                close_train(repo, pr,
                            f"Бисект назвал виновным {sha[:9]}, но позже в этом же поезде его откат "
                            f"({undone[:9]}) и, судя по откату, повторное применение: префиксы между ними "
                            "зелёные из-за отката, вердикт ложный. Шаг не выбрасывается (иначе тесты "
                            "повторного применения остаются без кода); поезд закрыт, чинить вперёд.")
                print(f"бисект: {sha[:9]} откачен ниже в этом же поезде ({undone[:9]}) — виновник не "
                      "выбрасывается, поезд закрыт. СРОЧНО (§ 5 п. 2, § 7.2 п. 5): починить вперёд "
                      "(тест вместе с шагом одним коммитом)")
                return 1
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
    target = pick_target_steps(steps, bisect_seeds(repo, failed, steps))
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


def rerun_failed_jobs(repo, run_id):
    """POST rerun-failed-jobs. Два tick-all одного узла (разные номера Луноботов) шли подряд:
    проигравший получал 403 «This workflow is already running» и `tick` падал (14-10-2026,
    поезд unxed/f4#1935: ОШИБКА tick). Перезапуск уже сделан другим — это не сбой."""
    try:
        api(f"repos/{repo}/actions/runs/{run_id}/rerun-failed-jobs", "-X", "POST")
    except SystemExit as e:
        if "already running" not in str(e):
            raise
        print(f"  перезапуск прогона {run_id} уже идёт (другой tick) — пропускаю")


def rerun(failed):
    """Перезапуск упавших и отменённых job'ов их прогонов. REST, а не `gh run rerun`: тот в облачной
    сессии не срабатывал (08-10-2026: tick писал «перезапустил», а run_attempt оставался 1)."""
    seen = set()
    for c in failed:
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", c.get("detailsUrl") or "")
        if m and m.groups() not in seen:
            seen.add(m.groups())
            rerun_failed_jobs(m.group(1), m.group(2))


def covered(repo, sha):
    """Результат quick для коммита в staging: первый завершённый прогон на нём или потомке."""
    runs = api(f"repos/{repo}/actions/workflows/quick.yml/runs?branch={STAGING}&per_page=30")
    for r in sorted(runs["workflow_runs"], key=lambda r: r["created_at"]):
        if r["status"] != "completed" or r["conclusion"] in ("cancelled", "skipped"):
            continue
        cmp = api(f"repos/{repo}/compare/{sha}...{r['head_sha']}", check=False)
        if cmp and cmp.get("status") in ("ahead", "identical"):
            verdict = "зелёный" if r["conclusion"] == "success" else "КРАСНЫЙ"
            print(f"{verdict} для {sha[:9]}: {r['html_url']} (прогон на {r['head_sha'][:9]})")
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
        # `gh run rerun` молча не срабатывал в облачной сессии Claude Code. Проверяем
        # результат REST-запроса до того, как сообщать, что quick перезапущен.
        rerun_failed_jobs(repo, last['id'])
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
        culprit_shas = [c["sha"] for c in culprits]
        # Откатываем и vendorhash-autosync, лежащие после виновника, правившего go.mod/go.sum:
        # иначе go.mod вернётся, а vendorHash в flake.nix останется от откатанных зависимостей.
        since = run("git", "log", "--reverse", "--no-merges", "--format=%H%x1f%B%x1e",
                    f"{culprit_shas[0]}^..HEAD", cwd=d).stdout
        after = []
        for rec in since.split("\x1e"):
            sha, _, body = rec.strip().partition("\x1f")
            if sha:
                after.append({"sha": sha, "commit": {"message": body}, "parents": [{}]})
        gomod = [c["sha"] for c in after
                 if {"go.mod", "go.sum"} & set(run(
                     "git", "show", "--name-only", "--format=", c["sha"], cwd=d).stdout.split())]
        extra = vendorsync_to_revert(after, culprit_shas, gomod)
        for sha in [*extra, *(c["sha"] for c in reversed(culprits))]:
            r = run("git", "revert", "--no-edit", sha, cwd=d, check=False)
            if r.returncode:
                print(f"  откат {sha[:9]} не лёг чисто — СРОЧНО (§ 5 п. 2): «красный "
                      "staging», чинить вперёд, land --fix-staging")
                return 1
            msg = run("git", "log", "-1", "--format=%B", cwd=d).stdout
            run("git", "commit", "-q", "--amend", "-m",
                f"{msg.rstrip()}\n\nStaging-Revert: {first_red['html_url']}", cwd=d)
        if extra:
            print(f"  вместе с ними откатил автокоммиты vendorHash: {len(extra)}")
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
    green_train = green_train_covering(repo, staging)
    if green_train:
        print(f"staging tip уже покрыт зелёным поездом #{green_train['number']} — ждёт merge в main")
        return 0
    train = train_pr(repo)
    hours = None
    if train:
        checks, pending, failed, cancelled = rollup(repo, train["number"])
        if pending and not failed and not cancelled:
            created = datetime.fromisoformat(train["created_at"].replace("Z", "+00:00"))
            train_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            if train["head"]["sha"] == staging:
                if train_hours <= STUCK_HOURS:
                    print(f"поезд #{train['number']} проверяется {train_hours:.1f} ч; "
                          "ожидание полной матрицы пока штатное")
                    return 0
                print(f"поезд #{train['number']} проверяется {train_hours:.1f} ч без ошибок")
                hours = train_hours
            else:
                # land во время полёта поезда уводит вершину staging вперёд головы поезда
                # (18-10-2026, unxed/f4#2085: поезд 14 минут в пути, а старший коммит staging,
                # который как раз едет в нём, старше 2 ч — ложный «ИНЦИДЕНТ ПРОЦЕССА»).
                # Голова поезда — предок вершины: коммиты поезда в подсчёт возраста не входят,
                # «ждут main» только те, что впереди головы; возраст самого поезда — как раньше.
                ahead = compare(repo, train["head"]["sha"], staging)
                if ahead.get("status") in ("ahead", "identical"):
                    if train_hours > STUCK_HOURS:
                        print(f"поезд #{train['number']} проверяется {train_hours:.1f} ч без ошибок")
                        hours = train_hours
                    else:
                        own = exclude_reverted([c for c in ahead["commits"] if len(c["parents"]) == 1])
                        if not own:
                            print(f"поезд #{train['number']} проверяется {train_hours:.1f} ч; "
                                  "ожидание штатное")
                            return 0
                        oldest = min(datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
                                     for c in own)
                        hours = (datetime.now(timezone.utc) - oldest).total_seconds() / 3600
                        print(f"в staging {len(own)} коммит(ов) ждут main впереди поезда "
                              f"#{train['number']} (проверяется {train_hours:.1f} ч); "
                              f"старший — {hours:.1f} ч")
                        if hours > STUCK_HOURS:
                            print(f"ИНЦИДЕНТ ПРОЦЕССА: приземлённая работа ждёт main дольше {STUCK_HOURS} ч. "
                                  "§ 4 «ретро круга»: найти, почему не едет поезд, починить конвейер и "
                                  "зафиксировать правкой LUNOBOT.md/train.py (§ 12)")
                            return 1
                        return 0
    train_in_flight = hours is not None
    own = [c for c in compare(repo, main, staging)["commits"] if len(c["parents"]) == 1]
    own = exclude_reverted(own)
    if not own:
        print("staging не впереди main — приземлённая работа вся в main")
        return 0
    if hours is None:
        oldest = min(datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
                     for c in own)
        hours = (datetime.now(timezone.utc) - oldest).total_seconds() / 3600
    label = "поезд идёт" if train_in_flight else "старший"
    print(f"в staging {len(own)} коммит(ов) ждут main; {label} — {hours:.1f} ч")
    if hours > STUCK_HOURS:
        print(f"ИНЦИДЕНТ ПРОЦЕССА: приземлённая работа ждёт main дольше {STUCK_HOURS} ч. "
              "§ 4 «ретро круга»: найти, почему не едет поезд, починить конвейер и "
              "зафиксировать правкой LUNOBOT.md/train.py (§ 12)")
        return 1
    return 0


def cancelled_main_is_expected(repo, head):
    """Отмена прогона вершины main ожидаема: вершина — merge-коммит, чьё дерево совпадает с
    деревом одного из родителей, а на этом родителе все прогоны полной матрицы завершены
    `success`/`skipped` (хотя бы один `success`). Это ручной мерж зелёного актуального PR по
    § 7.3 («результат мерж-коммита известен, отмени свежесозданный прогон»): тот же код уже
    проверен, повторять ~50 job'ов незачем (18-10-2026, unxed/f4#2083: merge-коммит 37fe96df8,
    прогон 39162354404 отменён по § 7.3, `health` перезапустил его). Возвращает sha зелёного
    родителя или None; любое сомнение (ошибка API, нет родителей, дерево не совпало, нет
    зелёного прогона) — None, то есть прежнее поведение (rerun)."""
    commit = api(f"repos/{repo}/commits/{head}", check=False)
    if not isinstance(commit, dict):
        return None
    parents = [p.get("sha") for p in commit.get("parents") or []]
    tree = ((commit.get("commit") or {}).get("tree") or {}).get("sha")
    if len(parents) != 2 or not tree or not all(parents):
        return None
    for parent in parents:
        pc = api(f"repos/{repo}/commits/{parent}", check=False)
        if not isinstance(pc, dict) or ((pc.get("commit") or {}).get("tree") or {}).get("sha") != tree:
            continue
        data = api(f"repos/{repo}/actions/runs?head_sha={parent}&per_page=100", check=False)
        if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
            continue
        full = [r for r in data["workflow_runs"] if r.get("name") not in ("quick", "sandbox")]
        if (full and all(r.get("status") == "completed" and r.get("conclusion") in ("success", "skipped")
                         for r in full)
                and any(r.get("conclusion") == "success" for r in full)):
            return parent
    return None


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
        if bad and r.get("run_attempt", 1) < 2 and len(bad) <= MAIN_FLAKE_MAX_JOBS:
            # rerun-failed-jobs GitHub принимает только у завершённого прогона: ждём конца,
            # потом ветка ниже перезапустит (до этого красным не объявляем — § 5 п. 2).
            print(f"main {head[:9]}: полная матрица идёт, упал {', '.join(bad)} — после конца "
                  f"прогона перезапущу один раз (флейк?): {r['html_url']}")
            return 0
        if bad and r.get("run_attempt", 1) >= 2:
            # Во время повтора уже упавшие jobs не означают, что весь retry завершился.
            # § 5 п. 2 требует не отвечать кодом 1 до результата повтора.
            print(f"main {head[:9]}: повторная попытка полной матрицы ещё идёт, упал "
                  f"{', '.join(bad)} — результат после конца прогона: {r['html_url']}")
            return 0
        if bad:
            print(f"main {head[:9]}: полная матрица ещё идёт, но уже КРАСНАЯ ({len(bad)}: "
                  f"{', '.join(bad[:6])}{' …' if len(bad) > 6 else ''}) — {r['html_url']}. "
                  "СРОЧНО (§ 5 п. 2): красный main, не ждать конца прогона")
            return 1
        print(f"main {head[:9]}: полная матрица идёт — {r['html_url']} (строка в CI.md, § 7.3)")
        return 0
    if r["conclusion"] == "cancelled":
        # Отменённый прогон на вершине main никто не повторит: новых push нет (09-10-2026: прогон
        # поезда #1841 отменился, tick печатал «cancelled» как норму, красный Race увидели через час).
        green = cancelled_main_is_expected(repo, head)
        if green:
            print(f"main {head[:9]}: прогон отменён, но дерево совпадает с зелёным {green[:9]} — "
                  "повтор не нужен")
            return 0
        if r.get("run_attempt", 1) < 2:
            api(f"repos/{repo}/actions/runs/{r['id']}/rerun", "-X", "POST", check=False)
            print(f"main {head[:9]}: прогон отменён (не упал) — перезапустил: {r['html_url']}")
        else:
            print(f"main {head[:9]}: прогон отменён и после перезапуска — {r['html_url']}; "
                  "разобрать, кто отменяет (§ 5 п. 2)")
        return 0
    if r["conclusion"] in ("success", "skipped"):
        print(f"main {head[:9]}: {r['conclusion']} — {r['html_url']}")
        return 0
    if r.get("run_attempt", 1) < 2:
        # 14-10-2026 main vtui четыре раза за день краснел одним job'ом (macOS/Race) на тесте с
        # коротким сроком, а тот же sha проходил в PR поезда; каждый раз чинили руками. Падение
        # одного-двух job'ов на первой попытке — как у поезда (§ 7.2 п. 5.1) — сначала один
        # перезапуск; настоящая регрессия роняет много job'ов и остаётся красной.
        jobs = api(f"repos/{repo}/actions/runs/{r['id']}/jobs?per_page=100", check=False) or {}
        bad = [j["name"] for j in jobs.get("jobs", []) if j.get("conclusion") == "failure"]
        if 0 < len(bad) <= MAIN_FLAKE_MAX_JOBS:
            rerun_failed_jobs(repo, r['id'])
            print(f"main {head[:9]}: упал {', '.join(bad)} — перезапустил один раз (флейк?): "
                  f"{r['html_url']}. Красным и после этого — СРОЧНО (§ 5 п. 2)")
            return 0
    print(f"main {head[:9]}: КРАСНЫЙ — {r['html_url']}. СРОЧНО (§ 5 п. 2): красный main")
    return 1


def health(repo):
    state, info = staging_health(repo)
    last = info["last"]
    print(f"staging: {state}" + (f" — {last['html_url']}" if last else ""))
    rc = max(stuck(repo), main_ci(repo), 1 if state == "red" else 0)
    transit_warn(repo)
    dispatch_format_warn()
    return rc


# Нарушения записи строк, а не состояния флота (гонка/keepalive/протухание сюда не входят).
DISPATCH_FORMAT_KINDS = ("формат", "время", "слиплось", "маршрут", "нет повода", "мусор")


def dispatch_format_warn(root=None):
    """Предупреждение (код возврата не меняет): полная проверка формата всех
    projects/*/DISPATCH.md учётного клона тем же check_dispatch.check. Гейт перед пушем и
    dispatch-lint.yml смотрят только добавленные строки, поэтому испорченная строка, проскочившая
    один раз, дальше невидима (14-10-2026: 5b329822 превратил захваты dn в строки формата CI.md,
    dispatch-lint упал, следующие пуши зелёные, мусор лежал до ручной уборки aab98732)."""
    import check_dispatch
    base = os.path.join(root or ACCOUNTING, "projects")
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return
    for name in names:
        path = os.path.join(base, name, "DISPATCH.md")
        if not os.path.isfile(path):
            continue
        try:
            _, problems = check_dispatch.check(path, 45)
        except Exception as e:  # noqa: BLE001 — предупреждение не должно ронять health
            print(f"ПРЕДУПРЕЖДЕНИЕ: DISPATCH.md {name}: формат не проверен ({e})")
            continue
        bad = [p for p in problems if p[0] in DISPATCH_FORMAT_KINDS]
        if bad:
            shown = "; ".join(f"строка {n} [{k}]: {msg[:120]}" for k, n, msg in bad[:3])
            more = f"; ещё {len(bad) - 3}" if len(bad) > 3 else ""
            print(f"ПРЕДУПРЕЖДЕНИЕ: DISPATCH.md {name}: формат — {len(bad)} наруш.: {shown}{more}. "
                  f"Проверь: python3 check_dispatch.py projects/{name}/DISPATCH.md")


QUICK_TIP_WAIT_MIN = 10


def ensure_quick_on_tip(repo):
    """Вершина staging без единого прогона quick (push только с .md/docs/** — например, слияние main в
    staging, где весь код уже был, — не запускает workflow): поезд от такого коммита не режется и
    вечно «ждёт quick» (08-10-2026: слияние main в staging висело 2 часа). Через QUICK_TIP_WAIT_MIN минут
    после коммита quick запускается руками: workflow_dispatch на ветке staging (REST, не `gh workflow run` —
    тот просит GraphQL, закрытый в облачных сессиях)."""
    tip = api(f"repos/{repo}/branches/{STAGING}", check=False)
    if not tip:
        return
    # С check=False ответ с ошибкой (лимит API, отказ прокси) приходит телом {"message": ...}, а не
    # веткой; падать на нём нельзя — tick-all ронял весь круг с KeyError: 'commit' (14-10-2026).
    if not isinstance(tip.get("commit"), dict) or "sha" not in tip["commit"]:
        print(f"  вершина {STAGING} не прочитана ({str(tip.get('message', tip))[:120]}) — "
              "проверку quick на вершине пропускаю до следующего tick")
        return
    sha = tip["commit"]["sha"]
    # staging, в котором нет ничего сверх main (вершина — сам main после перемотки), поезду не нужен:
    # код уже проверен полным CI main, и quick на нём ждать незачем (10-10-2026: vtui каждый круг
    # «запускал quick» на такой вершине).
    ahead = api(f"repos/{repo}/compare/main...{sha}", check=False)
    if ahead and ahead.get("ahead_by") == 0:
        return
    # слияние main в staging без правок (дерево равно main: `files` пуст) — тот же случай, что и
    # «вершина = main»: quick на нём не запускается (push без кода), а проверять нечего
    # (14-10-2026: vtui b7bd90f81 «Merge main into lunobot/staging», каждый круг «нет прогона quick»)
    if ahead and "files" in ahead and not ahead["files"]:
        return
    runs = api(f"repos/{repo}/actions/workflows/quick.yml/runs?head_sha={sha}&per_page=5", check=False)
    if runs and runs.get("total_count"):
        return
    when = tip["commit"]["commit"]["committer"]["date"]
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(when.replace("Z", "+00:00"))).total_seconds() / 60
    if age < QUICK_TIP_WAIT_MIN:
        return
    # Ответ проверяется: quick.yml без триггера workflow_dispatch отвечает 422, и «запустил» было бы
    # неправдой (10-10-2026, vtui).
    p = run("gh", "api", "-X", "POST", f"repos/{repo}/actions/workflows/quick.yml/dispatches",
            "-f", f"ref={STAGING}", check=False)
    if p.returncode:
        err = (p.stderr or p.stdout or "").strip().splitlines()
        print(f"на вершине staging {sha[:9]} нет прогона quick уже {int(age)} мин, запустить вручную НЕ вышло: "
              f"{err[-1] if err else 'код ' + str(p.returncode)} — добавь workflow_dispatch в quick.yml проекта "
              f"или запусти quick пушем в staging")
        return
    print(f"на вершине staging {sha[:9]} нет прогона quick уже {int(age)} мин — запустил quick вручную (workflow_dispatch)")


def tick(repo, sign):
    ensure_quick_on_tip(repo)
    rc = max(main_ci(repo), heal(repo))
    rc = max(rc, train_step(repo, sign))
    # После шага поезда, а не до: поезд, который этот же tick влил, больше не «ждёт
    # main». До 11-10-2026 stuck() мерил staging против main до вливания и объявлял
    # инцидент, который тот же tick тут же снимал (f4 #1872: «2.2 ч» при уже зелёном
    # поезде — а настоящий хвост после вливания был ~1 ч).
    rc = max(rc, stuck(repo))
    transit_warn(repo)
    return rc


def own_numbers(repo, commits):
    """Номера тикетов самого repo из `Touch:` коммитов (Touch: #N и Touch: <repo>#N)."""
    return {int(k.split("#")[1]) for k in tickets(repo, commits) if k.startswith(f"{repo}#")}


def triage_path(repo):
    return os.path.join(ACCOUNTING, "projects", repo.split("/")[1], "TRIAGE.md")


def staging_pending_numbers(repo, head):
    """Номера тикетов самого repo, чьи `Touch:`-коммиты ещё лежат в lunobot/staging впереди
    только что влитой головы main (`head`): часть тикета не доехала. Вернёт set() и молча, если
    в repo нет ветки lunobot/staging; None — список staging получить не удалось (ошибка API:
    вызывающий предупреждает и ведёт себя как раньше, а не падает: api(check=False), не compare())."""
    cmp = api(f"repos/{repo}/compare/{head}...{STAGING}", check=False)
    if isinstance(cmp, dict) and isinstance(cmp.get("commits"), list):
        return own_numbers(repo, cmp["commits"])
    br = api(f"repos/{repo}/branches/{STAGING}", check=False)
    if isinstance(br, dict) and not br.get("commit") and br.get("message") in ("Not Found", "Branch not found"):
        return set()
    return None


def mark_checking(repo, nums, sign, head=None):
    """После вливания поезда: `в пути` → `проверяют` в TRIAGE.md учётного клона (§ 5.1).
    Раньше tick это только печатал, и без ручной правки тикеты висели `в пути` вечно
    (28-09-2026: f4 #659, #1604, #1606). Нет клона/файла, не main, любые незакоммиченные правки в клоне, нет id в
    --sign — только сообщение: правь руками. В коммит идёт только TRIAGE.md (по имени). Комментарии и updatedAt не трогаются.
    Тикет, у которого в lunobot/staging впереди влитой головы `head` остался коммит с `Touch:` на
    него (многочастный тикет: часть 3 влита, часть 4 ещё едет — 16-10-2026 f4#1998), остаётся
    `в пути`; tick печатает такие номера. Не удалось получить staging (ошибка API) — предупреждение
    и прежнее поведение (все `nums` → `проверяют`). `head` не передан — staging не смотрим."""
    path = triage_path(repo)
    if not nums:
        return
    if head:
        pending = staging_pending_numbers(repo, head)
        if pending is None:
            print(f"ПРЕДУПРЕЖДЕНИЕ: список {STAGING} получить не удалось (ошибка API) — "
                  "тикеты, часть которых ещё в staging, не отличаю: `в пути` → `проверяют` как обычно; "
                  "такой тикет верни `в пути` руками")
        else:
            held = sorted(set(nums) & pending)
            if held:
                print("TRIAGE: остаются `в пути` (часть ещё в staging): "
                      + ", ".join(f"#{n}" for n in held))
                nums = set(nums) - set(held)
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
            with open(path, encoding="utf-8") as f:
                text = f.read()
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


def tried_since(repo, n, commits):
    """Тикет из нескольких частей законно остаётся `в пути` и после «Пробуйте!»: в staging едет
    следующая часть. Предупреждать незачем, если «Пробуйте!» в тикете новее последнего его
    коммита в main (10-10-2026: f4#1842 ложно предупреждался каждый круг)."""
    dates = [c["commit"]["committer"]["date"] for c in commits
             if n in own_numbers(repo, [c]) and c.get("commit", {}).get("committer", {}).get("date")]
    if not dates:
        return False
    comments = api_list(f"repos/{repo}/issues/{n}/comments?since={max(dates)}&per_page=100")
    return any("пробуйте!" in (c.get("body") or "").casefold() and (c.get("created_at") or "") >= max(dates)
               for c in comments)


def transit_warn(repo):
    """Предупреждение (не ошибка): тикет `в пути` в TRIAGE.md, а его `Touch:` уже в main за
    последние TRANSIT_WINDOW_H ч — «Пробуйте!» не разнесён, состояние не сдвинулось.
    Коммиты без Touch: (эпоха PR) этим не видны — их состояние ведёт автор вручную."""
    try:
        with open(triage_path(repo), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return
    transit = {int(m.group(2)) for m in IN_TRANSIT.finditer(text)}
    if not transit:
        return
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - TRANSIT_WINDOW_H * 3600))
    commits = api_list(f"repos/{repo}/commits?sha=main&since={since}&per_page=100")
    stale = sorted(n for n in transit & own_numbers(repo, commits) if not tried_since(repo, n, commits))
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
    # A queued matrix can coexist with cancelled jobs. Restart cancellations first;
    # otherwise the pending branch hides them until the matrix drains, which can
    # leave staging parked for hours behind an already lost job.
    if cancelled:
        rerun(cancelled)
        if pending:
            print(f"поезд #{n}: {len(cancelled)} проверок отменены — перезапустил; "
                  f"ещё {len(pending)} проверок идут")
        else:
            print(f"поезд #{n}: {len(cancelled)} проверок отменены (не упали) — перезапустил")
        return 0
    if pending:
        print(f"поезд #{n} в пути: {len(pending)} из {len(checks)} проверок ещё идут")
        return 0
    ff = run("gh", "api", "-X", "PATCH", f"repos/{repo}/git/refs/heads/main",
             "-f", f"sha={head}", "-F", "force=false", check=False)
    if ff.returncode and push_ref(repo, "main", head):
        # Прокси облачной сессии закрывает запись git/refs; обычный (не force) git push
        # точно так же продвигает main только вперёд.
        ff = subprocess.CompletedProcess(ff.args, 0, "", "")
    if ff.returncode == 0:
        how = "fast-forward"
        if should_cancel_main_run(repo):
            time.sleep(5)
            for r in main_push_runs_in_progress(repo, head):
                cancel_run(repo, r["id"])
        api(f"repos/{repo}/git/refs/heads/{pr['head']['ref']}", "-X", "DELETE", check=False)
    else:
        merged = run("gh", "pr", "merge", str(n), "--repo", repo, "--merge", "--delete-branch", check=False)
        if merged.returncode:
            # `gh pr merge` стоит на GraphQL; REST-эндпоинт мержа открыт и там, где он закрыт.
            rest = api(f"repos/{repo}/pulls/{n}/merge", "-X", "PUT", "-f", "merge_method=merge",
                       check=False)
            if not (isinstance(rest, dict) and rest.get("merged")):
                sys.exit(f"gh pr merge {n}: {merged.stderr.strip() or merged.stdout.strip()}")
            api(f"repos/{repo}/git/refs/heads/{pr['head']['ref']}", "-X", "DELETE", check=False)
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
        if not texts and "#" in key:
            print("(текста «Проверить:» нет — напиши «Пробуйте!» сам по «Проблема:»/"
                  "«Исправление:» коммитов, понятно автору тикета)")
    note = nightly_try_note(repo)
    if note:
        print(note)
    mark_checking(repo, own_numbers(repo, commits), sign, head)
    return 0


# Проекты с плавающим nightly-релизом, который публикует ТОЛЬКО прогон main (job Nightly в
# build.yml на push в main): отмена этого прогона после fast-forward поезда оставляет nightly
# без обновления, пока поезда идут fast-forward. Поэтому пока nightly старше NIGHTLY_MAX_AGE_H,
# прогон main не отменяют. Оговорки: (1) если main красный, job Nightly не выполняется (он за
# needs сборки и тестов) и nightly остаётся старым, значит, отмена отключена, и каждый
# fast-forward оставляет свой прогон main, пока main не починят; (2) workflow-level
# concurrency f4 всё равно отменяет прогон main следующим push'ем, так что обновление nightly
# не гарантировано, а лишь становится возможным.
NIGHTLY_MAX_AGE_H = 3
NIGHTLY_REPOS = {"unxed/f4"}


def nightly_try_note(repo):
    """Напоминание тому, кто разносит «Пробуйте!»: у проекта с плавающим nightly пользователь берёт
    сборку только из релиза nightly, а его публикует прогон main, то есть через 30–60 минут после
    влития поезда. «Пробуйте!» без ссылки на nightly и без оговорки о задержке отправляет автора
    проверять прежнюю сборку (unxed/f4#1758, 17-10-2026: «Пробуйте!» в 19:24, через две минуты
    автор спросил «Where is new Build?»). Пустая строка — у проекта нет плавающего nightly."""
    if repo not in NIGHTLY_REPOS:
        return ""
    return (f"ВНИМАНИЕ: {repo} отдаёт сборки только через релиз nightly "
            f"(https://github.com/{repo}/releases/tag/nightly), его публикует прогон main и это занимает "
            "до часа после влития. В каждый «Пробуйте!» добавь строку (на языке тикета): сборка с "
            "исправлением появится на странице nightly, когда закончится полная сборка main (ссылка на "
            "прогон — в CI.md); сверяйте время публикации релиза со временем этого комментария.")


def nightly_is_stale(repo):
    """True, если у проекта есть плавающий nightly и его нельзя считать свежим: релиз старше
    NIGHTLY_MAX_AGE_H, отсутствует или ответ API не разобрать. Ошибка gh не роняет tick:
    api(check=False) не вызывает sys.exit, а на всякий случай ловится и SystemExit (tick уже
    влил поезд и не должен упасть до удаления ветки, tag_next и печати «Пробуйте!»).
    True значит «не отменять прогон main» (цена только лишний прогон)."""
    if repo not in NIGHTLY_REPOS:
        return False
    try:
        rel = api(f"repos/{repo}/releases/tags/nightly", check=False)
        published = datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))
        if published.tzinfo is None:  # без пояса — UTC, иначе вычитание ниже падает TypeError
            published = published.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - published > timedelta(hours=NIGHTLY_MAX_AGE_H)
    except (Exception, SystemExit):  # noqa: BLE001 -- нет релиза, 404, 5xx, лимит: не отменять
        return True


def main_push_runs_in_progress(repo, head):
    """Незавершённые прогоны main на push для коммита head. Сбой gh не роняет tick: поезд уже
    влит, и ему ещё удалять ветку, ставить тег и печатать «Пробуйте!» — пустой список значит
    «ничего не отменять»."""
    try:
        resp = api(f"repos/{repo}/actions/runs?branch=main&head_sha={head}", check=False)
        runs = resp["workflow_runs"]
        return [r for r in runs if r["event"] == "push" and r["status"] != "completed"]
    except (Exception, SystemExit):  # noqa: BLE001
        return []


def should_cancel_main_run(repo):
    """Отменять ли прогон main после fast-forward поезда: не для PRESERVE_MAIN и не пока у
    проекта устарел плавающий nightly."""
    return repo not in PRESERVE_MAIN and not nightly_is_stale(repo)


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
    if r.returncode and push_tag(repo, tag, head):
        # Прокси облачной сессии закрывает запись git/refs, как и для веток (push_ref);
        # обычный git push тега проходит (10-10-2026: vtui v0.1.399 не ставился).
        r = subprocess.CompletedProcess(r.args, 0, "", "")
    print(f"{repo}: тег {tag} на {head[:9]}" if r.returncode == 0 else
          f"{repo}: тег {tag} не создан: {r.stderr.strip()}")


def push_tag(repo, tag, sha):
    """Поставить тег git push-ем, когда REST закрыт для записи ссылок. True — тег стоит."""
    url = f"https://github.com/{repo}"
    if run("git", "fetch", "-q", "--depth=1", url, sha, check=False).returncode:
        return False
    return run("git", "push", "-q", url, f"{sha}:refs/tags/{tag}", check=False).returncode == 0


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
    with open(os.path.join(root, "INDEX.md"), encoding="utf-8") as f:
        index = f.read()
    for name in re.findall(r"^\d+\.\s*\[([^\]]+)\]", index, re.M):
        try:
            with open(os.path.join(root, name, "PROJECT.md"), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        m = re.search(r"^- Код: https://github\.com/([^/\s]+/[^/\s]+)", text, re.M)
        if m and "commit" in (api(f"repos/{m.group(1)}/branches/{STAGING}", check=False) or {}):
            out.append(m.group(1))
    return out


COMPLAINT_STALE_H = 3


def complaints_warn(repo=None, now=None):
    """Предупреждение (код возврата не меняет): открытые PR `complaint/*` учётного репозитория старше
    COMPLAINT_STALE_H часов. Лунобот-2 жалобы не вливает (§ 12), и без напоминания они копятся
    (14-10-2026: 13 открытых PR жалоб за сутки, разобраны одним кругом Лунобота-1)."""
    if repo is None:
        url = run("git", "-C", ACCOUNTING, "remote", "get-url", "origin", check=False).stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
        repo = m.group(1) if m else None
    if not repo:
        return
    now = now or datetime.now(timezone.utc)
    old = []
    try:
        prs = api(f"repos/{repo}/pulls?state=open&per_page=100", check=False)
        for pr in prs if isinstance(prs, list) else []:
            if not pr.get("head", {}).get("ref", "").startswith("complaint/"):
                continue
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            if (now - created).total_seconds() >= COMPLAINT_STALE_H * 3600:
                old.append(pr["number"])
    except (ValueError, KeyError, TypeError, AttributeError):
        return  # предупреждение не должно ронять tick-all: битый ответ API — тишина
    if old:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {len(old)} PR жалоб {repo} открыты дольше {COMPLAINT_STALE_H} ч "
              f"({', '.join('#' + str(n) for n in sorted(old))}) — Лунобот-1: review отдельным субагентом "
              f"и вливание по § 12; Лунобот-2 их не вливает")


def tick_all(sign):
    """tick по всем проектам со staging. Сбой одного (сеть, API: tick падает через sys.exit)
    не прерывает остальные — иначе 14-10-2026 TLS-таймаут в f4 оставил vtui без tick."""
    rc = 0
    for repo in staged_repos():
        print(f"=== {repo}")
        try:
            rc = max(rc, tick(repo, sign))
        except SystemExit as e:
            print(f"ОШИБКА tick {repo}: {e.code}")
            rc = max(rc, 1)
    dispatch_format_warn()
    complaints_warn()
    return rc


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd in ("-h", "--help", "help") or "-h" in rest or "--help" in rest:
        print(__doc__)
        return 0
    opt = lambda k: rest[rest.index(k) + 1] if k in rest else None
    if cmd == "land":
        unknown = [a for a in rest if a != "--fix-staging"]
        if unknown:
            print(f"land: неизвестные аргументы {unknown} — ничего не сделано; допустим только --fix-staging")
            return 2
        return land(fix="--fix-staging" in rest)
    if cmd == "tick-all" and opt("--sign"):
        return tick_all(opt("--sign"))
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
    # Вывод в файл/канал (фоновый запуск, § 13.2) без построчной буферизации приходит
    # только в конце проекта, и идущий tick-all выглядит зависшим.
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main(sys.argv[1:]))
