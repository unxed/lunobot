# Очередь поручений владельца

Автор доверенных тикетов: unxed

Сюда владелец дописывает короткие обычные заметки — абзацы, между заметками строка `--`;
id, адресат и проект не нужны (пишет с телефона). Формальный блок `## id` необязателен.
Инструкции в этом файле — для всех агентов, любой живой агент берёт заметку в работу.
Взявший отмечает `Состояние: взял в работу — <id>, <UTC>`, превращает заметку в структуру
правкой файла (id, проект, поручение, критерий; исходный текст остаётся как «Заметка
владельца: …»), а закончив — УДАЛЯЕТ из файла всё, что связано с задачей: архива нет. Сделано
не так — напишите новую заметку. Проверка этого файла — первая операция на круге и при
запуске. Формат и порядок захвата — в [LUNOBOT.md](LUNOBOT.md), § 8.
В своей копии замените `unxed` в строке выше на GitHub-login владельца, который создаёт
поручения в Issues учётного репозитория (для организации — на личный login уполномоченного).
Боты могут добавлять блоки только как отражение тикета этого автора.

--

## account-29
Заметка владельца: https://github.com/unxed/lunobot/issues/29
Проект: учёт
Поручение: Учесть открытый доверенный issue «Вопросы владельцу» как очередь ожидающих решений владельца.
Критерий: новые решения владельца из issue #29 будут отражены отдельными поручениями после появления ответа; тестовые и уже отмеченные уведомления не исполняются как команды.
Состояние: ждёт владельца — issue #29 содержит вопросы к владельцу, а не разрешение принять решения за него; 29-09-2026 04:23:10 UTC

--

