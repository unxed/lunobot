# Unit TvAscii - functional specification

## 1. Purpose

TvAscii is a table-of-characters window ("ASCII table") for the view library. It consists of a table view (TAsciiTable) showing 256 codes in 8 rows of 32 cells with a movable cursor, a report line (TAsciiReport) under it showing the current character and its code in decimal and hexadecimal (or as U+XXXX), and a framed window (TAsciiChart) that holds both. The user moves the cursor with keys or the mouse and can "pick" a code (Enter, a double click, or typing the character), which notifies the owner and an optional callback.

Two modes: **code page mode** (default): codes are bytes 0..255, drawn through the code page of the screen (the cell holds one raw byte; the screen layer shows it through TvCodePg). **Unicode mode** (`Unicode = True`): the table shows one block of 256 code points; `Block * 256 .. Block * 256 + 255`; Ctrl+PgUp / Ctrl+PgDn change the block.

A program can supply its own cell text (own glyphs or own code page) through the `CharText` hook, and its own keys through virtual methods. The views are streamable. No global state apart from the variables listed in 2; not thread-safe (views belong to the UI thread).

## 2. Interface

```pascal
unit TvAscii;

interface

uses
  TvGeom, TvColors, TvEvents, TvKeys, TvDrawBuf, TvObjs, TvViews, TvWindow;

const
  AsciiCols = 32;
  AsciiRows = 8;
  AsciiCells = AsciiCols * AsciiRows;          { 256 }
  AsciiMaxBlock = $10FFFF div AsciiCells;      { 4351 = $10FF }

  { offsets from AsciiCommandBase }
  acFocused = 0;
  acPicked = 1;

type
  TAsciiTable = class;

  TAsciiCharText = function(Code: LongInt): AnsiString;
  TAsciiPickEvent = procedure(Sender: TAsciiTable; Code: LongInt) of object;

  TAsciiKey = (akNone, akLeft, akRight, akUp, akDown, akRowStart, akRowEnd, akColTop, akColBottom, akFirst, akLast,
    akUp2, akDown2, akLeft5, akRight5, akPrevBlock, akNextBlock, akPick);

  TAsciiTable = class(TView)
    Unicode: Boolean;
    Block: LongInt;
    TypePicks: Boolean;
    MarkCursor: Boolean;
    CharText: TAsciiCharText;
    OnPick: TAsciiPickEvent;
    constructor Create(const Bounds: TRect);
    class function Build: TStreamable; static;
  protected
    constructor Create(AInit: TStreamableInit); overload;
    function StreamableName: ShortString; override;
    function Read(Ip: ipstream): Pointer; override;
    procedure Write(Os: opstream); override;
  public
    function GetPalette: TPalette; override;
    procedure Draw; override;
    procedure HandleEvent(var Event: TEvent); override;
    function KeyAction(var Event: TEvent): TAsciiKey; virtual;
    function TypedCode(var Event: TEvent): LongInt; virtual;
    function Code: LongInt;
    procedure SetCode(ACode: LongInt);
    function CellText(ACode: LongInt): AnsiString;
    procedure Pick; virtual;
    procedure Focused; virtual;
    function DataSize: Integer; override;
    procedure GetData(var Rec); override;
    procedure SetData(var Rec); override;
  end;

  TAsciiReport = class(TView)
    Code: LongInt;
    Unicode: Boolean;
    CharStr: AnsiString;
    constructor Create(const Bounds: TRect);
    class function Build: TStreamable; static;
  protected
    constructor Create(AInit: TStreamableInit); overload;
    function StreamableName: ShortString; override;
    function Read(Ip: ipstream): Pointer; override;
    procedure Write(Os: opstream); override;
  public
    function GetPalette: TPalette; override;
    procedure Draw; override;
    procedure HandleEvent(var Event: TEvent); override;
    procedure ReportParts(out Prefix, Rest: AnsiString); virtual;
    procedure ShowCode(Table: TAsciiTable);
  end;

  TAsciiChart = class(TWindow)
    Table: TAsciiTable;
    Report: TAsciiReport;
    constructor Create(const ATitle: ShortString = 'ASCII Table'; AUnicode: Boolean = False);
    class function Build: TStreamable; static;
  protected
    constructor Create(AInit: TStreamableInit); overload;
    function StreamableName: ShortString; override;
    function Read(Ip: ipstream): Pointer; override;
    procedure Write(Os: opstream); override;
  public
    function MakeTable(const Bounds: TRect): TAsciiTable; virtual;
    function MakeReport(const Bounds: TRect): TAsciiReport; virtual;
  end;

function AsciiCodePageText(Code: LongInt): AnsiString;
function AsciiUnicodeText(Code: LongInt): AnsiString;

var
  AsciiCommandBase: Word = 910;
  AsciiPalette: ShortString = #6#7;
  AsciiCharText: TAsciiCharText = nil;
  RAsciiTable, RAsciiReport, RAsciiChart: TStreamableClass;
```

