# Unit TvVtExt - functional specification

## 1. Purpose

TvVtExt is the terminal side of the far2l terminal extensions, used by the embedded terminal emulator (TvVt). A program that runs inside the embedded terminal may announce itself with an APC string that begins with the text "far2l" and then talk to the terminal in requests and replies carried in further APC strings. TvVtExt takes the body of such a string (the emulator cuts off the leading ESC _ and the terminator and hands the rest over) and returns the bytes that must go back to the program: the acknowledgement of the activation, the reply to a request that has an ID, and the size event. It also builds the input events (keys and mouse) that the emulator sends to a program that asked for them.

What the server cannot do by itself it passes to a host object (TVtExtHost): asking the user whether a client may use the clipboard, showing a notification, showing titles of F-keys, setting the cursor height, giving the colour depth, the largest window size, maximizing or restoring the window, the quick edit of the mouse. The base host forwards these to TvSys and refuses the clipboard; the terminal view and the terminal runner give their own hosts.

The clipboard served is the clipboard of the application (TvClip) with its formats. A client is let in by the user (the four answers of the dialog "Clipboard access"), for the current activation only or for always (a file in the configuration directory). The data of the clipboard is read only within 5 seconds after a paste gesture of the user (Ctrl+V, Shift+Ins, the middle button), a read extends that time, at most 3 times. Images are not supported (no capabilities are reported).

The unit keeps state per server object only (no global state besides the helper function). It is not thread-safe; use one server from one thread.

Wire conventions used below (they come from TvFar2l): all numbers are little-endian. A request or reply is carried as a "stack" of bytes that is built by pushing values and read by popping values from the end (last pushed, first popped). A string is pushed as its bytes and then a 32-bit length, so it is popped as length first and then bytes. A request stack, read from the end, has: the ID (1 byte), the command (1 byte), then the arguments of the command in the reverse order of pushing. So on the wire the request ends with the command byte and the ID byte, preceded by the arguments. A reply stack ends with the ID; before it come the values, so the client pops the ID first and then the values in the reverse of the order the server pushed them. "Pushes A then B" below means in that order, so the client pops B first. A pop of more bytes than the stack has gives zeros and marks the stack "bad". A request is carried as ESC _ far2l : (base64 of the stack) ESC \ ; a reply as ESC _ far2l (base64 of the stack) BEL; an event as ESC _ f2l (base64 of the stack) BEL; the acknowledgement as ESC _ far2lok BEL. Base64 is the standard alphabet with padding.

## 2. Interface

```pascal
unit TvVtExt;

interface

uses
  SysUtils, TvFar2l, TvClip, TvSys, TvScreen, TvEvents, TvKeys;

type
  { the answers of the user to a client that asks for the clipboard }
  TVtClipAnswer = (vcaBlock, vcaRemote, vcaShare, vcaAlways);

  TVtExtHost = class
  public
    function AskClipboard(const ClientId: AnsiString): TVtClipAnswer; virtual;
    procedure Notify(const Title, Text: AnsiString); virtual;
    function FKeyTitles(const Titles: array of AnsiString): Boolean; virtual;
    procedure CursorHeight(Percent: Integer); virtual;
    function ColorBits: Integer; virtual;
    function WindowMaxSize(out Cols, Rows: Integer): Boolean; virtual;
    procedure WindowMaximize(Maximize: Boolean); virtual;
    procedure QuickEdit; virtual;
  end;

  TVtClockFunc = function: Int64;

  TVtExtServer = class
  public
    Active: Boolean;            { between far2l1 and far2l0; False after Create }
    CursorPercent: Integer;     { the cursor height the program asked for, -1: none }
    AuthedsPath: AnsiString;    { the file of the clients let in always }
    Now: TVtClockFunc;          { the clock of the paste gestures, milliseconds }
    constructor Create(ACols, ARows: Integer);
    destructor Destroy; override;
    function Body(const B: AnsiString): AnsiString;
    function Resized(ACols, ARows: Integer): AnsiString;
    procedure Stop;
    procedure PasteGesture;
    function CompactInput: Boolean;
    function KeyEvent(const Event: TEvent): AnsiString;
    function MouseEvent(X, Y: Integer; Buttons, Wheel: Byte; Moved, Double: Boolean; Mods: Word): AnsiString;
    property Host: TVtExtHost read FHost write SetHost;
  end;

function VtClipDataId(Format: LongWord; const Data: AnsiString): QWord;
```

