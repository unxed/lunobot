# Unit TvProc

## 1. Purpose

TvProc runs other programs on behalf of a terminal program. `RunShell` hands the terminal back to the system, runs a command line in the system shell with the output visible, optionally waits for the user to press Enter, and takes the terminal again. `RunQuiet` runs a command line in the shell without touching the screen or the terminal. `RunCapture` runs a program directly (no shell) and returns everything it wrote on standard output and standard error. `RunFirstLine` returns the first line of that output. `RestartSelf` starts the running program again with the same arguments. Results of the runners are exit codes: 0..255 for a normal exit, 128 plus the signal number for a program killed by a signal, and -1 when the command could not be run at all. DOS has no pipes, so `RunCapture` and `RunFirstLine` do not exist there; its shell runs go through the program named by the COMSPEC variable.

## 2. Interface declarations

```pascal
unit TvProc;

interface

function RunShell(const CmdLine: AnsiString; Pause: Boolean = False; const PauseText: AnsiString = 'Press Enter to return...'): LongInt;
function RunQuiet(const CmdLine: AnsiString): LongInt;
{ the following two exist on every target except DOS (GO32V2) }
function RunCapture(const Exe: AnsiString; const Args: array of AnsiString): AnsiString;
function RunFirstLine(const Exe: AnsiString; const Args: array of AnsiString): AnsiString;
procedure RestartSelf;
```

## 3. Behaviour

### 3.1 RunQuiet

Runs CmdLine as a command line of the system shell and waits for it to end. It writes nothing itself and does not suspend or resume the terminal; the child inherits the standard handles of the process. Returns the exit code of the command.

On Unix the command line is executed by the standard shell (as with the C `system` call: the shell is started with the command line as its single command string), so shell syntax (builtins, pipes, `$$`, `exit N`) works. The wait status is converted to the result: if the process could not be started or waited for (status -1) the result is -1; if the low seven bits of the status are not zero (the process was killed by a signal) the result is 128 plus those bits; otherwise it is the exit code (the next eight bits, 0..255). Examples: `exit 0` gives 0; `exit 7` gives 7; `exit 255` gives 255; `kill -9 $$` gives 137; a command that is not found by the shell gives 127.

Windows (separately marked, not required on Unix): the program named by the environment variable COMSPEC is run with the arguments `/c ` followed by CmdLine, the result is its exit code; any exception (cannot start) gives -1.

DOS (separately marked, not required on Unix): the DOS error indicator is cleared, COMSPEC is run through the DOS exec call with `/c ` plus CmdLine; if the DOS error indicator is non-zero afterwards the result is -1, otherwise the DOS exit code.

### 3.2 RunShell

Runs CmdLine in the foreground with the terminal returned to the system, in this order:

1. The terminal is given back: if the program has set the hook `OnSuspend` (a parameterless procedure variable of unit TvSys) it is called once; otherwise, on non-DOS targets, the terminal backend routine `UnixSuspend` of unit TvUnix is called. On DOS, with no hook, nothing is done.
2. An empty line is written to standard output, then a line consisting of the prompt marker followed by CmdLine: `$ ` followed by the command line on Unix, `> ` followed by it on Windows and DOS. The output buffer is flushed.
3. CmdLine is run with `RunQuiet`; its result is kept.
4. If Pause is True, and (on non-DOS targets) either the terminal backend reports itself active (`UnixActive` of TvUnix) or `OnSuspend` is assigned (on DOS: always when Pause is True), then an empty line and PauseText are written without a newline, the output is flushed and one line is read from standard input (it blocks until a newline or end of input). If the condition is false no pause happens.
5. The terminal is taken again: `OnResume` is called if assigned, otherwise on non-DOS targets `UnixResume` of TvUnix.

The result is the value of `RunQuiet`. Hook calls happen exactly once each per RunShell call, in all cases, including when the command fails; if the command cannot run the result is -1 and the terminal is still resumed. Default Pause is False; default PauseText is `Press Enter to return...`. Not safe to call concurrently (it uses the single terminal).

Example: with `OnSuspend` and `OnResume` set to counters, `RunShell('exit 3')` returns 3 and both counters are 1 afterwards.

### 3.3 RunCapture (not on DOS)

Starts the program Exe directly with the arguments in Args, each argument passed as a separate argument (no shell, no quoting, no splitting; arguments with spaces stay whole), and returns the complete output as one string. Standard output and standard error are joined into one stream, so their bytes appear in the order the program wrote them; nothing is trimmed or converted (newlines, a final newline and carriage returns are kept, binary bytes are kept). The function reads while the program runs, so a program that writes more than a pipe holds (any size, e.g. several hundred kilobytes) does not stall, and it reads until the end of the stream after the program has ended. The exit code of the program is not reported. If the program cannot be started (missing file, not executable) the result is the empty string; a program that runs and writes nothing also gives the empty string. An empty Args array is allowed. The standard input of the child is a pipe that the function never writes to and does not close before the child ends, so a program that waits for input will not finish; do not use it with such programs. The function itself does not do shell lookups; use an absolute path for Exe (searching of the PATH for a bare name is up to the process facility of the runtime and is not specified here).

