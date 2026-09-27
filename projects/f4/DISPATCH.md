# DISPATCH — f4


27-09-2026 15:02:56 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «https://github.com/unxed/f4/issues/1563, часть 1 из N: wasi-sdk сборка модуля isoimg (Observer) в отдельном форке, CI доказывает компиляцию в .wasm» по прямому указанию владельца [urgent: «поступи с ним по инструкции Лунобота» — прямая команда владельца]

27-09-2026 15:11:00 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «https://github.com/unxed/f4/issues/444, эмпирическая проверка PTY-последовательности pty_darwin.go на macOS-раннере через sandbox.yml, подбор рабочей альтернативы» по прямому указанию владельца [urgent: «поступи с ним по инструкции Лунобота» — прямая команда владельца]

27-09-2026 16:08:23 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «https://github.com/unxed/f4/issues/1571, часть 1 из 2: правки дефектов Cocoa-бэкенда в unxed/vtui (use-after-free, невалидный UTF-8 в title, отказ от logout/restart/shutdown, направление ResizeGrid) со smoke-проверками в cmd/cocoa-smoke на macOS CI, затем новый тег vtui» по прямому указанию владельца [urgent: «возьми https://github.com/unxed/f4/issues/1571 отдельным субагентом» — прямая команда владельца]

27-09-2026 16:12:00 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), работаю над https://github.com/unxed/f4/issues/1563 (часть 1 из N: wasi-sdk сборка isoimg, субагент ещё ждёт прогон sandbox.yml)

27-09-2026 16:12:00 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), работаю над https://github.com/unxed/f4/issues/444 (эмпирическая проверка PTY-последовательности на macOS-раннере, субагент ещё в работе)

27-09-2026 16:13:26 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «https://github.com/unxed/f4/issues/1572, красный main: multiarc real-exec тесты (7z/tar/unzip) на macOS и Windows — доделать существующую ветку claude/project-thread-xnolva (не компилируется, item 6), проверить через sandbox.yml, запушить в main» по § 5 п. 2 [urgent: по § 5 п. 2 — красный main]

27-09-2026 16:13:26 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «https://github.com/unxed/f4/pull/1570, починить golangci-lint (33 находки: errcheck/gosec/unused в новом пакете plugins/observer)» по прямому указанию владельца [urgent: «https://github.com/unxed/f4/pull/1570 падает» — прямая команда владельца]

27-09-2026 16:23:00 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «красный main: `go.mod` f4 не содержит `replace github.com/neurlang/wayland => github.com/unxed/wayland ...`, которую объявляет unxed/vtui v0.1.370 — replace не транзитивен, поэтому у f4 резолвится апстримный neurlang/wayland без SetAppID, `wayland_host.go:157: host.win.SetAppID undefined`; добавить такую же replace-директиву в go.mod f4, обновить go.sum» по § 5 п. 2 [urgent: по § 5 п. 2 — красный main]

27-09-2026 16:24:31 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «красный main a51901d» по § 5 п. 2 — коммит "Update vtui gofmt" бампнул vtui до v0.1.370, чей wayland_host.go зовёт host.win.SetAppID(), а f4's go.mod пинует чистый upstream github.com/neurlang/wayland v0.4.4 (там ещё нет SetAppID — апстрим-PR neurlang/wayland#36 не смержен); у vtui в его СОБСТВЕННОМ go.mod есть replace на форк unxed/wayland, но replace-директивы зависимостей игнорируются, когда модуль используется как библиотека — их нет в f4's go.mod, что и валит буквально всё (Build/Test/Vet/Race/Lint/cloudfox/ios/android) [urgent: по § 5 п. 2 — красный main]
