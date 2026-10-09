# f4

- Код: https://github.com/unxed/f4
- Задачи: тикеты и PR этого же репозитория
- PR: туда же, ветка -> PR -> мерж в main
- Зависимости: [vtui](../vtui/PROJECT.md), правку иногда нужно сделать сначала там
- Язык общения: по языку автора тикета
- Отладка GitHub CI: да
- Диагностический workflow: sandbox.yml
- Режим публикации: поезда
- Покрытие: Codecov, `go test -coverpkg=./...`; целевое — 70 % по проекту и 80 % на своих
  изменениях. В `.github/codecov.yml` проверки помечены informational, то есть PR они
  не блокируют: держать число вверх — обязанность Лунобота, а не гейта
- Особенности: сборка и тесты только на CI GitHub, локально ничего не собирать
  - `quick.yml` (с cc93367a) гоняет golangci-lint отдельным job'ом параллельно с `check`:
    `.golangci.yml` с `--new-from-rev=origin/main` и строгий `.golangci-strict.yml` по всему
    дереву, v2.13.1, как в `build.yml`. Lint-находка теперь красит `quick` сразу после `land`,
    а не всплывает только в поезде. Песочница перед `land` должна гонять те же два прогона:
    `git fetch -q origin +refs/heads/main:refs/remotes/origin/main && go run
    github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./...`
    и `... run --config .golangci-strict.yml`
  - `quick.yml` также гоняет job `Format checks` (параллельно с `check`): `gofmt -s -l .`,
    `go run ./tools/langfmt -check internal/i18n/lang/*.lng` и actionlint, как в `build.yml`.
    Формат `.lng` и gofmt красят `quick` сразу после `land`, а не поезд (#1642). Перед `land`
    локально допустимы только `gofmt -s -l .` и `langfmt -check`.
- Проверка в песочнице перед `land` обязана включать `go test ./cmd/f4/` — там глобальные
  аудит-тесты (`TestCommandPaletteProductionCommandSurfaceInventory` требует внести в карту
  аудита каждый новый тип с `ProcessKey`, `TestNoNewHardcodedUIStrings` и др.), которые
  падают от правок в ЛЮБОМ пакете. 28-09-2026 это дважды за час сделало staging красным
  (#1606 шаг 7, #312 шаг 1): песочница авторов гоняла только их пакеты.
  - Песочница `sandbox.yml` (с 2cc80354): команда разбирается настоящим shell —
    `bash -c` на Linux/macOS, `Invoke-Expression` pwsh 7 на Windows, так что `&&`,
    `|`, `;`, кавычки и циклы работают без обходов
  - Windows: `go vet` звать с `-unsafeptr=false` (как в `build.yml`), иначе ложные
    срабатывания на Win32-вызовах
  - Windows, полный `go test ./...` в песочнице — двумя шардами:
    `-run '^Test([A-D]|$)'` и `-run '^Test[^A-D]'`, одним прогоном может не уложиться
    в лимит времени джоба
- Замер покрытия (28-09-2026 10:48 UTC, Лунобот-3, по § 7.4, свежее прошлого замера
  10:08 UTC — сам агрегат по main опять не сдвинулся: между замерами появился только
  один новый «complete»-отчёт, `eb113ef4`, но у него `sessions=2` — частичный прогон,
  не вся матрица, — поэтому самым свежим ПОЛНЫМ отчётом (`sessions=9`) остаётся тот же
  `321a5945`, что и в прошлой записи): покрытие проекта на main — 69.18 %
  (commit `321a5945`, sessions=9). Данные взяты через
  `api.codecov.io/api/v2/gh/unxed/repos/f4/report/?sha=<sha>` (токен не понадобился)
  и агрегированы вручную по второму уровню пути файла (`internal/panel`,
  `plugins/cloudfox` и т. д.), не только по первому. **Важно про формат JSON**: во
  втором элементе пары `line_coverage` — состояние строки (0=hit, 1=miss, 2=partial),
  не счётчик.

  Топ-3 пакета по абсолютному числу непокрытых содержательных строк (misses+partials),
  ИСКЛЮЧАЯ уже основательно проработанные этим флотом (`internal/terminal`,
  `internal/app`, `internal/ttyx`, `internal/panel`, `internal/editor`, `plugins/git`,
  `plugins/observer`, `plugins/envman`, `plugins/netfox`, `plugins/mediainfo`,
  `plugins/cloudfox`, `plugins/ios`, `vfs`, `plugins/archive` — часть правок уже в
  `lunobot/staging`/трейне и ещё не видна в этом срезе main):
  1. `internal/media` — 2987 строк, 63.91 %, 1078 непокрытых (ниже цели 70 % и
     наибольший абсолютный разрыв среди непроработанных пакетов) — **взято в работу
     этим же замером**, см. коммит `Lunobot-Task: coverage-internal-media` в
     `lunobot/staging`. Внутри пакета хуже всего `image_view.go` (571 строк, 68.30 %,
     181 непокрытых) и `overlay_console.go`/`overlay_x11.go` (протокольная графика,
     низкая отдача от юнит-тестов); тестами этого захода покрыты
     `ImageGallery.galleryKey` (все клавиши движения), `GalleryPath`, no-op ветки
     `showGallery`/`showTile` и — главное — реальный асинхронный путь
     `requestThumb` (откат с превью на полную декодировку и обратная отправка в UI
     поток), который раньше ни один тест не проходил по-настоящему. 28-09-2026 15:44
     UTC, Лунобот-3: второй заход по тому же пакету, `audio_decode.go` (343 строки,
     56.56 %, 149 непокрытых — второй по размеру разрыв внутри пакета после
     `image_view.go`), коммит `Lunobot-Task: coverage-internal-media-audio_decode`
     (`811751837a22096b51391801da5245e7a6fcca06` в `lunobot/staging`): `openExternalAudio`/
     `ffprobeAudio` (путь через ffmpeg/ffprobe для AAC/Opus/AMR и т. п.) не имели ни
     одного теста — добавлены через подмену `tools.go`'s `toolPaths` на `/bin/true`/
     `/bin/false` вместо реального PATH (POSIX-only, `!windows`, по образцу
     `internal/editor/external_editor_process_unix_test.go`); также `decodeMP3`/
     `decodeVorbis` не имели тестов вовсе — добавлен разбор заведомо не-кодека под их
     расширением. Не трогали `decodeVorbis`/`flacPCM` happy-path (валидный поток
     руками не собрать без риска сломать тест вслепую) — это ещё один возможный заход.
  2. `internal/fileops` — 3337 строк, 74.95 % (уже выше цели), 836 непокрытых.
  3. `plugins/android` — 2234 строки, 65.26 %, 776 непокрытых.

  Следующие по размеру разрыва, ниже цели 70 %: `internal/fusefs` (1694 строки,
  58.74 %, 699 непокрытых), `internal/dialog` (2308 строк, 70.88 %, на грани цели,
  672 непокрытых), `internal/plughost` (2163 строки, 71.89 %, 608 непокрытых),
  `plugins/visren` (1861 строка, 71.52 %, 530 непокрытых), `internal/macro`
  (1034 строки, 69.05 %, 320 непокрытых), `internal/sysinfo` (865 строк, 67.28 %,
  283 непокрытых).

Этот паспорт — то место, где живут отличия проекта от остальных. Не хватает ответа
на вопрос, который встал в работе, — дополни паспорт вместе с правкой по задаче.

## vendorHash в flake.nix

Любой коммит, меняющий `go.mod`/`go.sum` (bump зависимости, прямая/косвенная), обязан в том же коммите обновить `vendorHash` в `flake.nix`: иначе красным станет поезд (джобы «vendorHash matches go.mod/go.sum» и «flake checks (Home Manager module)»). Автопочинка в CI есть только для пуша в `main` (шаг «Update vendorHash»), для PR и поездов CI лишь печатает нужное значение: сообщение `vendorHash is stale. Set vendorHash = "sha256-…"` лежит в аннотациях упавшего джоба (`gh api repos/unxed/f4/check-runs/<job id>/annotations --jq '.[].message'`, доступно ещё до конца прогона). Значение берут оттуда из прогона PR/поезда с теми же `go.mod`/`go.sum`, что у вершины staging, и приземляют коммитом с `Fixes-Staging:`/`Lunobot-Task:` (29-09-2026, поезд unxed/f4#1683: vtui v0.1.381 и xz-прямая зависимость без нового хэша). Пока хэш не получен из CI, вместе с bump в коммит не попасть; поэтому bump `go.mod` идёт отдельным коммитом, а сразу после первого красного джоба хэш вносится следующим `land`.


С 29-09-2026 (Lunobot-Task `vendorhash-autosync`) автопочинка есть и для `lunobot/staging`: job `nix-vendor-hash` в `quick.yml` на каждый push в staging проверяет хэш, если `go.mod`/`go.sum` отличаются от `main`, и при расхождении сам коммитит исправленный `vendorHash` поверх текущей вершины staging (трейлеры `Lunobot-Task: vendorhash-autosync` и `Fixes-Staging:`; до зелёного `quick` на этом коммите `tick` поезд не режет) и запускает `quick` на staging через `workflow_dispatch` (push токеном Actions других workflow не запускает). Воркер `flake.nix` руками больше не правит: bump `go.mod` приземляют как обычно, хэш появится сам в течение нескольких минут; не появился — смотреть job `nix-vendor-hash` последнего `quick` на staging. Ловушка: пока этого коммита ещё нет, `tick` может успеть вырезать поезд без него (окно — время nix-сборки, единицы минут против порога 30 минут).

Линтер gosec (job `Lint`) даёт G703 («path traversal via taint analysis») на каждый новый `os.WriteFile(path, …)`/`os.Create` с путём не из литерала — в коде и в тестах. Сразу ставь над строкой `// #nosec G703 -- <откуда путь: профиль пользователя / временный каталог теста>` (образец: internal/editor/colorer.go, internal/dialog/settings_portable.go); иначе staging краснеет на `quick` (08-10-2026 дважды: highlight.ini, farcolors.ini).

Перед `land` в клоне f4 всегда гоняй то, что `quick.yml` гоняет в «Format checks» (не требует сети, секунды): `test -z "$(gofmt -s -l .)"` и `go run ./tools/langfmt -check internal/i18n/lang/*.lng` (исправление — `go run ./tools/langfmt -w internal/i18n/lang/*.lng`, он только переставляет записи по порядку en.lng; новые ключи вставляй в том же месте, что в en.lng). Новые тексты Settings Center (`SettingsCenter.*`) требуют переводов во ВСЕХ 23 языковых файлах (`TestSettingsTranslationsComplete`), остальные ключи — только en и ru (остальные падают на английский). Локальный golangci-lint в песочнице (2.5.0) слишком старый для Go 1.26.6 и не запускается: gosec ловится только в CI, поэтому для каждой записи файла по нелитеральному пути ставь `#nosec G703`, для `int16(...)`/`uint16(...)` от int — `#nosec G115` (08-10-2026: три красных staging из-за этого и langfmt).

Перед `land` новой UI-вставки гоняй ещё `go test ./cmd/f4` (12 с): там аудит командной палитры (`command_palette_coverage_test.go`: каждый новый приёмник `ProcessKey` — запись в `commandPaletteProcessKeyAudit` и +1 к `commandPaletteF4Surfaces`; новый `vtui.NewVMenu` — запись в `commandPaletteNewVMenuAudit`) и `TestNoNewHardcodedUIStrings` (базовая линия литералов подписи: новую подпись клавиши/кнопки вроде `"F9"` в литерале `vtui.KeyBarLabels{...}` не пиши — ставь по индексу или бери из lng). Staticcheck в CI (Lint) придирается к `var x int = -1` (QF1011), лишнему `list.ListBox.OnKeyDown` через встраивание (QF1008) и неиспользуемым полям (08-10-2026).


Меняешь отрисовку или цвета панели (`internal/panel`) — перед `land` прогони весь пакет `go test ./internal/panel` (≈50 с), а не только свои тесты: 08-10-2026 `TestFileSystemPanel_FastFind_Rendering` ждал старый цвет строки ввода фильтра и краснил staging после «Filter window: edit-field colour…».

Конфликт «main → staging» в go.mod/go.sum/flake.nix (Иван обновляет зависимости прямо в main, CI-бот пересчитывает vendorHash: 08-10-2026 это случилось дважды за час): в клоне `git merge origin/main`, затем `git checkout --ours go.mod go.sum flake.nix` (у staging vtui — псевдоверсия с кнопкой f4#1782 и upstream neurlang/wayland без fork-replace), в go.mod поднять версии остальных зависимостей до значений main (`git diff ...origin/main -- go.mod`, строки zip/zipper и т.п.), `GOFLAGS=-mod=mod go mod tidy && go build ./...`, коммит и `git push origin <ветка>:lunobot/staging`; vendorHash пересчитает CI-автокоммит. Как только vtui получит новый тег с этой кнопкой — вернуть тег и убрать расхождение (тег из облака запушить нельзя).

Директива `go` в go.mod не выше Go из nixpkgs (сейчас 1.26.7): job «vendorHash matches go.mod/go.sum» собирает через nix с GOTOOLCHAIN=local и падает на «go.mod requires go >= …» (08-10-2026, моя правка до 1.26.9). Уязвимости stdlib (govulncheck в Quality) лечатся версией Go в `go-version` workflow (setup-go) — её можно поднимать независимо; уязвимости модулей — `go get` нужной версии.

Известное ограничение (f4#1774, закрыт автором 09-10-2026 без правки): нативный Wayland-бэкенд размыт при масштабе вывода > 1 (KDE Plasma 200%). Причина в neurlang/wayland@37f4fac (window/window_linux.go: `bufferScale = 1` на строках 303 и 3524, `SurfaceEnter`/`SurfaceLeave` пустые на 611–613, `output.scale` читается, но не применяется), vtui готов (WaylandHost.Resize считает scale из физических/логических размеров). Исправление — в библиотеке (enter/leave → max output.scale → set_buffer_scale + физический буфер; дробный масштаб — wp_fractional_scale_v1), а у бота доступ только к unxed/f4 и unxed/vtui; обход: `--gui=gogpu`. Если владелец решит делать — тикет открыть заново.

Отзывчивость интерфейса (09-10-2026, f4#1832): всё, что `GetMenuBar`, отрисовка панели и `Enabled`/`Visible`-функции строк меню делают на каждый кадр и нажатие (vtui зовёт меню 2–3 раза на клавишу), не должно ходить по `Entries`, в файловую систему или в плагин на каждый вызов — пользователи сразу замечают «жуткие тормоза» в папке из десятков тысяч файлов. Коммит f4#1814 (динамическое затемнение строк) именно так сломал навигацию. Правило: такое состояние опрашивается по штампу (панель, курсор, число строк) и не чаще раза в 250 мс, выделение читается один раз за проход (`FileSystemPanel.MemoizeSelection`), а на новое действие в меню нужен тест, который СЧИТАЕТ обходы (`panel.SelectionWalks`), как `TestMenuBarCostDoesNotGrowWithTheFolder`, а не меряет время.
