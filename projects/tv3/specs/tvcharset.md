# Unit TvCharset - functional specification

## 1. Purpose

TvCharset converts texts between UTF-8 and the "character sets" a program meets in files, the clipboard and the terminal: the single-byte sets of DOS and Windows (code pages such as 437, 866, 1251), KOI8-R/U, ISO 8859-n, Mac Roman, and UTF-16 (little and big endian). All conversions go through UTF-8: a set is converted to UTF-8 and from UTF-8. The unit also names the sets (name to id, id to name), lists them for dialogs, checks UTF-8 validity, and guesses which single-byte set a raw text is most likely written in.

It is distinct from TvCodePg (see tvcodepages.md), which keeps the one 256-entry page that the screen of a DOS program shows. TvCharset keeps its own, independent, tables and has no "current" set; it holds no state other than one cache (section 3.9).

Terms: **id** is a LongInt: the number of the set among the Windows code pages (437, 866, 1251 ...); KOI8-R is 20866, KOI8-U 21866, ISO-8859-n is 28590 + n, Mac Roman is 10000, UTF-8 is 65001, UTF-16LE 1200, UTF-16BE 1201. **Raw** text is bytes in the set. **Table** is the 256-entry map byte -> Unicode code point of a single-byte set.

## 2. Interface

```pascal
unit TvCharset;

interface

const
  csUtf8 = 65001;
  csUtf16LE = 1200;
  csUtf16BE = 1201;
  csCp437 = 437;
  csCp866 = 866;
  csCp1251 = 1251;
  csCp1252 = 1252;
  csKoi8R = 20866;
  csLatin1 = 28591;

function CharsetId(const Name: AnsiString): LongInt;
function CharsetName(Id: LongInt): AnsiString;
function CharsetKnown(Id: LongInt): Boolean;
function CharsetListCount: Integer;
function CharsetListId(I: Integer): LongInt;
function CharsetToUtf8(Id: LongInt; const Raw: AnsiString): AnsiString;
function CharsetFromUtf8(Id: LongInt; const Text: AnsiString; out Lost: Integer): AnsiString;
function Utf8Valid(const S: AnsiString): Boolean;
function IsPlainAscii(const S: AnsiString): Boolean;
function CharsetGuess(const Raw: AnsiString; const Candidates: array of LongInt): LongInt;
```

No other public identifiers. The tables and name list are private data (section 4).

## 3. Behaviour

### 3.1 CharsetId(Name)

Returns the id of the set called Name, or 0 if there is none. The name is lower-cased (ASCII letters A-Z only) and not trimmed. Matches, in this order:
* `utf-8`, `utf8` -> 65001.
* `utf-16le`, `utf-16`, `utf16le` -> 1200 (plain `utf-16` means little endian).
* `utf-16be`, `utf16be` -> 1201.
* `ascii`, `us-ascii` -> 28591 (Latin-1; see oddities).
* any name of the name table (section 4.2).
An empty or unknown name gives 0. Examples: `cp866` -> 866; `Windows-1251` -> 1251; `KOI8-R` -> 20866; `UTF-8` -> 65001; `iso-8859-15` -> 28605; `nope` -> 0.

### 3.2 CharsetName(Id)

The usual name of the set: `utf-8` for 65001, `utf-16le` for 1200, `utf-16be` for 1201; for a table set, the first name listed for that id in the name table (so 437 -> `cp437`, 866 -> `cp866`, 1125 -> `cp1125`, 1251 -> `windows-1251`, 20866 -> `koi8-r`, 28591 -> `iso-8859-1`, 10000 -> `macintosh`). Unknown id gives the empty string. The name returned always converts back by CharsetId (except 28591 is not reached from `ascii`).

### 3.3 CharsetKnown(Id)

True for 65001, 1200, 1201 and for every id of the list (section 4.1); False otherwise (12345 is unknown; 0 is unknown).

### 3.4 CharsetListCount / CharsetListId(I)

CharsetListCount is the number of single-byte sets in the tables: 46. CharsetListId(I) for 0 <= I < 46 is the id of the set number I, in the order given in section 4.1 (UTF-8 and UTF-16 are not in this list). I outside the range is a caller error with no defined result (the old unit performs no check).

### 3.5 CharsetToUtf8(Id, Raw)

