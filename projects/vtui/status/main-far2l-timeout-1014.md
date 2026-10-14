# Красный main vtui `53ed802`: Test (darwin/amd64), `TestFar2lInteract_Timeout`

Обновлено 14-10-2026 13:50 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX).

## Причина

Прогон main [38573753702](https://github.com/unxed/vtui/actions/runs/38573753702): `far2l_extensions_test.go:62: Interaction did not timeout, it hung`. Тест ждал `Far2lInteract` (таймаут 2 с) не дольше 3 с, `far2lInteractMu` общий для пакета; на загруженном macOS-раннере запас в 1 с кончился. Тот же sha 5c45599 прошёл в PR поезда (38572520383) — флейк теста, не кода. Сегодня на main это уже четвёртый ложный красный (SizePolling, двойной клик, framemanager_test.go:3351, этот): класс «жёсткие короткие сроки в тестах vtui».

## Сделано

- Коммит `01e521b2` в клоне `/tmp/lunobot-1/vtui`, ветка `lunobot/work-far2l-flake`: явный таймаут 200 мс, защита от зависания 30 с. Песочница macos-latest (vet, `-count=3`, lint) — [38574909529](https://github.com/unxed/vtui/actions/runs/38574909529). Вторым коммитом `16c87343` (там же, ветка `tmp/19d3/far2l-flake-1014` = HEAD клона) — класс: защитные сроки 1–3 с в 7 местах тестов (far2l_extensions, framemanager, tasks, screenbuf_cursor) подняты до 30 с; песочница macos-latest, полный `go test -count=1 .` + lint — [38575308724](https://github.com/unxed/vtui/actions/runs/38575308724) (результат не проверен; `headSha` обязан быть 16c87343). Прогон main перезапущен (`rerun --failed`).

## Дальше

- Обе песочницы зелёные — `python3 train.py land` (два коммита) из `/tmp/lunobot-1/vtui` (коммит несёт `Lunobot-Task: vtui-flaky-far2l-timeout`), снять захват «красный main 53ed802», этот файл удалить. Красная — читать лог.
- Остаток класса: короткие `time.After(N*time.Millisecond)` в `wayland_host_test.go` (6), `x11_host_test.go` (4), `gogpu_host_test.go` (2), `group_test.go`, `graphics_external_test.go` — открыть каждый: если это защита «событие обязано прийти», поднять до 30 с; если «ничего не должно прийти» — оставить. Отдельный шаг, один `land`.
