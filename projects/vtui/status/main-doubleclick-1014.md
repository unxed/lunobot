# Красный main vtui `7d73940`: Test (darwin/amd64), `TestFrameManager_DoubleClickDetection`

Обновлено 14-10-2026 08:04 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент ad5d076f).

## Причина

Прогон main [38528639673](https://github.com/unxed/vtui/actions/runs/38528639673) (#462), job [Test (darwin/amd64)](https://github.com/unxed/vtui/actions/runs/38528639673/job/115739450665): `--- FAIL: TestFrameManager_DoubleClickDetection (2.55s)`, `framemanager_test.go:2895: Fast second click was not detected as double click` (и 2902, 2905). Это не гонка из unxed/vtui#214 (там `TestFrameManager_SizePolling`). Тест кормит `markMultiClick` настоящим `time.Now()` после `time.Sleep(100ms)` при окне двойного клика 400 мс; на перегруженном раннере macOS Intel сон растянулся (тест шёл 2.55 с при 0.9 с сна) — интервал превысил 400 мс. Дефект теста (зависимость от настенных часов), не кода и не мержа unxed/vtui#206. Паника «boom» в логе — ожидаемый вывод `TestLogAndRepanicKeepsThePanicGoing`.

## Сделано

- Коммит `7a444df` в клоне `/tmp/lunobot-1/work/vtui-redmain2-1014-0759/vtui`, ветка `lunobot/urgent/vtui-main-doubleclick` от main `7d73940` (запушена): тест двигает синтетические часы вместо `time.Sleep`.
- PR [unxed/vtui#215](https://github.com/unxed/vtui/pull/215), прогон PR [#464](https://github.com/unxed/vtui/actions/runs/38532273832); песочница [38532243835](https://github.com/unxed/vtui/actions/runs/38532243835) (`macos-15-intel`, `go vet . && go test -run TestFrameManager_DoubleClickDetection -count=50 .`). Строка PR и пометка у прогона main 38528639673 — в CI.md; захват снят.
- Класс флейков (§ 7.1, поручение менеджера): фикс-форвард `0349182` в ту же ветку (тот же клон) — `TestFrameManager_WaitFar2lResponse_NilEvent` ждал регистрации ожидающего 100 снами по 1 мс при тайм-ауте 150 мс; теперь опрос до крайнего срока 5 с и тайм-аут 5 с. Прогон PR [#465](https://github.com/unxed/vtui/actions/runs/38532575497), песочница [38532578364](https://github.com/unxed/vtui/actions/runs/38532578364) (`macos-15-intel`, `go vet . && go test -run 'TestFrameManager_DoubleClickDetection|TestFrameManager_WaitFar2lResponse_NilEvent' -count=30 .`). Песочница 38532243835 проверяла только `7a444df`.

## Осталось (просмотрено, не чинилось)

- `TestFrameManager_SizePolling` — чинит unxed/vtui#214, не трогать.
- Тост в `framemanager_test.go` (~366–387): `time.After(100ms)` на постановку задачи и сон 150 мс при сроке 100 мс; сон в безопасную сторону, риск низкий — проверить, синхронно ли `ShowToast` кладёт задачу в `TaskChan`.
- `far2l_extensions_test.go:235`: ответ через 50 мс при ожидании 2 с — запас большой; `:90`, `:182`, `:520` — опрос с крайним сроком, в порядке.
- `framemanager_test.go:1209`, `:1342`, `:1356`, `:3310`: сон перед закрытием канала/`Stop`; на медленном раннере проверка становится пустой, но ложно не падает.
- `x11_host_test.go:46`, `:54`: сон 2 мс и `After` — монотонные часы, в безопасную сторону.

## Дальше

- Прогон PR #465 и песочница 38532578364 зелёные — влить #215 по § 7.3 (ветка из BRANCHES.md, этот файл удалить).
- Прогон main 38528639673 после завершения: если #215 ещё не влит — `gh run rerun 38528639673 --failed -R unxed/vtui` (другие упавшие job'ы того прогона — разбирать отдельно).
