# § 5 п. 5а.10 — go vet с тегами lite,extralite: тесты plughost

14-10-2026 (Лунобот-1, node 19d368003c6c048e43dbec70): локальный коммит `ed5b137` в `/tmp/lunobot-1/work/f4-extralite-1014-1422/f4` (ветка `tmp/19d3/extralite-vet-fix`, запушена): тесты с LuaPlugin/WasmPlugin (общий мок `luaTestHostAPI` вынесен в `host_api_test.go`; `identity_test.go`, `transport_lua*_test.go`, `transport_wazero_test.go`, части `permissions_test.go` и `scaffold_test.go` вынесены в `*_lua_test.go`) собираются только без extralite.
Проверка: sandbox 38579816203 (`go vet` с тегами extralite, `go vet` без тегов, `go test ./internal/plughost/`); репро на main — sandbox 38579255289.
Осталось: зелёный — `train.py land` из этого клона (трейлер `Lunobot-Task: extralite-vet-tests` уже есть), удалить этот файл и захват; красный — прочитать лог, дочинить (вероятно, ещё файлы с символами из `!extralite`).
