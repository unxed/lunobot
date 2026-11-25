# Рефлексия флота — сводка

Записей: 9; период: 2026-11-25T20:39:10Z … 2026-11-25T21:33:33Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 2 | 0 | 10 | 0.00 | 0.00 | 0 | — | — | — |

## Трения (повторы сверху)

- **tool-git** — 2× (1 инст.)
  - 2026-11-25T20:39:23Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial pull --rebase failed because accounting clone has existing edits in projects/dn/CI.md and status/176.md; preserved them and read OWNER_QUEUE.md through GitHub API. Same issue is tracked in PR unxed/lunobot#342.
  - 2026-11-25T21:06:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial pull --rebase in the persistent accounting clone was blocked by pre-existing modified projects/dn/CI.md and projects/dn/status/176.md; preserved them and used isolated fresh clones instead.
- **tool-pull** — 1× (1 инст.)
  - 2026-11-25T21:32:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): accounting pull --rebase failed because the persistent clone has two pre-existing modified dn files and is 291 commits behind; preserved it and used a separate clean clone for tick-all.

## Идеи

- 2026-11-25T20:39:23Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Continue using a clean accounting clone when the persistent clone contains edits; no duplicate complaint while #342 is pending.
- 2026-11-25T21:06:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep using an isolated fresh accounting clone when a persistent clone has unexplained dirty files; do not clean or overwrite them.
- 2026-11-25T21:32:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): At circle start, read OWNER_QUEUE from the known remote snapshot if persistent-clone pull is blocked, then continue only from an isolated clean clone.

Захватов снято: 1, медиана удержания 2 мин, дольше 2 ч: 0.