The view classes follow the conventions of the library's TView/TWindow hierarchy (the same as the Turbo Vision ones); the protected `Create(AInit)` overloads, `Build`, `StreamableName`, `Read`, `Write` are the streaming support. The declaration order and visibility above should be kept; the compiler warning about a "non-public constructor" is switched off in the unit.

## 3. Behaviour

### 3.1 Text hooks

* `AsciiCodePageText(Code)`: a one-byte string holding `Code and $FF`. The byte is later shown through the screen's code page.
* `AsciiUnicodeText(Code)`: for Code < 32 or Code = 127: the one-byte string holding that control code (the screen shows it as the IBM PC glyph of the code page). For Code in $80..$9F, in the surrogate range $D800..$DFFF, above $10FFFF, or whose display width (`CharWidth` of TvUtf8) is not 1 (wide, combining, zero-width, unprintable): a single space. Otherwise the UTF-8 encoding of the code point. Negative Code is outside the contract. Tests: `$E9` -> C3 A9; `$85` -> space; `$4E00` -> space; `1` -> #1.
* `CharText` hook: `function(Code): AnsiString`. It must return either one byte (shown through the code page) or the UTF-8 of one character of display width 1. `AsciiCharText` (global) is the default hook copied into each new table and read back after loading from a stream; nil means: `AsciiUnicodeText` in Unicode mode, `AsciiCodePageText` otherwise.

### 3.2 TAsciiTable

