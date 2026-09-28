# vtui

- Код: https://github.com/unxed/vtui
- Задачи: тикеты и PR того же репозитория, плюс правки, которые требуются для [f4](../f4/PROJECT.md)
- PR: с 27-09-2026 vtui тоже на staging/train (`lunobot/staging` +
  `lunobot/train/vtui/<timestamp>`, `train.py land`), как f4 — не
  отдельная ветка -> PR за каждый шаг. Проверено 28-09-2026 по факту
  существования `origin/lunobot/staging` и смерженных
  `lunobot/train/vtui/*` PR в репозитории.
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
- Релизы: после мержа в main тегируй следующий последовательный `vX.Y.Z`
  (смотри `gh api repos/unxed/vtui/tags --jq '.[0].name'`) на коммите мержа
  и пушь тег — только так f4 сможет подтянуть исправление через go.mod.
  Это разрешённое исключение из общего запрета на релизы (правка идёт
  в зависимость, которую ты же чинишь).

Этот паспорт — то место, где живут отличия проекта от остальных. Не хватает ответа
на вопрос, который встал в работе, — дополни паспорт вместе с правкой по задаче.
