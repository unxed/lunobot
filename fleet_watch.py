#!/usr/bin/env python3
"""Наблюдатель менеджера флота (§ 4, «Роли»): следит, что флот узла не простаивает.

    fleet_watch.py --node <24 hex> [--number <N>] [--min 4] [--interval 60] [--once]

Раз в --interval секунд обновляет учётный клон и печатает строку ТОЛЬКО когда есть повод
разбудить менеджера:

  ПРОСТОЙ   — живых захватов сессии в projects/*/DISPATCH.md меньше --min, а работа есть
  КРАСНОЕ   — train.py health по проекту со staging вернул 1 (красный staging/main, застой)
  ПРОТУХ    — захват сессии держится дольше 45 минут без отметки

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

ROOT = os.path.dirname(os.path.abspath(__file__))
REPEAT = timedelta(minutes=5)
STALE = timedelta(minutes=45)
TS = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}) ")


def sh(*cmd, timeout=180):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, ""


def projects():
    text = open(os.path.join(ROOT, "projects", "INDEX.md"), encoding="utf-8").read()
    return re.findall(r"^\d+\.\s*\[([^\]]+)\]", text, re.M)


def captures(node, number=None):
    own = re.compile(rf"Лунобот-{re.escape(number)} \((?:node|instance) {re.escape(node)}\b") \
        if number else None
    out = []
    for p in projects():
        path = os.path.join(ROOT, "projects", p, "DISPATCH.md")
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            if node in line and ("взял" in line or "работаю" in line) \
                    and (own is None or own.search(line)):
                m = TS.match(line)
                ts = (datetime.strptime(m.group(1), "%d-%m-%Y %H:%M:%S")
                      .replace(tzinfo=timezone.utc) if m else None)
                out.append((p, ts, line.strip()))
    return out


def free_work():
    found = []
    queue = os.path.join(ROOT, "OWNER_QUEUE.md")
    if os.path.exists(queue):
        with open(queue, encoding="utf-8") as source:
            content = source.read()
        # шапка (до первой заметки) — не поручение; заметки разделены строкой `--`,
        # формальные блоки начинаются с `## id`; поле «Адресат» больше не используется
        notes = re.split(r"^--\s*$", content, flags=re.M)[1:] or []
        for note in notes:
            for block in re.split(r"(?=^## )", note, flags=re.M):
                text = block.strip()
                if not text:
                    continue
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
        taken = open(dis, encoding="utf-8").read() if os.path.exists(dis) else ""
        for line in open(tri, encoding="utf-8"):
            m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+)\|\s*свободен\s*\|", line)
            if m and f"/issues/{m.group(1)}" not in taken:
                found.append(f"{p}#{m.group(1)}(п{m.group(2).strip()})")
        rc, out = sh("python3", "check_triage.py", p)
        drift = len(re.findall(r"^\[расхождение\]", out, re.M))
        if rc and drift:
            found.append(f"{p}: расхождений TRIAGE {drift}")
    return found


def staged_repos():
    rc, out = sh("python3", "-c", "import train; print('\\n'.join(train.staged_repos()))")
    return [r for r in out.split() if "/" in r] if rc == 0 else []


def check(node, minimum, last, number=None):
    sh("git", "pull", "-q", "--rebase")
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
    if not last.get("_health") or now - last["_health"] > timedelta(minutes=5):
        last["_health"] = now
        for repo in staged_repos():
            rc, out = sh("python3", "train.py", "health", repo)
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
