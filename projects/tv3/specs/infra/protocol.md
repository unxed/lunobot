# Specification: the protocol by which a file of tv3 is made

This text is the specification of `docs/CLEANROOM.md` of the repository unxed/tv3-new (the library tv3). The
document that implements it says the same in its own words, in English, as the rules of the project.

## Purpose

Every file of the repository is made by a fixed procedure, and the facts of how it was made are recorded beside it,
so that anyone can check, file by file and version by version, where its content comes from.

## Roles

- Implementer: writes one file, or one unit with its test program, from the inputs that its procedure names and
  nothing else. It starts with no other context, works in an empty directory that holds only its inputs, uses no
  network beyond what its procedure allows, and reports every file it read.
- Specification writer (procedure C only): writes the functional specification of a unit; never the implementer of
  the same unit.
- Maintainer: prepares the inputs, starts the implementer, puts its result into a branch, opens the pull request,
  runs the checks and completes the provenance record. A maintainer does not write or edit the code of a translated
  or specified file, except for changes that keep its tokens (line endings, file mode).

## Procedures

- A, a translated unit. Inputs: the C++ files of magiblot/tvision at commit
  b4831e2ca16652db327fb7cc964f1c8c2d512524, or of magiblot/tvterm at 210eb23564da06c358d2623388939bb02f7f3419, that
  the unit translates, with the headers they include; docs/API-NAMES.md; docs/ASYNC.md; the interface sections of
  the units of the repository that the unit uses; for terminal units the documents of standards of
  tools/audit/facts/ (xterm control sequences, ECMA-48, DEC STD 070); for the far2l terminal extensions VTExts.md
  (unxed/far2l, branch extsdocs) instead of C++. The implementer writes the unit (header with the notice
  "Translated from magiblot/tvision @ b4831e2" or "Translated from magiblot/tvterm @ 210eb23" and the list of the C++
  files; interface; implementation) and its test program tests/t_<name>.pas from the behaviour of the C++, function
  by function, and reports where the C++ cannot be expressed. It does not reproduce code remembered from any other
  source.
- B, a file from standards: as A, with documents of standards as the only outside inputs.
- C, a unit from a specification, for a unit that no allowed source covers: a specification writer writes the
  interface declarations and a paragraph of behaviour per routine, no implementation code; the specification is kept
  outside the repository and the record names it by id and SHA-256. A different implementer, who has seen no other
  implementation of the unit, writes the unit and its tests from it, docs/API-NAMES.md and docs/ASYNC.md.
- D, a file of the repository itself (tools, CI, documents, README, LICENSE): written for the repository by an
  implementer whose inputs are listed in the record. COPYRIGHT.magiblot and COPYRIGHT.tvterm are byte for byte
  copies of the files COPYRIGHT of their sources (kind verbatim).

## A step

1. One unit, or one group of related files, per pull request; units go bottom up by their uses. Inside a unit the
   commits show its course (interface, classes, tests). Commit messages say what was done, in a neutral tone.
2. The maintainer prepares the directory of inputs and starts a new implementer. A file read outside the inputs, or
   a use of the network outside the procedure, voids the result; a new implementer starts again.
3. The result goes into a branch together with its provenance record.
4. A failing test is given with its message to a new implementer together with the same inputs; after three failed
   attempts the step stops and the case is recorded in an issue.
5. A match of the audit is either proved by tools/audit/prove.py (an entry of tools/audit/proofs.txt) or the fragment
   is made again by a new implementer who is told which behaviour to express differently, never the fragment.
6. When CI is green, the maintainer writes the commit and the run of the audit into the versions of the record; the
   pull request is merged with a merge commit.

## The result

The state of the repository is the output of tools/audit/verdict.py as VERDICT.md shows it, and nothing is added to
it. A doubt about a file is not written as a remark: before the verdict it becomes a check of verdict.py or a change
of the file.
