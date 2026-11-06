# fix-it-in-wine

- Код: https://github.com/unxed/fix-it-in-wine
- Задачи: issues и PR этого репозитория; обслуживание — прямое поручение владельца https://github.com/unxed/lunobot/issues/315
- Назначение: ИИ-скилл для диагностики и исправления проблем Windows-программ под Wine; инструкции в `SKILL.md`, дизайн в `docs/concept.md`.
- PR: в `unxed/fix-it-in-wine`, ветка -> PR -> мерж в `main`
- Режим публикации: PR (`default branch main`; `lunobot/staging` отсутствует)
- Отладка GitHub CI: нет; узкие локальные тесты Python допустимы, тесты не требуют Wine или сети.
- CI: `.github/workflows/tests.yml` запускает `python3 -m unittest discover -s tests -v` и `bash -n tools/*.sh` на Ubuntu. Обязательные checks/branch protection не подтверждены (API вернул 403).
- Язык общения: английский (README, skill, issues и PR)
- Покрытие: цель не задана
- Особенности: не менять системный Wine и файлы префикса вручную; диагностические изменения обратимы и ограничены одним приложением и одним префиксом. Не публиковать ничего в WineHQ без явного согласия пользователя.

Этот паспорт фиксирует проверенные особенности проекта; неизвестное не выводить из предположений.
