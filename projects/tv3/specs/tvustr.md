# Unit TvUStr - functional specification

## 1. Purpose

`TvUStr` provides operations on byte strings (`AnsiString`, plus `ShortString` for some mutators) that may hold UTF-8 text. It lets a program address such strings by character ("column"), by screen cell, and by case, without ever losing data: a byte that is not part of a valid UTF-8 sequence is kept untouched and counts as one character of its own. When `Utf8Enabled` is False, the unit does no decoding at all and treats one byte as one column and one cell. Case mapping uses its own small tables (no runtime-library Unicode tables), so the unit also works on platforms without them.

Terms used below:

- **byte index**: 1-based position in the string (the Pascal one).
- **column**: 0-based number of a character. A character is either one valid UTF-8 sequence or one stray byte. A valid sequence is shortest-form, not a surrogate, at most U+10FFFF (this is what `Utf8Decode` accepts). Any byte that does not start a valid, complete sequence is a one-byte character, and decoding resynchronises on the next byte. A sequence cut off by the end of the string is therefore one stray byte for its first byte, and its remaining bytes are further stray bytes.
- **cell**: a screen position. A character occupies `CharWidth` cells: 2 for wide characters (CJK, etc.), 0 for combining and format marks, 1 otherwise. Only multi-byte characters have their own width. A stray byte, any ASCII byte (including controls) and any multi-byte character whose `CharWidth` is negative (for example U+0080..U+009F) take exactly 1 cell.
- **UTF-8 mode**: `Utf8Enabled = True`. **Byte mode**: `Utf8Enabled = False`.

## 2. Additions required of TvUtf8

The unit depends on the following, which must be visible to it through `uses TvUtf8` (or be written inside `TvUStr` if the new `TvUtf8` has them only as members of `TText` or under other names).

- `var Utf8Enabled: Boolean = True;` a plain assignable global variable (tests assign it). True: text that is valid UTF-8 is treated as UTF-8. False: the bytes of the text are the bytes of the current code page, so one byte is one character and nothing is decoded (in a one-byte code page such as CP866, valid-looking UTF-8 byte pairs must not be merged into a character). The default is True. This variable is the only thing that must really be added to TvUtf8.
- `const MaxCharSize = 4` (longest UTF-8 sequence). Needed only as a buffer size.
- A validating decoder (name `Utf8Decode`): given a pointer to bytes and the number of available bytes, it reports whether the bytes at the start form one valid UTF-8 sequence (shortest form, non-surrogate, at most U+10FFFF), and if so gives the code point and the number of bytes used. For invalid or truncated input it only has to report failure. Anything the new TvUtf8 offers with this meaning (for example the decoding step of `TText.Next`) may be used; if it only works on its own text type, write a small private validating decoder inside `TvUStr`. The rules are: lead bytes C2..DF take 1 continuation byte, E0..EF take 2, F0..F4 take 3; continuation bytes are 80..BF; E0 needs A0..BF second, ED needs 80..9F second, F0 needs 90..BF second, F4 needs 80..8F second; C0, C1, F5..FF never start a sequence.
- An encoder (name `Utf8Encode`): code point to 1..4 bytes (<= $7F: 1 byte, <= $7FF: 2, <= $FFFF: 3, otherwise 4), returns the byte count. It does no validation. The unit needs it for `U8Encode` and for case mapping; the new TvUtf8 has UTF-8 conversions, so use them or write the trivial encoder inside the unit.
- `CharWidth(CodePoint: LongWord): Integer`: -1 for control characters (< $20 and $7F..$9F), 0 for combining marks and format characters, 2 for East Asian Wide/Fullwidth, 1 otherwise. The new TvUtf8 has `CharWidth`; the unit only needs the values above. Everything else in TvUtf8 (`TText`, `Measure`, `Next`, `Prev`, UTF-16/32 conversion) is not required.

## 3. Interface (the contract)

