# Unit TvGadgets - functional specification

## 1. Purpose

TvGadgets has two small one-row views that show a value of the system: a clock (`TClockView`) and the memory in use by the program (`THeapView`). The program calls `Update` of each view from its idle handler or a timer; a view repaints only when its text has changed. Both are views of the Tv library and run on the UI thread only. Both draw a single row of text on a background of blanks, in the colour of palette entry 1 of the view.

## 2. Interface

```pascal
unit TvGadgets;

interface

uses
  SysUtils, TvGeom, TvColors, TvEvents, TvDrawBuf, TvViews;

type
  TClockView = class;

  TClockFormat = function(H, M, S: Word; Seconds, Separator, Hour12: Boolean): AnsiString;
  TClockClick = procedure(Sender: TClockView; var Event: TEvent) of object;
  TClockNowFunc = function: TDateTime;
  THeapValueFunc = function: Int64;

  TClockView = class(TView)
    ShowSeconds: Boolean;
    BlinkSeparator: Boolean;
    Hour12: Boolean;
    AutoSize: Boolean;
    RightAlign: Boolean;
    Margin: Integer;
    FormatHook: TClockFormat;
    OnClick: TClockClick;
    PaletteStr: ShortString;
    TimeStr: AnsiString;
    constructor Create(const Bounds: TRect);
    function GetPalette: TPalette; override;
    function ClockText: AnsiString; virtual;
    procedure Update; override;
    procedure Draw; override;
    procedure HandleEvent(var Event: TEvent); override;
    function MsToNextChange: Integer;
    procedure FitWidth(W: Integer);
  end;

  THeapView = class(TView)
    Kb: Boolean;
    ValueHook: THeapValueFunc;
    PaletteStr: ShortString;
    HeapStr: AnsiString;
    constructor Create(const Bounds: TRect);
    constructor CreateKb(const Bounds: TRect);
    function GetPalette: TPalette; override;
    function HeapText: AnsiString; virtual;
    procedure Update; override;
    procedure Draw; override;
  end;

function ClockFormatDefault(H, M, S: Word; Seconds, Separator, Hour12: Boolean): AnsiString;
function HeapInUse: Int64;

var
  ClockNow: TClockNowFunc = nil;
  GadgetPalette: ShortString = #2;
```

Source begins with `{$I tvdefs.inc}`. `Update` is a virtual method of `TView` (a no-op there) that is called by the program, not by the view system. `TimeStr` and `HeapStr` are public so that tests can read them.

## 3. Common behaviour

**Palette**. Both classes keep `PaletteStr`, copied from the global `GadgetPalette` when the view is created (changing the global later does not affect existing views). `GetPalette` returns the empty palette (`Default(TPalette)`, `Data = nil`: no palette of its own, the colours of the owner are used) when `PaletteStr` is empty; otherwise a palette made from the bytes of `PaletteStr` (`TPalette.Create(pointer, length)`: `Data[0]` = length, `Data[1..n]` = the bytes). With the default `#2` the palette has one entry and its data array has 2 elements; entry 1 (the text) maps to entry 2 of the owner's palette, the "normal text" of the menu bar of `TProgram`.

**Drawing (shared helper)**. The view's row 0 is written with the colour `GetColor(1)[0]` (the first attribute of the pair): first the whole width `Size.X` is filled with blanks of that colour, then the text S (if not empty) is written from cell X0 with the same colour, truncated at the right edge of the view (at most `Size.X - X0` cells). X0 is 0 when drawing to the left, or, when drawing to the right, `Size.X - width(S)` clamped to at least 0, where width is the number of screen cells of the UTF-8 text (`TText.Width` of TvText). Only one row is written (row 0 of the view, via `WriteLine(0, 0, Size.X, 1, buffer)`); a view higher than one row is not intended. A text wider than the view, drawn to the right, starts at cell 0 and loses its right end.

## 4. TClockView

**Create(Bounds)**: defaults `ShowSeconds = True`, `AutoSize = True`, the others False/0/nil, `TimeStr = ''`; `EventMask` gets `evMouseDown` added (in addition to the inherited mask).

