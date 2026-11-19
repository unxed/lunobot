# f4 red staging — follow-up tests survived the feature revert

## Состояние

19-11-2026 00:37:04 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): `tick-all` found `lunobot/staging` red at `a78df40a0bf8bfee6564296ee440af77429fa16d`; quick run [44406821382](https://github.com/unxed/f4/actions/runs/44406821382), attempt 2, fails `TestThemeListFillsTheFieldsAndFallsBackToCustom` because it expects the Appearance theme selector removed by the preceding staging revert. The original train comprised feature commit `02219eb`, test update `91a8c7c`, and follow-up test `31415f9`; the revert removed only the feature, leaving tests changed from main. A single test-only rollback commit `958236cbc144ef4d20fded7af4ca86ee1fbd0dbb` restores both test files to `origin/main`, parked on unxed/f4 branch `tmp/19d3/f4-red-staging-1119-0029`. Exact diagnostic sandbox command ran on ubuntu-latest; run [44430082890](https://github.com/unxed/f4/actions/runs/44430082890), exact SHA `958236cbc144ef4d20fded7af4ca86ee1fbd0dbb`, was `in_progress` at the last check.

## Осталось

Проверить результат диагностического прогона один раз. Если зелёный на точном SHA — приземлить `958236c` через `train.py land --fix-staging` с тем же `Fixes-Staging:`; иначе разобрать новую причину. Ветка парковки удаляется после приземления.

19-11-2026 00:38:53 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): retro `train.py health unxed/f4` подтвердил, что staging остаётся red на run 44406821382; три коммита старше main ждут более 5 ч, process incident сохраняется. `unxed/vtui` staging green и синхронен с main. Исправляющий quick на точном SHA `958236cbc144ef4d20fded7af4ca86ee1fbd0dbb` запущен как sandbox run [44430082890](https://github.com/unxed/f4/actions/runs/44430082890); его исход в этом круге не опрашивался. Следующий бот: проверить завершённый exact-SHA run; при success — `train.py land --fix-staging`, иначе продолжить диагноз; механизм поездов требует отдельного разбора в ретро.