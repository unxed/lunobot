# Unit TvGlyphs

## 1. Purpose

TvGlyphs gives names to the frame, shade, block, triangle and arrow characters that text-mode user interfaces draw with. A glyph is identified by its Unicode code point (`glLightH` = U+2500), never by a code-page byte. The unit converts a glyph to the forms a program needs: a byte of the IBM PC character set (for 16-bit buffers, `Char` arguments, one-byte-per-column strings), a string (UTF-8 when the library runs in UTF-8 mode, else a code-page byte), a run of repeated glyphs, a screen cell. It also exports `Char` constants (`gc*`) with the PC-set byte of the most used glyphs for places where a function call is not allowed (typed constants, case labels). No state; thread-safe provided the global UTF-8 mode flag and the current code page are not changed concurrently.

## 2. Interface

```pascal
unit TvGlyphs;

interface

uses
  TvCell;

const
  { light lines }
  glLightH         = $2500;   { ─ }
  glLightV         = $2502;   { │ }
  glLightDR        = $250C;   { ┌ down and right }
  glLightDL        = $2510;   { ┐ }
  glLightUR        = $2514;   { └ }
  glLightUL        = $2518;   { ┘ }
  glLightVR        = $251C;   { ├ }
  glLightVL        = $2524;   { ┤ }
  glLightDH        = $252C;   { ┬ }
  glLightUH        = $2534;   { ┴ }
  glLightVH        = $253C;   { ┼ }
  { double lines }
  glDblH           = $2550;   { ═ }
  glDblV           = $2551;   { ║ }
  glDblDR          = $2554;   { ╔ }
  glDblDL          = $2557;   { ╗ }
  glDblUR          = $255A;   { ╚ }
  glDblUL          = $255D;   { ╝ }
  glDblVR          = $2560;   { ╠ }
  glDblVL          = $2563;   { ╣ }
  glDblDH          = $2566;   { ╦ }
  glDblUH          = $2569;   { ╩ }
  glDblVH          = $256C;   { ╬ }
  { a single and a double line meeting }
  glDownSglRightDbl = $2552;  { ╒ }
  glDownDblRightSgl = $2553;  { ╓ }
  glDownSglLeftDbl  = $2555;  { ╕ }
  glDownDblLeftSgl  = $2556;  { ╖ }
  glUpSglRightDbl   = $2558;  { ╘ }
  glUpDblRightSgl   = $2559;  { ╙ }
  glUpSglLeftDbl    = $255B;  { ╛ }
  glUpDblLeftSgl    = $255C;  { ╜ }
  glVertSglRightDbl = $255E;  { ╞ }
  glVertDblRightSgl = $255F;  { ╟ }
  glVertSglLeftDbl  = $2561;  { ╡ }
  glVertDblLeftSgl  = $2562;  { ╢ }
  glDownSglHorizDbl = $2564;  { ╤ }
  glDownDblHorizSgl = $2565;  { ╥ }
  glUpSglHorizDbl   = $2567;  { ╧ }
  glUpDblHorizSgl   = $2568;  { ╨ }
  glVertSglHorizDbl = $256A;  { ╪ }
  glVertDblHorizSgl = $256B;  { ╫ }
  { blocks and shades }
  glShadeLight     = $2591;   { ░ }
  glShadeMedium    = $2592;   { ▒ }
  glShadeDark      = $2593;   { ▓ }
  glBlockFull      = $2588;   { █ }
  glBlockLower     = $2584;   { ▄ lower half }
  glBlockUpper     = $2580;   { ▀ upper half }
  glBlockLeft      = $258C;   { ▌ left half }
  glBlockRight     = $2590;   { ▐ right half }
  glSquare         = $25A0;   { ■ }
  glDot            = $2219;   { ∙ }
  glMidDot         = $00B7;   { · }
  glTriUp          = $25B2;   { ▲ }
  glTriDown        = $25BC;   { ▼ }
  glTriRight       = $25BA;   { ► }
  glTriLeft        = $25C4;   { ◄ }
  glUpDown         = $2195;   { ↕ }
  glArrowUp        = $2191;   { ↑ }
  glArrowDown      = $2193;   { ↓ }
  glArrowRight     = $2192;   { → }
  glArrowLeft      = $2190;   { ← }
  glIdentical      = $2261;   { ≡ }
  glRadical        = $221A;   { √ }

const
  { the same glyphs as Char constants, for a typed constant or a case label, where a function call is not allowed (the bytes of the IBM PC set) }
  gcShadeLight  = #$B0;
  gcShadeMedium = #$B1;
  gcShadeDark   = #$B2;
  gcBlockFull   = #$DB;
  gcBlockLower  = #$DC;
  gcBlockUpper  = #$DF;
  gcBlockLeft   = #$DD;
  gcBlockRight  = #$DE;
  gcDot         = #$F9;
  gcMidDot      = #$FA;
  gcRadical     = #$FB;
  gcSquare      = #$FE;
  gcIdentical   = #$F0;
  gcLightH      = #$C4;
  gcLightV      = #$B3;
  gcLightDR     = #$DA;
  gcLightDL     = #$BF;
  gcLightUR     = #$C0;
  gcLightUL     = #$D9;
  gcLightVR     = #$C3;
  gcLightVL     = #$B4;
  gcLightDH     = #$C2;
  gcLightUH     = #$C1;
  gcLightVH     = #$C5;
  gcTriUp       = #$1E;
  gcTriDown     = #$1F;
  gcTriRight    = #$10;
  gcTriLeft     = #$11;

function GlyphByte(CodePoint: LongWord): Byte;
function GlyphChar(CodePoint: LongWord): Char;
function GlyphStr(CodePoint: LongWord): ShortString;
function GlyphRun(CodePoint: LongWord; Count: Integer): ShortString;
procedure SetCellGlyph(var Cell: TScreenCell; CodePoint: LongWord);
```

