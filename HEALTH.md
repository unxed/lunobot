# Пульс флота

Пишет `janitor.py` (`pulse.py`) по журналам `refs/journal/*`; вручную не править. Тревога — срочная работа § 5 п. 2 для любого бота (модуль round, «Пульс»), снимается сама, когда условие пропало.

- **rounds-failing** — за 6 ч упали 15 из 18 кругов (lunobot-round-luna-high.sh/openai/gpt-6-luna#high: 15): хвосты — в `journal.py digest`, раздел «Неудачные круги»
- **friction-repeats** — трения повторяются без разбора: `tool-train.py` ×12, `ci-wait` ×9, `env-opencode` ×8, `deadline` ×8, `gate-false-positive` ×6 — разбор рефлексии (Лунобот-1) или жалоба § 12
