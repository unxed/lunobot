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
