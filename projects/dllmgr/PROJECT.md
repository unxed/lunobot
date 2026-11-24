# dllmgr

- Код: https://github.com/unxed/dllmgr
- Задачи: issues и PR этого репозитория; обслуживание — прямое поручение владельца https://github.com/unxed/lunobot/issues/315
- Назначение: менеджер вариантов DLL для Wine и Marwin, с каталогом библиотек и fixes; Go, GUI на goWidgets. Концепция: `docs/concept.md`.
- PR: в `unxed/dllmgr`, ветка -> PR -> мерж в `main`
- Режим публикации: PR (`default branch main`; `lunobot/staging` отсутствует)
- Отладка GitHub CI: да; локальные сборки и тесты — только с разрешения владельца, сначала предоставить patch.
- CI: проверено 24-11-2026: `catalog` и `apply-scripts` запускаются на push и pull_request. `catalog` выполняет go vet/test и проверку каталога; `apply-scripts` — регрессионные варианты legacy/patched, real-wine и scope-patch. Остальные workflows запускаются по путям или вручную. В PR #91 оба workflow сработали на точном SHA; результаты ведутся в CI.md. Обязательность checks/branch protection не подтверждена: API вернул 403.
- Язык общения: английский (README, концепция, issues и PR)
- Покрытие: код ещё не начат; цель не задана
- Особенности: начать с ручного И0-spike без кода по `spike/spike0.sh`; дальнейшие итерации I0/I1 описаны в `docs/concept.md`. Не начинать без доступной среды Wine/FastStone и подтверждённых результатов И0.

Этот паспорт фиксирует проверенные особенности проекта; неизвестное не выводить из предположений.