The class TVtExtServer has also private state, described in words (it need not be declared the same way): the current host and the own base host created by Create and freed by Destroy; the features word of the client (QWord); the host identity text; the terminal size (Cols, Rows); the "clipboard is open" flag; the list of client IDs shared for this activation; the pending chunk bytes; the list of clipboard items set since the clipboard was opened; the time of the last paste gesture (Int64), a flag that a gesture was ever seen, the count of extensions used; and the bytes to append after the reply of the current request ("After"). The property Host reads the current host; writing nil restores the own base host, writing a host object makes it current (the server never frees a host that was given to it).

Private constants: the clipboard features that the server reports on CLIP_OPEN are F2lClipDataId or F2lClipChunkedSet, that is 3. Statuses of the clipboard calls: ok = 1, fail = 0, closed = -1 (sent as one byte, so -1 is $FF).

No other public identifiers.

## 3. Behaviour

### 3.1 The base host (TVtExtHost)

* AskClipboard: returns vcaRemote for any client (the client keeps its own clipboard).
* Notify: calls TvSys.Notify with the same title and text.
* FKeyTitles: calls TvSys.SetFKeyTitles with the titles; returns True when the hook OnSetFKeyTitles of TvSys is assigned, else False.
* CursorHeight: does nothing.
* ColorBits: the result of TvSys.ColorBits; when that is 0, returns 4.
* WindowMaxSize: the result and the sizes of TvSys.WindowMaxSize. WindowMaximize and QuickEdit: call the same routines of TvSys.
* The answers mean: vcaBlock - the user refused; vcaRemote - "use the remote (your own) clipboard"; vcaShare - let the client in for this activation; vcaAlways - let the client in and remember it in the file.

### 3.2 Create, Destroy, defaults

Create(ACols, ARows) makes the own base host, makes it current, stores the size, sets CursorPercent to -1, Active False, features 0, no host identity, the gesture never seen, AuthedsPath to the configuration directory of TvFar2l (F2lConfigDir), then a path delimiter, then the file name F2lAuthedsFile (far2l-clipboard-autheds), and Now to a function that returns the tick count in milliseconds (THardwareInfo.GetTickCountMs, taken as Int64). Destroy frees the own host only. Destroy does not call Stop.

### 3.3 Body(B): the body of an APC string

