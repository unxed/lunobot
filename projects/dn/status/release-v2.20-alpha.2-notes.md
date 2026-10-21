DN v2.20-alpha.2 — a prerelease: all work merged into `main` since v2.20-alpha.1 (124 commits linked to tickets). Built and checked by the full CI matrix on the release commit.

## New

- #32 Неудобная структура релиза. — package Linux releases for direct installation
- #36 M2: Rare archive formats cut behind DN_MINI — ZOO archives open again, and the mini build keeps them
- #37 I3c: Remaining Far key map (panel keys behind FarUxMode) — I3c part 1: Far UX mode, Ctrl+Gray+/- select by the extension, the terminal forms of Ctrl+Gray keys; Ctrl+F3/F4/F5 reach the sort handler before the status line; Far Ctrl+F6..F10 sort by size, no sort, creation time, access time, description (and 10 more changes)
- #39 I5: FarUxMode checkbox in dlgFMSetup (3 languages) — a check box "Far UX mode" in the File Manager setup
- #40 M3: mc-gap features within size budget (mc.ext, background copy, subshell) — Test Enter on a file with a dn.ext association on Linux; Run the command files of dn.ext and the user menu with sh on Unix; the user menu item chosen by its number runs on Linux (and 21 more changes)
- #38 I4: Far F-keys, dialogs, histories behind FarUxMode — unxed/dn#38 part 3: pty check of the keys DN shares with Far under FarUxMode; unxed/dn#38 part 3: dn-linux-farkeys waits for the command to finish before the history; unxed/dn#38 part 3: Ctrl+Enter in the command history compares the key code without the character byte (and 3 more changes)
- #89 Обвязка DN вокруг консольных архиваторов (план по шагам; multiarc из far2l только как справка) — document candidate commands and link the reference from README.
- #87 Переход DN на Better Pascal: safe-модель, корутины и асинхронная архитектура (план по шагам) — add Safe Pascal source census; контракт Better Pascal и подмодуль bp без использования (unxed/dn#87, шаг 2)
- #88 Фоновое копирование: что ещё не сделано и атомарный план (продолжение части 4 тикета #40) — Fix the crash on closing Copy jobs; check its percent in the pty test; JobsStatusText, the short state of the background copy; dn#88: skip the Copy jobs check when the copy finished before the list was read (and 15 more changes)
- #90 Сетевые протоколы в DN: FTP, SFTP, FISH/shell как у mc (план) — dn#90 step 0, part 1: network audit script and a layout check; TRemoteFS, TLocalFS and the split of an address (dn#90, step 3); the tests of remotefs and netsplit on ARM64 Linux (dn#90, step 3) (and 22 more changes)
- #4 Автообновление — read /releases (newest first) and take the newest release tagged v*, skipping the nightly channel; take only the asset built for this arch, and no update when there is none. DN_UPDATE_API overrides the URL (tests). tools/tests/test_autoupdate.py runs the script against a release list and assets served from file:// with id/uname stubbed.
- #19 Настройка числа столбцов панели (2 столбца, как в mc) — the appearance of the panel (Alt-K) gets the field "Name columns" (TPanelShowSetup.Columns, '1'..'9'; empty or '0' keeps the old way). With it set, CalcLength gives the name the width the panel leaves to each of the columns (at least 8), so they are exactly that many and wider. The field is in the dialog and the help in English, Russian and Ukrainian. A configuration saved before is read as before: its block of presets is the old size, TOldPanelSetupPresets, and PresetsFromOld moves it over with no fixed number of columns. The desktop sign goes to #82: the panel setup it streams has the new field, so a desktop of the old version is not read (as for any other version).
- #20 Битая символическая ссылка: красный цвет и префикс «!» (как в mc) — osdep gets SysLinkIsBroken (Unix: lstat says a link, stat of its target fails; False elsewhere) and the bit SysBrokenLinkAttr ($2000, not a DOS bit). TDrive.GetDirectory sets the bit in the file record of a found link whose target is missing (only links cost the extra stat), and the panel puts the new mark nfmBrokenLink, "!", where the dot of the name stands, like the shades of hidden and system files. A colour of its own needs a palette entry and is left for a next step.
- #166 FreeBSD: проверить сборку, заявить, добавить в CI; так же — другие платформы без больших усилий — проверка сборки под FreeBSD x86_64 в CI (unxed/dn#166, шаг 1)

## Fixes

- #33 При нажатии Cntrl-O появляется фиолетовый фон — user screen of Ctrl-O in the terminal colours, not white on magenta; dnrun (Linux): DN_RUN_PAUSE is 0 by default
- #52 Command line: the cursor position uses the byte length of the prompt (non-ASCII directory names) — the command line measures its prompt in columns, not in bytes
- #58 В низу панели дата вышестоящей директории показывается неверно — the '..' entry shows the date of the parent directory
- #17 DN_UTF8=0: non-ASCII FS names show as ? in UTF-8 Linux PTY — the linux64 job runs tools/dn-linux-locale.py again
- #78 Access violation in TWhileView.Write when a directory is copied on linux-aarch64 — fix(dn): the routines of MakeDirectories are nested once, not twice (aarch64)
- #80 Routines nested two levels deep read wrong outer variables on linux-aarch64 (follow-up of #78) — Добавлен сканер процедур DN, вложенных на два уровня и глубже.; Hoist DoScan out of DoScanValue in TValuesHolder.GetValue; Hoist the routines of DoIt out of it in UnpackImage (and 13 more changes)
- #31 Загрузка палитры не работает — while there is no menu, GetFileNameMenu answers "More": every caller opens its file dialog. Load palette now shows "Load Color Palette" and a palette written by Store palette is loaded back; Shift-F6 of the viewer shows "Select Xlation table".

## Known issues

- No open priority 1–2 bugs. Windows and Linux builds are tested in CI; please report anything that worked in v2.20-alpha.1 and broke here.

**Full Changelog**: https://github.com/unxed/dn/compare/v2.20-alpha.1...v2.20-alpha.2

*Lunobot-1 (node 19d368003c6c048e43dbec70; LNX; Claude Opus 5.5; subagent)*
