# vtui: ложные красные main от коротких сроков в тестах (хвост)

Обновлено 14-10-2026 13:56 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX).

Сделано и приземлено `land` в `lunobot/staging` (вершина `5e58e0d8`): `TestFar2lInteract_Timeout` (явный таймаут 200 мс, защита 30 с) и защитные сроки 1–3 с в 7 местах (far2l_extensions, framemanager, tasks, screenbuf_cursor) → 30 с. Поезд ещё не влит.

## Осталось (простая работа для Лунобота-2, один `land`)

- Короткие `time.After(N*time.Millisecond)` в `wayland_host_test.go` (6), `x11_host_test.go` (4), `gogpu_host_test.go` (2), `group_test.go`, `graphics_external_test.go`: открыть каждый; «событие обязано прийти» — защиту поднять до 30 с, «ничего не должно прийти» — оставить.
- Остаток из `main-doubleclick-1014.md` (тост, сны перед закрытием канала) — рядом, тем же шагом.
- Проверка в песочнице: macos-latest, `go vet . && go test -count=1 .` + lint (PROJECT.md). После `land` — этот файл удалить.

14-10-2026 20:19 UTC (Лунобот-1, node 19d368003c6c048e43dbec70; LNX, круг): сроки «событие обязано прийти» в тестах хостов (wayland 4, x11 4, gogpu 2, group 1, flush 5 с → 30 с, тост в framemanager_test) подняты до 30 с; проверки «ничего не должно прийти» (20 мс, 200 мс) оставлены. Локальный коммит `a2abac45fa1c2931bd191bee5bcaccb9c6bbe6cf`, клон `/tmp/lunobot-1/work/vtui-timeouts-1017/vtui` (ветка `work`), запушен в `tmp/19d3/vtui-guard-timeouts`. Песочница: macos-latest https://github.com/unxed/vtui/actions/runs/38630847881 (`go vet . && go test -count=1 -run 'Wayland|X11|GoGPU|Group|Toast|Flush|External|Focus' .`) и ubuntu-latest (полный `go vet . && go test -count=1 .`, номер — `gh run list -R unxed/vtui --workflow sandbox.yml --branch tmp/19d3/vtui-guard-timeouts`). Осталось: оба зелёные на headSha `a2abac4` (сверить `gh run view <id> --json headSha`) → `train.py land` из клона (если staging красный или `land` заморожен — оставить припаркованным), затем строка TRIAGE не нужна (тикета нет), этот файл удалить вместе с хвостом `main-doubleclick-1014.md` (сны перед закрытием канала в framemanager_test остались — отдельным малым шагом, если ещё встречаются).
