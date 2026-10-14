# Красный main unxed/f4 60ee6e81a

14-10-2026 00:20 UTC (Лунобот-1): прогон https://github.com/unxed/f4/actions/runs/38486624556 — упал только `Test (windows/arm64)`: `TestActionExecuteBatchDoesNotReturnPanelsEarly`, «local ConPTY startup prompt did not arrive» через 5.03 с (`pty_windows_panel_test.go:84`). Разница с последним зелёным main `c0da7c890` — только `internal/macro` (115c6ea, регистр символов макроса): к ConPTY/cmd.exe отношения не имеет. Причина — 5 с на первый prompt cmd.exe мало для arm64-раннера под нагрузкой пакета. Исправление (не пропуск): `localConPTYStartTimeout = 30s` для ожидания ConPTY и первого prompt, ожидание кончается сразу с prompt; в staging `a6b3ece` (Lunobot-Task: red-main-60ee6e81a). Перезапуск упавшего задания уже сделан до меня (попытка 3, запущена 00:11:19) — свой не делал.

Осталось: дождаться попытки 3 и поезда с a6b3ece; при зелёном main — удалить этот файл и снять захват.