Raw bytes of set Id as UTF-8.
* Id = 65001: Raw is returned unchanged (no validation, no repair).
* Id = 1200 / 1201: Raw is decoded as UTF-16 little/big endian and re-encoded as UTF-8 (details in 3.7).
* Id of a table set: each byte below $80 is copied as it is (every table set is ASCII-compatible in its low half); each byte >= $80 becomes the UTF-8 of its table value; a byte whose table value is "undefined" becomes U+FFFD (bytes EF BF BD). If Raw has no byte >= $80 it is returned unchanged.
* Unknown Id: Raw is returned unchanged.
The empty string gives the empty string. Examples: cp866 bytes 8F E0 A8 A2 A5 E2 give the UTF-8 of the Russian word "Privet" (U+041F U+0440 U+0438 U+0432 U+0435 U+0442); cp1251 CF F0 E8 E2 E5 F2 and KOI8-R F0 D2 C9 D7 C5 D4 give the same; Latin-1 byte E9 gives C3 A9; cp1252 byte 80 gives E2 82 AC (euro); cp1251 byte 98 (undefined) gives EF BF BD; cp866 "abc" gives "abc".

### 3.6 CharsetFromUtf8(Id, Text, Lost)

Text (UTF-8) as bytes of set Id. Lost is set to the number of characters that could not be represented (always set; 0 for a clean result).
* Id = 65001: Text unchanged, Lost = 0.
* Id = 1200 / 1201: Text is encoded as UTF-16 (3.7); Lost counts invalid input bytes.
* Table set: bytes below $80 are copied; every other character is decoded from UTF-8 (a byte that does not start a valid, complete UTF-8 sequence is treated as one invalid character, decoding then continues with the next byte) and looked up in the reverse of the table restricted to bytes $80..$FF. If found, the byte is written; otherwise a single `?` is written and Lost is incremented. An invalid byte therefore always gives `?` and counts as one lost character; a valid U+FFFD in the text also gives `?` (no table has a mapping for it) and counts. Code points above U+FFFF never match. One input character gives exactly one output byte.
* Unknown Id: Text unchanged, Lost = 0. If Text has no byte >= $80 it is returned unchanged for any table set.
When two bytes of a set map to the same code point, the result is whichever byte the reverse table yields (none of the shipped sets has such duplicates in the range $80..$FF).
Examples: UTF-8 "Privet" to 866/1251/KOI8-R gives the byte strings of 3.5; to Latin-1 gives `??????` with Lost = 6; U+00E9 followed by `x` to Latin-1 gives E9 78; the euro sign to cp1252 gives byte 80.

### 3.7 UTF-16 details

Decoding (to UTF-8): units are read two bytes at a time in the given byte order; a trailing odd byte is ignored. A high surrogate (D800..DBFF) followed by a low surrogate (DC00..DFFF) forms one code point >= U+10000. A high surrogate not followed by a low one, and a lone low surrogate, give U+FFFD (the unit after an unmatched high surrogate is then processed on its own, not swallowed). A high surrogate that is the last unit gives U+FFFD. No byte order mark is interpreted or added: U+FEFF is treated as an ordinary character and appears in the output as EF BB BF; `utf-16` is simply little endian.
Encoding (from UTF-8): bytes below $80 are single units; valid sequences are decoded and written as one unit (BMP) or a surrogate pair (U+10000 and above); an invalid byte gives one unit U+FFFD and counts in Lost. Output byte order as requested. Examples: LE 'H' 00 'i' 00 -> "Hi"; BE 00 'H' 00 'i' -> "Hi"; LE 3D D8 00 DE <-> F0 9F 98 80 (U+1F600); UTF-8 "Privet" to UTF-16BE gives 04 1F 04 40 04 38 04 32 04 35 04 42.

### 3.8 Utf8Valid(S), IsPlainAscii(S)

Utf8Valid: True when S consists entirely of valid UTF-8: shortest forms only (C0, C1 never lead), no surrogates (ED A0..BF forbidden), nothing above U+10FFFF (F4 90.. and F5..FF forbidden), no truncated sequence, no stray continuation bytes. The empty string is valid. Examples: the UTF-8 "Privet" valid; the cp866 bytes of "Privet" not valid; "plain" valid; C0 80 not valid.
IsPlainAscii: True when no byte is >= $80 (the empty string is plain ASCII).

### 3.9 Cache and thread-safety

CharsetFromUtf8 for a table set builds a reverse table (code point -> byte, sorted) the first time it is called for that id and keeps only the one most recently used; calling it with another id rebuilds it. This is a single global cache with no locking: CharsetFromUtf8 must not be called from several threads at once. All other routines are pure and reentrant.

### 3.10 CharsetGuess(Raw, Candidates)

