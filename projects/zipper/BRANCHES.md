# BRANCHES — zipper

Журнал намерений создания веток под lunobot/; записи сверяются с GitHub.

- lunobot/f32c3c2d37ce4d094461f67a/lunobot-3/18-readme-features-table -> PR #31 (issue #18, features comparison table in README) — открыт 27-09-2026.

## 2026-09-27 — ревизия всех удалённых веток (кроме main)

Полный список веток на момент ревизии (`gh api repos/unxed/zipper/branches --paginate`):
main, codex/update-dependency-versions, codex/zip-version-update. Все ветки
lunobot/* из истории (PR #27–#31) на момент ревизии уже смержены и отсутствуют в
списке (автоудаление GitHub при мердже) — ничего делать не потребовалось.

Проверены и удалены (объективно доказано отсутствие уникальной ценности):

- `codex/zip-version-update` (последний коммит d02b0e2, 2026-09-24 07:48 +0200) —
  правило 1: полностью слита в main. `git merge-base --is-ancestor
  origin/codex/zip-version-update origin/main` → true; `git log
  origin/main..origin/codex/zip-version-update` пуст. Соответствует смерженному
  PR #25 "Update zip to fixed coverage release" (mergedAt 2026-09-24T05:49:57Z).
  Удалена через `gh api -X DELETE git/refs/heads/codex/zip-version-update`.
- `codex/update-dependency-versions` (последний коммит 25d0abf, 2026-09-24
  09:27 +0200) — правило 2: привязана к закрытому (не смержённому) PR #26
  "deps: update archives and sevenzip pins" (closedAt 2026-09-24T07:33:36Z,
  mergedAt null). Владелец (unxed) сам закрыл PR с комментарием: "No changes
  remain after preserving the fork-compatible archives/sevenzip module pins;
  the dependency update is already represented by the validated zipper main
  commit." — т.е. тема объективно превзойдена main (diff показывает попытку
  ОТКАТИТЬ пины archives/sevenzip/tar/xz/zip на более старые версии; main уже
  содержит более новый набор пинов). Удалена через `gh api -X DELETE
  git/refs/heads/codex/update-dependency-versions`.

Ни одна из двух веток не содержала коммитов за 27-09-2026 (обе от 24-09), под
правило "не трогай активную работу последних часов" не попадали.

Открытых PR на момент ревизии: 0 (`gh pr list --state open` пуст). Веток с
номерами тикетов #21/#22 не найдено в репозитории zipper — подтверждено по факту:
эти тикеты реализуются в зависимом репозитории unxed/sevenzip (PR #7, #8), в
самом zipper для них веток нет ни старых, ни новых.

Итог: main — единственная ветка. Находок по правилу 3 (уникальные коммиты без
PR, тема не решена) не обнаружено.
