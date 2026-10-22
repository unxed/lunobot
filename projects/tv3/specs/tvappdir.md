# Unit TvAppDir

## 1. Purpose

TvAppDir answers where a program should keep the files of the user: its configuration, its data, its state (logs, crash reports) and its caches, following the convention of each system. It supports four conventions: XDG Base Directory (Linux, BSDs, other Unix), macOS, Windows, and DOS. The path computation is separated from the system the program runs on: `AppDirIn` takes the system and an environment lookup function as arguments, so the rules of every system can be tested on any system. `AppDirPath` is the same for the native system, `AppDir` and the four wrappers additionally create the directory. A directory is the empty string when it is not known (no HOME, no APPDATA). Paths returned never end with a separator (except a bare root).

## 2. Interface declarations

```pascal
unit TvAppDir;

interface

type
  TAppDirKind = (adConfig, adData, adState, adCache);
  TAppDirSystem = (adsXdg, adsMac, adsWindows, adsDos);
  { The value of an environment variable ('' when it is not set). }
  TAppDirEnv = function(const Name: AnsiString): AnsiString;

function NativeAppDirSystem: TAppDirSystem;
function AppDirGetEnv(const Name: AnsiString): AnsiString;
function AppDirProgramDir: AnsiString;

function AppDirIn(Kind: TAppDirKind; const App: AnsiString; Sys: TAppDirSystem; Env: TAppDirEnv;
  const ProgramDir: AnsiString; const DosVar: AnsiString = ''): AnsiString;
function AppDirPath(Kind: TAppDirKind; const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;
function AppDir(Kind: TAppDirKind; const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;

function ConfigDir(const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;
function DataDir(const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;
function StateDir(const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;
function CacheDir(const App: AnsiString; const DosVar: AnsiString = ''): AnsiString;

function MakeAppDir(const Dir: AnsiString): Boolean;
```

## 3. Behaviour

### 3.1 Types

`TAppDirKind` selects which of the four directories is wanted. `TAppDirSystem` selects the convention. `TAppDirEnv` is a plain function (not a method) that returns the value of the named environment variable, or '' when it is not set; an unset variable and one set to the empty string are indistinguishable and both count as not set.

### 3.2 NativeAppDirSystem

Returns the convention of the system the program was built for: `adsMac` on macOS (Darwin), `adsWindows` on Windows, `adsXdg` on any other Unix, and `adsDos` on everything else (DOS and similar). On Linux it is `adsXdg`.

### 3.3 AppDirGetEnv

The environment of the process: returns the value of the variable Name, or '' when not set. This is the Env function used for the native system.

### 3.4 AppDirProgramDir

The directory that holds the running program: take `ParamStr(0)`, make it a full path with the `PathExpand` of TvPath, take its directory part (`PathDir`), and remove the trailing separator (`PathDelSep`). Example: program `/usr/bin/prog` gives `/usr/bin`; `/prog` gives `/` (the root keeps its separator).

### 3.5 AppDirIn

Computes the directory, without touching the file system or the real environment. All lookups go through the given Env. The App name is appended as the last component by `PathJoin` (so an empty App yields the base directory itself; an App that is itself a rooted path would replace the base; callers should pass a plain name). The result is finally passed through `PathDelSep` with the Unix rules (XDG, macOS) or the DOS rules (Windows, DOS). Any variable value counts as "usable" only if it is an absolute path by the rules of the target (for XDG and macOS: begins with `/`; for Windows: has a drive letter and separator, or is a UNC path); an empty or relative value is treated as unset (ignored).

XDG (`adsXdg`, Unix rules). The base is the usable value of `XDG_CONFIG_HOME` (adConfig), `XDG_DATA_HOME` (adData), `XDG_STATE_HOME` (adState) or `XDG_CACHE_HOME` (adCache). When that is not usable, the base is built from the usable value of `HOME` with a fixed relative part: `.config` (config), `.local/share` (data), `.local/state` (state), `.cache` (cache). When neither the XDG variable nor HOME is usable the result is ''. The XDG variable works even without HOME. The result is base joined with App; a trailing separator on HOME or on the variable does not appear in the result.

macOS (`adsMac`, Unix rules). Only `HOME` is consulted (XDG variables are ignored); if it is not usable the result is ''. The directory is `HOME/Library/Application Support/App` for config, data and state, and `HOME/Library/Caches/App` for cache.

Windows (`adsWindows`, DOS rules; marked section, not required on Unix hosts but computed by this function on any host). For state and cache the base is the usable `LOCALAPPDATA`, falling back to the usable `APPDATA`; for config and data the base is the usable `APPDATA` only. If no base is usable the result is ''. The result is base joined with App using backslash.

DOS (`adsDos`, DOS rules; marked section). App and Kind are not used: all four kinds give the same directory. If DosVar is not empty, the value of the environment variable of that name (obtained through Env, not required to be absolute) is used; when DosVar is empty or the variable's value is empty the ProgramDir argument is used. The trailing separator is removed. If both are empty the result is ''.

Examples (App = `app`; environment given by the caller):

