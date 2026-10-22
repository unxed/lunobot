# Unit TvTermOsBase

## 1. Purpose

TvTermOsBase holds the types and the global state that are shared between the terminal-operating-system facade (TvTermOs) and its platform backends (Unix, Windows and a null backend). It contains no routines: it is only a place for a callback type and three shared variables, so that the facade and the backends do not depend on each other.

## 2. Interface

```pascal
unit TvTermOsBase;

interface

type
  TOsHook = procedure;

var
  { set by the backend when the size of the terminal changes }
  OsResizeFlag: LongInt = 0;
  { the size that the terminal told in its input (the far2l extensions), used when the kernel does not know the size; 0: none }
  OsToldCols: LongInt = 0;
  OsToldRows: LongInt = 0;
```

## 3. Behaviour

**TOsHook.** A parameterless procedure type (a plain procedure, not a method, not "of object"); it is used for callbacks without arguments and results.

**OsResizeFlag.** Initial value 0. A backend sets it to a non-zero value when it learns that the size of the terminal has changed (for example from a resize signal or an input event); the code that polls it is expected to examine it and reset it to 0 itself. The unit itself never changes it. It is a plain variable with no locking: it is written from the backend, possibly from a signal handler or another context, and read by the facade, so the writes and reads must be single, atomic-sized `LongInt` accesses.

**OsToldCols, OsToldRows.** Initial value 0 each. The width in columns and the height in rows of the terminal as reported by the terminal in its input stream (the far2l protocol extensions). They are used only when the operating system kernel cannot report the size. The value 0 means "nothing has been told"; a backend that receives a size stores the two values (positive numbers); consumers must treat a value of 0 or less in either as "no information".

No initialisation or finalisation code exists; the variables have the stated initial values at program start.

## 4. Dependencies

Library units: none. Standard units: none.

## 5. Checks for a test program

- Right after start, `OsResizeFlag`, `OsToldCols` and `OsToldRows` are 0.
- A variable of type `TOsHook` can be assigned a parameterless procedure and called through the variable.
- The three variables can be assigned and read back (as `LongInt`; check that a value like 2147483647 and -1 survive).
- The unit can be used by two other units at once and they see the same variables (one writes, the other reads the same value).