Chooses among the single-byte sets in Candidates the one that reads the bytes >= $80 of Raw as the most plausible text. Rules:
1. Empty Candidates: returns 1252.
2. The default result is Candidates[0]. If Raw is plain ASCII, that is the answer (Candidates are not even examined).
3. Only the first 1048576 bytes of Raw are examined.
4. For each candidate that is a table set (others are skipped), a score is the sum over the examined bytes >= $80 of the contribution of the Unicode value U of the byte in that set: U undefined: -50; U in U+2500..U+259F (box drawing, blocks, shades): -20; U in U+0080..U+009F (C1 controls): -50; otherwise +10 times the Russian letter weight of U (3.11) plus 3 if U is in U+00C0..U+1FFF and its weight is 0 (any other letter-like character is slightly positive). Values U+00A0..U+00BF and everything else above contribute 0 or the formula above (so punctuation and symbols are neutral).
5. The candidate with the strictly highest score wins; a tie goes to the earlier candidate. The comparison starts from -1, so a candidate whose score is negative never wins; if no candidate has a score >= 0 the result stays Candidates[0] (even if that id is not a known set).
Examples (tests): a Russian sentence ("Eto primer russkogo teksta", in Cyrillic) encoded in cp866 with candidates [1251, 866, KOI8-R] gives 866; the same in cp1251 with [866, 1251, KOI8-R] gives 1251; in KOI8-R with [866, 1251, KOI8-R] gives 20866; "plain text" with [1251, 866] gives 1251.

### 3.11 Russian letter weight

A private function mapping a code point to a small non-negative integer, the frequency of Russian letters in percent times 10: for the lower-case letters U+0430..U+044F and U+0451 the values (in order U+0430...U+044F) are 80 16 45 17 30 85 9 16 74 12 35 40 32 67 110 28 47 55 63 26 3 10 5 14 7 3 2 19 17 3 6 20 and U+0451 is 2; for the capital letters U+0410..U+042F the weight is half (integer division) that of the matching lower-case letter (code point + $20); U+0401 has weight 1; all other code points 0. Exact values are not pinned individually by tests; any realistic frequency table in which the vowels O, E, A, I and the consonants N, T, S rank highest, and which makes KOI8-R/866/1251 readings of the same sentence strictly ordered, satisfies the tests. The reference values above should be used where possible.

## 4. Data

### 4.1 The sets and their tables

Each single-byte set has one table indexed by byte value 0..255 whose entries are 16-bit Unicode values; the value $FFFF means "undefined". Entries 0..127 are the identity (ASCII) in every set. The tables are derived from the mapping data of the Python standard codecs of the same names (which follow the Unicode Consortium mapping files); undefined entries are those the Python codec leaves undefined. The ids, in list order (46):

437, 720, 737, 775, 850, 852, 855, 857, 858, 860, 861, 862, 863, 864, 865, 866, 869, 874, 1125, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 20866, 21866, 28591, 28592, 28593, 28594, 28595, 28596, 28597, 28598, 28599, 28600, 28601, 28603, 28604, 28605, 28606, 10000.

Standards behind them: IBM/OEM code pages 437, 720, 737, 775, 850, 852, 855, 857, 858, 860-866, 869, 874 (Thai), 1125 (Ukrainian variant of 866, known also as 866u; Python codec cp1125); Windows code pages 1250-1258; KOI8-R (RFC 1489) and KOI8-U (RFC 2319); ISO 8859-1..11, 13..16 (there is no 8859-12); Mac OS Roman (Python codec mac_roman). Notes:
* The table of 28591 is the identity on all 256 values (including U+0080..U+009F).
* The OEM tables map bytes 0x00..0x1F and 0x7F to the control characters themselves (identity), not to the IBM PC graphic symbols.
* Spot values (byte -> code point, hexadecimal): cp437 80 -> 00C7, 9B -> 00A2, B0 -> 2591, E0 -> 03B1, FF -> 00A0; cp850 9B -> 00F8, D5 -> 0131 (dotless i); cp858 D5 -> 20AC (euro); cp866 80 -> 0410, A0 -> 0430, E0 -> 0440, F0 -> 0401, FF -> 00A0; cp1125 F2 -> 0490, F4 -> 0404, F6 -> 0406, F8 -> 0407; cp1250 8A -> 0160; cp1251 80 -> 0402, A8 -> 0401, C0 -> 0410, E0 -> 0430, 98 undefined; cp1252 80 -> 20AC, 9F -> 0178, 81 undefined; cp1253 C1 -> 0391; cp874 A1 -> 0E01, E0 -> 0E40; KOI8-R A3 -> 0451, B3 -> 0401, C0 -> 044E, C1 -> 0430, E1 -> 0410, F0 -> 041F; KOI8-U A4 -> 0454, B4 -> 0404; ISO-8859-2 A1 -> 0104; ISO-8859-5 A1 -> 0401, B0 -> 0410, D0 -> 0430; ISO-8859-15 A4 -> 20AC; Mac Roman 80 -> 00C4, DB -> 20AC.
* Undefined bytes: cp857 D5, E7, F2; cp864 9B, 9C, 9F, A6, A7, FF; cp869 80-85, 87, 93, 94; cp1251 98; cp1252 81, 8D, 8F, 90, 9D; ISO-8859-3 A5, AE, BE, C3, D0, E3, F0. The sets 437, 720, 737, 775, 850, 852, 855, 858, 860-866, 1125, 1256, KOI8-R/U, 28591, 28592, 28594, 28595, 28599, 28600, 28603-28606 and Mac Roman have no undefined byte.
The implementer should generate the tables from the mapping files named above rather than type them. Undefined entries must match the Python codecs (the lists above are complete for the sets they name; sets not named there with undefined bytes, such as 874, 1250, 1253-1255, 1257, 1258, 28596-28598 and 28601, follow the same rule).