```pascal
unit TvUStr;

interface

uses
  TvUtf8;

{ --- bytes and columns --- }
function U8CharBytes(const S: AnsiString; Idx: Integer): Integer;
function U8IsAscii(const S: AnsiString): Boolean;
function U8Len(const S: AnsiString): Integer;
function U8Idx(const S: AnsiString; Col: Integer): Integer;
function U8Col(const S: AnsiString; Idx: Integer): Integer;
function U8PrevIdx(const S: AnsiString; Idx: Integer): Integer;

{ --- cutting (columns are 0-based) --- }
function U8Copy(const S: AnsiString; Col, Cnt: Integer): AnsiString;
function U8Char(const S: AnsiString; Col: Integer): AnsiString;
procedure U8Delete(var S: AnsiString; Col, Cnt: Integer); overload;
procedure U8Delete(var S: ShortString; Col, Cnt: Integer); overload;
procedure U8Insert(const Sub: AnsiString; var S: AnsiString; Col: Integer); overload;
procedure U8Insert(const Sub: AnsiString; var S: ShortString; Col: Integer); overload;
function U8ColChar(const S: AnsiString; Col: Integer): Char;
function U8CodePoint(const S: AnsiString; Col: Integer): LongWord;
function U8Encode(CP: LongWord): AnsiString;
function U8Prefix(const S: AnsiString; MaxBytes: Integer): AnsiString;
procedure U8DeleteLast(var S: AnsiString); overload;
procedure U8DeleteLast(var S: ShortString); overload;

{ --- screen cells --- }
function U8Cells(const S: AnsiString; Col, Cnt: Integer): Integer;
function U8Cols(const S: AnsiString): Integer;
function U8ColAtCell(const S: AnsiString; Cell: Integer): Integer;
function U8Pad(const S: AnsiString; Cells: Integer): AnsiString;
function U8Fit(const S: AnsiString; Cells: Integer): AnsiString;

{ --- case --- }
function CpUpper(CP: LongWord): LongWord;
function CpLower(CP: LongWord): LongWord;
function U8Upper(const S: AnsiString): AnsiString;
function U8Lower(const S: AnsiString): AnsiString;
function U8CapFirst(const S: AnsiString): AnsiString;
function U8EqualNoCase(const A, B: AnsiString): Boolean;
```

No other symbols are exported. The unit has no state. All routines are pure except the `var` procedures.

## 4. Behaviour

Notation: in examples `Privet` is the 12-byte string D0 9F D1 80 D0 B8 D0 B2 D0 B5 D1 82 (six Cyrillic letters, columns 0..5, each 2 bytes); `Japan` is E6 97 A5 E6 9C AC (two wide characters, 3 bytes each); `Acute` is C3 A9 (U+00E9); `Comb` is CC 81 (U+0301, width 0).

### 4.1 Characters and indices

**U8CharBytes(S, Idx)** returns the byte length of the character starting at byte index Idx. It is 0 when Idx <= 0 or Idx > Length(S). Otherwise it is 1 if the byte is ASCII (< $80), or the mode is byte mode, or the bytes from Idx on do not begin with a valid sequence (stray byte, including a truncated sequence at the end of the string); else the sequence length 2..4. It does not check that Idx is on a character boundary (a continuation byte is simply a stray byte of length 1). Examples: `U8CharBytes(Privet,1)=2`, `(Privet,2)=1` (a continuation byte is a stray byte), `(Privet,13)=0`, `('ab'#$D0,3)=1`.

**U8IsAscii(S)** is True when every byte is < $80 (True for the empty string). It ignores `Utf8Enabled`.

**U8Len(S)** is the number of columns. Byte mode or an all-ASCII string: Length(S). Otherwise the number of characters per the definition above. Empty string: 0. Examples: `U8Len('abc')=3`, `U8Len(Privet)=6`, `U8Len('a'+Acute+#$F0#$9F#$98#$80)=3`, `U8Len('a'#$80'b')=3`, `U8Len('ab'#$D0)=3`. In byte mode `U8Len(Privet)=12`.

