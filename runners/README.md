# Раннеры кругов

Скрипты запускают Лунобота круг за кругом: каждый круг — отдельный неинтерактивный процесс
с чистым контекстом (`timeout --foreground 1800`), между кругами пауза 15 минут, логи в
`~/.lunobot/logs*`. Один раннер на номер бота на узел (lock `/tmp/lunobot-<номер>/runner.lock`).

| Скрипт | Среда и модель | Номер |
|---|---|---|
| `lunobot-round-claude.sh sonnet\|opus` | Claude Code, `EFFORT=high` по умолчанию | 1 |
| `lunobot-round.sh` | opencode, Nemotron 3 Ultra Free | 1 |
| `lunobot-round-luna-high.sh` | opencode, GPT-6 Luna High | 2 |
| `lunobot-round-muse.sh` | opencode, Muse Spark 1.3 Free | 2 |

В режиме одного круга потолок воркеров (б) — 1 (LUNOBOT.md § 5): промпт каждого раннера
говорит это явно, менеджер в потолок не входит.
