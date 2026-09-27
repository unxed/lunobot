# vtui — cmd/cocoa-smoke: "shutdown: RunInGUIWindow returned while the driver was still running"

## История

Найдено 27-09-2026 ~20:10 владельцем через живой прогон `cmd/cocoa-smoke` на macOS
(источник — не найден в failed runs репозитория напрямую, возможно ручной прогон
или прогон, отменённый до попадания в историю). Лог идентичен во всех трёх
предъявлениях (~20:10, ~20:19, ~20:37) — стабильно воспроизводится, не флейк.

Все проверки из фикса f4#1571 части 1 (PR unxed/vtui#157: use-after-free,
невалидный UTF-8 title, `applicationShouldTerminate:` → NSTerminateLater,
направление `ResizeGrid`) — зелёные, включая "terminate reply" и "after-shutdown
calls". Падает только последняя, новая проверка:

```
PASS  RunInGUIWindow: returned <nil> after 4.415s
PASS  after-shutdown calls: ... (GetWindowPosition correctly reports ok=false)
FAIL  shutdown: RunInGUIWindow returned while the driver was still running
```

Похоже на гонку: `RunInGUIWindow` возвращает управление раньше, чем реально
завершается цепочка `close()`/`vtuiReplyTerminate:`/`hostClosed`, добавленная
в #157 для асинхронного `NSTerminateLater`.

## Кто ведёт

Дежурный по main vtui (в рамках задачи "поставь субагентов дожидаться зелёных
CI... и исправить всё что упадёт") взял эту находку 27-09-2026 ~20:16. Ветка
`lunobot/19d368003c6c048e43dbec70/lunobot-1/vtui-main-watch-cocoa-smoke-shutdown-race`
существует и обновляется (последний коммит `dbece0f9`), PR ещё не открыт на
момент этой записи. Владелец дважды подтвердил, что баг стабильно
воспроизводится — это не гонка окружения CI, реальный порядок операций.
