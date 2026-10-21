# tv3 — протокол переписывания модулей (поручение unxed/lunobot#240, план unxed/tv3#12)

Этот файл — в учёте, а не в репозитории tv3: правило 3 `CLAUDE.md` tv3 запрещает утверждения о происхождении кода в
коде, документах и коммитах tv3. Здесь — как пишется модуль и что записывается о каждом шаге. В tv3 (код, коммит, PR,
тикет) о происхождении не пишется ничего, кроме обязательного заголовка `Translated from magiblot/tvision @ b4831e2`.

Цель (слово владельца): воспроизведение magiblot/tvision @ `b4831e2` на Free Pascal на классах, с нашими доработками,
с понятным происхождением. Каждое правило ниже отвечает на вопрос «откуда в этом файле эта строка».

**Метод — новый перенос, не правка и не «с нуля».** Модуль заново ПЕРЕНОСИТСЯ с magiblot/tvision @ `b4831e2` на
Free Pascal на классах, имена — по `docs/API-NAMES.md` (правило 13 tv3): каждая процедура следует своей функции C++.
Прежняя реализация tv3 не правится и не читается исполнителем (п. 3); «написать по-своему» — тоже нет, кроме наших
доработок, явно названных в шаге (асинхронный контракт S1a, классы tv3 без пары в magiblot).

**Цель — классы и асинхронная архитектура** (слово владельца 21-10-2026: «помни про то, что наша цель — классовый
синтаксис и возможность асинхронной архитектуры приложений в духе f4/vtui»). Поэтому сначала переносится ядро цикла
событий с контрактом `docs/ASYNC.md` tv3 (шаг S1a): `TvEvents`, затем `TvSys` (`WaitForEvents`, `WakeUp`, очередь
задач, таймеры); остальные модули — поверх него. Исполнителю модуля ядра в `room/` кладётся ещё `ASYNC.md` (вход п. 2).

## 1. Роли

- **Исполнитель** — отдельный субагент (новый, без истории разговора), который пишет один модуль. Он видит только
  входы из п. 2. Один модуль — один исполнитель; исправления по CI делает новый запуск исполнителя с тем же набором
  входов и текстом ошибок (п. 5), не оркестратор.
- **Оркестратор** — воркер Лунобота, который ведёт шаг: собирает каталог входов, запускает исполнителя, переносит его
  файл в ветку tv3, гоняет CI и аудиты, ведёт реестр (п. 7). Оркестратор код модуля не пишет и не правит, кроме
  механики, не меняющей токенов (перевод строк, права файла). Он видел старую реализацию — поэтому он и не пишет.
- **Классификатор** — Лунобот-1: разбирает каждое попадание аудита на пониженных порогах (п. 6.2) и отчёт сходства
  (п. 6.3). Может совпадать с оркестратором, если оркестратор — Лунобот-1.

## 2. Входы исполнителя (только они)

Каталог шага `/tmp/lunobot-<номер>/work/<слаг>/room/` — пустой, затем в него кладётся ровно это:

1. `magiblot/` — файлы magiblot/tvision @ `b4831e2ca16652db327fb7cc964f1c8c2d512524` (тот же коммит, что берёт
   `tools/audit/fetch-corpora.sh` tv3), перечисленные в заголовке модуля tv3, плюс заголовки `include/tvision/*.h`,
   на которые они ссылаются; если заголовок модуля называет их неточно (у `TvGeom` — «include/tvision geometry
   header»), точный список выбирает оркестратор по именам классов interface и записывает в реестр. Каждый —
   `gh api -H 'Accept: application/vnd.github.raw+json' 'repos/magiblot/tvision/contents/<путь>?ref=b4831e2ca16652db327fb7cc964f1c8c2d512524'`;
   путь и sha blob'а — в реестр.
2. `API-NAMES.md` — `docs/API-NAMES.md` tv3 с `main` (правила имён: как имя C++ становится именем Pascal).
3. `interface.pas` — секция `interface` модуля tv3 с `main`: от строки `unit` до строки `implementation`
   (не включая её), ровно как в файле, с заголовком модуля. Это контракт: имена, типы, поля, сигнатуры,
   публичные константы. Вырезает оркестратор скриптом (`sed -n '1,/^implementation/p' | sed '$d'`), не руками.
