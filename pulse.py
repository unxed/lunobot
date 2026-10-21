#!/usr/bin/env python3
"""Пульс петли самоулучшения: тревоги в HEALTH.md (EVOLUTION.md, 21-10-2026, «сторож самоулучшения»).

    python3 pulse.py [--write]      # без --write только печатает тревоги

Рефлексия (journal.py) чинит то, что боты замечают. Сломаться может и сама петля: боты перестали писать
рефлексию, Лунобот-1 не разбирает журналы, круги массово падают, повтор трения не дошёл до жалобы. Изнутри
такую поломку боты не увидят — значит, смотреть должен тот, кто от них не зависит. Поэтому пульс считает
`janitor.py` в Actions каждые 10 минут по журналам `refs/journal/*` и пишет `HEALTH.md` — только при смене
набора тревог, без метки времени прогона, чтобы не плодить коммиты. Каждый круг читает `HEALTH.md` первым
после `OWNER_QUEUE.md` (модуль round): тревога — срочная работа § 5 п. 2.
"""
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import journal  # noqa: E402

HEADER = ("# Пульс флота\n\nПишет `janitor.py` (`pulse.py`) по журналам `refs/journal/*`; вручную не править. "
          "Тревога — срочная работа § 5 п. 2 для любого бота (модуль round, «Пульс»), снимается сама, когда "
          "условие пропало.\n")


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def alarms(recs, now=None):
    """Список (ключ, текст) тревог по записям журналов."""
    now = now or datetime.now(timezone.utc)
    d6, d24, d48 = iso(now - timedelta(hours=6)), iso(now - timedelta(hours=24)), iso(now - timedelta(hours=48))
    rounds24 = [r for r in recs if r["kind"] == "round" and r["ts"] >= d24]
    refl24 = [r for r in recs if r["kind"] == "reflection" and r["ts"] >= d24]
    out = []
    if len(rounds24) >= 4 and len(refl24) < len(rounds24) / 2:
        out.append(("no-reflection", f"за сутки {len(rounds24)} кругов, а записей рефлексии {len(refl24)}: боты не "
                    "пишут рефлексию (модуль round, «Рефлексия») — выясни, какие раннеры/модели, и почини причину"))
    digests = [r["ts"] for r in recs if r["kind"] == "digest"]
    l1 = [r for r in recs if r["kind"] == "round" and r["ts"] >= d48 and r.get("id", "").startswith("Лунобот-1 ")]
    refl_all = [r for r in recs if r["kind"] == "reflection"]
    if l1 and refl_all and (not digests or max(digests) < d48) and refl_all[0]["ts"] < d24:
        out.append(("no-digest", "Лунобот-1 работает, а разбора рефлексии не было больше двух суток (`journal.py "
                    "digest`, модуль round) — разбери и выясни, почему не запускался"))
    rounds6 = [r for r in recs if r["kind"] == "round" and r["ts"] >= d6]
    bad6 = [r for r in rounds6 if r.get("exit") not in (0, None) or r.get("rate_limited")]
    if len(rounds6) >= 3 and len(bad6) * 2 >= len(rounds6):
        who = Counter(f"{r.get('runner')}/{r.get('model')}" for r in bad6).most_common(3)
        out.append(("rounds-failing", f"за 6 ч упали {len(bad6)} из {len(rounds6)} кругов ({', '.join(f'{k}: {n}' for k, n in who)}): "
                    "хвосты — в `journal.py digest`, раздел «Неудачные круги»"))
    since = max(digests) if digests else d48
    tags = Counter(f["tag"] for r in recs if r["kind"] == "reflection" and r["ts"] > since
                   for f in r.get("friction") or [])
    hot = [(t, n) for t, n in tags.most_common() if n >= 3]
    if hot:
        out.append(("friction-repeats", "трения повторяются без разбора: " + ", ".join(f"`{t}` ×{n}" for t, n in hot[:5])
                    + " — разбор рефлексии (Лунобот-1) или жалоба § 12"))
    return out


def render(found):
    if not found:
        return HEADER + "\nТревог нет.\n"
    return HEADER + "\n" + "\n".join(f"- **{k}** — {t}" for k, t in found) + "\n"


def main(argv):
    recs = journal.read(HERE)
    text = render(alarms(recs))
    path = os.path.join(HERE, "HEALTH.md")
    if "--write" in argv:
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if old != text:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("HEALTH.md обновлён")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
