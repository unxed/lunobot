# pureffi

- Код: https://github.com/unxed/pureffi
- Задачи: issues и PR этого репозитория; обслуживание pureffi — прямое поручение владельца.
- Модуль Go: `github.com/ebitengine/purego` (`go.mod`); API совместим с `ebitengine/purego`, реализация использует goffi.
- Зависимости: `go.mod` требует `github.com/go-webgpu/goffi v0.6.2`, но заменяет его на `github.com/unxed/goffi v0.1.9`.
- PR: в `unxed/pureffi`, ветка -> PR -> мерж в `main`
- Режим публикации: PR (`lunobot/staging` и `quick.yml` отсутствуют; default branch — `main`)
- Отладка GitHub CI: да (Go library; сборки и тесты выполняются только в GitHub Actions, локально не собирать)
- CI: `.github/workflows/ci.yml`, Go `1.26.x`. Проверки workflow: Code Formatting, Vet, Platform Matrix (`scripts/check-platforms.sh`), Test (Ubuntu/Windows/macOS, `CGO_ENABLED=0/1`), Benchmarks и CI Success. Отдельный job Coverage запускается, но не входит в `ci-success`.
- Branch protection API недоступен (403), поэтому конфигурация обязательных status checks отдельно не подтверждена.
- Язык общения: английский (README и открытые issues)
- Покрытие: целевой порог не указан; не проверялось

Этот паспорт — источник особенностей проекта; неизвестное не выводить из предположений.