* XDG, HOME=`/home/u`, nothing else: config `/home/u/.config/app`, data `/home/u/.local/share/app`, state `/home/u/.local/state/app`, cache `/home/u/.cache/app`. With HOME=`/home/u/` the same results.
* XDG with XDG_CONFIG_HOME=`/c`, XDG_DATA_HOME=`/d/`, XDG_STATE_HOME=`/s`, XDG_CACHE_HOME=`/k`: `/c/app`, `/d/app`, `/s/app`, `/k/app`.
* XDG with XDG_CONFIG_HOME=`rel/c` and XDG_STATE_HOME=`./s`, HOME=`/home/u`: config `/home/u/.config/app`, state `/home/u/.local/state/app`.
* XDG with an empty environment: ''. Only XDG_CACHE_HOME=`/k`: cache `/k/app`. HOME=`home` (relative): config ''.
* macOS, HOME=`/Users/u` (XDG_CONFIG_HOME=`/c` present but ignored): config, data, state `/Users/u/Library/Application Support/app`; cache `/Users/u/Library/Caches/app`. Empty environment: ''.
* Windows, APPDATA=`C:\Users\u\AppData\Roaming`, LOCALAPPDATA=`C:\Users\u\AppData\Local\`: config and data `C:\Users\u\AppData\Roaming\app`; state and cache `C:\Users\u\AppData\Local\app`. LOCALAPPDATA empty: cache `C:\Users\u\AppData\Roaming\app`. LOCALAPPDATA=`Local` (relative): state falls back to Roaming. APPDATA=`\\srv\home\u`: config `\\srv\home\u\app`. Empty environment: ''.
* DOS, ProgramDir=`C:\PROG`, DosVar=`APPDIR`, variable unset: all four kinds `C:\PROG`. APPDIR=`D:\CFG\`: all kinds `D:\CFG`. DosVar='' and ProgramDir=`C:\PROG\`: `C:\PROG`.

Thread safety: pure apart from whatever the supplied Env does.

### 3.6 AppDirPath

`AppDirIn` for `NativeAppDirSystem` with Env = `AppDirGetEnv`. ProgramDir is `AppDirProgramDir` when the system is DOS and '' otherwise. DosVar is passed through. The directory is not created. For the native system on Linux the result equals `AppDirIn(Kind, App, adsXdg, @AppDirGetEnv, '')` with the real environment.

### 3.7 MakeAppDir

Creates the directory Dir and any missing directories above it. Returns False for an empty Dir. Returns True if Dir already exists as a directory (nothing is changed). Otherwise it determines the parent (Dir with trailing separators removed, then its directory part, again without trailing separator); if that parent is non-empty, differs from Dir, is not a root, and does not exist, the parent is created first by the same rule, and a failure there makes the result False. Then Dir itself is created. On Unix the directories this call creates (every missing level, not only the last) get permission mode 0700, i.e. readable and enterable by the owner only (the process umask can only remove more bits); existing directories are never changed. On other systems the plain create call is used (separately marked section). The result is True when the creation succeeded or the directory exists afterwards (so a concurrent creation by another process is tolerated); False when creation fails, e.g. a component is an existing regular file or the location is not writable. Note a relative single-component name (`x`) has no parent and is created in the current directory.

### 3.8 AppDir, ConfigDir, DataDir, StateDir, CacheDir

`AppDir` computes `AppDirPath` and, when that is non-empty, makes the directory with `MakeAppDir`; the result is '' when the directory is not known or cannot be made, otherwise the path (identical to what `AppDirPath` returns). `ConfigDir`, `DataDir`, `StateDir`, `CacheDir` are `AppDir` with the kinds `adConfig`, `adData`, `adState`, `adCache`. On DOS all four give the same directory.

## 4. Dependencies and checks

Dependencies: unit TvPath (declarations used: the type `TPathRules`, the constants `UnixPathRules` and `DosPathRules`, and the routines `PathIsAbsolute`, `PathJoin`, `PathDelSep`, `PathDir`, `PathExpand`, `PathIsRoot`, each in the form with and without rules as required); Free Pascal runtime units SysUtils (environment, `DirectoryExists`, `CreateDir`) and, on Unix, BaseUnix (`fpMkdir`).

Checks a test program should make (with a fake environment function backed by a name/value list, `App` = `app`, ProgramDir `C:\PROG`, DosVar `APPDIR`):

* All XDG, macOS, Windows and DOS examples of 3.5, including trailing-separator removal, relative values ignored, XDG without HOME, HOME relative, macOS ignoring XDG variables, Windows UNC base, empty environments giving ''.
* `AppDirPath(adConfig,'app')` equals `AppDirIn(adConfig,'app',NativeAppDirSystem,@AppDirGetEnv,AppDirProgramDir)`; on Linux `NativeAppDirSystem = adsXdg`.
* `AppDirProgramDir` is non-empty, absolute and has no trailing separator (unless it is the root).
* MakeAppDir with a fresh directory under the temporary directory, two levels deep (`tmp/a/b`): it does not exist before; the call returns True and the directory exists; a second call returns True; on Linux `stat` shows mode 0700 (permission bits equal 0700) for the last level; `MakeAppDir('')` is False; a path below a regular file returns False. Remove the test directories afterwards.
* AppDir/ConfigDir: with HOME and XDG variables of the process pointed to a temporary directory (set before the call), `ConfigDir('app')` returns the XDG path and the directory exists afterwards; with the XDG variable pointing below a regular file the result is ''.
