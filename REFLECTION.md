# Рефлексия флота — сводка

Записей: 47; период: 2026-11-20T17:24:12Z … 2026-11-20T22:25:04Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 9 | 0 | 24 | 0.00 | 0.00 | 1 | — | — | — |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-20T20:31:12Z lunobot-round-luna-high.sh круг 435, код 1:
  > ▶ shell
  > ▶ task_complete
  > Круг завершён по шагу **unxed/f4#2311**: проверил кандидатов меню, опубликовал классификацию и запушил учёт (`5b0ef885e`). Рефлексия записана.
  > 
  > Ретро: staging f4 зелёный, поезд #2364 проходит матрицу; vtui без отставания от main. Уборку оставил на dry-run: удалений не делал из-за ограничения на деструктивные действия.

## Трения (повторы сверху)

- **env-opencode** — 3× (1 инст.)
  - 2026-11-20T20:29:56Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): rg is not installed in this environment; switched to grep for source searches.
  - 2026-11-20T21:42:19Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `rg` is absent in this environment; replaced the failed search with `grep`/Python and completed the inventory.
  - 2026-11-20T21:50:36Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `rg` is absent; used grep/Python for static inventory.
- **tool-check_try** — 3× (1 инст.)
  - 2026-11-20T19:56:29Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Foreground check_try превысил 120 с; background повтор завершился штатно: 92 тикета проверяют, пропусков 0.
  - 2026-11-20T20:29:56Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Combined f4 snapshot command reached the 120s foreground limit; check_try was rerun once in background and completed with 92 checking tickets, 0 missing try comments.
  - 2026-11-20T21:15:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The first #2304 comment missed the exact “— Пробуйте!” marker; check_try caught it, and the existing comment was corrected before release.
- **tool-gh** — 3× (1 инст.)
  - 2026-11-20T18:01:42Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Проверка комментариев потребовала отдельного gh issue view --json вызова после несовместимой комбинации --comments и --json; опубликованный комментарий затем сверил с тикетом.
  - 2026-11-20T21:42:19Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `gh issue view` rejected combining `--comments` and `--json`; one failed invocation, then used each mode separately.
  - 2026-11-20T21:50:36Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): One `gh issue view` invocation combined mutually exclusive `--comments` and `--json`; reran in supported modes.
- **read-instruction** — 2× (1 инст.)
  - 2026-11-20T18:01:42Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): LUNOBOT.md превышал один вывод инструмента и требовал нескольких offset-чтений, чтобы покрыть обязательные инструкции; все разделы дочитаны до начала работы.
  - 2026-11-20T22:17:01Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): OpenCode read cap required sequential continuation for LUNOBOT.md and round.md after initial output truncated; all files were completed before work.
- **tool-claims.py** — 2× (1 инст.)
  - 2026-11-20T21:42:19Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First `claims.py take` used a workspace-relative path and failed; absolute accounting path worked on retry.
  - 2026-11-20T21:50:36Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): One claim invocation used a path relative to /home/ivan and failed; absolute path succeeded on retry.
- **tool-train.py** — 2× (1 инст.)
  - 2026-11-20T19:11:38Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all printed unxed/vtui#2276 from the train PR's local Touch #2276, but the actual ticket is unxed/f4#2276; vtui issue lookup returned 404. Posted the comment to f4 and corrected its TRIAGE row.
  - 2026-11-20T22:17:01Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all completed after 2 projects; emitted 15 stale complaint-PR warnings, explicitly assigned to Lunobot-1 review; no Lunobot-2 action.
- **module-missed-§5** — 1× (1 инст.)
  - 2026-11-20T21:50:36Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial work selection preceded a complete sweep of every project CI.md; later snapshot exposed mature tv3#29 and zip#25 rows. zip#25 was merged; tv3#29 was safely parked pending its project audit.
- **route-selection** — 1× (1 инст.)
  - 2026-11-20T18:41:18Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Despite f4/PROJECT.md specifying trains, I opened routine PR #2363; its route guard failed in 4 seconds before the heavy matrix. Closed it, repushed the commit to the status-recorded tmp branch, and started the prescribed sandbox. Select th
- **tool-accounting** — 1× (1 инст.)
  - 2026-11-20T18:01:42Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый journal read использовал неверный формат даты YYYY-MM-DD вместо требуемого DD-MM-YYYY и завершился ошибкой; запись рефлексии выполняется корректно отдельной командой.
- **tool-check_try.py** — 1× (1 инст.)
  - 2026-11-20T18:41:18Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): check_try.py exceeded the 120-second foreground limit twice (once in a chained gate and once standalone); no result was available for f4. Use a background invocation and do not retry after an unknown timeout without checking process state.
- **tool-gh-clone** — 1× (1 инст.)
  - 2026-11-20T19:56:29Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): gh repo clone --depth=100 превысил 120 с и оборвался; неглубокий clone depth=10 пригодился для посадки уже запаркованной работы.
- **tool-git-pull** — 1× (1 инст.)
  - 2026-11-20T19:56:29Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Постоянный accounting clone не обновился: конфликт refs/claims/f4/unxed-f4-2304 с part-2; использован отдельный свежий clone, не удаляя refs вручную.
- **tool-tick-all** — 1× (1 инст.)
  - 2026-11-20T20:34:35Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initially invoked nonexistent tools/tick-all.py; corrected to train.py tick-all. No work step started before correcting.

## Идеи

- 2026-11-20T18:01:42Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Сразу использовать offset-чтение для больших инструкций и перед journal read проверить формат даты в --help/описании CLI.
- 2026-11-20T18:01:42Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Считать код из ответа gh_post.py авторитетным идентификатором опубликованного комментария; TRIAGE синхронизировать через triage_touch.py.
- 2026-11-20T18:41:18Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): For f4 train-mode work, land directly through train.py; use PR branches only for urgent work. Keep the viewer contract parked until sandbox succeeds, then land it.
- 2026-11-20T19:11:38Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Use Touch: unxed/f4#2276 for cross-repository work in vtui so train output routes the try comment to the actual issue.
- 2026-11-20T19:56:29Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): До исправления конфликтующих claim refs вести учёт через свежий одноразовый clone; PR #337 уже адресует причину.
- 2026-11-20T20:29:56Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Run API-heavy per-project checks in the background or split them before the 120s foreground limit.
- 2026-11-20T21:15:47Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Run check_try on every train-generated “Пробуйте!” comment before releasing the issue claim.
- 2026-11-20T21:42:19Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep using absolute paths for accounting tools; use `gh issue view --comments` or `--json`, not both.
- 2026-11-20T21:50:36Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Before choosing ordinary work, inspect every project CI.md and snapshot latest main/open PRs alongside triage gates.

Захватов снято: 10, медиана удержания 5 мин, дольше 2 ч: 0.
