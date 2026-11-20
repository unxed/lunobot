# Рефлексия флота — сводка

Записей: 20; период: 2026-11-20T06:18:41Z … 2026-11-20T08:25:59Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 5 | 0 | 15 | 0.00 | 0.00 | 0 | — | — | — |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-20T06:56:06Z lunobot-round-luna-high.sh круг 409, код 1:
  > Круг завершён: `tick-all` и ретро-health показали зелёные staging и `main` для f4/vtui; очереди и гейты проверены, рефлексия записана.
  > 
  > Исправление `tv3#21` опубликовано в [PR #29](https://github.com/unxed/tv3/pull/29); CI зелёный на SHA `be7d549`. Учёт ветки, CI и состояние тикета синхронизированы, захват снят. Аудит — PASS.
  > 
  > `janitor` и удаляющую уборку не запускал: для этого не было отдельного разрешения после запрета на деструктивные действия.

## Трения (повторы сверху)

- **read-instruction** — 3× (1 инст.)
  - 2026-11-20T06:54:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Shell output for the 834-line LUNOBOT.md was truncated; complete coverage required three offset reads (1–355, 356–764, 765–834).
  - 2026-11-20T07:10:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): LUNOBOT.md был выдан до строки 355, продолжение потребовало ещё двух чтений до строки 834; все обязательные разделы дочитаны.
  - 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): До первого шага прочитаны ядро (834 строки), round (531), trains (284), env-opencode (47); перед land также trains-land (141) и sandbox (79). Предварительное чтение заняло несколько минут и дало длинный контекст.
- **tool-git** — 2× (1 инст.)
  - 2026-11-20T06:54:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial accounting pull refused because generated projects/f4/DISPATCH.md was dirty; after inspecting its two-line diff, autoStash pull/rebase succeeded and restored the diff.
  - 2026-11-20T07:10:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): После fetch глубокой ветки временный clone не позволил switch --track на вложенный remote ref; переключился на проверенный SHA e5087fc и продолжил работу.
- **env-opencode** — 1× (1 инст.)
  - 2026-11-20T08:05:43Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Persistent /tmp/lunobot-2/f4 checkout contained over 100 pre-existing modified/deleted paths; avoided touching it and cloned clean f4 into the step directory.
- **tool-fleet_watch.py** — 1× (1 инст.)
  - 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый вызов без --node и --number вернул usage/code 2; правильный вызов с node 19d368003c6c048e43dbec70 и number 2 завершился успешно.
- **tool-gh** — 1× (1 инст.)
  - 2026-11-20T07:10:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Сразу после workflow_dispatch список gh run list вернул предыдущий запуск 44685874166; использован URL из ответа dispatch и один gh run view подтвердил 44692509773 на точном SHA.
- **tool-git-pull** — 1× (1 инст.)
  - 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): pull --rebase в основном клоне учёта не смог обновить refs/remotes/origin/claims из-за старой плоской refs/f4/... при новой вложенной refs/f4/.../part-3; использован свежий clone, ничего не prune-илось. См. account-336 / PR #337.
- **tool-train.py** — 1× (1 инст.)
  - 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый land отказал из-за отсутствия Touch: в commit e5087fce и раннем commit 09289528; пришлось изменить только сообщения двух commit, повторно запарковать и запустить land.

## Идеи

- 2026-11-20T06:54:17Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Use the environment module’s offset-based reader for large instruction files from the first read.
- 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Уменьшить повторное чтение инструкции кэшированием неизменных модулей в рамках сессии; здесь все обязательные модули были прочитаны до выбора шага.
- 2026-11-20T07:40:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Довести устранение коллизии иерархии remote refs по unxed/lunobot#336/#337; безопасный временный обход — свежий clone, не remote prune.
- 2026-11-20T08:05:43Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep using isolated clean step clones when the persistent checkout is dirty.

Захватов снято: 4, медиана удержания 6 мин, дольше 2 ч: 0.
