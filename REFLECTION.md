# Рефлексия флота — сводка

Записей: 22; период: 2026-11-19T13:03:21Z … 2026-11-19T16:04:30Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 4 | 0 | 18 | 0.00 | 0.00 | 0 | — | — | — |

## Трения (повторы сверху)

- **tool-train.py** — 3× (1 инст.)
  - 2026-11-19T13:14:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all сообщил, что 5 коммитов staging ждут main 17.5 ч; train #2349 запущен, в run #44529310453 появились failed checks до завершения полной матрицы. Логи недоступны, безопасная причина ещё не установлена.
  - 2026-11-19T14:57:01Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): health accepts only a repository argument; an initial call with --sign exited 2 before any work, then the correct invocation reported the f4 stall.
  - 2026-11-19T15:31:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all повторно отправил ту же вершину staging `5c3bed6725c18561950ce6efd0527ceb0f47796` после красных поездов; механизм уже вынесен в unxed/lunobot#338 и PR #339, этот круг не устранил повтор.
- **duplicate-work** — 1× (1 инст.)
  - 2026-11-19T13:57:48Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): f4 trains #2344/#2345 replayed identical staging/base SHAs after a red base control, repeating expensive CI; complaint PR #339 adds an exact-pair hold
- **read-instruction** — 1× (1 инст.)
  - 2026-11-19T13:14:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Read усекал LUNOBOT.md на строках 355/764 и round.md на 380; понадобились offset-продолжения до EOF.

## Идеи

- 2026-11-19T13:14:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): После exact-SHA sandbox обработать завершённые логи #2349 через tick и продолжить только из записи status/2071; не повторять CI вслепую.
- 2026-11-19T13:57:48Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep the train open and mark the exact head/base pair after a red control base; unblock only when main or train head changes.
- 2026-11-19T15:31:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): По sandbox exact-SHA проверить поле match и фактическую разметку ячейки перед исправлением причины повторяющегося red train.

Захватов снято: 5, медиана удержания 11 мин, дольше 2 ч: 0.
