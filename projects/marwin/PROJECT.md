# marwin

- Код: https://github.com/unxed/Marwin
- Задачи: issues и PR этого репозитория; запуск рантайма — прямое поручение владельца в https://github.com/unxed/lunobot/issues/315
- Назначение: только консольный runtime для Far2/Far3 и текстовых DOS-программ через DOSBox-X; dllmgr и fix-it-in-wine — отдельные проекты.
- Связанные проекты: [dllmgr](https://github.com/unxed/dllmgr) управляет вариантами DLL для Wine и Marwin; его план cc580 — в unxed/dllmgr#1. [fix-it-in-wine](https://github.com/unxed/fix-it-in-wine) — отдельный ИИ-скилл для исправления программ под Wine.
- Ограничения: разработку Marwin runtime начинать только после выполнения условия из заметки Marwin в OWNER_QUEUE.md; cc580 вести в dllmgr, не здесь.
- PR: в unxed/Marwin, ветка -> PR -> мерж в main
- Режим публикации: PR (default branch `main`; `lunobot/staging` отсутствует)
- Отладка GitHub CI: да (README и PR требуют публикации через GitHub; локальные сборки и тесты не запускать)
- CI: на 06-11-2026 workflow в `.github/workflows/` отсутствуют; обязательные checks/branch protection не подтверждены (API вернул 403).
- Язык общения: английский (README, issues и PR)
- Покрытие: цель не задана; runtime ещё не начат

Этот паспорт фиксирует проверенные особенности проекта; неизвестное не выводить из предположений.
