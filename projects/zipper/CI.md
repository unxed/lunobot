# zipper #17 - CI tracking

- PR: https://github.com/unxed/zipper/pull/29
- Branch: lunobot/06d4bb9a877260b805ef354b/lunobot-3/17-7z-progress-bar
- Local checks before push: `go build ./...` succeeded (repo root, current
  main + changes). Local investigation also ran the built CLI directly to
  reproduce/diagnose the ticket (create/extract 7z and zip archives, compare
  progress bar output) - this was diagnostic only, done before realizing the
  no-local-builds policy applies here; no further local go build/go test was
  run after committing the fix. `go test ./archive/...` for the new tests was
  intentionally left to GitHub Actions CI on the PR, not run locally.
- Per process note: pushed branch and opened PR, then stopped - no CI
  polling done in this turn. Follow up in a later turn to check
  https://github.com/unxed/zipper/actions for the PR's run and address any
  CI failures on the two new tests (TestFallbackProgressReader_TracksBytes,
  TestIssue17_FallbackExtractor7zProgress) if they occur.
- Status: awaiting CI.
