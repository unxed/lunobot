# vtui#160 — Wayland-клавиатура без FFI (libxkbcommon)

## Найдено

Хуже, чем предполагалось: `window.DisplayCreate` в форке `unxed/wayland`
(`window/window_linux.go`) жёстко падал без `libxkbcommon.so` — FFI через
purego/goffi был безальтернативным путём (не "тяжёлый фолбэк"), причём дёргался
на каждое нажатие клавиши/модификатор, не только на разбор keymap.

## Готово, но не запушено — блокер PAT (новый класс, серьёзнее прежних)

Патч написан и закоммичен ЛОКАЛЬНО в клоне субагента: `github.com/unxed/xkb-go`
(`NewKeymapFromString`) стал основным путём разбора `wl_keyboard.keymap`,
libxkbcommon — фоллбек только для dead-key compose. Плюс обновление `replace`
в `vtui/go.mod` на новый коммит форка.

**PAT этой сессии не может ПУШИТЬ в `unxed/wayland`** (не только "не может
создавать PR в чужом репо", как было с Observer/xkb-go — тут собственный форк,
`git push` и Git Data API оба дают 403, хотя `GET /repos/unxed/wayland`
показывает `push: true` для аккаунта). Похоже на неполный allowlist
fine-grained токена (тот же repository-access-list симптом, что раньше, но
на этот раз задевает пуш в СВОЙ форк, не только сторонние PR).

Сохранено в scratchpad прошлой сессии (не в git):
`unxed-wayland-vtui-160-wayland-ffi.bundle` (git bundle с веткой и коммитом),
`0001-window-use-xkb-go-for-Wayland-keymap-parsing-and-key.patch`.

Отписался в тикете:
- https://github.com/unxed/vtui/issues/160#issuecomment-5859673969 (находка)
- https://github.com/unxed/vtui/issues/160#issuecomment-5859702768 (готово, упёрлось в PAT)

**Нужно от владельца:** добавить `unxed/wayland` в Repository access list PAT
(или дать push через другой токен/SSH), дальше по накатанной: пуш ветки →
обновить пин в vtui → зелёный ci.yml → PR в vtui → апстрим-PR в
neurlang/wayland (per правило владельца — доработки wayland слать в апстрим).

## ЗАВЕРШЕНО (кроме апстрима)

Блокер снят владельцем (PAT получил доступ к unxed/wayland). Патч запушен,
vtui/go.mod обновлён, CI зелёный (один известный флейк Cocoa darwin/amd64,
не связан, прошёл на повторе). PR в vtui: https://github.com/unxed/vtui/pull/162.

Апстрим-ветка готова и запушена в unxed/wayland: `upstream/xkb-go-wayland-keymap`
(один коммит, от чистого master апстрима, не смешана с ещё не смерженным SetAppID).
`gh pr create --repo neurlang/wayland` отказал — права PAT на СТОРОННИЙ репозиторий
(другой класс ограничения, чем было с unxed/wayland). Текст готов в scratchpad
(`neurlang_wayland_PR_TEXT_ready_to_open.md`), открыть вручную:
https://github.com/neurlang/wayland/compare/master...unxed:wayland:upstream/xkb-go-wayland-keymap