## f4-winget-12-skip-20261001
Заметка владельца: «Про winget: пока я не сделаю свою часть и не отпишусь там, просто пропускай.»
Проект: f4 (winget, unxed/f4#12)
Поручение: ничего по winget в f4#12 не делать и не спрашивать (форк microsoft/winget-pkgs и CLA за владельцем) до слова владельца в тикете f4#12.
Критерий: владелец написал в f4#12, что сделал свою часть; тогда блок удалить и продолжить.
Состояние: ждёт владельца, не брать; 01-10-2026

--

--

## account-46
Заметка владельца: https://github.com/unxed/lunobot/issues/46
Проект: учёт
Поручение: устранить оставшиеся несовместимости скриптов и инструкции с облачной сессией Claude Code по пунктам тикета.
Критерий: выполнены шаги и тесты тикета; проверить доступные критерии готовности по шагам и отчитаться в issue.
Прогресс: пункт 1 — REST-перезапуск failed jobs теперь проверяет результат запроса; `python3 -m unittest test_train` (65 тестов), коммит `89d0d67` в main. Пункт 2 — fallback REST dispatch для `sandbox.yml` в bisect с проверкой отказа и регрессионными тестами; `python3 -m unittest test_train` (67 тестов), коммит `4c04ddec` в main. Пункт 3 — отмена run переведена на REST endpoint `actions/runs/{id}/cancel`; тест `CancelRunTest`, полный `test_train` проходит (68 тестов), 13-10-2026 13:28:23 UTC. Пункт 4 — `sweep.py gh_all()` теперь при отказе `gh --paginate` обходит страницы через явный `page=N`, ошибки не маскируются пустым списком; `python3 -m unittest test_sweep test_private` (10 тестов), 13-10-2026. Пункт 5 — `owner_questions.py api_json()` при proxy-отказе `gh api --paginate` использует страницы `page=N`, прочие ошибки сохраняют корректное поведение; `python3 -m unittest test_owner_questions` (12 тестов), 13-10-2026. Пункт 6 — `status.py` для числа влитых PR и открытых issues перешёл с `search/issues` на paginated REST pulls и `open_issues_count` за вычетом открытых PR; при ошибке API пульт явно показывает недоступность, а не пустые данные; `python3 -m unittest test_status` (8 тестов), 13-10-2026. Пункт 7 — REST-варианты для облачных сессий добавлены в LUNOBOT.md (коммит 378837ecccbaeea614e21321d5dfaab504002a17); отчёт в issue: https://github.com/unxed/lunobot/issues/46#issuecomment-6149110194. `git diff --check`, 91 теста и health f4/vtui прошли; облачную интеграционную проверку именно в Claude Code этой сессией подтвердить нельзя, поэтому оставлено открытым.
Доп. проверка 13-10-2026 19:52:51 UTC: `tick-all`, `check_triage.py f4`, health f4/vtui; sweep не удалил файлов. Пульт `status.py f4` вывел 404 fallback-ошибки, прямые REST-запросы успешны; отчёт: https://github.com/unxed/lunobot/issues/46#issuecomment-6153912237. Claude Code live-проверка не выполнена; поручение остаётся открытым.
Доп. проверка 14-10-2026 03:00:44 UTC: `python3 -m unittest test_train test_sweep test_owner_questions test_status` — 95 тестов прошли. В этой среде нет Claude Code cloud proxy, поэтому пункты live-проверки из issue не подтверждены; поручение остаётся открытым.
Доп. проверка 14-10-2026 13:40:24 UTC: воспроизведён шум `status.py f4`: `work_commits()` запрашивал `lunobot/staging` у всех проектов, в том числе без поездов, вызывая ожидаемые 404 и fallback к анонимному API. Исправление с регрессионным тестом в PR https://github.com/unxed/lunobot/pull/66 (коммит `050e67fec2b792176c02108c6fa39e2ef0baa872`); `python3 -m unittest test_status` (9 тестов) и `git diff --check` прошли. Две ошибки rate limit в текущем OpenCode-выводе ещё остались; облачная live-проверка Claude Code всё ещё недоступна.
Доп. проверка 14-10-2026: `python3 -m unittest test_train test_sweep test_owner_questions test_status test_gh_post` — 134 теста прошли; PR #66 влит. Проверки `train.py health`: f4 staging зелёный, main успешен; vtui main успешен, staging без коммитов впереди main (quick pending). Отчёт: https://github.com/unxed/lunobot/issues/46#issuecomment-6177248772. Live-проверка в Claude Code proxy недоступна в этой среде; поручение остаётся незавершённым.
Доп. проверка 14-10-2026 23:23 UTC: `python3 -m unittest test_train test_sweep test_owner_questions test_status test_gh_post` — 139 тестов прошли; ResourceWarning о незакрытых файлах в `check_dispatch.py` остаются. Отчёт: https://github.com/unxed/lunobot/issues/46#issuecomment-6180692374. Live-проверка в Claude Code cloud недоступна в этой среде; поручение остаётся незавершённым.
Состояние: ждёт владельца — пункты 1–7 сделаны (см. Прогресс), остался только live-критерий: `health`/`sweep`/`status` из облачной сессии Claude Code; локальные инстансы (OpenCode, локальный Claude Code) его выполнить не могут, нужен запуск в облачной сессии; захват Лунобота-2 брошен с 17-10-2026, переведено Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), 20-10-2026 21:52:55 UTC
Доп. проверка 15-10-2026 07:25 UTC: 139 тестов `test_train`, `test_sweep`, `test_owner_questions`, `test_status`, `test_gh_post` прошли; `check_triage.py f4` подтвердил 134 тикета. `tick-all` отправил поезд f4, vtui зелёный. `status.py f4` вновь вывел два HTTP 404; облачный Claude Code proxy в этой среде недоступен, live-критерий #46 не подтверждён. Отчёт: https://github.com/unxed/lunobot/issues/46#issuecomment-6186820032. Поручение остаётся открытым.
Доп. проверка 15-10-2026 09:52 UTC: `test_train test_sweep test_owner_questions test_status test_gh_post` — 143 теста прошли; остались ResourceWarning в `check_dispatch.py`. `check_triage.py f4` подтвердил 134/134 открытых тикета. `tick-all` прошёл для f4 и vtui; оба staging зелёные, main vtui успешен, у f4 идёт полная матрица. `sweep.py --number 2 --apply` удалил один устаревший каталог шага; `owner_questions.py sweep` оставил 2 нерешённых вопроса. Live-проверка Claude Code proxy этой средой не поддерживается.
Доп. проверка 16-10-2026 03:11:00 UTC: `python3 -m unittest test_train test_sweep test_owner_questions test_status test_gh_post` — 175 тестов прошли; check_triage.py прошёл по всем 12 проектам после синхронизации dn#20; health f4/vtui — staging зелёный, main успешен. Отчёт: https://github.com/unxed/lunobot/issues/46#issuecomment-6207119215. Live-проверка Claude Code proxy недоступна; поручение остаётся открытым.
Доп. проверка 17-10-2026 04:12 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): прочитан новый отчёт владельца из live Claude Code: подтверждены tick-all, REST-обходы и ряд операций; в нём отмечены ограничения GraphQL/search, загрузки файловых вложений, merge permission и удаления веток. Этот отчёт не подтверждает явно весь критерий #46 для health/sweep/status из Claude Code; в текущей OpenCode-среде cloud proxy недоступен. В этом круге check_triage/check_try/close_candidates прошли по 12 проектам; health f4/vtui — staging зелёный, main успешен/идёт; `owner_questions.py sweep` оставил 3 открытых вопроса. Не взял пересекающиеся/уже отслеживаемые status-шаги и незрелый CI bp#16; поручение остаётся открытым.
Доп. проверка 17-10-2026 04:54:12 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): на текущем `main` учёта `python3 -m unittest test_train test_sweep test_owner_questions test_status test_gh_post` прошёл — 208 тестов; остались `ResourceWarning` в `train.py:1603`. `check_triage.py` прошёл по всем 12 проектам, `check_try.py` не нашёл тикетов без «Пробуйте!», кандидатов на закрытие нет. Отчёт владельца из Claude Code всё ещё не подтверждает live-критерий для `health`/`sweep`/`status`; в этой OpenCode-сессии Claude Code proxy недоступен, поэтому #46 остаётся открытым.
Доп. шаг 17-10-2026 (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): по live-отчёту владельца уточнён § 13.2 `LUNOBOT.md`: REST merge может быть запрещён permission classifier, удаление веток через git/API — недоступно прокси, а 403 файловых вложений не покрывается image-fetch; записано не обходить эти ограничения и оставлять merge/cleanup инстансу с нужными правами или фиксировать блокер. Документальные проверки выполнены; live-проверки `health`/`sweep`/`status` остаются непроверенными в этом окружении, поручение #46 остаётся открытым.

