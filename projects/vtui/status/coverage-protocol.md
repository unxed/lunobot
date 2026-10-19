# Покрытие protocol (кастомная задача § 5.6)

- Клон: `/tmp/lunobot-2/work/vtui-coverage-20261019-01/vtui`
- Коммит: `f5140571f7c245a0f0c9847df92a5e7646eb1c21`
- Шаг: тесты ошибок JSON-кодирования, записи в транспорт и отправки после закрытия `ProtocolSession`.
- Проверки: форматирование Go и `git diff --check`; тесты запрещены локальной политикой vtui. Sandbox run [39194876493](https://github.com/unxed/f4/actions/runs/39194876493) запущен на точном клоне из `tmp/19d3/coverage-vtui-protocol`, при последней проверке `queued`.
- Дальше: запушить точный коммит во временную ветку, проверить `go test ./...` через `sandbox.yml`, затем выполнить `train.py land` при зелёной проверке.
- 19-10-2026 03:28 UTC

- 19-10-2026 05:29 UTC: Run `39194876493` was in `unxed/f4`, whose workflow checked out f4; it did not test this vtui commit. Correct `unxed/vtui` sandbox run `39204796007` now targets exact SHA `f5140571f7c245a0f0c9847df92a5e7646eb1c21`; it is running. Keep this step captured and resume after the run completes.

- 19-10-2026 05:54:46 UTC: Corrected sandbox run 39206967580 targets the exact commit and runs the project-required incremental lint plus `go test ./...`; queued. Previous run 39204796007 failed before tests because its command referenced absent `.golangci-strict.yml`.
