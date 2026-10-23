# Unit TvIni - functional specification

## 1. Purpose

TvIni reads, edits and writes INI files while keeping everything the user wrote: comments, blank lines, order, spacing, quoting and line ends of every line that the program did not change. The program sees sections and entries (tag = value, with an optional trailing comment); a line that is not an entry (comment, blank line, any text) is kept verbatim as a pseudo-entry of its section. Tags and section names are compared without regard to case (UTF-8 aware). Values are plain byte strings; UTF-8 passes through unchanged. A file can be read from disk, written back through a temporary file, or handled as text in memory (for tests). All classes are single-threaded: no locking, no sharing between threads.

Terms: a *line* is the text between line ends (CR LF or LF), without the line end. An *entry line* is a line that is parsed as `Tag=Value`. The *main section* is the section called `MainSection` that holds the lines before the first `[Header]`.

## 2. Interface

```pascal
unit TvIni;

interface

type
  TIniEntry = class
  public
    constructor Create(const ALine: AnsiString); overload;
    constructor Create(const ALine: AnsiString; ARaw: Boolean); overload;
    constructor Create(const ATag, AValue, AComment: AnsiString; ARaw: Boolean = False); overload;
    function GetText: AnsiString;
    function GetTag: AnsiString;
    function GetValue: AnsiString;
    function GetComment: AnsiString;
    procedure SetValue(const S: AnsiString);
    procedure SetComment(const S: AnsiString);
    function IsEntry: Boolean;       { False for an empty line or a comment line }
  end;

  TIniSection = class;

  PIniEntry = TIniEntry;
  PIniSection = TIniSection;

  TIniEntryEnumProc = procedure(P: PIniEntry) is nested;
  TIniSectionEnumProc = procedure(P: PIniSection) is nested;

  TIniSection = class
  public
    constructor Create(const AName: AnsiString; ARaw: Boolean = False);
    destructor Destroy; override;
    function GetName: AnsiString;
    function AddEntry(const S: AnsiString): PIniEntry; overload;
    function AddEntry(const Tag, Value, Comment: AnsiString): PIniEntry; overload;
    function SearchEntry(const Tag: AnsiString): PIniEntry;
    procedure DeleteEntry(const Tag: AnsiString);
    procedure ForEachEntry(EnumProc: TIniEntryEnumProc);
    function Count: Integer;
    function Entry(I: Integer): PIniEntry;
  end;

  TIniFile = class
  public
    MakeNullEntries: Boolean;
    InlineComments: Boolean;
    constructor Create(const AFileName: AnsiString);
    destructor Destroy; override;
    function GetFileName: AnsiString;
    function Read: Boolean;
    function Update: Boolean;
    function IsModified: Boolean;
    procedure LoadFromText(const Text: AnsiString);
    function SaveToText: AnsiString;
    function SearchSection(const Section: AnsiString): PIniSection;
    function SearchEntry(const Section, Tag: AnsiString): PIniEntry;
    procedure ForEachSection(EnumProc: TIniSectionEnumProc);
    procedure ForEachEntry(const Section: AnsiString; EnumProc: TIniEntryEnumProc);
    function GetEntry(const Section, Tag, Default: AnsiString): AnsiString;
    procedure SetEntry(const Section, Tag, Value: AnsiString); overload;
    procedure SetEntry(const Section, Tag, Value, Comment: AnsiString); overload;
    function GetIntEntry(const Section, Tag: AnsiString; Default: LongInt): LongInt;
    procedure SetIntEntry(const Section, Tag: AnsiString; Value: LongInt);
    function GetBoolEntry(const Section, Tag: AnsiString; Default: Boolean): Boolean;
    procedure SetBoolEntry(const Section, Tag: AnsiString; Value: Boolean);
    function EntryExists(const Section, Tag: AnsiString): Boolean;
    procedure DeleteSection(const Section: AnsiString);
    procedure DeleteEntry(const Section, Tag: AnsiString);
    function SectionCount: Integer;
    function SectionAt(I: Integer): PIniSection;
  end;
  PIniFile = TIniFile;

const
  MainSectionName = 'MainSection';
  CommentChar = ';';

function IniQuote(const S: AnsiString): AnsiString;
```

The private parts (fields, `Parse`, `IndexOf`, `AddSection`) are not part of the interface; the unit needs them only as described below. The `P` names are aliases kept for old programs (classes are references, so `PIniEntry` is the class itself). The enumeration callbacks are declared `is nested` (the Free Pascal modifier), so a nested procedure of the caller can be passed with `@`. The source uses mode objfpc.

## 3. File format