## account-213
Заметка владельца: https://github.com/unxed/lunobot/issues/213
Проект: bp
Поручение: вести unxed/bp#56 (safe-диалект) по плану тикета, один шаг — один PR; после шагов 2 и 13 сверить планы unxed/dn#87 и unxed/bp#3 и записать сверку в тикетах.
Критерий: шаги unxed/bp#56 влиты в main с зелёным CI, SPEC v0.7 — по критерию шага 16; сверка планов unxed/dn#87 и unxed/bp#3 записана в тикетах.
Состояние: свободно
Прогресс 21-10-2026 09:33:38 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер ac7aecfe): шаг 10 — указатели: поле ^T задачи уже ловит S4, отдельного правила S11 нет; lint-тест и SPEC влиты 5ee3976 (PR unxed/bp#92), обоснование и «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — поля именованных типов-указателей (Pointer, PChar), потокобезопасный `TWeak.TryLock` со стресс-тестом (projects/bp/status/56.md).
Прогресс 21-10-2026 09:30:48 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер ac7aecfe): шаг 10 — S11 интерфейсы записаны в SPEC (§6, статус, H6) влито 1238a93 (PR unxed/bp#91), «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — указатели, потокобезопасный `TWeak.TryLock` со стресс-тестом (projects/bp/status/56.md).
Прогресс 21-10-2026 09:27:53 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер ac7aecfe): шаг 10 — S11 видит интерфейсы подключённых модулей (как классы S5: рядом с файлом и в -Fu) влита 4367894 (PR unxed/bp#90), «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — указатели, запись про интерфейсы в SPEC, потокобезопасный `TWeak.TryLock` (projects/bp/status/56.md).
Прогресс 21-10-2026 09:24:48 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер ac7aecfe): шаг 10 — S11 для полей задачи интерфейсного типа (интерфейсы модуля, IInterface/IUnknown/IInvokable) влита 09cd132 (PR unxed/bp#89), «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — интерфейсы подключённых модулей, указатели, запись в SPEC, потокобезопасный `TWeak.TryLock` (projects/bp/status/56.md).
Прогресс 21-10-2026 08:59:13 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер acd67e03dccdd7d7e): шаг 10 — S11 записано в SPEC (таблица правил §6, статус, список правил bpvet, регистр H6) влито f95e69c (PR unxed/bp#88), «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — прочие поля задачи, потокобезопасный `TWeak.TryLock` (projects/bp/status/56.md).
Прогресс 21-10-2026 08:56:24 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер acd67e03dccdd7d7e): шаг 10, первая часть — правило `bpvet` S11 (поле задачи классового типа — ошибка и с `// borrow:`) влита 1d3ec69 (PR unxed/bp#87), «Пробуйте!» в unxed/bp#56; осталось в шаге 10 — S11 в SPEC, прочие поля задачи, потокобезопасный `TWeak.TryLock` (projects/bp/status/56.md).
Прогресс 21-10-2026 08:52:13 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер acd67e03dccdd7d7e): шаг 9, вторая часть — отчёт о циклах `TShared` в `SafeCheckNoLeaks` под `SAFE_DEBUG` (число, типы, путь цикла) влит f4d8dab (PR unxed/bp#86), «Пробуйте!» в unxed/bp#56; шаг 9 выполнен, дальше — шаг 10 плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 21-10-2026 08:46:02 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер acd67e03dccdd7d7e): шаг 9, первая часть — правило `bpvet` S15 (поле `TShared`, ведущее обратно к своему классу: предупреждение с путём и подсказкой «обратная ссылка — `TWeak`») влита f71e070 (PR unxed/bp#85), «Пробуйте!» в unxed/bp#56; осталось в шаге 9 — отчёт о циклах в `SafeCheckNoLeaks` под `SAFE_DEBUG` (projects/bp/status/56.md).
Прогресс 21-10-2026 08:17:22 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a0e32d2f1b7a64a4c): шаг 8, вторая часть — бенчмарк `TArenaRef.Get` (tests/bench, отчёт в job portable) влит 25955d4 (PR unxed/bp#84), «Пробуйте!» в unxed/bp#56; шаг 8 выполнен: R10 в отладке есть, но в релизе `Get` не нулевой стоимости (1,6 против 8,2 нс/чтение, вызов без inline) — записано в SPEC H3; дальше — шаг 9 плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 21-10-2026 08:12:47 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a0e32d2f1b7a64a4c): шаг 8, первая часть — поколения арены и `TArenaRef<T>` (`Get` после `FreeAll` → `ESafety` SAFE-R10 в отладке) влита 7587653 (PR unxed/bp#83), «Пробуйте!» в unxed/bp#56; осталось в шаге 8 — бенчмарк стоимости в релизе (projects/bp/status/56.md).
Прогресс 21-10-2026 07:43:55 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a8a8b90eb5691028f): шаг 7, часть (а) — `bpvet -FuDIR` (классы модулей из других каталогов, CI `-Fusafe -Fuext`) влит 3a52255 (PR unxed/bp#82), «Пробуйте!» в unxed/bp#56; шаг 7 выполнен, дальше — шаг 8 плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 21-10-2026 07:39:47 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): захват круга снят; шаг 7 части (в) unxed/bp#80 и (а)-1 unxed/bp#81 влиты; дальше — часть (а)-2: классы модулей из других каталогов пути поиска (опция путей bpvet), projects/bp/status/56.md.
Прогресс 21-10-2026 07:38:49 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a8a8b90eb5691028f): шаг 7, часть (а), кусок «классы модулей из uses, лежащих рядом с файлом» влит e4b4965 (PR unxed/bp#81), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — классы модулей из других каталогов пути поиска (projects/bp/status/56.md).
Прогресс 21-10-2026 07:33:14 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a8a8b90eb5691028f): шаг 7 — (б3) замыкания: в FPC 3.2.2 их нет (fcl-passrc разбирает, компилятор нет), записано в SPEC; (в) `Reset`/`Move` владельца при живом заимствовании влита 6eb0b79 (PR unxed/bp#80), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — классы других модулей (projects/bp/status/56.md).
Прогресс 21-10-2026 07:11:02 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a7e916e0eac94f4ee): шаг 7, часть (б3), кусок «поле задачи `TTask`» — lint-тест s05_param_task_bad влит 627fdc8 (PR unxed/bp#79), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — (б3) замыкания (сначала проверить разбор анонимных процедур fcl-passrc), `Reset`/`Move` при живом заимствовании, классы других модулей (projects/bp/status/56.md).
Прогресс 21-10-2026 06:34:36 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a8c6556f36973d3f9)): шаг 7, часть (б2) — параметр классового типа в поле/глобальную переменную без `// borrow:` — влита 6b67c50 (PR unxed/bp#78), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — замыкания и поля задачи, `Reset`/`Move` при живом заимствовании, классы других модулей
Прогресс 21-10-2026 06:33:13 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a8c6556f36973d3f9)): шаг 7, часть (б2) — параметр классового типа в поле/глобальную переменную — PR unxed/bp#78 открыт, не влит (первый прогон красный: лишний `end;`, починка fe79f2b, новый прогон 39556092539 не досмотрен); состояние в projects/bp/status/56.md
Прогресс 21-10-2026 06:24:10 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a8c6556f36973d3f9)): шаг 7, часть (б) — утечка результата `.Get` в поле/глобальную переменную без `// borrow:` — влита 63f094b (PR unxed/bp#77), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — параметр классового типа в поле/замыкание/поле задачи, `Reset`/`Move` при живом заимствовании, классы других модулей
Прогресс 21-10-2026 06:20:26 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a8c6556f36973d3f9)): шаг 7, часть S5 (поля и глобальные переменные классового типа без `// borrow:`) влита 56a0dfb (PR unxed/bp#76), «Пробуйте!» в unxed/bp#56; осталось в шаге 7 — классы других модулей, утечка `.Get`/параметра в поле, `Reset`/`Move` при живом заимствовании
Прогресс 21-10-2026 05:49:33 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a362fc252270f44cc)): шаг 6, проверка `TOwned` во время выполнения (R9) влита 7f8213c (PR unxed/bp#75; `-dSAFE_DEBUG`/`SafeDebugChecks`: `TOwned.Reset` при живой копии → `SAFE-R9`), «Пробуйте!» в unxed/bp#56; шаг 6 выполнен, дальше — шаг 7 (S5)
Прогресс 21-10-2026 05:45:14 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a362fc252270f44cc)): шаг 6, часть S10 (статическая проверка bpvet) влита 6b47ce3 (PR unxed/bp#74; копия `TOwned` только через `.Move`, без передачи по значению), «Пробуйте!» в unxed/bp#56; осталось в шаге 6 — проверка в `SAFE_DEBUG`
Прогресс 21-10-2026 05:39:56 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a362fc252270f44cc)): шаг 5, часть S9 влита 53d0d9f (PR unxed/bp#73; `UnicodeString/WideString/ShortString`/`String[N]` только под `// UNSAFE:`), «Пробуйте!» в unxed/bp#56; шаг 5 выполнен целиком, дальше — шаг 6 (S10)
Прогресс 21-10-2026 05:18:05 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a469dc52)): шаг 5, часть S6 влита b0fe413 (PR unxed/bp#72; `TFoo.Create` сразу в Own/Share/Adopt/Go/raise, иначе `// UNSAFE:`), «Пробуйте!» в unxed/bp#56; осталось в шаге 5 — S9 (projects/bp/status/56.md).
Прогресс 21-10-2026 05:08:11 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a469dc52)): шаг 4, пункт (5) `--strict` в job `lint` влит bf80807 (PR unxed/bp#71; safe/, ext/, tests/safe, tests/ext — 0 находок), «Пробуйте!» в unxed/bp#56; шаг 4 выполнен целиком, следующий — шаг 5 плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 21-10-2026 04:37:40 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a4cc9192)): шаг 4, пункт (2) S7 в программах тестов влит 5aaeb58 (PR unxed/bp#70; метка `// UNSAFE:` снимает предупреждение S7, 6 программ тестов помечены, `bpvet --report tests/safe tests/ext` — 0 warning), «Пробуйте!» в unxed/bp#56; следующее — пункт (5) `--strict` в job `lint`.
Прогресс 21-10-2026 04:09:47 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер ada544c7)): шаг 4, пункт (3) исключить tests/lint влит 499a8b6 (PR unxed/bp#69), «Пробуйте!» в unxed/bp#56; осталось в шаге 4 — S7 в программах тестов, затем --strict в `lint` (projects/bp/status/56.md).
Прогресс 21-10-2026 04:08:49 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер ada544c7)): шаг 4, пункт (3) исключить tests/lint — PR unxed/bp#69 (3047e3b) открыт, CI идёт (projects/bp/status/56.md).
Прогресс 21-10-2026 03:59:40 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер ada544c7)): шаг 4, пункт (1) `@Процедура` (S4) влит be4127d (PR unxed/bp#68), «Пробуйте!» в unxed/bp#56; осталось в шаге 4 — S7 в программах тестов, исключить tests/lint, затем --strict в `lint` (projects/bp/status/56.md).
Прогресс 21-10-2026 03:58:28 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер ada544c7)): шаг 4, пункт (1) `@Процедура` (S4) — PR unxed/bp#68 (2216289) открыт, CI идёт (projects/bp/status/56.md).
Прогресс 21-10-2026 02:56:19 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a88e1a28)): шаг 4, Fatal `nostackframe` в ext/bpthreads.pas — обход в bpvet влит 65d4c94 (PR unxed/bp#67), «Пробуйте!» в unxed/bp#56; `bpvet --report safe ext` чист (4 файла, обход полный); осталось в шаге 4 — `@Процедура` (S4), S7 в программах тестов, исключить tests/lint, затем --strict в `lint` (projects/bp/status/56.md).
Прогресс 21-10-2026 02:23:06 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер adde35bf)): шаг 4, --strict: метки в fail-тестах влиты 1ac7361 (PR unxed/bp#65), S8 в safe/ и ext/ — b02cb98 (PR unxed/bp#66), «Пробуйте!» в unxed/bp#56; осталось в шаге 4 — Fatal `nostackframe` в ext/bpthreads.pas, `@Процедура` (S4), S7 в программах тестов, затем --strict в `lint` (projects/bp/status/56.md).
Прогресс 21-10-2026 01:53:40 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): шаг 4, S4 влит целиком (unxed/bp#63 5d3384e, unxed/bp#64 00f4700); захват снят в конце круга. Следующее — bpvet --strict по safe/, ext/, tests/ (projects/bp/status/56.md).
Прогресс 21-10-2026 01:52:47 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a3db47b1)): шаг 4, часть S4 — арифметика указателей — влита 00f4700 (PR unxed/bp#64), «Пробуйте!» в unxed/bp#56; S4 закрыт целиком; осталось в шаге 4 — --strict по safe/, ext/, tests/ (projects/bp/status/56.md).
Прогресс 21-10-2026 01:45:19 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a3db47b1)): шаг 4, часть S4 для `^T`/`@` влита 5d3384e (PR unxed/bp#63), «Пробуйте!» в unxed/bp#56; осталось в шаге 4 — арифметика указателей (S4) и --strict по safe/, ext/, tests/ (projects/bp/status/56.md).
Прогресс 21-10-2026 01:21:58 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a1d2e9f4)): шаг 4, часть S3 влита 9a0c095 (PR unxed/bp#62), «Пробуйте!» в unxed/bp#56; осталось в шаге 4 — S4 и --strict по safe/, ext/, tests/ (projects/bp/status/56.md).
Прогресс 21-10-2026 01:12:47 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a1d2e9f4)): шаг 3 влит целиком — S12 d70b6a6 (PR unxed/bp#60), S8 973352a (PR unxed/bp#61), «Пробуйте!» в unxed/bp#56. Следующий — шаг 4 (S3, S4) плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 21-10-2026 01:07:17 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер a1d2e9f4)): шаг 3, часть S12 влита d70b6a6 (PR unxed/bp#60), «Пробуйте!» в unxed/bp#56; осталось в шаге 3 — правило S8 (projects/bp/status/56.md).
Прогресс 21-10-2026 00:44:35 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): шаг 2 влит 37f51bd (PR unxed/bp#58), «Пробуйте!» в unxed/bp#56; сверка шага 2 записана в unxed/dn#87 и unxed/bp#3. Следующий — шаг 3 плана unxed/bp#56 (projects/bp/status/56.md).
Прогресс 20-10-2026 21:53:22 UTC: шаг 1 (реестр рисков в safe/SPEC.md §8) — PR unxed/bp#57, коммит 8f2aceb, CI идёт; следующий — шаг 2 (каркас bpvet) после влития.
Прогресс 20-10-2026 21:58:45 UTC: шаг 1 влит 83dee43 (PR unxed/bp#57), «Пробуйте!» в unxed/bp#56; следующий — шаг 2 (каркас bpvet, S7).

## account-214
Заметка владельца: https://github.com/unxed/lunobot/issues/214
Проект: goWidgets
Поручение: вести unxed/goWidgets#30 (showcase — GUI для unxed/zipper по UX WinRAR) небольшими шагами, чередуя с планом pixy; одновременно не больше одного PR showcase; недостающее API zipper — отдельный тикет и PR в unxed/zipper.
Критерий: шаги 1–12 unxed/goWidgets#30 влиты с зелёными fast, linux, windows, macos; по каждому шагу в тикете — комментарий «что попробовать».
Состояние: свободно
Прогресс 21-10-2026 07:01:32 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a7e916e0eac94f4ee): шаг 2 влит 8cbc4a7 (PR unxed/goWidgets#32), «что попробовать» в unxed/goWidgets#30; API zipper Z1/Z7 влиты (unxed/zipper#36 → ebed9c3, unxed/zipper#37 → 431b760), «Try it!» в unxed/zipper#35. Дальше — шаг 3 unxed/goWidgets#30, тег zipper и подъём версии в zipgui (projects/goWidgets/status/30.md, projects/zipper/status/35.md).
Прогресс 21-10-2026 00:44:35 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): шаг 1 влит 25d2a0f (PR unxed/goWidgets#31), «что попробовать» в unxed/goWidgets#30. Следующий — шаг 2 по projects/goWidgets/status/30.md.
Прогресс 20-10-2026 22:53 UTC: TRIAGE #30 обновлён; ADR-0019 + план 12 шагов + каркас showcase/zipgui закоммичены локально (status/30.md), PR шага 1 открывается.

## account-215
Заметка владельца: https://github.com/unxed/lunobot/issues/215
Проект: dn
Поручение: вести unxed/dn#166 — FreeBSD в CI, документации и релизах; пробы и решения по другим несложным платформам таблицей в тикете; обновить projects/dn/PROJECT.md.
Критерий: FreeBSD-job зелёный и обязателен, README заявляет только проверенное, FreeBSD-архив есть в nightly и в релизе; решения по остальным кандидатам — в таблице тикета; паспорт dn обновлён.
Состояние: свободно
Прогресс 21-10-2026 07:01:32 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX); воркер a7e916e0eac94f4ee): PR unxed/dn#168 (шаг 2 FreeBSD) зелёный, но не влит — правит строку `commit:` в dn/third-party/f4-fish/NOTICE, по п. 5 CLAUDE.md dn нужно решение владельца; вопрос: https://github.com/unxed/dn/pull/168#issuecomment-6310068934 (notify_owner). Остальные шаги — по projects/dn/status/166.md.
Прогресс 21-10-2026 01:02:11 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): прежняя сессия узла завершилась; таблица платформ опубликована (https://github.com/unxed/dn/issues/166#issuecomment-6305062661), захват воркера a5978c8d снят; шаги 1–2 FreeBSD — у узла 801452e4 (PR unxed/dn#168). Следующее — по projects/dn/status/166.md.
Прогресс 20-10-2026 22:51:57 UTC: проба платформ (freebsd x64/aarch64, netbsd, openbsd, dragonfly, haiku, macos arm64/x64, linux armhf/riscv64) — ветка tmp/19d3/dn166-plat-1020-2245, прогон https://github.com/unxed/dn/actions/runs/39511037412; план шагов 3–4 FreeBSD готовится (status/166.md).

## account-216
Заметка владельца: https://github.com/unxed/lunobot/issues/216
Проект: f4
Поручение: вести unxed/f4#2115 — спека «far2l compatibility» для двухпанельников, аудиты unxed/dn и blue-panels/mcommander (код в форке unxed/mcommander, PR в upstream), подзадачи отдельными тикетами; завести паспорт projects/mcommander/ и строку в конце projects/INDEX.md.
Критерий: спека влита в f4 (шаг 3); аудиты f4, dn, mcommander опубликованы, пробелы заведены тикетами и закрыты до заявленного уровня; в README f4 ссылки на прошедшие аудит проекты (шаг 9).
Состояние: свободно
Прогресс 20-10-2026 22:54:08 UTC: паспорт projects/mcommander/ (код unxed/mcommander, тикеты blue-panels/mcommander, PR в upstream) и строка 13 в INDEX.md; инвентаризация клавиш/протоколов far2l и f4 собрана, черновик спеки docs/FAR2L_COMPAT.md пишется (шаги 1–3 unxed/f4#2115).
Прогресс 21-10-2026 00:10:11 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): прежняя сессия узла (воркеры от 20-10-2026 22:45Z) завершилась; в main учёта — паспорт projects/mcommander/ и строка 13 в INDEX.md; черновик спеки docs/FAR2L_COMPAT.md не был запушен и не записан в status — не доверяем (§ 1), шаги 1–3 unxed/f4#2115 начинать с инвентаризации заново.

## account-218
Заметка владельца: https://github.com/unxed/lunobot/issues/218
Проект: dn
Поручение: вести миграцию dn на асинхронную архитектуру в духе Far 4 (issue unxed/lunobot#218): сначала завести тикет в unxed/dn с атомарным планом по 9 пунктам scope и пререквизитам (DN 3.0, bp safe-диалект unxed/bp#56, примитивы tv3), затем шаги по плану — не раньше пререквизитов.
Критерий: тикет плана в unxed/dn со ссылкой из issue; шаги влиты в main с зелёным CI; прогресс отмечен в тикете.
Состояние: свободно
Прогресс 21-10-2026 03:25:52 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): тикет плана unxed/dn#170 заведён, ссылка в unxed/lunobot#218; следующие шаги — по плану после пререквизитов.
Прогресс 21-10-2026 00:12:55 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): отражено из issue; в этом круге узла 19d3 не взято (один воркер занят поручением account-releases-protocol и land) — свободно для любого живого Лунобота-1.
--