## 3. Behaviour

### 3.1 Glyph code-point constants (`gl*`)

The constants are plain integer constants (the values above are the contract) and are the arguments of all routines. Groups: light box lines (glLightH, V, and the four corners DR, DL, UR, UL, the T-pieces VR, VL, DH, UH and the cross VH), double lines (glDbl*, same eleven), eighteen single/double mixed joints (glDownSglRightDbl ... glVertDblHorizSgl), shades (glShadeLight/Medium/Dark), blocks (glBlockFull, Lower, Upper, Left, Right), glSquare, glDot (U+2219), glMidDot (U+00B7), four triangles, glUpDown, four arrows, glIdentical, glRadical. Naming rule for lines: D = down, U = up, L = left, R = right, V = vertical, H = horizontal; "Sgl"/"Dbl" tell which stroke is single or double.

### 3.2 PC-set table

The mapping between the glyph code points and positions in the IBM PC (CP437-style) character set is the following data. These bytes are the same in every DOS code page except the Arabic one, which the unit does not treat specially.

| Code point | Name | Byte |
|---|---|---|
| U+2591 | glShadeLight | $B0 |
| U+2592 | glShadeMedium | $B1 |
| U+2593 | glShadeDark | $B2 |
| U+2502 | glLightV | $B3 |
| U+2524 | glLightVL | $B4 |
| U+2561 | glVertSglLeftDbl | $B5 |
| U+2562 | glVertDblLeftSgl | $B6 |
| U+2556 | glDownDblLeftSgl | $B7 |
| U+2555 | glDownSglLeftDbl | $B8 |
| U+2563 | glDblVL | $B9 |
| U+2551 | glDblV | $BA |
| U+2557 | glDblDL | $BB |
| U+255D | glDblUL | $BC |
| U+255C | glUpDblLeftSgl | $BD |
| U+255B | glUpSglLeftDbl | $BE |
| U+2510 | glLightDL | $BF |
| U+2514 | glLightUR | $C0 |
| U+2534 | glLightUH | $C1 |
| U+252C | glLightDH | $C2 |
| U+251C | glLightVR | $C3 |
| U+2500 | glLightH | $C4 |
| U+253C | glLightVH | $C5 |
| U+255E | glVertSglRightDbl | $C6 |
| U+255F | glVertDblRightSgl | $C7 |
| U+255A | glDblUR | $C8 |
| U+2554 | glDblDR | $C9 |
| U+2569 | glDblUH | $CA |
| U+2566 | glDblDH | $CB |
| U+2560 | glDblVR | $CC |
| U+2550 | glDblH | $CD |
| U+256C | glDblVH | $CE |
| U+2567 | glUpSglHorizDbl | $CF |
| U+2568 | glUpDblHorizSgl | $D0 |
| U+2564 | glDownSglHorizDbl | $D1 |
| U+2565 | glDownDblHorizSgl | $D2 |
| U+2559 | glUpDblRightSgl | $D3 |
| U+2558 | glUpSglRightDbl | $D4 |
| U+2552 | glDownSglRightDbl | $D5 |
| U+2553 | glDownDblRightSgl | $D6 |
| U+256B | glVertDblHorizSgl | $D7 |
| U+256A | glVertSglHorizDbl | $D8 |
| U+2518 | glLightUL | $D9 |
| U+250C | glLightDR | $DA |
| U+2588 | glBlockFull | $DB |
| U+2584 | glBlockLower | $DC |
| U+258C | glBlockLeft | $DD |
| U+2590 | glBlockRight | $DE |
| U+2580 | glBlockUpper | $DF |
| U+25A0 | glSquare | $FE |
| U+2219 | glDot | $F9 |
| U+221A | glRadical | $FB |
| U+00B7 | glMidDot | $FA |
| U+25B2 | glTriUp | $1E |
| U+25BC | glTriDown | $1F |
| U+25BA | glTriRight | $10 |
| U+25C4 | glTriLeft | $11 |
| U+2195 | glUpDown | $12 |
| U+2191 | glArrowUp | $18 |
| U+2193 | glArrowDown | $19 |
| U+2192 | glArrowRight | $1A |
| U+2190 | glArrowLeft | $1B |
| U+2261 | glIdentical | $F0 |

