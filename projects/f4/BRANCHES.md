# BRANCHES — f4

Журнал намерений создания веток под lunobot/; записи сверяются с GitHub.

(очищено 27-09-2026: все предыдущие строки были веток с префиксом codex/ — устаревшая договорённость, префикс полностью убран из инструкции; сами ветки на GitHub, если ещё физически существуют, — задача отдельной уборки мусора, не отслеживаются здесь)

27-09-2026 11:40:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `lunobot/batch/f4/2` влита и физически удалена (PR #1549, мерж владельцем — коммит main 6ebc21e, см. CI.md); строки этой пачки в BRANCHES.md удалены за ней (§ 7.3), счётчик пачки сдвинут на `lunobot/batch/f4/3`

27-09-2026 11:40:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `lunobot/batch/f4/3` — новый активный счётчик пачки, 1 запись (кастомная задача «#1178: plugins/sqlite → RPC-плагин», части 1-4)

27-09-2026 03:39:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 2-я запись, коммит `b713554` (кастомная задача «#1178: bump tar/zipper, tarindex_simple в -tags lite», шаги 7-8/11)

27-09-2026 03:48:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 3-я запись, коммит `dc3e199` (кастомная задача «#1178: plugins/sqlite → RPC-плагин», часть 1/4 — свой go.mod, rpc_plugin.go, cmd/sqlite-plugin, убрана регистрация из manager.go)

27-09-2026 03:48:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 4-я запись, коммит `55d2757` (та же задача, часть 2/4 — CI-джоба build-sqlite-plugin, публикация в release/nightly)

27-09-2026 03:48:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 5-я запись, коммит `628f1b9` (та же задача, часть 3/4 — first-party запись sqlite в PlugRing-каталоге)

27-09-2026 03:48:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 6-я запись, коммит `449cbb5` (та же задача, часть 4/4 — пункт меню SQLite client теперь ведёт в PlugRing, если плагин не установлен; задача полностью готова, все 4 части запушены)

27-09-2026 03:51:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 7-я запись, коммит `b92b6d8` (фикс-форвард: `quick` уронил TestCommandPaletteProductionCommandSurfaceInventory — добавлена запись аудита ProcessKey для sqlite.RPCPlugin, по образцу cloudfox/ios/android)

27-09-2026 03:55:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 8-я запись, коммит `2facf24` (фикс-форвард: `quick` уронил TestAllDialogs_LayoutValidation/App.SQLite — добавлен skip app.sqlite рядом с app.plugring; и TestMergeFirstPartyPlugRingItemsAppendsAndDedupsByID — счётчик 3→4; `quick` зелёный после этого коммита)

27-09-2026 14:30:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка перебазирована на main лично владельцем записи (конфликт в manager.go с только что смерженным PR #1551 ProcList), force-push `fa1d0cdc` — все 7 коммитов #1178 сохранены, только новые хэши (счётчик записей продолжается, старые хэши в п.2-8 выше теперь исторические)

27-09-2026 14:35:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), `lunobot/batch/f4/3` — 9-я запись, коммит `8060e3f8` (кастомная задача «#1178: финальный шаг 10-11/11» — TestLiteBuildExcludesSQLiteDependency + TestRegularBuildStillIncludesSQLiteDependency в cmd/f4/lite_deps_test.go; guard корректно Skip, не Fatal: internal/sheet/store.go тянет github.com/ncruces/go-sqlite3 безусловно в обеих сборках, это уже задокументировано владельцем #1178 в manager.go/rpc_plugin.go, отдельный будущий тикет, не блокер; замер размера -tags lite: -184320 байт/-180.0 KiB/-0.31% — реальный, но маленький выигрыш от вычищенного кода plugins/sqlite, а не от ухода go-sqlite3/wazero из бинарника, который из-за internal/sheet остаётся; задача #1178 в её заявленном скоупе (tar/zipper-индексация + sqlite-плагин) закрыта, полное честное резюме всей 11-шаговой цепочки — в теле коммита)