### 4.2 The name table

122 names, each mapping to an id, matched case-insensitively (the stored names are lower case, at most 16 characters). Per id, in this order (the first is what CharsetName returns):
* 437, 720, 737, 775, 850, 852, 855, 857, 858, 860, 861, 862, 863, 864, 865, 866, 869, 874: `cpN`, `ibmN`, `N` (N the decimal id).
* 1125: `cp1125`, `ibm1125`, `cp866u`, `1125`.
* 1250..1258: `windows-N`, `cpN`, `N`.
* 20866: `koi8-r`, `koi8r`. 21866: `koi8-u`, `koi8u`.
* 28591..28606 (except 28602): `iso-8859-n`, `iso8859-n` with n = id - 28590 (no leading zero).
* 10000: `macintosh`, `mac-roman`, `macroman`.

## 5. Dependencies

* TvUtf8 (implementation only): a validating UTF-8 decoder (given bytes and an available count, reports validity, the code point and the number of bytes used; rules as in TvUStr's `Utf8Decode`) and a UTF-8 encoder (code point to 1..4 bytes, returns the count; `Utf8Encode`).
* No other library units. Standard units: none required.

## 6. What the tests pin down (tests/t_charset.pas)

All examples in 3.1-3.10: ids by name (cp866, Windows-1251, KOI8-R, UTF-8, iso-8859-15, unknown); `CharsetName(1251) = 'windows-1251'`; known sets and 12345 unknown; `CharsetListCount > 40`; the "Privet" conversions in 866, 1251, KOI8-R both ways; Latin-1 `E9`; cp1252 euro both ways; undefined cp1251 byte 98 gives U+FFFD; ASCII unchanged; UTF-8 to UTF-8 unchanged; lost characters become `?` and are counted (6 for Cyrillic "Privet" into Latin-1); UTF-16 LE/BE both ways, including a surrogate pair; Utf8Valid and IsPlainAscii examples; four CharsetGuess cases. A good extra test program should also check: CharsetToUtf8 followed by CharsetFromUtf8 is the identity for every defined byte of every set in the list (Lost = 0); a lone surrogate in UTF-16 gives U+FFFD; an odd-length UTF-16 text drops the last byte; CharsetGuess with an empty candidate list is 1252; empty strings through every routine.

## 7. Observed oddities

* `ascii` and `us-ascii` map to Latin-1 (28591), not to a separate 7-bit set. Intended (it is a superset that never loses ASCII data); CharsetName(28591) never returns `ascii`.
* `utf-16` without a suffix means little endian. Intended.
* CharsetListId has no range check. Accidental; callers must not rely on any result out of range. An implementer may return 0 for out-of-range I.
* A valid U+FFFD in the text given to CharsetFromUtf8 is counted as lost like any unmappable character. Intended.
* CharsetGuess returns Candidates[0] when every candidate scores negative, even if that id is unknown; and the comparison start of -1 means a score of exactly -1 cannot win. Accidental but harmless; keep.
* The Russian weights are applied to every script, so the guess works for Cyrillic; for other scripts only the "letter-like value in U+00C0..U+1FFF" bonus (+3) and the penalties apply. This is the intended simple heuristic.
* The reverse-table cache is global and unsynchronised (3.9). Accidental; a thread-safe implementation is welcome but not required.
* The comment of the old unit says UTF-16 ids are for "units that need only a name or an id of them"; the conversions do accept them. Intended behaviour is the conversion described above.
