# vtinput

- Код: https://github.com/unxed/vtinput (свой репозиторий владельца, не форк): разбор ввода виртуальных терминалов (VT, win32-input-mode, kitty, far2l).
- Задачи: тикеты и PR этого репозитория, плюс правки, которые нужны unxed/vtui и unxed/f4.
- Режим публикации: PR
- Отладка GitHub CI: да (есть платформенный код: `reader_windows.go`, `reader_plan9.go`; Windows-часть Linux-CI не проверяет)
- CI: `coverage.yml` (`go test ./...`, ubuntu) на push в main и на PR — обязательная проверка; матрицы ОС и `sandbox.yml` нет, поэтому Windows-код проверяют сборкой в CI потребителя (unxed/vtui) или отдельным разовым workflow.
- Зависимости: unxed/winkeys (`InputEvent`), golang.org/x/term, golang.org/x/sys, emmansun/base64. Новая версия winkeys — сначала тег winkeys, потом `go.mod` здесь.
- Релизы: ручной тег; схема: vX.Y.Z (последний v0.1.11 на 21-10-2026).
- Язык общения: по языку автора (PR uranic2 — английский).
- Паспорт заведён 21-10-2026 по § 2 («Репозитории-зависимости владельца»); строки в `INDEX.md` нет, её согласуют с владельцем.
