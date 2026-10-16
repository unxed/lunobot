# archives

- Код: https://github.com/unxed/archives (форк mholt/archives; `SevenZip.Extract` строится на unxed/sevenzip;
  используется unxed/zipper и f4)
- Задачи: приходят из зависимых репозиториев (например unxed/f4#1731); issues в самом репозитории отключены
- PR: в ветку по умолчанию `write`: ветка `lunobot/pr/<ключ>` -> PR -> мерж зелёного
- Режим публикации: PR (`lunobot/staging`/`quick.yml` нет)
- Отладка GitHub CI: да (компилируемый Go-проект, локально ничего не собирать). Проверки PR: `ubuntu-latest`,
  `windows-latest`, `macos-latest` (`go test -race ./...`) и `coverage`
- Язык общения: английский
- Bump зависимостей (`unxed/sevenzip`, `unxed/xz`): `go.mod` и две строки `go.sum`; хэши берём из
  `https://sum.golang.org/lookup/github.com/unxed/<модуль>@<версия>`, без локального `go`
- Покрытие: не проверялось