* `[Name]` on a line (after trimming white space at both ends; at least the two bracket characters) starts a section. The name is the text between the brackets, trimmed.
* Lines before the first header go to the section `MainSection` (created on the first such line, even if it is a blank line). If the text starts with a header there is no main section.
* `Tag=Value ;Comment` is an entry. Everything else is a line that is not an entry.
* A text is split at LF; a CR immediately before the LF is removed (and noted, see 5.3). A final line without a line end is still a line. A text that ends with a line end gives no extra empty line at the end. A lone CR is not a line end.
* A UTF-8 byte order mark (EF BB BF) at the very start is removed on reading and written back on saving.

## 4. TIniEntry

An entry object is either an entry (`IsEntry` True) or a kept line. It remembers the *original text* of the line it was parsed from; once the value or comment is changed, the text is generated anew.

**Parse of a line** (constructors taking a line; `ARaw` selects raw mode, default False, the one-argument constructor is the same as `ARaw = False`):

1. Let P be the position of the first `=`, I the position of the first `;`. The line is *not* an entry (it is kept, tag/value/comment empty, original text = the line) when there is no `=`, or a `;` comes before the first `=`, or the text before the `=` is empty after trimming white space. So `; a=b` and `x;y=1` are not entries; `=v` is not an entry.
2. Otherwise tag = text before the first `=`, trimmed (spaces inside the tag are kept). The original text is the whole line.
3. Raw mode: value = everything after the first `=` (not trimmed, `;` is no comment, comment stays empty); if the value has two or more characters, starts with `'` or `"` and ends with the same character, those two quote characters are removed (the inside is not unescaped). 
4. Normal mode: skip white space (bytes <= space) after `=`. If the next character is `'` or `"` it is the delimiter and the value is quoted: it ends at the next delimiter not followed by another delimiter; a doubled delimiter inside stands for one delimiter. Text after the closing quote up to the next `;` is dropped. An unterminated quote runs to the end of the line (the value is the rest, no comment). When the value is not quoted, it runs up to the first `;` (anywhere, including in the middle of a word), and is then trimmed at both ends; a quote character in the middle of an unquoted value is an ordinary character. A quoted value is not trimmed. The comment is the text after the `;` that ended the value, without the `;`, otherwise unchanged (a leading space is part of it); no `;` means an empty comment. A `;` inside quotes is part of the value.

**Constructor `Create(ATag, AValue, AComment, ARaw)`** makes an entry with these fields and no original text (it is written by the generator below).

**GetText**: the original text if the entry has not been changed since parsing; otherwise, for a non-entry the empty text; for a raw entry `Tag=Value` (comment dropped); else `Tag=` + `IniQuote(Value)` and, when the comment is not empty, a space, `;` and the comment. Example: tag `Count`, value `6` gives `Count=6`; with comment `the masks` and value `*.pas;*.pp` gives `Count='*.pas;*.pp' ;the masks`.

**GetTag / GetValue / GetComment**: the fields (empty for a non-entry).

**SetValue(S)**: nothing happens when the entry is an entry and the value is equal to S (so the original text, with its spacing and quoting, survives). Otherwise the value is replaced, the object becomes an entry and its original text is forgotten.

**SetComment(S)**: nothing happens when the entry is an entry and the comment equals S; otherwise the comment is replaced and the original text is forgotten.

**IsEntry**: True for entries.

**IniQuote(S)**: the text to put after `=`. S is returned unchanged unless it needs quotes: S is not empty and its first or last byte is <= space or its first byte is `'` or `"`; or S contains a `;` or any byte < space anywhere. The empty text needs no quotes. When quoting, the delimiter is `'`, except `"` when S contains a `'`; every delimiter inside S is doubled; the result is delimiter + text + delimiter. Examples: `abc` -> `abc`; `a;b c` -> `'a;b c'`; `x'y;z` -> `"x'y;z"`; `  pad ` -> `'  pad '`; `it's` -> `it's` (a quote in the middle needs nothing).

## 5. TIniSection

Holds the entries of one section in file order, including the non-entry lines. Owns its entries (frees them in the destructor).

**Create(AName, ARaw)**: ARaw is given to every entry that is parsed from a line later.

**GetName**: the name as it was written first (case kept).

**AddEntry(S)**: appends a new entry object parsed from the line S (raw as the section is); returns it. **AddEntry(Tag, Value, Comment)** appends an entry made from the fields. No check for duplicates. Neither marks the file modified (the file is not known to the section).

**SearchEntry(Tag)**: the first *real entry* (not a kept line) whose tag equals Tag in the case-insensitive sense (`U8Lower` of both); nil when none.

**DeleteEntry(Tag)**: removes and frees the first such entry; nothing when none. Later entries move up.

**ForEachEntry**: calls the callback for each real entry in order; kept lines are skipped. Changing the section's entry list during the enumeration is not allowed.

**Count**: number of objects including kept lines. **Entry(I)**: the I-th object, 0-based; I outside 0..Count-1 is a caller error (no check required).

## 6. TIniFile

