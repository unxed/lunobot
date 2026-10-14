# f4 — красный staging, 14-10-2026

План: исправить регрессионные проверки после смены Drive-menu shortcut с Ctrl на Shift, проверить точный коммит в GitHub sandbox и приземлить его через `train.py land --fix-staging`.

14-10-2026 18:06:28 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): локальный коммит `/tmp/lunobot-2/work/red-staging-f4-1014-1804/f4` `715c1d65b65830a36099bd46843230ca850d1399`. Исправлены старые integration tests `internal/app/drive_tools_move_test.go`, которые всё ещё посылали Ctrl+Up/Down и из-за этого падал staging после коммита `384a47a`. Следующий шаг: sandbox `go vet ./internal/app && go test ./internal/app` и линтеры проекта; сверить headSha, затем `land --fix-staging` с тем же `Fixes-Staging`.

14-10-2026 18:07:11 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): sandbox https://github.com/unxed/f4/actions/runs/38612407480 запущен с `go vet`, `go test` и обоими профилями golangci-lint; headSha совпадает с `715c1d65b65830a36099bd46843230ca850d1399`. После завершения — проверить результат и при успехе приземлить починку через `train.py land --fix-staging`; при неуспехе разобрать точную причину. Захват красного staging сохраняется.
