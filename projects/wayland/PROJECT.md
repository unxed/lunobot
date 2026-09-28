# wayland

- Код: https://github.com/unxed/wayland — форк `neurlang/wayland` (чистый Go-клиент
  Wayland-протокола + бэкенды окон на linux/darwin/js/windows). У `unxed/f4` и
  `unxed/vtui` на этот форк `replace` в `go.mod` (нужен `Window.SetAppID` для Wayland-
  бэкенда vtui).
- Задачи: тикеты этого репозитория, а также находки из `unxed/f4` (например
  unxed/f4#1607 — довести до мержа брошенную ветку `SetAppID`, см. историю тикета).
- PR: ветка → PR → мерж, как обычно (§ 7.1–7.3), **кроме** правок самой CI-
  инфраструктуры (`.github/workflows/**`) — их по прямому указанию владельца можно
  коммитить/пушить напрямую в `master` этого форка, пока CI только строится и
  проверять PR всё равно нечем.
- **До 28-09-2026 в этом форке не было CI вообще** (не было `.github/workflows`) —
  это и стало причиной unxed/f4#1607 (смерженный без единой проверки PR #1 несколько
  раз терялся). Заведён `.github/workflows/ci.yml`: `build-vet` (матрица `go build`
  + `go vet` под linux/windows/js-wasm (native ubuntu-latest, cross-compile
  CGO_ENABLED=0) и darwin (**macos-latest**, не кросс-компиляция — у
  `window/window_darwin.go` часть функций реально требует cgo-мост в
  `window_cgo_darwin.go`, тег `darwin && cgo`, так что CGO_ENABLED=0 недостаточен;
  macos-latest бесплатен для публичного репо) и `e2e-smoke` (поднимает headless
  `weston --backend=headless-backend.so` прямо в джобе `ubuntu-latest` и гоняет
  против него `go-wayland-ci-smoke` — новый минимальный клиент на пакете `window`,
  без cairo/xkbcommon/EGL, только чтобы получить `*xdg.Toplevel` и вызвать
  `SetAppID`; проверка регрессии — `WAYLAND_DEBUG=1` на самом `weston` (сервер
  печатает входящий протокольный трафик так же, как и клиент — это свойство самого
  libwayland, не этого Go-порта) и `grep set_app_id` по его логу, у клиентской
  стороны в этом порту протокольного трейсинга нет).
  Зелёный прогон, подтверждающий PR #1 (уже смержен в master):
  https://github.com/unxed/wayland/actions/runs/36363850004
- **`go build`/`go vet` не покрывают весь `./...` буквально** — исключён
  `go-wayland-cube` (сломан независимо от этого тикета: пиннутая версия
  `vulkan-go` не совпадает по API, `undefined: vulkan.CreateWaylandSurface` и
  т.п., даже на нативном linux с cgo — отдельная, более глубокая проблема, не
  тронута). По пути найдены и исправлены как раз таки платформенные дыры теми
  же средствами, что чинили `window_darwin.go` в PR #1 — добавлены теги
  `linux`/`darwin`/`!windows,!js` файлам `libdecor/*.go`, `libwayland/wayland.go`,
  `wl/context_*_test.go`, которые раньше собирались (или должны были собраться)
  на всех платформах без разбора; `go vet` запускается с `-unsafeptr=false`
  (purego FFI) и `-asmdecl=false` (`external/swizzle/swizzle_amd64.s`, старое
  именование FP-офсетов).
- **Staging/поезда (§ 7.2) здесь не подключены** — `train.py`/`lunobot-guard.yml`
  рассчитаны на уже существующую полную матрицу (f4/vtui); в этом маленьком форке
  до появления `ci.yml` гонять было нечего. Пока здесь нет отдельного `sandbox.yml`
  для итерации — только что заведённый `ci.yml` и есть первая точка опоры; заводить
  staging/train имеет смысл, только если объём работы здесь вырастет настолько,
  что общая полная матрица станет узким местом (пока это один PR раз в долгое время).
  До тех пор — обычный цикл ветка → PR → мерж (или прямой пуш для самой CI-
  инфраструктуры, см. выше), без `land`/`[land]`.
- Язык общения: английский (апстрим-стиль форка, PR/коммиты на английском — см.
  уже смерженный/открытый PR #1).
- **Апстрим**: `neurlang/wayland` — токен здесь только `pull`, `createPullRequest`
  падает 403 (как в unxed/f4#1593 для `godesktop/xkb-go`/`jezek/xgb`). Уже открыт
  `neurlang/wayland#38` (xkb-go keymap, тем же путём — форк→ветка→ссылка на compare).
  `SetAppID` тоже нужно туда отправить — ветка `upstream-set-app-id` в этом форке
  (коммит `ace75ef`, чистый cherry-pick поверх `upstream/master`) уже готова,
  copy-paste текст PR и compare-ссылка — в unxed/f4#1609 (не удалять эту ветку как
  брошенную, она не в неймспейсе `lunobot/*`, см. BRANCHES.md).
- Висящая ветка `lunobot/19d368003c6c048e43dbec70/lunobot-1/vtui-160-wayland-ffi`
  («window: use xkb-go for Wayland keymap parsing and key translation», см.
  unxed/f4#1610) ребейзнута на master, прогнана через `ci.yml` (зелено с первого
  раза после починки отставшего `go.sum` для только что добавленной зависимости
  `xkb-go` — исходный коммит трогал `go.mod`, но не `go mod tidy`) и смержена
  через unxed/wayland#2: https://github.com/unxed/wayland/commit/fa6821d86beef46b2fd4240672498b00d3ba61b5.
  Ветка удалена.
