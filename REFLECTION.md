# Рефлексия флота — сводка

Записей: 73; период: 2026-11-04T23:57:45Z … 2026-11-05T02:02:47Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-claude.sh | sonnet | 4 | 0 | 20 | 10.90 | 2.55 | 3 |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 4 | 3 | 30 | 0.00 | 0.00 | 0 |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-05T00:21:10Z lunobot-round-luna-high.sh круг 23, код 124:
  > ▶ read
  > ▶ shell
  > ▶ shell
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-05T01:28:56Z lunobot-round-luna-high.sh круг 24, код 124:
  > ▶ read
  > ▶ shell
  > ▶ read
  > ▶ read
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}
- 2026-11-05T02:00:12Z lunobot-round-luna-high.sh круг 24, код 124:
  > ▶ shell
  > ▶ read
  > ▶ shell
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}

## Трения (повторы сверху)

- **gate-false-positive** — 4× (1 инст.)
  - 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_prs.py печатает [ждёт ответа] для blue-panels/mcommander#451 (PR мейнтейнера ilia-maslakov; нашего ответа там никогда не было, у бота в upstream только pull) — строка не работа, но выглядит как работа § 5 п. 3
  - 2026-11-05T01:16:36Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): triage_touch.py bp 129/128 по одному: после каждой правки check_triage находил следующий тикет с обновлением владельца (комментарий-плана #108 сдвинул updatedAt у #128/#129); три коммита вместо одного.
  - 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_prs.py печатал [ждёт ответа] для blue-panels/mcommander#451, где у токена только READ; исправлено жалобой unxed/lunobot#300 (ждёт review отдельного субагента, автором была та же сессия)
- **read-instruction** — 4× (1 инст.)
  - 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Ядро (31 тыс. токенов) первым Read без allow_large обрезано на 557 из 809 строк — второй вызов; round+manager+trains+env-claude-code+writing+releases+cleanup+merge прочитаны целиком, на это ушло ~6 минут из 30 до первого захвата (00:34 → 00
  - 2026-11-05T01:16:36Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Ядро (809 строк) прочитано в два Read (лимит 25 тыс. токенов обрезал на 557 строке) + round/manager/trains/env-claude-code/cleanup/releases ≈ 340 КБ модулей; первый захват поставлен примерно на 7-й минуте круга.
  - 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Первый Read ядра без allow_large обрезал на 557 из 809 строк (лимит 25 тыс. токенов), второй Read добрал хвост; в промпте этого запуска раннера (старая копия скрипта) не было требования allow_large, хотя в runners/lunobot-round-claude.sh на
- **deadline** — 1× (1 инст.)
  - 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): релиз dn v2.20-alpha.3: тег запускает матрицу dn/dn-linux/dn-windows/release (>20 мин), а заметки (gh release edit) возможны только после создания релиза workflow — в круге раннера в 30 минут это шаг на два круга; пришлось парковать через s
- **env-opencode** — 1× (1 инст.)
  - 2026-11-05T00:42:28Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Worker report initially named a different parking ref than the authoritative status; reconciled by checking remote refs and full SHA. Follow-up code investigation did not establish root cause, so work remains parked with an explicit next st
- **idle** — 1× (1 инст.)
  - 2026-11-05T00:04:59Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Зелёный PR unxed/sandbox#7 стоял в CI.md с 18:06 (около 6 часов) без вливания; устаревшая строка main f4 от 21:11 висела около 3 часов — § 5 п. 3 в прошлых кругах не дошёл до этих строк
- **rule-unclear-§12** — 1× (1 инст.)
  - 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Воркер-fork влил #297 без захвата на review (поставил позже по моему повтору) — в промпте захват надо требовать ДО чтения; потолок воркеров 1 мешает review своей же жалобы #300 отдельным субагентом в круге
- **rule-unclear-§5** — 1× (1 инст.)
  - 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): unxed/bp#148 (PR бота lunobot/pr/…, часть 1 из 4) оставался открытым с красным windows 80 минут после того, как тот же фикс влит чужим PR unxed/bp#151 с ветки fix/146-findings; в CI.md строка висела, janitor/гейт «PR заменён» не ловит
- **rule-unclear-§7.2** — 1× (1 инст.)
  - 2026-11-05T01:48:14Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Prompt characterized train #2271 as a fix ready for ‘Пробуйте!’, but its sole commit only added internal/terminal/log_vfs_viewer_test.go; corrected the posted comment rather than claim a user-visible fix.
- **rule-unclear-§7.7** — 1× (1 инст.)
  - 2026-11-05T01:16:36Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Модуль releases запрещает двигать существующие теги без слова владельца, а status/166.md (мой же план прошлого круга) требовал удалить и переставить v2.20-alpha.3 без релиза; пришлось уточнять воркеру условия (нет релиза/черновика) и запасн
- **tool-check_try** — 1× (1 инст.)
  - 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): unxed/vtui#244 стоял `проверяют` без «Пробуйте!» около часа после влития поезда — tick поставил состояние, текст не разнесён (нет автоматического разноса)
- **tool-triage_touch** — 1× (1 инст.)
  - 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_triage находит расхождения по одному тикету за вызов triage_touch; идея: triage_touch --all, одним коммитом (не сделано, нет времени в круге)

## Идеи

- 2026-11-04T23:57:54Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Сохранить открытый вопрос в unxed/lunobot#216; новые записи оценивают чтение примерно в 3–4 минуты, но не устанавливают отдельный устранимый дефект механизма.
- 2026-11-05T00:04:59Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_prs.py: не печатать [ждёт ответа], если у бота нет ни одного комментария/отзыва в PR или у токена нет прав писать в репозиторий
- 2026-11-05T00:04:59Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): tick-all мог бы сам снимать строки main в CI.md, когда вершина main зелёная или её прогон отменён по cancelled_main_is_expected
- 2026-11-05T00:42:28Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Keep worker completion reports aligned with the authoritative status branch/ref and specify an executable next diagnostic when static inspection cannot establish the failure.
- 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_prs.py: не печатать [ждёт ответа] для PR, в который у бота нет прав и в котором мы не писали
- 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): janitor/check_ci.py: предупреждать о строке CI.md, где PR бота открыт, а тот же тикет/часть закрыта влитым другим PR
- 2026-11-05T00:44:56Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release.yml dn: брать заметки релиза из аннотации тега (--notes-from-tag), чтобы заметки писались до push тега, а не после workflow
- 2026-11-05T01:16:36Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_triage.py --fix-touch (или triage_touch.py без номера = все расхождения) одним коммитом
- 2026-11-05T01:16:36Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): f4 release_due: кандидат с порогом (б) ≥7 суток не получает слот при потолке воркеров 1 в круге раннера из-за поезда, идущего почти всегда; нужен явный критерий окна (поезд зелёный/не идёт) в модуле releases
- 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): runners/lunobot-round-claude.sh: раннер при старте круга брать скрипт из свежего main учёта, чтобы промпт с allow_large не отставал
- 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): triage_touch.py --all: обновить все расхождения check_triage одним коммитом
- 2026-11-05T01:58:05Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): review жалобы #300 — следующий круг (отдельный субагент, не автор)

Захватов снято: 23, медиана удержания 2 мин, дольше 2 ч: 0.
