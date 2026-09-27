# keytrans

- Код: https://github.com/unxed/keytrans — не форк, оригинальный проект unxed
  ("pure go keyboard layout and text translation library for Unix windowing
  systems"), используется unxed/vtui для X11-раскладок (и не только).
- Архитектура: `x11_factory.go` — фабрика бэкендов, перебирает по порядку:
  `backend_xkbcommon.go` (FFI, purego) → `backend_x11xim.go` (FFI) →
  `backend_purexkb.go` (чистый Go, xkb-go.NewKeymapFromNames по RMLVO-именам
  из `_XKB_RULES_NAMES`) → `backend_dynamicxkb.go` → `backend_xkbcomp.go`
  (внешний бинарник + xkb-go) → `backend_corex11.go` (эвристики).
- Уже зависит от `github.com/jezek/xgb` и `github.com/unxed/xkb-go` (v0.1.8) —
  инфраструктура для протокольного пути уже есть, просто версия xkb-go
  старее той, что добавила пакет `x11` (GetMap/GetNames/GetControls,
  `x11.NewKeymapFromX11Device`) в рамках unxed/vtui#10.
- Задачи: тикеты этого репозитория.
- Тикеты уже открыты (2026-08-01): #1 (встроить xkeyboard-config для полной
  X11-независимости), #2 (баг Core X11 эвристик на 3+ раскладках), #3 (arm64
  трамплин для purego-фоллбека).