Examples: `RunCapture('/bin/echo', ['hello','world'])` = `hello world` followed by a line feed. `RunCapture('/bin/sh', ['-c','echo out; echo err 1>&2'])` = `out`, line feed, `err`, line feed. `RunCapture('/no/such/program', [])` = ''.

### 3.4 RunFirstLine (not on DOS)

Calls `RunCapture` and cuts the result at the first line feed or carriage return character (whichever comes first), returning the part before it. If the output has no line break the whole output is returned; if it is empty or the program could not be run, the result is ''; if the output begins with a line break the result is ''. Examples: `RunFirstLine('/bin/sh', ['-c','echo one; echo two'])` = `one`; output `a`, CR, LF, `b` gives `a`.

### 3.5 RestartSelf

Starts the program again with the same arguments: the arguments are `ParamStr(0)` to `ParamStr(ParamCount)`.

Unix: the current process image is replaced (an exec of `ParamStr(0)` with those arguments and the current environment). On success the call never returns; no terminal cleanup is done by it, so the caller must restore the terminal and flush before calling. If the exec fails the procedure simply returns, with no error indication; the caller is expected to carry on or exit.

Other systems (separately marked, not required on Unix): a new process of `ParamStr(0)` is started with `ParamStr(1)..ParamStr(ParamCount)` and the procedure then returns after that process was run through the runtime's process-execution call; the intention is that the caller then exits. The runtime call used waits for the child to end (see section 5, point 1).

## 4. Dependencies and checks

Dependencies: unit TvSys (declarations used: the procedure variables `OnSuspend` and `OnResume`, parameterless procedures that the program may assign; a test assigns plain procedures to them); unit TvUnix (non-DOS targets; used: `UnixSuspend`, `UnixResume`, and `UnixActive`, a flag telling whether the terminal backend is active); runtime units SysUtils, Process (non-DOS), BaseUnix and Unix (Unix), Dos (DOS).

Checks a test program should make on Linux (no special privileges; `/bin/sh` and `/bin/echo` are used):

* `RunQuiet('exit 0')` = 0; `'exit 7'` = 7; `'exit 255'` = 255; `'kill -9 $$'` = 137; `'exit 1'` = 1.
* `RunQuiet` writes nothing to the terminal and does not call the hooks (set counters on OnSuspend/OnResume, run, check both still 0).
* `RunCapture('/bin/echo',['hello','world'])` = `hello world` + LF; with an argument that has spaces, `['a  b']` gives `a  b` + LF.
* Both streams: `RunCapture('/bin/sh',['-c','echo out; echo err 1>&2'])` = `out`+LF+`err`+LF.
* Missing program `RunCapture('/no/such/program',[])` = ''; a program with no output (`/bin/sh -c ':'`) gives ''.
* Large output: `/bin/sh -c 'head -c 300000 /dev/zero'` returns a string of length 300000 (no deadlock), and a program that writes 200000 bytes to stderr only also returns all bytes.
* The output is not trimmed: `printf 'a\n\n'` through `sh -c` returns `a`+LF+LF.
* `RunFirstLine('/bin/sh',['-c','echo one; echo two'])` = `one`; `printf 'a\r\nb'` gives `a`; no output gives ''; missing program gives ''; output starting with LF gives ''.
* `RunShell('exit 3')` with OnSuspend/OnResume counters set returns 3, and both counters equal 1; with hooks set and Pause = False no input is read. With Pause = True and a hook assigned, standard input fed with one line terminator, the call returns the exit code and consumes that line (optional, needs redirected stdin).
* The text printed by RunShell contains a line `$ ` + the command line (capture by running the test with its output redirected to a file, optional).
* `RestartSelf` is not testable without replacing the test process; a test may run a helper copy of the test program that calls it once under a guard variable in the environment and check that it ends with the second instance's output.

## 5. Notes on the old behaviour

1. The introductory comment of `RestartSelf` says that outside Unix it "starts a new one and goes on", but the call used there (the runtime's synchronous process execution) waits for the child to finish before returning, so the caller does not "go on" in parallel; whoever re-implements this should decide which of the two is wanted. The tests do not cover `RestartSelf`.
2. `RunCapture` gives the child a stdin pipe that is never closed, see 3.3.