**Time source**. `ClockNow` (a global function variable) gives the current time as `TDateTime`; when nil the system's local time (`Now`) is used. Tests set their own.

**ClockText** (virtual): decodes the hour H, minute M, second S and millisecond Ms of the time. The separator flag Sep is `not BlinkSeparator or ShowSeconds or (Ms < 500)`; thus blinking works only without seconds, and then the separator is blank in the second half of every second. The text is `FormatHook(H, M, S, ShowSeconds, Sep, Hour12)` when the hook is assigned, otherwise `ClockFormatDefault(...)`. If `Margin > 0`, `Margin` blanks are added on both sides (a zero or negative margin adds nothing). The result is not stored.

**ClockFormatDefault(H, M, S, Seconds, Separator, Hour12)**: hour, separator, minutes and optionally seconds. The separator between hours and minutes is `:` or, when Separator is False, a blank; the separator before seconds is always `:`. Minutes and seconds have two digits. 24-hour (Hour12 False): the hour has two digits. 12-hour: `am` when H < 12, else `pm`; the hour is H mod 12 with 0 shown as 12, written without a leading zero but padded with a blank to two characters (so the width is constant); the suffix `am`/`pm` is appended after the minutes (or seconds) with no blank. Examples: (9,5,7,secs,sep,24h) `09:05:07`; (9,5,7,no secs) `09:05`; blank separator `09 05`; (0,5,0,no secs,12h) `12:05am`; (13,5,0,12h) ` 1:05pm`; (12,0,9,secs,12h) `12:00:09pm`.

**MsToNextChange**: milliseconds from `ClockNow` until the text will change: with `BlinkSeparator` and not `ShowSeconds`: `500 - Ms mod 500`; else with `ShowSeconds`: `1000 - Ms`; else `(60 - S) * 1000 - Ms`. Always between 1 and 60000. It assumes the default format. Examples: 10:20:31.000 with seconds gives 1000; 10:20:31.600 blinking without seconds gives 400; 10:20:31.600 not blinking without seconds gives 28400.

