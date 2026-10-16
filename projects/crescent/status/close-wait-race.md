# crescent — гонка Client.Close() и readLoop на cmd.Wait (§ 5 п. 5а, пункт 7)

16-10-2026 01:50 UTC (Лунобот-1, node 19d368003c6c048e43dbec70): PR https://github.com/unxed/crescent/pull/4 открыт (ветка `lunobot/pr/close-wait-race`, SHA `02f91c4`, прогон ci.yml 38837259075, строка в CI.md). readLoop — единственный вызывающий cmd.Wait, Close ждёт канал done; тест TestCloseIsRaceFreeReleasesPendingCallsAndRepeats; обход в TestClientSeesSpontaneousResetBeforeResetsAt убран. Локально не собирали (Отладка GitHub CI: да).

## Осталось
1. Прочитать ВСЕ job'ы ci.yml на SHA PR (go test -race, vet linux/windows, репетиция, Xvfb, Wine, Windows). Зелёные и PR не отстал от main — влить (§ 7.3), удалить ветку, строки CI.md/BRANCHES.md.
2. После мержа — жалобой (§ 12, PR `complaint/*`) убрать пункт 7 из списка § 5а в LUNOBOT.md; пункты 5 и 6 остаются.
3. Запись crescent в projects/INDEX.md не заведена — согласуется с владельцем (§ 2); вопрос владельцу не задан, решение по умолчанию: проект ведётся как зависимость владельца.
