# Unit TvCStr

## 1. Purpose

TvCStr provides helpers for the texts of menus and controls in which a hot key is marked by the character `~`. At present it offers one routine: obtaining the text as the user sees it, without the marks.

## 2. Interface

```pascal
unit TvCStr;

interface

{ S without any '~' (the text as the user sees it): '~F~ile' gives 'File'. }
function StripTilde(const S: AnsiString): AnsiString;
```

## 3. Behaviour

**StripTilde(S).** Returns `S` with every occurrence of the character `~` (code 126) removed; all other bytes are kept in their original order. No pairing of marks is looked at: an unclosed mark, a lone mark, two marks in a row and any number of marks are all simply deleted (there is no escaping, `~~` does not yield a literal tilde). The text is treated as a byte string: bytes of `$80` and above (for example UTF-8 sequences) are copied unchanged, and since no byte of a multi-byte UTF-8 sequence equals 126, characters are never damaged. The empty string gives the empty string. There is no length limit (a 303-byte input works); no errors, no exceptions, no side effects, and the input is not modified. The function is re-entrant and thread safe. A ShortString may be passed and the result assigned back to a ShortString (the usual conversions apply; the result is cut by the language rules if it exceeds 255 characters, which cannot happen when it is the stripped form of a ShortString).

**Examples:**

| Input | Result |
|---|---|
| `~F~ile` | `File` |
| `Save ~a~s...` | `Save as...` |
| `plain` | `plain` |
| (empty) | (empty) |
| `~` | (empty) |
| `a~b` | `ab` |
| `a~~b` | `ab` |
| `x~y~z~w` | `xyzw` |
| bytes `$D0 $A4 ~ $D0 $B0 ~` | bytes `$D0 $A4 $D0 $B0` |
| 300 tildes followed by `end` | `end` |
| ShortString `~O~pen` passed and result stored in a ShortString | `Open` |

## 4. Dependencies

Library units: none. Standard units: none (system unit only).

## 5. Checks for a test program

- Every row of the table above.
- Result length equals input length minus the number of `~`.
- A text without `~` is returned equal to the input.
- A text consisting only of tildes gives the empty string.
- Bytes `$80..$FF` surrounding tildes are preserved exactly.
- The original variable passed is not changed.
