# Unit TvWordNav

## 1. Purpose

TvWordNav computes the word boundaries for Ctrl+Left and Ctrl+Right (and the "fine" variants Ctrl+Shift+Left/Right) in a single-line input field. The rules use three character classes (space, divider, word) and a stop condition that looks at the pair of characters around the new cursor position. A position is the number of bytes before the cursor, from 0 to the length of the text. The text is a byte string: every byte of `$80` and above is a word character, so stops always fall between ASCII bytes and a multi-byte character is never split by a stop that is inside a word (taking at least one whole character as a step is the job of the caller).

## 2. Interface

```pascal
unit TvWordNav;

interface

const
  wnSpace = 0;
  wnDivider = 1;
  wnWord = 2;

var
  { Ctrl+Left and Ctrl+Right in input fields follow these rules; False: the classic jump over blanks only }
  UxWordNav: Boolean = True;
  { the word dividers (a space and a tab are not among them) }
  WordDividers: ShortString = '~!%^&*()+|{}:"<>?`-=\[];'',./';

function WordClassOf(Ch: Char): Integer;

{ The position after Ctrl+Right (Fine = False) or Ctrl+Shift+Right in an input field (Fine = True), starting at Pos; it moves at least one byte. }
function WordNavRight(const S: ShortString; Pos: Integer; Fine: Boolean = False): Integer;

{ The same to the left. }
function WordNavLeft(const S: ShortString; Pos: Integer; Fine: Boolean = False): Integer;
```

## 3. Behaviour

**Constants wnSpace, wnDivider, wnWord.** The values 0, 1, 2 of the class returned by `WordClassOf`.

**WordDividers.** The initial value is the 28 characters `~ ! % ^ & * ( ) + | { } : " < > ? ` - = \ [ ] ; ' , . /` (the apostrophe is included, the quote is included; space, tab, `_`, `$`, `#`, `@` are not). It may be changed by the program at run time and `WordClassOf` uses the current content.

**UxWordNav.** A switch for the callers (initially True): True means the rules of this unit are to be used, False means the caller should use the classic jump over blanks. The three routines of this unit do not read the switch; they always apply the rules below.

**WordClassOf(Ch).** Returns `wnSpace` for a space (code 32) and a tab (code 9). Otherwise, for a character with code below 128 that occurs in `WordDividers`, returns `wnDivider`. Everything else (letters, digits, `_ $ # @`, control characters other than tab, bytes of `$80` and above) gives `wnWord`.

**Stop rule.** Let the candidate position be `Q`; the "previous" character is the byte before the position (index `Q`, 1-based) and the "current" one is the byte at the position (index `Q+1`); their classes are `Prev` and `Curr`.

*Right, coarse (Fine = False):* a candidate stops if `Q` is at or past the end of the text, or if (`Prev` = space and `Curr` is not space) or (`Prev` = word and `Curr` = divider).

*Right, fine (Fine = True):* a candidate stops at the end of the text, or if not (`Prev` = word and `Curr` = word) and `Curr` is not space. (Stops everywhere except inside a word and before a space.)

*Left, coarse:* a candidate stops if `Q` is 0 or less, or if (`Prev` = space and `Curr` is not space) or (`Prev` = divider and `Curr` = word).

*Left, fine:* a candidate stops at 0, or if not (`Prev` = word and `Curr` = word), and `Curr` is not space, and not (`Prev` = word and `Curr` = divider). (Everywhere except inside a word, before a space, and on a divider that follows a word character.)

**WordNavRight(S, Pos, Fine).** If `Pos` is already at or beyond `Length(S)`, returns `Length(S)`. Otherwise the candidate starts at `Pos+1` and increases by one until the right stop rule holds; the first such candidate is returned. The result is therefore always greater than `Pos` (moves at least one byte) and never greater than `Length(S)`.

**WordNavLeft(S, Pos, Fine).** If `Pos` is 0 or negative, returns 0. Otherwise the candidate starts at `Pos-1` and decreases by one until the left stop rule holds; the first is returned. The result is less than `Pos` and not below 0. 

Both routines are pure (no state changed, thread safe, no exceptions). `Pos` is expected within 0..Length(S); a `Pos` beyond the length on the right returns the length; on the left a `Pos` larger than the length is not a supported input.

**Worked examples (positions visited by repeated calls, from 0 to the right or from the end to the left):**

| Text | Direction, Fine | Positions visited |
|---|---|---|
| `foo.bar` | right, no | 3, 7 |
| `foo.bar` | left, no | 4, 0 |
| `...///` | right, no | 6 |
| `foo bar baz` | right, no | 4, 8, 11 |
| `foo bar baz` | left, no | 8, 4, 0 |
| `a.-/b` | right, no | 1, 5 |
| `a.-/b` | right, yes | 1, 2, 3, 4, 5 |
| `foo bar` | right, yes | 4, 7 |
| `foo bar` | left, yes | 4, 0 |
| `a.-/b` | left, yes | 4, 3, 2, 0 |

Single calls: `WordNavRight('abc',3)=3`; `WordNavLeft('abc',0)=0`; `WordNavRight('',0)=0`. Classes: `WordClassOf(' ')=wnSpace`, `'.'` is wnDivider, `_ $ # @` are wnWord, byte `$D0` is wnWord.

## 4. Dependencies

Library units: none. Standard units: none beyond the system unit.

## 5. Checks for a test program

- Every row of the table above (a helper that repeats calls until the end/start is reached).
- The single-call and class checks above; additionally `WordClassOf(#9) = wnSpace`, and every character of the default `WordDividers` is a divider.
- Changing `WordDividers` (for example to `'_'`) changes the class of `_` and `.` accordingly; restore it afterwards.
- Right never returns a value `<= Pos` unless `Pos >= Length`; left never returns `>= Pos` unless `Pos <= 0`; results are always within 0..Length(S).
- Termination for random strings: repeated moves from 0 reach `Length(S)`, and from the end reach 0.
- A text of only spaces: coarse right from 0 gives its length (no token starts); fine right also gives the length.
- Non-ASCII bytes: in `#$D0#$A4 'x'` no coarse stop falls between the bytes `$D0` and `$A4`.
