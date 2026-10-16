# crescent — гонка Client.Close() и readLoop на cmd.Wait (§ 5 п. 5а, пункт 7)

16-10-2026 01:55 UTC (Лунобот-1, node 19d368003c6c048e43dbec70): ГОТОВО — PR https://github.com/unxed/crescent/pull/4 влит (merge `42857bd`; job'ы linux и windows ci.yml зелёные на `02f91c4` и на push, и на pull_request, PR не отставал от main, прогон main отменён по § 7.3). readLoop — единственный вызывающий cmd.Wait, Close ждёт канал done; тест TestCloseIsRaceFreeReleasesPendingCallsAndRepeats.

## Осталось
1. Жалобой (§ 12, PR `complaint/*`, review отдельным субагентом) убрать пункт 7 из списка § 5а в LUNOBOT.md; пункты 5 и 6 остаются. После этого удалить этот файл.
2. Запись crescent в projects/INDEX.md не заведена — согласуется с владельцем (§ 2); вопрос владельцу не задан, проект ведётся как зависимость владельца.
