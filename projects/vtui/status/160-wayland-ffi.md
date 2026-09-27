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
