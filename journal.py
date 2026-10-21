#!/usr/bin/env python3
"""Журнал инстанса: метрики кругов, события захватов и рефлексия (§ 4 п. 6; EVOLUTION.md, 21-10-2026).

    python3 journal.py add      --sign "<id>" --kind reflection --file <запись.json>    # рефлексия круга
    python3 journal.py add      --sign "<id>" --kind round --json '{…}'                 # метрики круга (раннер)
    python3 journal.py metrics  <лог круга> [--format claude|opencode]                  # метрики из лога → JSON
    python3 journal.py round    <лог круга> --number N --runner R --model M --round K --exit C --duration S  # раннер
    python3 journal.py read     [--since ДД-ММ-ГГГГ] [--kind K]                          # все журналы, JSON строками
    python3 journal.py digest   [--since ДД-ММ-ГГГГ] [--out REFLECTION.md]               # сводка для разбора (Лунобот-1)

Зачем. Учёт хранит состояние, а не опыт: что круг сделал, сколько стоил, где споткнулся. Раньше это жило в
чате круга и в логах раннера на диске одного узла (`~/.lunobot`), а находки ретро без жалобы терялись. С
захватами на ref (`claims.py`) пропала и история захватов из коммитов `DISPATCH.md`. Журнал собирает всё это
на GitHub, где его видят все узлы и Лунобот-1, разбирающий рефлексию.

Устройство: у каждого инстанса (номер + узел) свой ref `refs/journal/<узел>-<номер>` — цепочка коммитов с
пустым деревом, одна запись — один коммит, сообщение — `journal <kind>` и JSON. Писатели разных инстансов
не конкурируют (ref у каждого свой), пуш в `refs/journal/*` не запускает Actions и не трогает `main`.
Воркеры одного id пишут в один ref: гонка снимается lease и повтором.

Запись: {"ts": UTC ISO, "id": подпись, "kind": round|reflection|claim|digest, ...}. Рефлексия (`kind:
reflection`) — минимум `did` (список: что сделано, ссылки) и `friction` (список {"tag", "text"}: что заняло
больше, чем должно, мешало, делалось руками или дважды; пустой — тоже ответ); по желанию `ideas`, `cost`,
`main_advanced`. Метки `tag` — короткие и повторяемые (`read-instruction`, `ci-wait`, `push-race`,
`gate-false-positive`, `tool-<имя>`, `rule-unclear-§N`…), по ним digest считает повторы.
Коды: 0 — сделано, 1 — запись отклонена (формат, кодировка), 2 — сеть или вызов.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

NS = "refs/journal"
REMOTE_NS = "refs/heads/journal"  # на GitHub — ветки: прокси облачных сессий режет ref вне refs/heads (как у claims.py)
SIGN = re.compile(r"(?:Лунобот|Lunobot)-(\d+) \((?:node|instance) ([0-9a-f]{24}); ([A-Z]{3})")
KINDS = ("round", "reflection", "claim", "digest")


def git(repo, *args, data=None, env=None, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=env,
                       input=None if data is None else data.encode("utf-8"))
    r.stdout = r.stdout.decode("utf-8", "replace")
    r.stderr = r.stderr.decode("utf-8", "replace")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def ref_of(sign):
    m = SIGN.search(sign or "")
    return f"{NS}/{m.group(2)}-{m.group(1)}" if m else None


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate(rec):
    """Претензии к записи (пустой список — годится)."""
    problems = []
    if rec.get("kind") not in KINDS:
        problems.append(f"kind — одно из {KINDS}")
    if rec.get("kind") == "reflection":
        if not isinstance(rec.get("did"), list):
            problems.append("рефлексия: нужен список did (что сделано; пустой — если ничего)")
        fr = rec.get("friction")
        if not isinstance(fr, list) or any(not isinstance(f, dict) or not f.get("tag") or not f.get("text")
                                            for f in fr):
            problems.append("рефлексия: friction — список {\"tag\", \"text\"} (пустой список — тоже ответ)")
    from gh_post import check_text
    for value in _strings({k: v for k, v in rec.items() if k != "tail"}):  # хвост лога — как есть
        why = check_text(value) if value.strip() else ""
        if why:
            problems.append(f"кодировка: {why}: {value[:60]!r}")
    return problems


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)


def add(repo, sign, rec, remote="origin", quiet=False):
    """Дописать запись в журнал инстанса. 0 — записано, 1 — отклонено, 2 — сеть."""
    ref = ref_of(sign)
    if not ref:
        print("--sign: нужен полный id «Лунобот-N (node <24 hex>; LNX)»", file=sys.stderr)
        return 2
    rec = {"ts": now_iso(), "id": SIGN.search(sign).group(0) + ")", **rec}
    problems = validate(rec)
    if problems:
        for p in problems:
            print(f"ОТКАЗ: {p}")
        return 1
    tree = git(repo, "hash-object", "-t", "tree", "-w", "--stdin", data="").stdout.strip()
    msg = f"journal {rec['kind']}\n\n{json.dumps(rec, ensure_ascii=False, sort_keys=True)}\n"
    for _ in range(4):
        rref = REMOTE_NS + ref[len(NS):]
        r = git(repo, "fetch", "-q", remote, f"+{rref}:{ref}", check=False)
        old = git(repo, "rev-parse", "-q", "--verify", ref, check=False).stdout.strip() if r.returncode == 0 else ""
        if r.returncode and "couldn't find remote ref" not in r.stderr:
            time.sleep(1)
            continue
        args = ["commit-tree", tree] + (["-p", old] if old else [])
        commit = git(repo, *args, data=msg).stdout.strip()
        p = git(repo, "push", "-q", remote, f"--force-with-lease={rref}:{old}", f"{commit}:{rref}", check=False)
        if p.returncode == 0:
            git(repo, "update-ref", ref, commit, check=False)
            if not quiet:
                print(f"записано в {ref}: {rec['kind']}")
            return 0
        time.sleep(1)
    print("журнал: пуш не прошёл", file=sys.stderr)
    return 2


def try_add(repo, sign, rec, remote="origin"):
    """Лучшее усилие: событие журнала не должно ронять основное действие (захват, снятие)."""
    try:
        add(repo, sign, rec, remote, quiet=True)
    except Exception:  # noqa: BLE001 — журнал вторичен
        pass


def read(repo, remote="origin", since=None, kind=None):
    """Все записи всех журналов (после fetch), по времени."""
    git(repo, "fetch", "-q", remote, f"+{REMOTE_NS}/*:{NS}/*", "--prune", check=False)
    heads = git(repo, "for-each-ref", NS, "--format=%(refname)", check=False).stdout.split()
    out = []
    for h in heads:
        log = git(repo, "log", "--reverse", h, "--format=%x1e%B", check=False).stdout  # старые первыми
        for chunk in log.split("\x1e"):
            body = chunk.strip().split("\n", 2)
            if len(body) < 3:
                continue
            try:
                rec = json.loads(body[2])
            except ValueError:
                continue
            if since and rec.get("ts", "") < since:
                continue
            if kind and rec.get("kind") != kind:
                continue
            out.append(rec)
    return sorted(out, key=lambda r: r.get("ts", ""))


def metrics(path, fmt=None):
    """Метрики круга из лога раннера: стоимость, ходы, токены (Claude stream-json), строки ошибок."""
    text = open(path, encoding="utf-8", errors="replace").read()
    if not fmt:
        fmt = "opencode"
        for line in text.splitlines()[:50]:
            try:
                t = json.loads(line).get("type")
                if t in ("system", "assistant", "result"):
                    fmt = "claude"
                    break
                if t in ("step_start", "step_finish", "text", "tool_use", "reasoning"):
                    fmt = "opencode-json"  # opencode run --format json
                    break
            except (ValueError, AttributeError):
                continue
    m = {"log_format": fmt}
    said = []  # собственные слова бота (текст ассистента), без вывода инструментов: учёт публичный
    if fmt == "claude":
        results, usage = [], Counter()
        for line in text.splitlines():
            try:
                j = json.loads(line)
            except ValueError:
                continue
            if j.get("type") == "result":
                results.append(j)
            if j.get("type") == "assistant":
                for c in (j.get("message") or {}).get("content") or []:
                    if c.get("type") == "text" and c.get("text", "").strip():
                        said.append(c["text"].strip())
                    elif c.get("type") == "tool_use":
                        said.append(f"▶ {c.get('name')} {json.dumps(c.get('input'), ensure_ascii=False)[:160]}")
                u = (j.get("message") or {}).get("usage") or {}
                for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                    usage[k] += u.get(k) or 0
        if results:
            m["cost_usd"] = round(max(r.get("total_cost_usd") or 0 for r in results), 4)
            m["turns"] = sum(r.get("num_turns") or 0 for r in results)
            # итог круга — ПОСЛЕДНИЙ result: `claude -p` дожидается фоновых воркеров и продолжает по их
            # уведомлениям, первый result — лишь промежуточная остановка («жду отчёт воркера»)
            m["result"] = (results[-1].get("result") or "")[:600]
            m["resumes"] = len(results) - 1
        m["tokens"] = dict(usage)
    elif fmt == "opencode-json":
        # step_finish.part: cost (USD за шаг) и tokens (TokenUsage: вложенные счётчики) — суммируем по шагам
        cost, usage, steps, last = 0.0, Counter(), 0, ""
        for line in text.splitlines():
            try:
                j = json.loads(line)
            except ValueError:
                continue
            part = j.get("part") or j.get("data") or {}
            if j.get("type") == "step_finish":
                steps += 1
                cost += float(part.get("cost") or 0)
                for k, v in _flat(part.get("tokens") or {}):
                    usage[k] += v
            elif j.get("type") == "text" and (part.get("text") or "").strip():
                last = part["text"].strip()
                said.append(last)
            elif j.get("type") == "tool_use":
                said.append(f"▶ {part.get('tool') or part.get('name') or 'tool'}")
            elif j.get("type") == "error":
                said.append("Error: " + json.dumps(j.get("error") or part, ensure_ascii=False)[:300])
        m.update({"cost_usd": round(cost, 4), "turns": steps, "tokens": dict(usage), "result": last[:600]})
    # лимит — только по итогу круга и строкам вне JSON (stderr среды), не по выводу инструментов
    if fmt in ("claude", "opencode-json"):
        tail = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("{")) + "\n" + m.get("result", "")
        tail += "\n" + "\n".join(x for x in said if x.startswith("Error: "))
    else:  # opencode печатает вывод инструментов простым текстом — смотрим только его строки «Error:»
        plain = re.sub(r"\x1b\[[0-9;]*m", "", text)
        tail = "\n".join(l for l in plain.splitlines() if re.match(r"\W*Error\b", l))
    m["rate_limited"] = bool(re.search(r"(?i)usage limit|hit your limit|rate.?limit|429 Too Many|overloaded|quota exceeded", tail))
    if fmt == "opencode":
        said = tail.splitlines()
    m["_said"] = said
    m["errors"] = len(re.findall(r"(?i)\b(traceback|cannot lock ref|\[rejected\]|\[remote rejected\])", text))
    return m


def _flat(d, prefix=""):
    """Числовые листья вложенного словаря: {"cache": {"read": 5}} → ("cache.read", 5)."""
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flat(v, f"{prefix}{k}.")
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            yield f"{prefix}{k}", v


def digest(recs):
    """Сводка для разбора: эффективность по средам/моделям и повторяющиеся трения."""
    lines = ["# Рефлексия флота — сводка", "",
             f"Записей: {len(recs)}; период: {recs[0]['ts'] if recs else '—'} … {recs[-1]['ts'] if recs else '—'}.",
             "Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».", ""]
    rounds = [r for r in recs if r["kind"] == "round"]
    refl = [r for r in recs if r["kind"] == "reflection"]
    by = defaultdict(list)
    for r in rounds:
        by[(r.get("runner") or "?", r.get("model") or "?")].append(r)
    lines += ["## Круги по раннерам и моделям", "",
              "| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    did = {(r["id"], r.get("round")): bool(r.get("did")) for r in refl}
    for (runner, model), rs in sorted(by.items()):
        dur = [r.get("duration_s", 0) / 60 for r in rs if r.get("duration_s")]
        cost = [r["cost_usd"] for r in rs if isinstance(r.get("cost_usd"), (int, float))]
        useful = sum(1 for r in rs if did.get((r["id"], r.get("round"))))
        lines.append(f"| {runner} | {model} | {len(rs)} | {sum(1 for r in rs if r.get('exit') == 124)} | "
                     f"{statistics.median(dur):.0f} | {sum(cost):.2f} | "
                     f"{statistics.median(cost) if cost else 0:.2f} | {useful} |" if dur else
                     f"| {runner} | {model} | {len(rs)} | — | — | {sum(cost):.2f} | — | {useful} |")
    bad = [r for r in rounds if r.get("tail")]
    if bad:
        lines += ["", "## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова", ""]
        for r in bad[-10:]:
            lines.append(f"- {r['ts']} {r.get('runner')} круг {r.get('round')}, код {r.get('exit')}"
                         f"{', лимит' if r.get('rate_limited') else ''}:")
            lines += [f"  > {l[:200]}" for l in r["tail"].splitlines()[-5:]]
    tags = defaultdict(list)
    for r in refl:
        for f in r.get("friction") or []:
            tags[f["tag"]].append((r["ts"], r["id"], f["text"]))
    lines += ["", "## Трения (повторы сверху)", ""]
    for tag, items in sorted(tags.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines.append(f"- **{tag}** — {len(items)}× ({len({i[1] for i in items})} инст.)")
        for ts, who, text in items[-3:]:
            lines.append(f"  - {ts} {who}: {text[:240]}")
    ideas = [(r["ts"], r["id"], i) for r in refl for i in (r.get("ideas") or [])]
    if ideas:
        lines += ["", "## Идеи", ""] + [f"- {ts} {who}: {i[:240]}" for ts, who, i in ideas[-30:]]
    claims = [r for r in recs if r["kind"] == "claim" and r.get("event") == "drop"]
    held = [c.get("held_min") for c in claims if isinstance(c.get("held_min"), (int, float))]
    if held:
        lines += ["", f"Захватов снято: {len(held)}, медиана удержания {statistics.median(held):.0f} мин, "
                  f"дольше 2 ч: {sum(1 for h in held if h > 120)}."]
    return "\n".join(lines) + "\n"


def last_digest_ts(recs):
    ds = [r.get("until") for r in recs if r["kind"] == "digest" and r.get("until")]
    return max(ds) if ds else None


def _since(arg):
    if not arg:
        return None
    return datetime.strptime(arg, "%d-%m-%Y").strftime("%Y-%m-%dT00:00:00Z")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("op", choices=["add", "metrics", "round", "read", "digest"])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--sign")
    ap.add_argument("--kind")
    ap.add_argument("--json")
    ap.add_argument("--file")
    ap.add_argument("--format")
    ap.add_argument("--since")
    ap.add_argument("--out")
    ap.add_argument("--number", type=int, help="round: номер бота; подпись — по node.py этого узла")
    for k in ("runner", "model", "round", "exit", "duration"):
        ap.add_argument("--" + k)
    ap.add_argument("--repo", default=HERE)
    ap.add_argument("--remote", default="origin")
    a = ap.parse_args(argv)
    try:
        if a.op == "metrics":
            m = metrics(a.path, a.format)
            m.pop("_said", None)
            print(json.dumps(m, ensure_ascii=False))
            return 0
        if a.op == "round":
            import node
            import release
            sign = a.sign or f"Лунобот-{a.number} (node {node.identify()}; {release.platform_code()})"
            rec = {"kind": "round", "runner": a.runner, "model": a.model,
                   "round": int(a.round) if a.round else None, "exit": int(a.exit) if a.exit else None,
                   "duration_s": int(a.duration) if a.duration else None}
            if a.path and os.path.exists(a.path):
                m = metrics(a.path, a.format)
                said = m.pop("_said", [])
                bad = rec.get("exit") not in (0, None) or m.get("rate_limited") or not m.get("result", "x")
                if bad and said:
                    # неудачный круг: хвост — чтобы причину видел разбор рефлексии с любого узла (полный лог на диске раннера)
                    rec["tail"] = "\n".join(said[-15:])[-4000:]
                rec.update(m)
            return add(a.repo, sign, {k: v for k, v in rec.items() if v is not None}, a.remote)
        if a.op == "add":
            raw = open(a.file, encoding="utf-8").read() if a.file else (a.json or "{}")
            try:
                rec = json.loads(raw)
            except ValueError as e:
                print(f"ОТКАЗ: не JSON: {e}")
                return 1
            if a.kind:
                rec["kind"] = a.kind
            return add(a.repo, a.sign, rec, a.remote)
        recs = read(a.repo, a.remote, _since(a.since), a.kind if a.op == "read" else None)
        if a.op == "read":
            for r in recs:
                print(json.dumps(r, ensure_ascii=False, sort_keys=True))
            return 0
        start = _since(a.since) or last_digest_ts(recs)
        recs = [r for r in recs if not start or r.get("ts", "") > start]
        text = digest(recs)
        if a.out:
            with open(a.out, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print(f"сводка: {a.out}; записей {len(recs)}; после разбора — journal.py add --kind digest "
                  f"--json '{{\"until\": \"{recs[-1]['ts'] if recs else now_iso()}\", \"actions\": [...]}}'")
        else:
            print(text)
        return 0
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