**U8Idx(S, Col)** is the byte index where column Col starts. Col <= 0 gives 1 (also for the empty string). If Col is at or beyond the number of columns, the result is Length(S)+1. In byte mode the result is `Col+1`, with Col first limited to Length(S). Examples: `U8Idx(Privet,0)=1`, `(Privet,2)=5`, `(Privet,6)=13`, `(Privet,99)=13`, `(-3)=1`; with `S='a'+Acute+smile` (smile = F0 9F 98 80): columns 0,1,2,3 give 1,2,4,8. In byte mode `U8Idx(Privet,3)=4`.

**U8Col(S, Idx)** is the column of the byte at index Idx. Idx <= 1 gives 0. Byte mode gives Idx-1 for any Idx. In UTF-8 mode the result is the number of whole characters that lie completely before Idx, so: if Idx points inside a character the result is the column of that character; Idx = Length(S)+1 gives U8Len(S); beyond that every extra byte position counts as one more column. Examples: `U8Col(Privet,5)=2`, `(Privet,6)=2` (inside column 2), `(Privet,13)=6`, `(Privet,15)=8`, `(Privet,0)=0`.

**U8PrevIdx(S, Idx)** is the byte index of the start of the last character that starts before Idx; 1 when Idx <= 1 (and when there is no earlier character). Characters are delimited as in U8CharBytes, and positions beyond the end of the string count as one-byte characters. If Idx points inside a character, the result is the start of that character (the one containing Idx), not of the preceding one. Examples: `U8PrevIdx(Privet,5)=3`, `(Privet,6)=5`, `(Privet,13)=11`, `(Privet,1)=1`, `(Privet,2)=1`, `(Privet,20)=19`. In byte mode it is `Idx-1` for Idx >= 2.

### 4.2 Cutting (columns 0-based)

**U8Copy(S, Col, Cnt)** returns the characters of columns Col .. Col+Cnt-1. A negative Col is first cut off from the count: Cnt := Cnt+Col, Col := 0. If the resulting Cnt <= 0 the result is ''. Columns past the end are simply missing (no error). Examples: `U8Copy(Privet,1,3)` = D1 80 D0 B8 D0 B2; `U8Copy(Privet,-2,4)` = D0 9F D1 80 (columns 0..1); `U8Copy(Privet,4,99)` = D0 B5 D1 82; `U8Copy(Privet,6,1)=''`; `U8Copy(Privet,0,0)=''`; `U8Copy(Privet,-5,3)=''`. Note: the sum Col+Cnt is computed in `Integer`; callers should not rely on `Cnt=MaxInt` with Col > 0 (see section 7).

**U8Char(S, Col)** equals `U8Copy(S, Col, 1)`: the one character, or '' for Col < 0 or at/past the end. `U8Char(Privet,1)` = D1 80.

**U8Delete(S, Col, Cnt)** (both overloads) removes the same columns that `U8Copy` would return (same treatment of negative Col, Cnt <= 0 and out-of-range). Nothing is changed if nothing is selected. Example: Privet with `U8Delete(S,1,2)` gives D0 9F D0 B2 D0 B5 D1 82. `U8Delete(Sh,0,1)` on a ShortString holding Privet removes the first letter. The ShortString overload behaves like the AnsiString one on the same bytes (the result always fits since it only shrinks).

**U8Insert(Sub, S, Col)** inserts Sub before column Col. Col <= 0 inserts at the start; Col >= the number of columns appends. For the ShortString overload the result is stored into a ShortString, so it is silently truncated to 255 bytes (the cut is by byte and may split a character). Example: inserting `'x'` into Privet at 3 gives D0 9F D1 80 D0 B8 'x' D0 B2 D0 B5 D1 82. `U8Insert('x','ab',99)` gives `'abx'`; into `''` at any column gives `'x'`.

**U8ColChar(S, Col)** returns the first byte of the character at Col, or `' '` (space) if Col < 0 or Col is at/past the end. `U8ColChar(Privet,1)=#$D1`, `U8ColChar('ab',2)=' '`.

