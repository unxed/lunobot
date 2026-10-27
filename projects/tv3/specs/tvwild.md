# Unit TvWild

## 1. Purpose

TvWild is the single file-mask matcher of the library. It decides whether a file name matches a mask containing wild cards (`*`, `?`, `[set]`) and whether a name matches a list of masks with optional exclusions (`*.pas;*.inc|test*`). Matching is case-insensitive by default, works on characters (UTF-8 sequences) when UTF-8 mode is on and on bytes otherwise, and treats the DOS mask `*.*` as "every name". All routines are pure functions of their arguments (plus the global UTF-8 mode flag), keep no state and are thread-safe as long as the flag is not changed concurrently.

## 2. Interface

```pascal
unit TvWild;

interface

function WildMatch(const Name, Mask: AnsiString; CaseSensitive: Boolean = False): Boolean;
function WildMatchList(const Name, List: AnsiString; CaseSensitive: Boolean = False): Boolean;
{ True when the text has a wild card of a mask ('*', '?', '['). }
function HasWild(const S: AnsiString): Boolean;
```

No other public identifiers.

## 3. Behaviour

### 3.1 Mask syntax (used by WildMatch and, per item, by WildMatchList)

* `*` matches any sequence of characters, including the empty one and including dots and path separators (no character is special for it).
* `?` matches exactly one character. A "character" is one whole UTF-8 sequence while the library's UTF-8 mode (`Utf8Enabled` of TvUtf8) is on, otherwise one byte. In UTF-8 mode a Cyrillic letter (2 bytes) is matched by one `?`.
* `[...]` is a set that matches exactly one character of the name.
  * If the first character after `[` is `!` or `^`, the set is negated: it matches one character that is not in the set.
  * The members are single characters or ranges `lo-hi` (inclusive, compared by Unicode code point; in non-UTF-8 mode, by byte value). A range with lo > hi matches nothing.
  * A `-` is a range operator only when it follows a member and is followed by something other than `]`. Thus `[a-]` is the set {a, -}.
  * The first member position (right after `[` or after the negation sign) is always a member, even when it is `]`: `[]a]` is the set {], a}; `[!]a]` is its complement.
  * Members are read as characters in the same sense as above (a multi-byte member is one member).
* A `[` that has no closing `]` anywhere after it in the mask is not a set: it is an ordinary `[` that matches only a `[` in the name. (Example: mask `[x` matches name `[x` and nothing else.) A well-formed set that does not match the current character is a mismatch; it does not fall back to a literal `[`.
* There is no escape character. Every other character matches itself exactly.
* The whole name must be matched (anchored at both ends). Mask matching with several `*` is by backtracking semantics: the result is true iff there exists an assignment of the stars that makes the whole name match.
* An empty mask matches only the empty name. An empty name matches a mask made only of `*` (or an empty mask).

### 3.2 WildMatch(Name, Mask, CaseSensitive)

If `Mask` is exactly the three characters `*.*`, the result is True for every name (including names without a dot and the empty name), whatever `CaseSensitive` is. This special case applies only to the exact text `*.*`; a mask such as `a*.*` is an ordinary mask and requires a dot in the name.

Otherwise, with `CaseSensitive = True` the name and mask are compared as they are. With `CaseSensitive = False` (default) both name and mask are first converted to lower case by the library's UTF-8-aware lower-casing (TvUStr `U8Lower`), then matched; so the case-folding also applies to set members and range ends (`[A-C]` matches `b` and `B`) and to non-ASCII letters (Cyrillic `П` equals `п`). The mask is not trimmed.

