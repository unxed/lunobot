# Рефлексия флота — сводка

Записей: 58; период: 2026-11-05T06:39:54Z … 2026-11-05T08:21:29Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-claude.sh | sonnet | 3 | 0 | 22 | 10.36 | 3.10 | 0 |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 4 | 1 | 25 | 0.00 | 0.00 | 1 |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-05T06:43:41Z lunobot-round-luna-high.sh круг 27, код 124:
  > ▶ shell
  > ▶ shell
  > ▶ subagent
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-05T08:18:39Z lunobot-round-luna-high.sh круг 29, код 1:
  > ▶ shell
  > ▶ shell
  > Круг 29 завершён: шаг по f4#2124 запаркован в ветке vtui `tmp/19d3/f4-2124-wheel-20261105` (SHA `3df52c2`), песочница ещё идёт; закрытый #2208 удалён из TRIAGE, гейт прошёл. Ретро записано в журнал.
  >
  > PR-жалоба [#303](https://github.com/unxed/lunobot/pull/303) запушена, но оставлена незавершённой: не привязан issue и проверка охватила 8 из 15 проектов. `main` не продвинулся; захваты снимет раннер.

## Трения (повторы сверху)

- **gate-false-positive** — 3× (2 инст.)
  - 2026-11-05T07:26:40Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tv3-new PR вливались по зелёным linux+verdict без tv3-audit в песочнице (#47–#70), хотя паспорт требует песочницу; воркер запустил аудит для #71 — расхождение практики и паспорта
  - 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_try.py назвал «Пробуйте!» по unxed/dn#177 преждевременным: в режиме PR тикет в описании PR, а не в сообщении merge-коммита afd917b; исправлено жалобой unxed/lunobot#303 (на реальных данных: 1 ложная строка → 0)
  - 2026-11-05T08:17:27Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): check_try.py flagged dn#177 despite merged PR unxed/dn#188 body containing Touch: unxed/dn#177; merge commit afd917b lacks that ticket in its message. Complaint PR: https://github.com/unxed/lunobot/pull/303.
- **read-instruction** — 3× (1 инст.)
  - 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро (2 Read) + round/manager/trains/env-claude-code, затем releases/cleanup: до первого захвата прошло ~6 мин круга из 30
  - 2026-11-05T07:26:40Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро (809 строк, 2 Read) + round/manager/env-claude-code/trains/cleanup/releases (~190 КБ) прочитаны за ~5 минут из 30; round и manager дублируют друг друга
  - 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Ядро (~31k токенов в двух Read) + round, manager, env-claude-code, trains, merge, writing, cleanup, releases: около 9 минут из 30 до первого захвата (07:52 → 07:56 захват, воркер в 07:57)
- **tool-train.py** — 2× (2 инст.)
  - 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): train.py health <repo> --sign ... печатает «укажите ровно один репозиторий» и выходит с кодом 0 — вводит в заблуждение, потеряна 1 команда
  - 2026-11-05T07:33:24Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый вызов health завершился exit 2 из-за лишнего --sign; повтор с точной сигнатурой дал результат f4 healing.
- **duplicate-work** — 1× (1 инст.)
  - 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): мои until-циклы с pgrep -f совпадали с собственной bash-командой и давали ложное «tick-all идёт» ~10 минут
- **env-claude-code** — 1× (1 инст.)
  - 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в круге раннера потолок воркеров 1, а шаги account-240 (cleanroom) сами требуют вложенного исполнителя; правило не говорит, считается ли он воркером потолка
- **env-opencode** — 1× (1 инст.)
  - 2026-11-05T08:17:27Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Shared /tmp/lunobot-2/f4 clone had extensive pre-existing edits; left untouched and delegated through an isolated step clone.
- **rule-unclear-§5** — 1× (1 инст.)
  - 2026-11-05T07:26:40Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): свободные блоки OWNER_QUEUE (216/240/280) идут раньше обычной работы, но в круге на 30 минут с одним воркером взять блок целиком нереально; взяты сначала созревший CI.md и откат staging — трактовка
- **tool-acct_line** — 1× (1 инст.)
  - 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): первый acct_line.py remove projects/dn/CI.md ответил «нет в origin/main» (код 2) при существующем файле, повтор через минуту прошёл — вероятно гонка с пушем janitor
- **tool-acct_line.py** — 1× (1 инст.)
  - 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): acct_line.py не принимает --sign с суффиксом воркера (dn#188): запись CI.md/BRANCHES.md подписана id без суффикса, расхождение со status

## Идеи

- 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py: печатать, сколько суток кандидат голодает, и сразу проверять блокирующие p1–2 bug (иначе релиз берут и тут же откладывают, как f4 v0.5.0-beta)
- 2026-11-05T06:55:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): train.py health: код 2 при лишних аргументах; acct_line.py: принимать суффикс воркера в --sign
- 2026-11-05T07:26:40Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick мог бы сам возвращать тикет в свободен при Staging-Revert (сейчас руками, f4#2153)
- 2026-11-05T07:26:40Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в кругах раннера на 30 минут блоки OWNER_QUEUE нужно дробить заранее в status/ на шаги в 10–15 минут
- 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_try: брать PR по commits/<sha>/pulls — сделано в unxed/lunobot#303, нужен review
- 2026-11-05T08:07:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в модуле manager явно сказать, что изолированный исполнитель cleanroom не входит в потолок (б) круга раннера
- 2026-11-05T08:17:27Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Teach check_try.py to resolve ticket association from the exact merged PR body/head commit when a merge commit message lacks Touch; preserve detection of foreign SHA.

Захватов снято: 20, медиана удержания 2 мин, дольше 2 ч: 0.
