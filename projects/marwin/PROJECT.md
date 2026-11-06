# marwin

- Код: https://github.com/unxed/Marwin
- Задачи: issues и PR этого репозитория; dllmgr — прямое поручение владельца в https://github.com/unxed/lunobot/issues/312
- Части: Marwin runtime, dllmgr + wine-fix, cc580. Работать только над dllmgr по текущему поручению; runtime и cc580 отложены до стабилизации unxed/bp#108 и порядка unxed/bp#128 (см. OWNER_QUEUE.md).
- PR: в unxed/Marwin, ветка -> PR -> мерж в main
- Режим публикации: PR (default branch `main`; `lunobot/staging` отсутствует)
- Отладка GitHub CI: да (Go-проект; локально сборку и тесты не запускать)
- Диагностический workflow: не найден; репозиторий пока не содержит `.github/workflows/`. Перед диагностическими прогонами нужен отдельный workflow.
- CI: на 06-11-2026 GitHub Actions workflows отсутствуют; обязательные checks/branch protection не подтверждены (API вернул 403). Открытый PR #6 не имеет status checks.
- Язык общения: английский (README и PR); концепция dllmgr — русский
- Покрытие: код dllmgr отсутствует; цель не задана
- Ограничения dllmgr: `docs/dllmgr-concept.md`; И0 — ручной Wine/FSViewer spike, И1 — минимальный CLI; сборка и тесты только с разрешения пользователя.

Этот паспорт фиксирует проверенные особенности проекта; неизвестное не выводить из предположений.
