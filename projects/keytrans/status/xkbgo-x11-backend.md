# keytrans — новый бэкенд xkbgo-x11 (протокольный путь, без FFI)

## Решение: переносим в keytrans (не документируем)

Обоснование: готовая фабрика бэкендов, нет конфликта владения X11-соединением
(все бэкенды берут *xgb.Conn из OSInfo.XgbConn), путь точнее purexkb (реально
разрешённый keymap устройства, не RMLVO-эвристика), уже проверен в бою через
vtui#159/vtui#10.

## Готово локально, заблокировано на push — PAT не включает unxed/keytrans

Третий случай за сессию (после lazyhamster/Observer — чужой репо, и
unxed/wayland — уже решённый). На этот раз это СВОЙ репозиторий unxed/keytrans,
которого просто нет в Repository access list токена (тот же паттерн, что был
с wayland до фикса).

Обе ветки готовы локально, компаньон-PR в vtui подготовлен ЗАРАНЕЕ (не отложен):
- `keytrans` ветка `lunobot/19d368003c6c048e43dbec70/lunobot-1/keytrans-xkbgo-x11-backend`
  (коммит 4eab2d5): новый бэкенд первым в цепочке фабрики, тесты, README,
  xkb-go поднят до псевдо-версии после PR unxed/xkb-go#2.
- `vtui` ветка `lunobot/19d368003c6c048e43dbec70/lunobot-1/vtui-drop-x11-xkb-duplication`
  (коммит f6edcbe): убран x11_xkb_translator.go, x11_translator_select.go
  упрощён до прямого keytrans.NewX11Translator — устраняет дублирование.
  go.mod НЕ трогали (зависит от появления коммита в удалённом keytrans).
  **Важно: мержить только после keytrans-PR + бампа зависимости в vtui.**

Тексты PR готовы: scratchpad `keytrans_pr_body.md`, `vtui_pr_body.md`.

**Нужно от владельца:** добавить `unxed/keytrans` в Repository access list PAT.
