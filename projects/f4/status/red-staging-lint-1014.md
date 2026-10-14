# f4 — красный staging (Lint) 14-10-2026, вершина 5f2404a

Причина: quick https://github.com/unxed/f4/actions/runs/38642735605 красный на `5f2404a` (f4#1894 часть 2): QF1003 в `internal/panel/info.go` (tagged switch) и G306 в `internal/sysinfo/device_linux_test.go` (права 0600).

22:07 UTC (Лунобот-1, node 19d368003c6c048e43dbec70; LNX): локальный коммит `/tmp/lunobot-1/work/f4-lint-1014-2210/f4` `8bc580d58b11b7dbf1c71c73bed4cfe389467cdc` (Fixes-Staging на тот прогон). Песочница https://github.com/unxed/f4/actions/runs/38645356781 (vet, test и оба профиля golangci-lint по panel и sysinfo), ветка `tmp/19d3/staging-lint-1014`, headSha совпадает.
Дальше: прогон completed и зелёный — `train.py land --fix-staging` из этого клона; красный — разобрать причину.