Examples:
* `WildMatch('readme.txt','*.txt')` = True; `('readme.txt','*.pas')` = False.
* `('README.TXT','*.txt')` = True; with CaseSensitive=True = False.
* `('a.b.c','*.c')` = True (star takes dots). `('abc','a?c')` = True; `('ac','a?c')` = False.
* `('noext','*.*')` = True. `('','*')` = True.
* `('abc','a*b*c')` = True; `('aXbXc','a*b*c')` = True; `('abcd','a*b*c')` = False; `('aaa','a*a')` = True.
* `('b.pas','[a-c].pas')` = True; `('d.pas','[a-c].pas')` = False; `('d.pas','[!a-c].pas')` = True.
* `('[x','[x')` = True; `('x','[x')` = False.
* UTF-8 mode on: `('Привет.txt','п*.TXT')` = True; `('Привет','??????')` = True (6 characters); `('Привет','?????????????')` = False.

### 3.3 WildMatchList(Name, List, CaseSensitive)

`List` consists of an include part and an optional exclude part separated by the first `|` in the text. Any further `|` characters belong to the exclude part and are ordinary mask characters.

* Each part is a sequence of masks separated by `;` or `,`. Every mask is trimmed of leading/trailing white space (spaces) before use; empty items (after trimming) are ignored. So `*.pas, *.inc` has two masks.
* A part "matches" a name when at least one of its masks matches it by WildMatch with the same `CaseSensitive` (including the `*.*` rule).
* Result: if the include part has at least one non-blank character, the name must match the include part; otherwise (include part blank or absent) the result starts as True exactly when the exclude part text is non-empty (not trimmed), and False when there is no exclude text, so an empty list matches nothing and a list `|test*` matches everything not excluded. Then, if the exclude text is non-empty and the name matches the exclude part, the result becomes False.
* Consequences: `''` matches nothing; `'|'` matches nothing; a list whose exclude text consists only of blanks and has a blank include part (`'|  '`) matches every name (nothing can be excluded).

Examples: `('a.pas','*.pas;*.inc')` True; `('a.inc','*.pas, *.inc')` True; `('a.txt','*.pas;*.inc')` False; `('test.pas','*.pas|test*')` False; `('main.pas','*.pas|test*')` True; `('main.pas','|test*')` True; `('test1','|test*')` False; `('a','')` False.

### 3.4 HasWild(S)

True iff `S` contains at least one of the characters `*`, `?`, `[`. A lone `]` or `-` does not count. No check is made that a `[` forms a valid set. `HasWild('')` = False.

## 4. Dependencies

* Library units: TvUStr (implementation only). The implementation needs from it: the code point of the UTF-8 character at a position of a string, the byte length of the character at a position (1 when UTF-8 mode is off or the byte is invalid), and a UTF-8-aware lower-casing function (`U8CodePoint`, `U8CharBytes`, `U8Lower`). The UTF-8 mode flag `Utf8Enabled` lives in TvUtf8 (tests set it; the interface does not mention it).
* Standard units: SysUtils (trimming).

## 5. Checks for a test program

(UTF-8 mode set on at the start.) All examples of 3.2, 3.3 and 3.4, plus:
1. `*` against the empty name; `''` against mask `''` is True, `'a'` against `''` is False; `''` against `?` is False.
2. `[]a]` matches `]` and `a`; `[!]a]` does not match `]`; `[a-]` matches `-`; `[z-a]` matches nothing; `[^a]` equals `[!a]`.
3. A set at the end of a mask with the name exhausted (`ab` vs `a[b]` True, `a` vs `a[b]` False); a mask ending with `[` alone matches a name ending with `[`.
4. `*.*` exact rule: `WildMatch('x','*.*',True)` True; `WildMatch('x','a*.*')` False.
5. Case folding in sets: `WildMatch('B','[a-c]')` True, `WildMatch('B','[a-c]',True)` False.
6. Mask with several stars needing backtracking: `('aXbXbXc','*b*c')`, `('mississippi','*iss*ppi')`.
7. With UTF-8 mode off: a Cyrillic name of 12 bytes needs 12 `?`, and `??????` fails.
8. List: separators `;` and `,`, white space around items, empty items (`;;*.pas;`), second `|` inside the exclude part, `'|  '` quirk, CaseSensitive passed on to both parts.
