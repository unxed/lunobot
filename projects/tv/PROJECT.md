# tv

- Код: https://github.com/unxed/tv
- Задачи: тикеты и PR этого же репозитория
- PR: туда же, ветка -> PR -> мерж в `main`
- Зависимости: `unxed/dn` and `unxed/tv3` are related repositories; do not modify them from a tv task
- Язык общения: по языку автора тикета
- Режим публикации: PR
- Отладка GitHub CI: да
- Диагностические workflow: не настроены; issue #1 tracks a reproducible CI baseline
- Объём CI (решение владельца 21-10-2026, unxed/tv#1, вариант 1): только тесты, которые собираются из текущих исходников `tv`; остальные — в README списком «не проверяется» с причиной (отсутствующий модуль или include). Архивный код (`src/`, существующие тесты) и историю не менять; новые тесты — новыми файлами (имя до 8 знаков, `testlib.inc`, `ALL OK`).
- Покрытие (Pascal, измеримый критерий): *interface coverage* — каждая процедура, функция, метод и конструктор из `interface` каждого собираемого юнита вызывается хотя бы одним тестом, который гоняет CI; цель 100 % по каждому юниту, исключения поимённо в README с причиной. Меряет скрипт в CI (`<юнит>: <вызвано>/<объявлено>` и список невызванных). Процент строк не заявлять: инструмента покрытия строк для Free Pascal нет.
- Гейт аудита перед релизом (поручение владельца 21-10-2026, unxed/lunobot#235): `tools/audit/run.sh` tv на кандидатном sha — в CI песочницы `unxed/sandbox` (корпуса только в CI, артефакт удалить после скачивания), полный вывод — в unxed/tv#1. Первый прогон — до CI-шагов (G1), второй — на sha релиза (G2). Тег и релиз — только при `AUDIT PASS` на том же sha, что и зелёный CI; `AUDIT FAIL` — разбор совпадений в формате tv3 (unxed/tv3#3: файл и корпус, raw/ren/lit, окно, заимствование или ложное срабатывание с обоснованием) и вопрос владельцу через `notify_owner.py`.
- Обязательная проверка: green checks for the exact PR SHA; until CI exists, do not claim a verified stable release
- Особенности: README marks this repository as historical; development continues in `unxed/tv3`. History was rewritten on 2026-10-08; older trees may not build. Keep historical scope and provenance explicit.

Этот паспорт создан по прямому поручению владельца от 15-10-2026. Новые ограничения фиксируй здесь вместе с соответствующей правкой.
