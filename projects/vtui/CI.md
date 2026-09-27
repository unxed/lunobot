# CI — vtui

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 03:41:03 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), PR #146 (Wayland SetAppID) — после мержа main возник конфликт в vmenu.go (main вынёс отрисовку сепаратора в drawSeparator, f4 #263); смержил main, перенёс #nosec G115 в общий хелпер (2fb8a3d), запушено — жду свежий прогон

27-09-2026 04:10:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/vtui/issues/136 (часть 1 из 4 — Wayland SetFont), PR [#148](https://github.com/unxed/vtui/pull/148), коммит `021d074`, прогон [#293](https://github.com/unxed/vtui/actions/runs/36292827724)

27-09-2026 15:55:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/vtui/issues/136 (часть 2 из 4 — X11 SetFont), PR [#149](https://github.com/unxed/vtui/pull/149) — Lint падал дважды (36293709479, 36293725076) на gosec G115 в x11_host.go:650-651 (`uint32(cols*cellW)`/`uint32(rows*cellH)` в новом SetFont); задокументировал инвариант (cols/rows/cellW/cellH всегда малые неотрицательные) через `#nosec G115` в стиле symchar.go/screenbuf.go, коммит `33d5ea5`, запушено в ту же ветку, прогон [pull_request](https://github.com/unxed/vtui/actions/runs/36294628447) — жду прогон (по договорённости — без поллинга в этом ходе)

27-09-2026 15:35:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), тикет https://github.com/unxed/vtui/issues/136 (часть 3 из 4 — Win32 SetFont), PR [#150](https://github.com/unxed/vtui/pull/150), ветка `lunobot/19d368003c6c048e43dbec70/lunobot-3/136-gui-font-hotswap-3of4`, коммит `b4c5c29`, прогон [#297](https://github.com/unxed/vtui/actions/runs/36294381784) — запушено, жду прогон (по договорённости — без поллинга в этом ходе)
