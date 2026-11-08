# Рефлексия флота — сводка

Записей: 65; период: 2026-11-07T13:35:19Z … 2026-11-08T01:36:25Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 18 | 0 | 10 | 0.00 | 0.00 | 1 | — | — | — |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-07T19:59:39Z lunobot-round-luna-high.sh круг 86, код 1, лимит:
  > Error: {"type": "provider.quota", "message": "The usage limit has been reached", "response": {"body": "{\"type\":\"error\",\"error\":{\"type\":\"usage_limit_reached\",\"message\":\"The usage limit has
- 2026-11-07T21:41:32Z lunobot-round-luna-high.sh круг 88, код 1, лимит:
  > ▶ read
  > ▶ shell
  > ▶ read
  > ▶ shell
  > Error: {"type": "provider.quota", "message": "The usage limit has been reached", "response": {"body": "{\"type\":\"error\",\"error\":{\"type\":\"usage_limit_reached\",\"message\":\"The usage limit has

## Трения (повторы сверху)

- **read-instruction** — 4× (1 инст.)
  - 2026-11-07T17:36:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Ядро LUNOBOT.md (829 строк) и round.md (529 строк) пришлось дочитывать через offset после автоматической обрезки вывода; оба модуля обязательны целиком.
  - 2026-11-07T19:17:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): LUNOBOT.md (829 lines), round.md (529 lines), trains.md (284 lines), and env-opencode.md (47 lines) required sequential reads across 7 Read calls because OpenCode truncates large responses; all ranges completed.
  - 2026-11-07T19:42:23Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Read tool ограничил первое чтение ядра до строки 355; дочитал с offset 356 и 771, round.md — с offset 381 до последней строки, до любых действий.
- **env-opencode** — 3× (1 инст.)
  - 2026-11-07T13:42:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): В двух разных записях круга (11:47 и 13:11 UTC) shell command substitution из обратных кавычек повредил аргумент acct_line.py; открыл unxed/lunobot#325 и PR #326 с --text-file, regression test подтверждает буквальный текст.
  - 2026-11-07T16:39:15Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Path.read_text не принимает newline=; переход на Path.open(newline="") после одной неудачной попытки.
  - 2026-11-07T21:22:12Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Could not inspect BMPs with Read (binary) or PIL (not installed); used textual assertions/logs instead.
- **push-race** — 2× (1 инст.)
  - 2026-11-07T14:02:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting main advanced between local commit and push; rebased once and pushed.
  - 2026-11-07T17:58:21Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting push for status commit was rejected once because origin advanced; pull --rebase then check_status_times and push succeeded.
- **deadline** — 1× (1 инст.)
  - 2026-11-07T19:17:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Exact GUI/bootstrap checks remained in progress at last read; safely parked and recorded rather than waiting or claiming a result.
- **gate-false-positive** — 1× (1 инст.)
  - 2026-11-07T17:03:12Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): GUI workflow 42389350632 concluded success while top drivers in both 5.6 and 8.5 had 12 failed assertions; artifact inspection was needed to distinguish workflow status from product evidence.
- **tool-acct_line** — 1× (1 инст.)
  - 2026-11-07T15:11:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Командная строка съела backticks SHA как shell substitution; первая запись CI.md была удалена, add-гейт поймал пустой SHA, корректная запись добавлена через Python argv.
- **tool-gh** — 1× (1 инст.)
  - 2026-11-07T17:58:21Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): gh run list --branch returned an empty list immediately after workflow_dispatch; direct run view by returned run ID confirmed exact SHA and in_progress.
- **tool-gh_post.py** — 1× (1 инст.)
  - 2026-11-07T13:42:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый progress-комментарий отклонён из-за кириллической подписи к преимущественно английскому тексту; заменил подпись на латиницу, повторная отправка прошла.
- **tool-output** — 1× (1 инст.)
  - 2026-11-07T18:22:14Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Artifact review initially emitted hundreds of window-dump records; a filtered assertion-only summary was needed to isolate the 12 failures per version.
- **tool-owner_questions.py** — 1× (1 инст.)
  - 2026-11-07T14:46:27Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): owner_questions.py sweep оставил 7 записей; ручной разбор и возможные удаления не выполнены в этом круге.
- **tool-test** — 1× (1 инст.)
  - 2026-11-07T14:02:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Initial unittest invocation lacked PYTHONPATH=tools; corrected invocation passed 21 tests.
- **tool-train** — 1× (1 инст.)
  - 2026-11-07T15:11:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): train.py health отверг --sign (лишний аргумент); повторены health для f4 и vtui с корректным синтаксисом.
- **tool-train.py** — 1× (1 инст.)
  - 2026-11-07T16:39:15Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Первый health вызов был отвергнут из-за лишнего --sign; повторён корректной формой train.py health <owner/repo>.

## Идеи

- 2026-11-07T13:42:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Оставить --text-file на review; использовать его для acct_line.py вместо shell-аргументов, содержащих обратные кавычки.
- 2026-11-07T13:42:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Не повторять вопрос о сокращении инструкций в #216 без нового корня причины; проверить ответ владельца в следующем круге.
- 2026-11-07T14:02:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Document --text-file in acct_line.py help; positional API remains intact.
- 2026-11-07T14:46:27Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Перед ручной уборкой оставшихся уведомлений сначала приоритизировать и разобрать все 7 записей по модулю writing.
- 2026-11-07T15:11:08Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Для поиска дочернего ListView учитывать Unicode class name, а не только стандартный SysListView32.
- 2026-11-07T16:39:15Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Сверять CLI-параметры по фактическому --help и использовать Path.open для newline-preserving правок.
- 2026-11-07T17:03:12Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Ensure GUI workflow summaries make driver assertion failures conspicuous; do not infer GUI success from Actions conclusion alone.
- 2026-11-07T17:36:07Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): При ограничении вывода читать большие обязательные файлы заранее небольшими смежными диапазонами; среда OpenCode это предписывает.
- 2026-11-07T17:58:21Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Run view by workflow-dispatch run ID is more reliable than immediate branch-filtered gh run list.
- 2026-11-07T18:22:14Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): When reading GUI artifacts, extract assert/summary records first and inspect window dumps only for a specific failing assertion.
- 2026-11-07T21:22:12Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Provide a text-native artifact summary of assertion events and selected pixel statistics alongside GUI screenshots.

Захватов снято: 7, медиана удержания 1 мин, дольше 2 ч: 0.
