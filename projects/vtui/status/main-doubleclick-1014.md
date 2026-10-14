# Красный main vtui `7d73940`: Test (darwin/amd64), `TestFrameManager_DoubleClickDetection`

Обновлено 14-10-2026 08:00 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент ad5d076f).

## Причина

Прогон main [38528639673](https://github.com/unxed/vtui/actions/runs/38528639673) (#462), job [Test (darwin/amd64)](https://github.com/unxed/vtui/actions/runs/38528639673/job/115739450665): `--- FAIL: TestFrameManager_DoubleClickDetection (2.55s)`, `framemanager_test.go:2895: Fast second click was not detected as double click` (и 2902, 2905). Это не гонка из unxed/vtui#214 (там `TestFrameManager_SizePolling`). Тест кормит `markMultiClick` настоящим `time.Now()` после `time.Sleep(100ms)` при окне двойного клика 400 мс; на перегруженном раннере macOS Intel сон растянулся (тест шёл 2.55 с при 0.9 с сна) — интервал превысил 400 мс. Дефект теста (зависимость от настенных часов), не кода и не мержа unxed/vtui#206. Паника «boom» в логе — ожидаемый вывод `TestLogAndRepanicKeepsThePanicGoing`.

## Дальше

- Починка: тест подаёт в `markMultiClick` синтетическое время (база + смещения), без `time.Sleep`. Ветка `lunobot/urgent/vtui-main-doubleclick`, клон `/tmp/lunobot-1/work/vtui-redmain2-1014-0759/vtui`.
