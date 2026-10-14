# vtui: ложные красные main от коротких сроков в тестах (хвост)

Обновлено 14-10-2026 13:56 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX).

Сделано и приземлено `land` в `lunobot/staging` (вершина `5e58e0d8`): `TestFar2lInteract_Timeout` (явный таймаут 200 мс, защита 30 с) и защитные сроки 1–3 с в 7 местах (far2l_extensions, framemanager, tasks, screenbuf_cursor) → 30 с. Поезд ещё не влит.

## Осталось (простая работа для Лунобота-2, один `land`)

- Короткие `time.After(N*time.Millisecond)` в `wayland_host_test.go` (6), `x11_host_test.go` (4), `gogpu_host_test.go` (2), `group_test.go`, `graphics_external_test.go`: открыть каждый; «событие обязано прийти» — защиту поднять до 30 с, «ничего не должно прийти» — оставить.
- Остаток из `main-doubleclick-1014.md` (тост, сны перед закрытием канала) — рядом, тем же шагом.
- Проверка в песочнице: macos-latest, `go vet . && go test -count=1 .` + lint (PROJECT.md). После `land` — этот файл удалить.