4. `units.txt` — для каждого модуля из `uses` этого модуля (секции interface и implementation): путь к его
   `interface.pas` в `deps/`; сами `deps/<unit>.pas` — тоже только секции `interface` (п. 2.3) с `main`.
5. `tests.txt` — имена тестовых программ модуля (`tests/t_<…>.pas`) и что каждая проверяет, одной строкой со слов
   оркестратора по именам процедур теста; исходники тестов исполнителю не даются (п. 3).
6. `PROMPT.md` — промпт из п. 8 с подставленными именами.

## 3. Чего исполнителю нельзя

- секция `implementation` любого модуля tv3 — текущая и из любой ревизии истории;
- что-либо из `unxed/tv` (удалён владельцем; копия у владельца — тоже);
- Free Vision и любые пакеты FPC (`fv`, `ide`, `fcl-*`, `rtl-objpas`), Borland Pascal Turbo Vision, fpide и `unxed/bp`
  (`sp`), DOS Navigator и `unxed/dn`, far2l (код), веб-поиск и чтение кода Turbo Vision где бы то ни было;
- исходники тестов tv3 (они тоже унаследованы и пока не разобраны; поведение исполнитель берёт из magiblot и
  `tests.txt`, а результат тестов — из CI, п. 5);
- любые инструменты сети (`gh`, `curl`, WebFetch, WebSearch) и чтение файлов вне каталога `room/`.

Исполнителя запускай типом агента, у которого есть только файловые инструменты (Read, Write, Edit, Glob, Grep), если
среда его даёт; иначе запрет — в промпте, и исполнитель в отчёте перечисляет каждый прочитанный файл (п. 8). Отчёт с
путём вне `room/` или с сетевым вызовом — шаг недействителен: файл выбросить, запустить нового исполнителя.

