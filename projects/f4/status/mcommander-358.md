# blue-panels/mcommander#358 — resurrect (кастомная задача mcommander-358-20260930)

Состояние: не завершено, код не написан, веток и коммитов нет (остановлено словом владельца 30-09-2026, на стадии изучения).
Клон для продолжения: /tmp/lunobot-3/work/mc358-0930-2010/mc (ветка resurrect-358 от upstream/master 221319645, без правок). Прогонов CI нет.

## Что в тикете
Тикет пустой: 0 комментариев, только тело: "...чтобы можно было использовать M-commander как терминальный мультиплексор. Весит ерунду, кайфа добавляет очень сильно. Делать не сложно: есть проверенные референсы."

## Как устроено в far2l (источник: WinPort/src/Backend/WinPortMain.cpp, TTY/TTYRevive.cpp, TTY/TTYBackend.cpp)
- По умолчанию "immortal" (кроме Linux VT): процесс форкается, родитель-"шим" держит терминал, ребёнок делает setsid(), SIGHUP игнорирует, результат отдаёт родителю через notify-pipe; шим пересылает SIGWINCH ребёнку. Флаги --mortal/--immortal, FAR2L_ARGS.
- Терминал пропал (чтение/запись даёт ошибку): ребёнок создаёт TTY/srv-<pid>.ipc + .info (.info = заголовок консоли + feats), ждёт клиента, раз в 51 с делает utimes, чтобы tmpwatch не удалил.
- Новый far2l при старте перечисляет srv-*.info (проверка жив ли: connect, иначе файлы удаляются), печатает "Some far2l-s lost in space-time nearby" со списком, спрашивает индекс; пусто = новый экземпляр.
- Оживление: клиент шлёт по unix-сокету флаги и SCM_RIGHTS: stdin, stdout, конец notify-pipe (+ набор env: TERM, DISPLAY, ...). Сервер делает dup2 на свои 0/1, перенастраивает терминал, продолжает; клиент остаётся шимом (ждёт notify-pipe, пересылает SIGWINCH).

## Как в f4 (internal/terminal/session_unix.go)
Демон-сервер (--server <sock>, setsid) + клиент (--client), сессии в каталоге f4-sessions-<uid>, выбор сессии в пикере; клиент гоняет байты. Для mc выбрана модель far2l (передача fd), а не реле.

## План для mcommander (upstream/master 221319645; C, автотулс; CI: unxed/sandbox mcommander-full.yml, форматирование clang-format только по diff CI)
1. lib/tty/key.c: хук tty_hangup_hook; в tty_get_event после select, если input_fd читаем и poll даёт POLLHUP/POLLERR — вызвать хук, вернуть EV_NONE.
2. src/resurrect.c/.h (+ src/Makefile.am): сервер (stream-сокет AF_UNIX + .info в mc_tmpdir(); ждёт клиента; utimes раз в 51 с), клиент (перечисление живых, выбор номера, sendmsg SCM_RIGHTS: in, out, notify, TERM; ответ Y/N), шим (пересылка SIGWINCH и SIGINT — mc ставит VINTR=^G и ISIG, SIGTSTP/SIGQUIT игнорируются), resurrect_start() в main.c после load_setup (до mc_runtime_plugins_load), только MC_RUN_FULL и isatty(0/1), не внутри mcterm/вложенного mc (MC_SID/MC_TTY), не на Linux VT.
3. Оживление в ребёнке: dup2 на 0/1 (и 2, если он был тем же терминалом), замена notify, затем post_exec() (ca-mode, reset_prog_mode, мышь, bracketed paste, kitty), tty_clear_screen(), dialog_change_screen_size(), update_xterm_title_path().
4. Код возврата: resurrect_exit_code(code) перед return из main + atexit, запись в notify-pipe только из процесса-владельца (у форкнутых фоновых потомков atexit не должен писать).
5. Включение: опция --immortal/--mortal (args.c) и ключ immortal в [Midnight-Commander] (по умолчанию выключено: смена модели процесса для всех — решение владельца; если нужен умолчанием как far2l — сменить константу). TERM нового терминала должен совпадать с TERM сессии (иначе не предлагать).
6. Тест tests/src/resurrect.c (check): сервер/клиент на unix-сокете в каталоге теста, fork клиента, передача fd (проверка записью через переданный pipe), зонд без сообщения, отказ при другом TERM. Документация: doc/man/mcommander.md (+ roff через вывод CI apply_generated), NEWS по стилю проекта.
7. Порядок: ветка resurrect-358 от upstream/master, один коммит, CI mcommander-full (apply_generated=true, форматирование взять из diff), затем compare-ссылка и текст PR (English) комментарием в blue-panels/mcommander#358 и в unxed/f4#1628, один notify_owner.

## Не сделано
Пункт поручения про #347/#348 (ветки far2l-keys-347, far2l-mouse-347, far2l-mcterm-347, osc52-clipboard, mcterm-osc52, bracketed-paste-block, far2l-clipboard-348 и compare-ссылки в unxed/f4#1628) не проверялся: в комментариях unxed/f4#1628 уже есть compare-ссылки и тексты PR для far2l-mouse-347, far2l-mcterm-347 и far2l-clipboard-348 (по прочтённому хвосту), остальное сверить. Ветки на origin есть: far2l-keys-347, far2l-mouse-347, far2l-mcterm-347, osc52-clipboard, mcterm-osc52, bracketed-paste-block, far2l-clipboard-348.


## Решение владельца (30-09-2026)
Resurrect включён по умолчанию, как в far2l (не `--immortal`, а выключатель `--mortal`/ключ конфига).
