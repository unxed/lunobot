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

Список (план unxed/tv3#12, S2–S28; владелец считает унаследованных модулей 28): `TvGeom` (S2, пилот), затем `TvMem`,
`TvSys`, `TvKeys`, `TvEvents`, `TvObjs`, `TvTermIo`, `TvTermOs`, `TvUnix`, `TvViews`, `TvWindow`, `TvMenus`, `TvApp`,
`TvDialog`, `TvInput`, `TvCluster`, `TvList`, `TvHist`, `TvValid`, `TvMsgBox`, `TvFileDlg`, `TvChDir`, `TvColorSel`,
`TvHelp`, `TvVtView`, `TvFar2l`.

**Сверка списка — первый шаг S2 (до пилота):** 14 файлов `src/` с заголовком `Translated from magiblot/tvision` в
списке не названы (`tvansi`, `tvcell`, `tvclipcmd`, `tvcodepg`, `tvcolors`, `tvdrawbuf`, `tvfiles`, `tvmouse`,
`tvscreen`, `tvtext`, `tvtextview`, `tvtimer`, `tvutf8`, `tvutil`), а у 5 из списка (`tvmem`, `tvsys`, `tvtermos`,
`tvvtview`, `tvfar2l`) заголовка нет (status/12.md, «Находка»). Корневой коммит tv3 `652bd98` внёс все файлы `src/`
разом, поэтому «пришёл из tv» по истории tv3 не определить. Правило: переписывается объединение обоих списков
(40 модулей), кроме тех, про которые владелец скажет «не из tv» — вопрос владельцу через менеджера с этим списком;
до ответа порядок идёт по объединению, начиная с модулей обоих списков.

Порядок — ядро цикла событий первым (зависимости `TvEvents`: `TvKeys`, `TvGeom`, `TvUtf8`; затем `TvEvents`, `TvSys`); `TvApp` (`TProgram.GetEvent`, `Idle`) — как только перенесены его зависимости по `uses` (`TvViews`, `TvWindow`, `TvMenus` …), до того старый `TvApp` зовёт новый `TvSys`. Дальше — снизу вверх по графу `uses`: модуль идёт после всех модулей tv3, которые он использует (обе секции).
Граф строит скрипт по `main` (`grep -A30 -iE '^\s*uses' src/*.pas`, имена модулей `Tv*`), циклы через implementation
разрываются: модуль, использующий другой только в implementation, может идти раньше. Итоговый порядок — в п. 9 этого
файла (заполняет S2 до пилота), шаги S3… идут по нему.

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
   поведение). Нужен режим `mode=lowered` в `tv3-audit.yml` unxed/sandbox — шаг S1b ниже.
3. **Сходство с прежней реализацией** — `borrow-audit.py --max` новой implementation против старой implementation того
   же модуля (`main` до PR), обе секции вырезаны от `implementation` до конца. Печатается самая длинная цепочка raw/ren.
   Флаг: raw ≥ 24 или ren ≥ 200 (стандартные пороги): классификатор разбирает каждое такое место как в п. 6.2;
   общий результат — число и длина цепочек — в реестр. Ожидаемо высокое сходство коротких процедур (геттеры, `Assign`)
   — не флаг, если цепочка внутри одной процедуры длиной до 40 токенов и процедура повторяет поведение magiblot строка
   в строку. Нужен режим `mode=prev` в `tv3-audit.yml` — S1b.
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

Построено S2 (21-10-2026) по `main` `73c212e`: граф `uses` обеих секций всех `src/*.pas`, топологическая сортировка
объединения (40 модулей), ядро цикла первым; циклов нет. `*` — модуль с заголовком перевода вне списка плана (ждёт
ответа владельца, unxed/lunobot#240). Номер — порядковый; шаг S<n+1>. Модули вне объединения, от которых зависят
перечисленные (их не переписываем, пока S30 не скажет иное): tvappdir, tvclip, tvdosnames, tvformat, tvglyphs, tvpath,
tvpty, tvtermosbase, tvtermosnone, tvtermosunix, tvtermoswin, tvvt, tvvtext, tvvtkeys, tvwordnav, tvxlat.

```
1 TvGeom (S2, пилот)
2 TvKeys
3 TvUtf8 *
4 TvEvents — TvGeom, TvKeys, TvUtf8
5 TvSys — TvEvents, TvKeys, TvUtf8 (ядро: WaitForEvents, WakeUp, очередь задач, таймеры; `const TvAsyncCore = True`)
6 TvColors *
7 TvAnsi * — TvColors
8 TvCodePg * — TvUtf8
9 TvCell * — TvCodePg, TvColors
10 TvText * — TvCell, TvCodePg, TvColors, TvUtf8
11 TvDrawBuf * — TvCell, TvColors, TvText, TvUtf8
12 TvUtil * — TvCodePg, TvEvents, TvKeys, TvText, TvUtf8
13 TvObjs — TvUtil
14 TvScreen * — TvCell, TvColors, TvGeom, TvSys
15 TvTimer * — TvScreen, TvSys
16 TvViews — 11 модулей выше
17 TvMenus — … TvViews
18 TvWindow — … TvViews
19 TvApp — … TvMenus, TvWindow (TProgram.GetEvent, Idle по docs/ASYNC.md)
20 TvDialog — … TvWindow
21 TvFiles * — TvObjs, TvUtil
22 TvMsgBox — TvApp, TvDialog
23 TvValid — TvMsgBox
24 TvInput — … TvValid
25 TvList — … TvDialog, TvWindow
26 TvHist — … TvInput, TvList
27 TvFileDlg — … TvFiles, TvHist
28 TvChDir — … TvFileDlg
29 TvClipCmd *
30 TvCluster — … TvDialog
31 TvColorSel — … TvCluster, TvList
32 TvFar2l — TvUtf8 (по VTExts.md)
33 TvHelp — … TvWindow
34 TvMem — TvCell, TvCodePg, TvColors, TvEvents, TvScreen, TvSys
35 TvMouse * — TvEvents, TvGeom, TvSys
36 TvTermIo — TvCodePg, TvEvents, TvFar2l, TvKeys, TvUtf8
37 TvTermOs
38 TvTextView * — … TvWindow
39 TvUnix — … TvClipCmd, TvMouse, TvTermIo, TvTermOs, TvViews
40 TvVtView — … TvApp, TvDialog, TvMsgBox
```

## Шаги вне плана tv3, нужные протоколу

- **S1b (Л2)** — `tv3-audit.yml` в unxed/sandbox: вход `mode` (`standard` — как сейчас; `lowered` — п. 6.2 по входу
  `paths`, ref-список — фильтр `list.txt` по `bp7tv/`, `fpc/packages/fv/`, `fpcmain/packages/fv/`, `--raw-k 16
  --ren-k 100`; `prev` — п. 6.3 по входу `unit`: implementation модуля на `refs[0]` против implementation на
  `refs[1]`, `--max`). Готово: три прогона на `main` tv3 с `paths=src/tvgeom.pas`/`unit=tvgeom` завершены, вывод
  каждого режима в журнале прогона, артефакт удалён; ссылки — в status/12.md.
