# Красный main unxed/f4 059c5e62d

14-10-2026 03:20 UTC (Лунобот-1): прогон https://github.com/unxed/f4/actions/runs/38502498871 — `Race (shard 0)`: DATA RACE, отнесён к `TestStaticDirectActionsRegistered`. Чтение `os.Stdout` в `colorer4go.NewSession` (горутина фонового списка схем `settings.refreshSchemeChoices`, запущенная `TestSettingsEmbeddedHotkeyConfiguratorDraft`) против записи `os.Stdout` в cleanup `TestSimpleInline_ReturnsWithoutPauseAndLeavesRoomForOverlay`. Коммиты поезда (#1784 меню, #1463 сумма прописью) ни при чём — утечка горутины в тестах, порядок решил shuffle. Воспроизведено локально (1 из 15), исправление — счётчик `schemeRefreshes` + `settings.WaitSchemeRefreshes` в cleanup теста (0 из 30). В staging `c900fe6` (Lunobot-Task: red-main-059c5e62d). Перезапуск не делал: не инфраструктура.

Осталось: поезд с c900fe6 → зелёный main → удалить файл и снять захват.
