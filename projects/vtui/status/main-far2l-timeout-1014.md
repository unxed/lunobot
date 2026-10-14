# Красный main vtui `53ed802`: Test (darwin/amd64), `TestFar2lInteract_Timeout`

Обновлено 14-10-2026 13:50 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX).

## Причина

Прогон main [38573753702](https://github.com/unxed/vtui/actions/runs/38573753702): `far2l_extensions_test.go:62: Interaction did not timeout, it hung`. Тест ждал `Far2lInteract` (таймаут 2 с) не дольше 3 с, `far2lInteractMu` общий для пакета; на загруженном macOS-раннере запас в 1 с кончился. Тот же sha 5c45599 прошёл в PR поезда (38572520383) — флейк теста, не кода. Сегодня на main это уже четвёртый ложный красный (SizePolling, двойной клик, framemanager_test.go:3351, этот): класс «жёсткие короткие сроки в тестах vtui».

## Сделано

- Коммит `01e521b2` в клоне `/tmp/lunobot-1/vtui`, ветка `lunobot/work-far2l-flake`: явный таймаут 200 мс, защита от зависания 30 с. Песочница macos-latest (gofmt, vet, `-count=3`, lint) — [38574909529](https://github.com/unxed/vtui/actions/runs/38574909529). Прогон main перезапущен (`rerun --failed`).

## Дальше

- Песочница зелёная — `python3 train.py land` из `/tmp/lunobot-1/vtui` (коммит несёт `Lunobot-Task: vtui-flaky-far2l-timeout`), снять захват «красный main 53ed802», этот файл удалить. Красная — читать лог.
- Класс: пройти `grep -n 'time.After(' *_test.go` и поднять защитные сроки ниже 5 с там, где ждут горутину/раннер (отдельный шаг, один `land`).
