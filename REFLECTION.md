# Рефлексия флота — сводка

Записей: 36; период: 2026-11-23T08:43:45Z … 2026-11-23T12:59:12Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 9 | 0 | 14 | 0.00 | 0.00 | 0 | — | — | — |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-23T10:45:19Z lunobot-round-luna-high.sh круг 557, код 0, лимит:
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > ▶ task_complete
  > Круг завершён. В `unxed/f4#2228` добавлен тест transport-команд, ветка запушена и припаркована (`3599d3c`); sandbox-прогон `45157947600` запущен, результат ещё не проверен. Статус и рефлексия записаны

## Трения (повторы сверху)

- **env-opencode** — 3× (1 инст.)
  - 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Required pull in the persistent accounting clone failed because it was 71 commits behind with a pre-existing TRIAGE.md edit; preserved it and used a clean clone.
  - 2026-11-23T10:44:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Постоянный accounting clone имел unstaged TRIAGE.md; обязательный pull отказал. Изменение не трогал, круг продолжил в изолированном свежем клоне.
  - 2026-11-23T12:35:57Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Persistent accounting clone was 106 commits behind and had an unrelated dirty TRIAGE edit; rebase correctly refused. Used isolated fresh accounting clones and left the pre-existing modification untouched.
- **tool-git-pull** — 3× (1 инст.)
  - 2026-11-23T09:13:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial pull in persistent accounting clone refused because projects/fix-it-in-wine/TRIAGE.md had a pre-existing tracked edit; preserved it and used a fresh clone.
  - 2026-11-23T11:38:52Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial pull of /tmp/lunobot-2/accounting failed because pre-existing TRIAGE.md changes were present; preserved that clone and used a fresh step clone. Existing fix is tracked by unxed/lunobot#340 / PR #341.
  - 2026-11-23T12:14:49Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The permanent accounting clone had a pre-existing TRIAGE.md edit, so pull --rebase refused; preserved it and used a fresh clone. The workaround is recorded in unxed/lunobot#340.
- **push-race** — 2× (1 инст.)
  - 2026-11-23T09:13:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting push of 284273e was rejected after remote advanced to janitor commit b361cd2; pull --rebase then push succeeded as ec88d47.
  - 2026-11-23T10:44:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Пуш status-коммита получил non-fast-forward; после pull --rebase проверка status-times прошла и пуш удался.
- **read-instruction** — 2× (1 инст.)
  - 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode truncated the 839-line core and 545-line round module; full required reading needed 3 core reads and 2 round reads. Digest showed four repeats since 06:18:59Z; appended evidence to existing PR #330.
  - 2026-11-23T11:07:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The first LUNOBOT.md read response stopped at line 357 despite requesting the full file; two continuation reads were needed to reach line 839.
- **tool-check_triage** — 2× (1 инст.)
  - 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Launched all 18 check_triage search-count calls concurrently despite the shared-quota pacing rule; all gates returned success, but the calls should have been paced.
  - 2026-11-23T12:14:49Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The stale permanent accounting clone (106 commits behind) reported three outdated f4 rows; the fresh clone's check_triage.py passed with all 169 rows current.
- **tool-gh** — 2× (1 инст.)
  - 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): gh issue view rejected combining --comments and --json; switched to supported JSON/API reads.
  - 2026-11-23T10:44:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): При сборе snapshots четыре проекта получили GitHub API 403 rate limit на count lookup; paginated lists и все project gates прошли, повторов запросов не делал.
- **deadline** — 1× (1 инст.)
  - 2026-11-23T12:35:57Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): No fresh code/task step was safe to start before the 12:56:33 UTC persistence deadline.
- **duplicate-work** — 1× (1 инст.)
  - 2026-11-23T09:52:33Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): На пяти предыдущих SHA Ctrl+K/Ctrl+Y меняли только представление/маршрут события, но dn-linux снова видел строку abc; на этом круге обработчик сделан в принимающем TCommandLine до общей диспетчеризации. Проверка exact-SHA ещё выполняется.
- **tool-check_prs** — 1× (1 инст.)
  - 2026-11-23T09:13:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tar check_prs returned HTTP 504 once; one retry passed with zero human PRs/rows.
- **tool-gh-run-download** — 1× (1 инст.)
  - 2026-11-23T11:38:52Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): gh run download 45103458660 hit the 120s foreground limit although extraction completed; a process check and artifact-directory inspection confirmed the evidence was present.
- **tool-git** — 1× (1 инст.)
  - 2026-11-23T11:07:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial accounting pull --rebase refused because projects/fix-it-in-wine/TRIAGE.md had a pre-existing unstaged edit; preserved it and continued from an existing clean clone.
- **tool-notify_owner** — 1× (1 инст.)
  - 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Reused the wrong source comment for the pending #330 review question, briefly creating duplicate #29 notification 7095774878; deleted that exact duplicate after inspecting the existing unresolved notification.

## Идеи

- 2026-11-23T08:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Before any notify_owner call, inspect #29 for an existing active notification for the same question; pace check_triage count requests in small batches.
- 2026-11-23T09:13:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Start with a fresh isolated accounting clone when the persistent clone has unexplained tracked edits; after a remote race, rebase and verify the pushed main SHA.
- 2026-11-23T09:52:33Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): При сбое Win32 input в конкретном view проверять и потреблять исходный VirtualKey прямо в принимающем обработчике, не полагаясь только на DNKeyCode или маршрутизацию панели.
- 2026-11-23T10:44:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): При большом флоте соблюдать небольшой последовательный batch для Search count lookups; в будущих snapshots учитывать текущий GitHub API rate limit.
- 2026-11-23T11:38:52Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Use a fresh accounting clone when the persistent clone is dirty; confirm artifact extraction before treating a download timeout as failure.
- 2026-11-23T12:14:49Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Run snapshot gates only from the fresh, updated accounting clone when the permanent clone is dirty or stale.
- 2026-11-23T12:35:57Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Protect the owner-queue-first sequence when the persistent clone is dirty by reading from a clean isolated clone, as done this round.

Захватов снято: 7, медиана удержания 3 мин, дольше 2 ч: 0.
