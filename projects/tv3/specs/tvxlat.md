# Unit TvXlat - functional specification

## 1. Purpose

TvXlat makes keyboard shortcuts independent of the keyboard layout. A terminal reports a key typed on a non-Latin layout as a letter of another script (for example Alt plus a Cyrillic letter). TvXlat knows, for a number of layouts, which Latin key sits at the same physical place, and rewrites a key event so that Alt+(Cyrillic letter) becomes the Alt+(Latin letter) shortcut of the same key, and so that a plain non-Latin letter can be looked up as its Latin counterpart among hot keys (menus, button labels).

Typing is not touched by this unit: a view that takes a letter as text takes it before these routines are used. The unit keeps a private global map from code point to the Latin code point; it is filled lazily with built-in layouts and can be extended at run time. It is not thread-safe (global map, lazy initialisation); use it from the input thread only.

Terms: the **Latin keys** are the 34 positions, in this order: `q w e r t y u i o p [ ] a s d f g h j k l ; ' z x c v b n m , . ` \` (the string `qwertyuiop[]asdfghjkl;'zxcvbnm,.` followed by a backquote and a backslash). A **layout string** lists the characters a layout has on those keys, in the same order.

## 2. Interface

```pascal
unit TvXlat;

interface

uses
  TvEvents;

function XlatLatin(CodePoint: LongWord): LongWord;
procedure XlatAdd(const Letters: AnsiString);
function XlatLoadFile(const Name: AnsiString): Boolean;
function XlatModded(var Event: TEvent): Boolean;
function XlatPlain(var Event: TEvent): Boolean;

var
  XlatEnabled: Boolean = True;
```

No other public identifiers.

## 3. Behaviour

### 3.1 The map and the layouts

The map holds pairs (From, To): From is a code point of a layout character, To the code point of the Latin key character (lower-case a..z, or one of the punctuation key characters; or upper-case A..Z for entries that came from an upper-case half, see 3.3). For each From there is at most one entry.

A layout string is read as UTF-8 into code points (a byte that does not start a valid UTF-8 sequence counts as the code point of that byte value, one per byte). At most 128 characters are used. The character at position I is paired with the Latin key at position I (positions beyond the 34 keys are ignored). A pair is skipped when the layout character is a blank or control (code point <= 32) or equals the Latin key character itself. So a blank in a layout string means "this key has no character in this layout". Pairs with an ASCII From are legal and stored but are never found by XlatLatin (3.4).

When a pair is added for a From that already exists: during the loading of the built-in layouts the old entry is kept (the first layout that has the character wins); for layouts added by the program afterwards the new pair replaces the old one (the last added wins). See "Observed oddities" for the intended rule.

### 3.2 Built-in layouts

