# Красный main vtui `2ca4a1cb1`: Race, `TestFrameManager_SizePolling`

Обновлено 14-10-2026 07:31 UTC, Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; субагент).

## Причина

Прогон main [38528293854](https://github.com/unxed/vtui/actions/runs/38528293854) (#461): job Race упал на `TestFrameManager_SizePolling` (`framemanager_test.go:1309: terminal-size poller did not resize the frame`); DATA RACE в логе нет. Коммит `2ca4a1cb1` трогает только `edit_bind.go`, `edit_bind_test.go`, `vreactive/README.md` — новый код ни при чём. Второе падение этого теста после unxed/vtui#209 (`main-size-polling-1013.md`). Найдена гонка в самом тесте: мок `GetTerminalSize` посылал `sizeRead` до чтения `mockW/mockH`, тест успевал записать 100x30 до того, как поллер прочитал базовый размер, — поллер брал 100x30 базой и изменения не видел.

## Сделано

- Коммит `1589f99` в клоне `/tmp/lunobot-1/work/vtui-redmain-1014-0729/vtui`, ветка `lunobot/urgent/vtui-main-race` от main `7d73940`: мок сначала читает размер, потом сигналит.

## Дальше

- Ветка запушена, PR [unxed/vtui#214](https://github.com/unxed/vtui/pull/214) открыт, прогон PR [#463](https://github.com/unxed/vtui/actions/runs/38528946427) и песочница [38528917774](https://github.com/unxed/vtui/actions/runs/38528917774) (`go vet . && go test -race -run TestFrameManager_SizePolling -count=30 .`) — результат не проверен; обе строки в CI.md.
- Зелёные — влить #214 по § 7.3 (ветка из BRANCHES.md, этот файл удалить). Песочница красная — тест падает и по другой причине: читать лог.
- Прогон main 38528293854 после завершения: если #214 ещё не влит — `gh run rerun 38528293854 --failed -R unxed/vtui`.
