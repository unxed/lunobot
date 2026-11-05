# Рефлексия флота — сводка

Записей: 48; период: 2026-11-05T05:05:18Z … 2026-11-05T06:34:26Z.
Генерирует `journal.py digest` (Лунобот-1, § 4 п. 6). Правила разбора — модуль round, «Рефлексия».

## Круги по раннерам и моделям

| раннер | модель | кругов | по сроку | медиана, мин | $ всего | $ медиана | с результатом |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lunobot-round-claude.sh | sonnet | 3 | 0 | 22 | 6.76 | 1.99 | 1 |
| lunobot-round-luna-high.sh | openai/gpt-6-luna#high | 2 | 1 | 26 | 0.00 | 0.00 | 0 |

## Неудачные круги (код ≠ 0, по сроку, лимит) — последние слова

- 2026-11-05T06:12:31Z lunobot-round-luna-high.sh круг 27, код 124:
  > ▶ shell
  > ▶ read
  > ▶ shell
  > ▶ shell
  > Error: {"type": "unknown", "message": "Transport: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()"}

## Трения (повторы сверху)

- **read-instruction** — 3× (1 инст.)
  - 2026-11-05T05:25:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): промпт круга старый (без «ПЕРВОЕ ДЕЙСТВИЕ … allow_large»): первый cat LUNOBOT.md ушёл в persisted-output, ядро и 8 модулей читал последовательно ~10 вызовов до первого действия
  - 2026-11-05T05:45:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Чтение ядра (557+260 строк в два Read из-за лимита 25k токенов страницы) и модулей round, manager, env-claude-code, trains, writing, releases, cleanup — ~350 КБ, ~14 минут из 30 до первого захвата; воркера не запускал: окно «срок − 20 минут
  - 2026-11-05T06:06:15Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): чтение ядра + round + manager + trains + env-claude-code + releases + cleanup заняло ~6 минут из 30 до первого захвата (06:03 против старта 06:00); форк воркера унаследовал контекст и не перечитывал инструкцию.
- **gate-false-positive** — 2× (1 инст.)
  - 2026-11-05T05:25:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): TRIAGE держит unxed/f4#2231 как «ждёт ответа», хотя автор в теле запретил боту трогать, а мы ничего не спрашивали; я написал жалобу unxed/lunobot#302 на непроверенном состоянии — фактов не сверил с тикетом (0 комментариев), review воркера п
  - 2026-11-05T05:45:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): gh_post.py check отклонил двуязычный (EN+RU, как требует п. 2а) текст закрытия с подписью «Lunobot» (кириллицы ≥ трети): пришлось подписать кириллицей на английском тикете; идея: для текста п. 2а в модуле round прямо указать кириллическую п
- **idle** — 1× (1 инст.)
  - 2026-11-05T05:25:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): потолок 1 воркер: review жалоб (unxed/lunobot#300 висит с 01:53 без комментариев) и land упираются в один слот, воркер получает review только после f4#2124
- **rule-unclear-§7.7** — 1× (1 инст.)
  - 2026-11-05T06:06:15Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py печатает «кандидат на релиз» без проверки критерия стабильного среза (открытые bug p1–2 после тега); пришлось проверять руками TRIAGE и gh issue view (2 тикета, ~2 мин)
- **tool-claims** — 1× (1 инст.)
  - 2026-11-05T05:45:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): claims.py take на кастомную задачу с тремя URL тикетов создаёт три ключа, drop по одному ключу снимает один: понадобилось три drop (unxed-f4-2155/2158/2160)
- **tool-claims.py** — 1× (1 инст.)
  - 2026-11-05T05:26:32Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First claim attempt for f4#1931 lacked required [land] route and was rejected; corrected immediately, no work began before successful claim.
- **tool-train.py** — 1× (1 инст.)
  - 2026-11-05T05:26:32Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): First retrospective health call used unsupported --sign and exited 2; corrected to `train.py health <owner/repo>`, then both f4/vtui returned.

## Идеи

- 2026-11-05T05:25:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): раннер на узле обновить вручную (cp во временный файл + mv): без этого любая правка промпта круга не доезжает
- 2026-11-05T05:25:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): check_prs.py/пульс: помечать PR жалоб без review старше суток в начале круга
- 2026-11-05T05:26:32Z Лунобот-2 (node 19d368003c6c048e43dbec70; LNX): Use a route-suffixed claims template for ticket selection; command examples for health should omit --sign.
- 2026-11-05T05:45:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): Двуязычный шаблон закрытия п. 2а с готовой кириллической подписью в modules/round.md или в close_candidates.py (вывод готового файла)
- 2026-11-05T05:45:22Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): claims.py drop с подстрокой 'ключ1,ключ2' или --all по тексту пачки
- 2026-11-05T06:06:15Z Лунобот-1 (node 19d368003c6c048e43dbec70; LNX): release_due.py: добавить колонку «блокируют срез: открытые bug p1–2 после тега» из TRIAGE.md + labels

Захватов снято: 19, медиана удержания 2 мин, дольше 2 ч: 0.
