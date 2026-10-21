# bp

- Код: https://github.com/unxed/bp
- Что это: Better Pascal — диалект FPC с безопасной моделью памяти (концепции Rust и Go); в каталоге `fpide/` — Free Pascal IDE,
  перенесённая на tv3 (submodule `fpide/tv` -> unxed/tv3, `fpide/tve` -> unxed/tve)
- Задачи: тикеты и PR этого же репозитория (и языка, и fpide)
- PR: туда же, ветка -> PR -> мерж в `main`
- Зависимости: submodule unxed/tv3 (правки его кода — по паспорту `tv3`) и unxed/tve; submodule не двигать без отдельной задачи
- Язык общения: по языку автора тикета
- Режим публикации: PR
- Отладка GitHub CI: да
- Диагностические workflow: `ci.yml`, `fpide.yml`, `fpide-accept.yml`; отдельного `sandbox.yml` нет
- Обязательная проверка: `ci.yml` на SHA PR (прогон события `pull_request`); при изменениях в `fpide/**` — ещё `fpide.yml` и `fpide-accept.yml` (тоже `pull_request`). `push` в `ci.yml`, `fpide.yml` и `fpide-accept.yml` ограничен веткой `main` (unxed/bp#27, 17-10-2026): один коммит ветки PR даёт по одному прогону каждого workflow, а не два; прогоны `push` в `main` идут после мержа.
- Особенности: лицензионные правила `CLAUDE.md` репозитория важнее всего остального (код IDE остаётся под GPL; tve и tv3 —
  без GPL/RIT кода). Для fpide есть правила в `.cursor/rules/fpide-full-port.mdc`. Сводный план работ — `docs/HANDOFF.md`
  в unxed/dn.
- Safe в модуле: `uses Safe` прячет в этом модуле `FreeAndNil`, `.Free`, `New`, `Dispose`, `Move`, `FillChar`, `GetMem` и т. п. (`safe/poison.intf.inc`). Прежде чем коммитить модуль с новым `Safe`, прогрепай его: `grep -nE '\.Free\b|FreeAndNil\(|\b(New|Dispose|Move|FillChar|GetMem|FreeMem)\(' <файл>` — каждое место переведи на `TOwned`/`Reset` либо на `SysUtils.FreeAndNil(...)` с `// UNSAFE:` строкой выше (`safe/SPEC.md`, раздел UNSAFE). Иначе первая же сборка падает (unxed/bp#10, 16-10-2026: `Illegal type conversion ... to "TSafeForbidden"`). Тест с `SafeCheckNoLeaks` — проверки в процедуре, а не в основном блоке программы: владельцы (`TOwned`) в основном блоке и временные значения вызовов живут до конца программы, и `SafeCheckNoLeaks` видит их живыми даже после `Reset` (unxed/bp#11, 16-10-2026: «3 owned object(s) still alive» в `t_fpdlv`). Логи job'ов с цветом читать: `gh api --allow-escape-sequences repos/unxed/bp/actions/jobs/<id>/logs`.
- NOTICE, строка `commit:` (постоянное решение владельца 21-10-2026, unxed/lunobot#233): на вопрос «разрешаете ли боту впредь самому обновлять строку `commit:` в NOTICE при побайтном обновлении вендоренного файла» владелец ответил «да». Условие: вендоренный файл в PR побайтно равен файлу источника на указанном коммите (git sha blob'ов совпадают: `gh api repos/<источник>/contents/<путь>?ref=<коммит> --jq .sha` против того же для файла в PR) и в NOTICE меняется только строка `commit:`. Текст лицензии, копирайты, `LICENSE` и прочие правовые тексты (правило 5 `CLAUDE.md` репозитория) — по-прежнему только решением владельца.

Этот паспорт — то место, где живут отличия проекта от остальных. Не хватает ответа
на вопрос, который встал в работе, — дополни паспорт вместе с правкой по задаче.