**U8CodePoint(S, Col)** returns the code point of the character at Col. For a stray byte (or any byte in byte mode) it is the byte value (e.g. `U8CodePoint('a'#$80,1)=$80`). For Col < 0 or past the end it is 0 (a real NUL character also gives 0). Examples: `U8CodePoint(Privet,1)=$440`, `U8CodePoint('a',5)=0`, `U8CodePoint('a',0)=$61`, `U8CodePoint(Japan,0)=$65E5`.

**U8Encode(CP)** returns the UTF-8 bytes of CP as a string of 1 to 4 bytes (1 for <= $7F, 2 for <= $7FF, 3 for <= $FFFF, otherwise 4). There is no validation: surrogates are encoded arithmetically, and values above $10FFFF are not meaningful (their result is unspecified, not tested). `U8Encode(0)` is a one-byte string #0. Examples: `U8Encode($439)` = D0 B9, `U8Encode($41)='A'`, `U8Encode($20AC)` = E2 82 AC, `U8Encode($1F600)` = F0 9F 98 80. This routine does not depend on `Utf8Enabled`.

**U8Prefix(S, MaxBytes)** returns the longest beginning of S with at most MaxBytes bytes that does not cut a character in the middle. MaxBytes < 0 is treated as 0. If Length(S) <= MaxBytes the whole S is returned. Otherwise, in byte mode the result is the first MaxBytes bytes. In UTF-8 mode, let N = MaxBytes; while N > 0 and the byte just after the cut (byte N+1) is a continuation byte (80..BF), N is decreased by one; the result is the first N bytes. This test looks only at the byte values; it does not validate sequences (a stray continuation byte is treated as belonging to the byte before it). Examples: `U8Prefix(Privet,5)` = D0 9F D1 80 (the cut would fall inside D0 B8), `U8Prefix(Privet,4)` = D0 9F D1 80, `U8Prefix(Privet,99)=Privet`, `U8Prefix(Privet,0)=''`, `U8Prefix(Privet,-1)=''`, `U8Prefix('abc',2)='ab'`, `U8Prefix('a'#$80#$80'b',2)=''` (a consequence of the rule).

**U8DeleteLast(S)** (both overloads) removes the last character; an empty string stays empty. In byte mode it removes the last byte. In UTF-8 mode it finds the start of the last character by moving back over continuation bytes (80..BF) while more than one byte remains, then deletes everything from that point. As with U8Prefix, it looks only at byte values. Examples: Privet gives D0 9F D1 80 D0 B8 D0 B2 D0 B5; `'ab'` gives `'a'`; `'a'+Acute` gives `'a'`; `'ab'#$D0` gives `'ab'`; `'a'#$80` gives `''` (the stray byte is swallowed together with the byte before it).

### 4.3 Screen cells

**U8Cells(S, Col, Cnt)** is the number of screen cells taken by Cnt columns starting at column Col. Cnt <= 0 gives 0. In byte mode, or when S is all ASCII, the result is Cnt exactly (whatever Col is, even past the end). Otherwise the columns are visited from Col (a Col <= 0 starts at column 0; it is not cut off from Cnt as U8Copy does), each column contributes its width as defined in section 1 (wide 2, combining 0, others 1), and each column past the end contributes 1. Examples: `U8Cells(Japan,1,1)=2`, `U8Cells('ab',1,3)=3`, `U8Cells('a'+Japan,0,2)=3`, `U8Cells('a'+Comb+'b',0,3)=2`, `U8Cells(Japan,2,3)=3`.

**U8Cols(S)** is the number of cells of the whole string: `U8Cells(S, 0, U8Len(S))`. Examples: `U8Cols(Japan)=4`, `U8Cols('a'+Japan)=5`, `U8Cols('a'+Comb)=1`, `U8Cols('')=0`. In byte mode `U8Cols(Privet)=12`.

