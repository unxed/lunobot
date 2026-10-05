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
- Особенности: Pascal/FreePascal, исходники DN и TV разделены; сборка и проверки
  охватывают Linux x86_64/i386/ARM64, Windows win32/win64 с UTF-8 и code page,
  DOSBox-X и Windows ConPTY. Локальную сборку и тесты не считать доказательством:
  для компиляции, PTY/ConPTY, DOS и аудита пользоваться GitHub Actions. Не
  переписывать историю и не менять `tv`-submodule без отдельной задачи.

Этот паспорт фиксирует отличия `dn` от общего протокола; новые ограничения,
обнаруженные при работе с тикетом, дописывай сюда вместе с соответствующей правкой.
