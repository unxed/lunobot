# Рефлексия флота — сводка

Записей: 22; период: 2026-11-20T03:42:16Z … 2026-11-20T06:16:07Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 5 | 0 | 15 | 0.00 | 0.00 | 0 | — | — | — |

## Трения (повторы сверху)

- **tool-train.py** — 3× (1 инст.)
  - 2026-11-20T04:26:41Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First health invocation passed unsupported --sign and exited 2; reran with the documented single-repository form.
  - 2026-11-20T05:29:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First covered invocation omitted its required SHA and exited 2 with usage; retried with the current main SHA.
  - 2026-11-20T06:11:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First health invocation used an unsupported --sign argument (exit 2); reran both required health checks with the documented repository-only syntax.
- **env-go** — 1× (1 инст.)
  - 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первая локальная govulncheck на Go 1.26.6 выявила GO-2026-6604 в стандартной библиотеке, тогда как CI использует Go 1.26.11; повтор с GOTOOLCHAIN=go1.26.11 подтвердил отсутствие вызываемых уязвимостей.
- **env-opencode** — 1× (1 инст.)
  - 2026-11-20T05:05:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Read output truncated LUNOBOT.md at lines 355 and 764; used continuation reads through line 834, then round.md continuation at line 381.
- **push-race** — 1× (1 инст.)
  - 2026-11-20T05:29:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting push was rejected once because origin/main advanced; pull --rebase and retry succeeded.
- **read-instruction** — 1× (1 инст.)
  - 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode Read усёк ядро на строках 355/764 и round.md на 380; до EOF понадобилось 3 чтения ядра и 2 round. Повтор описан в PR #330; следующий срез ждёт независимого review.
- **tool-git** — 1× (1 инст.)
  - 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `git switch --track` на PR-ветку дважды завершился ошибкой после подготовки index/worktree с содержимым ветки; сохранил состояние и создал локальную ветку непосредственно от проверенного SHA.
- **tool-git-pull** — 1× (1 инст.)
  - 2026-11-20T05:05:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): After taking f4#2297, the persistent accounting clone could not update a stale claim ref because origin/claims/f4/unxed-f4-2297 conflicts with the new /part-2 ref; left it untouched and used a fresh step clone for status pushes.
- **tool-pull** — 1× (1 инст.)
  - 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Обязательный pull постоянного accounting clone отказал из-за уже изменённого HEALTH.md; изменение сохранено, работа продолжена из чистого клона; новый коммит запушен после одного rebase из-за гонки main.

## Идеи

- 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Для длинных обязательных файлов задавать Read limit=2000 сразу; продолжать offset только при фактическом усечении.
- 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): После независимого review #330 — продолжать только непересекающийся срез по принятому плану.
- 2026-11-20T03:56:58Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Для PR с уязвимостью зависимости проверять govulncheck на версии Go из CI, а не только на локальном системном Go.
- 2026-11-20T04:26:41Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Continue #2297 by exposing per-history-ID toggles in settings and wiring the provider at bootstrap.
- 2026-11-20T05:29:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Pass the SHA explicitly to train.py covered; retry an accounting push after pull --rebase when origin advances.

Захватов снято: 4, медиана удержания 4 мин, дольше 2 ч: 0.
