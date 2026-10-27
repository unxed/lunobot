# Unit TvClipCmd - functional specification

## 1. Purpose

TvClipCmd reads and writes the system clipboard by running helper programs of the operating system (`wl-copy`, `xsel`, `xclip`, `pbcopy`, `clip.exe` under WSL, ...), and shows desktop notifications through `notify-send` or `osascript`. It is the first way a text mode program tries to reach the clipboard; every routine returns False when there is no program or the program failed, and the caller then goes on to other ways (the terminal OSC 52 sequence, the program's own buffer). The unit is meaningful on Unix-like systems only; on all other systems every routine is a stub that does nothing and returns False or the empty text.

The routines are synchronous and block the calling thread for at most about 1.5 seconds per call. They keep global state (a lazily built table) and change the process-wide SIGPIPE disposition during a write, so call them from one thread at a time (in practice the UI thread).

## 2. Interface

```pascal
unit TvClipCmd;

interface

function ClipCmdSet(const Text: AnsiString): Boolean;
function ClipCmdGet(out Text: AnsiString): Boolean;

type
  TClipEnvProc = function(const Name: AnsiString): AnsiString;

var
  OnClipEnv: TClipEnvProc = nil;

function NotifyCmd(const Title, Text: AnsiString): Boolean;
function ClipCmdSetName: AnsiString;
function ClipCmdGetName: AnsiString;
```

Source uses mode objfpc and `{$H+}` (long strings). `OnClipEnv`: when assigned, the unit reads the environment variables `PATH`, `DISPLAY` and `WAYLAND_DISPLAY` through it instead of the process environment (tests supply their own values; an unknown name should return the empty text). No other variable is read through it.

## 3. Behaviour (Unix)

### 3.1 The programs

Two ordered tables are used; an entry is a program name (or absolute path), fixed arguments, and an optional *required environment variable* that must be set (non-empty) for the entry to be considered. Not-Darwin (Linux, BSD, WSL):

* Writing (the text goes to the program's standard input): 1. `/mnt/c/Windows/System32/clip.exe` (no argument, no required variable; the text is sent with one NUL byte appended, because clip.exe needs it); 2. `wl-copy` (needs `WAYLAND_DISPLAY`); 3. `xsel --input --clipboard` (needs `DISPLAY`); 4. `xclip -in -selection clipboard` (needs `DISPLAY`).
* Reading (the text is the program's standard output): 1. `wl-paste --no-newline` (`WAYLAND_DISPLAY`); 2. `xsel --output --clipboard` (`DISPLAY`); 3. `xclip -out -selection clipboard` (`DISPLAY`); 4. `/mnt/c/Windows/System32/cmd.exe /D /Q /C <script>` (WSL, no required variable) whose output is UTF-16LE.

On macOS (Darwin) the tables hold one entry each: `pbcopy` and `pbpaste`, no arguments, no required variable.

An entry is *available* when its required variable (if any) is non-empty and its program can be found: a name that is an absolute path must be a regular file with execute permission; any other name is searched in the directories of `PATH` (separator `:`; an empty directory element means the current directory; if `PATH` is empty the list `/usr/local/bin:/bin:/usr/bin` is used) and the first directory holding a regular, executable file of that name wins. Only the **first available entry** of a table is used; if its run fails, the next one is not tried. The tables are built on first use.

The WSL reading script is a one-argument command line for `cmd.exe`. In prose: for the first writable of the directories `%TMP%`, `%TEMP%`, `%USERPROFILE%`, `.`, `..` it composes a script file name made of the hex process id and `%RANDOM%` with the extension `.vbs`; it writes into that file a one-line Visual Basic script that creates an HTMLFile object and writes `ParentWindow.ClipboardData.GetData("Text")` to standard output; it runs `cscript //NoLogo //B //U` on that file (so the output is UTF-16LE), deletes the file whether cscript succeeded or not, and exits with status 0 only if cscript succeeded. The quote character inside is the environment variable `q`, because `cmd.exe` called from WSL loses double quotes (microsoft/WSL#2835); for this entry the child's environment is the current environment plus `WSLENV=q` and `q="`. Source gate: the Visual Basic function name that creates a COM object must not appear in the source file as one contiguous word (the tree's checker greps for it); build it from pieces.

### 3.2 Running a program (shared by all calls)

The program is run with its full path as argument 0, followed by its fixed arguments (an empty argument is skipped, so no empty argument can be passed; at most 12 arguments). Pipes and process: a pipe is created; the program is started with fork and exec in a child whose standard error and the unused one of standard input/output are `/dev/null`; if the pipe or the fork fails the call fails.

* **Write mode**: the child's standard input is the pipe. The parent closes the read end, ignores SIGPIPE for the time of the write (restoring the old disposition afterwards), sets the pipe non-blocking and writes all bytes, waiting with poll when the pipe is full (so texts much larger than the pipe buffer, such as 400 KB, work). A write error other than "would block"/interrupted (for example the program ended early) stops the writing and counts as failure. Then the write end is closed.
* **Read mode**: the child's standard output is the pipe. The parent closes the write end, sets the read end non-blocking and reads until end of file, waiting with poll.
* **Time limit**: one deadline of 1500 ms is set when the transfer starts and covers both the transfer and the wait for the program to end (polled about every 5 ms). If the deadline is passed with the transfer or the program unfinished, the program (only that process) is killed with SIGKILL and reaped, and the call fails.
* **Result**: write mode succeeds when the program exited normally with status 0 and every byte was written. Read mode succeeds when the program exited with status 0 and end of file was reached, **or when it produced at least one byte** (output of a program that then fails is accepted); a program that produced nothing and failed, or that was killed on time out, is a failure. A program that exits with 0 and gives nothing is a success with an empty text.

### 3.3 Routines

**ClipCmdSet(Text)**: False if no entry of the write table is available. Otherwise runs it in write mode with Text (a NUL appended for `clip.exe`) and returns the result. The text goes through byte for byte (UTF-8, line breaks and NUL bytes included); an empty text is allowed.

**ClipCmdGet(Text)**: sets Text to the empty text first. False if no entry of the read table is available. Otherwise runs it in read mode; Text receives the whole output byte for byte. For the WSL entry the output is converted from UTF-16LE to UTF-8 (an odd trailing byte is dropped; no BOM handling beyond the conversion; surrogate pairs become 4-byte sequences). On a False result Text is empty (the old unit could leave partial output there; the intended behaviour is the empty text).

**ClipCmdSetName / ClipCmdGetName**: the full path of the program that `ClipCmdSet` / `ClipCmdGet` would use now, or the empty text when none is available. For tests and for the `TV_CLIPBOARD_DEBUG` diagnostics of the caller.

**NotifyCmd(Title, Text)**: True when a notification program ran and ended with status 0 within the time limit. An empty Title or Text is replaced by one space (an empty argument cannot be passed). Darwin: runs `osascript -e 'display notification "<Text>" with title "<Title>"'`, where in both texts a backslash and a double quote are preceded by a backslash and CR/LF are replaced by a space. Other systems: False at once when both `DISPLAY` and `WAYLAND_DISPLAY` are empty; otherwise runs `notify-send -- <Title> <Text>`. The program is looked up like in 3.1 (in `PATH`); if absent the result is False. It is run like a write of an empty text (input from an empty pipe) and its result is the result of the run.

## 4. Behaviour (non-Unix)

`ClipCmdSet` False; `ClipCmdGet` False with the empty text; `NotifyCmd` False; both name functions return the empty text. `OnClipEnv` still exists.

## 5. Units used

* `SysUtils` (implementation): environment access, tick counter (`GetTickCount64`), sleeping, UTF-16 to UTF-8 conversion (`UTF8Encode` of a `UnicodeString`).
* `BaseUnix` (implementation): pipe, fork, exec, dup2, poll, waitpid, kill, signal action, file status and access checks, fcntl.
* `TvPath` (implementation): `PathIsRooted(Name)`, `PathJoin(Dir, Name)`, and the Unix path rules' list separator (`:`).

## 6. What the tests pin down (t_clipcmd, Unix)

The test creates a private directory with shell-script fakes `xclip` (`-in` copies standard input to a file, `-out` prints the file), `xsel` (same with `--input`/`--output`, another file), `wl-copy` and `wl-paste` (their own file), puts that directory as the whole `PATH` through `OnClipEnv`, and drives `DISPLAY` and `WAYLAND_DISPLAY` through it. The fakes dispatch on the exact words `-in`/`-out`/`--input`/`--output` among the arguments, so the arguments must be as listed in 3.1.

1. Without `DISPLAY` and `WAYLAND_DISPLAY`: both names empty, `ClipCmdSet('x')` and `ClipCmdGet` False.
2. `DISPLAY=:0`: the name of both directions contains `/xsel` (xsel before xclip). `ClipCmdSet` of a two-line Cyrillic text (UTF-8, LF between the lines) True and the xsel file holds exactly those bytes; `ClipCmdGet` returns them.
3. After removing the fake xsel: names contain `/xclip`; a text with an embedded NUL (`abc`, NUL, `def`) is written and read back whole.
4. With `WAYLAND_DISPLAY` set also: names contain `/wl-copy`; write and read through the wl pair (file `.wl`).
5. A text of 20000 lines (about 400 KB, with UTF-8) is written (file equal) and read back equal.
6. An empty store: `ClipCmdGet` True with the empty text.
7. `xclip` that does `exit 1`: both calls False. `xclip` that sleeps 20 s: each call False and returns in under 4 seconds (time out 1.5 s, the process killed).

A test program for the new unit should additionally check: `NotifyCmd` with a fake `notify-send` that records its arguments (`--`, title, text; blanks for empty ones) and with no display (False); a read program that prints text then fails is accepted; a write program that exits early with status 0 without reading a large text fails; `OnClipEnv` returning the empty text for `PATH` falls back to the default path list.

## 7. Observed oddities

Intended: first available program only; success of a read that gave output but a failing status; the NUL appended for `clip.exe`; UTF-16LE conversion for the WSL reader; empty arguments replaced by a blank in `NotifyCmd`.

Accidental or questionable: the write table puts `clip.exe` first and the read table puts the WSL reader last, so on a WSL system that also has X11 or Wayland the text is written to the Windows clipboard and read from the X/Wayland one (keep the order; it follows the original library); only the started process is killed on time out, so a shell script that started a long grandchild leaves it running; on time out the old code returned with partial output in the out parameter (see ClipCmdGet); `ScriptStr` exists on all Unix systems although only Darwin uses it; the 12-argument limit is silent; the tables of at most four entries are fixed in size.
