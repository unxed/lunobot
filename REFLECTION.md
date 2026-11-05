# Рефлексия флота — сводка

Записей: 45; период: 2026-11-05T17:14:37Z … 2026-11-05T18:53:13Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом | вызовов, медиана | контекст макс., тыс., медиана | субагентов |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-claude.sh | sonnet | 4 | 0 | 8 | 4.55 | 1.01 | 1 | 31 | 173 | 0 |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 3 | 0 | 14 | 0.00 | 0.00 | 0 | — | — | — |

## Трения (повторы сверху)

- **read-instruction** — 5× (2 инст.)
  - 2026-11-05T17:41:12Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро + round/trains/env-claude-code + writing/merge прочитаны за 3 ответа; writing и merge (~460 строк) нужны были только ради одного комментария и проверки PR
  - 2026-11-05T18:10:03Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро 830 строк + round/trains/env + позже trains-land/sandbox/cleanup/releases — модули под шаг и ретро читались отдельными ходами, ~6 ходов чтения за круг
  - 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): чтение ядра (98 КБ) и модулей round, trains, env-claude-code, merge, writing, releases заняло три ответа до первого захвата; merge/writing нужны были уже на выбранном шаге, но читал их целиком отдельным ответом после захвата
- **deadline** — 4× (2 инст.)
  - 2026-11-05T17:41:12Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): 30-минутный срок: к 17:52 осталось ~12 мин, а части 2 unxed/dn#179 нужен ещё tve/dn-клон и CI — кода не успел, только разбор
  - 2026-11-05T17:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Inspected f4#2233 (depends on vtui renderer) and f4#2247 (workspace restoration follow-up); neither had a safely bounded implementation step selected before the persistence deadline.
  - 2026-11-05T18:10:03Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release f4 (90 Touch:, 15 суток) — кандидат, но стабильный срез + заметки по 90 тикетам не помещаются в остаток круга после шага; нужен отдельный круг под релиз с захватом в начале
- **duplicate-work** — 3× (1 инст.)
  - 2026-11-05T17:24:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): At 17:14 check_triage bp reported stale #181/#185, but a concurrent L1 update reconciled them before the 17:21 touch; no duplicate edit was made and the batch claim was dropped.
  - 2026-11-05T18:21:25Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): I started an identical local change before inspecting status/2253.md; the push to the existing parked branch was rejected. I resumed the existing SHA; no duplicate code was pushed.
  - 2026-11-05T18:30:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Started a local duplicate before reading status/2253.md; a colliding push was rejected. Resumed the existing parked SHA, with no duplicate remote code push.
- **ci-gap** — 1× (1 инст.)
  - 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): тест unxed/dn#190 проверялся узким dn.yml (зелёный), а dn-linux-clip.py идёт только в PR-матрице dn-linux: ошибка в тесте (Ctrl+Z вместо Alt-BkSp) вскрылась после открытия PR, PR простоял красным ~1 ч 40 мин (16:52 → 18:28) до круга, взявше
- **env-opencode** — 1× (1 инст.)
  - 2026-11-05T17:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): The shared /tmp/lunobot-2/f4 clone contained extensive pre-existing modifications, so I left it untouched and cloned a clean work copy.
- **plan-gap** — 1× (1 инст.)
  - 2026-11-05T17:18:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): digest-отметка (journal.py add --kind digest) не была записана прошлым разбором, хотя жалоба #309 уже подана: тревога friction-repeats висела, пока отметки нет; разбор не считается законченным без неё
- **push-race** — 1× (1 инст.)
  - 2026-11-05T18:30:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): One accounting main push was rejected after a concurrent fleet commit; pull --rebase and retry pushed the triage update successfully.
- **release-starvation** — 1× (1 инст.)
  - 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4 — кандидат на релиз (15,3 сут с v0.4.0-beta, 90 коммитов с Touch:), но релиз не умещается в остаток круга (заметки по 90 коммитам, тег с тяжёлой матрицей непарковаем) — отложен второй круг подряд
- **token-cost** — 1× (1 инст.)
  - 2026-11-05T18:10:03Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): выбор работы: status_todo --all и TRIAGE дали ~40 свободных тикетов приоритета 5 без подсказки по размеру; пришлось читать 4 status-файла и 18 заголовков, чтобы найти малый атомарный шаг
- **tool-gh** — 1× (1 инст.)
  - 2026-11-05T17:18:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): gh issue view --comments --json несовместимы: потерян ход на повтор для unxed/bp#181 и unxed/bp#185 (используй --json comments без --comments)
- **tool-github-actions** — 1× (1 инст.)
  - 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): job linux64-utf8 в прогоне dn-linux 42068826091 завис в in_progress >90 мин со шагом failure; check-runs не завершён, поэтому статус PR выглядел «ещё идёт» — причину нашёл только через run_log.py по job'у
- **tool-python** — 1× (1 инст.)
  - 2026-11-05T17:24:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Two accounting-edit attempts failed on non-ASCII bytes literals / bytes-vs-str; corrected before commit, with no incorrect file change. One follow-up commit was needed to restore the required OWNER_QUEUE progress line.
- **tool-train.py** — 1× (1 инст.)
  - 2026-11-05T17:41:12Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick-all выдал nightly-оговорку шаблоном, но не сказал, что nightly (a64872d, 16:24Z) fix ещё не содержит из-за отмены прогона main; пришлось сверять release вручную (2 вызова gh)

## Идеи

- 2026-11-05T17:18:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py: выводить расхождение «последний тег» с паспортом (паспорт f4 отставал на версию)
- 2026-11-05T17:18:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в round.md разбор рефлексии: пункт 4 (digest-отметка) выделить как обязательный и в конце, а не после жалобы
- 2026-11-05T17:18:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): релиз с запуском workflow разбить на два шага: тег (круг N) и заметки (круг N+1, любой бот), чтобы вмещалось в круг раннера
- 2026-11-05T17:41:12Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick-all мог бы печатать, содержит ли текущий nightly влитый sha (release target vs поезд)
- 2026-11-05T17:41:12Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в status/N.md многочастных тикетов сразу писать, в каком подмодуле лежит код следующей части
- 2026-11-05T17:48:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Before claiming a task, verify that its implementation boundary is within the selected repository and can be safely parked within the round.
- 2026-11-05T18:10:03Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py мог бы печатать и признак голодания (порог выполнен 7+ суток назад), чтобы круг сразу брал релиз по правилу модуля releases
- 2026-11-05T18:10:03Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): status_todo.py --all с колонкой «последняя запись — когда, кем» упростил бы пропуск ждущих автора тикетов
- 2026-11-05T18:21:25Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): At ticket selection, read that ticket’s status file before taking the claim; status_todo.py --all exposes parked work but the step must be resumed at its recorded SHA.
- 2026-11-05T18:30:46Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Check status_todo/status files before claiming a TRIAGE-free ticket; serialize accounting main pushes and rebase on rejection.
- 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): скрипт release_notes.py: собирает «Новое/Исправления» из трейлеров Проблема:/Исправление: диапазона тег...main в файл, чтобы релиз f4/dn укладывался в круг
- 2026-11-05T18:34:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в dn.yml добавить dn-linux-clip.py (или PROJECT.md dn: гонять целевой тест узко через workflow_dispatch до PR), чтобы тесты вставки/буфера не падали уже в PR

Захватов снято: 14, медиана удержания 2 мин, дольше 2 ч: 0.
