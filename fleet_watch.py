#!/usr/bin/env python3
"""Наблюдатель менеджера флота (§ 4, «Роли»): следит, что флот узла не простаивает.

    fleet_watch.py --node <24 hex> [--number <N>] [--min 4] [--interval 60] [--once]

Раз в --interval секунд обновляет учётный клон и печатает строку ТОЛЬКО когда есть повод
разбудить менеджера:

  ПРОСТОЙ   — живых захватов сессии (refs/claims, claims.py) меньше --min, а работа есть
  КРАСНОЕ   — train.py health по проекту со staging вернул 1 (красный staging/main, застой)
  ПРОТУХ    — захват сессии держится дольше 45 минут без отметки; а также
              `ПРОТУХ очередь <id>` — блок OWNER_QUEUE.md `Состояние: взял в работу`, у которого
              последняя метка времени (Состояние/Прогресс/Доп. проверка/Доп. шаг) старше 90 минут
              и в DISPATCH.md нет строки захвата с этим id в «ёлочках» (§ 6, § 8): подхватывай

Сессия — захваты с id `Лунобот-<N> (node <узел>; …)`: потолок воркеров считается на сессию
(LUNOBOT.md § 4, «(б)»), а на одном узле могут работать сессии разных номеров. Без --number
считаются захваты всего узла, как раньше.

Одинаковый повод повторяется не чаще раза в 5 минут. Только чтение: ничего не пушит, ничего
не захватывает. Менеджер гоняет его с --once в процесс-часах под Monitor и сам реагирует
на каждую строку (заявками на воркеров через основной инстанс).
"""
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import claims

ROOT = os.path.dirname(os.path.abspath(__file__))
REPEAT = timedelta(minutes=5)
STALE = timedelta(minutes=45)
QUEUE_STALE = timedelta(minutes=90)  # § 6: захват без следов дольше 90 минут брошен
TS = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}) ")
# метка следа в блоке OWNER_QUEUE.md: `ДД-ММ-ГГГГ ЧЧ:ММ[:СС]`; одна дата без времени — след «в
# течение суток», считается концом этих суток (лучше опоздать с подхватом, чем ложно сорвать живой)
QUEUE_TS = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})(?: (\d{2}):(\d{2})(?::(\d{2}))?)?")
QUEUE_TRACE = re.compile(r"^(?:Состояние|Прогресс|Доп\. проверка|Доп\. шаг)\b", re.M)


def sh(*cmd, timeout=180):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, ""


def projects():
    with open(os.path.join(ROOT, "projects", "INDEX.md"), encoding="utf-8") as f:
        text = f.read()
    return re.findall(r"^\d+\.\s*\[([^\]]+)\]", text, re.M)


def captures(node, number=None):
    own = re.compile(rf"Лунобот-{re.escape(number)} \((?:node|instance) {re.escape(node)}\b") \
        if number else None
    latest = {}
    for p in projects():
        lines = claims.dispatch_text(ROOT, p).splitlines()
        for line in lines:
            if node in line and ("взял" in line or "работаю" in line) \
                    and (own is None or own.search(line)):
                m = TS.match(line)
                ts = (datetime.strptime(m.group(1), "%d-%m-%Y %H:%M:%S")
                      .replace(tzinfo=timezone.utc) if m else None)
                url = re.search(r"https://github\.com/\S+?/(?:issues|pull)/\d+", line)
                custom = re.search(r"кастомн\w+ задач\w+\s*«([^»]+)»", line)
                key = url.group(0) if url else (custom.group(1) if custom else line.strip())
                part = re.search(r"\(часть \d+ из \d+\)", line)
                if part:
                    key += " " + part.group(0)
                capture_key = (p, key)
                previous = latest.get(capture_key)
                if previous is None or (ts and (previous[1] is None or ts >= previous[1])):
                    latest[capture_key] = (p, ts, line.strip())
    return list(latest.values())


def queue_blocks(content):
    """Блоки OWNER_QUEUE.md: шапка (до первой заметки) — не поручение; заметки разделены
    строкой `--`, формальные блоки начинаются с `## id`; поле «Адресат» больше не используется."""
    notes = re.split(r"^--\s*$", content, flags=re.M)[1:] or []
    for note in notes:
        for block in re.split(r"(?=^## )", note, flags=re.M):
            if block.strip():
                yield block.strip()


def read_queue():
    queue = os.path.join(ROOT, "OWNER_QUEUE.md")
    if not os.path.exists(queue):
        return ""
    with open(queue, encoding="utf-8") as source:
        return source.read()


def queue_last_trace(text):
    """Последняя метка времени (UTC) в строках следа блока или None."""
    best = None
    for line in text.splitlines():
        if not QUEUE_TRACE.match(line):
            continue
        for m in QUEUE_TS.finditer(line):
            d, mo, y, h, mi, sec = m.groups()
            try:
                if h is None:
                    ts = datetime(int(y), int(mo), int(d), 23, 59, 59, tzinfo=timezone.utc)
                else:
                    ts = datetime(int(y), int(mo), int(d), int(h), int(mi), int(sec or 0),
                                  tzinfo=timezone.utc)
            except ValueError:
                continue
            if best is None or ts > best:
                best = ts
    return best


