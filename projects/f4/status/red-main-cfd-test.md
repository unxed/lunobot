# f4 red main cfd559df0

Run `https://github.com/unxed/f4/actions/runs/39091749086`, head `cfd559df0d3fa08133673b6ff6b12cb236987102`, attempt 2 (rerun of failed jobs). Two test timeouts:

- `TestDriveMenuWatchRebuildsTheOpenMenu`, linux/amd64: open menu did not show plugged-in drive within 15 seconds (job 117570468489).
- `TestActionExecuteBatchExitRestartsShell`, windows/arm64: local ConPTY startup prompt did not arrive (job 117570468511).

Neither failing package/test was changed in this push; the commit changes `internal/panel/tree.go` and `tree_test.go`. Narrow diagnostic runs on the exact main SHA: linux/amd64 `39093413353`; windows/arm64 `39093415571`. Both were still running at last inspection; do not poll the same runs in this turn.

Next: classify from completed sandbox logs; if failures reproduce, investigate/fix in a branch and verify with required CI. If both pass, assess as runner/test flakiness and rerun main CI only if procedure calls for it. Keep urgent capture until main is no longer red.

18-10-2026 03:27 UTC: узкий linux/amd64 sandbox `39093413353` завершился успешно (`go test -count=1 -run ... ./internal/panel`, 0.080s), поэтому исходный timeout не воспроизвёлся изолированно. Windows/arm64 sandbox `39093415571` ещё выполнял PowerShell-команду при последней проверке; вывод недоступен, не опрашивать циклически.
