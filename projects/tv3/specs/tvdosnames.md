# Unit TvDosNames

## 1. Purpose

TvDosNames converts file names at the border between a program and a DOS that offers a UTF-8 file-name API (an optional provider; when it is switched on the DOS takes and returns names in UTF-8). Programs of two kinds exist: those with UTF-8 strings inside (library UTF-8 mode on) and those whose strings are bytes of the current code page (UTF-8 mode off). The unit translates names to the form the DOS expects and back. A character that the current code page cannot represent travels inside a code-page program, or to/from a code-page DOS, as the text `{U+XXXX}` (a brace, `U+`, 4 to 6 hexadecimal digits, a brace); the escape is turned back to the real character when the name crosses the border again. A literal `{` that would start such text is itself written as `{U+007B}` so that the mapping stays reversible. The unit is platform-independent (no DOS calls); another unit sets the three global flags on a DOS target. On other platforms the flags stay False and the general pair does nothing. Not thread-safe against changes of the flags or the code page; the conversion routines themselves keep no state.

## 2. Interface

```pascal
unit TvDosNames;

interface

var
  { True when the DOS takes and gives names in UTF-8; the functions DosNameToUtf8/DosNameFromUtf8 do nothing while it is False }
  NamesUtf8: Boolean = False;

{ A name of the program (bytes of the page) as the DOS wants it. }
function DosNameToUtf8(const S: string): string;
{ A name from the DOS as the program wants it (bytes of the page). }
function DosNameFromUtf8(const S: string): string;

var
  { The names are mapped by NameToDos and NameFromDos }
  NamesMapped: Boolean = False;
  { The provider is there (also when the program did not switch the mode on): U+XXXX in braces is the form of a character that the page lacks }
  NamesProvider: Boolean = False;

{ A name of the program as the DOS wants it, and a name of the DOS as the program wants it. }
function NameToDos(const S: string): string;
function NameFromDos(const S: string): string;
```

`string` is the compiler's default string type of the library; results must not be truncated for names within its limits.

## 3. Behaviour

### 3.1 The escape `{U+XXXX}` (common definition)

An escape at a position of a text is: `{`, `U` (upper case only), `+`, then 4 to 6 hexadecimal digits (either case), then `}`; its value is the digits read as a number and must be at most $10FFFF. Anything else (3 or fewer digits, 7 or more digits, no closing brace, a non-hex character, value above $10FFFF) is not an escape and is ordinary text. A surrogate value is not specially rejected. Escapes written by the unit use upper-case hexadecimal, at least 4 digits (so U+1F600 is `{U+1F600}`, U+65E5 is `{U+65E5}`). An escape may also name an ASCII character (`{U+0041}` is `A`); the one the unit writes itself is `{U+007B}` for `{`.

### 3.2 DosNameToUtf8(S): program with a code page -> DOS in UTF-8

While `NamesUtf8` is False the result is `S` unchanged. While it is True the result is built left to right: an escape (3.1) is replaced by the UTF-8 encoding of its code point; any other byte below $80 is copied; any byte $80 and above is replaced by the UTF-8 encoding of the Unicode value that the current code page gives to that byte (TvCodePg `CpToUnicode`). The escape recognition is not conditional on `NamesProvider`.

Examples (current page cp866): `#$8F#$E0#$A8#$A2#$A5#$E2` (Privet) -> `D0 9F D1 80 D0 B8 D0 B2 D0 B5 D1 82`; `readme.txt` unchanged; Privet + `.txt` -> Privet(UTF-8) + `.txt`; `{U+65E5}{U+672C}{U+8A9E}` -> `E6 97 A5 E6 9C AC E8 AA 9E`; Privet(cp866) + `{U+65E5}` -> Privet(UTF-8) + `E6 97 A5`; `a{U+007B}U+x}` -> `a{U+x}`.

### 3.3 DosNameFromUtf8(S): DOS in UTF-8 -> program with a code page

While `NamesUtf8` is False the result is `S`. While it is True, scan left to right:
* An ASCII byte is copied, except that every `{` that is immediately followed by `U+` (the three characters `{U+`, whether or not a full escape follows) is replaced by the text `{U+007B}` (only the brace is replaced; the following characters are copied as usual).
* A byte $80 or above that starts a valid UTF-8 sequence is decoded to a code point; if the current code page has that character (TvCodePg `CpFromUnicode` non-zero) the page byte is written, otherwise the escape of 3.1 with the code point in upper-case hex (at least 4 digits). The whole sequence is consumed.
* A byte that does not start a valid UTF-8 sequence is copied as it is and one byte is consumed.

Examples (cp866): Privet(UTF-8) -> `8F E0 A8 A2 A5 E2`; `readme.txt` unchanged; Japanese `E6 97 A5 E6 9C AC E8 AA 9E` -> `{U+65E5}{U+672C}{U+8A9E}`; Privet(UTF-8)+Japanese -> Privet(cp866) + `{U+65E5}{U+672C}{U+8A9E}`; `a{U+x}` -> `a{U+007B}U+x}`; `FF FE 61` unchanged. Round trip: `DosNameFromUtf8(DosNameToUtf8(Privet_cp866))` = Privet_cp866.

### 3.4 NameToDos(S) and NameFromDos(S): the general pair

