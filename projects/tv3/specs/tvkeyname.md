# Unit TvKeyName

## 1. Purpose

TvKeyName converts between a key value (`TKey` of TvKeys: a key code plus a modifier mask) and its textual name such as `Ctrl+Shift+F5`, `Alt+Enter`, `Num+`, `Ctrl+A`. It is the single place for key names used in user-visible hot-key text, key bindings and event logs. Writing produces one canonical text per key; reading is tolerant (case-insensitive, several aliases, `-` instead of `+`). Because the unit works on `TKey` values, the several historical code spellings of one key (for example a combined "Ctrl+F5" code and F5 with the Ctrl modifier) are the same key and have the same name. The routines are pure and thread-safe.

## 2. Interface

```pascal
unit TvKeyName;

interface

uses
  TvKeys;

{ The name of a key. A key without a name comes as "Key $XXXX"; kbNoKey as an empty text. }
function KeyToStr(const K: TKey): AnsiString;
function KeyCodeToStr(KeyCode: Word): AnsiString;
{ False when the text is no key; K is nothing then. }
function StrToKey(const S: AnsiString; out K: TKey): Boolean;
```

## 3. Reliance on TvKeys (not reproduced here)

The unit relies on the following from TvKeys, which the new repository already has:

* `TKey`: a record with fields `Code: Word` and `Mods: Word`; a constructor-like `TKey.Create(Code)` and `TKey.Create(Code, Mods)` that **normalises** the pair to a canonical form, so that every equivalent spelling of a key yields the same record; and an equality operator `=` on two TKey. The canonical form that the names rely on: function and navigation keys carry their classic code `(scan << 8) | ascii` (table below) with the modifiers in `Mods`; letters and digits and printable characters carry the plain ASCII code (letters in upper case) in the low byte, high byte 0, with modifiers in `Mods`. For example `TKey.Create(kbCtrlF5)` = F5 + Ctrl, `kbCtrlA` = `A` + Ctrl, `kbAltQ` = `Q` + Alt, `kbAlt5` = `5` + Alt, `kbShiftTab` = Tab + Shift, `kbAltEnter` = Enter + Alt, `kbCtrlPgUp` = PageUp + Ctrl.
* Modifier masks: `kbCtrlShift` (any Ctrl), `kbAltShift` (any Alt), `kbShift` (any Shift); the name test is "Mods and mask <> 0".
* Code constants: `kbNoKey` (the code of "no key"), `kbEsc`, `kbEnter`, `kbBack`, `kbIns`, `kbDel`, `kbPgUp`, `kbPgDn`, `kbGrayPlus`, `kbGrayMinus`, `kbCtrlPrtSc`.

## 4. Behaviour

### 4.1 Name table (code to name)

Canonical codes (hex) and their names; this is both the writing table and the first reading table:

| Name | Code | Name | Code | Name | Code |
|---|---|---|---|---|---|
| Esc | 011B | F1 | 3B00 | Left | 4B00 |
| Backspace | 0E08 | F2 | 3C00 | Right | 4D00 |
| Tab | 0F09 | F3 | 3D00 | Num+ | 4E2B |
| Enter | 1C0D | F4 | 3E00 | End | 4F00 |
| Space | 0020 | F5 | 3F00 | Down | 5000 |
| Home | 4700 | F6 | 4000 | PageDown | 5100 |
| Up | 4800 | F7 | 4100 | Insert | 5200 |
| PageUp | 4900 | F8 | 4200 | Delete | 5300 |
| Num- | 4A2D | F9 | 4300 | F11 | 8500 |
| | | F10 | 4400 | F12 | 8600 |

(29 rows.) `Num+` and `Num-` are the keypad plus and minus (`kbGrayPlus` = 4E2B, `kbGrayMinus` = 4A2D); they are different keys from the printable `+` (2B) and `-` (2D).

Read-only aliases (compared case-insensitively, after the table): `Escape` = kbEsc, `Return` = kbEnter, `BkSp` = kbBack, `Ins` = kbIns, `Del` = kbDel, `PgUp` = kbPgUp, `PgDn` = kbPgDn, `Plus` = kbGrayPlus, `Minus` = kbGrayMinus, `Spacebar` = 0020, `PrtSc` = kbCtrlPrtSc. Aliases are never produced when writing.

### 4.2 KeyToStr(K)

* If `K.Code = kbNoKey` the result is the empty string (whatever the modifiers).
* Otherwise the result is the modifier prefix followed by the key text. The prefix is, in this fixed order, `Ctrl+` if `K.Mods` has any bit of kbCtrlShift, then `Alt+` if any bit of kbAltShift, then `Shift+` if any bit of kbShift (each at most once, none if there are none).
* Key text: the table name if `K.Code` is a table code (so code 0020 is `Space`, not a blank); else, if the high byte of the code is 0 and the low byte is a printable ASCII character other than space (21..7E), that character in upper case (`a` and `A` both come as `A`); else the text `Key $` followed by the code as upper-case hexadecimal with at least 4 digits (always 4 for a Word).

