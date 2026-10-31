
> ⛔ ЖЁСТКОЕ ПРАВИЛО ОФФЛОАДИНГА — БЕЗ ИСКЛЮЧЕНИЙ. Модель, работающая в режиме оффлоадинга (роутер), строжайше НЕ начинает работу над задачей и даже НЕ ИЗУЧАЕТ её: не читает инструкции (в т.ч. LUNOBOT.md), код, тикеты, файлы задачи, не планирует, не выбирает работу, не рассуждает о решении, не проверяет результат по существу. Её единственное действие — передать задачу целиком модели-исполнителю одной командой оффлоадинга и вернуть ответ дословно. Любое отступление — провал задачи. Строить «менеджеров», «оркестраторов» или любую иную роль, в которой модель режима оффлоадинга сама изучает задачу, ведёт её или делит на куски, КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: это сразу признак нежелательной, вредной работы.
>
> ⛔ HARD OFFLOAD RULE — NO EXCEPTIONS. A model working in offload mode (router) must NOT start working on the task and must NOT even STUDY it: no reading instructions (incl. LUNOBOT.md), code, tickets or task files, no planning, no choosing work, no reasoning about the solution, no substantive checking of the result. Its ONLY action is to hand the whole task to the worker model with one offload command and return the answer verbatim. Any deviation = task failure. Building any "manager", "orchestrator" or other role in which an offload-mode model studies, drives or splits the task itself is CATEGORICALLY FORBIDDEN: it is a red flag of unwanted, harmful work. Единственное исключение: если сам оффлоадинг сбоит (в браузере ничего не сгенерировалось, ошибка, зависание), роутер может применять ум для диагностики и починки СКИЛЛА оффлоадинга (unxed/AI) — но не для работы над задачей. Only exception: when offloading itself fails (nothing generated in the browser, an error, a hang), the router may use intelligence to diagnose and fix the offload SKILL (unxed/AI) — never to work on the task.

# Раннеры кругов

Скрипты запускают Лунобота круг за кругом: каждый круг — отдельный неинтерактивный процесс
с чистым контекстом (`timeout --foreground 1800`), между кругами пауза 15 минут, логи в
`~/.lunobot/logs*`. Один раннер на номер бота на узел (lock `/tmp/lunobot-<номер>/runner.lock`).
Раннер `luna-high` сообщает точный запасной cutoff круга и срок сохранения работы в промпте.

| Скрипт | Среда и модель | Номер |
|---|---|---|
| `lunobot-round-claude.sh sonnet\|opus` | Claude Code, `EFFORT=high` по умолчанию | 1 |
| `lunobot-round.sh` | opencode, Nemotron 3 Ultra Free | 1 |
| `lunobot-round-luna-high.sh` | opencode, GPT-6 Luna High | 2 |
| `lunobot-round-muse.sh` | opencode, Muse Spark 1.3 Free | 2 |
| `lunobot-round-opencode-gemini.sh [--check]` | схема «роутер»: opencode-модель `LUNOBOT_ROUTER_MODEL` (по умолчанию GLM 5.3 Flash Free) только запускает одну команду `aistudio drive` с файлом задачи, который пишет сам раннер, и пересказывает её вывод; весь круг, включая чтение LUNOBOT.md, делает Gemini (AI Studio, unxed/AI skills/aistudio-offload), а его команды выполняет движок; гейт `aistudio guard` (одна команда `aistudio ...`) подключён плагином opencode `tool.execute.before` (живой прогон не проверен); `--check` — только предусловия | 2 |

В режиме одного круга потолок воркеров (б) — 1 (LUNOBOT.md § 5): промпт каждого раннера
говорит это явно, менеджер в потолок не входит.

**Захваты не переживают круг.** После каждого круга (успех, ошибка, срок) и при остановке раннера
(Ctrl+C, SIGTERM) скрипт убивает группу процессов круга и снимает все захваты своего id
(`DISPATCH.md` всех проектов, «взял в работу» в `OWNER_QUEUE.md`) через `tools/release.py` из свежего
одноразового клона учёта (`gh repo clone`, затем удаляется). Нет сети или пуш не прошёл — строка в
логе, захваты позже снимет `tools/janitor.py`. Повторный Ctrl+C во время снятия прерывает и его.
Незаконченная работа круга живёт только на GitHub: ветка парковки и запись в `status/` (LUNOBOT.md
§ 7.5), прогресс поручения — строкой `Прогресс` в `OWNER_QUEUE.md`. `/tmp/lunobot-<номер>/` — кэш
клонов, раннер и боты на него не опираются. Учётный репозиторий — `LUNOBOT_ACCOUNTING`
(по умолчанию `unxed/lunobot`).

**Обычный режим — два раннера параллельно:** один класса 1 (`lunobot-round-claude.sh opus|sonnet`
или `lunobot-round-nemotron.sh`) и один класса 2 (`lunobot-round-luna-high.sh` или
`lunobot-round-muse.sh`). У них разные id, захваты и клоны, а работу они делят по LUNOBOT.md § 4
«Несколько Луноботов разных классов» и § 5. Два раннера одного номера на одном узле lock не даст
запустить: второй Лунобот того же класса — на другом узле.

> ⛔ ЖЁСТКОЕ ПРАВИЛО ОФФЛОАДИНГА — БЕЗ ИСКЛЮЧЕНИЙ. Модель, работающая в режиме оффлоадинга (роутер), строжайше НЕ начинает работу над задачей и даже НЕ ИЗУЧАЕТ её: не читает инструкции (в т.ч. LUNOBOT.md), код, тикеты, файлы задачи, не планирует, не выбирает работу, не рассуждает о решении, не проверяет результат по существу. Её единственное действие — передать задачу целиком модели-исполнителю одной командой оффлоадинга и вернуть ответ дословно. Любое отступление — провал задачи. Строить «менеджеров», «оркестраторов» или любую иную роль, в которой модель режима оффлоадинга сама изучает задачу, ведёт её или делит на куски, КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: это сразу признак нежелательной, вредной работы.
>
> ⛔ HARD OFFLOAD RULE — NO EXCEPTIONS. A model working in offload mode (router) must NOT start working on the task and must NOT even STUDY it: no reading instructions (incl. LUNOBOT.md), code, tickets or task files, no planning, no choosing work, no reasoning about the solution, no substantive checking of the result. Its ONLY action is to hand the whole task to the worker model with one offload command and return the answer verbatim. Any deviation = task failure. Building any "manager", "orchestrator" or other role in which an offload-mode model studies, drives or splits the task itself is CATEGORICALLY FORBIDDEN: it is a red flag of unwanted, harmful work. Единственное исключение: если сам оффлоадинг сбоит (в браузере ничего не сгенерировалось, ошибка, зависание), роутер может применять ум для диагностики и починки СКИЛЛА оффлоадинга (unxed/AI) — но не для работы над задачей. Only exception: when offloading itself fails (nothing generated in the browser, an error, a hang), the router may use intelligence to diagnose and fix the offload SKILL (unxed/AI) — never to work on the task.