Loaded on first need (first call of XlatLatin, XlatModded, XlatPlain or XlatLoadFile) in this order, first wins (all strings are given by code points; each lists the keys q w e r t y u i o p [ ] / a s d f g h j k l ; ' / z x c v b n m , . in that order; a "lower|upper" form gives the lower-case characters and then, after the bar, the upper-case ones, which are paired with the upper-case Latin keys):
1. Russian (standard JCUKEN), lower case only: U+0439 U+0446 U+0443 U+043A U+0435 U+043D U+0433 U+0448 U+0449 U+0437 U+0445 U+044A / U+0444 U+044B U+0432 U+0430 U+043F U+0440 U+043E U+043B U+0434 U+0436 U+044D / U+044F U+0447 U+0441 U+043C U+0438 U+0442 U+044C U+0431 U+044E.
2. Ukrainian, lower case only: as Russian except U+044A (key `]`) is U+0457, U+044B (key s) is U+0456, U+044D (key `'`) is U+0454.
3. Russian with upper case (the capital letters U+0419 U+0426 ... U+042E on the same keys; Latin side upper case).
4. Ukrainian with upper case.
5. Serbian Cyrillic with both cases: adds the letters U+0459 (key q), U+045A (key w), U+0452, U+0458, U+045B, U+045F and their capitals U+0409, U+040A, U+0402, U+0408, U+040B, U+040F; characters already mapped by an earlier layout keep their key. Only the Serbian-only letters matter; their exact keys are not pinned by tests (use the standard Serbian Cyrillic layout; U+0459 on q and U+045A on w are the certain ones).
6. Belarusian (adds only U+045E) and 7. Bulgarian (both cases; adds nothing beyond layouts 1-4). Not pinned by tests; may be omitted or corrected (see oddities).
8. Greek (lower case only, standard ELOT 747 layout): key q is a semicolon (ASCII, inert), then w U+03C2, e U+03B5, r U+03C1, t U+03C4, y U+03C5, u U+03B8, i U+03B9, o U+03BF, p U+03C0; a U+03B1, s U+03C3, d U+03B4, f U+03C6, g U+03B3, h U+03B7, j U+03BE, k U+03BA, l U+03BB; z U+03B6, x U+03C7, c U+03C8, v U+03C9, b U+03B2, n U+03BD, m U+03BC. (The old unit's string is misaligned in its bottom key row; see oddities. Only U+03B1 -> a is pinned.)
9. Hebrew (standard 101-key layout; ASCII slash and apostrophe on q and w are inert): e U+05E7, r U+05E8, t U+05D0, y U+05D8, u U+05D5, i U+05DF, o U+05DD, p U+05E4; a U+05E9, s U+05D3, d U+05D2, f U+05DB, g U+05E2, h U+05D9, j U+05D7, k U+05DC, l U+05DA, semicolon U+05E3; z U+05D6, x U+05E1, c U+05D1, v U+05D4, b U+05E0, n U+05DE, m U+05E6, comma U+05EA, period U+05E5.
After the built-ins are loaded, "later wins" mode is switched on for everything added later.
Only the Russian, Ukrainian and Greek mappings are pinned by tests (3.8); the rest should follow the standard layout of the language named.

### 3.3 XlatAdd(Letters)

Adds a layout. If Letters contains `|`, the text before the first bar is a layout string paired with the Latin keys (lower case) and the text after it is a layout string paired with the Latin keys converted to upper case (letters A..Z; punctuation keys unchanged). Without a bar the whole string is paired with the Latin keys as they are. Pair rules as in 3.1. No error is reported for odd input. Examples: `XlatAdd('ABC')` adds pairs that are never used, since XlatLatin never maps ASCII (test). Calling XlatAdd does not by itself load the built-in layouts (see oddities); the intended behaviour is that built-ins are loaded first and that added layouts override them, last added wins.

### 3.4 XlatLatin(CodePoint)

Returns the Latin code point for the key where some layout has CodePoint, or 0 when none does. Code points below 128 always give 0 (a Latin character is itself and needs no translation). Otherwise: loads the built-ins if needed; returns the To of the entry whose From is CodePoint, if there is one; otherwise, for a capital letter of a layout that supplied lower-case letters only, tries the lower-case letter: for U+0410..U+042F the letter at +$20, for U+0400..U+040F the letter at +$50, for U+0391..U+03A9 the letter at +$20, and returns the To of that lower-case entry (so the result is lower-case); otherwise 0. The result for entries of a both-case layout is the upper-case Latin letter for a capital (U+0419 gives `Q`). XlatEnabled is NOT consulted here. Examples (tests): U+0444 -> `a`; U+044B -> `s`; U+0419 -> `Q`; U+0456 -> `s`; U+0457 -> `]`; U+03B1 -> `a`; `a` -> 0.

### 3.5 XlatLoadFile(Name)

Reads a text file of layout definitions and adds them (after loading the built-ins). Returns False, without side effects, when the file cannot be opened; True otherwise, even if no line was usable. Each line: everything from the first `#` to the end of the line is a comment; the rest is split at the first `=`; a line without `=`, or with `=` as its first character, is ignored. The text left of `=` is a layout string and the text right of `=` the Latin key characters to pair with, each trimmed of leading and trailing white space; pairs are formed as in 3.1 (position by position, the right side taking the place of the Latin keys; it can name any characters, not just the standard Latin keys). Because trimming removes leading blanks, a layout cannot start with a blank in a file; the `|` two-case form of XlatAdd is NOT recognised in files (a bar would be a layout character; to give both cases use two lines). A `#` cannot be used as a key character in a file. Added pairs follow the later-wins rule of 3.1.

### 3.6 XlatModded(Event)

Changes a Ctrl or Alt key combination typed on a non-Latin layout. Returns True and modifies Event only when all of the following hold, otherwise returns False and leaves Event untouched: XlatEnabled is True; Event.What is evKeyDown; the control key state has at least one of the Ctrl bits or Alt bits (the masks kbCtrlShift and kbAltShift of TvKeys; left and right variants both count); the event carries text (TextLength > 0) whose first UTF-8 character is valid and has code point >= 128; XlatLatin of that character is, after folding A..Z to a..z, a letter a..z; and ModdedKeyCode (TvTermIO) yields a non-zero code for the Latin letter with the wanted modifier. The modifier chosen is Alt if any Alt bit is set (even together with Ctrl), otherwise Ctrl. Effect: KeyDown.KeyCode is set to the key code of Alt+letter or Ctrl+letter for the Latin letter (kbAltS for Alt+U+044B; kbCtrlR for Ctrl+U+043A), and TextLength is set to 0 (the event is a shortcut, not text). Shift state does not matter; the control key state itself is left as it was. A character that maps to a punctuation key (for example U+0457 -> `]`) is not translated by this routine.

### 3.7 XlatPlain(Event)

For places that look for a letter among hot keys. Returns True and modifies Event only when: XlatEnabled is True; Event.What is evKeyDown; the control key state has neither a Ctrl nor an Alt bit; the event text begins with a valid UTF-8 character of code point >= 128; and XlatLatin of it is non-zero. Effect: Text[0] is set to the Latin character, TextLength to 1 and KeyDown.CharScan.CharCode to the same value. Case is that of the XlatLatin result (upper case for a capital of a both-case layout, lower case otherwise; punctuation keys give the punctuation character). Otherwise False, event unchanged.

### 3.8 What the tests pin (tests/t_xlat.pas)

Events are built by clearing an event, setting What = evKeyDown, the control key state, and the UTF-8 of one code point as Text. Pinned: the six XlatLatin values of 3.4; Alt (kbLeftAlt) plus U+044B -> XlatModded True and KeyCode = kbAltS; Ctrl (kbLeftCtrl) plus U+043A -> kbCtrlR; a plain U+043A: XlatModded False, XlatPlain True with TextLength 1 and Text[0] = `r`; Alt plus U+044B: XlatPlain False; XlatAdd('ABC') leaves XlatLatin('A') = 0; with XlatEnabled False, XlatModded is False. Additional checks recommended: LoadFile with a missing file returns False; a file `layout = keys` with a comment and a bad line; XlatModded with Ctrl+Alt picks Alt; a Latin letter with Alt returns False; an event with no text returns False.

## 4. Dependencies

* TvEvents: the TEvent record (What, KeyDown with KeyCode, CharScan.CharCode, ControlKeyState, Text bytes, TextLength) and evKeyDown.
* TvKeys: kbCtrlShift, kbAltShift (control key state masks) and, for the tests, kbAltS, kbCtrlR, kbLeftAlt, kbLeftCtrl.
* TvUtf8: a validating UTF-8 decoder (bytes, count -> code point and byte count, False if invalid) and an encoder (for tests).
* TvTermIO: ModdedKeyCode(KeyCode, Largest): for an upper-case letter code A..Z returns the Ctrl key code (Largest = 1) or Alt key code (Largest = 2) of that letter, 0 when there is none.
* SysUtils: Trim, UpperCase.

## 5. Observed oddities

* Built-in layouts are not loaded by XlatAdd. If a program calls XlatAdd before any other routine, its pairs are stored with "first wins" semantics and built-ins come after them; if it calls after, the pairs replace earlier ones. Accidental. Intended: user layouts always override built-ins, and among user layouts the last added wins; XlatAdd must load built-ins first.
* XlatLatin contains a leftover empty loop (no effect). Remove.
* The Belarusian layout string is shifted by one position in the second key row (it has an extra apostrophe in the bracket row), so most of its pairs fall on the wrong keys; because nearly all its letters are already mapped by the Russian layout (first wins) it only contributes U+045E. Bulgarian adds nothing new. Accidental; the implementer may drop or correct these two layouts; no test depends on them.
* The Serbian layout string is shorter than 32 keys and its lower rows are shifted by one position (for example a letter meant for key z falls on the key before); this only affects the Serbian-only letters. Accidental; intended is the standard Serbian Cyrillic layout.
* The Greek layout string has an accent mark (U+0384) at the semicolon key and no entry for the apostrophe key, so its letters of the bottom row (z..m) fall one key to the right (zeta on the apostrophe key, chi on z, and so on). Accidental; intended is the standard layout listed in 3.2. Only U+03B1 is pinned.
* Greek capital letters and Cyrillic capitals of lower-case-only layouts translate to the lower-case Latin letter (case is lost) in XlatPlain and are folded anyway in XlatModded. Accepted behaviour.
* XlatLatin ignores XlatEnabled; only XlatModded and XlatPlain obey it. Intended.
* A layout defined in a file cannot use the two-case `|` form. Accepted.
* ASCII-valued layout characters (semicolon, brackets, comma, apostrophe in the Greek, Hebrew and Belarusian strings) create unused entries mapping an ASCII character to another key (for example an apostrophe to a bracket key). They have no effect because XlatLatin never maps code points below 128. Intended to stay inert.
