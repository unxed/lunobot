# Пульс флота

Пишет `janitor.py` (`pulse.py`) по журналам `refs/journal/*`; вручную не править. Тревога — срочная работа § 5 п. 2 для любого бота (модуль round, «Пульс»), снимается сама, когда условие пропало.

- **rounds-failing** — за 6 ч упали 12 из 17 кругов (lunobot-round-luna-high.sh/openai/gpt-6-luna#high: 12): хвосты — в `journal.py digest`, раздел «Неудачные круги»
- **friction-repeats** — трения повторяются без разбора: `tool-train.py` ×11, `ci-wait` ×7, `gate-false-positive` ×6, `deadline` ×6, `env-opencode` ×4 — разбор рефлексии (Лунобот-1) или жалоба § 12
