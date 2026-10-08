# CI — dn

Прогоны, которые запущены и результат которых не проверен. Формат — § 8 инструкции.
2026-10-08 04:51:59 PR #25 (unxed/dn#23, часть 1: заголовок панели) — проверки PR dn.yml, dn-linux.yml, dn-windows.yml, layout.yml не проверены https://github.com/unxed/dn/pull/25

08-10-2026 (Лунобот-1): main 03dec35f8 (PR #25): dn-accept 179/180, красный только u8cp (5) util_item6 — «class dn.err: timeout after 30s» (таймаут запуска class-сборки в пти, к пути не относится; на ветке PR тот же сценарий проходил). Запустил rerun-failed-jobs (run 37808031156). Если и повторный прогон красный на том же сценарии — разбирать как настоящий.
08-10-2026 (Лунобот-1): rerun-failed-jobs dn-accept не лечит summarize: артефакт accept-shard-N упавшей попытки остаётся (upload-artifact overwrite: false), summarize читает старый лог и снова даёт fail=1, хотя все шарды второй попытки зелёные (u8cp (5) прошёл). Для таких таймаутов нужен полный `POST actions/runs/<id>/rerun`, что я и запустил (run 37808031156, попытка 3). Правка workflow (overwrite: true для shard-логов) — на усмотрение, пока не делал.
