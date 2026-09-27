# zipper/sevenzip CI log

## unxed/sevenzip PR #8 (branch lunobot/e2d630e0524e1c081b5e1572/lunobot-3/22-7z-header-compression, base write)

- Pushed 2026-09-27. Not built/tested locally (no-local-builds policy) -- gofmt -l
  was run locally (formatting/parse check only, not a build) and reported clean.
- Per process note: pushed the branch, opened the PR, commented on the ticket, and
  ended the turn without polling GitHub Actions. CI status on PR #8 is unknown as of
  this entry -- check `gh pr checks 8 --repo unxed/sevenzip` in a later pass before
  merging.

## unxed/sevenzip PR #9 (branch lunobot/19d368003c6c048e43dbec70/lunobot-3/coverage-write-fix-header-tests, base write)

- Custom task: `write` branch's `Coverage` workflow was red from three real test
  failures caused by #7+#8 interacting (see DISPATCH.md for full diagnosis), not
  from a coverage-percentage gate -- confirmed `.github/workflows/coverage.yml`
  has no threshold at all, just `go test ./...` + a report upload.
- Fixed `TestZstdEncodedHeader` (decompress the now-always-LZMA2-compressed
  header via the generic `folderReader` before recompressing as zstd for the
  fixture) and the two `require.Equal(t, idEncodedHeader, id)` type-mismatch
  failures in `writer_header_compress_test.go` (cast to `byte(idEncodedHeader)`).
  Also added `internal/util` unit tests (owner explicitly permitted a
  coverage-focused commit this time).
- Pushed 2026-09-27. Not built/tested locally (no-local-builds policy) -- gofmt -l
  was run locally (formatting/parse check only, not a build); one alignment
  issue in the new `internal/util/byte_reader_test.go` was auto-fixed by
  `gofmt -w`, then `gofmt -l .` came back clean.
- Per process note: pushed the branch, opened the PR, and ended the turn without
  polling GitHub Actions. CI status on PR #9 is unknown as of this entry --
  check `gh pr checks 9 --repo unxed/sevenzip` in a later pass.
