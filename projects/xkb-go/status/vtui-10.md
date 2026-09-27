# unxed/vtui#10 — статус (X11 keymap без CGO/xkbcomp)

Части 1-2 из 3 (wire-protocol + публичное API `x11.NewKeymapFromX11Device`) —
готовы и влиты: unxed/xkb-go#2.

## Апстрим (godesktop/xkb-go) — подготовлено, не отправлено (блокер PAT)

Ветка готова и запушена: `unxed/xkb-go` → `upstream-x11-getmap-getnames-getcontrols`
(от актуального `upstream/main`, апстрим не разошёлся с точки ветвления PR#2).
По пути нашли и исправили реальный баг: файлы ссылались на module path форка
(`github.com/unxed/xkb-go`) вместо апстримного (`github.com/thegrumpylion/xkb-go`) —
без этого PR не собрался бы в апстриме.

`gh pr create --repo godesktop/xkb-go` отказал: "Resource not accessible by
personal access token" — тот же класс блокера, что и с lazyhamster/Observer
(см. status/1563.md в проекте f4): токен может пушить в `unxed/*`, но не может
создавать PR в чужих репозиториях.

Готовый текст PR лежит в scratchpad прошлого субагента (не в этом репозитории) —
нужно либо расширить права PAT, либо открыть вручную по ссылке:
https://github.com/godesktop/xkb-go/compare/main...unxed:xkb-go:upstream-x11-getmap-getnames-getcontrols?expand=1
(заголовок: "x11: retrieve XKB keymaps from an X server without CGO/xkbcomp")

Проверено: в godesktop/xkb-go нет пересекающихся по теме открытых PR/issues (есть
#3, #4, issue #1 — все про другое, multi-layout/group offsets).

## Часть 3 из 3 (проводка в vtui, фоллбек keytrans)

В работе параллельно (отдельный субагент), см. DISPATCH.md на момент чтения.
