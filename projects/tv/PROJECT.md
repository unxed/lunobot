# tv

- Код: https://github.com/unxed/tv
- Задачи: тикеты и PR этого же репозитория
- PR: туда же, ветка -> PR -> мерж в `main`
- Зависимости: `unxed/dn` and `unxed/tv3` are related repositories; do not modify them from a tv task
- Язык общения: по языку автора тикета
- Режим публикации: PR
- Отладка GitHub CI: да
- Диагностические workflow: не настроены; issue #1 tracks a reproducible CI baseline
- Релиз: отложен решением владельца 21-10-2026 (unxed/tv#1, https://github.com/unxed/tv/issues/1#issuecomment-6321006800; unxed/lunobot#235): CI, README, новые тесты, тег и релиз не делать; работы по проекту нет до решения владельца, закрывать ли направление tv. Аудит `tools/audit/run.sh` — `AUDIT PASS` на `49c50781baace2ca00c26db6a771a0a52c778211` (https://github.com/unxed/sandbox/actions/runs/39633252866).
- Обязательная проверка: green checks for the exact PR SHA; until CI exists, do not claim a verified stable release
- Особенности: README marks this repository as historical; development continues in `unxed/tv3`. History was rewritten on 2026-10-08; older trees may not build. Keep historical scope and provenance explicit.

Этот паспорт создан по прямому поручению владельца от 15-10-2026. Новые ограничения фиксируй здесь вместе с соответствующей правкой.
