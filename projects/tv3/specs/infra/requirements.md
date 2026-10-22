# Specification: the infrastructure of the repository unxed/tv3-new

The repository will hold tv3, a class-based Free Pascal library for text user interfaces whose units translate
magiblot/tvision and magiblot/tvterm. This specification lists what the infrastructure around the library must be:
the rules, the audit, the provenance records, the verdict, the text rules, the test harness, CI and the documents.
No unit of the library is part of it. Every text of the repository is English and neutral (section 8).

## 1. Files and history

- History: a new root (an orphan branch). Its first commits, one file each, in this order: `COPYRIGHT.magiblot`,
  `COPYRIGHT.tvterm`, `LICENSE`; then the infrastructure in several commits, each a meaningful group with the
  provenance records of its files.
- `COPYRIGHT.magiblot`: the file `COPYRIGHT` of magiblot/tvision at b4831e2ca16652db327fb7cc964f1c8c2d512524, byte for
  byte (git blob a200eaeb79f6095c5c8dcbc4f41b2f17267ec1da). `COPYRIGHT.tvterm`: the file `COPYRIGHT` of
  magiblot/tvterm at 210eb23564da06c358d2623388939bb02f7f3419 (blob f591b9c81a1890b9cc9676ef809670ac4a4d57cc).
- `LICENSE`: a section "Scope" saying that the license covers every file except a file whose header says
  "Translated from magiblot/tvision @ <commit>" (under COPYRIGHT.magiblot: the disclaimer of Borland International and
  the MIT license of magiblot) or "Translated from magiblot/tvterm @ <commit>" (under COPYRIGHT.tvterm, the MIT
  license of magiblot/tvterm); then the standard MIT License text with the line
  "Copyright (c) 2026 the authors of tv3 (see the history of the repository)".
- Commit identity: author and committer `tv3 maintainers <tv3-maintainers@users.noreply.github.com>`. Messages say
  what was done, in a neutral tone, with no trailers.

## 2. CLAUDE.md: the rules of the repository

Rules that hold for every file of the tree and every commit of the history and win over any other document:

1. Outside sources: magiblot/tvision at b4831e2, magiblot/tvterm at 210eb23 (its own include/ and source/, not the
   libraries it builds on such as libvterm), VTExts.md (branch extsdocs of unxed/far2l, the specification of the
   far2l terminal extensions), the documents of standards in tools/audit/facts/. A file follows an outside source only
   when its provenance record names it.
2. No code of another implementation of Turbo Vision, of Free Vision or another package of Free Pascal, of the Free
   Pascal IDE, of DOS Navigator or of far2l, in any form, in the tree or the history. The far2l extensions follow
   VTExts.md only.
