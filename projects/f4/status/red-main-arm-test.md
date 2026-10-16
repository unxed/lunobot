# f4 red-main-arm-test

Проблема: main SHA `08bf54637fda40e98a76aa6cedef1287d786209b` упал на `TestDriveMenuWatchRebuildsTheOpenMenu` только на linux/arm64. Попытка 2 также завершилась ошибкой; sandbox run `38884014435` на том же SHA завершился успешно.

Шаг: увеличено окно ожидания теста с 5 до 15 секунд и заменён повторный `time.After` на один `time.Ticker`.

Каталог клона: `/tmp/lunobot-2/work/red-main-1016-1017/f4`
Коммит: `09ad236b27b7e79b0a7f1714ac04f786db9671b4`
Ветка: `lunobot/urgent/main-flake-19d3`; PR: https://github.com/unxed/f4/pull/1988

Проверка: локальные сборки и тесты запрещены паспортом; шаг ожидает обязательный CI в PR.
Прогон полной матрицы: https://github.com/unxed/f4/actions/runs/38886648759 (выполняется); quick: https://github.com/unxed/f4/actions/runs/38886617775 (выполняется).
Дальше: после завершения CI проверить все обязательные гейты; зелёный проверенный SHA влить, иначе исправить в той же ветке.
