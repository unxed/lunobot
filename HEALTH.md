# Пульс флота

Пишет `janitor.py` (`pulse.py`) по журналам `refs/journal/*`; вручную не править. Тревога — срочная работа § 5 п. 2 для любого бота (модуль round, «Пульс»), снимается сама, когда условие пропало.

- **rounds-failing** — за 6 ч упали 2 из 3 кругов (lunobot-round-luna-high.sh/openai/gpt-6-luna#high: 2): хвосты — в `journal.py digest`, раздел «Неудачные круги»
