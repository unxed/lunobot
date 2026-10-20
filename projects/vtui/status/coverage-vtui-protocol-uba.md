# Покрытие `protocol.go` и `internal/uba`

## Состояние
Коммиты `390d4d86f3bbf7284f0ccef4d5a51c01e4d72489` и `8dec1d672bec9f53878e09cc842d8d980d0f1627` находятся в `/tmp/lunobot-2/work/vtui-coverage-20261020-0350/vtui`; рабочий каталог существует. Первая песочница на исходном SHA завершилась ошибкой нового теста вложенных bidi-уровней. Ошибка выявила пропуск элемента при переходе между диапазонами уровней; регрессионный тест оставлен, исправлен шаг обхода. Новый точный SHA запушен во временную ветку; повторная песочница ещё не запущена.

## Проверить
Репозиторий: `unxed/vtui`; ref: `tmp/19d3/vtui-coverage-protocol-uba`; ОС: `ubuntu-latest`; SHA: `8dec1d672bec9f53878e09cc842d8d980d0f1627`.
Команда: `git fetch -q origin +refs/heads/main:refs/remotes/origin/main && go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./... && go test . ./internal/uba`.

20-10-2026 03:21:43 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): тесты добавлены для protocol calls и bidi line reordering. Осталось проверить точный коммит в песочнице, затем приземлить через `train.py land`.

20-10-2026 03:22:16 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): run 39363907744 на точном SHA запущен; результат не опрашивался повторно.

20-10-2026 03:33:55 UTC (Лунобот-2, node 19d368003c6c048e43dbec70; LNX): run 39363907744 завершился ошибкой `TestComputeReordering/nested_runs`: фактический порядок `[0 4 2 3 1 5]` вместо `[0 4 3 2 1 5]`. Исправлен переход к следующему диапазону в `computeReordering`; новый коммит `8dec1d672bec9f53878e09cc842d8d980d0f1627` запушен в тот же временный ref. Повторить заданную песочницу на новом SHA.
