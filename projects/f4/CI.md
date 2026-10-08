# CI — f4

Проверенные и ожидающие прогоны. Формат — § 14.2 инструкции.

08-10-2026 (Лунобот-1): main 9ba8fc5f8 краснел на Race (shard 0), TestEditorView_WorkspaceCloseActionClosesCleanEditor: гонка за vtui.FrameManager между воркером открытия просмотрщика из TestActionOpenViewer_PromptStaysAboveDelayedProgressDialog и SwapFrameManager следующего теста. Причина: тест заканчивался по «экранов больше одного», а не по появлению просмотрщика. Воспроизведено локально (go test -race ./internal/app -shuffle 1791462183168784827), исправлено (feca8c22 в staging, уйдёт следующим поездом). Заодно в staging 0634ae37 — nosec G703 для нового WriteFile (Lint (1) был красным на 0795cf6).

08-10-2026 (Лунобот-1): поезд #1816 (15:23) — прогон CI целиком «cancelled» (не упал), tick писал «перезапустил», но run_attempt оставался 1; в 16:25 запустил вручную `POST repos/unxed/f4/actions/runs/<id>/rerun` (REST работает) → attempt 2. Если повторится — делать rerun сразу, не ждать tick.

08-10-2026 (Лунобот-1), ретро «приземлённая работа ждёт main > 2 ч»: (1) поезд #1816 стоял с 15:23 до ~16:30: прогон CI целиком «cancelled», `tick` писал «перезапустил», а попытка не росла — вручную `POST actions/runs/<id>/rerun` помог; (2) после влития поезда main уходил вперёд, и merge main→staging, который запушил я (а не `land`), не запускал quick: у вершины 3ff10d92a quick появился только через 27 мин по `ensure_quick_on_tip` (workflow_dispatch). Вывод: после ручного merge main→staging сразу `gh api -X POST repos/<repo>/actions/workflows/quick.yml/dispatches -f ref=lunobot/staging`. Хвост — очередь раннеров dn-accept (≈12 шардов ×2) вперемешку с f4: quick f4 ждёт раннер.

08-10-2026 (Лунобот-1): main 23e6638cf красный на Test (darwin/amd64): TestCmdSessionStalePromptDoesNotEndExecution/Windows_10_19045 (internal/panel/cmd_session_test.go:283, «executing=true, want false») — тест по времени (settledWithin = 120 мс, wait(5 мс)), на загруженном macOS-раннере не успевает; код вокруг не менялся (PR #1785 — курсор при перечитывании). Один rerun failed jobs (run 37826245926). Если упадёт снова на том же тесте — поднять settledWithin или сделать ожидание по условию (корень — таймерная гонка теста).
