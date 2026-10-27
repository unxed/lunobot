# vtui

- Код: https://github.com/unxed/vtui
- Задачи: тикеты и PR того же репозитория, плюс правки, которые требуются для [f4](../f4/PROJECT.md)
- PR: с 27-09-2026 vtui тоже на staging/train (`lunobot/staging` +
  `lunobot/train/vtui/<timestamp>`, `train.py land`), как f4 — не
  отдельная ветка -> PR за каждый шаг. Проверено 28-09-2026 по факту
  существования `origin/lunobot/staging` и смерженных
  `lunobot/train/vtui/*` PR в репозитории.
- Быстрая проверка: `quick.yml` (push в `lunobot/**`) с 28-09-2026 гоняет параллельный job `Lint` — golangci-lint v2.13.1, `--new-from-rev=origin/main`, как в ci.yml; находки gosec ловятся до поезда.
- Зависимости: нет
- Покрытие: настроено (28-09-2026, Лунобот-3). Задание `Coverage` в
  `.github/workflows/ci.yml` (`go test -covermode=atomic ./...`, linux/amd64,
  CGO_ENABLED=0) гоняется на PR (поезда) и main; профиль — артефакт
  `coverage` и, с 28-09-2026, загрузка в Codecov (OIDC, без CODECOV_TOKEN,
  `fail_ci_if_error: false`). Публичный API
  `https://api.codecov.io/api/v2/gh/unxed/repos/vtui/report/` заработает после
  первого прогона на main с этой правкой (до того отвечает «branch main not in
  our records»); до тех пор цифры — `gh run download <run main CI> -n coverage`.
  В `line_coverage` второе число — состояние строки (0=hit/1=miss/2=partial).
  На main (run 36416612450) — 69.5% операторов, цель 80%. Наименее покрытые
  файлы с логикой без GUI: `properties.go` (32%), `far2l_extensions.go` (38%),
  `validator.go` (52%), `protocol.go` (54%), `internal/uba/core.go` (58%),
  `vui_loader.go` (63%); `semantic.go` поднят с 43.6% почти до 100%
  (Lunobot-Task `coverage-vtui-semantic`). Нативные хосты (x11/wayland/gogpu/
  ebiten/cocoa/win32) и `cmd/*` покрываются плохо по природе — их не брать.
- Язык общения: по языку автора тикета
- Особенности: библиотека, от которой зависит f4; правка, ломающая её API,
  требует парной правки в f4
- Песочница `sandbox.yml` исполняет `-f command=…` через shell (`bash -c`
  на Linux/macOS, `Invoke-Expression` pwsh 7 на Windows): `&&`, `|`, `for` работают
- Проверка в песочнице перед `land` обязана включать lint, как у f4: `git fetch -q origin
  +refs/heads/main:refs/remotes/origin/main && go run
  github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1 run --new-from-rev=origin/main ./...`
  (14-10-2026 golden-тест `cmd/vtui-replay` с `defer f.Close()` приземлился с зелёным `go test`
  и покрасил `quick` на `Lint`/errcheck — исправление пришлось приземлять `land --fix-staging`).
- Релизы: после мержа в main тегируй следующий последовательный `vX.Y.Z`
  (смотри `gh api repos/unxed/vtui/tags --jq '.[0].name'`) на коммите мержа
  и пушь тег — только так f4 сможет подтянуть исправление через go.mod.
  Это разрешённое исключение из общего запрета на релизы (правка идёт
  в зависимость, которую ты же чинишь).

Этот паспорт — то место, где живут отличия проекта от остальных. Не хватает ответа
на вопрос, который встал в работе, — дополни паспорт вместе с правкой по задаче.
- Теги из облачной сессии (08-10-2026): `git push origin vX.Y.Z` и `POST git/refs` отвечают 403 (прокси не пускает refs/tags). Тогда f4 берёт коммит main как pseudo-версию (`go get github.com/unxed/vtui@<sha>`, коммит с `Touch:`), а тег ставит тот, кто может (владелец или сессия с правом на теги); после тега go.mod f4 переводят на него.
- Живые тесты X11 (16-10-2026): тест, которому нужен X-сервер, сам пропускается без `DISPLAY` (так проходят `quick` и CI), а в песочнице гоняется под Xvfb: `sudo apt-get install -y -qq xvfb >/dev/null 2>&1; CGO_ENABLED=1 xvfb-run -a go test -race -count=1 -run <имя> -v . 2>&1 | tail -n 60` (образец — `TestX11DragSourceBorrowedPointerLive`, два клиента на одном сервере; `go vet` и lint — отдельными командами перед этим, как выше).
- Форки зависимостей (решение владельца 21-10-2026, чат основного инстанса): `replace` в `go.mod` на форк допускается только на форки владельца (`unxed/*`) и постоянных контрибуторов Zoin и sogonov; правки прочих авторов (в том числе uranic2) идут PR в репозиторий владельца или в upstream, а при нужде — через форк владельца. Цитаты: «там заменяются зависимости на кучи его форков, это не вариант конечно (ну может кроме как когда так делает Zoin, который постоянный контрибутор)»; «ветку sogonov использовать можно, это постоянный контрибьютор и он там всерьез занялся»; «для остального свою». Пример: `replace github.com/gogpu/gogpu => github.com/sogonov/gogpu` в vtui допустим; форки uranic2/winkeys, uranic2/vtinput, uranic2/gogpu — нет (unxed/vtui#207, unxed/lunobot#241).
