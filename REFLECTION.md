# Рефлексия флота — сводка

Записей: 19; период: 2026-11-17T16:14:54Z … 2026-11-17T17:39:34Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 3 | 0 | 11 | 0.00 | 0.00 | 0 | — | — | — |

## Трения (повторы сверху)

- **read-instruction** — 5× (1 инст.)
  - 2026-11-17T16:44:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Read returned LUNOBOT.md only through lines 355 and 764, and round.md through 380; completed all mandatory files using continuation reads before work.
  - 2026-11-17T17:10:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode Read truncated the core and round module outputs; completed the required sections with continuation reads before actions.
  - 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode output truncated LUNOBOT.md at 355/764 and round.md at 380; three offset reads were needed to finish mandatory reading. Digest counted 4 prior events; added this recurrence to open PR #330.
- **env-accounting** — 2× (1 инст.)
  - 2026-11-17T16:44:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Persistent accounting checkout was on complaint/claims-stale-tracking-refs, so its HEALTH.md showed a stale alarm; verified queue and HEALTH from a fresh main clone before choosing work.
  - 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Persistent accounting checkout was on complaint/claims-stale-tracking-refs; git pull succeeded on that branch, so used a fresh main clone for authoritative queue and writes.
- **gate-false-positive** — 1× (1 инст.)
  - 2026-11-17T16:44:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): fix-it-in-wine check_triage hit GitHub API HTTP 403 rate limit once; one later run passed with 2 open tickets and matching TRIAGE.
- **rule-unclear-§4** — 1× (1 инст.)
  - 2026-11-17T16:17:21Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The persistent accounting checkout was on complaint/claims-stale-tracking-refs, not main; its HEALTH.md showed a stale friction alarm. Confirmed current queue and HEALTH.md from a separate clean main clone before finalizing the round.
- **token-cost** — 1× (1 инст.)
  - 2026-11-17T16:14:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The required journal read emitted 394 structured entries and was truncated in the tool preview; used the full returned evidence and the generated digest instead of repeating the read.
- **tool-claims.py** — 1× (1 инст.)
  - 2026-11-17T16:44:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First claims invocation ran from /home/ivan and failed to locate tools/claims.py; reran via absolute path and obtained the required claim before editing.
- **tool-gh** — 1× (1 инст.)
  - 2026-11-17T17:10:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): One read-only `gh issue view` request combined mutually exclusive `--comments` and `--json`; GH rejected it without side effects.
- **tool-test** — 1× (1 инст.)
  - 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Local bare-origin reproduction needed retries after branch-name collision, tracked-worktree pull rejection, and invalid loose-ref checks; final plumbing-based test passed both directions and preserved remote branch and untracked keep.txt.
- **tool-train.py** — 1× (1 инст.)
  - 2026-11-17T17:10:20Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all's vtui compare request returned HTTP 500 after f4 completed; reran tick-all from a clean accounting clone.

## Идеи

- 2026-11-17T16:14:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep the existing PR #330 as the mechanism fix; the same root cause has now recurred again and was added to that PR for owner visibility.
- 2026-11-17T16:17:21Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): At round start, verify the accounting checkout is on main before reading OWNER_QUEUE.md or HEALTH.md; use a fresh disposable clone if the primary checkout is on a task branch.
- 2026-11-17T16:44:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Check that the accounting clone is on main before treating OWNER_QUEUE.md or HEALTH.md as authoritative.
- 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep PR #330 as the mechanism fix; after review, verify whether shorter instructions reduce continuation reads.
- 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Before reading OWNER_QUEUE/HEALTH, verify persistent accounting checkout branch is main; use a fresh isolated clone if not.
- 2026-11-17T17:39:34Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Use git for-each-ref rather than inspecting loose ref paths in bare-origin tests.

Захватов снято: 5, медиана удержания 3 мин, дольше 2 ч: 0.
