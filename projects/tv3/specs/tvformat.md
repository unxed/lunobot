# Unit TvFormat

## 1. Purpose

TvFormat provides `FormatStr`, which builds a short text from a format string and an array of arguments using the rules of the `Format` function of the standard SysUtils unit, and returns it as a ShortString (limited to 255 characters).

## 2. Interface

```pascal
unit TvFormat;

interface

{ SysUtils.Format with Args, cut at 255 characters. }
function FormatStr(const Fmt: ShortString; const Args: array of const): ShortString;
```

## 3. Behaviour

**FormatStr(Fmt, Args).** The result is the text that `SysUtils.Format(Fmt, Args)` produces (all conversion specifiers, widths, precisions, left-justification `-`, index specifiers and `*` widths of that function work identically), converted to a ShortString. If the formatted text is longer than 255 characters (bytes), the first 255 are kept and the rest is silently discarded; no error is raised for this. A format without specifiers returns the format itself (`'no items'` gives `'no items'`); an empty format gives the empty string. Arguments of the types allowed by `array of const` are accepted, including ShortString, AnsiString, string literals and integers. Errors in the format or arguments (for example a specifier that does not fit the argument type, or too few arguments) are not caught: the exception that `SysUtils.Format` raises (for instance `EConvertError`) propagates to the caller. There are no side effects; the function is thread safe to the extent that `SysUtils.Format` is. Cutting is by bytes and may split a multi-byte character; no repair is attempted.

**Examples:**

| Fmt, Args | Result |
|---|---|
| `'%s=%d'`, `['n', 5]` | `n=5` |
| `'name %s, %d items'`, `[A, 42]` with `A` a ShortString `file` | `name file, 42 items` |
| `'[%5d][%-4s]'`, `[7, 'ab']` | `[    7][ab  ]` |
| `'no items'`, `[]` | `no items` |
| `''`, `[]` | empty |
| `'%s'`, `[300 times 'a']` | 255 times `a` (length 255) |

## 4. Dependencies

Library units: none. Standard units: SysUtils (implementation only).

## 5. Checks for a test program

- Every row of the table above.
- A result of exactly 255 characters is returned unchanged, 256 is cut to 255 and the first 255 characters are the first 255 of the full text.
- `FormatStr(f, a)` equals `SysUtils.Format(f, a)` for a handful of shorter formats (`%x`, `%.2f`, `%%`, `%e`).
- A bad specifier such as `FormatStr('%d', ['x'])` raises an exception (do not rely on its precise class beyond it being an exception of SysUtils.Format).
