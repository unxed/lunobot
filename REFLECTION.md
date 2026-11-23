# Рефлексия флота — сводка

Записей: 35; период: 2026-11-23T13:11:08Z … 2026-11-23T18:00:58Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 10 | 1 | 16 | 0.00 | 0.00 | 0 | — | — | — |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-23T17:53:41Z lunobot-round-luna-high.sh круг 571, код 124:
  > ▶ read
  > ▶ read
  > ▶ read
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}

## Трения (повторы сверху)

- **read-instruction** — 3× (1 инст.)
  - 2026-11-23T13:51:45Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode truncated LUNOBOT.md at lines 357 and 768 and round.md at line 388; full reading required 3 core and 2 round reads before action.
  - 2026-11-23T14:20:02Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initially claimed f4#2228 before checking its issue body; body explicitly forbids bot work. Dropped claim after identifying prohibition; no repository changes were made.
  - 2026-11-23T16:44:55Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode Read has no allow_large and capped/truncated output before EOF; core (839 lines) and round module (545 lines) required continuation reads.
- **tool-gh** — 3× (1 инст.)
  - 2026-11-23T13:51:45Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Search count API returned HTTP 403 rate limit after 14 sequential project counts at 13:41 UTC; remaining counts succeeded at 13:46, and all 18 paginated counts matched.
  - 2026-11-23T15:27:16Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `gh issue view --comments --json` rejected the combined flags; used the REST issue and comments endpoints instead.
  - 2026-11-23T17:07:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): One gh issue view invocation failed because --comments and --json are mutually exclusive; no remote side effect.
- **env-opencode** — 2× (1 инст.)
  - 2026-11-23T13:51:45Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The persistent f4 clone contained extensive pre-existing edits, so the step used a fresh work clone instead of risking that tree.
  - 2026-11-23T16:44:55Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): No DISPLAY, Wine, or xdotool in this runner, so the first unclaimed dllmgr probes requiring stand reproduction could not be safely started.
- **deadline** — 1× (1 инст.)
  - 2026-11-23T17:07:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Runner persistence deadline passed before tick-all completion was available; no new code step was started or safely parked.
- **push-race** — 1× (1 инст.)
  - 2026-11-23T16:13:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Учётный push main был отклонён (remote продвинулся с 84b57c5e7); один pull --rebase и повторный push прошли, итоговый main 7ad4e9301b1d3aa0cbea8e101bca201f3789c6dd.
- **tool-git** — 1× (1 инст.)
  - 2026-11-23T15:27:16Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting pull --rebase refused the local triage_touch change; stashed that named file, rebased, restored it, then committed and pushed.
- **tool-git-pull** — 1× (1 инст.)
  - 2026-11-23T13:11:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Pull --rebase persistent accounting clone отказал из-за прежнего unstaged TRIAGE.md; изменение сохранено, работа продолжена из чистого клона. Повторная проблема уже отражена в unxed/lunobot#340 / PR #342 и уведомление владельца существует.
- **wrong-trace-scenario** — 1× (1 инст.)
  - 2026-11-23T14:56:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Задание message-trace запустило edge сценарии вместо top-thumbnail; обе трассировки завершились exit 143, поэтому потребовалось повторно отделить подтверждённые данные от вопроса wheel delivery. Следующий прогон должен быть top-only и огран

## Идеи

- 2026-11-23T13:11:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Для учётной работы продолжать использовать чистый изолированный clone при наличии сторонних изменений в постоянном clone; не создавать повторное уведомление по уже открытому вопросу.
- 2026-11-23T13:51:45Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): If GitHub Search rate limits recur during otherwise-required parallel gates/snapshots, pace count requests and API-heavy batches; this round recovered on retry, so no mechanism change was made.
- 2026-11-23T14:56:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): В GUI workflow привязать профиль трассировки к сценарию явно и завершать задачу диагностическим отказом, если запрошен top wheel trace, а выбран edge plan.
- 2026-11-23T15:27:16Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Prefer `gh api repos/<owner>/<repo>/issues/<N>` plus the comments endpoint when both issue metadata and comments are needed.
- 2026-11-23T16:13:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Для медленного GUI под Wine +message сначала запускать ограниченный сценарий с одним wheel input; полный top сценарий под message trace не дошёл до события колеса за 600 guest seconds.
- 2026-11-23T16:44:55Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Provide a runner-compatible GUI/Wine stand for tasks whose first acceptance step requires interactive reproduction.

Захватов снято: 6, медиана удержания 4 мин, дольше 2 ч: 0.
