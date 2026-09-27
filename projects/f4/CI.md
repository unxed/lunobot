# CI — f4

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 21:45:00 Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент), тикет https://github.com/unxed/f4/issues/312 (части 3 и 4 из 4), красный `quick` (`TestSettingsStoreSaveIsAtomic`) починен (инвертированное условие в тесте), коммит `161d2e3b`, `quick` зелёный (прогон https://github.com/unxed/f4/actions/runs/36352784116), пачка перезрела (висела с утра без PR) — открыт PR [#1592](https://github.com/unxed/f4/pull/1592), полная матрица ещё не стартовала на момент записи


27-09-2026 22:00:00 Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент), f4#1563 end-to-end через plugins/observer доказан на реальном isoimg.wasm (немодифицированные исходники Observer): LoadSubModule/OpenStorage (PR #1590, полная матрица build.yml зелёная), GetItem (PR #1591, стек на #1590, quick зелёный), ExtractItem+прогресс (PR #1594, стек на #1591, quick зелёный). wasm-opt -Oz: 365608→303155 байт (-17%)