Examples: F5 -> `F5`; kbCtrlF5 -> `Ctrl+F5`; (F5, Ctrl+Shift mods) -> `Ctrl+Shift+F5`; kbAltEnter -> `Alt+Enter`; kbCtrlA -> `Ctrl+A`; kbAltQ -> `Alt+Q`; kbShiftTab -> `Shift+Tab`; kbEsc -> `Esc`; kbAlt5 -> `Alt+5`; kbCtrlPgUp -> `Ctrl+PageUp`; code 002B (`+`) -> `+`; kbGrayPlus -> `Num+`; kbNoKey -> `` ; code FE00 -> `Key $FE00`; (FE00, Ctrl) -> `Ctrl+Key $FE00`.

### 4.3 KeyCodeToStr(KeyCode)

Exactly `KeyToStr(TKey.Create(KeyCode))`: the code is normalised first, so `KeyCodeToStr(kbAltF3)` = `Alt+F3`.

### 4.4 StrToKey(S, K)

Returns True and sets `K` to `TKey.Create(Code, Mods)` when the text is a key; otherwise returns False and sets `K` to `Code = kbNoKey, Mods = 0`.

Parsing, in order:
1. The text is trimmed; an empty result is not a key.
2. Modifier prefixes are peeled off repeatedly. The next prefix is the text from the start up to the first `+` or `-` found at a position after the first character, provided that separator is followed by at least one more character (so a separator that is the last character never splits). The prefix is trimmed and compared case-insensitively: `ctrl` or `control` adds the Ctrl mask, `alt` the Alt mask, `shift` the Shift mask; modifiers may come in any order and may repeat; spaces around them are allowed (`Ctrl + F5`). When the prefix is not a modifier name, or there is no splitting separator, peeling stops and the rest (trimmed) is the key text. The modifier flags of the mask are `kbCtrlShift`, `kbAltShift`, `kbShift` respectively.
3. The key text is looked up case-insensitively in the table, then in the aliases; a hit gives the code.
4. Otherwise a one-character key text that is a printable ASCII character above space (21..7E) gives that character's code, letters in upper case (`a` -> 0041); any other single character is not a key.
5. Otherwise a key text longer than 5 characters whose first five characters are `Key $` (case-insensitive) gives the code from the rest read as hexadecimal; if it does not parse or is 0, it is not a key.
6. Anything else (unknown names, unknown modifier such as `Hyper+X`, a modifier alone such as `Ctrl+`) is not a key.

Because of rule 2, `Ctrl++` is `+` with Ctrl, `Ctrl--` is `-` with Ctrl, `Num-` and `Num+` are the keypad keys (the trailing sign is not a separator), a lone `+` or `-` is the printable key, and `Ctrl-S` equals `Ctrl+S`.

Examples: `F5` -> F5; `ctrl+f5` -> same key as kbCtrlF5; `Ctrl-S` -> kbCtrlS; `Alt+Shift+F10` -> F10 with Alt+Shift; `Ctrl++` -> (002B, Ctrl); `Ctrl--` -> (002D, Ctrl); `Num-` -> kbGrayMinus; `Del` -> kbDel; `PgDn` -> kbPgDn; `Return` -> kbEnter; `Alt+a` -> kbAltA; `Space` -> 0020; `Key $FE00` -> (FE00); `Hyper+X`, `` and `Ctrl+` -> False.

Round trip: for any key whose writing is a table name or a printable upper-case character or `Key $XXXX`, `StrToKey(KeyToStr(K))` yields K (checked for Ctrl+Home and Shift+Insert). The lower-case letter `a` (code 0061) writes as `A` and reads back as 0041, so that case is not a round trip. Codes above FFFF in `Key $` text are outside the tested domain.

## 5. Dependencies

* Library: TvKeys (TKey and the constants of section 3).
* Standard: SysUtils (case conversion, trimming, hexadecimal conversion).

## 6. Checks for a test program

1. Every example of 4.2, 4.3 and 4.4.
2. Every table row: `KeyCodeToStr(code)` = name, `StrToKey(name)` = key of that code; every alias reads as given in 4.1; each name also reads in upper and lower case.
3. Modifier order: all 8 combinations of Ctrl/Alt/Shift on F5 write in the order Ctrl, Alt, Shift; reading `Shift+Alt+Ctrl+F5` gives the same key as `Ctrl+Alt+Shift+F5`; spaces around `+`; `control+x` accepted.
4. Printable characters: each of 21..7E written and read (letters upper-cased, `a` reads as `A`); `+`, `-` alone; `Alt+-`.
5. Failures: `Hyper+X`, `` (empty), blanks only, `Ctrl+`, `Ctrl+Alt`, `Key $`, `Key $0000`, `Key $ZZ`, a single non-ASCII or control character; on failure `K.Code = kbNoKey`.
6. `PrintScreen` is not required to be recognised (see note: it is mentioned in the unit's description but absent from the table); `PrtSc` reads as kbCtrlPrtSc.
7. Round trip for every table row with every modifier combination.
