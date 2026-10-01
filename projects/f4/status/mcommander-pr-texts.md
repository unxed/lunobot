# mcommander: готовые названия и описания для PR владельца

Токен бота не правит PR в blue-panels/mcommander (`updatePullRequest` → 403), поэтому готовые
тексты лежат здесь. Название = заголовок головного коммита ветки, описание = тело коммита;
строка «Builds on…» стоит первой там, где в PR видны коммиты предыдущих звеньев стопки.
Стопка веток обязательна (правило владельца): мейнтейнер принимает зелёные PR, затем те, что стали зелёными после этого.

Порядок PR: #359 (osc52) → #360 (far2l keys, включает Win32 input) → #365 (mouse) → #366 (mcterm)
→ #361 (DnD) → #363 (DnD mcterm) → #364 (progress); #362 (режим Far, части 1–2) независим.
Ветки пересобирались после открытия PR; сверяй sha с веткой. Не создан: `win32-input-mode`
(#347, отдельным PR). Открыты: #367 (`bracketed-paste-block`), #368 (`far2l-clipboard-348`), #369 (`far-mode-349-3`).

## #359 (mcterm-osc52)

TITLE:
mcterm: pass a program's OSC 52 clipboard text on to the terminal mc runs in

BODY:
> Builds on the editor OSC 52 copy fallback (first commit of this PR). Review the last commit.

A program in the built-in terminal (vim, tmux, an SSH session, a shell script)
that sets the clipboard with OSC 52 had its sequence swallowed by the terminal
emulator. The payload, which is far longer than the buffer of the other
sequences, is now collected on its own (up to 100000 bytes, more is dropped
whole), decoded, and passed to the terminal mc itself runs in with the OSC 52
writer of the editor's clipboard fallback (so MC_OSC52=0 turns it off there
too). The clipboard is only set: a query ("?") is not answered, and an empty
or malformed payload is ignored.

Follows the OSC 52 copy fallback of the editor; tests in vterm_terminal.

---

## #360 (far2l-keys-347)

TITLE:
Terminal input: support the far2l keyboard extensions

BODY:
> Builds on the Win32 input mode change (first commit of this PR). Review the last commit.

Ask the terminal for the far2l extensions together with the other start-up
questions (APC far2l1; MC_FAR2L=0 skips it, and so does a screen or tmux TERM).
A terminal that answers APC far2lok is taken to send every key as
APC f2l <base64> ST, and the extensions are switched on and off with far2l1 and
far2l0 wherever the kitty keyboard protocol is switched on and off (start,
exit, around an external command), so a subshell or a child program never gets
a terminal still in far2l mode. The key packets (K/k and the short C/c) carry
the virtual key, character and Windows control key state, and are turned into
the code a legacy terminal gives for the same key with the rules of Win32 input
mode, so Ctrl-Enter, Shift-Tab, Ctrl-Shift letters and Alt with function keys
are told apart. Releases, replies, mouse and resize packets are no key. While
the extensions are on, the kitty protocol and Win32 input mode are not asked
for: they would only carry the same information twice. A terminal without the
extensions is never told about them and behaves as before.

Builds on the Win32 input mode change (its key decoding is reused). Documented
in doc/FAR2L_INPUT.md; replayable decoder tests in tests/src/tty_far2l_input.c.

Related to the request for a negotiated keyboard input layer.

---

## #365 (far2l-mouse-347)

TITLE:
Terminal input: take the mouse of the far2l extensions

BODY:
> Builds on the two commits below it (Win32 input mode, far2l keyboard extensions). Review the last commit.

