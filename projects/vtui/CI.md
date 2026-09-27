# CI — vtui

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 04:00:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), PR https://github.com/unxed/vtui/pull/147 — нашёл дубль TestFitInside (старый в graphics_native_test.go, новый табличный в graphics_scale_test.go), убрал старый (f8fdecc), нашёл gosec G115 на int16-конверсиях в checkgroup_test.go, добавил #nosec с обоснованием (c262e94), жду свежий прогон

27-09-2026 04:50:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), PR https://github.com/unxed/vtui/pull/146 — subagent нашёл, что unxed уже форкнул neurlang/wayland с добавленным SetAppID (branch app-id, upstream PR neurlang/wayland#36 не смержен), запушил replace на псевдо-версию форка (6c351ce), жду свежий прогон
