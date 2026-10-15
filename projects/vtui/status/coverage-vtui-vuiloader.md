# Coverage: VUI loader

Путь: `/tmp/lunobot-2/work/vtui-vuiloader-1015-0640`, commit `f334a6920d107bbda53fbc0be51ab638f98b57a4` (ветка-клон `main`, base `da756b91c`). Временная ветка для песочницы: `tmp/19d3/vui-loader-coverage-1015-0640`.

План: добавить регрессионные тесты ошибок чтения/JSON, валидации корня и узлов, компоновки/размеров окна, buddy/command-связей, преобразования значений и разбора command ID. Исходный файл — `vui_loader.go`; Codecov main показывал покрытие 61.99% (83 misses, 20 partials).

Локально выполнены только `gofmt` и `git diff --check`; тесты и сборка локально не запускались (PROJECT.md: `Отладка GitHub CI: да`).

Песочница https://github.com/unxed/vtui/actions/runs/38694477515 запущена на SHA `f334a6920d107bbda53fbc0be51ab638f98b57a4`; результат не опрашивался.

Следующий шаг: при следующем круге однократно проверить завершение этого прогона и совпадение SHA; затем выполнить `train.py covered` для коммита и `train.py land` из указанного клона, если прогон зелёный и staging остаётся зелёным. Команда песочницы: `go vet ./... && go test -count=1 -timeout 4m ./... && git fetch -q origin +refs/heads/main:refs/remotes/origin/main && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./...`.

Предыдущая формулировка запуска песочницы: `Запустить `sandbox.yml` на указанной временной ветке с командой `go vet ./... && go test -count=1 -timeout 4m ./... && git fetch -q origin +refs/heads/main:refs/remotes/origin/main && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./...`; сверить `headSha` с `f334a6920d107bbda53fbc0be51ab638f98b57a4`, не ждать результат. При зелёном прогоне — `train.py land` из указанного клона; затем удалить этот status-файл и захват. При красном — исправить и обновить запись до следующего запуска.
