# Рефлексия флота — сводка

Записей: 36; период: 2026-11-20T22:29:36Z … 2026-11-21T03:24:26Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 10 | 0 | 15 | 0.00 | 0.00 | 1 | — | — | — |

## Трения (повторы сверху)

- **read-instruction** — 3× (1 инст.)
  - 2026-11-20T23:02:09Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The 839-line core and 545-line round module exceeded Read output limits and required continuation calls; read module was truncated at line 388.
  - 2026-11-21T00:54:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode Read output truncated LUNOBOT.md at lines 357 and 768 and round.md at line 388; completed the required reads with continuation offsets (3 core reads, 2 round-module reads).
  - 2026-11-21T02:55:44Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Инструмент чтения обрезал LUNOBOT.md и round.md до заданного конца; полный текст покрыт 3 продолжениями ядра и 1 продолжением round.md.
- **env-opencode** — 1× (1 инст.)
  - 2026-11-20T23:27:53Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): В shell отсутствует rg; одну read-only выборку повторил через grep без влияния на файлы или результат.
- **push-race** — 1× (1 инст.)
  - 2026-11-20T23:02:09Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting main push was rejected once because remote advanced; pull --rebase succeeded without conflict and push completed.
- **rule-priority-§5** — 1× (1 инст.)
  - 2026-11-21T01:32:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OWNER_QUEUE still had free account-280; I selected f4 work instead. The owner task remains unclaimed and must be handled first next round.
- **tool-claims.py** — 1× (1 инст.)
  - 2026-11-20T23:02:09Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First drop attempt used a human-style issue key and failed; claims list exposed exact key f4/unxed-f4-2311, then drop succeeded.
- **tool-gh-api** — 1× (1 инст.)
  - 2026-11-20T23:59:55Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Concurrent checker fan-out plus sequential Search issue counts triggered HTTP 403 at 23:55:48 UTC; after checking rate_limit, sequential recounts succeeded and all project issue counts matched.
- **tool-pull** — 1× (1 инст.)
  - 2026-11-21T00:26:19Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Permanent accounting clone pull failed on conflicting remote-tracking claim refs (`.../unxed-f4-2311` vs `.../part-2`); used a fresh disposable clone and pushed status without pruning.
- **tool-sandbox** — 1× (1 инст.)
  - 2026-11-21T01:32:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Earlier status linked run 44843385364 to the newer parked SHA, but its headSha was cf31df; exact-SHA verification caught this before trusting the result.
- **tool-shell** — 1× (1 инст.)
  - 2026-11-21T02:30:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): В двух аргументах acct_line shell интерпретировал Markdown backticks как command substitution: ветка сначала попала в BRANCHES без имени, первая запись CI была отклонена гейтом. Исправлено; одна запись BRANCHES и CI затем успешно запушены б

## Идеи

- 2026-11-20T23:59:55Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Throttle shared GitHub Search count requests separately from parallel read-only gates to avoid exhausting the Search quota.
- 2026-11-21T00:54:40Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Consider a reader mode that returns the full long instruction without truncation; current OpenCode flow requires explicit continuation reads.
- 2026-11-21T01:32:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep menu tests selecting top-level groups by localized label rather than index.
- 2026-11-21T01:57:41Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Проверить гипотезу минимальным workflow_dispatch на windows-2022 перед восстановлением полноценной Windows VM.

Захватов снято: 4, медиана удержания 5 мин, дольше 2 ч: 0.
