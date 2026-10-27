# Specification: tests/testlib.inc

A Free Pascal 3.2 include file (mode objfpc) that a test program includes after its uses clause.

- Two global counters: the number of checks run and the number of checks failed, both starting at 0.
- `procedure Check(Cond: Boolean; const Name: string);` counts one check; when `Cond` is false it counts a failure and
  writes the line `FAIL <Name>` to the standard output.
- `procedure Done;` ends the test: with no failure it writes the line `ALL OK (<n> checks)`, where `<n>` is the number
  of checks run; otherwise it writes the line `<k> FAILED of <n>` and ends the program with exit code 1.
- A comment at the top of the file says how to use it, in two or three lines of English.
