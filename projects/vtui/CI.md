# CI — vtui

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 20:34:00 Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент), cmd/cocoa-smoke "shutdown" — PR [#161](https://github.com/unxed/vtui/pull/161) влит: причина была в самом smoke-тесте (гонка performSelectorOnMainThread:waitUntilDone:YES в closeWindow() safety-net после того, как applicationShouldTerminate: уже запустил асинхронный quit), не в cocoa_gui_darwin.go — close()/hostClosed уже были корректны. Подтверждено зелёным на реальном macOS CI (run 36347244667)
