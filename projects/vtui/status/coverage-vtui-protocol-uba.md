# Покрытие `protocol.go` и `internal/uba`

## Состояние
Локальный коммит `390d4d86f3bbf7284f0ccef4d5a51c01e4d72489` находится в `/tmp/lunobot-2/work/vtui-coverage-20261020-0350/vtui`; рабочий каталог существует. Песочница запущена: https://github.com/unxed/vtui/actions/runs/39363907744 (run 39363907744, head `390d4d86f3bbf7284f0ccef4d5a51c01e4d72489`, in_progress по единственной проверке статуса).

## Проверить
Репозиторий: `unxed/vtui`; ref: `tmp/19d3/vtui-coverage-protocol-uba`; ОС: `ubuntu-latest`.
Команда: `git fetch -q origin +refs/heads/main:refs/remotes/origin/main && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./... && go test . ./internal/uba`.

20-10-2026 03:21:43 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): тесты добавлены для protocol calls и bidi line reordering. Осталось проверить точный коммит в песочнице, затем приземлить через `train.py land`.

20-10-2026 03:22:16 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): run 39363907744 на точном SHA запущен; результат не опрашивался повторно.
