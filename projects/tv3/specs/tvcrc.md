# Unit TvCrc

## 1. Purpose

TvCrc computes the CRC-32 checksum used by zip, PNG and Ethernet (generator polynomial $04C11DB7, processed in the reflected bit order). The checksum of no data is 0, and a checksum can be continued over further data, so a large input can be processed in parts. The convention is the same as that of `crc32()` in zlib. The checksum of the ASCII text `123456789` is `$CBF43926`.

## 2. Interface

```pascal
unit TvCrc;

interface

function Crc32(Crc: LongWord; const Buf; Len: SizeInt): LongWord;
function Crc32Str(Crc: LongWord; const S: AnsiString): LongWord;
```

There are no types, constants or variables in the interface.

## 3. Behaviour

**Definition.** The CRC is the standard reflected CRC-32: reflected polynomial `$EDB88320`; the running register is initialised from the bitwise complement of the incoming value `Crc`; each data byte is combined with the low byte of the register, the register is shifted right by 8 bits and xor-ed with the table entry selected by that combination; at the end the register is complemented again and returned. The 256-entry table is defined by: entry `b` (0..255) starts as `b`, and 8 times it is shifted right by one bit, xor-ed with `$EDB88320` whenever the bit shifted out was 1. Examples: entry 0 = `$00000000`, entry 1 = `$77073096`, entry 255 = `$2D02EF8D`.

**Crc32(Crc, Buf, Len).** Returns the CRC of the `Len` bytes that start at the address of `Buf` (an untyped parameter: any variable, array element or string character can be passed; its address is used), continuing from the previous value `Crc`. Pass `Crc = 0` to start. `Crc32(Crc32(0, A), B)` equals the CRC of `A` followed by `B`. If `Len` is 0 (or negative; no byte is read) the result equals `Crc` unchanged, and `Buf` is not accessed. There is no maximum length other than the range of `SizeInt`. There are no error conditions and no exceptions; the caller must guarantee that `Len` bytes are readable. Bytes are treated as unsigned 0..255. The routine has no side effects visible to callers except that the lookup table is built lazily on first use; this lazy build is not protected, so the first call must not race with another first call in another thread (afterwards the routine is safe to call concurrently).

**Crc32Str(Crc, S).** The same for the bytes of the string `S`, all `Length(S)` bytes, with no regard for any text encoding. For the empty string it returns `Crc` unchanged.

**Worked examples (all with start value 0):**

| Input | Result |
|---|---|
| empty string | `$00000000` |
| `'a'` | `$E8B7BE43` |
| `'123456789'` | `$CBF43926` |
| `'The quick brown fox jumps over the lazy dog'` | `$414FA339` |
| `'MICROSOFT'` | `$795B3767` |
| `'BORLAND'` | `$4DF4784C` |
| the 256 bytes 0,1,...,255 | `$29058C73` |
| `Crc32Str(Crc32Str(0,'The quick brown '),'fox jumps over the lazy dog')` | `$414FA339` |
| `Crc32(7, anything, 0)` | `7` |

## 4. Dependencies

Library units: none. Standard units: none (the unit only needs the system unit). The common conditional-definitions include file of the library is included by every unit and has no effect on the interface.

## 5. Checks for a test program

- `Crc32Str(0,'') = 0`; `Crc32(7, Buf, 0) = 7`.
- All values of the table above.
- Splitting any input at any point and chaining gives the same result as one call (try several split points, including at 0 and at the end).
- `Crc32` over a buffer and `Crc32Str` over the same bytes agree; `Crc32` over the characters of a ShortString (`Sh[1]`, `Length(Sh)`) gives the same as for the AnsiString.
- Bytes of `$80` and above are handled as unsigned (the 256-byte test).
- `Crc32Str(5,'')=5` (continuation value is kept for empty input).