A terminal with the far2l extensions on sends its mouse only as APC f2l packets
('M' and the compact 'm'), never as xterm reports, so with the keyboard part of
the extensions alone the mouse was dead. A packet is now turned into the SGR
report (ESC [ < b ; x ; y M or m) mc asks other terminals for and handed back to
the keyboard: presses and releases of the left, middle and right buttons, wheel
turns, and moves with a button held in button-event tracking. Moves with nothing
held, horizontal wheel turns and everything while the mouse is off are no event.

Builds on the far2l keyboard extensions change. Decoder tests in
tests/src/tty_far2l_input.c.

Related to the request for a negotiated keyboard input layer.

---

## #366 (far2l-mcterm-347)

TITLE:
mcterm: give the far2l extensions to the programs in the embedded terminal

BODY:
> Builds on the commits below it (Win32 input mode, far2l keyboard, far2l mouse). Review the last commit.

The embedded terminal now takes APC strings itself, where their text used to be
drawn on the screen. A program that asks with APC far2l1 is answered far2lok when
the terminal M-Commander runs in has the extensions, and gets no answer when it has
not; far2l0 and the emulator's reset end the mode. While it is on, the keys handed
to the program are far2l packets (a press and a release, with the virtual key,
character and control key state) instead of xterm bytes, so f4 or far2l in mcterm
tell Ctrl-Enter from Enter, Shift-Tab from Tab and the like; a key with no such
form (a byte of a character out of ASCII) goes as before. The negotiation of
M-Commander with its own terminal and that of the program stay on their sides.

The About box shows which keyboard input is active (far2l, kitty, win32 or
legacy), so terminal reports can name it. doc/FAR2L_INPUT.md gets the embedded
terminal, the About line and a manual check for Linux, Windows and multiplexed or
remote terminals; replayable tests for the emulator and the key encoder.

Builds on the far2l keyboard extensions change.

Related to the request for a negotiated keyboard input layer, both for an
external and for the embedded terminal.

---

## #361 (dnd-357)

TITLE:
Take files dropped on a far2l terminal into the panel under the drop

BODY:
> Builds on the far2l input commits below it (Win32 input mode, keyboard, mouse, embedded terminal). Review the last commit.

Files dragged from the desktop onto a far2l terminal window are copied into
the directory of the panel they landed on. This is the application side of
the terminal drag and drop protocol that rides on far2l extensions
(https://github.com/unxed/f4/blob/main/docs/FAR2L_DND.md, elfmz/far2l#3647,
unxed/f4#1628), the same one f4 speaks.

How it works. Once the far2l extensions are on, mc binds drop reception
(BIND). A drop reaches mc as one small INPUT_DND event that names an offer;
mc pulls the list (LIST) and the byte ranges it wants (READ), one bounded
chunk per reply, and releases the offer (CLOSE). Nothing travels unasked, so
the same protocol serves a local mc and one behind SSH.

The copy is done by mc's own VFS into the panel's current directory, so a
panel showing an archive or a remote host needs no special case. The panel is
found from the cell the terminal reports; if the position is unknown, mc asks
before copying to the active panel instead of guessing. Existing files ask for
overwrite/skip/overwrite all/cancel; a half-received file is removed. Only
plain files are taken (directories are outside the first version of the
protocol), names that are not plain names (slashes, "..", control characters)
are refused, every length is checked against the frame before allocation, and
a request that gets no answer times out instead of hanging mc.

It builds on the far2l keyboard and mouse support: the extensions are switched
on there, and off while an external command runs; mc unbinds drop reception
before they go off. The change is documented in doc/FAR2L_INPUT.md.

Tests: the wire codec is checked against the byte vectors of the specification
(section 10, made with far2l's own StackSerializer), plus BIND, LIST and error
replies, INPUT_DND and the name checks (tests/lib/far2l.c).

Not in this change: directories, several READs in flight (window is 1), a
progress bar and Esc to cancel a long copy, and dropping into the built-in
terminal for the programs that run in it.

---

## #363 (dnd-357-mcterm)

TITLE:
mcterm: serve far2l drag and drop to the programs in the terminal

BODY:
> Builds on the commits below it. Review the last commit.

The built-in terminal is now a far2l terminal for the program that runs in it, so that a
file dropped on the outer far2l terminal window over it reaches the program, and mc inside
mc inside a far2l terminal works. Each hop is an application for the offer outside it and
the terminal for the one inside: the program's LIST and READ are answered with LIST and READ
of the outer offer, chunk by chunk with nothing kept in between, and CLOSE (or far2l0, a new
binding, the lease running out, the terminal closing) releases it.

The emulator keeps answering far2l1 and giving the program its keys as far2l events, as
before; what is new rides on that. It now holds every APC that arrives whole for the
terminal, which answers the far2l requests in them: BIND is refused while the terminal mc
runs in has no drop reception bound, the other interactions are answered with the empty
reply. The APCs of a program are still not drawn as text.

New: the terminal's side of the codec (lib/tty/far2l.c), src/mcterm/mcterm_far2l.c, APC
capture in the terminal emulator, and a drop landing on the terminal in the file manager's
drop handler. Tests replay the exchange against a fake outer terminal
(tests/src/mcterm_far2l.c). Documented in doc/FAR2L_INPUT.md.

Not in this change: the mouse events of the extensions for the program, directories, more
than one request in flight, a progress bar.

Builds on the change that gives the far2l extensions to the programs in the embedded
terminal.

---

## #364 (dnd-357-progress)

TITLE:
Show the progress of files dropped on a far2l terminal, and let Esc give it up

BODY:
> Builds on the commits below it. Review the last commit.

A file that comes over SSH takes time, and until now mc showed nothing while it did. Once the
copy lasts more than half a second a dialog shows the file, its place among the dropped ones
and how much of it is in; Esc or Abort gives the drop up. The file that was coming is
removed, the files already received stay, and the offer is released as cancelled, which the
terminal takes as the user's choice and not as a failure.

The dialog is the one the other long operations of the file manager use, so it also keeps the
screen alive. While a drop is being received another is turned down (the dialog reads the keys,
and with them a second drop announcement).

---

## #362 (far-mode-349-2)

TITLE:
Far mode: the keys of Far Manager in the editor and the viewer

BODY:
> Builds on the first part of Far mode (first commit of this PR). Review the last commit.

Second part of the opt-in Far mode: the editor and the viewer answer to the
keys of Far Manager while the mode is on (Options > Configuration > Far
Manager keys, or far_mode=true). With the mode off nothing changes.

Editor: Ctrl-F7 replaces (F4 quits the editor, together with F10 and Esc, as in
Far), Alt-F8 goes to a line, Ctrl-F3 shows the line numbers, Alt-F11 shows the
history of the edited files, Ctrl-Z undoes, Ctrl-U deselects the block and
Ctrl-A selects all. A key that an action gives up for this goes to the action
that Far gives it to: Ctrl-F7 no longer continues the search (Shift-F7 does),
Ctrl-Z no longer moves a word left.

Viewer: Alt-F8 goes to a position, Alt-F7 continues the search in the opposite
direction, Alt-F11 shows the history of the viewed files. The keys that these
actions had before stay bound where the manual says so.

The keys come from the far2l help; what differs (F3 still marks a block in the
editor, the clipboard keys Ctrl-C, Ctrl-V and Ctrl-X are not bound, the viewer
keeps F8, F9, Space and plus and minus) is listed in the "Far mode" section of
the manual. The tests check the keys with the mode on and that the editor and
the viewer are unchanged with it off.

Related to the proposal of an opt-in Far mode (issue 349); dialogs, workflows,
the listing modes and the command line keys are next.

---


## #367 (bracketed-paste-block)

TITLE:
tty: take a bracketed paste as one block

BODY:
The text between ESC[200~ and ESC[201~ was fed through the key loop byte by
byte: every byte was looked up in the keymap, the editor pushed an Undo step
for each, and a long paste was slow. Now the dialog loop asks for the whole
paste (MCKEY_PASTE) and sends it to the focused widget as one MSG_PASTE; a
paste that no widget takes goes to the owner as MSG_UNHANDLED_PASTE, which the
file manager passes to the command line.

The text is cleaned when it is read: a line break is LF, a tab stays, every
other control byte and ESC are dropped, so nothing in it runs as a command or
ends the paste early. At most 16 MiB are kept, and a paste that has been silent
for 2 seconds without ESC[201~ is given up.

- mcedit inserts the text as typed but as one step for Undo, without auto
  indent, and draws the screen once (edit_paste_text).
- an input line inserts the text on one line: a line break or a tab becomes a
  space, so a paste of several lines does not submit the input.
- mcterm tracks DECSET 2004 (mcview_vterm_bracketed_paste). A program that has
  asked for it gets the paste as one block in ESC[200~ ... ESC[201~, with no
  ESC in the text; otherwise the lines are joined into one and no line runs by
  itself. It works in the terminal view and at the panels' command line over the
  shell (mcterm_overlay_handle_paste).

Loops that do not go through the dialog (progress, find) keep the old
behaviour. Tests: tty_paste (reading, cleaning, limit, timeout), mcterm_paste,
the mode in vterm_terminal, and the editor paste in edit_undo_history.

---

## #368 (far2l-clipboard-348)

TITLE:
clipboard: use the clipboard of a far2l terminal

BODY:
With the far2l extensions on and no clipboard_store / clipboard_paste command,
a copy is put on the clipboard of the terminal and a paste takes the text from
it, through the clipboard requests of the far2l protocol (open, set or get of
text, close). The terminal asks its user first; a refusal, no text or no answer
in 15 seconds changes nothing. A configured command is used as before, and
nothing is sent when the extensions are off.

Keys typed while the terminal answers are put back. At most 4 MiB go either
way. Tests in tty_far2l_clipboard play the terminal.

---

## #369 (far-mode-349-3)

TITLE:
Far mode: listing modes and the keys of the command line

BODY:
Ctrl-1 to Ctrl-0 switch a panel to the ten listing modes of Far, Ctrl-A
opens the attributes of a file, Ctrl-F puts its full name into the command
line, and Ctrl-E, Ctrl-X and Ctrl-Y walk the history of the command line and
delete the line, in the command line and in the edit lines of the dialogs.
The prefix of the extended commands moves to Alt-X while the mode is on.

A terminal that speaks the kitty keyboard protocol sends Ctrl with a digit;
it was turned into the control character of the same code (Ctrl-1 became
Ctrl-Q), and is now the digit with the modifier, as the key names of the
keymap say it.

---

Сверка 2026-09-30 (Лунобот-1, субагент): у #359–#369 название совпадает с заголовком последнего коммита ветки, описание — с телом коммита (без Co-Authored-By); у #367–#369 абзацы в описании без переносов строк, смысл тот же. Замена вручную не требуется.

---

## Перебазирование под master 221319645 (PR #356) и порядок мержа

Порядок мержа: #359, #362, #369, #360, #365, #366, #361, #363, #364, #367, #368. Моделирование `git merge --no-ff` этой цепочки на свежем upstream/master (221319645) проходит без конфликтов; итоговое дерево сверено с ожидаемым (s368 плюс правки #359, #362, #369), дублей нет. CI mcommander-full на каждом новом коммите зелёный. mergeable у всех 11 PR: MERGEABLE (UNSTABLE у GitHub - это статус проверок самого PR).

| PR | ветка | прежний sha | новый sha | mergeable / CI |
| --- | --- | --- | --- | --- |
| #359 | mcterm-osc52 | ce710a90f | без изменений | MERGEABLE |
| #362 | far-mode-349-2 | d394f9567 | без изменений | MERGEABLE |
| #369 | far-mode-349-3 | 2c9c1dc81 | b25b3ead9 | MERGEABLE, CI зелёный |
| #360 | far2l-keys-347 | 9e50dd916 | 1e86f27f8 | MERGEABLE, CI зелёный |
| #365 | far2l-mouse-347 | 1c33d0655 | 6f774677c | MERGEABLE, CI зелёный |
| #366 | far2l-mcterm-347 | aa840dd17 | 1e7e18578 | MERGEABLE, CI зелёный |
| #361 | dnd-357 | 6ef2b49df | 96914b163 | MERGEABLE, CI зелёный |
| #363 | dnd-357-mcterm | 9cd1f0cb9 | f3493cb69 | MERGEABLE, CI зелёный |
| #364 | dnd-357-progress | 7b614d7d1 | 48c540b93 | MERGEABLE, CI зелёный |
| #367 | bracketed-paste-block | 00e02140e | 98e920e26 | MERGEABLE, CI зелёный |
| #368 | far2l-clipboard-348 | 23de932d5 | defb1b5f4 | MERGEABLE, CI зелёный |

Конфликты и решения:
- #369 против #362 (CHANGELOG, doc/man, src/keymap.c, tests/src/keymap_reload.c): коммит перенесён на вершину #362, обе стороны слиты дословно.
- #360 против master (lib/tty/tty.c, новый порядок опросов): запросы идут kitty `?u`, DECRQM 9001, APC far2l1, `16t`, OSC 11 с ST, DA1 последним; ответы на наши запросы приходят до DA1, поздние ответы в клавиатуру не попадают (как сделал мейнтейнер).
- #360, #366, #363 против #359 (tty.c/h, vterm.c, mcterm.c, vterm.h): свои вставки сдвинуты в соседние места; без сдвига git сливал тихо, но с дублем (take_apc в vterm.h).
- #363: убран неиспользуемый `answer` в tests/src/mcterm_far2l.c (-Werror).
- #367 и #368 как один коммит: свои хунки сдвинуты от хунков цепочки и #359 (key.c, key.h, Makefile.am, vterm_terminal.c); доку far2l-буфера вынес в новый doc/FAR2L_CLIPBOARD.md (FAR2L_INPUT.md создаётся цепочкой, правка даёт add/add).
- По смыслу: в clipboard_file_to_ext_clip при пустом clipboard_store сначала far2l-буфер (если терминал его дал), иначе OSC 52 из #359.

## Новые ветки (30-09-2026, Лунобот-1, воркер mcfar349)

12. **Режим Far, часть 4 (диалоги, Ctrl-\\ в корень, быстрый поиск, сортировки, Ctrl-G)** — после #362 и #369, от них зависит (ветка их продолжает): https://github.com/blue-panels/mcommander/compare/master...unxed:far-mode-349-4?expand=1
13. **Документация терминального ввода, буфера обмена, вставки и DnD (#347, #348, #357)** — после #359–#368 (несёт их код, как #368): https://github.com/blue-panels/mcommander/compare/master...unxed:docs-terminal-349?expand=1

Мерж по порядку стопки (1–11, затем 12 и 13) на свежем master `221319645` проходит без конфликтов; CI mcommander-full зелёный на каждой ветке и на слитой цепочке целиком. Ветка п. 12 продолжает `far-mode-349-3` (в сравнении 4 коммита, название и описание не подставятся сами: вставьте ниже); п. 13 — один коммит на master, подставится само.

<details><summary><b>п. 12</b> (far-mode-349-4) — Far mode: dialogs, the root directory, fast find and more sort keys</summary>

**Название:**
```
Far mode: dialogs, the root directory, fast find and more sort keys
```
**Описание:**
```
> Builds on the commits below it (the Far mode parts of #362 and #369). Review the last commit.

The next part of the opt-in Far mode (far_mode, off by default): the dialogs
and the workflows that Far users reach for.

Dialogs. Ctrl-Enter does the default action of a dialog, and the numeric plus
and minus (and those of the main keyboard) switch the check box that has the
focus on and off; the other keys of the dialogs are the same in Far and in
M-Commander, and the parts of Far that M-Commander has no counterpart for
(moving a dialog, a file name into an edit line) are listed in the manual.

Panels. Ctrl-\ goes to the root directory of the file system, the archive or
the remote host the panel shows, and the directory hotlist moves to Alt-\.
Alt, or Alt-Shift, with a character is the fast find of Far, with Ctrl-Enter
and Ctrl-Shift-Enter for the next and the previous match; an Alt key that has
an action keeps it, so nothing of M-Commander is lost. Ctrl-F7, Ctrl-F8,
Ctrl-F9 and Ctrl-F11 sort by nothing, by the time of change, by the time of
access and by the owner. Ctrl-G applies a command to the tagged files (the
file under the cursor when none is tagged) with %f, %n and %x for the name,
the name without the extension and the extension (new action ApplyCommand).
Alt-F6, Alt-F10, Shift-F9 and Shift-F10 create a hard link, show the tree of
directories, save the setup and choose the last menu item.

Ctrl-H, Ctrl-M and Ctrl-Z stay unbound on purpose, since a terminal sends
Backspace and Enter as the first two and M-Commander cannot tell them apart;
the manual says so, with the rest of the differences from Far. The mode is a
layer over the keymap, so keymap.ini of the user still has the last word, and
with the mode off nothing changes: tests in tests/src/keymap_reload.c check
the keys with the mode on, with it off and across a switch.
```
</details>

<details><summary><b>п. 13</b> (docs-terminal-349) — doc: terminal input, clipboard, paste and dropped files</summary>

**Название:**
```
doc: terminal input, clipboard, paste and dropped files
```
**Описание:**
```
> This commit carries the code of #359 to #368 that it documents (the far2l input, the clipboard, the bracketed paste and the drop changes). Review doc/man/mcommander.md.

The manual said nothing about what M-Commander asks of the terminal it runs in,
so a report about a key, a copy or a paste could not name the path it took. A
new chapter, "Terminal input, clipboard and dropped files", says it, for
users and for plugin authors:

- Keyboard input: the far2l extensions, the kitty keyboard protocol and Win32
  input mode, what is asked at start and when it is not (screen and tmux, the
  MC_FAR2L, MC_KITTY_KEYBOARD and MC_WIN32_INPUT variables), how it is switched
  off around a child program, what the built-in terminal keeps apart, the
  "Keyboard input:" line of the About box, that the key codes of plugins and
  keymaps do not change, and a short manual check for each terminal path.
- Clipboard: the order of the copy (clipboard_store, the far2l terminal, OSC 52),
  the size limits, MC_OSC52=0, the OSC 52 of a program in the built-in terminal,
  tmux and remote terminals, the clipboard_store example that prints OSC 52,
  and why OSC 52 is written but never read.
- Paste: bracketed paste as one block, one Undo step, what happens to line
  breaks and control bytes, and the built-in terminal.
- Dropped files: what a drop does, the limits, and what is not there yet.

The About command, the clipboard_store setting and the environment section
point to it. No code is changed.
```
</details>


## Перебазирование #371 и #372 (01-10-2026, по слову владельца «Разрешаю»)

Причина: #371/#372 давали конфликт в src/clipboard.c при мерже цепочки. Пересобраны как один коммит
поверх upstream/master 221319645 с деревом (смоделированный мерж #359..#368 + собственное изменение);
заголовки, тела и автор коммитов прежние. Собственный diff #371 не трогает clipboard.c (far2l-буфер
раньше OSC 52 уже в #368), конфликт был только из-за старого дерева ветки.

- #371 resurrect-358: d5a6ef6e3 -> 083aac5d6 (ahead 1, behind 0, MERGEABLE)
- #372 termux-build: 11b9ded6b -> 9bf0ccc7d (ahead 1, behind 0, MERGEABLE)
- CI (unxed/sandbox): mcommander-full resurrect-358 36801813298 зелёный; mcommander-full termux-build
  36801826963 зелёный; mcommander-termux termux-build 36801830383 зелёный.
- Моделирование: #359 -> #362 -> #369 -> #370 -> #360 -> #365 -> #366 -> #361 -> #363 -> #364 -> #367 -> #368
  -> #371 -> #372 на upstream/master 221319645 без конфликтов; порядок #359, #368 -> #371 -> #372 тоже чистый.

Lunobot-Instance: Лунобот-1 (node 91d86915909d88ed7991a74c; LNX)