(The first 48 rows are the box/shade/block positions B0..DF in order; the last 14 rows are the additional glyphs.) Only the code points in this table are glyphs of the unit.

### 3.3 Constants gc*

Each `gc*` Char constant equals the byte of the table row of the glyph with the corresponding name: gcShadeLight = B0, gcShadeMedium = B1, gcShadeDark = B2, gcBlockFull = DB, gcBlockLower = DC, gcBlockUpper = DF, gcBlockLeft = DD, gcBlockRight = DE, gcDot = F9, gcMidDot = FA, gcRadical = FB, gcSquare = FE, gcIdentical = F0, gcLightH = C4, gcLightV = B3, gcLightDR = DA, gcLightDL = BF, gcLightUR = C0, gcLightUL = D9, gcLightVR = C3, gcLightVL = B4, gcLightDH = C2, gcLightUH = C1, gcLightVH = C5, gcTriUp = 1E, gcTriDown = 1F, gcTriRight = 10, gcTriLeft = 11. For every `gc*` constant, `GlyphChar` of the glyph with the same name gives that constant when the current code page is a DOS page (see 3.4). There are no gc constants for the double, mixed, arrow or up-down glyphs.

### 3.4 GlyphByte(CodePoint)

Result is a byte, resolved in this order:
1. Ask the current code page for the byte of this code point (TvCodePg `CpFromUnicode`; 0 when the page lacks the character). If that byte is non-zero, is not an ASCII-range byte (it is below $20 or at least $7F), and the code point itself is above $7F, return it. (A code page that has the frame or other character at some position wins over the table.)
2. Otherwise return the table byte of 3.2 for the code point.
3. Otherwise 0.

So on a DOS code page (such as 437 or 866) the result is the table value for every glyph. With an ASCII code point (at most $7F), such as `Ord('a')`, the result is 0. Caveat: for a non-glyph character that the current page does have as a byte of $80 or above (for example Cyrillic Zhe on cp866 gives $86), step 1 returns that page byte, so the result of "0 for non-glyphs" is only guaranteed for characters that the page lacks and for ASCII. Likewise a code point in the table that a non-DOS page maps to some other high byte (for instance U+00B7 on a Latin page that has it at $B7) yields the page byte, not the table byte; test the table values with a DOS page selected (the default).

