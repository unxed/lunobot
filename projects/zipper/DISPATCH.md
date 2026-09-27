# zipper DISPATCH log

## 2026-09-27 — unxed/zipper#22 "unxed/sevenzip: support original 7-zip header compression"

- Ticket title (from `gh issue view`) differs from TRIAGE paraphrase: actual title is
  "[Feature] unxed/sevenzip: support original 7-zip header compression". Body:
  "Improve the header compression routines to ensure exact compatibility with the
  various header compression levels produced by different versions of the official
  7-Zip archiver."
- Cloned fresh unxed/zipper (default branch main) and unxed/sevenzip (default branch
  `write`, which is what zipper's go.mod pins via `github.com/unxed/sevenzip v0.1.7`,
  matching the tip of `write`). There is a separate stale `main` branch in sevenzip
  that is NOT what's consumed -- ignored it.
- Read sevenzip's writer.go/write_struct.go/reader.go/struct.go/types.go/register.go.
  Findings:
  - Writer.Close() ALWAYS wrote the archive Header in the clear (`idHeader`/0x01),
    or, when a password is set, only AES-encrypted the raw header bytes (no LZMA2
    step at all) -- unlike original 7-Zip/p7zip, which compress the header by
    default (EncodedHeader / 0x17).
  - The READ side was already fully generic/coder-agnostic (register.go registers
    LZMA, LZMA2, BCJ*, AES, deflate, bzip2, zstd, brotli, lz4, ppmd decompressors,
    and reader.go's idEncodedHeader case reuses the exact same folderReader used for
    file data). This is inherited from upstream bodgit/sevenzip and is exercised by
    real-world .7z files routinely, so decode-side "compat with headers compressed
    by various 7-Zip versions" already existed. The actual gap was purely on the
    WRITE side: zipper-produced .7z archives never had compressed headers at all.
  - zipper itself doesn't call sevenzip.NewWriter directly; 7z creation goes through
    unxed/archives' `archives.SevenZip{}` (archives/7z.go), which does call
    `sevenzip.NewWriter(ws, WithSolid, WithPassword, WithConcurrency)`. Since header
    compression was implemented as unconditional default behaviour inside
    Writer.Close() (no new WriterOption), no changes were needed in unxed/archives
    or unxed/zipper -- bumping the sevenzip dependency version is enough once the PR
    lands (not done yet, out of scope for this atomic step; sevenzip PR needs to
    merge/tag first).
- Verdict: atomic, well-scoped (~150 line diff in one file + tests), implemented in
  full in this pass.
- Implementation (unxed/sevenzip, branch
  `lunobot/e2d630e0524e1c081b5e1572/lunobot-3/22-7z-header-compression`, PR
  https://github.com/unxed/sevenzip/pull/8, base `write`):
  - Added `compressHeaderLZMA2([]byte) (byte, []byte, error)` helper reusing the
    existing getLZMAWriter/putLZMAWriter pool, sizing the LZMA2 dictionary to the
    header via the same EncodeDictCap/DecodeDictCap round-trip already used
    elsewhere in CreateHeader.
  - Writer.Close() now always LZMA2-compresses the Header bytes and writes them out
    as an EncodedHeader (0x17). When `w.password != ""`, the compressed bytes are
    additionally AES-encrypted, using a 2-coder folder (AES -> LZMA2 via a bind
    pair) that mirrors the exact coder chain already used for encrypted file data.
  - No reader.go/struct.go/types.go changes needed (confirmed the generic decoder
    already understands both new coder-chain shapes).
- Test (added, not run locally per no-local-builds policy -- CI on the PR will run
  `go test ./...`):
  - `TestWriterHeaderIsCompressed`: writes 200 files with a repetitive-name header,
    manually re-parses the raw file (signature header -> start header -> NextHeader
    id byte -> readStreamsInfo) to assert the id is `idEncodedHeader`, the folder's
    coder is LZMA2 (`0x21`), and the packed size < the unpacked size. Also
    round-trips through `OpenReader`.
  - `TestWriterHeaderIsCompressedAndEncrypted`: same with `WithPassword`, asserts a
    2-coder AES+LZMA2 folder with a bind pair, round-trips through
    `OpenReaderWithPassword`.
  - Existing TestWriterBasic/TestWriterSolid/TestWriterEncrypted now also exercise
    the new default path as regression coverage.
- Commented on unxed/zipper#22 with findings + PR link, signed Lunobot-3.
- Did NOT poll CI after pushing/commenting, per process note.

### Follow-ups (not done, left for a later pass)
- Bump `github.com/unxed/sevenzip` in unxed/zipper's go.mod once PR #8 merges and a
  new sevenzip tag is cut, so zipper-produced .7z archives actually pick this up.
- Sibling ticket unxed/zipper#21 ("support Zstandard (zstd) header compression")
  is a related but separate, algorithm-choice feature -- not touched here.

27-09-2026 18:35:00 Я Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), взял кастомную задачу «unxed/sevenzip (write): Coverage workflow красный — реальные упавшие тесты после мержа #7+#8, плюс покрыть недостающее по явной просьбе владельца» по § 10 [urgent: § 10 — прямая просьба владельца, покрытие явно разрешено на этот раз]
