# Красный main vtui: flaky `TestFrameManager_SizePolling`

## Причина

На `main` `3c04f85ea` красным завершился только `Test (darwin/amd64)`: `TestFrameManager_SizePolling` остановил цикл через фиксированные 300 мс, до обработки отложенного resize на медленном macOS-раннере. В frame остались размеры `0x0`, а screen buffer — `80x24`. Остальные jobs прошли.

## Сделано

- Ветка `lunobot/urgent/main-size-polling-91d8`, коммиты `a4831be` и `fd2688f`: тест синхронизирован с первым измерением размера и фактическим resize; два новых закрытия pipe явно отбрасывают неиспользуемый результат, чтобы пройти errcheck.
- PR [unxed/vtui#209](https://github.com/unxed/vtui/pull/209) открыт. Sandbox run [38369020559](https://github.com/unxed/vtui/actions/runs/38369020559) и quick прошли успешно.

## Осталось / Дальше

- Полный PR run #453 зелёный; PR #209 влит 13-10-2026 09:44:34Z (merge commit `bc84451`). На `main` запущен run #454; сохранить статус до проверки его результата. После зелёного результата удалить status-файл; после красного — диагностировать и исправить.
