# f4 red train #2314 — govulncheck Go standard-library vulnerability

## Состояние

14-11-2026 20:04:29 UTC (Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)): `tick-all` identified red train [unxed/f4#2314](https://github.com/unxed/f4/pull/2314), run [#43627134649](https://github.com/unxed/f4/actions/runs/43627134649). Failure is `Quality / Run govulncheck`: GO-2026-6859 in `net/http`, found with Go 1.26.10, fixed in Go 1.26.11. `go.mod` on both `main` and train declares `go 1.26.6`; no code fix or train disposition was made. `tick-all` also reports 2.2h of staged work waiting for main (process incident).

## Осталось

Inspect the CI toolchain selection and current `main` run; update to a Go patch release containing the fix (expected 1.26.11), run required checks on the exact SHA, then rerun `train.py tick unxed/f4`. Do not bisect/eject the f4#1148 train commits: the failure is the Go standard library vulnerability, not demonstrated to be caused by those changes. Close the train only if the selected fix cannot safely unblock it. Claim key: `f4/train-2314`.