**U8ColAtCell(S, Cell)** returns the column that is drawn at the 0-based cell number Cell. Cell <= 0 gives 0. In byte mode, or when S is all ASCII, it returns Cell (even beyond the end). Otherwise, the result is the first column whose cumulative cell count (cells of this column and all before it) exceeds Cell; so a cell inside a wide character belongs to that wide character, and zero-width characters are never returned (the cell they follow belongs to the previous base character, and a mark that follows the last cell position is skipped to the next column). If no column qualifies (Cell is at or past the total number of cells), the result is the number of columns plus the excess `Cell - TotalCells` (past the end every column takes one cell). Examples with `T='a'+Japan+'b'` (cells: a=0, first wide=1..2, second wide=3..4, b=5): `U8ColAtCell(T,2)=1`, `(T,4)=2`, `(T,1)=1`, `(T,3)=2`, `(T,5)=3`, `(T,6)=4`, `(T,0)=0`; `U8ColAtCell('ab',5)=5`; `U8ColAtCell('a'+Comb+'b',1)=2`; `U8ColAtCell(Acute,5)=5` (non-ASCII string, the excess rule gives 1+(5-1)). Note that for a string that ends with combining marks the result for Cell equal to the total number of cells is the column count (the mark columns are skipped).

**U8Pad(S, Cells)** appends spaces so that the string occupies Cells cells: `U8Cols(S)` spaces are subtracted. When S already takes Cells cells or more, S is returned unchanged (never cut). Examples: `U8Pad(Japan,6)=Japan+'  '`, `U8Pad(Japan,2)=Japan`, `U8Pad('ab',1)='ab'`, `U8Pad('',3)='   '`, `U8Pad('x',0)='x'`.

**U8Fit(S, Cells)** returns the longest run of leading columns whose total width is at most Cells. Cells <= 0 gives ''. In byte mode, or when S is all ASCII, the result is the first Cells bytes (the whole S if shorter). Otherwise columns are taken one at a time and the process stops at the first column that would make the total exceed Cells; the later columns are not considered even if they would fit. A wide character that does not fit is therefore dropped, and zero-width marks that follow the last fitting character are kept (they add 0). Examples: `U8Fit('a'+Japan,2)='a'`, `U8Fit('a'+Japan,3)='a'+E6 97 A5`, `U8Fit('a'+Japan,5)='a'+Japan`, `U8Fit(Japan,1)=''`, `U8Fit('a'+Comb+'b',1)='a'+Comb`, `U8Fit('abc',2)='ab'`, `U8Fit('abc',0)=''`.

### 4.4 Case

Case is the simple one-to-one Unicode mapping restricted to the ranges below. Define CpUpper(c) and CpLower(c) as total functions on LongWord that return c itself for every code point not listed. Characters outside the BMP, titlecase digraphs, Latin Extended-B (other than U+01CD/U+01CE), Greek Extended (U+1F00..), Georgian, Hebrew, Arabic, CJK and everything else are unchanged. There are no multi-character mappings (U+00DF stays; U+1E9E is not mapped either way). The mappings depend on nothing but the code point (not on `Utf8Enabled`).

"Pair range [A..B], upper at even" means: for c in A..B, an odd c is the lower letter of the pair, its upper letter is c-1; an even c is the upper letter, its lower letter is c+1. "Upper at odd" is the opposite: an even c is lower with upper c-1, an odd c is upper with lower c+1.

**CpUpper** (everything not listed is returned unchanged):

