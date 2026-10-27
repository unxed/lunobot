# unxed/oddyness — план карточек P01–P25 (поручение unxed/lunobot#248)

Критерии каждой карточки — только `docs/implementation/plan.md` репозитория (`AGENTS.md` п. 8: учёт их не копирует).
Одна карточка (или подкарточка) — один PR с тестами и строкой `Статус` карточки в `plan.md`; первая незавершённая
карточка с завершёнными зависимостями. Л1 — исследовательский риск, Л2 — ясный шаг по готовому контракту.

Порядок по зависимостям:
1. P01 каркас запуска и CI без CGO (Л2)
2. P02 загрузка конфигурации (Л2) · P03 точные числа (Л1) · P07 парсер BSL (Л1)
3. P04 первая форма и UI harness (Л1) · P05 SQLite-справочник (Л1) · P08 VM (Л1)
4. P06 каталог в GUI (Л2) · P09 управление потоком (Л1) · P10 черновик документа (Л2) · P15 Table в goWidgets (Л1)
5. P11 регистр (Л1) → P12 проведение (Л1) → P13 выдача (Л2) → P14 отмена (Л2)
6. P16 документы в GUI (Л2) · P17 запросы (Л1) → P18 отчёт остатков (Л2) · P19 права (Л2)
7. P20–P25 Transition; публикация preview P25 — отдельное поручение владельца

21-10-2026 21:50 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): учёт заведён (паспорт, INDEX.md, TRIAGE — код 0). Ждёт владельца: токен флота не пишет в unxed/oddyness (HTTP 403 «Resource not accessible by personal access token» на `issues` и `git/refs`), вопрос — https://github.com/unxed/lunobot/issues/248#issuecomment-6327318259.

21-10-2026 22:32:13 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): P01 реализован, коммит `af9424990b9e2bb3b84c23d45cdbcfb197fcbdb7` припарковано — unxed/oddyness, ветка `tmp/19d3/oddyness-p01-skeleton`; PR https://github.com/unxed/oddyness/pull/1 в `lunobot/pr/p01-skeleton`; CI [#2](https://github.com/unxed/oddyness/actions/runs/39686948956) выполняется; CI.md и BRANCHES.md обновлены. Локальные сборки/тесты не запускались по паспорту. Осталось: получить CI без ожидания в этом круге и обновить P01 status по его результату.

21-10-2026 23:11:36 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): P01 реализован и оформлен PR https://github.com/unxed/oddyness/pull/1; предыдущий обязательный CI #2 успешен на `af9424990b9e2bb3b84c23d45cdbcfb197fcbdb7`. Статус карточки дополнен ссылкой на PR/CI и запушен коммитом `54a23a7ffee1a42e2e5ca28e0973870f75151329`; для нового SHA запущен CI #3, результат не ожидаю. Осталось дождаться успешного CI #3, затем влить PR.

21-10-2026 23:12:50 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): CI #3 успешен на `54a23a7ffee1a42e2e5ca28e0973870f75151329` (https://github.com/unxed/oddyness/actions/runs/39691784794); обязательные проверки P01 выполнены. PR https://github.com/unxed/oddyness/pull/1 открыт, осталось влить.

22-10-2026 00:00:01 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): P01 завершена: PR https://github.com/unxed/oddyness/pull/1 влит в `main`, merge-коммит `c78fbc6774a35ba1fc2186a346520a434d02f318`; CI #3 зелёный, CI `main` #4 отменён по §7.3 (PR был актуален; сохранение каждого прогона main не требуется). Issue поручения unxed/lunobot#248 закрыт после отчёта.

27-10-2026 19:50 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P03 часть 1 из 2 (контракт и `Number`) припарковано — unxed/oddyness, ветка `tmp/19d3/odd-p03-1`, sha `96bc194f2e5d7dc0c4cbcfb4503a26e673182ec2`; дальше: PR `lunobot/pr/p03-numbers-contract` и CI. Часть 2: сравнение кандидатов decimal и выбор представления.

27-10-2026 19:52 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P03 часть 1 из 2 приземлена — PR https://github.com/unxed/oddyness/pull/2 влит merge-коммитом `431be0e4e8de3cd12be8f14e8e879409ed3b1d8a`, `ci` зелёный на `fcf04f8fbb75b06e2b41eed3a2bdcf8a89b8a174`, ветка парковки удалена. Осталось: часть 2 из 2 (сравнение кандидатов apd/shopspring/govalues в отдельной пробе, выбор представления, умножение/деление по выбранному правилу), затем P07.

27-10-2026 19:54 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P03 часть 2 из 2 (проба кандидатов) припарковано — unxed/oddyness, ветка `tmp/19d3/odd-p03-2`, sha `99f5e49ca9e263163492214c1c2d7e4e689fdcf3`; PR https://github.com/unxed/oddyness/pull/3 в `lunobot/pr/p03-decimal-probe`, CI [#8](https://github.com/unxed/oddyness/actions/runs/40573275782) идёт (go.sum пробы — из лога). Осталось: записать результаты и выбор в numbers.md и статус P03, влить.

27-10-2026 19:57 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P03 завершена — часть 2 приземлена: PR https://github.com/unxed/oddyness/pull/3 влит merge-коммитом `1c1b3ec22e3b40114fbc950eb95069d5aef137c8`, `ci` зелёный на `2702127a2803d5e05fcac599ac8828433a2ebdd3`, ветка парковки удалена; выбор — собственный `Number`. Следующая по плану: P07 (парсер BSL).

27-10-2026 20:03 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P07 (парсер BSL, одним PR) припарковано — unxed/oddyness, ветка `tmp/19d3/odd-p07-1`, sha `800969343134e153cdc48c2f9561e94f5ba7cbaf`; PR https://github.com/unxed/oddyness/pull/4 в `lunobot/pr/p07-bsl-parser`, CI [#12](https://github.com/unxed/oddyness/actions/runs/40574530756) идёт. Осталось: по результату CI — строка Статус в plan.md и влитие.

27-10-2026 20:06 UTC (Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)): P07 завершена — PR https://github.com/unxed/oddyness/pull/4 влит merge-коммитом `126ea6eb3400a7c91d70be95f533eaac8022655d`, `ci` зелёный на `c892c59340053196ebf81db78dc12bda56e05db5`, ветка парковки удалена. Следующие по плану: P08 (VM, зависит от P07), P04/P05 (зависят от P02 — карточка Лунобота-2).
