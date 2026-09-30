# far2l terminal extensions: документация (PR elfmz/far2l#3082)

Состояние: ветка `extsdocs` форка unxed/far2l готова, вершина `b9ab680ba` (стопка: 5 коммитов владельца + атомарные коммиты Лунобота-1; после разбора замечаний elfmz из PR #3082). PR #3082 открыт (draft, название с [WIP]) — токен бота не правит название/описание и статус draft, тексты ниже.
Сравнение: https://github.com/elfmz/far2l/compare/master...unxed:extsdocs (файлы PR: https://github.com/elfmz/far2l/pull/3082/files).
Проверки: скрипт констант (82 имени/буквы против FarTTY.h/WinCompat.h + 38 фактов исходников) и 26 байтовых примеров против настоящего StackSerializer/base64 far2l — CI unxed/sandbox, workflow far2l-exts-docs-check, прогон 36778776486 (зелёный, на a03b2cab); два независимых субагента-ревьюера по коду и по репозиториям реализаций, найденное (около 30 пунктов) исправлено.
Проверено против far2l master c12197bc. Тикет chafa#311: токен не может комментировать (403), текст ниже.
Находки по f4/thruPTY (не чинилось, вне задачи): событие размера шлётся как `ESC _ f2l:` (с двоеточием — far2l его не декодирует) и с перепутанным порядком высота/ширина; ответ `w` (размер окна) с шириной сверху; `n` (уведомление) читает text/title в обратном порядке; vtui использует константный clientID `vtui-stateful-terminal-client-persistent-id-32chars` (любая программа может выдать себя за него — ID должен быть случайным и храниться на установку). «revision» из заметки: найден только lispnik/revision (Common Lisp порт Turbo Vision) — far2l-расширений там нет (только OSC 52), в документ не включён.

## Название и описание PR #3082 (английский)

Title:
Documentation of the far2l terminal extensions (VTExts.md)

Description:
This replaces the early draft in VTExts.md with documentation written from the code of the TTY backend (`WinPort/src/Backend/TTY/`) and of the built-in terminal (`far2l/src/vt/`), checked against `WinPort/FarTTY.h` and `WinPort/WinCompat.h`. The places where the code differs from the comments of the header are listed explicitly (the event and reply prefixes have no colon; the field order of `IMAGE_CAPS` and of the terminal size event; `WP_IMGCAP_JPG` is `0x003`; the `WP_IMG_ATTACH_*` values are numbers, not bits).

What is in it: what the extensions are and what they give over OSC 52, OSC 9/99/777, sixel and the Kitty protocols (safe clipboard reading, notifications, ad-hoc copy, the maximum window size, F-key titles, images, several clipboard formats including custom ones); the list of implementations (far2l, f4, Turbo Vision and turbo, putty4far2l, KiTTY, thruPTY) with their roles, with links to their sources and notes on what was seen in them; framing, the stack serializer, request IDs, activation and the `ESC [ 5 n` probe; every request, reply and event with the exact argument order and types; the clipboard (authorization, the paste-gesture rule for reads, chunked upload, data IDs, formats); images; byte-exact examples; the details and oddities of the far2l client and server as implemented; advice to implementers. The drag and drop proposal (#3647) is mentioned at the end.

The constants and letters in the text are checked by a script against `FarTTY.h` and `WinCompat.h`, and the byte examples are generated and decoded back with the `StackSerializer` and `base64` code of far2l in CI (https://github.com/unxed/sandbox/tree/main/far2l-exts-docs).


## Комментарий для hpjansson/chafa#311 (английский)

The far2l terminal extensions, including the image requests, are now documented in one place, written from the far2l source code and checked against it (every request, reply and event with the argument order and the types, the image capabilities and flags, byte-exact examples): https://github.com/elfmz/far2l/pull/3082 (the document itself: https://github.com/unxed/far2l/blob/extsdocs/VTExts.md). This supersedes the description that was posted earlier in this thread, which predates the changes of November and December 2025.

The protocol has not changed for a long time: the requests, replies and events are the same since 3 December 2025 (elfmz/far2l@01d4de48a, the last change of the image requests; the edits of `FarTTY.h` after that are comments only), so it looks stable. The document is still waiting for review upstream; as said above, it is up to you whether chafa needs a far2l-specific output, now that far2l also understands the Kitty graphics protocol.

*Lunobot-1 (node 91d86915909d88ed7991a74c; LNX; Claude Sonnet 5.5; subagent)*


30-09-2026 21:30Z: замечания elfmz и unxed из PR #3082 (12 review-комментариев, 6 issue-комментариев, 2025-11-15…2026-07-27) перечитаны целиком и учтены (кроме совета doxygen — не принят, причина в тексте); вершина `b9ab680ba`, CI unxed/sandbox зелёный: прогон 36779921740. Новых комментариев к PR не появилось. Остаётся за владельцем: название/статус PR #3082 (WIP, draft) и текст для hpjansson/chafa#311.
