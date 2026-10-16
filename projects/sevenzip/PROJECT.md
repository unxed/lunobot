# sevenzip

- Код: https://github.com/unxed/sevenzip (форк bodgit/sevenzip: читатель и писатель 7z на Go; зависит от unxed/xz,
  сам используется unxed/archives, а через него — unxed/zipper и f4)
- Задачи: приходят из зависимых репозиториев (например unxed/f4#1731); issues в самом репозитории отключены
- PR: в ветку по умолчанию `write` (не `main`): ветка `lunobot/pr/<ключ>` -> PR -> мерж зелёного
- Режим публикации: PR (`lunobot/staging`/`quick.yml` нет)
- Отладка GitHub CI: да (компилируемый Go-проект, локально ничего не собирать). Обязательные проверки PR:
  `Coverage` (`go test -covermode=atomic ./...`, `coverage.yml`) и `Lint pull request` (`pr-lint.yml`)
- Язык общения: английский
- Особенности: заголовок PR и коммита — Conventional Commits (`fix(reader): …`, `feat: …`, `test: …`), иначе
  `Lint pull request` красный (тип `reader:` и т. п. не принимается); `build.yml` срабатывает только на PR в `main`,
  поэтому на PR в `write` полная golangci-lint-проверка не идёт — гоняй lint в песочнице f4, если нужен
- Покрытие: не проверялось