**Construction** `Create(Bounds)`: view options get `ofSelectable`; the event mask gets `evMouseMove`; `TypePicks := True`, `MarkCursor := True`, `CharText := AsciiCharText`; Unicode False, Block 0; the cursor is made a block cursor and shown. Palette: the string `AsciiPalette` (default #6#7: two entries mapping to entries 6 and 7 of the owner's palette): entry 1 = the characters, entry 2 = the cell under the cursor.

**Cursor and code.** The cursor position (Cursor.X in 0..31, Cursor.Y in 0..7) is the view's hardware cursor. `Code` = `Block * 256 + Cursor.Y * 32 + Cursor.X`, and `and $FF` in code page mode. `CellText(ACode)`: the text of a cell: the `CharText` hook if assigned, else `AsciiUnicodeText` when Unicode, else `AsciiCodePageText`.

**SetCode(ACode)**: negative values become 0. Unicode: values above $10FFFF become $10FFFF; Block := ACode div 256. Code page mode: ACode := ACode and $FF (Block is untouched). The cursor goes to column (ACode mod 256) mod 32, row (ACode mod 256) div 32; the view is redrawn; `Focused` is called (even when nothing moved).

**Focused**: when the table has an owner, broadcasts (`evBroadcast`) to the owner the command `AsciiCommandBase + acFocused` with InfoPtr = the table. **Pick**: reads `Code`; calls `OnPick(Self, Code)` if assigned; then, if an owner exists, sends it an `evCommand` event with command `AsciiCommandBase + acPicked` and InfoPtr = the code as a pointer-sized integer. Both are virtual; a subclass may extend.

**Draw**: for each of the view's rows Y (0..Size.Y-1): the whole row is first filled with spaces in color 1. For Y < 8 and for columns X = 0..31 while X < Size.X: the cell uses color 2 if `MarkCursor` and (X, Y) is the cursor, else color 1. The text T is `CellText(Block*256 + Y*32 + X)` in Unicode mode and `CellText(Y*32 + X)` in code page mode. If T is exactly one byte, that byte is the cell's character; otherwise the cell is first a space and, if T is not empty, T is written at X for a width of one column (so a multi-byte UTF-8 text forms one cell, and empty text leaves a space). Rows of the view below row 7 stay blank. (Test: in a 34x12 window with the table at its interior, row 1 begins ` !"#$%&'()` = codes 32..41; row 2 begins `@ABC`; in the Unicode mode with code $E9 selected row 7 begins with U+00E0 .. U+00E9 characters.)

**KeyAction(Event)** maps `Event.KeyDown.KeyCode` to a TAsciiKey: Left, Right, Up, Down -> akLeft/akRight/akUp/akDown; Home -> akRowStart; End -> akRowEnd; PgUp -> akColTop; PgDn -> akColBottom; Ctrl+Home -> akFirst; Ctrl+End -> akLast; Ctrl+Left -> akLeft5; Ctrl+Right -> akRight5; Ctrl+PgUp -> akPrevBlock; Ctrl+PgDn -> akNextBlock; Enter -> akPick; anything else akNone. (akUp2, akDown2 exist for subclasses and are handled by HandleEvent as a move of two rows but are never returned by the default KeyAction.)

**TypedCode(Event)**: the code that a typed character stands for, or -1. Unicode mode: if the event has text (TextLength > 0), its first UTF-8 character is valid and its code point is >= 32, that code point (this admits $7F..$9F). Code page mode: `Event.KeyDown.CharScan.CharCode` when it is >= 32 (a byte), else -1. A key without a character gives -1. (In code page mode a letter delivered only as multi-byte UTF-8 text with a zero CharCode is therefore not picked.)

**HandleEvent(Event)**: first the inherited handling (standard view behaviour such as selecting on a click). Then:
* `evMouseDown` with the double-click flag: if the pointer is inside the view, move the cursor to the cell under it (as `MoveTo` below); then `Pick`; clear the event; return. Without the double-click flag: loop: while the mouse button is held (until a mouse event other than a move arrives, i.e. `MouseEvent(Event, evMouseMove)` returns False), if the pointer is inside the view, move the cursor to the local cell under it; clear the event afterwards. A single click never picks.
* `evKeyDown`: act by `KeyAction`: moves by one cell (left, right, up, down), to the row start/end, to the column top/bottom (row 0 / row 7), to the very first (0,0) or last (31,7) cell, two rows up/down, five columns left/right; `akPrevBlock`/`akNextBlock` change `Block` by -1/+1 only in Unicode mode and only when the new block is within 0..AsciiMaxBlock (otherwise nothing happens: no redraw, no Focused), then redraw and `Focused`; `akPick` calls `Pick`. For akNone: if `TypePicks` is False the handler returns at once and the event is NOT cleared (so a key can reach other handlers); otherwise `TypedCode`; if it is negative, or above $10FFFF in Unicode mode, or above 255 in code page mode, the handler returns without clearing the event; otherwise `SetCode(code)` then `Pick`. After any recognised action the event is cleared.
* **MoveTo(X, Y)** (private): clamps X to 0..31 and Y to 0..7; if the position changed, sets the cursor and, when `MarkCursor`, redraws; always calls `Focused` (even if the cursor did not move, e.g. Right at column 31 stays but still announces).
* Moves stop at the table edges (no wrap): End then Right and Down at code 255 leave 255.
* In code page mode Ctrl+PgUp and Ctrl+PgDn change nothing.

**Data**: `DataSize` = 4 (a LongInt); `GetData` stores `Code`; `SetData` calls `SetCode` with the value.

**Streaming**: `Write` stores the inherited view data (which includes the cursor), then `Block` (4 bytes), then one byte with bit 0 = Unicode, bit 1 = TypePicks, bit 2 = MarkCursor. `Read` reverses this and sets `CharText := AsciiCharText`. `StreamableName` = 'TAsciiTable'.

### 3.3 TAsciiReport

A one-row view. `Code`, `Unicode`, `CharStr` are the data to show. **Construction**: event mask gets `evBroadcast`. Palette: `AsciiPalette` (entry 1 = text, entry 2 = the character).

**ReportParts(Prefix, Rest)** (virtual): Prefix is ` Char: ` (with one leading and one trailing space). Rest is, in Unicode mode, two spaces, `Dec: ` and the decimal code, two spaces, `U+` and the code as at least 4 uppercase hex digits (e.g. `  Dec: 233  U+00E9`); in code page mode two spaces, `Dec: ` and the code in decimal right-aligned in a field of width 3, two spaces, `Hex: ` and two uppercase hex digits (`  Dec:  33  Hex: 21`).

**Draw**: a row of spaces in color 1; Prefix at column 0 in color 1; then, if the column after Prefix is inside the view: `CharStr` in color 2 in one cell (if exactly one byte, that byte with #0 shown as a space; if longer, the text written at that column occupying one cell; if empty, nothing is written, leaving a space), then, starting in the column right after the character cell (the character always occupies exactly one cell), the Rest string in color 1, limited to the remaining width, when it fits at least partly and is not empty. Test: the whole row for code 33 in code page mode, trimmed on the right, is ` Char: !  Dec:  33  Hex: 21`; for code 0 it contains `Dec:   0`; Unicode U+00E9 gives ` Char: <e-acute>  Dec: 233  U+00E9`.

**ShowCode(Table)**: copies `Table.Code` into Code, `Table.Unicode` into Unicode, `Table.CellText(Code)` into CharStr, then redraws.

**HandleEvent**: inherited handling; then, for an `evBroadcast` with command `AsciiCommandBase + acFocused` whose InfoPtr is an object of class TAsciiTable, `ShowCode` of that table. The event is not cleared (other reports or the window may also see it).

**Streaming**: Write: inherited data, `Code` (4 bytes), then a byte (1 if Unicode). Read: reverses, then recomputes `CharStr` from the code: by `AsciiCharText` if assigned, else `AsciiUnicodeText` in Unicode mode, else `AsciiCodePageText`. `StreamableName` = 'TAsciiReport'.

### 3.4 TAsciiChart

A window (class TWindow) with no window number (`wnNoNumber`) of outer size AsciiCols+2 by AsciiRows+4 (34 x 12). The window flags lose `wfGrow` and `wfZoom` (it cannot be resized or zoomed). The interior (frame excluded) is 32 x 10. Inside, the report is created by `MakeReport` on the last interior row (full width, 1 row) and the table by `MakeTable` on the first 8 interior rows (one empty row between them); both get `ofFramed`; the report is inserted first, then the table (with `Unicode := AUnicode` set after creation); the table is selected (focused) and the report shows its code immediately (ShowCode). Default title 'ASCII Table'. `MakeTable` and `MakeReport` (virtual) create default instances so that a subclass can substitute its own. Tests: Size = 34 x 12; table Size = 32 x 8; the table is focused; the report row is the 10th interior row (index 9).

The window needs no special event handling of its own: key and mouse events reach the focused table; the table's broadcast on cursor moves reaches the report through the window group, and a picked code arrives at the window's owner as the `acPicked` command (an event the window passes on if it does not handle it).

**Streaming**: Write: inherited window data, then the pointers Table and Report (stored through the stream's pointer mechanism). Read reverses. `StreamableName` = 'TAsciiChart'. In `initialization` the three classes are registered: `RAsciiTable := TStreamableClass.Create('TAsciiTable', @TAsciiTable.Build)` and likewise for TAsciiReport and TAsciiChart.

### 3.5 Messages

`AsciiCommandBase` is a Word (default 910); `acFocused` (offset 0) is a broadcast to the table's owner with InfoPtr = the table when the cursor or block moves or SetCode is used; `acPicked` (offset 1) is an `evCommand` sent to the owner with InfoPtr = the picked code (as a pointer-sized integer) after `OnPick` ran.

## 4. Dependencies

* TvGeom: TRect, TPoint. TvColors: TColorAttr and the palette type. TvEvents: TEvent, evKeyDown/evMouseDown/evMouseMove/evBroadcast/evCommand, meDoubleClick, mbLeftButton, ClearEvent. TvKeys: kbLeft, kbRight, kbUp, kbDown, kbHome, kbEnd, kbPgUp, kbPgDn, kbCtrlHome, kbCtrlEnd, kbCtrlLeft, kbCtrlRight, kbCtrlPgUp, kbCtrlPgDn, kbEnter.
* TvDrawBuf: TDrawBuffer (Create(width), MoveChar, MoveStr returning the next column, Free). TvObjs: the stream classes (ipstream, opstream, TStreamable, TStreamableClass, TStreamableInit). TvViews: TView (Cursor, SetCursor, BlockCursor, ShowCursor, DrawView, WriteLine, GetColor, MouseInView, MakeLocal, MouseEvent, Message, ClearEvent, option flags ofSelectable and ofFramed, GetExtent, Insert, Select). TvWindow: TWindow, wnNoNumber, wfGrow, wfZoom.
* Implementation only: SysUtils (Format for the report), TvUtf8 (Utf8Encode, Utf8Decode, CharWidth).
* The tests also use TvCodePg (the code page of the screen: a byte in a cell is shown through the current page), TvCell and TvScreen (the screen buffer to read cell texts back).

## 5. Tests (tests/t_ascii.pas, and tests/pty/test_ascii.py through a terminal)

t_ascii.pas builds a 40 x 14 screen and a test desk; pinned: window size 34 x 12, table 32 x 8, focus on the table; first rows of cells (codes 32..41 and 64..); report text at code 0 and 33; key results (Right+Down from 0 gives 33; End 63; Home 32; PgDn 224; PgUp 0; Ctrl+End 255; edges clamp; Ctrl+Right 5; Ctrl+PgDn no effect in code page mode); picking by Enter (OnPick called with 65 and the window receiving one command with 65), typed `z` (cursor and pick), TypePicks False (not picked), single click moves (code 35) without picking, double click picks (code 68); data set/get with 200 (cursor row 6); the text hooks; streaming a window with code 200 and reading it back (table and report found, both codes 200); Unicode mode: row 7 shows U+00E0..., report shows ` Char: <e-acute>  Dec: 233  U+00E9`, Ctrl+PgDn goes to block 1 (code $1E9, first cell U+0100), Ctrl+PgUp twice stops at block 0, typing U+0436 goes to block 4, code $436 and is picked; palette string has two entries.

## 6. Observed oddities

* `akUp2` and `akDown2` are handled but never produced by the default KeyAction. Intended (extension points for subclasses).
* `Focused` is announced even when the cursor does not move (MoveTo at an edge, a click on the already selected cell). Intended (simple, idempotent).
* `TypedCode` in Unicode mode accepts code points $7F..$9F, whose cell is shown as a space, and in code page mode a key that has only a multi-byte text and a zero CharCode is ignored. Accepted.
* `SetCode` in code page mode ignores Block (it is not reset). Accidental but harmless; `Code` ignores Block in that mode.
* In `Draw`, a multi-byte text is written with a one-column width limit; a hook returning wide or multi-character text is cut by the draw buffer. Intended limit (the hook's contract is width 1).
* When the key is not recognised and TypePicks is False the event is intentionally left uncleared; with TypePicks True and an unusable character it is also left uncleared. Intended.
* The test `Length(TPalette.Create(...).Data) = 3` for a palette of two entries depends on the TPalette representation of the library (a length/terminator byte plus entries); it is not a requirement of this unit.
