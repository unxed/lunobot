# Пульс флота

Пишет `janitor.py` (`pulse.py`) по журналам `refs/journal/*`; вручную не править. Тревога — срочная работа § 5 п. 2 для любого бота (модуль round, «Пульс»), снимается сама, когда условие пропало.

- **rounds-failing** — за 6 ч упали 6 из 6 кругов (lunobot-round-luna-high.sh/openai/gpt-6-luna#high: 6): хвосты — в `journal.py digest`, раздел «Неудачные круги»
- **friction-repeats** — трения повторяются без разбора: `tool-train.py` ×16, `env-opencode` ×10, `deadline` ×10, `ci-wait` ×10, `tool-claims.py` ×7 — разбор рефлексии (Лунобот-1) или жалоба § 12
