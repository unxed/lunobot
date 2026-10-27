# Unit TvPath

## 1. Purpose

TvPath is the single place that knows how a file path looks on a system: the separator, the root, drive prefixes, absolute versus relative paths, joining, splitting into directory, name and extension, normalising and expanding against a current directory. Every routine exists in two forms. One takes a rules record (`TPathRules`) and is a pure string function that does not look at the machine, so the behaviour of every system can be tested on any system. The other, without the rules argument, uses the rules of the system the program runs on (`NativePathRules`). Two rule sets are provided: Unix (`/` only, no drives, case-sensitive) and DOS/Windows (`\` written, `/` also read as a separator, `C:` drives and `\\server\share` roots, case-insensitive). All functions work on byte strings (`AnsiString`, `Char` is one byte); no function touches the file system except the ones that read the current directory (`PathExpand`, `PathExpandFrom`, `PathCurRoot`). The unit has no dependency on other units of the library; it uses only the Free Pascal runtime unit SysUtils (`GetCurrentDir`, `ExpandFileName` on drive systems, `SameText`, `AnsiCompareText`).

## 2. Interface declarations

```pascal
unit TvPath;

interface

type
  TPathRules = record
    Sep: Char;              { the separator that is written }
    AltSep: Char;           { a second character read as a separator (#0: none) }
    Drives: Boolean;        { "C:" drive prefixes and "\\server\share" roots }
    CaseSensitive: Boolean; { names that differ in case are different files }
    ListSep: Char;          { between the directories of a list such as PATH }
    AllFiles: string[3];    { the mask of every file }
  end;

const
  UnixPathRules: TPathRules = (Sep: '/'; AltSep: #0; Drives: False; CaseSensitive: True; ListSep: ':'; AllFiles: '*');
  DosPathRules: TPathRules = (Sep: '\'; AltSep: '/'; Drives: True; CaseSensitive: False; ListSep: ';'; AllFiles: '*.*');

{ Native constants; the first group when the target is DOS, Windows or OS/2 (drive systems),
  the second group on every other target. }
  PathSep = '\';
  PathHasDrives = True;
  PathAllFiles = '*.*';
{ -- or, on non-drive targets -- }
  PathSep = '/';
  PathHasDrives = False;
  PathAllFiles = '*';

function NativePathRules: TPathRules;

function IsPathSep(C: Char): Boolean; overload;
function IsPathSep(C: Char; const R: TPathRules): Boolean; overload;
function EndsWithSep(const S: AnsiString): Boolean; overload;
function EndsWithSep(const S: AnsiString; const R: TPathRules): Boolean; overload;

function PathDrive(const S: AnsiString): AnsiString; overload;
function PathDrive(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathRootLen(const S: AnsiString): Integer; overload;
function PathRootLen(const S: AnsiString; const R: TPathRules): Integer; overload;
function PathIsRooted(const S: AnsiString): Boolean; overload;
function PathIsRooted(const S: AnsiString; const R: TPathRules): Boolean; overload;
function PathIsAbsolute(const S: AnsiString): Boolean; overload;
function PathIsAbsolute(const S: AnsiString; const R: TPathRules): Boolean; overload;
function PathIsRoot(const S: AnsiString): Boolean; overload;
function PathIsRoot(const S: AnsiString; const R: TPathRules): Boolean; overload;

function PathAddSep(const S: AnsiString): AnsiString; overload;
function PathAddSep(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathDelSep(const S: AnsiString): AnsiString; overload;
function PathDelSep(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathJoin(const Dir, Name: AnsiString): AnsiString; overload;
function PathJoin(const Dir, Name: AnsiString; const R: TPathRules): AnsiString; overload;

procedure PathSplit(const S: AnsiString; out Dir, Name, Ext: AnsiString); overload;
procedure PathSplit(const S: AnsiString; out Dir, Name, Ext: AnsiString; const R: TPathRules); overload;
function PathDir(const S: AnsiString): AnsiString; overload;
function PathDir(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathName(const S: AnsiString): AnsiString; overload;
function PathName(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathExt(const S: AnsiString): AnsiString; overload;
function PathExt(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathChangeExt(const S, Ext: AnsiString): AnsiString; overload;
function PathChangeExt(const S, Ext: AnsiString; const R: TPathRules): AnsiString; overload;

function PathNative(const S: AnsiString): AnsiString; overload;
function PathNative(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathNormalize(const S: AnsiString): AnsiString; overload;
function PathNormalize(const S: AnsiString; const R: TPathRules): AnsiString; overload;
function PathExpand(const S: AnsiString): AnsiString;
function PathExpandFrom(const S, Base: AnsiString): AnsiString;
function PathExpandIn(const S, Cur: AnsiString; const R: TPathRules): AnsiString;

function PathSameName(const A, B: AnsiString): Boolean; overload;
function PathSameName(const A, B: AnsiString; const R: TPathRules): Boolean; overload;

function PathCurRoot: AnsiString;
```

(The constants `PathSep`, `PathHasDrives`, `PathAllFiles` are declared in the same constant section as the two rule records; exactly one of the two alternatives exists in a build.)

## 3. Behaviour

### 3.1 Terms used below

For a string S and rules R, the drive part ("drive") is determined first and everything else is defined in terms of it. A separator is the character `R.Sep` or, when `R.AltSep` is not #0, `R.AltSep`.

* Drive part, when `R.Drives` is True: if S has at least two characters, the first is an ASCII letter and the second is `:`, the drive is those two characters. Otherwise, if S has at least three characters, begins with two separators and the third character is not a separator, the drive is the UNC prefix: starting at position 3, scan forward; the drive ends just before the second separator met in that scan, or at the end of S if fewer than two separators follow. So `\\srv\share\x` has drive `\\srv\share`, `\\srv\sh` has drive `\\srv\sh`, `\\srv` has drive `\\srv`, and `\\\x` has no drive. When `R.Drives` is False the drive is always empty. A drive of length 2 is a letter drive; a drive of length greater than 2 is a UNC drive (a UNC drive can never have length 2).
* Root length: the drive length, plus one if the character right after the drive is a separator. For a path without a root directory the root length equals the drive length.
* Rooted: the path does not depend on the current directory of a drive, i.e. either a separator follows the drive part (`/x`, `\x`, `C:\x`, `\\srv\sh\x`), or the whole path is a UNC drive (`\\srv`, `\\srv\sh`). `C:`, `C:x` and relative names are not rooted. With Unix rules only a leading `/` makes a path rooted.
* Absolute: rooted, and, when the rules have drives, with a non-empty drive. So under DOS rules `\a` is rooted but not absolute, `C:\a` and `\\srv\sh\a` are absolute; under Unix rules absolute equals rooted.

### 3.2 Constants and NativePathRules

`UnixPathRules` and `DosPathRules` are the two typed constants shown above. `NativePathRules` returns a copy of `DosPathRules` on drive systems (DOS, Windows, OS/2) and of `UnixPathRules` on every other system. `PathSep`, `PathHasDrives`, `PathAllFiles` are the compile-time forms of the `Sep`, `Drives` and `AllFiles` fields of the native rules (`PathSep = NativePathRules.Sep`, `PathAllFiles = NativePathRules.AllFiles`). On Unix: `/`, False, `*`. Drive systems only: `\`, True, `*.*`.

### 3.3 IsPathSep, EndsWithSep

`IsPathSep(C, R)` is True when C equals `R.Sep` or equals the non-#0 `R.AltSep`. The one-argument form uses the native rules (on Unix only `/`; on drive systems both `\` and `/`). `EndsWithSep(S, R)` is True when S is non-empty and its last character is a separator. Examples: Unix: `IsPathSep('\')` False, `EndsWithSep('a/')` True, `EndsWithSep('a\')` False; DOS: `EndsWithSep('a\')` True.

### 3.4 PathDrive, PathRootLen

`PathDrive` returns the drive part defined in 3.1 (copied from S with its original case), or '' if none or if the rules have no drives. `PathRootLen` returns the root length of 3.1.
Examples: Unix `PathDrive('C:\x')` = ''; DOS `PathDrive('c:\x')` = `c:`; DOS `PathDrive('\\srv\share\x')` = `\\srv\share`; DOS `PathDrive('\\srv')` = `\\srv`. Root length: Unix `/a` 1, Unix `a` 0, Unix `''` 0; DOS `C:\a` 3, DOS `C:a` 2, DOS `\\srv\sh\a` 9, DOS `\\srv\sh` 7, DOS `\a` 1.

### 3.5 PathIsRooted, PathIsAbsolute, PathIsRoot

`PathIsRooted` and `PathIsAbsolute` are defined in 3.1. `PathIsRoot(S)` is True when S is non-empty, rooted, and its root length equals its length (the path is a root and nothing more). Examples: Unix: `PathIsRooted('/a')` True, `PathIsRooted('a/b')` False, `PathIsRooted('C:\a')` False, `PathIsAbsolute('\a')` False, `PathIsRoot('/')` True, `PathIsRoot('/a')` False, `PathIsRoot('')` False, `PathIsRoot('C:\')` False, `PathIsRoot('//')` False (the root length is 1). DOS: `PathIsRooted('\a')`, `('/a')`, `('C:\a')` True and `('C:a')` False; `PathIsAbsolute('C:\a')`, `('\\srv\sh\a')`, `('\\srv\sh')` True; `PathIsAbsolute('\a')`, `('C:a')`, `('a')` False; `PathIsRoot('C:\')`, `('\')`, `('\\srv\sh\')` True, `PathIsRoot('C:')` False.

### 3.6 PathAddSep, PathDelSep

`PathAddSep(S)` returns S with one `R.Sep` appended unless S is empty, already ends with a separator (either kind), or is exactly a bare letter drive (two characters, `X:`). Nothing else is altered, no separator is doubled. Under Unix rules a backslash is an ordinary character, so `PathAddSep('a\')` = `a\/`. A UNC drive without a trailing separator does get one: DOS `PathAddSep('\\srv')` = `\\srv\`.
`PathDelSep(S)` removes trailing separators (any number, either kind) but never cuts into the root: characters within the root length are kept. Results: Unix `/a/` becomes `/a`; `/` stays `/`; `a//` becomes `a`; `''` stays `''`. DOS: `C:\` stays `C:\`, `C:\a\` becomes `C:\a`, `\` stays `\`.

### 3.7 PathJoin

`PathJoin(Dir, Name)` yields Name alone when Dir is empty, or Name is rooted, or Name has a non-empty drive. Otherwise, when Name is empty it yields Dir unchanged (no separator added); otherwise it yields `PathAddSep(Dir)` followed by Name. Examples: Unix `('/a','b')` = `/a/b`; `('/a/','b')` = `/a/b`; `('/a','/b')` = `/b`; `('','b')` = `b`; `('/a','')` = `/a`; `('/a','C:x')` = `/a/C:x` (no drives on Unix). DOS: `('C:\a','b')` = `C:\a\b`; `('C:','b')` = `C:b` (a bare drive gets no separator); `('C:\a','D:x')` = `D:x`.

### 3.8 PathSplit, PathDir, PathName, PathExt, PathChangeExt

`PathSplit` cuts S into three parts such that their concatenation Dir + Name + Ext equals S exactly. The directory part Dir ends at the last separator that lies after the drive part; it includes the drive and that last separator. If no separator follows the drive, Dir is just the drive (or '' if none). The remainder is the file part. In the file part, Ext starts at the last dot that is not the first character of the file part; Name is what precedes it. If the file part is `.` or `..`, or has no such dot (including the case of a single leading dot such as `.profile`), Ext is '' and Name is the whole file part. A trailing dot gives Ext = `.` (e.g. `a.` splits into `a` and `.`). `PathDir` returns the Dir part, `PathName` returns Name + Ext (the whole file part), `PathExt` returns Ext. `PathChangeExt(S, Ext)` returns Dir + Name + Ext, where the given Ext replaces the old one (give it with its dot, or '' to remove it; nothing is added automatically).
Examples (Dir|Name|Ext): Unix `/a/b/file.name.ext` is `/a/b/|file.name|.ext`; `file` is `|file|`; `/a/b/` is `/a/b/||`; `/a/.profile` is `/a/|.profile|`; `/a/.x.conf` is `/a/|.x|.conf`; `..` is `|..|`; `a\b.txt` is `|a\b|.txt` (backslash not a separator on Unix); `C:\a\b.txt` is `|C:\a\b|.txt`. DOS: `c:\dir\sub\file.name.ext` is `c:\dir\sub\|file.name|.ext`; `c:file.txt` is `c:|file|.txt`; `c:/a/b.txt` is `c:/a/|b|.txt` (original separator kept). `PathDir('/a/b')` (Unix) = `/a/`; `PathName('/a/b.c')` = `b.c`; `PathExt('/a.d/b')` = ''; DOS `PathExt('C:\a.d\b.PAS')` = `.PAS` (case kept). `PathChangeExt('/a.d/b.txt','.bak')` = `/a.d/b.bak`; `('/a.d/b','.bak')` = `/a.d/b.bak`; `('/a/.profile','.bak')` = `/a/.profile.bak`; Unix `('a.b\c','.x')` = `a.x`; DOS `('a.b\c','.x')` = `a.b\c.x`; DOS `('C:\a\b.txt','')` = `C:\a\b`.

### 3.9 PathNative

Replaces every occurrence of `R.AltSep` by `R.Sep` and changes nothing else; with a rules record that has no alternative separator (Unix) the string is returned unchanged. DOS `a/b\c` becomes `a\b\c`; Unix `a/b\c` stays.

### 3.10 PathNormalize

Result of PathNative(S) then simplified as follows. An empty string gives an empty string. The root (3.1 root length, after native conversion) is kept verbatim as the start of the result; the remainder is cut into parts at `R.Sep`. Empty parts (repeated separators) and parts `.` are dropped. A part `..` removes the preceding kept part, unless there is none or the preceding kept part is itself `..`; in that case, if the path is rooted the `..` is dropped (above a root is the root, for a UNC drive the share is the limit), and if the path is not rooted the `..` is kept. The result is the root followed by the kept parts joined by `R.Sep`. If the root is empty and no parts remain, the result is `.`. If the original (after native conversion) was longer than its root and ended with a separator, and at least one part remains, a separator is appended. (When nothing remains, no separator is added: `a/../` gives `.`.) Bare drive roots such as `C:` that are not rooted follow the non-rooted rules, so `C:..\x` keeps its `..`.
Examples: Unix `/a//b/./c/../d/` gives `/a/b/d/`; `/../a` gives `/a`; `../a/..` gives `..`; `a/..` gives `.`; `/a\b/../c` gives `/c` (`a\b` is one name); DOS `C:/a/../b` gives `C:\b`; DOS `\\srv\sh\a\..\..\b` gives `\\srv\sh\b`; DOS `C:\` stays `C:\`.

### 3.11 PathExpandIn

Pure function: the complete path of S when the current directory is Cur (Cur is expected to be absolute). If S is absolute under R, the result is `PathNormalize(S)`. Otherwise let D be the drive of S and CurD the drive of Cur. If D is non-empty and differs from CurD when compared ignoring case, the result is the normalised form of D, a separator and the rest of S after D (so `D:b` becomes `D:\b`, the root of that other drive; this is the only treatment of foreign-drive relative paths). If S is rooted (but has no foreign drive and is not absolute, e.g. `\b`), the result is CurD followed by the rest of S, normalised. Otherwise (relative, including a path with the same drive as Cur) the result is the rest of S (after the drive) joined to Cur by PathJoin, normalised. The case of the drive in the result comes from Cur. A trailing separator in S is kept (through PathNormalize). Under Unix rules, drives do not exist, so `C:\x` is an ordinary relative name.
Examples: Unix with Cur `/home/u`: `b` gives `/home/u/b`; `../b/` gives `/home/b/`; `/x` gives `/x`; `C:\x` gives `/home/u/C:\x`. Cur `/` and S `b` gives `/b`. DOS with Cur `C:\a`: `b` gives `C:\a\b`; `\b` gives `C:\b`; `c:b` gives `C:\a\b`; `D:b` gives `D:\b`. DOS with Cur `\\srv\sh\a`: `d/e` gives `\\srv\sh\a\d\e`.

### 3.12 PathExpand, PathExpandFrom

`PathExpand(S)` returns the full path of S relative to the process current directory. An empty S gives the current directory with a separator appended (`/home/u/`; for the root `/`). On Unix otherwise it is `PathExpandIn(S, current directory, UnixPathRules)`. Drive-system targets (separately marked, not required on Unix): the result is the runtime library's `ExpandFileName` (which knows the per-drive current directories) passed through PathNormalize, with a separator appended if S itself ended with a separator. The current directory is a process-wide value; the function is therefore not safe against a concurrent change of directory.
`PathExpandFrom(S, Base)` is `PathExpand(S)` when Base is empty or S is rooted or S has a drive (native rules); otherwise it is `PathExpand(PathJoin(Base, S))`. Base may itself be relative.
Examples on Unix with current directory `/home/u`: `PathExpand('x')` = `/home/u/x`; `PathExpand('a/../x')` = `/home/u/x`; `PathExpand('a\b')` = `/home/u/a\b`; `PathExpand('')` = `/home/u/`; `PathExpandFrom('x','sub')` = `/home/u/sub/x`; `PathExpandFrom('/x','sub')` = `/x`.

### 3.13 PathSameName

With case-sensitive rules the result is plain string equality; otherwise strings are equal when `AnsiCompareText` says so (equality ignoring case). Unix `A.txt` vs `a.txt` is False; DOS rules True. It compares whole strings; it does not normalise them.

### 3.14 PathCurRoot

The root of the current directory: the current directory cut at its native root length; if that piece is not rooted (a bare drive `C:`), a separator is appended. Unix: always `/`. Drive systems: `C:\` (or the UNC root). If the current directory cannot be determined (empty string) the result is empty.

### 3.15 Thread safety

All functions that take only strings and rules are pure and safe from any thread. `PathExpand`, `PathExpandFrom` and `PathCurRoot` read the process-wide current directory.

## 4. Dependencies and checks

Dependencies: only the Free Pascal run-time library (SysUtils). No other unit of the library.

Checks a test program should make (all run on Linux; Unix and DOS rules are given explicitly, so the DOS rows are valid on any system):

* IsPathSep: `/` is a separator under Unix, `\` is not; both are under DOS. EndsWithSep for `a/` (Unix), `a\` (Unix False, DOS True).
* PathDrive: `C:\x` Unix ''; `c:\x` DOS `c:`; `\\srv\share\x` DOS `\\srv\share`; `\\srv` DOS `\\srv`.
* PathRootLen: the values in 3.4 (`/a` 1, `a` 0, `C:\a` 3, `C:a` 2, `\\srv\sh\a` 9).
* PathIsRooted, PathIsAbsolute, PathIsRoot: every example in 3.5.
* PathAddSep / PathDelSep: `a` to `a/` (Unix) and `a\` (DOS); `/` and `''` unchanged by add; `C:` unchanged by add (DOS); `a\` to `a\/` (Unix); delete cases of 3.6.
* PathJoin: all examples in 3.7.
* PathSplit, PathDir, PathName, PathExt, PathChangeExt: all examples in 3.8, checking that Dir+Name+Ext equals the input.
* PathNative: `a/b\c` unchanged under Unix, `a\b\c` under DOS.
* PathNormalize: all examples in 3.10, plus idempotence (normalising a normalised path changes nothing) and `''` gives `''`.
* PathExpandIn: all examples in 3.11.
* PathSameName: case-sensitivity difference between the two rule sets.
* Native forms on Linux: `PathSep = '/'`, `PathHasDrives = False`, `PathAllFiles = '*'`, and `PathSep = NativePathRules.Sep`, `PathAllFiles = NativePathRules.AllFiles`.
* Current directory: `PathIsAbsolute(GetCurrentDir)`; `PathExpand('x')` equals `PathJoin(cwd,'x')`; `PathExpand('a/../x')` the same; `PathExpandFrom('x','sub')` equals `PathJoin(PathJoin(cwd,'sub'),'x')`; `PathIsRoot(PathCurRoot)` and the current directory begins with it; `PathExpand(PathCurRoot)` equals `PathCurRoot`; `PathExpand('a\b')` equals cwd + `/a\b`; PathCurRoot contains no colon.
