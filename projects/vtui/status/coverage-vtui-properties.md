# Coverage: generated widget properties

Путь: `/tmp/lunobot-2/work/vtui-coverage-properties-1015-0032/vtui`, commit `547ff17a41326e73306f5fdf2c953ed39ba782cd`.

Добавлен table-driven тест для сгенерированных `SetProperty`/`GetProperty` неохваченных виджетов, включая неверный тип, делегирование базовым свойствам и неизвестные свойства. Свежий артефакт main CI `38638350123` показывал `properties.go` на 100%, поэтому реальный остаток выбран в `properties_gen.go`; свойства `Window.autoSize` и `Window.center` намеренно read-only и тестируют текущие возвращаемые значения.

Песочница: https://github.com/unxed/vtui/actions/runs/38660645009, `headSha` совпадает с коммитом, при первой проверке `queued`. Ветка: `tmp/19d3/vtui-properties-coverage`.

Следующий шаг: на следующем круге проверить завершённый прогон (не опрашивать в цикле). Если проверки зелёные и staging зелёный — `train.py land` из указанного клона; после завершения удалить этот status-файл и снять захват. Красный результат — исправить причину в этом же step-клоне и повторить песочницу.
