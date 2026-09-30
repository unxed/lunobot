# mcommander: готовые названия и описания для PR владельца

Токен бота не правит PR в blue-panels/mcommander (`updatePullRequest` → 403), поэтому готовые
тексты лежат здесь. Название = заголовок головного коммита ветки, описание = тело коммита;
строка «Builds on…» стоит первой там, где в PR видны коммиты предыдущих звеньев стопки.
Стопка веток задумана: мейнтейнер принимает зелёные PR, затем те, что стали зелёными после этого.

Порядок PR: #359 (osc52) → #360 (far2l keys, включает Win32 input) → #365 (mouse) → #366 (mcterm)
→ #361 (DnD) → #363 (DnD mcterm) → #364 (progress); #362 (режим Far, части 1–2) независим.
Ветки пересобирались после открытия PR; сверяй sha с веткой. Не созданы: `win32-input-mode`
(#347, отдельным PR), `bracketed-paste-block` (#351/#352), `far2l-clipboard-348` (#348),
`far-mode-349-3` (часть 3 режима Far, прогон красный).

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

