# Рефлексия флота — сводка

Записей: 370; период: 2026-11-04T00:56:02Z … 2026-11-04T20:08:10Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-claude.sh | sonnet | 31 | 0 | 15 | 54.90 | 1.94 | 12 |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 28 | 15 | 30 | 0.00 | 0.00 | 0 |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-04T13:18:42Z lunobot-round-luna-high.sh круг 11, код 124:
  > ▶ read
  > ▶ read
  > ▶ grep
  > ▶ read
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T13:49:55Z lunobot-round-luna-high.sh круг 11, код 124:
  > ▶ shell
  > ▶ shell
  > ▶ subagent
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T14:21:06Z lunobot-round-luna-high.sh круг 11, код 124:
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > Пачку триажа BP закрыли и проверили; тот же воркер сейчас разбирает уже запущенный Windows-прогон f4#2175. После его отчёта закончу ретро и запишу рефлексию.
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T15:06:21Z lunobot-round-luna-high.sh круг 12, код 124:
  > ▶ shell
  > ▶ subagent
  > ▶ read
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T17:11:27Z lunobot-round-luna-high.sh круг 15, код 124:
  > ▶ grep
  > ▶ shell
  > ▶ shell
  > ▶ subagent
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T18:22:02Z lunobot-round-luna-high.sh круг 16, код 124:
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > Триаж `bp#108` завершён и проверен. Поручение `account-216` пока упирается в недоступную интерактивную проверку, поэтому передаю тому же воркеру следующий исполнимый шаг свободного поручения `account-
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T20:04:48Z lunobot-round-claude.sh круг 28, код 1:
  > ▶ Bash {"command": "p=$$; while [ \"$p\" -gt 1 ]; do ps -o pid=,ppid=,etimes=,args= -p $p | cut -c1-150; p=$(ps -o ppid= -p $p | tr -d ' '); done; date -u", "descripti
  > ▶ Bash {"command": "mkdir -p /tmp/lunobot-1/work/r17-1104-2003 && cd /tmp/lunobot-1/work/r17-1104-2003 && gh repo clone unxed/lunobot accounting -- --depth=50 -q 2>&1
  > ▶ Bash {"command": "cd /tmp/lunobot-1/work/r17-1104-2003/accounting && ID=\"Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)\" && (python3 tools/train.py tick-all --sign
  > ▶ Bash {"command": "cd /tmp/lunobot-1/accounting && W=/tmp/lunobot-1/work/r17-1104-2003 && for p in f4 dn tv3 bp keytrans vtui goWidgets tar zipper zip xz mcommander o
  > You've hit your session limit · resets 9pm (UTC)
- 2026-11-04T20:05:19Z lunobot-round-luna-high.sh круг 18, код 124:
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-04T20:06:01Z lunobot-round-claude.sh круг 28, код 1:
  > You've hit your session limit · resets 9pm (UTC)
- 2026-11-04T20:07:14Z lunobot-round-claude.sh круг 28, код 1:
  > You've hit your session limit · resets 9pm (UTC)

## Трения (повторы сверху)

- **read-instruction** — 28× (2 инст.)
  - 2026-11-04T18:44:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Первый Read ядра без allow_large обрезан на 557/809 строках (подсказка про allow_large на строке 9 видна только в обрезанном ответе); итого 2 Read ядра + 4 параллельных модуля сразу, первый захват в 18:34 (~3.5 мин от старта) — лучше прежни
  - 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро (2 Read: первый без allow_large обрезан на 557 из 809 строк) и 8 модулей (round 69 КБ, manager 26, trains 38, env 27, writing 28, merge 39, cleanup 22, releases 12) = ~260 КБ чтения до 1-го захвата; merge/writing/cleanup/releases читал
  - 2026-11-04T19:43:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ядро + round + manager + env-claude-code + trains + trains-land + writing + complaints прочитаны целиком: около 9 минут из 30 до первого захвата
- **tool-train.py** — 11× (2 инст.)
  - 2026-11-04T18:18:05Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): tick-all завершился кодом 1: f4#2259 превысил порог задержки; отменённые macOS jobs имели runner_id=0, но причина отмен не установлена. Подтверждённого дефекта train.py нет, поэтому механизм не менялся.
  - 2026-11-04T18:44:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): второй tick-all через 8 мин перезапустил бисект f4 #2261 другой командой (windows вместо ubuntu): первый бисект на ubuntu не воспроизводил падение Race (windows/amd64) — в выводе нет причины перезапуска, приходится сопоставлять два лога
  - 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick-all (из одноразового клона, фон) шёл дольше 9 минут из 30 и в этот момент ещё не закончился; f4: 8 коммитов staging ждали main 4.3 ч, поезд #2264 отправлен только в этом тике, захват «застой main» держал Лунобот-2
- **duplicate-work** — 9× (1 инст.)
  - 2026-11-04T17:16:17Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4#2180: первая песочница прошлого круга гоняла ветку без отладочной строки; в этом круге отладочная строка в логе шага не видна (VTUI_DEBUG=stderr уходит в pty kit) — прогон 41869047527 дал вывод только через файлы проб T-02
  - 2026-11-04T18:44:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4#2262 и «застой main» f4 взял Лунобот-2 за 2–3 мин до меня; мой захват «красный поезд #2261» отклонён сервером (занято f4/stall-main) — гейт сработал как надо, потеря ~1 мин
  - 2026-11-04T19:43:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): припаркованный шаг unxed/f4#2262 пришёл с красной песочницей, которую Лунобот-2 не проверил: в нём было два независимых дефекта (lint-тест и golden), каждый стоил круга песочницы (~2 мин)
- **gate-false-positive** — 7× (1 инст.)
  - 2026-11-04T17:16:17Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): HEALTH.md держит friction-repeats, хотя разбор сделан в 15:03 UTC; Лунобот-2 в 17:10 взял захват «пульс: friction-repeats» на тот же повтор — ещё один ход на проверку журнала (digest 17:07 показал записи только с 15:03)
  - 2026-11-04T17:43:52Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): health для f4 даёт код 1 «ИНЦИДЕНТ ПРОЦЕССА» при поезде, у которого все проверки зелёные, кроме одной, 7 раз отменённой платформой; в сообщении нет причины (capacity macOS), приходится ходить в check-runs/annotations руками (~4 вызова).
  - 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в тесте goWidgets не учёл, что headless.Golden() накапливает журнал: первый CI fast был красным на моём же тесте (https://github.com/unxed/goWidgets/actions/runs/41894047229), +1 коммит; локально не запускал по правилу CI-only
- **env-opencode** — 6× (1 инст.)
  - 2026-11-04T16:08:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Accounting clone started 3 commits behind with unrelated dirty HEALTH/DISPATCH files; avoided overwriting them and used a fresh clone for tick-all and accounting writes.
  - 2026-11-04T17:36:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Предварительный accounting clone был позади origin/main на 16 коммитов и имел локальные изменённые HEALTH.md/DISPATCH.md; сохранил его без reset и использовал чистый клон круга.
  - 2026-11-04T18:18:05Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Основной клон учёта был грязным и отставал на 38 коммитов; учёт пришлось вести в отдельном свежем клоне, чтобы не затронуть посторонние изменения.
- **deadline** — 4× (1 инст.)
  - 2026-11-04T06:44:42Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): круг 30 минут не вмещает чтение инструкции и воркера: правило «воркер не позже срок−20» на практике запрещает воркера, если чтение заняло >10 минут
  - 2026-11-04T10:16:10Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): круг 30 минут: после тревоги пульса и review жалоб на релиз f4/dn (кандидаты по порогу (б)) и свободные тикеты слота не осталось — потолок воркеров 1 в круге раннера
  - 2026-11-04T16:09:08Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): новый воркер не запускался: к моменту, когда инцидент был разобран (16:09 UTC), до убийства 16:30 оставалось меньше 20 минут (правило «срок − 20»), поэтому ни одной кодовой задачи f4 в круге не взято, потолок воркеров 1 не использован
- **rule-unclear-§7.7** — 4× (1 инст.)
  - 2026-11-04T11:35:30Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): unxed/f4 (50 коммитов с Touch:, 14,1 сут от v0.4.0-beta) и unxed/dn (8 Touch:, 14,1 сут) — кандидаты на релиз по порогу (б); правило против голодания включится только через 7 сут, до этого релиз вытесняется блоками очереди в круге с одним в
  - 2026-11-04T13:21:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Против голодания релиз-кандидат получает слот раньше свободных блоков OWNER_QUEUE, но при потолке 1 и 14 суток без тега мне нужно решить, брать ли блок или релиз; релиз-порог (б) пройден 0,1 сут назад — не голодает, решение однозначное, но
  - 2026-11-04T14:10:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): порог релизов проверен только на ретро, после захвата account-216: правило голодания (§ 7.7) велит дать релизу f4/dn слот раньше свободных блоков OWNER_QUEUE, но release_due.py вызывается в ретро, а блоки берутся в начале круга; в круге с о
- **rule-unclear-§4** — 3× (2 инст.)
  - 2026-11-04T11:35:30Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): потолок воркеров 1 в круге раннера: review жалобы Лунобота-1 (§ 12, отдельный субагент), свободные блоки очереди и релизы делят один слот; жалоба unxed/lunobot#287 открыта с 07:55 UTC (3,7 ч к 11:35), её review пошёл только после освобожден
  - 2026-11-04T16:08:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Worker initially interpreted the queue claim key as missing; manager verified both claim lines and resumed the same worker session.
  - 2026-11-04T19:43:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): правило «шаги делает воркер» против «нового воркера не позже срок−20 мин»: код чинил сам (прямой фикс в 1 строку), воркера запустил только для review жалоб
- **tool-train** — 3× (1 инст.)
  - 2026-11-04T11:35:30Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick-all печатает предупреждение о жалобе старше 3 ч, но в § 5 review жалобы не имеет места в списке — выбор между ним и блоками очереди остаётся за толкованием
  - 2026-11-04T16:09:08Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): health печатает «ИНЦИДЕНТ ПРОЦЕССА» без причины; чтобы увидеть, что поезд стоит на нехватке macOS-раннера, понадобилось 6 вызовов gh api (jobs по попыткам, аннотации check-run), ~8 минут; исправляет PR unxed/lunobot#291 (только для tick, he
  - 2026-11-04T19:43:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): eject откат без Staging-Revert: два поезда подряд повезли выброшенный коммит (unxed/f4#2263, #2264); исправлено в unxed/lunobot#295
- **idle** — 2× (1 инст.)
  - 2026-11-04T02:19:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): потолок воркеров 1: после отчёта воркера в 02:19 до срока 02:33 оставалось 14 мин — релиз f4 и проверка 5 кандидатов close_candidates (f4#1255, f4#2068, dn#31, dn#80, bp#48) в слот не влезли; воркер ушёл по завершении, без ПЕРЕДАЙ
  - 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4 стоит кандидатом на релиз (61 Touch-коммит с v0.4.0-beta от 21-10, порог давно выполнен), а круг с одним воркером и 30 минутами не вмещает стабильный срез + тег: релиз f4 голодает
- **tool-claims** — 2× (1 инст.)
  - 2026-11-04T07:29:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): захват Лунобота-2 «красный main c95f70555» от 06:29 остаётся при зелёном main (run 41784306585) — сам снимет janitor
  - 2026-11-04T11:01:44Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): claims.py drop queue-account-280 после завершения воркера ответил «захват продлён или уже снят» — не ясно, снял ли воркер сам; release.py раннера добьёт
- **env-claude-code** — 1× (1 инст.)
  - 2026-11-04T07:29:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): api.github.com через прокси давал connection reset на check_try/check_prs/tick vtui; повтор помог, f4-гейты после повтора ушли в фон на 200 с
- **env-github-macos** — 1× (1 инст.)
  - 2026-11-04T17:43:52Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4 поезд #2259 стоит 3 ч: job Test (darwin/arm64 A-D) 6 раз подряд отменена ровно через 15 мин без раннера («The job was not acquired by Runner of type hosted even after multiple attempts», аннотация capacity constraints macOS arm64), на 7-
- **env-network** — 1× (1 инст.)
  - 2026-11-04T08:11:26Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): ECONNRESET на api.github.com/git ~08:00-08:09: оборвался review-субагент жалобы #287, упали release_due.py, клон для sweep.py, один claims.py take (с повтором прошёл); review не завершён, жалоба не влита
- **module-missed-§8.1** — 1× (1 инст.)
  - 2026-11-04T02:19:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): запустил sweep.py --apply в фоне до чтения modules/cleanup.md (таблица ядра требует читать перед sweep.py); вреда нет (0 удалено), но порядок нарушен: модули ретро (cleanup, releases) надо читать в начальном пакете Read
- **push-race** — 1× (1 инст.)
  - 2026-11-04T03:40:39Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Push of account-216 queue-state commit was rejected once because origin/main advanced; pull --rebase, queue gate passed, and push then succeeded (fee4059).
- **rule-unclear-§2** — 1× (1 инст.)
  - 2026-11-04T08:40:28Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): gh repo clone ... -- --depth=50 --no-upstream в § 2 падает (git clone не знает --no-upstream, это флаг gh) — одна лишняя попытка
- **rule-unclear-§5** — 1× (1 инст.)
  - 2026-11-04T12:41:28Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): блоки OWNER_QUEUE свободны (216, 240, 280), но все крупные, а срок круга 30 мин; взята тревога пульса вместо них — порядок «очередь раньше списка» vs срок не определён
- **rule-unclear-§7.2** — 1× (1 инст.)
  - 2026-11-04T09:43:29Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick отменил прогон main f4 после fast-forward, nightly (06:34) не содержит исправления f4#2234; образец «Пробуйте!» в tick.log обещает сборку после main — текст неверен при отменённом main
- **tool-bash-sleep** — 1× (1 инст.)
  - 2026-11-04T13:21:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Переднее ожидание блокируется средой; для удержания круга до прихода воркера пришлось держать фоновый until-цикл по часам
- **tool-check_prs** — 1× (1 инст.)
  - 2026-11-04T06:44:42Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_try/check_prs/close_candidates по f4 в параллельном запуске 9 проектов дали TLS handshake timeout (rc=2), пришлось перезапускать последовательно
- **tool-check_triage** — 1× (1 инст.)
  - 2026-11-04T01:09:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_triage.py dn: exit 2 «TLS handshake timeout», при повторе прошёл; f4 отставал на 14 тикетов
- **tool-claim-clone** — 1× (1 инст.)
  - 2026-11-04T09:43:29Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): `gh repo clone ... -- --no-upstream` из § 2 не работает (git exit 129); воркер использовал обычный клон — править формулировку § 2
- **tool-claims.py** — 1× (1 инст.)
  - 2026-11-04T16:08:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First queue-claim command lacked required “взял” state phrase and was rejected; corrected form claimed queue-account-216.
- **tool-close_candidates** — 1× (1 инст.)
  - 2026-11-04T18:07:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): close_candidates.py по f4 печатает ~100 строк «пропущен …» перед тремя кандидатами; все три кандидата оказались незавершёнными (status/ с остатком) — скрипт не учитывает status/<N>.md с «осталось»
- **tool-gh_post** — 1× (1 инст.)
  - 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): pr-body берёт файл целиком, а pr — первую строку как заголовок: при общем файле заголовок PR попал в тело, пришлось переотправить (+2 вызова); в writing.md нигде не сказано, что файл для pr-body — без строки-заголовка
- **tool-journal.py** — 1× (1 инст.)
  - 2026-11-04T01:09:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): digest показал 3 из 4 записей read-instruction, journal.py read --format json без ts/sign — воркер разбора обходил
- **tool-notify_owner.py** — 1× (1 инст.)
  - 2026-11-04T15:03:35Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Старая версия owner-question workflow трижды падала на импорте owner_questions из корня вместо tools/ (runs 41833870920, 41852574395, 41852610172); локальная проверка исправленного gate и проверочный run 41853557976 прошли.
- **tool-owner_questions.py** — 1× (1 инст.)
  - 2026-11-04T14:10:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): owner_questions.py sweep упал на сетевом сбросе соединения (RuntimeError без повтора), повторный вызов прошёл; ходил >120 с и ушёл в фон
- **tool-pwsh-sandbox** — 1× (1 инст.)
  - 2026-11-04T12:14:35Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): команда песочницы с test -z "$(gofmt ...)" на windows-latest падает «filename too long» (pwsh 7 берёт Git test.exe); f4#2175 потерял один прогон sandbox; в PROJECT.md f4 пример с test -z не помечен как bash-only
- **tool-release_due** — 1× (1 инст.)
  - 2026-11-04T02:19:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py пишет только «кандидат на релиз»: дату выполнения порога (б) пришлось считать руками тремя вызовами gh (20-й коммит с Touch после v0.4.0-beta — 22-10-2026, т.е. голодание 13 суток, порог голодания 7); f4 релиз не делался ни в
- **tool-status_todo** — 1× (1 инст.)
  - 2026-11-04T12:32:43Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): `status_todo.py --all` surfaced tv3#12 C1 as the next task although current status/12.md records C1 complete and identifies TvText TTextCells as next; one worker handoff had to be corrected.
- **tool-triage_touch** — 1× (1 инст.)
  - 2026-11-04T01:09:27Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): gh issue edit --add-label обновляет updatedAt: триаж-воркер прогонял triage_touch по 11 тикетам дважды (метки надо ставить до triage_touch)

## Идеи

- 2026-11-04T11:35:30Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): решить, берёт ли круг с потолком 1 релиз кандидата сразу по порогу (б) — иначе релизы f4/dn снова ждут 7 сут
- 2026-11-04T12:14:35Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в PROJECT.md f4 пометить, что test -z "$(gofmt…)" — только для linux/macOS; на Windows gofmt проверять через gofmt -l | findstr или пропускать
- 2026-11-04T12:14:35Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в trains.md п. 0/§ 7.5 явно написать: land не требует train.py covered, отказ land — только красный staging или заморозка
- 2026-11-04T12:32:43Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Make status_todo.py derive cleanroom next steps from the latest status entry, and make cleanroom tooling accept a caller-selected work directory rather than a fixed instance path.
- 2026-11-04T12:41:28Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): следующий шаг сжатия: round.md (69 КБ) — вынести приём OWNER_QUEUE и разбор рефлексии в отдельные модули
- 2026-11-04T12:41:28Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): замерить read-instruction в следующих разборах после #289
- 2026-11-04T13:21:13Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): В round.md п. 1 поставить release_due.py в снимок круга перед выбором блока очереди (иначе голодание релиза проверяется только на ретро, уже после взятия слота)
- 2026-11-04T14:10:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в круге раннера выполнять `release_due.py` в начале выбора работы (рядом с проверкой «активный Лунобот-1») и печатать кандидатов голодания, чтобы правило § 7.7 действовало до захвата блока очереди
- 2026-11-04T14:10:49Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): owner_questions.py: повтор api_json при сетевых ошибках (§ 1)
- 2026-11-04T14:44:35Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_dispatch/claims: отказывать [pr] для проекта с Режим публикации: поезда (Лунобот-2 взял [pr] в f4)
- 2026-11-04T14:44:35Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due: учитывать в разборе круга с одним воркером — выделять слот релизу, а не только блоку очереди
- 2026-11-04T15:03:35Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): После review/мержа PR #290 повторно проверять owner-question workflow на свежем main; механизмное сокращение ядра/round/trains остаётся открытым решением владельца.
- 2026-11-04T15:17:23Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_triage.py/triage-гейт: помечать тикеты, в теле которых есть «не трогать» от владельца, чтобы выбор по § 5 п. 5 их не предлагал
- 2026-11-04T15:17:23Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): § 7.5: при парковке коммит сразу делать в формате land (трейлеры Touch:/Lunobot-Task:/Проверить:) и ребейзить на staging перед песочницей
- 2026-11-04T15:39:25Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): close_candidates.py: исключать тикеты, у которых status/<N>.md содержит непустое «Осталось» после последней записи «приземлено»
- 2026-11-04T16:09:08Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): health тоже должен показывать причину застоя (аннотации отменённых job'ов поезда) и считать поезд, потерявший проверки только из-за capacity, «ожидание внешнее»; нужен отдельный сигнал владельцу, если macOS arm64 недоступен больше 2 часов (
- 2026-11-04T16:09:08Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): в круге раннера делать инцидентный диагноз воркером, а менеджерскую часть (гейты, tick-all) держать короткой, чтобы воркер успел стартовать до «срок − 20»
- 2026-11-04T16:45:21Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): pulse.py: не держать friction-repeats как тревогу, пока по этому трению в #29 открыт вопрос владельцу (эскалация уже сделана) — иначе каждый круг каждого бота перепроверяет одно и то же
- 2026-11-04T17:16:17Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): pulse.py: учитывать запись digest при оценке friction-repeats и не поднимать тревогу на трения, уже разобранные последним digest
- 2026-11-04T17:16:17Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): train.py health: печатать причину ожидания поезда (queued job + его раннер/лейбл) в строке ИНЦИДЕНТ ПРОЦЕССА
- 2026-11-04T17:36:03Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): В #291 уже зафиксировано улучшение диагностики причин ожидания macOS runner; решение по runner capacity остаётся владельцу.
- 2026-11-04T17:43:52Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): train.py health/tick: при отмене job с аннотацией «not acquired by Runner» печатать причину «платформенный дефицит раннеров <ОС>, попытка N» и считать N подряд таких отмен; после N≥3 — не «ИНЦИДЕНТ ПРОЦЕССА, чини конвейер», а отдельный стат
- 2026-11-04T17:43:52Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due: учитывать занятость потолка (а) (идущий поезд f4) и сразу писать «отложено до окончания поезда», чтобы ретро не читало releases.md ради вердикта «отложить».
- 2026-11-04T18:07:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): close_candidates.py: пропускать тикет, чей projects/<проект>/status/<N>.md содержит «Осталось/Дальше» без «приземлено» в последней записи; по умолчанию печатать только кандидатов
- 2026-11-04T18:18:05Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Повторно разбирать отмены macOS jobs только при появлении новых доказательств или воспроизводимого сбоя; не менять train.py по одному runner_id=0.
- 2026-11-04T18:44:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): train.py tick: при бисекте на ОС, отличной от упавшего job (ubuntu вместо windows), печатать почему выбрана эта ОС
- 2026-11-04T18:44:53Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py: показывать «отложено: поезд проекта в пути» чтобы ретро не читало releases.md ради вердикта (повтор идеи 17:43)
- 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): writing.md: дописать, что gh_post.py pr берёт заголовок из 1-й строки, а pr-body — файл целиком без заголовка
- 2026-11-04T19:11:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): round.md: на ретро Лунобота-1 в круге раннера пропускать release_due-кандидатов с голоданием в отдельный круг без другой работы или давать им слот сразу после гейтов
- 2026-11-04T19:43:09Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Добавить в промпт Лунобота-2 / модуль trains-land напоминание: golden-файл порядка действий (internal/app/testdata/action_order.golden) обновлять вместе с actionMenuOrder, а в тестах f4 использовать testutil.Rune сразу (оба правила уже част

Захватов снято: 102, медиана удержания 4 мин, дольше 2 ч: 0.
