# CI — f4

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 11:00:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), main, коммит 6ebc21e, прогон https://github.com/unxed/f4/actions/runs/36290893458 (после мержа #1549 владельцем — cloudfox/iOS/Android полностью, покрытие, quick.yml-фикс, оба моих багфикса)

27-09-2026 12:50:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), tar (v0.1.137) и zipper (v0.1.176) закрыты и смержены — цепочка sqlite-free почти готова, статус опубликован в #1178

27-09-2026 03:53:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/f4/issues/312 (часть 1 из 4), PR [#1551](https://github.com/unxed/f4/pull/1551), коммит `a619103`, прогон [#5278](https://github.com/unxed/f4/actions/runs/36292685714)

27-09-2026 13:40:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), PR #1551 (ProcList часть 1) — падал на langfmt (.lng не форматированы) и errcheck (defer controller.Close()); оба пофикшены лично (7b72ff0c), жду свежий прогон

27-09-2026 14:30:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка lunobot/batch/f4/3 перебазирована на main лично (был конфликт в manager.go — main уже смержил PR #1551 ProcList, разрешил вручную сохранив оба плагина), force-push fa1d0cdc

27-09-2026 16:45:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/f4/issues/1178 (финальный шаг — вынос plugins/sqlite), PR https://github.com/unxed/f4/pull/1554, жду прогон

27-09-2026 15:35:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/f4/issues/1552, PR https://github.com/unxed/f4/pull/1553, жду прогон

27-09-2026 04:40:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/f4/issues/312 (часть 2 из 4), PR [#1555](https://github.com/unxed/f4/pull/1555), коммит `ccc4095`, прогон [#5283](https://github.com/unxed/f4/actions/runs/36294964697)

27-09-2026 17:15:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/f4/issues/1178 (PR #1554) — Build sqlite-plugin (darwin/amd64) упал: cannot use vfs.MetadataExplicit as uint32 (нет явной конверсии); лично пофикшено, коммиты `0836167d`+`973f26d1`, жду свежий прогон

27-09-2026 18:05:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), красный main после мержа #1554 (Touch #1178) — TestLiteBuildExcludesSQLiteDependency резолвил plugins/sqlite как путь внутри корневого модуля, что больше не работает после его выноса в свой go.mod; тегам go list в тесте не хватало tarindex_simple (как в build-lite), PR https://github.com/unxed/f4/pull/1556, коммит `7da77d92`, прогон https://github.com/unxed/f4/actions/runs/36295956196

27-09-2026 17:40:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX; субагент), тикет https://github.com/unxed/f4/issues/312 (часть 3 из 4), коммит `4eda0086` ушёл пачкой в ветку `lunobot/batch/f4/4` (см. BRANCHES.md) — PR за пачку не открывался (1 запись из 10, ветка младше часа): полная матрица не запускается, только `quick`, прогон https://github.com/unxed/f4/actions/runs/36296386837

27-09-2026 20:00:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX; субагент), тикет https://github.com/unxed/f4/issues/312 (часть 4 из 4, финальная), коммит `3c1420dc` ушёл в ту же пачку `lunobot/batch/f4/4` (см. BRANCHES.md) — PR за пачку не открывался (2 записи из 10, ветка младше часа с момента ребейза владельцем): полная матрица не запускается, только `quick`, прогон https://github.com/unxed/f4/actions/runs/36298188066 (не проверен, был in_progress на момент записи)
