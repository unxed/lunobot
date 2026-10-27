# sandbox

- Код: https://github.com/unxed/sandbox
- Задачи: прямое поручение владельца https://github.com/unxed/lunobot/issues/280, затем issues и PR этого репозитория.
- PR: в `unxed/sandbox`, ветка -> PR -> мерж в `main`.
- Режим публикации: PR (`lunobot/staging` и `quick.yml` отсутствуют в origin на 24-10-2026).
- Отладка GitHub CI: да — корневой README запрещает локальные сборки и запуски; проверка только в GitHub Actions.
- Диагностические workflows: `faststone-native.yml` (Windows API probes, dispatch или ветка `faststone-5.6-validation`) и `vmlab-session.yml` (ручной dispatch VM); общего FastStone GUI workflow пока нет.
- CI: обязательные status checks не подтверждены; до публикации каждой правки определить применимый workflow по изменённым путям и проверить точный SHA в GitHub Actions.
- Язык общения: русский (основные документы), английский — для внешних upstream.
- Покрытие: целевой порог не указан; для FastStone критерием служат реальные сохранённые E2E/API evidence из `faststone/HANDOFF.md`, не локальная сборка и не packaging-only pass.
- Особенности: FastStone загружается только из закреплённых Wayback snapshots; `FSViewer.exe` не менять; точка входа — `faststone/HANDOFF.md`.

Этот паспорт — источник особенностей проекта; неизвестное не выводить из предположений.
