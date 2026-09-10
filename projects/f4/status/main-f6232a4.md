# main f6232a4

Часть 1 из 2: исправлен wrapper `archiveTestingReader`, чтобы ZIP/7z extractor-ы сохраняли доступ к `io.ReaderAt` и `io.Seeker`; коммит `a5ab969` отправлен в ветку `codex/f33f64cd91460430a21da326/lunobot-2/main-f6232a4-1of2`, PR #1137, CI #4133 в очереди.

Осталась часть 2: исправить ошибки `go vet` в `vfs/trash_darwin_test.go` из прогона main #4128.
