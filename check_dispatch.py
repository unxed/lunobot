#!/usr/bin/env python3
"""Линтер DISPATCH.md.

Файл протокола содержит только действующие захваты (§ 8 инструкции). Проверяется
формат строк, отсутствие записей о законченной работе, повторные захваты одного шага,
keepalive без захвата и протухшие захваты.

Каждая строка захвата («взял», не «работаю») обязана нести ровно одну метку маршрута —
`[land]`, `[pr]` или `[urgent: <причина>]` — решение из § 4 инструкции о маршруте шага,
зафиксированное машиночитаемо, а не только текстом абзаца. Строка без метки или с меткой
неверного формата проваливает гейт (см. `route_error`, kind «маршрут»). Это ответ на два
повторных лапса координирующей модели с забытым маршрутом (§ 7.2, инцидент bot-pr-queue и
повторный случай с покрытием тестами, тогда ещё при старом механизме пачек — `[batch:
lunobot/batch/<проект>/<N>]`, замененном на `[land]` 27-09-2026) — текстовое напоминание
в инструкции читается один раз и забывается, а этот гейт запускается перед каждым пушем.

Использование:
    python3 check_dispatch.py projects/f4/DISPATCH.md [--timeout-min 45] [--since ДД-ММ-ГГГГ]
    python3 check_dispatch.py projects/f4/DISPATCH.md --added-only [--base <коммит>]

`--added-only` оставляет только претензии к строкам, добавленным последним коммитом.
Добавленная строка, которая не захват, не keepalive, не запись о завершении или заморозке
и не шапка, тоже даёт претензию «формат» (`stray_lines`); полный режим её не ищет.
Так проверка отвечает на вопрос «правильно ли записал именно ты», а не «какое сейчас
состояние флота»: состояние почти всегда ненулевое, и гейт из него горел бы всегда.

Коды возврата: 0 — нарушений нет, 1 — есть.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

TS = r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})"
ID = r"Я Лунобот-(?P<num>\d+) \((?:instance|node) (?P<node>[0-9a-f]{6,24}); (?P<plt>[A-Z]{3})(?:; воркер [0-9a-f]{6,})?\)"
LIVE = ("взял", "работаю")
CLOSED = ("закончил", "освобождаю", "разблокировано по таймауту")
FINAL = ("считаю цель", "прекращаю работу", "объявляю заморозку")

# Метка маршрута (§ 4, § 8): обязательна в конце каждой строки ЗАХВАТА («взял»), не нужна
# для keepalive («работаю»). Ровно один из трёх видов, ничего четвёртого.
ROUTE_MARKER = re.compile(r"\[(land|pr|urgent)(?::\s*(.+?))?\]\s*$")
BARE_URGENT = {"срочно", "срочная", "срочная работа", "срочно!", "urgent"}


def is_record_line(line):
    """Строка записи учёта начинается с метки времени ДД-ММ-ГГГГ ЧЧ:ММ:СС и пробела.

    Общий предикат: им же `acct_line.py add` отказывает строке без метки (DISPATCH.md, CI.md,
    BRANCHES.md), а гейт `--added-only` ищет вписанный мимо него текст.
    """
    return bool(re.match(TS + r"\s", line))


def route_error(line):
    """Проверяет метку маршрута в конце строки захвата. Возвращает текст ошибки или None.

    `[land]` — рутинная работа уходит в `lunobot/staging` через `train.py land` (§ 7.2), без
    своей ветки и своего PR — метке не нужен аргумент, весь маршрут один и тот же для любой
    рутинной работы.

    `[pr]` — рутинная работа проекта с режимом публикации PR: отдельная ветка, PR и
    обязательные CI-гейты; аргумент не нужен.

    `[urgent: <причина>]` — причина обязана называть конкретный пункт правила (содержит
    «§») или быть прямой цитатой команды владельца (в «ёлочках»); голое «срочно» без
    основания не проходит — это и есть тот самый лапс, который метка должна сделать
    структурно невозможным.
    """
    m = ROUTE_MARKER.search(line)
    if not m:
        return ("строка захвата без метки маршрута — нужна ровно одна в конце строки: "
                "[land] (рутинная работа — уходит в lunobot/staging, § 7.2) или "
                "[pr] (рутинная работа проекта с режимом PR) или "
                "[urgent: <причина>] (причина — пункт правила «§ …» или прямая цитата "
                "команды владельца); см. § 8")
    kind, content = m.group(1), (m.group(2) or "").strip()
    if kind in ("land", "pr"):
        if content:
            return (f"метка [{kind}: {content}] не по формату — [{kind}] не принимает "
                     "аргумент")
    else:  # urgent
        if not content:
            return ("метка [urgent] без причины — нужен конкретный пункт правила "
                     "(например «по § 5 п. 2») или прямая цитата команды владельца")
        if content.lower().strip("!.") in BARE_URGENT:
            return (f"метка [urgent: {content}] — голое «срочно» без основания; нужен "
                     "конкретный пункт правила (например «по § 5 п. 2») или прямая цитата "
                     "команды владельца")
        if "§" not in content and "«" not in content:
            return (f"метка [urgent: {content}] не называет ни пункт правила (§ …), ни "
                     "прямую цитату владельца («…»)")
    return None


REF_URL = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull)/(\d+)")
REF_SHORT = re.compile(r"(?<![\w./-])([\w.-]+)/([\w.-]+)#(\d+)")
# «часть 3 из 4», а также «(часть 5в, …)» и «(часть 5, …)» без «из M»: ключ делится по части, поэтому и
# часть с буквой (§ 5.1: 5а/5б/5в) обязана распознаваться (17-10-2026 «часть 5в» и «часть 5» одного тикета
# дали ложную «гонку»: обе не разобрались и получили ключ «1/1»). Форма без «из M» признаётся только
# в скобках «(часть N» — иначе зацепится посторонний текст («часть 2 PR»). «Шаг» — синоним «части»
# (17-10-2026 захват unxed/bp#27 «(шаг 2 из 3: …)» не распознал часть, хотя «часть 2 из 3» уже была в
# CI.md: гейт принял вторую работу над готовым PR, воркер запущен зря).
PART_ANY = re.compile(r"(?:\((?:часть|шаг) (\d+[а-яa-z]?)(?: из (\d+))?|(?:часть|шаг) (\d+) из (\d+))(?![\w])")


def part_id(line):
    """Номер части (с буквой) для сравнения частей: «3 из 4» и «3» — одна часть; нет части — None."""
    m = PART_ANY.search(line)
    return (m.group(1) or m.group(3)) if m else None


# Инцидент без тикета: «красный поезд #1968», «красный main d5f1ef202» (§ 5 п. 2) — у него нет ссылки
# на тикет, а чинить его одновременно двум сеансам незачем.
INCIDENT = re.compile(r"красн\w*\s+(?:поезд\s*#(\d+)|main\s+([0-9a-f]{7,40})\b)", re.I)
# Инцидент конвейера проекта без sha: «красный staging f4», «красный quick на lunobot/staging», «застой main»
# (§ 5 п. 2). Файл DISPATCH.md — один проект, поэтому ключ без имени проекта. Раннеры Лунобота-1 и
# Лунобота-2 начинают круг почти одновременно и оба видят тот же красный staging; текст задачи у них
# разный, и без нормализации гейт пропускал вторую починку одной причины.
PIPELINE = re.compile(r"(красн\w*\s+(?:quick\s+(?:на\s+)?)?(?:lunobot/)?staging)|(застой\w*\s+main)", re.I)


def refs(text):
    """Ссылки на тикеты/PR в строке: URL github.com/<o>/<r>/(issues|pull)/N и <o>/<r>#N.

    Нормализуются в «o/r#N» (регистр не важен): кастомная задача «влить PR … unxed/dn#33» и
    захват https://github.com/unxed/dn/issues/33 — одна и та же работа (14-10-2026, два
    захвата unxed/dn#33 часть 3 из 4 разными сеансами одного узла: ключи разной формы,
    гейт их не сравнивал). Инцидент без тикета («красный поезд #N», «красный main <sha>»)
    нормализуется в «поезд#N» / «main@<sha7>»: 15-10-2026 красный поезд #1968 взяли два
    сеанса одного узла с разным текстом задачи, за минуту, и оба чинили одно и то же."""
    found = {f"{o}/{r}#{n}".lower() for o, r, n in REF_URL.findall(text)}
    found |= {f"{o}/{r}#{n}".lower() for o, r, n in REF_SHORT.findall(text)}
    for train, sha in INCIDENT.findall(text):
        found.add(f"поезд#{train}" if train else f"main@{sha[:7].lower()}")
    for staging, stall in PIPELINE.findall(text):
        found.add("staging" if staging else "застой-main")
    return found


def ci_refs(path):
    """Строки CI.md того же проекта (рядом с DISPATCH.md): [(ссылки, часть или None)].

    Часть нужна, чтобы следующая часть многочастного тикета (§ 5.1) не считалась повтором
    строки CI.md по предыдущей части."""
    ci = os.path.join(os.path.dirname(os.path.abspath(path)), "CI.md")
    try:
        with open(ci, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        if r := refs(line):
            out.append((r, part_id(line)))
    return out


def looks_like_record(line):
    """Строка без id Лунобота, но с признаками записи захвата (а не шапки файла)."""
    return bool(re.match(r"\d{2}-\d{2}-\d{4}\b", line)
                or re.search(r"\b(?:взял|работаю)\b", line)
                or re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", line)
                or ROUTE_MARKER.search(line))


def parse(path):
    entries, malformed, no_origin, route = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if any(f in line for f in FINAL):
                continue  # записи о завершении сессии — законное исключение
            if "Лунобот" not in line:
                # шапка файла («Файл содержит только действующие захваты…») — законный текст;
                # строка без id, похожая на запись (глагол состояния, ссылка, метка маршрута,
                # дата в начале), — испорченный захват, который иначе молча пропускался бы
                if looks_like_record(line):
                    malformed.append((n, line[:110], {"нет id Лунобота": True}))
                continue
            ts, who = re.match(TS, line), re.search(ID, line)
            verb = next((v for v in LIVE + CLOSED if v in line), None)
            body = re.sub(r"\]\(https?://[^)]+\)", "]", line)
            key = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", body)
            if key:
                key = key.group(0)
            else:
                # «взял кастомную задачу «X»» и «работаю над кастомной задачей «X»» — один шаг
                custom = re.search(r"кастомн\w+ задач\w+\s*«([^»]+)»", body)
                if not custom:
                    custom = re.search(r"кастомную задачу,\s*([^(]+)", body)
                key = custom.group(1).strip() if custom else None
                if key and "взял" in line and "по §" not in body:
                    no_origin.append((n, line[:110]))
            part = PART_ANY.search(line)
            if not (ts and who and verb and key):
                malformed.append((n, line[:110], {
                    "нет метки времени": not ts,
                    "id не по формату (нужно «Я Лунобот-N (node <hex>; ПЛАТФОРМА)», без имени модели)": not who,
                    "нет глагола состояния": not verb,
                    "нет ключа задачи": not key,
                }))
                continue
            # часть не указана — значит единственная
            if part:
                num, total = (part.group(1), part.group(2)) if part.group(1) else (part.group(3), part.group(4))
                part_key = f"{num}/{total}" if total else num
            else:
                part_key = "1/1"
            entries.append({"line": n, "ts": datetime.strptime(ts.group(1), "%d-%m-%Y %H:%M:%S"),
                            "who": who.group(0), "node": who.group("node"), "num": who.group("num"),
                            "verb": verb, "refs": refs(line), "text": line,
                            "part": part_id(line),
                            "route": (ROUTE_MARKER.search(line) or [None, None])[1],
                            "key": f"{key}#{part_key}",
                            "worker": (re.search(r"воркер\s+([0-9a-f]{6,})", line) or [None, None])[1]})
            if verb == "взял":
                if err := route_error(line):
                    route.append((n, line[:160], err))
    return entries, malformed, no_origin, route


def owner_differs(a, b):
    """Разные владельцы захвата: другой узел, другой номер на том же узле или другой воркер."""
    if (a["node"], a["num"]) != (b["node"], b["num"]):
        return True
    return bool(a["worker"] and b["worker"] and a["worker"] != b["worker"])


def check(path, timeout_min, since=None):
    entries, malformed, no_origin, route = parse(path)
    if since:
        entries = [e for e in entries if e["ts"] >= since]
        def fresh(text):
            m = re.match(r"(\d{2}-\d{2}-\d{4})", text)
            return not (m and datetime.strptime(m.group(1), "%d-%m-%Y") < since)
        malformed = [x for x in malformed if fresh(x[1])]
        no_origin = [x for x in no_origin if fresh(x[1])]
        route = [x for x in route if fresh(x[1])]

    problems = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for e in entries:
        if e["ts"] > now:
            problems.append(("время", e["line"],
                             f"метка времени захвата из будущего (UTC): {e['ts']:%d-%m-%Y %H:%M:%S}"))
    for n, text, msg in route:
        problems.append(("маршрут", n, msg + f": {text}"))
    for n, text in no_origin:
        problems.append(("нет повода", n,
                         "кастомная задача без указания, откуда взялась "
                         f"(нужно «по § …»): {text}"))
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if len(re.findall(TS, line)) > 1:
                if since:
                    m = re.match(r"(\d{2}-\d{2}-\d{4})", line)
                    if m and datetime.strptime(m.group(1), "%d-%m-%Y") < since:
                        continue
                problems.append(("слиплось", n,
                                 "в одной строке несколько записей — между ними нужна пустая строка"))
    for n, text, flags in malformed:
        problems.append(("формат", n, ", ".join(k for k, v in flags.items() if v) + f": {text}"))

    holders, live, in_ci = {}, [], ci_refs(path)
    for e in sorted(entries, key=lambda x: (x["ts"], x["line"])):
        if e["verb"] in CLOSED:
            problems.append(("мусор", e["line"],
                             f"«{e['verb']}» — записей о законченном в файле быть не должно, "
                             f"строки по закрытому шагу удаляются: {e['key']}"))
            continue
        prev = holders.get(e["key"])
        # владелец захвата — узел, а не номер: при смене номера (= смены модели, § 4) менеджер
        # переписывает захваты узла под новый id, и это не чужой захват и не гонка
        if e["verb"] == "взял" and prev and prev["node"] != e["node"]:
            problems.append(("гонка", e["line"],
                             f"{e['key']} уже захвачен другим (строка {prev['line']})"))
        # воркеры одного узла делят id инстанса; различает их суффикс «воркер <agentId>» после id
        if (e["verb"] == "взял" and prev and prev["node"] == e["node"] and e["worker"]
                and prev["worker"] and e["worker"] != prev["worker"]):
            problems.append(("дубль", e["line"],
                             f"{e['key']} уже взят другим воркером узла (строка {prev['line']})"))
        # Лунобот-1 и Лунобот-2 одного узла — две разные сессии с одним id узла и без суффикса «воркер»:
        # то же «взял» на тот же ключ от другого номера на том же узле — дубль работы (14-10-2026
        # unxed/dn#40 часть 4а взяли оба, оба написали юнит; гейт молчал)
        # prev — текущий держатель ключа, в том числе его «работаю»: между двумя «взял» чужой
        # keepalive перезаписывает держателя, и сверка только с «взял» пропускала бы дубль
        if (e["verb"] == "взял" and prev and prev["node"] == e["node"]
                and prev["num"] != e["num"] and not (e["worker"] and prev["worker"])):
            problems.append(("дубль", e["line"],
                             f"{e['key']} уже взят Луноботом-{prev['num']} этого узла (строка {prev['line']})"))
        if e["verb"] == "работаю" and not prev:
            problems.append(("состояние", e["line"], f"keepalive без захвата: {e['key']}"))
        if e["verb"] == "взял" and e["refs"]:
            # пересечение по ссылкам: тот же тикет/PR под ключом другой формы (URL против
            # кастомного текста) у другого владельца; разные явные части — не пересечение
            for other in live:
                if other["key"] == e["key"] or not (other["refs"] & e["refs"]):
                    continue
                if not owner_differs(other, e):
                    continue
                if other["part"] and e["part"] and other["part"] != e["part"]:
                    continue
                problems.append(("пересечение", e["line"],
                                 f"{', '.join(sorted(other['refs'] & e['refs']))} уже в работе "
                                 f"у другого владельца (строка {other['line']})"))
                break
        dup_ci = set()
        if e["verb"] == "взял" and e["route"] in ("land", "pr"):
            for r, part in in_ci:
                if (r & e["refs"]) and not (part and e["part"] and part != e["part"]):
                    dup_ci |= r & e["refs"]
        if dup_ci:
            problems.append(("уже в CI.md", e["line"],
                             f"{', '.join(sorted(dup_ci))} уже есть в CI.md проекта "
                             "(§ 5 п. 5: брать можно только то, чего нет ни в DISPATCH.md, ни в "
                             "CI.md); доводка строки CI.md — [urgent: по § 5 п. 3 …]"))
        if e["verb"] in LIVE:
            live.append(e)
        if not prev or e["ts"] >= prev["ts"]:
            holders[e["key"]] = e

    if entries:
        now = max(e["ts"] for e in entries)
        for key, h in holders.items():
            age = now - h["ts"]
            if age > timedelta(minutes=timeout_min):
                problems.append(("протух", h["line"],
                                 f"{key} держится {int(age.total_seconds() // 60)} мин без отметки"))
    return entries, problems


def added_lines(path, base=None):
    """Номера строк, добавленных последним коммитом."""
    import subprocess
    base = base or "HEAD~1"
    try:
        diff = subprocess.run(["git", "diff", "--unified=0", base, "HEAD", "--", path],
                              capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    lines, cur = set(), 0
    for l in diff.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", l)
        if m:
            cur = int(m.group(1))
            continue
        if l.startswith("+") and not l.startswith("+++"):
            lines.add(cur)
            cur += 1
        elif not l.startswith("-"):
            cur += 1
    return lines


# Стандартное описание под заголовком шапки: законный текст, не запись.
HEADER_TEXT = ("Файл содержит только действующие захваты", "Закончил шаг — удали свои строки")


def stray_lines(path):
    """Строки, которые не захват, не keepalive, не запись о завершении/заморозке и не шапка.

    Только для режима --added-only: полный разбор файла шапку и такой текст не трогает.
    Строка с «Лунобот» разбирается в parse() и даёт претензию там; строка без него и без
    признаков записи (looks_like_record) в parse() молча пропускается. Так
    «красный main 72bdcb32», дописанный руками мимо acct_line.py, провисел два часа.
    Возвращает {номер строки: текст}.
    """
    out = {}
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            text = raw.rstrip()
            if not text.strip() or text.lstrip().startswith("#"):
                continue
            if any(x in text for x in FINAL) or text.startswith(HEADER_TEXT):
                continue
            if "Лунобот" in text or looks_like_record(text):
                continue
            out[n] = text
    return out


def wrong_place(path):
    """Проверяет, что файл учёта — тот самый, а не одноимённый в чужом репозитории.

    Живой случай: бот вёл учёт в клоне проекта, в DISPATCH.md в его корне. Записи
    делались исправно и коммитились, но пульт и линтер читают учётный репозиторий,
    поэтому инстанса не было видно пять часов. Ни одна проверка формата такого не
    ловит: содержимое файла было безупречным, неверным было его место.
    """
    real = os.path.normpath(os.path.abspath(path))
    if os.sep + "projects" + os.sep not in real:
        return (f"файл учёта должен лежать в projects/<проект>/, а лежит здесь: {real}. "
                "Похоже, это клон проекта, а не учётного репозитория")
    try:
        root = os.path.normpath(subprocess.run(
            ["git", "-C", os.path.dirname(real) or ".", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10).stdout.strip())
    except Exception:
        return None  # не в git — не наше дело, формат проверим как обычно
    if root:
        root = os.path.normpath(os.path.abspath(root))
        project_dir = os.path.normpath(os.path.abspath(os.path.join(root, "projects")))
        if (os.path.commonpath((real, project_dir)) != project_dir
                or not os.path.isfile(os.path.join(root, "LUNOBOT.md"))
                or not os.path.isfile(os.path.join(project_dir, "INDEX.md"))):
            return ("учёт ведётся вне клона учётного репозитория: "
                    f"{real}. Используй его projects/<проект>/DISPATCH.md")
    return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "DISPATCH.md"
    if misplaced := wrong_place(path):
        print(f"НЕ ТОТ РЕПОЗИТОРИЙ: {misplaced}")
        return 1
    timeout = 45
    if "--timeout-min" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout-min") + 1])
    since = None
    if "--since" in sys.argv:
        since = datetime.strptime(sys.argv[sys.argv.index("--since") + 1], "%d-%m-%Y")
    entries, problems = check(path, timeout, since)
    if "--added-only" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
        added = added_lines(path, base)
        if added is not None:
            # протухшие захваты — состояние, а не ошибка записи: в гейт не попадают
            problems = [p for p in problems if p[1] in added and p[0] != "протух"]
            for n, text in sorted(stray_lines(path).items()):
                if n in added:
                    problems.append(("формат", n, f"лишний текст в DISPATCH.md — используй acct_line.py: «{text[:80]}»"))
    print(f"действующих записей разобрано: {len(entries)}")
    if not problems:
        print("нарушений нет")
        return 0
    by_kind = {}
    for kind, line, msg in problems:
        by_kind.setdefault(kind, []).append((line, msg))
    for kind in sorted(by_kind, key=lambda k: -len(by_kind[k])):
        items = by_kind[kind]
        print(f"\n[{kind}] {len(items)}")
        for line, msg in items[:8]:
            print(f"  строка {line}: {msg}")
        if len(items) > 8:
            print(f"  ... ещё {len(items) - 8}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # вывод обрезан через | head
        sys.exit(0)