Examples (DOS page): GlyphByte(glLightH) = $C4; glLightV = $B3; glDblH = $CD; glDblDR = $C9; glDblUL = $BC; glVertDblRightSgl = $C7; glDownSglRightDbl = $D5; glUpDblHorizSgl = $D0; glVertSglHorizDbl = $D8; glShadeMedium = $B1; glBlockFull = $DB; glSquare = $FE; glDot = $F9; glMidDot = $FA; glRadical = $FB; glTriUp/Down/Right/Left = $1E/$1F/$10/$11; GlyphByte(Ord('a')) = 0.

### 3.5 GlyphChar(CodePoint)

`Chr(GlyphByte(CodePoint))`: the glyph as one Char of a one-byte-per-column string. Not a glyph: `#0`. Example: GlyphChar(glLightH) = #$C4 (not equal to gcShadeLight); GlyphChar(glShadeLight) = gcShadeLight, glShadeMedium = gcShadeMedium, glShadeDark = gcShadeDark, glBlockFull = gcBlockFull, glDot = gcDot, glMidDot = gcMidDot, glRadical = gcRadical, glSquare = gcSquare.

### 3.6 GlyphStr(CodePoint)

If UTF-8 mode is off (`Utf8Enabled` of TvUtf8 is False): the one-character string `GlyphChar(CodePoint)` (so a non-glyph, even ASCII, gives `#0`). If UTF-8 mode is on: the UTF-8 encoding of the code point (1 to 4 bytes; the empty string if the encoder rejects the value). Examples: UTF-8 on: GlyphStr(glLightH) = #$E2#$94#$80; off: #$C4.

### 3.7 GlyphRun(CodePoint, Count)

`Count` copies of `GlyphStr(CodePoint)` concatenated, in a ShortString. `Count <= 0` gives `''`. Copies are appended whole and appending stops before the result would exceed 255 bytes (so with 3-byte glyphs at most 85 copies). Examples: UTF-8 on: GlyphRun(glLightH,3) = #$E2#$94#$80#$E2#$94#$80#$E2#$94#$80; off: #$C4#$C4#$C4; Count 0: ''.

### 3.8 SetCellGlyph(Cell, CodePoint)

Replaces the character of a screen cell (`TScreenCell.Character`, TvCell) by the UTF-8 encoding of the code point, whatever the UTF-8 mode, as an ordinary (not wide) character, replacing any previous text of the cell completely (no leftover bytes of a longer previous text). The attribute of the cell and all other cells are untouched. Examples: after SetCellGlyph(c, glDblH) the cell text is the three bytes E2 95 90; after a further SetCellGlyph(c, glLightH) it is exactly E2 94 80.

## 4. Dependencies

* TvCell: `TScreenCell` with a field `Character` that offers `InitWithMultiByteChar(Bytes: pointer; Len: Integer; Wide: Boolean)` (the unit passes False for the last argument) and `GetText` (the text of the cell as a string); a field `Attribute` that is not touched.
* TvUtf8 (implementation): `Utf8Enabled: Boolean`, `Utf8Encode(CodePoint, Buffer): Integer` (number of bytes written), and `MaxCharSize` (largest UTF-8 sequence length).
* TvCodePg (implementation): `CpFromUnicode(CodePoint: LongWord): Byte`.
* Standard: none beyond the system unit.
* Not part of this unit but described in its header and used by its test: `TDrawBuffer.MoveGlyph` and `TDrawBuffer.PutGlyph` of TvDrawBuf, which draw glyphs into a draw buffer using the cell rule of 3.8; this specification does not cover them.

## 5. Checks for a test program

1. GlyphByte values of every example in 3.4, and the whole table of 3.2 (62 rows) with a DOS page selected; no two rows share a code point.
2. GlyphChar equals each `gc*` constant for the glyph of the same name (all 28 constants).
3. GlyphByte of ASCII `a` is 0; of a code point that is not in the table (for example U+2603) on a DOS page is 0.
4. GlyphStr and GlyphRun in both UTF-8 modes (restore the flag afterwards); GlyphRun with Count 0, with a large Count (length never above 255, multiple of the glyph length).
5. SetCellGlyph on zero-filled cells: bytes E2 95 90 for U+2550 in three cells and the fourth cell untouched; overwriting a cell with a different glyph leaves exactly the new three bytes; the attribute of a cell is preserved.
6. A 1-byte glyph in a cell: SetCellGlyph with glMidDot gives the two bytes C2 B7.