Both return `S` unchanged unless `NamesMapped` is True. When mapped, the behaviour depends on the UTF-8 mode of the library (`Utf8Enabled` of TvUtf8) and on `NamesUtf8`:

| Program | DOS | NameToDos | NameFromDos |
|---|---|---|---|
| UTF-8 mode on | `NamesUtf8` True | unchanged | unchanged |
| UTF-8 mode on | `NamesUtf8` False (code page) | Utf8ToPage | PageToUtf8 |
| UTF-8 mode off | any | DosNameToUtf8 | DosNameFromUtf8 |

(In the last row the functions themselves do nothing when `NamesUtf8` is False, so program page + DOS page leaves the name as it is.)

**Utf8ToPage** (UTF-8 program, DOS code page), left to right: an ASCII byte is copied, except that when `NamesProvider` is True every `{` followed by `U+` becomes `{U+007B}`; a valid UTF-8 sequence becomes the page byte if the current page has the character, else `{U+XXXX}` (3.1 spelling) when `NamesProvider` is True, else `_`; a stray byte that is not valid UTF-8 is copied and one byte consumed.

**PageToUtf8** (UTF-8 program, DOS code page), left to right: when `NamesProvider` is True and an escape (3.1) starts at the position, it is replaced by the UTF-8 encoding of its code point; otherwise a byte below $80 is copied and a byte $80 or above becomes the UTF-8 encoding of the code page's Unicode value for it. Without a provider, `{U+XXXX}` is plain text.

Examples (UTF-8 mode on, `NamesMapped` True, page cp866):
* `NamesUtf8` True: Privet(UTF-8) unchanged both directions.
* `NamesUtf8` False, provider False: NameToDos(Privet UTF-8) = Privet(cp866) bytes; NameFromDos(Privet cp866) = Privet UTF-8; NameToDos(Japanese) = `___` (one underscore per character); NameFromDos(`{U+65E5}`) = `{U+65E5}` (plain text).
* `NamesUtf8` False, provider True: NameToDos(Japanese) = `{U+65E5}{U+672C}{U+8A9E}`; NameToDos(`a` + Japanese + `.txt`) = `a{U+65E5}{U+672C}{U+8A9E}.txt`; NameFromDos(`{U+65E5}{U+672C}{U+8A9E}`) = Japanese; NameFromDos(Privet cp866 + `{U+65E5}`) = Privet UTF-8 + `E6 97 A5`; NameFromDos(NameToDos(Privet UTF-8 + Japanese)) = Privet UTF-8 + Japanese; NameToDos(`{U+x}`) = `{U+007B}U+x}`; NameFromDos(`{U+007B}U+x}`) = `{U+x}`; NameFromDos(`{U+12}`) = `{U+12}` (fewer than 4 digits); NameFromDos(`{U+110000}`) = `{U+110000}` (above U+10FFFF).
* UTF-8 mode off, `NamesUtf8` True: NameToDos(Privet cp866) = Privet UTF-8. `NamesUtf8` False: NameToDos(Privet cp866) = Privet cp866.
* `NamesMapped` False: NameToDos(Privet UTF-8) is unchanged whatever the other flags.

Notes on edge cases: the empty string maps to the empty string in all routines. A page byte $80 or above for which the page has no Unicode value is outside the tested domain (behaviour then is whatever the encoder does with the page's value for it; a conforming implementation may use U+FFFD or the byte itself). Without the provider a literal `{U+` in a program name is not protected in Utf8ToPage, so such a name is not reversible; this is accepted.

## 4. Dependencies

* TvCodePg: `CpToUnicode(Byte): LongWord` (Unicode value of a byte of the current page), `CpFromUnicode(LongWord): Byte` (0 when the page lacks the character), `CpSelect(Integer)` (used by the tests to choose page 866).
* TvUtf8: `Utf8Enabled: Boolean`, `Utf8Encode(CodePoint, Buffer): Integer` (bytes written), `Utf8Decode(Bytes pointer, Available: Integer, out CodePoint: LongWord, out Used: Integer): Boolean` (False for an invalid or truncated sequence).
* Standard: SysUtils (hexadecimal conversion in both directions).

## 5. Checks for a test program

Select code page 866 first, and restore flags at the end (UTF-8 mode off, `NamesMapped` False).
1. With `NamesUtf8` False, DosNameToUtf8 and DosNameFromUtf8 are identities on Privet in both encodings.
2. With `NamesUtf8` True, all examples of 3.2 and 3.3, including mixed names, ASCII names, the extension, stray bytes `FF FE 61`, the brace-escape cases, and round trips in both directions (name -> UTF-8 -> name).
3. Escape recognition boundaries in DosNameToUtf8: `{U+0041}` -> `A`; `{U+004}` (3 digits), `{U+1234567}` (7 digits), `{U+110000}`, `{U+12G4}`, `{U+1234` (no brace) all stay as plain text byte for byte; 6 digits `{U+01F600}` -> F0 9F 98 80; lower-case hex accepted; `{u+0041}` not an escape.
4. DosNameFromUtf8 of a 4-byte character outside the BMP gives `{U+1F600}`; of `{U+` at the end of the text gives `{U+007B}U+`.
5. The table of 3.4 in all combinations of Utf8Enabled, NamesUtf8, NamesProvider with NamesMapped True; with NamesMapped False everything is the identity.
6. Two sequential characters absent from the page and a character present in the page in one name keep their order.
