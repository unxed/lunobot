# zip

- Код: https://github.com/unxed/zip
- Задачи: тикеты и PR этого же репозитория; форк, от которого зависит unxed/zipper
- PR: туда же, ветка -> PR -> мерж в main
- Зависимости: нет
- Покрытие: настроено и работает (28-09-2026, Лунобот-3): 100%. Задание CI
  `Coverage` в `.github/workflows/ci.yml` сливает covdata всех тестовых ячеек
  (6 hosted + FreeBSD) и само падает при любом непокрытом операторе (на main —
  5894 из 5894); `sys_other.go` намеренно в списке `UNBUILT`. С PR
  [#20](https://github.com/unxed/zip/pull/20) тот же `merged.txt` уходит в
  Codecov (OIDC, без CODECOV_TOKEN; `fail_ci_if_error: false`); публичный API
  `https://api.codecov.io/api/v2/gh/unxed/repos/zip/report/` — 100% (6852/6852
  строк). Добирать тесты под покрытие здесь нечего: цель § 7.4 достигнута,
  любой новый код без тестов уронит CI сам.
- Язык общения: английский (upstream-репозиторий)
- Особенности: правка API требует парной правки в zipper

Этот паспорт — то место, где живут отличия проекта от остальных.