| Code points | Result |
|---|---|
| $61..$7A | c - $20 |
| $B5 (micro) | $39C |
| $E0..$F6, $F8..$FE | c - $20 ($F7 and $DF unchanged) |
| $FF | $178 |
| $100..$12F | pair, upper at even (odd c gives c-1) |
| $131 (dotless i) | $49 ('I') |
| $132..$137 | pair, upper at even |
| $139..$148 | pair, upper at odd (even c gives c-1); $138 and $149 unchanged |
| $14A..$177 | pair, upper at even |
| $17A..$17E | even c gives c-1 (upper at odd, pairs inside $179..$17E) |
| $17F (long s) | $53 ('S') |
| $1CE | $1CD |
| $1E00..$1E95 and $1EA0..$1EFF | pair, upper at even; $1E96..$1E9F unchanged |
| $3AC | $386 |
| $3AD..$3AF | c - $25 |
| $3B1..$3C1 and $3C3..$3CB | c - $20 |
| $3C2 (final sigma) | $3A3 |
| $3CC | $38C |
| $3CD, $3CE | c - $3F |
| $430..$44F | c - $20 |
| $450..$45F | c - $50 |
| $460..$481, $48A..$4BF, $4D0..$52F | pair, upper at even ($482..$489 unchanged) |
| $4C2..$4CE | even c gives c-1 (pairs $4C1/$4C2 ... $4CD/$4CE) |
| $4CF | $4C0 |
| $561..$586 | c - $30 |
| $2170..$217F | c - $10 (small Roman numerals) |
| $24D0..$24E9 | c - $1A (circled small letters) |
| $FF41..$FF5A | c - $20 (full-width small letters) |

**CpLower** (everything not listed is returned unchanged):

| Code points | Result |
|---|---|
| $41..$5A | c + $20 |
| $C0..$D6, $D8..$DE | c + $20 |
| $100..$12F | pair, upper at even (even c gives c+1) |
| $130 (dotted I) | $69 ('i') |
| $132..$137 | even c gives c+1 |
| $139..$148 | odd c gives c+1 |
| $14A..$177 | even c gives c+1 |
| $178 | $FF |
| $179..$17E | odd c gives c+1 |
| $1CD | $1CE |
| $1E00..$1E95 and $1EA0..$1EFF | even c gives c+1 ($1E9E unchanged) |
| $386 | $3AC |
| $388..$38A | c + $25 |
| $38C | $3CC |
| $38E, $38F | c + $3F |
| $391..$3A1 and $3A3..$3AB | c + $20 |
| $400..$40F | c + $50 |
| $410..$42F | c + $20 |
| $460..$481, $48A..$4BF, $4D0..$52F | even c gives c+1 |
| $4C0 | $4CF |
| $4C1..$4CD | odd c gives c+1 |
| $531..$556 | c + $30 |
| $2160..$216F | c + $10 |
| $24B6..$24CF | c + $1A |
| $FF21..$FF3A | c + $20 |

Worked values: `CpUpper($3C2)=$3A3`, `CpLower($130)=$69`, `CpUpper($45F)=$40F`, `CpUpper($E9)=$C9`, `CpUpper($FF)=$178`, `CpLower($178)=$FF`, `CpUpper($101)=$100`, `CpLower($100)=$101`, `CpUpper($148)=$147`, `CpLower($147)=$148`, `CpUpper($17E)=$17D`, `CpLower($179)=$17A`, `CpLower($138)=$138`, `CpUpper($DF)=$DF`, `CpUpper($3CE)=$38F`, `CpLower($38F)=$3CE`, `CpUpper($44F)=$42F`, `CpUpper($561)=$531`, `CpUpper($1E01)=$1E00`, `CpLower($1E9E)=$1E9E`, `CpUpper($4CF)=$4C0`, `CpLower($4C0)=$4CF`, `CpUpper($4C2)=$4C1`, `CpUpper($FF41)=$FF21`, `CpUpper($10D0)=$10D0` (Georgian unchanged), `CpUpper($B5)=$39C`, `CpLower($39C)=$3BC`, `CpUpper($131)=$49`, `CpUpper($17F)=$53`, `CpUpper($1CE)=$1CD`.

Consistency property (tested for code points $80..$24FF): for every c, if `CpLower(c) <> c` then `CpUpper(CpLower(c)) = c`, except c in {$130, $3A3, $1E9E}; and if `CpUpper(c) <> c` then `CpLower(CpUpper(c)) = c`, except c in {$B5, $131, $17F, $3C2}. (The exceptions are the one-way mappings; $3A3 and $1E9E are listed in the test but satisfy or avoid the property anyway.)

