# Coverage: generated widget properties

Путь: `/tmp/lunobot-2/work/vtui-coverage-properties-1015-0032/vtui`, commit `547ff17a41326e73306f5fdf2c953ed39ba782cd`.

Добавлен table-driven тест для сгенерированных `SetProperty`/`GetProperty` неохваченных виджетов, включая неверный тип, делегирование базовым свойствам и неизвестные свойства. Свежий артефакт main CI `38638350123` показывал `properties.go` на 100%, поэтому реальный остаток выбран в `properties_gen.go`; свойства `Window.autoSize` и `Window.center` намеренно read-only и тестируют текущие возвращаемые значения.

Следующий шаг: отправить commit в `tmp/19d3/vtui-properties-coverage`, запустить песочницу на Linux с `go test ./...` и golangci-lint v2.13.1 (`--new-from-rev=origin/main`), сверить SHA прогона. Если проверки зелёные и staging зелёный — `train.py land` из указанного клона; после завершения удалить этот status-файл и снять захват.
