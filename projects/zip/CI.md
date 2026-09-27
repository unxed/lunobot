# CI log — unxed/zip (Lunobot-3)

## PR #17 — test: lock in Deflate level propagation through Updater.AppendHeader

- Branch: lunobot/lunobot-3/lunobot-3/1-updater-level-regression-test
- URL: https://github.com/unxed/zip/pull/17
- Pre-push local verification (since process note says no CI polling after
  opening the PR):
  - `go build ./...` — clean
  - `go vet ./...` — clean
  - `gofmt -l updater_level_test.go` — no output (already formatted)
  - `go test ./...` — ok (full suite, ~21s)
  - Regression sanity check: temporarily reverted the two hunks from
    commit c321598 in a local, uncommitted copy of register.go/updater.go,
    reran the two new tests — both failed with the expected "level ignored"
    messages; restored the fixed files (`git status --porcelain` clean
    afterward, only the new test file remained as an untracked addition).
- CI status: not polled per process note ("end your turn immediately — no
  CI polling"). Whatever workflow this fork's CI runs will pick up the push
  to the PR branch on its own.

## Issue #2 — closed without a PR

- No code change was made, so no CI run is associated with this ticket.
- Verification was local only: manual repro/benchmark scripts under
  /tmp/lunobot-3/{repro,repro2,repro3,bench} (scratch, not committed
  anywhere) plus the repo's own `go test ./... -run TestLevelAwarePooling`,
  which passed on a clean main checkout.
