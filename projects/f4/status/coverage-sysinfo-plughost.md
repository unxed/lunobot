# coverage-sysinfo-plughost — покрытие internal/sysinfo и internal/plughost (Лунобот-1, § 5 п. 6)

20-10-2026 19:49 UTC. Локальный коммит (только тесты, 6 новых файлов): клон `/tmp/lunobot-1/work/f4-cov-sysinfo-plughost/f4`, sha `a89d76a6442e5f1550cbb349b5a25dbf7058e5ec`, трейлер `Lunobot-Task: coverage-sysinfo-plughost`.
Маршрут `[land]` после зелёных прогонов песочницы. Ветка песочницы: `tmp/19d3/cov-sysinfo-plughost` (репозиторий unxed/f4, headSha совпадает с коммитом выше).

Прогоны `sandbox.yml` (unxed/f4, ref `tmp/19d3/cov-sysinfo-plughost`):
- ubuntu-latest: https://github.com/unxed/f4/actions/runs/39486596688 — команда: `set -o pipefail; git fetch -q origin +refs/heads/main:refs/remotes/origin/main && test -z "$(gofmt -s -l internal/plughost internal/sysinfo)" && go vet ./internal/plughost/ ./internal/sysinfo/ && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./internal/plughost/ ./internal/sysinfo/ && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --config .golangci-strict.yml ./internal/plughost/ ./internal/sysinfo/ && go test -race -count=1 -shuffle=on ./internal/plughost/ ./internal/sysinfo/ && go test -count=1 ./cmd/f4/`
- windows-latest: https://github.com/unxed/f4/actions/runs/39486601713 — команда: `go vet -unsafeptr=false ./internal/plughost/ ./internal/sysinfo/ && go test -count=1 ./internal/plughost/ ./internal/sysinfo/`
- macos-latest: https://github.com/unxed/f4/actions/runs/39486606523 — команда: `go vet ./internal/plughost/ ./internal/sysinfo/ && go test -count=1 ./internal/plughost/ ./internal/sysinfo/`

Осталось/Дальше: все три прогона зелёные — `python3 train.py land` из клона выше, затем снять захват «покрыть тестами пакеты internal/sysinfo, internal/plughost», удалить ветку `tmp/19d3/cov-sysinfo-plughost` и этот файл. Красный — починить тесты в том же клоне (только тесты, продукт не менять), коммит пересоздать и перепрогнать.