**U8Upper(S)** and **U8Lower(S)** map every character of S. In byte mode, and for all-ASCII strings, only the ASCII letters change (a-z / A-Z), every byte >= $80 is left alone. Otherwise the string is scanned: each valid multi-byte sequence is decoded, mapped by CpUpper/CpLower, and re-encoded (if the mapping returns the same code point, the original bytes are copied as they are; if it differs, the new code point is encoded, which may change the byte length, for example U+0131 becomes the one-byte 'I', U+0130 becomes 'i'); ASCII letters are mapped; stray bytes are copied unchanged. The result is therefore always valid where the input was. Examples: `U8Upper(Privet)` = D0 9F D0 A0 D0 98 D0 92 D0 95 D0 A2; `U8Lower(D0 9F D0 A0 D0 98)` = D0 BF D1 80 D0 B8; `U8Upper('abc'+Acute)='ABC'+C3 89`; `U8Upper('a'#$80'b')='A'#$80'B'`; `U8Upper(Japan)=Japan`; `U8Upper(C4 B1)='I'`; `U8Lower(C4 B0)='i'`; `U8Upper('ab'#$D0)='AB'#$D0`; `U8Upper('')=''`; in byte mode `U8Upper('abc')='ABC'` and `U8Upper(Privet)=Privet`.

**U8CapFirst(S)** returns S with only its first character converted to upper case (via `U8Upper` of the first character; the first character is determined with `U8CharBytes(S,1)`), the rest unchanged. `''` gives `''`. Examples: `U8CapFirst(D0 BF D1 80)` = D0 9F D1 80; `U8CapFirst(Privet)=Privet`; `U8CapFirst('abc')='Abc'`; `U8CapFirst(#$80'a')=#$80'a'`. In byte mode only the first byte is considered, and only an ASCII letter changes.

**U8EqualNoCase(A, B)** is True when A = B byte for byte, or when `U8Lower(A) = U8Lower(B)`. It compares lower-case forms only; hence characters that are the target of a one-way mapping do not equal their lower forms: for example 'S' and U+017F are not equal, U+03C2 and U+03A3 are not equal (Lower of U+03A3 is U+03C3), while U+0130 equals 'i'. Examples: `U8EqualNoCase(Privet,U8Upper(Privet))` is True; `U8EqualNoCase(Privet,'privet')` is False; `U8EqualNoCase('','')` is True; `U8EqualNoCase('Abc','aBC')` is True.

## 5. Mode summary (Utf8Enabled = False)

Every routine treats each byte as one character of one cell: `U8CharBytes` = 1 inside the string; `U8Len` = Length; `U8Idx(Col)` = min(Col,Length)+1 (1 for Col <= 0); `U8Col(Idx)` = Idx-1 (0 for Idx <= 1); `U8PrevIdx` = Idx-1 (min 1); `U8CodePoint` = byte value; `U8Prefix` = first MaxBytes bytes; `U8DeleteLast` removes one byte; `U8Cells` = Cnt; `U8ColAtCell` = Cell; `U8Fit` = first Cells bytes; `U8Upper`/`U8Lower`/`U8CapFirst` change only ASCII letters. `CpUpper`/`CpLower` and `U8Encode` do not look at the flag.

## 6. Dependencies

- Uses only `TvUtf8` (section 2). No other unit, no RTL Unicode tables, no file or OS access, no global state besides reading `Utf8Enabled`.
- No exceptions are raised; invalid input never fails (stray bytes are data). Out-of-range indices are handled as described per routine, never as errors. Strings are `AnsiString` and compared bytewise.
- `Integer` is assumed to be 32 bits and `LongWord` 32 bits unsigned.

## 7. Checks for a test program

Use a `Check(cond, message)` helper and run with `Utf8Enabled := True` unless stated.

