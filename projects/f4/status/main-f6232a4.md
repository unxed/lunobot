# main f6232a4

Часть 1 из 2: исправлен wrapper `archiveTestingReader`, чтобы ZIP/7z extractor-ы сохраняли доступ к `io.ReaderAt` и `io.Seeker`; PR #1137 влит, merge commit `cd75f65`, post-merge main CI #4134 в очереди.

Часть 2: исправлены ошибки `go vet` в `vfs/trash_darwin_test.go` из прогона main #4128; коммит `fdd2252` отправлен в ветку `codex/f33f64cd91460430a21da326/lunobot-2/main-f6232a4-2of2`, quick #12 выполняется.