**FitWidth(W)**: sets the width of the view to W cells, choosing which edge stays. Let R be the view's current bounds (`Origin` to `Origin + Size`). If `RightAlign` is set and the view has an owner: the right edge becomes the owner's width and the left edge is that minus W. Else if the view has an owner and `Origin.X + Size.X div 2 > Owner.Size.X div 2` (the view lies in the right half of the owner): the right edge stays and the left edge becomes right minus W. Otherwise (left half, or no owner): the left edge stays and the right edge is left plus W. Y coordinates are unchanged. If the resulting left and right edges equal the present ones nothing is done; otherwise the view is moved/resized with `Locate(R)` when it has an owner (so it is redrawn and the owner's clipping is updated) or `SetBounds(R)` without an owner.

**Update**: computes `ClockText`. If it equals `TimeStr`: when `RightAlign` is set, there is an owner and the view's right edge is not at the owner's width, `FitWidth(Size.X)` is called (so the clock follows a changed owner width); no redraw; return. Otherwise `TimeStr` takes the new text; then if `AutoSize` the width is fitted to the width of the text in screen cells (`FitWidth`), else if `RightAlign` `FitWidth(Size.X)`; then the view is redrawn (`DrawView`). Redrawing causes exactly one call of `Draw` when the view is visible.

**Draw**: the shared helper, text `TimeStr`, drawn to the left. Before the first `Update` the row is blank.

**HandleEvent**: calls the inherited handler, then, if the event is still `evMouseDown` and `OnClick` is assigned, calls `OnClick(Self, Event)` (the callback is expected to clear the event). No position test is made (the owner has already routed the click to the view).

## 5. THeapView

**Create(Bounds)**: `PaletteStr` from `GadgetPalette`, `Kb` False. **CreateKb(Bounds)**: the same with `Kb = True`.

**HeapInUse**: the number of bytes currently in use in the program's heap (any reasonable counter of the memory manager; the test only needs it to be positive).

**HeapText** (virtual): V = `ValueHook()` when assigned, else `HeapInUse`. With `Kb`: `(V + 1023) div 1024` in decimal followed by `K` (rounded up); otherwise V in decimal. Examples: 123456 gives `123456`, or `121K` with `Kb`.

**Update**: computes `HeapText`; if it equals `HeapStr` nothing happens; otherwise it is stored in `HeapStr` and the view is redrawn.

**Draw**: if `HeapStr` is empty it is first filled from `HeapText`; then the shared helper draws it to the right. (Changing `Kb` or the hook does not show before the next `Update`.)

## 6. Units used

* `SysUtils`: `IntToStr`, `Now`, `DecodeTime`, `TDateTime`, string-of-char padding, the heap status of the runtime for `HeapInUse`.
* `TvGeom`: `TRect`, `TPoint`-like `Origin`/`Size` members (used through TView).
* `TvColors`: `TColorAttr`.
* `TvEvents`: `TEvent`, `evMouseDown`.
* `TvDrawBuf`: `TDrawBuffer` (`Create(width)`, `MoveChar(x, char, attr, count)`, `MoveStr(x, bytes, length, attr, maxCells)`, `Free`).
* `TvViews`: `TView` (`Origin`, `Size`, `Owner`, `EventMask`, `GetBounds`, `Locate`, `SetBounds`, `DrawView`, `WriteLine`, `GetColor`, `ClearEvent`, `HandleEvent`), `TPalette`, `TGroup` (owner).
* `TvText` (implementation): `TText.Width(bytes, length)`, the screen width of UTF-8 text.

## 7. What the tests pin down (t_gadgets)

The test draws into an in-memory screen buffer of 40 x 3 cells under a `TGroup` desktop (`ClockNow` is replaced by a fake):

* `ClockFormatDefault` values of section 4.
* A clock in a 10-cell box at x=30..40 with `Margin = 1`, time 10:20:30.100: after `Update` `TimeStr` is ` 10:20:30 `, width 10, origin 30, and the cells 30..39 of row 0 show ` 10:20:30 `. A second `Update` at 10:20:30.900 does not call `Draw`; at 10:20:31.000 `Draw` is called exactly once more and the cells show ` 10:20:31 `. `MsToNextChange = 1000`.
* `ShowSeconds` off, `BlinkSeparator` on, 10:20:31.100: `TimeStr` ` 10:20 `, width 7, the right edge still at 40. At .600: ` 10 20 `, `MsToNextChange` 400. Blink off: ` 10:20 ` and 28400.
* `FormatHook` returning `H.MM` (hour not padded, minutes two digits) gives ` 10.20 `.
* A second clock at x=2 (box 10 wide), no seconds: `Update` makes it 5 wide at x=2 (left edge stays); `RightAlign := True` then `Update` puts its right edge at 40 (the owner's width).
* `OnClick` is called once for a mouse-down event delivered with `HandleEvent`, and the event ends as `evNothing` (the callback clears it).
* `GetPalette.Data` has 2 elements by default and is nil with an empty `PaletteStr`.
* A heap view at x=30..40, row 2, `ValueHook` returning 123456: after `Update` row 2 cells 30..39 show `    123456` (right-aligned); with `Kb` `      121K`; with the hook removed `HeapText` is a positive number.

A test program should also check: `Hour12` through the view; `AutoSize` false keeps the width; a clock without an owner uses `SetBounds` and keeps the left edge; a wide text in a narrow heap view is cut at the right; `GadgetPalette` copied at creation; `Draw` before `Update` shows blanks.

## 8. Observed oddities

Intended: repaint only on a changed text; width follows the text with the edge rule of `FitWidth`; `MsToNextChange` for a timer.

Accidental or limited: `MsToNextChange` ignores a `FormatHook` that shows other precision; the right-aligned text that does not fit loses its end instead of its start; a view higher than one row has its other rows left undrawn; `HeapText` rounds negative values toward zero; `THeapView.Draw` computes `HeapStr` when empty, which `TClockView.Draw` does not do for `TimeStr`; the click handler does not check which button or that the event is inside the view.
