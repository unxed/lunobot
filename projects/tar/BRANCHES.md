# BRANCHES — tar

Журнал намерений создания веток под lunobot/; записи сверяются с GitHub.

27-09-2026 03:50:48 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), lunobot/4c1475919cf481f65b4f749a/lunobot-3/3-gzidx-parallel-decompress — tar#3, запушена в origin, открыт PR #13

27-09-2026 04:11:24 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), lunobot/19d368003c6c048e43dbec70/lunobot-3/2-deterministic-archiving — tar#2, запушена в origin, открыт PR #14

27-09-2026 (ревизия веток) Лунобот-3, полная ревизия удалённых веток unxed/tar (gh api repos/unxed/tar/branches --paginate + git ls-remote --heads): всего было 2 non-main ветки на момент старта — `codex/coverage-ci`. Остальные ветки (lunobot/.../2-deterministic-archiving, lunobot/.../3-gzidx-parallel-decompress, lunobot/.../codecov-oidc, lunobot/.../1178-tar-*, fix/flaky-zstd-pool-test, fix/windows-macos-tests, Zoinen:zoin-bot/f4-642-arch) уже были удалены GitHub автоматически после merge (delete-branch-on-merge включен в репо) — на момент ревизии их не существовало, трогать было нечего.
- `codex/coverage-ci` (PR #6 "ci: add coverage report", merged 2026-09-24): `git merge-base --is-ancestor origin/codex/coverage-ci origin/main` → true, `git log origin/main..origin/codex/coverage-ci` → пусто. Полностью слита, уникальных коммитов нет → удалена (`git push origin --delete codex/coverage-ci`).
Итог: репозиторий чист, после ревизии из non-main веток не осталось ни одной. Открытых PR с висящими ветками не найдено — PR #13 (tar#3) и #14 (tar#2), упомянутые в задаче как "открытые", на деле уже MERGED (оба слиты 2026-09-27 в ходе того же прохода), их ветки-головы GitHub удалил сам. tar#3 (issue) при этом остаётся OPEN в трекере несмотря на merged PR #13 — это вопрос состояния тикета/issue, не веток, вне рамок этой задачи, не трогал.
