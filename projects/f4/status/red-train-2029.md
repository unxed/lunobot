# f4: красный поезд 2029 (Windows-тест меню дисков)

Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), 17-10-2026 ~10:48 UTC. Поезд `lunobot/train/f4/261017-1008` красный на `Test (windows/amd64 A-D)`: `TestDriveMenuCaptionsLiveInTheSeparators` не узнаёт строку «Windows Registry │ …» (после unxed/f4#1148 за именем идут колонки).

Починка (только тест): локальный коммит `88e5f27ddfd898beb38a92743cae23791937d10a` в клоне `/tmp/lunobot-1/work/r17-1037/f4`, ветка проб `tmp/19d3/red-train-2029`. Песочница: windows-latest https://github.com/unxed/f4/actions/runs/39025983650, ubuntu (vet + оба lint + test) https://github.com/unxed/f4/actions/runs/39025985777.

Дальше: обе зелёные → `train.py land` из этого клона, затем `train.py close-train unxed/f4 2029` (виновника не выбрасывать), следующий тик режет новый поезд; убрать ветку `tmp/19d3/red-train-2029` и этот файл.

10:48 UTC: поезд 2029 закрыт `tick`, виновным выбран 797f43e (Staging-Revert 4650169), хотя падал только тест. Итоговый коммит для `land` — `ef23be3` в том же клоне, ветка `land-1148` (откат отката + правка теста, дерево идентично проверенному 88e5f27); ему же нужен зелёный Windows-прогон 39025983650 и `quick` на 4650169.