Returns the bytes for the program, or the empty string. The rules, in order:
* If B is shorter than 6 bytes, or its first 5 bytes are not exactly "far2l" (lower case): empty result, nothing changes.
* The sixth byte selects:
  * '1': Active becomes True; the result is the acknowledgement ESC _ far2lok BEL (F2lAckSeq). Repeated far2l1 while active answers again and changes nothing else (features and shares are kept). Bytes after the sixth are ignored (so "far2l1" is accepted whether the terminator was ST or BEL; the cutting is the emulator's task).
  * '0': the same as Stop (3.4); empty result.
  * '#': host identity. Only if no identity is set yet: the identity is the bytes of B from the 7th on, at most 256 of them, each byte below blank replaced by a blank. Later '#' strings are ignored (first wins). It is accepted whether Active or not. The identity is kept over Stop. Empty result.
  * ':': a request. Only if Active and B is longer than 6 bytes: the text after the colon is decoded from base64 (decoding stops at the first character outside the alphabet); if the decoded stack is not empty it is executed (3.5) and its result returned. An empty or all-invalid payload gives the empty result.
  * any other sixth byte (for example '_' in "far2l_marker"): empty result, ignored.
* A request before the activation (not Active) is ignored: empty result, no effect. The same after far2l0.

### 3.4 Stop, Resized, PasteGesture, CompactInput

* Stop: does nothing when not Active. Otherwise: Active False; the clipboard is closed (3.7 CloseClip: open flag off, chunks dropped, set items dropped, extension count 0); features 0; the list of shared clients forgotten; CursorPercent -1; the host's FKeyTitles is called with an empty list (so the titles are cleared; the result is ignored). The host identity, the gesture and the terminal size are kept.
* Resized(ACols, ARows): if the size equals the stored size, empty result. Otherwise stores the new size; if Active and the client asked for the size feature (bit F2lFeatTerminalSize, 2, of the features) the result is the size event F2lSizeSeq(Cols, Rows), else empty. The size is stored whether or not Active.
* PasteGesture: remembers that a gesture was seen, its time (the value of Now) and sets the extension count to 0. Works also when not Active.
* CompactInput: True when the features word has bit F2lFeatCompactInput (1).

### 3.5 Execution of a request

The request stack is read: first the ID (1 byte), then the command (1 byte). After execution a reply stack is built. Surplus unread bytes in the request are ignored. Rules:
* If after popping ID and command the stack is bad (the request had fewer than 2 bytes), nothing is executed; if the ID was read (the request had 1 byte) and is not 0, the reply is the ID alone.
* If the stack becomes bad at any time during the execution of the command (the arguments were too short), the values already put in the reply stack are dropped; the reply is the ID alone. Side effects that were already done stay (see oddities).
* The reply: if the ID is not 0, the reply stack gets the ID pushed last and is sent as a reply string (ESC _ far2l base64 BEL). If the ID is 0 nothing is sent for the reply, whatever the command (a request with ID 0 never gets an answer, also an unknown one).
* After the reply (or alone when the ID is 0) the bytes "After" are appended; it is non-empty only for the features command (below). Result is reply followed by After.
* Unknown commands: nothing is done; reply is the ID alone.

Commands (the command byte is the character shown):

| Cmd | Name | Arguments (popped in this order) | Effect and values pushed to the reply (in order) |
|---|---|---|---|
| 'x' | features | 64-bit features | Features are replaced (not added) by the value. If the size bit (2) is set and the stack was not bad, After becomes the size event for the current size. No values. |
| 'e' | quick edit | none | host QuickEdit. No values. |
| 'M' | maximize | none | host WindowMaximize(True). 'm' restore: WindowMaximize(False). No values. |
| 'h' | cursor height | 1 byte | Value above 100 is made 100. CursorPercent is set to it and host CursorHeight called with it (0 is allowed). A missing byte: nothing is set. No values. |
| 'w' | max window size | none | Asks host WindowMaxSize; if it returns False, or either size is zero or negative, the current size (Cols, Rows) is used instead. Pushes Cols as 16 bits, then Rows as 16 bits. |
| 'n' | notify | string, string | The first popped string is the title, the second the text; the host's Notify(Title, Text) is called only if both were read. No values. Example: payload "OK" len 2, "Done" len 4, then 'n', ID 0 gives title "Done", text "OK". |
| 'f' | F-key titles | up to 12 items | For I = F1 to F12: if the stack is empty, the title is empty (not an error). Otherwise pop a flag byte; if it is not 0, pop a string (the title), else the title is empty. If the stack is not bad, host FKeyTitles is called with the 12 titles (index 0 is F1) and pushes one byte, 1 if the host returned True, else 0. |
| 'p' | palette / colour depth | none | Pushes the byte 0 (reserved), then the byte of host ColorBits (low 8 bits). The client pops the depth first. |
| 'c' | clipboard | sub-command byte | See 3.6. |
| 'i' | image | 1 byte | If the byte is the character 'c' (capabilities): pushes 64-bit 0 (no capabilities), 16-bit 0, 16-bit 0 (no cell size); the reply is 12 zero bytes and the ID. Any other byte (set, transform, ...): pushes the byte 0 (not done). |

Examples (from the tests; each wire string is the whole APC):
* ESC _ far2l:MmgA BEL - cursor height 50 (bytes $32 'h' ID 0): no reply; CursorPercent 50; host got 50.
* ESC _ far2l:dwE= BEL - bytes 'w' ID 1: the test host says 200 by 50; the reply is ESC _ far2lyAAyAAE= BEL, that is bytes C8 00 32 00 01.
* ESC _ far2l:T0sCAAAARG9uZQQAAABuAA== BEL - notification; no reply; title "Done", text "OK".
* ESC _ far2l:AAAAAAAAAAAAAE1lbnUEAAAAAUhlbHAEAAAAAWYB BEL - F-key titles with ID 1: F1 "Help", F2 "Menu", F3..F12 none; reply ESC _ far2lAQE= BEL (bytes 01 01: success, ID 1); the host got "Help|Menu|" followed by ten empty titles.
* Stack 'F2' (string), flag 1, flag 0, 'f', ID 11: F1 none, F2 "F2", the remaining ten are missing and empty; the reply holds 1 and the ID.
* Palette with ID 10 and a host that says 24: reply values 24 then 0 then... popped: 24, 0, nothing left.
* Unknown command 'Z' with ID 9: reply ESC _ far2lCQ== BEL (the ID 9 alone). Command 'n' with ID 7 and no arguments: reply is the ID alone (ESC _ far2lBw== BEL). Command 'e' with ID 8: reply the ID alone, host QuickEdit called once.
* Image caps ID 5: reply is the base64 of twelve zero bytes and byte 5. Image set (ESC _ far2l:/wAA/wEAAAABAAAA/////wMAAgAAAAAAAAAAAGltZwMAAABzaQY= BEL, ID 6): reply ESC _ far2lAAY= BEL (status 0 and ID 6). Image transform with ID 7: ESC _ far2lAAc= BEL.
* Features with compact input and size (value 3), 'x', ID 0: no reply; the result is exactly the size event for 80 by 25: ESC _ f2lUAAZAFM= BEL (bytes 50 00 19 00 'S').
* ESC _ far2l:AQAAAAAAAAB4AA== BEL - features 1 (compact input), 'x', ID 0: no reply, no size event.

### 3.6 The clipboard command ('c')

The next byte is the sub-command (popped after ID and 'c'). If the stack is bad here nothing more is done (ID alone). Clipboard state: "open" flag, the list of items set by this client since opening ("set items"), the pending chunk bytes. Sub-commands:

* 'o' CLIP_OPEN. Argument: a string (the client ID). The pending chunk bytes are dropped first (always, even on failure). If the stack is bad: ID alone, nothing else. If the client ID is not valid (not 32 to 256 characters of 0-9, a-z, '-' and '_'; F2lValidClientId), or the clipboard is already open: status fail (0) and the user is not asked. Otherwise the ID is made into "identity:ID" when a host identity is set, and is authorised in this order: (1) it is in the list of clients shared for this activation: ok; (2) it is a line of the file AuthedsPath (each line trimmed of blanks, compared exactly and case-sensitively; no file, an empty AuthedsPath or an unreadable file means not found): ok; (3) otherwise the host's AskClipboard is called with the full ID (with the identity prefix, if any): vcaRemote gives status closed (-1); vcaBlock gives status fail (0), not remembered, so it is asked again next time; vcaShare adds the ID to the shared list of this activation and gives ok; vcaAlways first appends the ID to the file (creating the directory with its parents and the file if needed; failure to write is silent) and then adds it to the shared list and gives ok. On ok the clipboard becomes open and the set items list is emptied. The reply pushes the 64-bit clipboard features (always 3, also on failure) then the status byte; the client pops the status first. Example: ESC _ far2l:MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWYgAAAAb2MB BEL (client ID "0123456789abcdef0123456789abcdef", 'o', 'c', ID 1) with the answer vcaShare gives ESC _ far2lAwAAAAAAAAABAQ== BEL (features 3, status 1, ID 1); the host was asked once, with that ID.
* 'c' CLIP_CLOSE. No argument. Status ok if it was open, else closed (-1). In both cases the clipboard is closed (open flag off, chunks dropped, set items dropped, extension count 0). Pushes the status byte. The shared list and the gesture are kept.
* 'e' CLIP_EMPTY. If open: the set items list is emptied, the clipboard of the application is set to no items (ClipboardSetItems with an empty list; the text becomes empty), status ok. If not open: status closed. Pushes the status byte.
* 'a' CLIP_ISAVAIL. Argument: a 32-bit format. Pushes one byte, 1 if ClipboardHasItem(format) else 0. It needs neither an open clipboard nor a gesture. A bad stack: ID alone.
* 'S' CLIP_SET_CHUNK. Arguments: a 16-bit count N, then N times 256 bytes of data (pushed before the count). If the stack is bad or the clipboard is not open: nothing is done and nothing pushed (ID alone). N = 0: the pending chunk bytes are dropped. Otherwise the bytes are appended to the pending chunk bytes. No values.
* 's' CLIP_SET_DATA. Arguments, popped in this order: a 32-bit format, a 32-bit size, then Size bytes of data. A bad stack at any point: ID alone, nothing done. If the clipboard is not open: pushes the status closed (-1) (the data was read first, so a short stack still gives the ID alone). Otherwise the data is the pending chunk bytes followed by the given data, and the pending chunk bytes are dropped. The data is stored (below); then pushes the 64-bit data ID VtClipDataId(format, data) of the merged data in the format the client named, and then the status ok; the client pops the status first. Storing: for the text format (cfText, 1) the data is cut at its first NUL byte (data without a NUL is whole); for the Unicode text format (cfUnicodeText, 13) the data is UTF-32 little-endian and is converted to UTF-8 (F2lUtf32ToUtf8; stops at a zero character) and then treated as cfText; so both text formats are one text slot. Any other format is stored as it is. In the set items list an item of the same format is replaced, otherwise one is added at the end; then the whole set items list is given to the clipboard of the application (ClipboardSetItems) and the success is always reported. Examples: set cfText "hello" gives status 1 and data ID of (cfText, "hello"), and ClipboardGetText is "hello"; set cfText "vert" NUL (size 5) stores "vert"; set the registered vertical-block format with 4 zero bytes keeps the text; set cfUnicodeText with the UTF-32 of a 3-letter Cyrillic word (12 bytes of UTF-32, size 12) replaces the text and keeps the other format. Chunks: 256 bytes 'x' sent as one chunk, then 'end' set as data (cfText) gives "x" times 256 followed by "end", with the data ID of that text; a chunk of N = 0 afterwards drops pending chunks, so a set of "only" gives "only".
* 'g' CLIP_GET_DATA. Argument: a 32-bit format (bad stack: ID alone). If not open: pushes the 32-bit value $FFFFFFFF alone. Otherwise, if reading is allowed with extension (3.8) and the format can be fetched (below), pushes the 64-bit data ID of the fetched data, then the data bytes, then the 32-bit length of the data (the client pops the length, then the data, then the ID). In every other case (no gesture, time over, nothing to fetch) pushes 64-bit 0 and then 32-bit 0 (the client pops size 0 then ID 0). Fetching: cfText - the text of the clipboard (ClipboardGetItem for cfText), fails if absent or empty; cfUnicodeText - the same text converted to UTF-32 little-endian (F2lUtf8ToUtf32, no terminating zero: "vert" gives 16 bytes); any other format - ClipboardGetItem for that format (an item of empty data is a success with size 0 and a data ID of the empty data). The data ID is computed (VtClipDataId) over the fetched bytes with the requested format, so for cfUnicodeText over the UTF-32 bytes. Note that the reading permission (and an extension) is used before the fetch, so a failed fetch still uses an extension.
* 'i' CLIP_GET_DATA_ID. Argument: a 32-bit format. Pushes the 64-bit data ID of the fetched data (as in 'g') if the clipboard is open, reading is allowed without extension and the fetch succeeds; else pushes 64-bit 0.
* 'r' CLIP_REGISTER_FORMAT. Argument: a string (a format name). Pushes the 32-bit number from ClipboardRegisterFormat(name). It needs no open clipboard. The same name gives the same number; the first registered number of a process is $C000, so the test's request for "FAR_VerticalBlock_Unicode" gives bytes 00 C0 00 00 then ID: ESC _ far2lAMAAAAQ= BEL for ID 4 (when no other format was registered before).
* Any other sub-command: no effect; ID alone.

### 3.7 CloseClip (internal)

Sets the open flag off, drops the pending chunk bytes and the set items list, and sets the extension count to 0. Called by CLIP_CLOSE and Stop. It does not clear the gesture time or the "gesture seen" flag.

### 3.8 Reading permission (ReadAllowed)

A read of the clipboard data by the client is allowed only if a paste gesture was seen and at most F2lGestureMs (5000) milliseconds have passed since the stored gesture time (the age is Now minus the time; an age of exactly 5000 is still allowed; above 5000 is refused). When allowed and the call is one that extends (CLIP_GET_DATA) and fewer than F2lGestureExtends (3) extensions were used since the gesture (or since the clipboard was closed), then the stored gesture time becomes the current time and the count goes up by one. CLIP_GET_DATA_ID never extends. Both the gesture and the extension count apply to the whole server, not to a client. Example (time in ms, gesture at 200000): reads at 204000, 208000, 212000 each succeed and each extend (3 extensions used, stored time 212000); a read at 216000 succeeds (age 4000) but does not extend; a read at 217500 fails (age 5500). Without any gesture a read gives the "no data" answer (ID 0, size 0 for GET_DATA, 0 for GET_DATA_ID). A new gesture sets the count to 0.

### 3.9 VtClipDataId(Format, Data)

The 64-bit data ID of clipboard data, never 0. N is the length of Data; for the text format cfText, N is the position of the first NUL minus one when Data has a NUL (so only the text before it counts). The value starts as $CBF29CE484222325 exclusive-or N; then for each of the first N bytes in order: exclusive-or with the byte, then multiply by $100000001B3 (64-bit, wrapping). (This is FNV-1a 64 with the length mixed into the start.) If the final value is 0, the result is 1.

### 3.10 KeyEvent(Event)

Returns the empty string when not Active. Otherwise builds the key event string for the program:
* The character: EventUtf16(Event) gives the text of the key as 1 or 2 UTF-16 units; 1 unit gives that unit; 2 units are joined into the full code point (above $FFFF); 0 units give 0.
* The control state is EventWin32State(Event) (wk* bits: right alt $0001, left alt $0002, right ctrl $0004, left ctrl $0008, shift $0010 ...).
* If a Ctrl bit (left or right) is set and no Alt bit is set: the character 'a'..'z' becomes 1..26; the characters from '@' to '_' (this includes the capitals) become 0..31; other characters are unchanged. (A character that EventUtf16 gave already as a control character is below '@' and unchanged.)
* The repeat count is Event.KeyDown.RepeatCount, 0 counted as 1.
* The string is F2lKeySeq(Down, Ch, State, ScanCode, VirtualKey, Repeat, CompactInput), where Down is True unless Event.What is evKeyUp (every other kind counts as a press), ScanCode is EventScanCode(Event) and VirtualKey EventVirtualKey(Event).
* Examples: with compact input on, a press of 'a' with no modifiers gives ESC _ f2lQQAAYQBD BEL (bytes: $41 VK, state 00 00, char 61 00, 'C'). The release of it starts with ESC _ f2l and its first stack byte popped is the character 'c'. Ctrl+A (code kbCtrlA, state kbLeftCtrl): popped are 'C', character 1, a state with a Ctrl bit ($0C mask not 0), VK $41.

### 3.11 MouseEvent(X, Y, Buttons, Wheel, Moved, Double, Mods)

Returns the empty string when not Active. Otherwise builds the mouse event with F2lMouseSeq(Flags, KeyState, Buttons, X, Y, CompactInput):
* Button state: bit 1 for mbLeftButton, 2 for mbRightButton, 4 for mbMiddleButton.
* Flags: 1 if Moved; 2 if Double.
* Wheel: if Wheel has mwUp or mwDown: flag 4 is added and the high 16 bits of the button state are 1 for up, $FFFF (-1) for down (up wins when both are set); else if Wheel has mwLeft or mwRight: flag 8 is added and the high 16 bits are 1 for right, $FFFF for left (right wins). The vertical wheel wins over the horizontal one.
* Key state: wkShift ($10) if Mods has kbShift; wkLeftCtrl ($08) if Mods has any of kbCtrlShift; wkLeftAlt ($02) if Mods has any of kbAltShift. No other bits.
* X and Y are cells of the terminal (zero-based, as given).
* Examples (compact on): left button at column 10, row 5, no wheel: ESC _ f2lCgAFAAEAAABt BEL (bytes 0A 00 05 00 01 00 00 00 'm'); the wheel down at 10,5: ESC _ f2lCgAFAAAA//8AAAAABAAAAE0= BEL (not compact because the high word is used: bytes 0A 00 05 00, buttons 00 00 FF FF, state 0, flags 4, 'M').

## 4. Dependencies

* TvFar2l: the types TF2lStack (Clear, Size, Data, Bad, PushRaw/PushU8/PushU16/PushU32/PushU64/PushStr, PopRaw/PopU8/PopU16/PopU32/PopU64/PopStr); the command constants f2rFeatures 'x', f2rQuickEdit 'e', f2rMaximize 'M', f2rRestore 'm', f2rCursorHeight 'h', f2rMaxSize 'w', f2rNotify 'n', f2rFKeys 'f', f2rPalette 'p', f2rClipboard 'c', f2rImage 'i'; the clipboard sub-commands f2cOpen 'o', f2cClose 'c', f2cEmpty 'e', f2cIsAvail 'a', f2cSetChunk 'S', f2cSetData 's', f2cGetData 'g', f2cGetDataId 'i', f2cRegister 'r'; the image sub-command f2iCaps 'c'; the features F2lFeatCompactInput (1), F2lFeatTerminalSize (2), F2lClipDataId (1), F2lClipChunkedSet (2); F2lGestureMs (5000), F2lGestureExtends (3); F2lAckSeq (ESC _ far2lok BEL); F2lAuthedsFile ('far2l-clipboard-autheds'); the functions F2lBase64Decode, F2lReplySeq (builds the reply string from a stack), F2lSizeSeq(Cols, Rows), F2lKeySeq, F2lMouseSeq (they choose the compact form when nothing is lost), F2lValidClientId, F2lConfigDir, F2lUtf8ToUtf32, F2lUtf32ToUtf8.
* TvClip: cfText (1), cfUnicodeText (13), TClipItem, ClipItem(Format, Data), ClipboardSetItems(array of items), ClipboardGetItem(Format, out Data): Boolean (for the text formats the UTF-8 text), ClipboardHasItem(Format), ClipboardRegisterFormat(Name): LongWord. The test also uses ClipboardGetText and VerticalBlockFormat ('FAR_VerticalBlock_Unicode').
* TvSys: Notify, SetFKeyTitles, ColorBits, WindowMaxSize, WindowMaximize, QuickEdit (the routines that forward to the hooks), and the hook OnSetFKeyTitles (tested for assigned).
* TvScreen: THardwareInfo.GetTickCountMs (milliseconds clock).
* TvEvents: TEvent (What, KeyDown.RepeatCount), evKeyUp, EventUtf16, EventWin32State, EventScanCode, EventVirtualKey, the Win32 control bits wkLeftCtrl, wkRightCtrl, wkLeftAlt, wkRightAlt, wkShift, the mouse masks mbLeftButton, mbRightButton, mbMiddleButton, mwUp, mwDown, mwLeft, mwRight.
* TvKeys: kbShift, kbCtrlShift, kbAltShift (masks of the control key state of the program's own events).
* SysUtils: Trim, FileExists, ForceDirectories, ExtractFileDir, PathDelim and the text file routines.
* For the tests also: TvVt (the emulator TVtEmu: Feed, TakeReply, Resize, Ext - the server), the test helpers MakeKeyEvent, ClearEvent, the keys kbCtrlA, kbLeftCtrl, and the client class TF2lClient of TvFar2l with its Send and WaitReply overridden to talk to the emulator.

## 5. Checks for a test program

The tests drive the server through the emulator (a request fed as an APC string, the answer taken from the reply queue) with a test host that records its calls (clock set by the test, authorised-file in a temporary directory).
* A request before any far2l1 gives no answer (empty).
* ESC _ far2l1 ESC \ followed by ESC [ 5 n gives ESC _ far2lok BEL then ESC [ 0 n (the second part is the emulator's); Active becomes True.
* far2l1 again (ended with BEL) is answered again with ESC _ far2lok BEL.
* An APC "far2l_marker" gives no answer; an empty request "far2l:" gives no answer.
* Cursor height request MmgA: no reply; CursorPercent = 50 and the host got 50.
* GET_WINDOW_MAXSIZE with ID 1 and a host saying 200 by 50: reply ESC _ far2lyAAyAAE= BEL.
* Notification request: no reply; title "Done", text "OK".
* F-key titles request: reply ESC _ far2lAQE= BEL; host titles "Help|Menu|" and ten empty ones.
* CLIP_OPEN with the 32-character client ID and the answer vcaShare: reply ESC _ far2lAwAAAAAAAAABAQ== BEL; the host was asked once with exactly that ID.
* CLIP_SETDATA cfText "hello": status 1, size left 0, data ID equal to VtClipDataId(cfText, 'hello'); ClipboardGetText is 'hello'.
* CLIP_GETDATA cfText before any gesture: size 0 and ID 0, nothing else; after PasteGesture: size 5, the bytes 'hello', then the data ID.
* CLIP_REGISTER_FORMAT for "FAR_VerticalBlock_Unicode" with ID 4: reply ESC _ far2lAMAAAAQ= BEL.
* CLIP_CLOSE with ID 0: no reply.
* IMAGE_CAPS ID 5: base64 of twelve zero bytes and 5; IMAGE_SET ID 6: ESC _ far2lAAY= BEL; IMAGE_TRANSFORM ID 7: ESC _ far2lAAc= BEL.
* Features 1 (compact input) with ID 0: no reply.
* Unknown command 'Z' ID 9: reply ID alone; command 'n' with ID 7 and no arguments: ID alone; 'e' with ID 8: ID alone and QuickEdit called once.
* 'M' then 'm' with ID 0: host maximize once and restore once.
* Palette ID 10 on a 24-bit host: values 24, 0, nothing more.
* F-key titles with only F2 given ("F2", flag 1, flag 0): host titles "|F2|" followed by ten empty ones.
* Features compact + size, ID 0: the result is exactly ESC _ f2lUAAZAFM= BEL (80 by 25). Resize to 100 by 30: the emulator reply queue holds F2lSizeSeq(100, 30). Resize back to 80 by 25 and read the reply. Features compact only: Resize to 90 by 25 gives no size event.
* KeyEvent of 'a' (no modifiers, compact on): ESC _ f2lQQAAYQBD BEL. The same event as evKeyUp: begins with ESC _ f2l and its first popped byte is 'c'.
* MouseEvent(10, 5, left button, 0, False, False, 0): ESC _ f2lCgAFAAEAAABt BEL. MouseEvent(10, 5, 0, mwDown, ...): ESC _ f2lCgAFAAAA//8AAAAABAAAAE0= BEL.
* KeyEvent of Ctrl+A (kbCtrlA, kbLeftCtrl): popped 'C', character 1, a state with $0C bits not 0, VK $41.
* Open for the first time with the host answer vcaShare gives status 1 and the host is asked once; opened again with an ID 21 while open: status 0; the host was not asked again.
* Gesture window: now 200000, PasteGesture; reads at 204000, 208000, 212000, 216000 each give 5 bytes; at 217500 size 0.
* CLIP_GETDATAID without a gesture: 0; after a new PasteGesture: the data ID of 'hello'.
* CLIP_ISAVAIL for cfText: 1.
* CLIP_EMPTY: ClipboardGetText is empty.
* Set cfText "vert" NUL (size 5): status 1; set the vertical-block format with four zero bytes: status 1; text 'vert' and that item both on the clipboard.
* GETDATA cfUnicodeText: 16 bytes; F2lUtf32ToUtf8 of them is 'vert'.
* Set cfUnicodeText with UTF-32 of a Cyrillic 3-letter word (12 bytes of UTF-8 in the test): the text becomes that word and the vertical-block item stays.
* A chunk (256 bytes, count 1) with ID 0: no reply; with ID 34: the reply is the ID alone (ESC _ far2l then base64 of byte 34 then BEL).
* A set of "end" (size 3, cfText) after a 256-byte chunk of 'x': status 1, data ID of (256 'x' + "end"), the clipboard has that text.
* A chunk then a chunk of count 0 then a set of "only": the clipboard text is "only".
* After CLIP_CLOSE: GETDATA cfText gives $FFFFFFFF alone (size of reply after the ID: 0); SETDATA gives status -1 and nothing more.
* CLIP_OPEN with the ID 'short': status 0.
* Answer vcaBlock: open gives 0, and again 0, and the host was asked twice more (total 3).
* Answer vcaRemote: open gives -1. Answer vcaAlways: open gives 1; after close, the file AuthedsPath exists.
* far2l0: Active False and the host's F-key titles are the empty list; a request after it gets no answer.
* After far2l1 again: a client saved in the file is let in without a question (host Asked 0, status 1); a client that was shared only for the previous activation is asked again (status 0 with the answer vcaBlock, Asked 1).
* The host identity: "far2l#user@host" then "far2l#other" (ignored), far2l1, answer vcaShare: open of Cid+'a' gives 1, the host was asked once and the ID it got is "user@host:" followed by the ID, and the file does not let it in.
* With the client class of TvFar2l talking to the server (AuthedsPath empty, answer vcaShare): the activation is acknowledged; registering the vertical-block format gives the same number as the server's ClipboardRegisterFormat; setting [cfUnicodeText, that format] with ['Kolonka' in Cyrillic, 4 zero bytes] puts the text and the item on the clipboard; a get of cfText before a gesture fails; after PasteGesture a get of cfUnicodeText returns the text, a get of the registered format returns the four zero bytes; ClipHas says available; WindowMaxSize returns 200 columns by 50 rows; ColorBits asked returns 24; SetFKeyTitles(['a','b']) shows "a|b|" and ten empty ones.

## 6. Observed oddities

* Features command: the value is stored before the stack is checked, so a features request that is too short (fewer than 8 bytes of value) sets the features to 0 instead of leaving them. Accidental; intended: a short request leaves features unchanged.
* Any side effect done before the stack went bad stays (for example CLIP_OPEN has dropped the pending chunks, the cursor height clamps first). Accepted; only the reply is dropped.
* CLIP_OPEN drops the pending chunks even when the open fails because the clipboard is already open, so it cuts the upload of the open session. Accidental; intended: leave the chunks of an open session alone when the open is refused.
* The clip store function never fails, so the status fail on CLIP_SETDATA cannot be produced. It stays as a reserved path.
* The data ID of CLIP_SETDATA is computed on the data as the client sent it (with its NULs, and for cfUnicodeText over the UTF-32 bytes), while the data ID of CLIP_GETDATA for the same text in cfUnicodeText is computed over the UTF-32 bytes of the clipboard text after UTF-8 conversion; so the two IDs for the same text can differ (a client that caches by ID may fetch again). Accidental; intended: the same text should have the same ID on both sides. Not pinned by tests; an implementer may keep it.
* The extension count is zeroed on close, but the gesture time and the "seen" flag are not, so after a close and a reopen the last gesture still allows reads while it is fresh and 3 further extensions are available. Accidental for the count; the gesture time staying is intended (the gesture belongs to the user, not to the client).
* The gesture is a state of the server, not of a client: another client that opens inside the window can read. Intended (the user pasted for whatever program is running).
* CLIP_ISAVAIL needs neither authorisation nor an open clipboard nor a gesture, so any program in the terminal can see which formats are on the clipboard. Accidental or accepted; the intended result is not decided here.
* CLIP_REGISTER_FORMAT also works without an open clipboard. Intended (it changes nothing).
* A read permission is used up (an extension) even when the format then cannot be fetched. Accepted.
* Stop does not tell the host to restore the cursor height (it only forgets CursorPercent) and does not undo maximize. Accepted; the host that owns the view resets by itself.
* The palette depth is sent as the low 8 bits of what the host returns. Intended (values 4, 8, 24).
* The mouse key state has only left Ctrl and left Alt bits, whatever side the user pressed, and none of the lock keys. Accepted.
* A vertical wheel hides a horizontal one in the same call. Accepted.
* The server does not call Stop when destroyed, so the host gets no F-key clearing then. Accepted; the owner calls Stop first.
* A request whose data is longer than the stack allows (for example a chunk with a count that promises more bytes than exist) is answered with the ID alone and the data is dropped; the status is not an error code. Accepted.
* Key events: a press of every kind but evKeyUp is a press. Intended. A character above $FFFF is sent whole in the long form and, since the compact form needs it below $10000, never in the compact form.
