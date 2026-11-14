# f4 red train #2314 — govulncheck Go standard-library vulnerability

## Состояние

14-11-2026 20:04:29 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): `tick-all` identified red train [unxed/f4#2314](https://github.com/unxed/f4/pull/2314), run [#43627134649](https://github.com/unxed/f4/actions/runs/43627134649). Failure is `Quality / Run govulncheck`: GO-2026-6859 in `net/http`, found with Go 1.26.10, fixed in Go 1.26.11. `go.mod` on both `main` and train declares `go 1.26.6`; no code fix or train disposition was made. `tick-all` also reports 2.2h of staged work waiting for main (process incident).

## Осталось

Закрытый PR [unxed/f4#2315](https://github.com/unxed/f4/pull/2315) содержит исправление: Go toolchain обновлён до 1.26.11; полная матрица успешна на SHA `162f676c93cb307bff92b1df066ae695d1c646d9`. Мерж в `main` — `d23028e16335dcd711561bdb28a713d4d5059fc3`. `tick` закрыл красный поезд #2314 после продвижения main, затем влил main в staging. Для новой вершины staging `bb2652f6f6fde46e10e53073c6d798918e1c944f` идёт `quick` [#43636380330](https://github.com/unxed/f4/actions/runs/43636380330); не ждать результат, следующий `tick` продвинет поезд. Доезжание двух staged-коммитов до main ещё не подтверждено.


14-11-2026 20:19:49 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): корневая причина красного поезда устранена существующим зелёным PR #2315; старый поезд закрыт. Staging синхронизирован с main, новый quick запущен на точном head SHA; оставлено для следующего tick без ожидания CI.
