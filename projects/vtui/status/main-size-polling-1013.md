# Красный main vtui: flaky `TestFrameManager_SizePolling`

## Причина

На `main` `3c04f85ea` красным завершился только `Test (darwin/amd64)`: `TestFrameManager_SizePolling` остановил цикл через фиксированные 300 мс, до обработки отложенного resize на медленном macOS-раннере. В frame остались размеры `0x0`, а screen buffer — `80x24`. Остальные jobs прошли.

## Сделано

- Ветка `lunobot/urgent/main-size-polling-91d8`, коммиты `a4831be` и `fd2688f`: тест синхронизирован с первым измерением размера и фактическим resize; два новых закрытия pipe явно отбрасывают неиспользуемый результат, чтобы пройти errcheck.
- PR [unxed/vtui#209](https://github.com/unxed/vtui/pull/209) открыт. Sandbox run [38369020559](https://github.com/unxed/vtui/actions/runs/38369020559) и quick прошли успешно.

## Осталось / Дальше

- Полный PR run #451 завершился красным только на Lint: оба новых `pw.Close()` без обработки результата (errcheck); исправлено в `fd2688f`. Новый полный PR run #453 зарегистрирован и ещё queued. На следующем круге, если он завершён зелёным, влить PR и проверить `main`; если красный — исправить причину. До вливания PR исходный красный `main` считается неустранённым.