def stale_queue(now):
    """Блоки `Состояние: взял в работу` без следов дольше QUEUE_STALE и без строки захвата
    с их id в «ёлочках» в DISPATCH.md. «Ждёт владельца» и свободные блоки не трогает."""
    dispatch = ""
    for p in projects():
        dispatch += claims.dispatch_text(ROOT, p) + "\n"
    found = []
    for text in queue_blocks(read_queue()):
        key = re.match(r"## (\S+)", text)
        states = re.findall(r"^Состояние: (.+)$", text, re.M)
        if not key or not states or not states[-1].strip().startswith("взял в работу"):
            continue
        ident = key.group(1)
        if re.search(rf"«[^»\n]*(?<![\w-]){re.escape(ident)}(?![\w-])[^»\n]*»", dispatch):
            continue
        last = queue_last_trace(text)
        if last is not None and now - last > QUEUE_STALE:
            found.append((ident, last, states[-1].strip()))
    return found


def free_work():
    found = []
    for text in queue_blocks(read_queue()):
        key = re.match(r"## ([^\n]+)", text)
        state = re.search(r"^Состояние: (.+)$", text, re.M)
        if state and state.group(1).strip() != "свободно":
            continue
        label = key.group(1) if key else text.splitlines()[0][:40]
        found.append(f"очередь {label}")
    for p in projects():
        tri = os.path.join(ROOT, "projects", p, "TRIAGE.md")
        dis = os.path.join(ROOT, "projects", p, "DISPATCH.md")
        if not os.path.exists(tri):
            continue
        taken = claims.dispatch_text(ROOT, p, dis)
        with open(tri, encoding="utf-8") as f:
            tri_lines = f.readlines()
        for line in tri_lines:
            m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+)\|\s*свободен\s*\|", line)
            if m and f"/issues/{m.group(1)}" not in taken:
                found.append(f"{p}#{m.group(1)}(п{m.group(2).strip()})")
        rc, out = sh(sys.executable, "check_triage.py", p)
        drift = len(re.findall(r"^\[расхождение\]", out, re.M))
        if rc and drift:
            found.append(f"{p}: расхождений TRIAGE {drift}")
    return found


def staged_repos():
    rc, out = sh(sys.executable, "-c", "import train; print('\\n'.join(train.staged_repos()))")
    return [r for r in out.split() if "/" in r] if rc == 0 else []


def check(node, minimum, last, number=None):
    sh("git", "pull", "-q", "--rebase")
    claims._fetched.clear()  # захваты — refs/claims, pull их не обновляет
    now = datetime.now(timezone.utc)
    events = []
    live = captures(node, number)
    if len(live) < minimum:
        work = free_work()
        who = f"сессии Лунобот-{number}" if number else "узла"
        events.append(("ПРОСТОЙ", f"захватов {who} {len(live)} < {minimum}; свободная работа: "
                       f"{', '.join(work[:12]) or 'по § 5 п. 6 (покрытие) или следующий проект'}"))
    for p, ts, line in live:
        if ts and now - ts > STALE:
            events.append((f"ПРОТУХ {line[:60]}", f"захват держится "
                           f"{int((now - ts).total_seconds() // 60)} мин: {line[:160]}"))
    for ident, ts, state in stale_queue(now):
        events.append((f"ПРОТУХ очередь {ident}",
                       f"блок OWNER_QUEUE.md «{ident}» без следов {int((now - ts).total_seconds() // 60)} мин "
                       f"(последний {ts:%d-%m-%Y %H:%M} UTC) и без строки захвата в DISPATCH.md — "
                       f"подхватить по § 6/§ 8: {state[:100]}"))
    if not last.get("_health") or now - last["_health"] > timedelta(minutes=5):
        last["_health"] = now
        for repo in staged_repos():
            rc, out = sh(sys.executable, "train.py", "health", repo)
            if rc == 1:
                # health пишет «staging: red» латиницей — без этого красный staging не виден
                lines = [l for l in out.splitlines()
                         if re.search(r"КРАСН|ИНЦИДЕНТ|^staging: red", l)]
                events.append((f"КРАСНОЕ {repo}", f"{repo}: " + " | ".join(lines)[:400]))
    for key, text in events:
        if key not in last or now - last[key] > REPEAT:
            last[key] = now
            print(f"{now:%H:%M:%S}Z {key.split()[0]}: {text}", flush=True)


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    node = opt("--node")
    if not node:
        print(__doc__)
        return 2
    number = opt("--number")
    minimum, interval, last = int(opt("--min", "4")), int(opt("--interval", "60")), {}
    while True:
        check(node, minimum, last, number)
        if "--once" in argv:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