1. Lengths: `U8Len('abc')=3`, `U8Len(Privet)=6`, `U8Len('a'+Acute+smile)=3`, `U8Len('a'#$80'b')=3`, `U8Len('ab'#$D0)=3`, `U8Len('')=0`.
2. Indices: `U8Idx(Privet,0|2|6|99|-1)` = 1, 5, 13, 13, 1; `U8Col(Privet,5|6|13|15|0)` = 2, 2, 6, 8, 0; `U8PrevIdx(Privet,5|6|13|1|2)` = 3, 5, 11, 1, 1; `U8CharBytes` at 1, 2, 13, 0, -1 of Privet = 2, 1, 0, 0, 0.
3. Cutting: all `U8Copy`, `U8Char`, `U8Delete` and `U8Insert` examples of section 4.2 (negative Col, Cnt 0, past the end, empty string); the ShortString overloads of `U8Delete`, `U8Insert`, `U8DeleteLast` give the same bytes as the AnsiString ones; ShortString insert beyond 255 bytes is truncated to 255.
4. `U8CodePoint` for a letter ($440), a stray byte ($80), past the end (0), negative column (0), a 3-byte character; `U8Encode` for $41, $439, $20AC, $1F600 and round trip `U8CodePoint(U8Encode(x),0)=x` for x in {$7F, $80, $7FF, $800, $FFFF (not a surrogate), $10000, $10FFFF}.
5. `U8Prefix` and `U8DeleteLast` examples of section 4.2 including the ASCII, truncated-lead and `'a'#$80` cases.
6. Invalid UTF-8: C0 80 (overlong), ED A0 80 (surrogate), F4 90 80 80 (> U+10FFFF), lone continuation byte, truncated 3-byte sequence followed by an ASCII byte: each byte is its own column and `U8Upper` returns the bytes unchanged apart from ASCII letters.
7. Cells: `U8Cols`, `U8Cells`, `U8ColAtCell`, `U8Pad`, `U8Fit` examples of section 4.3, including the combining mark cases and a C1 control (C2 85 takes 1 cell).
8. Case: every worked value of section 4.4, the consistency loop over $80..$24FF with the stated exceptions (expect zero violations), boundaries of each range (first and last code point, and the code point just before and just after, which must be unchanged: for example $F7, $DF, $138, $149, $17F lower, $1E96, $1E9E, $482, $4C1 upper, $3A2, $3B0), length-changing cases (U+0131, U+0130, U+017F in `U8Upper`/`U8Lower` of a string), and the string-level examples of `U8Upper`, `U8Lower`, `U8CapFirst`, `U8EqualNoCase`.
9. Byte mode (`Utf8Enabled := False`): `U8Len(Privet)=12`, `U8Cols(Privet)=12`, `U8Idx(Privet,3)=4`, `U8Idx(Privet,99)=13`, `U8Col(Privet,15)=14`, `U8Upper('abc')='ABC'`, `U8Upper(Privet)=Privet`, `U8Prefix(Privet,5)` = first 5 bytes, `U8DeleteLast(Privet)` leaves 11 bytes, `U8Fit(Privet,3)` = 3 bytes. Restore True afterwards.
10. Idempotence: `U8Upper(U8Upper(x)) = U8Upper(x)` and `U8Lower(U8Upper(U8Lower(x))) = U8Lower(x)` for sample strings made of letters whose mapping is two-way.

## 8. Known quirks to preserve (or consciously decide on)

- `U8Prefix` and `U8DeleteLast` decide by byte class (continuation or not) and do not validate sequences, so on malformed text they disagree with the column model of `U8Len`/`U8Idx` (for example `U8Len('a'#$80)=2` but `U8DeleteLast` of it gives `''`; `U8Prefix('a'#$80#$80'b',2)=''`). The listed results are what the tests' author-visible behaviour requires for valid text; for malformed text the values above are the reference.
- `U8Cells` with a negative Col still counts Cnt columns starting at column 0 (unlike `U8Copy`), and its ASCII shortcut ignores Col entirely.
- `U8PrevIdx` with Idx inside a character returns the start of that character.
- `U8Copy`/`U8Delete` compute `Col+Cnt` in 32-bit `Integer`; `Cnt` near `MaxInt` with positive Col overflows.
- Case tables are limited to the ranges above; they are not full Unicode.