Модуль `TvFar2l`: вход — только `VTExts.md` ветки `extsdocs` unxed/far2l (`gh api … 'repos/unxed/far2l/contents/VTExts.md?ref=extsdocs'`,
sha blob'а в реестр) вместо `magiblot/`; код far2l не читать (правило 2 `CLAUDE.md`).

## 4. Модули и порядок

**Состав — все 50 файлов `src/`, пришедших из tv** (факты основного инстанса по копии tv у владельца, HEAD `c9bb5c4` до
переписывания: в его `src/` 50 файлов, все есть в tv3; решение 21-10-2026 — переносятся ВСЕ, вопрос unxed/lunobot#240 снят):
- 46 модулей Pascal (порядок — п. 9) и 2 включаемых файла кода `tvapppal.inc`, `tvdefs.inc` (идут с модулем, который их
  включает: `tvapppal.inc` — с TvApp, `tvdefs.inc` — отдельным шагом после S29, это настройки компилятора);
- 2 таблицы `tvcp.inc`, `tvwidth.inc` — генератором, шаг S29.
- Не из tv (идут в S30, аудит «по памяти»): tvactions, tvappdir, tvascii, tvcharset (.pas/.inc), tvclipcmd, tvcrc, tvcstr,
  tvdosnames, tvformat, tvgadgets, tvglyphs, tvini, tvkeyname, tvpath, tvproc, tvtermosbase, tvtermosnone, tvtermosunix,
  tvtermoswin, tvtermstub.inc, tvtermunix.inc, tvtermwin.inc, tvustr, tvvtext, tvwild, tvwordnav, tvxlat. Тесты `tests/`
  из tv — тоже S30, на пониженных порогах.

**Источники по модулям** (правило 1 `CLAUDE.md` tv3: единственный чужой источник — magiblot/tvision):
- модули, у которых есть пара в magiblot/tvision @ b4831e2 — её файлы (п. 2.1);
- TvVt, TvVtRun, TvVtKeys, TvVtView, TvPty (эмулятор терминала и pty; у magiblot/tvision их нет) — только стандарты:
  xterm «Control Sequences» (ctlseqs), ECMA-48, DEC STD 070; сначала они кладутся в `tools/audit/facts/` tv3 как
  разрешённые документы (правило 4: каждый называет свой источник) отдельным PR, затем — вход исполнителя вместо
  `magiblot/`. magiblot/tvterm и libvterm — НЕ источник (это не magiblot/tvision);
- TvFar2l — только `VTExts.md` ветки `extsdocs` unxed/far2l (п. 3), код far2l не читать;
- модули без пары и без стандарта (TvDos, TvLocale, TvMem, TvTermOs, TvUnix — платформенные слои) — по interface,
  `docs/ASYNC.md`, документации ОС/RTL Free Pascal (не TV-кода) и поведению по тестам; список таких входов шаг пишет в реестр.

## 5. Ход шага (один модуль — один PR tv3)

1. Захват по блоку `account-240` (`claims.py take tv3 "… «account-240: S<n> <модуль>» по § 8 [urgent: по § 4 п. 1 — поручение владельца]"`).
2. Оркестратор собирает `room/` (п. 2), запускает исполнителя с промптом п. 8.
3. Исполнитель отдаёт `src/<модуль>.pas` (весь файл: заголовок, interface без изменений, новая implementation) и
   отчёт (п. 8). Оркестратор сверяет: секция interface побайтно равна `interface.pas` (`diff`), иначе — назад
   исполнителю с этим diff.
4. Оркестратор кладёт файл в ветку `lunobot/pr/<модуль>-rw` tv3 от свежего `main`, коммит — обычный технический
   («… rewritten against magiblot …» недопустимо — это утверждение о происхождении; пиши `<модуль>: new
   implementation`, тело — что проверено тестами), PR, строка
   `CI.md`, `BRANCHES.md`.
5. CI tv3 красный — оркестратор даёт НОВОМУ исполнителю тот же `room/` плюс `ci.txt`: имена упавших тестов и их
   сообщения из лога CI (`run_log.py … --grep 'FAIL|Error'`), без исходников тестов. Не больше трёх итераций, дальше —
   запись в status и вопрос классификатору (тест может проверять поведение старой реализации, расходящееся с magiblot:
   тогда решает Лунобот-1 по magiblot, расхождение записывается в реестр и в описание PR без слов о происхождении).
6. Проверки (п. 6) — все до вливания. Вливание — merge-коммит, как у прочих PR tv3 (`ci` целиком на точном SHA).

## 6. Проверки шага

1. **Стандартный аудит** — `AUDIT PASS` на голове PR: `gh workflow run tv3-audit.yml --repo unxed/sandbox --ref main
   -f repo=unxed/tv3 -f refs="main <sha головы>"`; до вливания S0 — пустой `new.txt` (правило паспорта tv3). Артефакт
   удалить после скачивания.
2. **Пониженный аудит** — `borrow-audit.py --raw-k 16 --ren-k 100` по одному файлу модуля против корпусов Borland
   Pascal TV (`bp7tv`) и Free Vision (`fpc/packages/fv`, `fpcmain/packages/fv`; список — фильтр `list.txt` по этим
   путям), с `--allowed` как в `run.sh`. Каждое попадание классифицирует Лунобот-1: (а) общий API (шапка, объявление,
   имя из magiblot), (б) стандартная идиома Pascal (цикл, `case`, `inherited`, `Free`), (в) общий факт (код клавиши,
   цвет, таблица стандарта) — ложные, с причиной; (г) заимствование — модуль выбрасывается целиком и пишется заново
   новым исполнителем с пометкой в промпте, какой фрагмент не повторять (без самого фрагмента — только место и
   поведение). Запуск — п. 10.6 (вход `extra`).
3. **Сходство с прежней реализацией** — `borrow-audit.py --max` новой implementation против старой implementation того
   же модуля (`main` до PR), обе секции вырезаны от `implementation` до конца. Печатается самая длинная цепочка raw/ren.
   Флаг: raw ≥ 24 или ren ≥ 200 (стандартные пороги): классификатор разбирает каждое такое место как в п. 6.2;
   общий результат — число и длина цепочек — в реестр. Ожидаемо высокое сходство коротких процедур (геттеры, `Assign`)
   — не флаг, если цепочка внутри одной процедуры длиной до 40 токенов и процедура повторяет поведение magiblot строка
   в строку. Запуск — п. 10.6.
4. **CI tv3** — `ci` (`linux`, `pty`, `generated`) зелёный на точном SHA.
5. **Поведение** — тесты модуля проходят; расхождение с magiblot, найденное исполнителем (его отчёт), — в реестр и в
   описание PR (по существу поведения, без слов о происхождении).

## 7. Реестр (`projects/tv3/status/12.md`, раздел «Реестр»)

Одна запись на модуль (абзац): модуль; шаг; дата UTC; входы (пути magiblot и sha blob'ов, sha `main` tv3, с которого
взяты interface и `API-NAMES.md`); модель и среда исполнителя (подпись § 9), число запусков; sha коммита в PR; прогоны:
CI, стандартный аудит, пониженный аудит (число попаданий и классы), сходство (самые длинные цепочки); итог «влит
`<merge sha>`». Реестр — единственное место, где записано, откуда модуль: репозиторий tv3 этого не содержит.

## 8. Шаблон промпта исполнителя (`PROMPT.md`)

```
You write one Free Pascal unit, <Unit>, for a class-based Turbo Vision library.

Inputs, all in this directory and nothing else:
  interface.pas  - the unit header and its interface section. Keep them byte for byte.
  deps/*.pas     - the interface sections of the units it uses.
  magiblot/      - the C++ sources of magiblot/tvision at <sha> that this unit corresponds to. The behaviour of every
                   routine follows them.
  API-NAMES.md   - how C++ names and forms map to the Pascal names of this library.
  tests.txt      - the test programs of this unit and what each checks.
  ci.txt         - (only on a retry) the failing tests and their messages.

Write src/<unit>.pas: the header and interface exactly as given, then an implementation section that implements every
routine of the interface with the behaviour of the C++ sources. Free Pascal 3.2, mode objfpc, {$I tvdefs.inc} as in the
header.

Rules:
- Read only the files of this directory. Do not use the network, a shell, or any file outside it.
- Do not reproduce code you remember from Turbo Vision, Free Vision, Borland Pascal, the Free Pascal packages,
  DOS Navigator or far2l. Write each routine from the C++ source in front of you and the interface.
- Do not add comments about where the code comes from.
- Where the C++ behaviour cannot be expressed with the given interface, say so in the report; do not change the
  interface.

Report at the end: the list of every file you read; for each routine, the C++ function it follows (file:line);
every place where you departed from the C++ behaviour and why.
```

## 9. Порядок модулей по `uses`

Построено 21-10-2026 по `main` tv3 (граф `uses` обеих секций, топологическая сортировка, ядро цикла первым; циклов
нет), 46 модулей из tv; шаг S<n+1> для номера n: 1. TvGeom, 2. TvKeys, 3. TvUtf8, 4. TvEvents, 5. TvSys, 6. TvColors, 7. TvAnsi, 8. TvCodePg, 9. TvCell, 10. TvText, 11. TvDrawBuf, 12. TvUtil, 13. TvObjs, 14. TvClip, 15. TvScreen, 16. TvTimer, 17. TvViews, 18. TvMenus, 19. TvWindow, 20. TvApp, 21. TvDialog, 22. TvFiles, 23. TvMsgBox, 24. TvValid, 25. TvInput, 26. TvList, 27. TvHist, 28. TvFileDlg, 29. TvChDir, 30. TvCluster, 31. TvColorSel, 32. TvMouse, 33. TvDos, 34. TvFar2l, 35. TvHelp, 36. TvLocale, 37. TvMem, 38. TvPty, 39. TvTermIo, 40. TvTermOs, 41. TvTextView, 42. TvUnix, 43. TvVt, 44. TvVtKeys, 45. TvVtRun, 46. TvVtView. Пересчитывать при каждом изменении `uses` (скрипт — запись
21-10-2026 в status/12.md).

## Шаги вне плана tv3, нужные протоколу

- **S1b** — сделан минимумом в пилоте S2: вход `extra` в `tv3-audit.yml` unxed/sandbox (`45c9a2d`), команда — п. 10.6.

## 10. Чек-лист оркестратора (S3+, Лунобот-2; классификация — Лунобот-1)

Проверено пилотом S2 (TvGeom, unxed/tv3#15). Порядок модулей — п. 9; один модуль — один круг.

1. Захват: `claims.py take tv3 "<UTC> Я <id>, взял кастомную задачу «account-240: S<n> <Модуль>» по § 8 [urgent: по § 4 п. 1 — поручение владельца]"`.
2. Каталог `room-<модуль>/` в каталоге шага, только входы п. 2: `interface.pas` (`sed -n '1,/^implementation/p' src/<m>.pas | sed '$d'`),
   `deps/tvdefs.inc` и `deps/<unit>.pas` (interface-секции модулей из `uses`, той же командой), `magiblot/<файлы>` (п. 2.1,
   sha blob'а — `gh api "repos/magiblot/tvision/contents/<путь>?ref=b4831e2ca16652db327fb7cc964f1c8c2d512524" --jq .sha`),
   `API-NAMES.md`, для ядра — `ASYNC.md`, `tests.txt` (имена проверок теста модуля: `grep -oE "Check\([^;]*'[^']+'\)" tests/t_<..>.pas`,
   по строке «имя — что ожидается» словами оркестратора, без кода), `PROMPT.md` (п. 8, имена подставить), пустой `out/`.
3. Исполнитель — инструмент запуска субагента (тип general-purpose; типа только с файловыми инструментами в среде нет),
   промпт-обёртка: «Your working directory is <room>. Use only Read, Write and Edit, only inside it. No Bash, network,
   gh, git; do not read outside it. Read PROMPT.md and do what it says; output out/<m>.pas. Nobody compiles it during
   the task. Final message: the report of PROMPT.md, plus how long it took and what was unclear.» Ждать уведомления.
3a. Перед запуском: все файлы C++, которые называет interface модуля (комментарии вида `drivers2.cpp: ctrlToArrow`,
   `grep -oE '[a-z0-9_]+\.(cpp|h)' interface.pas`), — в `magiblot/`; заголовок модуля бывает неполным (S3, TvKeys: без
   `drivers2.cpp` исполнитель написал `CtrlToArrow` по памяти — файл выброшен, второй запуск с полным набором). В обёртку
   промпта: «routine without C++ source among the inputs — leave `begin end;` and say so; never from memory».
4. Отчёт: каждый прочитанный файл внутри `room/` (иначе — выбросить, новый исполнитель). `diff` interface — пусто.
5. Ветка `lunobot/pr/<m>-rw` от свежего `main` (BRANCHES.md до неё), файл в `src/`, коммит:
   `<Модуль>: new implementation` / тело «A new implementation section …; the interface is unchanged. tests/t_<..>.pas
   checks the behaviour. Part of #12 (step S<n>).» + трейлер `Co-Authored-By`. Запрещены слова о происхождении
   («written again», «as tvision does», «ported», «clean», «from scratch», «not copied»); поведение — фактами.
6. PR (`gh_post.py pr`), строка CI.md, затем аудит с доп. проверками одной командой:
   `gh workflow run tv3-audit.yml --repo unxed/sandbox --ref main -f repo=unxed/tv3 -f refs="main <sha головы>" -f extra="$(cat extra.sh)"`,
   где `extra.sh` — текст ниже с подставленными `M=<m>` и `OLD=<sha main>`:
   ```
   set -u; M=<m>; OLD=<sha main>; L=/tmp/low; mkdir -p $L/old $L/new; grep -E "/(bp7tv|fpc/packages/fv|fpcmain/packages/fv)/" "$CORPORA/list.txt" > $L/ref.txt; echo "== lowered (raw 16, ren 100) vs bp7tv and fv"; python3 tools/audit/borrow-audit.py --cache "$CORPORA/index" --ref $L/ref.txt --allowed "$CORPORA/allowed.txt" --raw-k 16 --ren-k 100 src/$M.pas; echo "lowered exit $?"; git show $OLD:src/$M.pas | sed -n "/^implementation/,\$p" > $L/old/$M.pas; sed -n "/^implementation/,\$p" src/$M.pas > $L/new/$M.pas; echo $L/old/$M.pas > $L/prev.txt; echo "== prev"; python3 tools/audit/borrow-audit.py --cache $L/cache --ref $L/prev.txt --max $L/new/$M.pas; echo "prev exit $?"
   ```
7. Результат: `run_log.py unxed/sandbox <id> --job audit` — строки `AUDIT PASS|FAIL` по ревизиям, `keys … missing`,
   блок `== lowered` и `== prev`; выдержки обеих сторон — `gh run download <id> --repo unxed/sandbox -n tv3-audit`
   (`2-sheet.txt`), после чтения артефакт удалить. Всё это — в status/12.md записью «ждёт классификации Л1» со ссылками.
8. Классификация (Л1) — п. 6.2 плюс класс **(д) прямой перевод строки разрешённого источника**: окно — токены строки
   magiblot (`file:line` назвать) в синтаксисе Pascal с именами, которые фиксирует API, и больше ничего; любой другой
   текст на Pascal, переводящий ту же строку, даёт те же токены. Это ложное срабатывание. Стандартный FAIL такого класса —
   строка в `tools/audit/known.txt` того же PR (формат шапки файла: comparison, tokens, window, reference:line, ссылка на
   комментарий-разбор в PR, причина техническими словами), затем повторный аудит: `AUDIT PASS` и 0 новых ключей.
   Разбор — комментарием в PR (формат — unxed/tv3#15), без слов о происхождении. Сходство с прежней implementation:
   флаг только для цепочки ≥ 24, которую НЕ диктуют строка C++ и interface (совпал выбор, которого C++ не задаёт:
   порядок проверок, вспомогательная процедура, имя локальной переменной); продиктованная — запись в реестр, не флаг.
9. Зелёный `ci` + `AUDIT PASS` на одной голове — влить merge-коммитом, прогон main отменить (PR не отставал), отметить шаг
   в unxed/tv3#12, «Реестр» (п. 7), строки CI.md/BRANCHES.md снять, захват снять.

## 11. Итоги пилота S2 (TvGeom, 21-10-2026)

- Исполнитель: 66 с, 53 тыс. токенов, 8 вызовов; файл с первого раза собрался и прошёл `ci` (5 job'ов). Трения: Glob/Grep
  в среде исполнителя нет (не нужны: входы названы поимённо); правил файл через Edit — разрешено (п. 10.3); `tests.txt` с
  одними именами проверок не дал ему граничных значений, а старые имена в метках теста (`PointAdd`) путали — поэтому в
  п. 10.2 «имя — что ожидается» словами.
- Стандартный аудит дал FAIL, которого у прежней реализации не было: `TRect.Contains` в порядке операндов magiblot
  совпал на 43 токена с `dn214/_defines.pas:829`. Прямой перевод маленьких методов API совпадает с другими переводами той
  же строки — это ожидаемо и на крупных модулях (FV и DN переводят тот же Borland TV). Отсюда класс (д) и known.txt в
  том же PR (п. 10.8).
- Пониженный аудит: 1 попадание (`TPoint.<>` против `bp7tv/DRAGDROP.PAS:51`, 23 токена) — класс (д).
- Сходство с прежней implementation: 87 токенов (`TRect.Intersect`, `if … then …` вместо `max`) — продиктовано C++ без
  `Math`; правило флага уточнено (п. 10.8).
- Пробел S1b закрыт минимумом: вход `extra` в `tv3-audit.yml` (unxed/sandbox `45c9a2d`); отдельные режимы `lowered`/`prev`
  не нужны — команда п. 10.6.