3. No statement about the origin of code in code, comments, documents or commit messages (examples: "written from
   scratch", "not copied", "our own code", "nothing is taken from", "after X"). Required instead, as the only
   statements of origin: (a) the notice "Translated from magiblot/tvision @ <commit>" or "Translated from
   magiblot/tvterm @ <commit>" with the list of C++ sources and a pointer to COPYRIGHT.magiblot or COPYRIGHT.tvterm;
   (b) provenance/ with a record of facts for every file, checked by tools/audit/provenance_lint.py; (c)
   docs/CLEANROOM.md, the protocol; (d) VERDICT.md, the output of tools/audit/verdict.py, written by CI only.
4. Neutral text: the repository describes the code, its rules and how they are checked, as they are; it does not
   refer to the process that produced a change, to the tools or services of that process, to discussions or to the
   reasons of past decisions. tools/text_lint.py checks it.
5. The audit as in section 3, with its numbers; a match is accepted only when tools/audit/prove.py proves it; any
   other match is made again from the allowed sources.
6. The CI job verdict runs on every pull request and on main; a file without a complete record, or an unproved
   match, fails it.
7. LICENSE, COPYRIGHT.magiblot, COPYRIGHT.tvterm and the notices of files change only by a decision of the owner of
   the repository.
8. Something in violation is removed from the tree and the history and made again by docs/CLEANROOM.md; a loss of
   function is acceptable until then, a violation is not.

## 3. The audit (tools/audit/)

### 3.1 Corpora

A script fetches into a cache directory outside the repository (default `~/.cache/tv3-corpora`, overridable by the
environment variable CORPORA) and writes there a list of reference files and a list of allowed files. Every fetch is
pinned and retried a few times on a network error. A git corpus is the tree of one commit (shallow fetch of that
commit; sparse paths where given).

References (code that must not be in the repository):

| name | where | pin | files |
| --- | --- | --- | --- |
| fpc322 | https://github.com/fpc/FPCSource | 0d122c49534b480be9284c21bd60b53d99904346 | packages/fv, packages/ide, packages/fcl-base, packages/rtl-objpas, packages/fcl-passrc |
| fpcmain | https://github.com/fpc/FPCSource | 82197d8f98e073779c633fc7ef5b9592bb93016b | the same paths |
| fpide | https://github.com/unxed/bp | 2d6891b9983b65a184ccba7d7e851231b820af3e | fpide |
| tvdelphi | https://github.com/MikeFalcon77/turbovision-delphi | 6c6f66ad4c3e37a1daea9ae28449e11802a994b0 | all |
| far2l | https://github.com/elfmz/far2l | 5ec2011794fa0c781e6dde92c84c77b5ae02b25b | all |
| sigala | https://github.com/benwbooth/tvision | cb0849252a43be9d81ee8fa54519f778fad1a599 | all |
| jserv | https://github.com/jserv/tvision | 3537200715baf7de7c61c9ebbb639373b7a6b1ac | all |
| rhtv | https://github.com/set-soft/tvision | 197ea6801a98faacb82d0456201d73c5a3ea5dfa | all |
| tv20 | https://github.com/FSharpCSharp/TurboVision | b73b2ed7672df5d8f789c309076752ddee1c8adf | all |
| dn214 | https://web.archive.org/web/20220202202636if_/http://www.dnosp.com/files/dn2/dn2s214.rar | SHA-256 4b8feadac86780f615d4b2a7847d81ad41f551c1962c9dd58b721806f36608c3 | the whole RAR archive |
| dn151 | https://web.archive.org/web/20250406173244if_/https://download.ritlabs.com/dn/dn151src.zip | SHA-256 d2d12bad4a040e751d5a6f4186a8caabd5ba8b3540e3dc7cab69a58a4f210440 | the whole ZIP archive |
| bp7tv | https://web.archive.org/web/20231211134715if_/http://old-dos.ru/dl.php?id=9670 (a RAR archive) | SHA-256 1ba6251209ae4a56a4f6ce5926bff0eca815ea53a3dd5f57f779d52d1e1dc2fc | the *.pas files of the inner ZIP archives BPASCAL.700/D11/TVSRC.ZIP, BPASCAL.700/D11/TVDEMO.ZIP, BPASCAL.700/D8/TVFM.ZIP, BPASCAL.700/D12/TVDEBUG.ZIP, and rtl/tv/*.pas and rtl/common/objects.pas of _UPDATE_/BP_OBJEC.701/2/BP7ETC.ZIP (names of the inner archives in any letter case) |

Allowed sources: magiblot/tvision at b4831e2ca16652db327fb7cc964f1c8c2d512524 (include/, source/), magiblot/tvterm at
210eb23564da06c358d2623388939bb02f7f3419 (include/, source/), unxed/far2l at 8030902caf42498e1612e5a393ab7fc489048f51
(VTExts.md), and every *.md under tools/audit/facts/ of the repository.

Code files of a corpus: Pascal (.pas .pp .inc .lpr .dpr) and C/C++ (.c .cc .cpp .cxx .h .hh .hpp), extensions in any
letter case.

### 3.2 Comparisons

Tokens: comments and layout do not count; identifiers and keywords compare without letter case; numbers by value
(decimal, Pascal $hex %bin &oct, C 0x and octal and suffixes); a character literal and a string of one character
are the number of the character; a longer string is its text. A Pascal routine heading (procedure, function,
constructor, destructor, operator up to its semicolon, with the directives after it) is one token that matches
nothing, so a repeated signature never makes a chain. Files that are neither Pascal nor C/C++ are read as plain text
tokens (words, numbers, quoted strings, punctuation).

Three comparisons, with these parameters (the one profile of the repository):

- raw: the tokens of a file against the Pascal references; a chain of 16 tokens or more in common is a match.
- ren: the same with every identifier made one token and every literal another; a chain of 60 tokens or more in
  common, of which at least 40 % are identifiers and keywords, is a match.
- lit: the literals of a file alone against the C/C++ references; a run of 12 literals or more in common is a match
  when it has 6 different significant values (numbers of 32 and more, strings of two characters and more) and is not
  a count (most neighbours one apart). A Pascal routine heading breaks a run.

A window (16, 60 or 12 consecutive tokens) that also occurs in an allowed source does not count (for documents of
standards: their numbers and quoted texts, in the literal comparison). Consecutive windows in common make one match;
a match is identified by the SHA-256 of its tokens, its comparison and the path of the file.

Scope: every version of every tracked file in the history of HEAD (each distinct blob once), all files of the
repository (code, tests, tools, documents). Output: a JSON report (profile, list of corpora present, number of
references, head commit, scope, every match with its tokens, lines, reference file, whether it is proved, invalid
proofs, pass) and the line AUDIT PASS or AUDIT FAIL; exit code 0 or 1. tools/audit/run.sh runs the corpora script and
the audit with the numbers above fixed in it.

### 3.3 Proofs (tools/audit/proofs.txt, tools/audit/prove.py)

A line: comparison, window (SHA-256), path, proof; tab separated. A proof is one of:

- `translation SOURCE:FILE:A-B[,SOURCE:FILE:A-B...]` with SOURCE magiblot/tvision or magiblot/tvterm: holds when
  every identifier and every literal of the match occurs among the tokens of those lines of the allowed file
  (identifiers in any letter case, literals by value);
- `api`: holds when the match is only keywords, punctuation and names written in backticks in docs/API-NAMES.md, and
  no literal.

Keywords, punctuation and a fixed list of the predeclared identifiers of Pascal (Result, Self, Exit, Inc, Dec, Ord,
Chr, Low, High, Length, SetLength, SizeOf, Succ, Pred, True, False, the standard integer, boolean, char, string,
pointer and real types, Break, Continue, Assigned, New, Dispose, GetMem, FreeMem, Move, FillChar, Copy, Pos, Delete,
Insert, Abs, Odd, Trunc, Round, Halt, Include, Exclude, Create, Destroy, Free) need no source. A match is not counted
only when a proof line names it and the proof holds; a proof that does not hold fails the audit.

## 4. Provenance (provenance/, tools/audit/provenance_lint.py)

One JSON record per tracked file at `provenance/<path>.json`, except the files under provenance/ and VERDICT.md:

- `path`; `kind`: translation, specification, standard, verbatim or new;
- `sources`: translation: objects {source (magiblot/tvision or magiblot/tvterm), commit (the pinned one), file,
  lines A-B}; specification: {specification: id}; standard: {document, url}; verbatim: one {source, commit, file,
  blob}; new: none;
- `inputs`: objects {origin, sha256}: every file the implementer read for the file. Allowed origins:
  `magiblot/tvision@<pinned commit>:<path>`, `magiblot/tvterm@<pinned commit>:<path>`,
  `unxed/far2l@8030902caf42498e1612e5a393ab7fc489048f51:VTExts.md`, `repository:<path>` (a file of this repository),
  `standard:<name>`, `specification:<id>`; a file of kind new takes only repository:, standard: and specification:;
- `implementer`: who implemented it (a neutral description of the role, such as "implementer 1");
- `proofs`: the windows of the proofs of this file in tools/audit/proofs.txt;
- `versions`: objects {blob, commit, pr, audit_run}: every version of the file in the history; commit (the commit
  that introduced the blob), pr (a link to the pull request) and audit_run (a link to the CI run that audited it)
  may be null while the change is in review: such a version is pending.

The check: every tracked file has a record; every field is present and of its form; a translated Pascal file carries
its notice; a verbatim version equals the blob of its source; a named commit holds the blob at the path; with
`--history`, every version of every file in every commit of HEAD is listed; provenance/INDEX.md, the summary table
(file, kind, sources, versions, pending versions, proofs), is current (an option writes it). Errors and missing
versions give exit code 1; pending versions are reported, not errors. A JSON report for the verdict.

## 5. The verdict (tools/audit/verdict.py)

Reads the reports of the audit, of the provenance check (with --history) and of the text check (files and every
commit message of HEAD), all of the same HEAD, and a link to the dossier (provenance/INDEX.md at that commit). It
prints exactly one of two outputs and nothing else:

- when every item holds (the audit covered the whole history of HEAD with the profile of section 3.2 and every
  corpus of section 3.1, left no unproved match and no invalid proof; the provenance check has no error, no missing
  version and no pending version; the text check found nothing):

  `TASK SOLVED: the code of unxed/tv3 is clean: every file of every version of the history is translated from magiblot/tvision or magiblot/tvterm or written from a specification without access to other code; there are no matches with the known implementations of Turbo Vision except the mechanically proved translation; dossier: <link>.`

- otherwise `NOT READY:` and then one line per unmet item, each naming the file, version, match or check.

Exit code 0 or 1.

## 6. The text rules (tools/text_lint.py)

Checks: every tracked file is UTF-8 with no byte order mark and no U+FFFD; no Cyrillic outside tests/; the file
names and the text keep to the neutral rule; with options, the messages of the commits of a range and a given text
(the title and description of a pull request). The neutral rule is a list of patterns in the script (case
insensitive, whole words where it matters): the names of assistant tools and models (lunobot and its Cyrillic
spelling, claude except the file name CLAUDE.md, sonnet, opus, codex), the words agent/agents and their Russian
equivalent, "owner decided" and the Russian words for owner, "rewrit..." and its Russian equivalent, references to
the repository unxed/lunobot, the word chat. The script is exempt from the check of its own text, and its own
non-ASCII patterns are written with escape sequences. A JSON report for the verdict.

## 7. Test harness, CI, documents

- tests/testlib.inc: Check(Cond, Name) counts a check and prints "FAIL <Name>" when false; Done prints
  "ALL OK (<n> checks)" or "<k> FAILED of <n>" and then ends with exit code 1. tools/test.sh builds the units of src/
  with Free Pascal 3.2 (mode objfpc) and runs every tests/t_*.pas; a test passes when its last line starts with
  "ALL OK"; with no unit or no test it reports that and passes.
- Tests of every script (Python unittest, texts made inside the tests, no corpus needed).
- .github/workflows/ci.yml, workflow `ci`, on push, pull request and manual dispatch:
  - job `linux`: the tests of the tools; the text rules of the files; on a pull request the text rules of its
    commits and of its title and description, and a check that it does not change VERDICT.md; the provenance check
    with --history; the build of every unit of src/; the unit tests.
  - job `verdict`: the corpora (cached by the hash of the corpora script), the audit of the whole history, the
    provenance check with --history, the text check of the files and of every commit of HEAD, then verdict.py; its
    output in the job summary; the job fails when the audit fails or the provenance check has errors or missing
    versions; on a push to main the output becomes VERDICT.md, committed by CI when it changed.
- docs/CLEANROOM.md: the protocol, from the specification "protocol".
- docs/ASYNC.md: the asynchronous contract and the porting rule:
  - the contract: one UI thread owns every view; the thread-safe surface is exactly TEventQueue.WakeUp,
    TEventQueue.PostEvent and the timers; TEventQueue.WaitForEvents(TimeoutMs) returns on input, on a wake-up, on a
    due timer or after the time-out (on Unix a pipe in the same poll, on Windows an event object in the same wait,
    on DOS a flag that the input polling reads); every loop, nested modal ones too, goes through TProgram.GetEvent,
    which drains the posted events; cancel tokens and progress by posted events; on DOS tasks are resumable objects
    run from Idle; events address views by weak references, a gone view voids the event;
  - the porting rule: P1 the existing API (names and signatures per docs/API-NAMES.md, observable behaviour) is
    translated as it is, the contract only adds; P2 ExecView stays a nested loop and reaches WaitForEvents through
    GetEvent, a posted event reaches the innermost active loop, a gone addressee drops it; P3 blocking operations
    stay synchronous, asynchronous variants are new APIs, nothing in GetEvent or Idle blocks except WaitForEvents, no
    mutable global state is reachable from another thread; P4 every TView is UI-thread only, state that the
    thread-safe surface touches is protected by a lock or an atomic and listed as "difference: thread safety of ..."
    in docs/API-NAMES.md; P5 where an existing API would block the UI thread on another thread or break the contract,
    it stays and a new non-blocking API is added beside it (listed as "added"), explained in the pull request; P6
    where P5 does not help, the unit is translated as the C++ has it and the one test is marked skipped with a link to
    an issue; P7 the units TvViews, TvWindow, TvMenus, TvApp and TvDialog pass in CI the test that PostEvent or
    WakeUp from a second thread during a modal ExecView is delivered, with no deadlock.
- docs/API-NAMES.md: how a C++ name of magiblot becomes a Pascal name (classes keep their names; member and free
  functions take a capital first letter; data members take a capital first letter; constants, enumerators and
  commands keep their names; constructors are Create, destructors Destroy; value types are advanced records with
  class operators; reference parameters that change are var, const references are const; units are Tv<Name>),
  and two empty lists to fill: "Added" (P5) and "Differences" (P4).
- README.md: what the library is; that it is in development, units coming in one at a time bottom up; links to
  VERDICT.md, provenance/INDEX.md, docs/CLEANROOM.md, CLAUDE.md and the CI runs; the checks to run; and the section
  "License" with exactly these three bullets:

  - A unit whose header says `Translated from magiblot/tvision @ <commit>` is a derivative work of magiblot/tvision,
    and so of the Turbo Vision 2.0 release published by Borland: the Borland disclaimer and the MIT license of
    magiblot apply ([`COPYRIGHT.magiblot`](COPYRIGHT.magiblot)). Its header names the magiblot files it was
    translated from.
  - A unit whose header says `Translated from magiblot/tvterm @ <commit>` is a derivative work of magiblot/tvterm: its
    MIT license applies ([`COPYRIGHT.tvterm`](COPYRIGHT.tvterm)). Its header names the tvterm files it was translated
    from.
  - Every other file (the units without such a notice, the tools, the tests, the demos) is under the MIT license
    ([`LICENSE`](LICENSE)).

## 8. Neutral text and language

Every file, commit message and pull request description is English and neutral (CLAUDE.md, rule 4): no reference to
the process that produced it, to the tools or assistants used, to discussions, issues of other repositories or the
reasons of earlier decisions; it reads as the rules of the project as they are.

## 9. Done when

On the branch, the CI run of the head has the job `linux` green and the job `verdict` green (the audit passes with no
unproved match; the provenance check has no error or missing version); the output of verdict.py may still be NOT
READY only because of pending versions (commit, pull request and audit run are filled after review).
