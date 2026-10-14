# Красный main vtui `7d73940`: Test (darwin/amd64), `TestFrameManager_DoubleClickDetection`

Обновлено 14-10-2026 08:02 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент ad5d076f).

## Причина

Прогон main [38528639673](https://github.com/unxed/vtui/actions/runs/38528639673) (#462), job [Test (darwin/amd64)](https://github.com/unxed/vtui/actions/runs/38528639673/job/115739450665): `--- FAIL: TestFrameManager_DoubleClickDetection (2.55s)`, `framemanager_test.go:2895: Fast second click was not detected as double click` (и 2902, 2905). Это не гонка из unxed/vtui#214 (там `TestFrameManager_SizePolling`). Тест кормит `markMultiClick` настоящим `time.Now()` после `time.Sleep(100ms)` при окне двойного клика 400 мс; на перегруженном раннере macOS Intel сон растянулся (тест шёл 2.55 с при 0.9 с сна) — интервал превысил 400 мс. Дефект теста (зависимость от настенных часов), не кода и не мержа unxed/vtui#206. Паника «boom» в логе — ожидаемый вывод `TestLogAndRepanicKeepsThePanicGoing`.

## Сделано

- Коммит `7a444df` в клоне `/tmp/lunobot-1/work/vtui-redmain2-1014-0759/vtui`, ветка `lunobot/urgent/vtui-main-doubleclick` от main `7d73940` (запушена): тест двигает синтетические часы вместо `time.Sleep`.
- PR [unxed/vtui#215](https://github.com/unxed/vtui/pull/215), прогон PR [#464](https://github.com/unxed/vtui/actions/runs/38532273832); песочница [38532243835](https://github.com/unxed/vtui/actions/runs/38532243835) (`macos-15-intel`, `go vet . && go test -run TestFrameManager_DoubleClickDetection -count=50 .`). Строка PR и пометка у прогона main 38528639673 — в CI.md; захват снят.

## Дальше

- Прогон PR и песочница зелёные — влить #215 по § 7.3 (ветка из BRANCHES.md, этот файл удалить).
- Прогон main 38528639673 после завершения: если #215 ещё не влит — `gh run rerun 38528639673 --failed -R unxed/vtui` (другие упавшие job'ы того прогона — разбирать отдельно).