State: the list of sections (file order), a modified flag, whether a BOM was read, whether line ends are CR LF. Owns the sections.

**Create(AFileName)**: no file access. `InlineComments` is True, `MakeNullEntries` False; the line end style starts as the platform default (LF on Unix-like systems, CR LF elsewhere). Empty file name is allowed (memory-only INI).

**InlineComments**: public field; set it before `Read`/`LoadFromText` (and before the first `SetEntry` that creates a section). False selects raw mode (the Windows profile way) for the sections created afterwards: the value is everything after `=`, `;` in a value is no comment, `SetEntry` does not quote and keeps no comment.

**MakeNullEntries**: public field; when True a read of a missing tag adds it to the file with the default (see GetEntry).

**GetFileName**: the name given to the constructor.

**LoadFromText(Text)**: discards all sections and loads the text as described in section 3. Detects the BOM; determines the line end style: starts from the platform default, then each line that was ended by CR LF sets CR LF and each line ended by a bare LF sets LF, so the style of the *last terminated line* wins; a last line without line end does not change it. Clears the modified flag. Section headers are recognized after trimming; two headers with the same name make two sections (lookups find the first). An empty text gives zero sections.

**SaveToText**: the BOM (if one was read), then for each section in order: the header line `[` + name + `]` (the name as stored, spacing normalised), then the text of every object of the section (`GetText`), every line ended with the stored line end (CR LF or LF). The header is omitted only for the first section when its name equals `MainSectionName` exactly. Consequences: saving what was read gives the same text when headers were written without extra spaces and the last line had a line end; a final line without a line end gets one.

**Read**: False when the file name is empty (nothing else happens). Opens the file for reading; if it cannot be opened the content becomes empty (as `LoadFromText('')`) and the result is False. Otherwise reads all bytes, loads them with `LoadFromText` and returns True (also for an empty file). The modified flag is False afterwards. The file must be opened read-only locally, without changing any global file mode.

**Update**: True without doing anything when the file name is empty or nothing was modified. Otherwise `SaveToText` is written to a temporary file in the same directory, then the temporary file replaces the real one. The temporary name is the file name with its extension replaced by `.tmp` (a name without extension gets `.tmp`), or by `.$$$` when the extension already is `.tmp` (compared without case); that gives one dot, so the name also fits DOS 8.3. Returns False if the temporary file cannot be created or written, or the rename fails (the modified flag then stays True). On success the modified flag is cleared and True is returned. At no moment may the real file contain a half-written text: the new content replaces the old by rename (a platform whose rename does not replace an existing file deletes the old file first).

**IsModified**: the flag. It is set by `SetEntry` when the file text would change, by `DeleteSection`, and by `DeleteEntry` that found a tag; it is not set by direct changes made through an entry or section object obtained from the file, nor by the reading routines (except `MakeNullEntries` additions).

**SearchSection(Name)**: the first section whose name equals Name, case-insensitively (`U8Lower`), or nil. **SearchEntry(Section, Tag)**: nil if the section or the tag is missing. **ForEachSection**: all sections in order, including the main one. **ForEachEntry(Section, proc)**: real entries of the section in order; nothing for a missing section.

**GetEntry(Section, Tag, Default)**: the value of the first matching entry without quotes. If the tag is missing the result is Default, and when `MakeNullEntries` is True the tag is also added with `SetEntry(Section, Tag, Default)` (so an empty default is written as `Tag=` and the file is marked modified).

**SetEntry(Section, Tag, Value)**: as the four-argument form with the comment the entry has now (or empty for a new one). **SetEntry(Section, Tag, Value, Comment)**:
* tag missing: if Value is empty and `MakeNullEntries` is False nothing is written (not even the section). Otherwise, if the section is missing it is created at the end with the name as given; before a new section, if the file has sections and the last object of the last section has a non-blank text, an empty line is appended to that last section as a separator. The entry is appended at the end of the section's objects (after trailing blank lines and comments), and the file is marked modified.
* tag present (first match): the text it would have is compared before and after setting value and comment; only if the text differs is the file marked modified. Setting the value that is already there, with the same comment, leaves the original line untouched (spacing, quoting, comments). A changed entry is written as `Tag=value` (quoted by `IniQuote` when needed, unless raw) plus ` ;comment`; the tag keeps the case it had. In the three-argument form the existing comment is kept; in the four-argument form an empty Comment removes it.

**GetIntEntry(Section, Tag, Default)**: the value is trimmed and converted by the system's string-to-integer-with-default routine (decimal with optional sign; hex with `$`/`0x` prefix as that routine accepts); the default is returned when the tag is missing, empty or not a 32-bit integer. A missing tag is read with the decimal text of Default as its default, so with `MakeNullEntries` the number is added. **SetIntEntry**: `SetEntry` with the decimal text.

