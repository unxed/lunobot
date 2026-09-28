# keytrans

- Код: https://github.com/unxed/keytrans — не форк, оригинальный проект unxed
  ("pure go keyboard layout and text translation library for Unix windowing
  systems"), используется unxed/vtui для X11-раскладок (и не только).
- Архитектура: `x11_factory.go` — фабрика бэкендов, перебирает по порядку:
  `backend_xkbgo_x11.go` (чистый Go, читает реальный keymap устройства по
  проводному XKB-протоколу через `xkb-go/x11.NewKeymapFromX11Device` —
  GetMap/GetNames/GetControls, без CGO/FFI) → `backend_xkbcommon.go` (FFI,
  purego) → `backend_x11xim.go` (FFI) → `backend_purexkb.go` (чистый Go,
  xkb-go.NewKeymapFromNames по RMLVO-именам из `_XKB_RULES_NAMES`) →
  `backend_dynamicxkb.go` → `backend_xkbcomp.go` (внешний бинарник + xkb-go)
  → `backend_corex11.go` (эвристики поверх сырого core-протокола, без
  XKB-осведомлённости о полном keymap — последний фоллбэк).
- Зависит от `github.com/jezek/xgb` и `github.com/unxed/xkb-go` (v0.1.9,
  уже включает пакет `x11` с GetMap/GetNames/GetControls,
  `x11.NewKeymapFromX11Device`, добавленный в рамках unxed/vtui#10; PR #6
  этого репозитория уже использует его для `backend_xkbgo_x11.go`).
- Задачи: тикеты этого репозитория.
- Тикеты уже открыты (2026-08-01): #1 (встроить xkeyboard-config для полной
  X11-независимости — первый срез оценки размера сделан, PR
  unxed/keytrans#8, см. `status/1.md`), #2 (баг Core X11 эвристик на 3+
  раскладках — фикс влит в main через PR unxed/keytrans#7), #3 (arm64
  трамплин для purego-фоллбека — сам трамплин уже реализован без
  ассемблера в `variadic_syscall.go`, padding-трюк вместо реального
  trampoline, см. его комментарий; PR unxed/keytrans#9 добавляет
  юнит-тесты этой логики и arm64-проверки в CI, тикет не закрыт ботом по
  § 3 п. 3).
- `xkb-go` (в контексте #1): `Context` в `context.go`/`rules.go` читает
  XKB-данные через `os.Open`/`os.ReadFile` по реальным путям файловой
  системы, а не через `fs.FS`/`embed.FS` — вшить данные `go:embed`
  напрямую нельзя, нужен шаг «распаковать embed.FS во временный/кэш
  каталог → `Context.PrependIncludePath(dir)`» внутри `keytrans`, без
  правки самой `xkb-go` (публичного API достаточно). Флаг
  `ContextNoEnvironmentNames` в `xkb-go` задокументирован как влияющий на
  чтение `XKB_DEFAULT_*`, но фактически нигде не реализован (no-op) —
  источник RMLVO без X11-соединения тоже надо строить в `keytrans`.
- `backend_corex11.go`: `xkb.ParseX11GetControlsReply` (из `xkb-go`,
  переиспользуется без правки библиотеки) даёт число реально настроенных
  XKB-групп через сырой запрос `GetControls`; `lookup()` использует его,
  чтобы выбрать между старой эвристикой (только 2 группы, два разных
  магических раскладки индексов) и равномерной раскладкой блоков
  `width = symsPerKeycode/numGroups` для 3-4 групп.
- CI: единственный workflow — `.github/workflows/coverage.yml`
  (`go test -covermode=atomic ./...` на push в main/master и на каждый PR).
  Нет `lunobot/staging`/`quick.yml`/`train.yml` — `Режим публикации: PR`.
