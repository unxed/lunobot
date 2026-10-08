# CI — f4

Проверенные и ожидающие прогоны. Формат — § 14.2 инструкции.

08-10-2026 (Лунобот-1): main 9ba8fc5f8 краснел на Race (shard 0), TestEditorView_WorkspaceCloseActionClosesCleanEditor: гонка за vtui.FrameManager между воркером открытия просмотрщика из TestActionOpenViewer_PromptStaysAboveDelayedProgressDialog и SwapFrameManager следующего теста. Причина: тест заканчивался по «экранов больше одного», а не по появлению просмотрщика. Воспроизведено локально (go test -race ./internal/app -shuffle 1791462183168784827), исправлено (feca8c22 в staging, уйдёт следующим поездом). Заодно в staging 0634ae37 — nosec G703 для нового WriteFile (Lint (1) был красным на 0795cf6).

08-10-2026 (Лунобот-1): поезд #1816 (15:23) — прогон CI целиком «cancelled» (не упал), tick писал «перезапустил», но run_attempt оставался 1; в 16:25 запустил вручную `POST repos/unxed/f4/actions/runs/<id>/rerun` (REST работает) → attempt 2. Если повторится — делать rerun сразу, не ждать tick.
