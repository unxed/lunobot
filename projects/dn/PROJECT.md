# dn

- Код: https://github.com/unxed/dn
- Задачи: тикеты и PR этого же репозитория
- PR: туда же, ветка -> PR -> мерж в `main`
- Зависимости: submodule [unxed/tv3](https://github.com/unxed/tv3); изменения его кода
  ведутся по паспорту `tv3`, если он подключён отдельным проектом
- Язык общения: по языку автора тикета
- Режим публикации: PR
- Отладка GitHub CI: да
- Диагностические workflow: `dn.yml`, `dn-linux.yml`, `dn-windows.yml` и
  `class-migration.yml` через `workflow_dispatch`; отдельного `sandbox.yml` нет
- Обязательная проверка: для изменений в DN используй PR-проверки `dn.yml`,
  `dn-linux.yml` и `dn-windows.yml`; `class-migration.yml` добавляется, когда
  затронуты class-порт, `dn/**`, `tv` или инструменты миграции. После мержа
  учитывай push-проверки `tv.yml`, `layout.yml`, `audit.yml` и `toolchain.yml`,
  если их пути затронуты.
- Прогоны `main` после мержа не отменять (исключение из § 7.3, как у vtui): `nightly.yml` публикует коммит `main`, только
  когда все его push-прогоны `dn-linux`, `dn`, `dn-windows`, `dos-utf8` завершились успехом; отменённый прогон оставляет
  `nightly` без исправления, которое «Пробуйте!» предлагает проверить (14-10-2026, PR unxed/dn#43).
- Особенности: Pascal/FreePascal, исходники DN и TV разделены; сборка и проверки
  охватывают Linux x86_64/i386/ARM64, Windows win32/win64 с UTF-8 и code page,
  DOSBox-X и Windows ConPTY. Локальную сборку и тесты не считать доказательством:
  для компиляции, PTY/ConPTY, DOS и аудита пользоваться GitHub Actions. Не
  переписывать историю и не менять `tv`-submodule без отдельной задачи.

Этот паспорт фиксирует отличия `dn` от общего протокола; новые ограничения,
обнаруженные при работе с тикетом, дописывай сюда вместе с соответствующей правкой.

Перед PR прогоняй политику текста: `python3 -B -m unittest discover -s tools/tests -p 'test_text_policy.py'` (весь `discover -s tools/tests` включает `test_pack.py`, который собирает пакет и локально без сборки падает на `dn-pack.sh`, 15-10-2026; в `test_text_policy.py`: кириллица
только в местах из `docs/TEXT-POLICY.md`, всё остальное — английский, в том числе `.desktop`, README, комментарии). PR-проверки
`dn.yml`, `dn-linux.yml` и `dn-windows.yml` этого теста НЕ гоняют: его запускают `layout.yml` и `class-migration.yml` уже
после мержа, и красный `main` — это цена пропуска (так было с dn#22, PR #24 -> починка #26). Новый файл вне `dn/` и `tv/`
тоже сверяй с этой политикой и с `tools/check-layout.sh`.

Часть исходников `dn/src` (например, `basics.pas`, `drives.pas`, `panelroot.pas`) — с окончаниями строк CRLF, часть — LF. Правь их так,
чтобы окончания сохранились (в Python — `open(..., newline='')`), иначе дифф переписывает файл целиком (12-10-2026, dn#20).