**GetBoolEntry(Section, Tag, Default)**: the value trimmed and lower-cased: `1`, `true`, `yes`, `on` give True; `0`, `false`, `no`, `off` give False; anything else (including missing or empty) gives Default. A missing tag is read with the empty text as its default. **SetBoolEntry**: writes `1` or `0`.

**EntryExists**: True when `SearchEntry` is not nil. **DeleteSection**: removes and frees the first section of that name and marks modified; nothing otherwise. **DeleteEntry(Section, Tag)**: removes the first entry and marks modified when found. **SectionCount**, **SectionAt(I)** (0-based, I in range is a caller condition).

## 7. Units used

* `TvUStr` (implementation): `U8Lower(S)`, the UTF-8 aware lower-casing, for all case-insensitive comparisons of tags, section names and boolean words.
* `SysUtils` (implementation): trimming, integer-to-text and text-to-integer-with-default, file existence/deletion/rename, extension handling (`ExtractFileExt`, `ChangeFileExt`, `CompareText`), plus the Pascal untyped-file routines for reading and writing the whole file.
* Compiler mode objfpc with long strings.

## 8. What the tests pin down (t_ini)

A fixed text with a comment line, `Comment=Do NOT delete`, an empty line, `[Files]` with `OpenExts='*.pas;*.pp' ;the masks`, `Count = 5`, `; between`, `Name="it's"`, and `[Other]` with `Flag=1` (all LF terminated):
* three sections; the entry before the first header is in `MainSection`; quoted value keeps its `;`; the comment after a quoted value is `the masks`; tag and section lookup ignore case and spaces around `=`; a doubled quote is one quote; missing tag gives the default; boolean reading; reading does not set modified; `SaveToText` returns exactly the original text.
* `SetEntry` with the same value is not a change; `SetIntEntry('Files','Count',6)` is, and the saved text then contains `Count=6` plus LF, the other lines (`OpenExts=...;the masks` line and `; between`) unchanged.
* A value `a;b c` is saved as `Path='a;b c'`; `x'y;z` as `Q="x'y;z"`; `  pad ` survives; all three read back identically after `LoadFromText(SaveToText)`.
* New section and entry; an empty value of a missing tag is not written; `DeleteEntry`, `DeleteSection`; `ForEachEntry` skips kept lines; `ForEachSection` visits `SectionCount` sections; `MakeNullEntries` adds the tag on read.
* CR LF text round-trips with CR LF; BOM is skipped on read and written back; UTF-8 value passes unchanged.
* Raw mode (`InlineComments := False`): `Cmd=a -r ; b` value is the whole `a -r ; b`; `Q='x'` gives `x`; a new `p;q` is written as `New=p;q` (CR LF kept).
* File: missing file `Read` False; after `SetEntry` `Update` True and `IsModified` False; a new object reads it back (`Read` True, value 1).

Further checks a test program should make: the oddities below that are marked intended; the header/BOM/blank-line separator cases; case-insensitive lookup of non-ASCII (Cyrillic) tags; `GetBoolEntry` words; `Update` with a name ending in `.tmp`; `Update` with an empty file name returns True and writes nothing.

## 9. Observed oddities

Intended (keep):
* Unchanged lines are written back byte-for-byte; a changed line is normalised (`Tag=Value ;comment`, original spacing lost).
* Duplicate tags and duplicate sections are kept in the file; lookups and changes act on the first one.
* A new tag is appended at the end of its section, after trailing blank/comment lines.
* Header lines are rewritten as `[Name]` (inner spaces trimmed); the main section header is never written for the first section.
* The line end style of the last terminated line wins for the whole file; a missing final line end is added.
* Text after a closing quote (before the `;`) is dropped when the line is parsed, but only matters if the entry is changed.

Accidental (do not copy; the intended choice is stated):
* `Read` sets the global file mode to read-only and does not restore it. Intended: no global side effect.
* `Update` deletes the old file before renaming, so a crash between the two steps loses the file, against the purpose of the temporary file. Intended: replace by rename where the system can.
* `GetBoolEntry` reads a missing tag with the empty default, so under `MakeNullEntries` an empty `Tag=` is added instead of the default value. Intended: write the text of the default (`1`/`0`).
* `SetValue` on a kept line (reachable only through `Section.Entry(I)`) makes an entry with an empty tag that is written as `=value`; `SetComment` on a kept line wipes its text (it becomes an empty line). Intended: both do nothing on a kept line.
* A value containing a line break or other control byte is quoted but written with the raw control bytes, which breaks the file. Intended: leave as is (callers must not store such values); not tested.
* A header that is a line like `[A] ; note` is not recognised (it does not end in `]`) and is kept as a line of the previous section.
* A file that starts with an explicit `[MainSection]` header loses the header on saving (the content is equivalent).
* When the temporary file cannot be completed it is left on disk.
