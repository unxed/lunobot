# Unit TvActions - functional specification

## 1. Purpose

TvActions is the action registry. An action is declared once with a name, a menu caption, a command number, a key and a help context. Menus, status line items, the translation of keys into commands, key rebinding by the user and the search for two actions on one key all read the same table. The table is one global list, owned by the unit, in registration order. All routines run on the UI thread only; there is no locking.

## 2. Interface

```pascal
unit TvActions;

interface

uses
  TvKeys, TvEvents, TvViews, TvMenus;

type
  TAction = record
    Name: ShortString;      { 'file.save'; the identity; case does not matter }
    Caption: ShortString;   { the text of the menu item, with the ~hot~ letter }
    Command: Word;
    Key: Word;              { the key code now in force, kbNoKey for none }
    DefaultKey: Word;
    HelpCtx: Word;
  end;

function RegisterAction(const AName, ACaption: ShortString; ACommand: Word;
  AKey: Word = kbNoKey; AHelpCtx: Word = hcNoContext): Integer;
function ActionCount: Integer;
function ActionAt(Index: Integer): TAction;
function FindAction(const AName: ShortString): Integer;
function FindActionByCommand(ACommand: Word): Integer;
function FindActionByKey(const Event: TEvent): Integer;
function BindActionKey(const AName: ShortString; AKey: Word): Boolean;
procedure ResetActionKeys;
function ActionKeyText(Index: Integer): AnsiString;
function NewActionItem(const AName: ShortString; Next: TMenuItem): TMenuItem;
function NewActionStatusKey(const AText, AName: ShortString; ANext: TStatusItem): TStatusItem;
function ActionKeyToCommand(var Event: TEvent): Boolean;
function ActionKeyConflicts: AnsiString;
procedure ClearActions;
procedure UseActionsForSwitcher(const AName: ShortString = 'window.switch');
```

Source begins with `{$I tvdefs.inc}`. No other public identifiers.

## 3. Behaviour

Names are compared case-insensitively (ASCII upper-casing of the byte string is enough; names are ASCII by convention). Keys are compared as `TKey` values (`TKey.Create(KeyCode)` of TvKeys, compared with `=`), so different codes that mean the same key (for example Ctrl+F5 written two ways) are the same key. `kbNoKey` never matches anything.

**RegisterAction(AName, ACaption, ACommand, AKey, AHelpCtx)**: if an action with that name (case-insensitive) exists, it is replaced in place (the number stays, the record is overwritten, `Key` and `DefaultKey` both become AKey, so a user rebinding of it is lost); otherwise a new action is appended. Returns the index (0-based). The stored name is as given. No check of duplicate commands or keys.

**ActionCount**: number of actions (0 at program start). **ActionAt(Index)**: a copy of the record; Index must be in 0..ActionCount-1 (not checked).

**FindAction(Name)**: index of the action with that name, case-insensitive, or -1. **FindActionByCommand(C)**: index of the first action (registration order) with that command, or -1.

**FindActionByKey(Event)**: -1 unless `Event.What` is `evKeyDown`; otherwise the index of the first action, in registration order, whose `Key` is not `kbNoKey` and equals the key of the event (`EventKey(Event)` of TvEvents, which includes the modifier state). Returns -1 when none.

**BindActionKey(AName, AKey)**: sets the current `Key` of the named action (`DefaultKey` unchanged; AKey may be `kbNoKey` to unbind). Returns False if the name is unknown, True otherwise. The same key may be given to several actions. **ResetActionKeys**: every action's `Key` becomes its `DefaultKey`.

**ActionKeyText(Index)**: the key of the action as text, by `KeyCodeToStr` of TvKeyName: `F2` for `kbF2`, `Ctrl+S`, and the empty text for `kbNoKey`. Index must be valid.

**NewActionItem(AName, Next)**: a new `TMenuItem` for the named action, linked before `Next`: caption = `Caption`, command = `Command`, key code = the current `Key`, help context = `HelpCtx`, and the shown key text (the item's parameter string) = `ActionKeyText`. For an unknown name nothing is created and `Next` is returned unchanged. The item is built with the TvMenus constructor `TMenuItem.Create(Caption, Command, KeyCode, HelpCtx, ParamText, Next)`; the item's `Command`, `KeyCode`, `Next` and `Param` (pointer to the text) are readable. Example from the test: for `file.save` (`~S~ave`, command 200, key F2) with `Next` = the result for an unknown name (nil): `Command = 200`, `KeyCode = TKey.Create(kbF2)`, `Next = nil`, `Param^ = 'F2'`.

**NewActionStatusKey(AText, AName, ANext)**: a new `TStatusItem` linked before `ANext` with text AText, key = the action's current `Key` and command = its `Command`; unknown name gives `ANext`. (The key text is not taken from the action: the caller writes it in AText.)

**ActionKeyToCommand(Event)**: when `FindActionByKey(Event)` finds an action (and it is not the switcher action, below), the event is changed in place into a command event: `What = evCommand`, `Message.Command` = the action's command, `Message.InfoPtr = nil`; returns True. Otherwise the event is untouched and False is returned. The event is changed only on True.

**ActionKeyConflicts**: for each key that is current on two or more actions, one line `KeyText: name1, name2, ...` ended with a line feed (#10), names in registration order, the key text taken from the first action of that key (`ActionKeyText`); keys appear in the registration order of their first action; actions with `kbNoKey` are ignored; two codes that are the same `TKey` count as the same key. The empty text when there is none. Example: `file.save` and `edit.find` both on F2 gives `F2: file.save, edit.find` + LF.

**ClearActions**: removes all actions (count 0). It does not undo `UseActionsForSwitcher`.

**UseActionsForSwitcher(AName)**: makes the key of the named action the key of the window switcher of the desktop. It stores the upper-cased name and sets the global hook `OnSwitcherKey` of TvApp (type `function(const Event: TEvent; out Backward: Boolean): Boolean`, called by the desktop for a key-down to ask whether it starts or steps the switcher) to a routine of this unit. The routine answers True when the event is `evKeyDown`, the switcher action exists and has a key other than `kbNoKey`, and the key of the event with the Shift bit removed from its control-key state (`TKey.Create(KeyCode, ControlKeyState and not kbShift)`) equals the key of the action; `Backward` is True exactly when the answer is True and the event has the Shift bit set. Otherwise False (Backward False). So rebinding the action with `BindActionKey` changes the switcher key at once, and the old key stops working. `ActionKeyToCommand` never turns the key of the switcher action into a command (the desktop needs the modifiers); it returns False for it and leaves the event unchanged. Before `UseActionsForSwitcher` is called, no action is excluded. The switcher action is normally declared as `RegisterAction('window.switch', '~S~witch', cmNext, kbCtrlTab)`. The hook is not removed by this unit; a program or test sets `OnSwitcherKey` to nil itself.

## 4. Units used

* `TvKeys`: `TKey` (constructors `Create(KeyCode)` and `Create(KeyCode, ControlKeyState)`, equality), `kbNoKey`, `kbShift`, key codes.
* `TvEvents`: `TEvent` (`What`, `KeyDown.KeyCode`, `KeyDown.ControlKeyState`, `Message.Command`, `Message.InfoPtr`), `evKeyDown`, `evCommand`, `EventKey(Event): TKey`.
* `TvViews`: `hcNoContext`.
* `TvMenus`: `TMenuItem`, `TStatusItem` and their constructors.
* `TvKeyName` (implementation): `KeyCodeToStr`.
* `TvApp` (implementation): the global `OnSwitcherKey`. TvApp must not use TvActions.
* `SysUtils` (implementation): upper-casing of names.

## 5. What the tests pin down

t_actions (registry empty at start): three actions `file.save` (`~S~ave`, cmSave, F2, help 5), `file.open` (`~O~pen`, F3), `edit.find` (`~F~ind`, no key). Count 3; `FindAction('FILE.SAVE') = 0`; unknown name -1; `FindActionByCommand` 1 / -1; fields of action 0; `ActionKeyText(0) = 'F2'`; menu item and status item as described in section 3 (the test frees the item through a `TMenu`); a key event F3 finds action 1 and becomes `evCommand` with the open command; F9 stays a key event; `BindActionKey('file.open', kbF4)` frees F3 and makes F4 work, an unknown name returns False; `ResetActionKeys` restores F3; conflicts: none at first, none after `edit.find` is bound to Ctrl+F3, `F2: file.save, edit.find` + LF after binding it to F2; redeclaring `edit.find` with F5 gives index 2, count still 3, no conflict; `ClearActions` gives 0.

t_switch (desktop switcher, uses this unit): after `ClearActions`, `RegisterAction('window.switch', ..., cmNext, kbCtrlTab)` and `UseActionsForSwitcher`, Ctrl+Shift+Tab opens the switcher list and the release of Ctrl chooses; after `BindActionKey('window.switch', kbAltF6)` the old key no longer opens it and Alt+F6 does, with the release of Alt choosing; Alt+F6 pressed with no modifier to hold switches at once.

A test program should also check: `ActionKeyToCommand` on a non-key event returns False; `BindActionKey(name, kbNoKey)` frees the key; `FindActionByKey` returns the first of two actions on one key; three actions on one key give one line `K: a, b, c`; re-registering resets a user-rebound key; the switcher action is not converted by `ActionKeyToCommand` but other actions on other keys still are.

## 6. Observed oddities

Intended: re-registration replaces in place and resets the key; registration order decides ties; `ActionKeyToCommand` skipping the switcher action.

Accidental (not required to copy): `ActionAt` and `ActionKeyText` do not check the index; `ClearActions` leaves the stored switcher name and the `OnSwitcherKey` hook set; if the switcher action shares its key with an earlier action, `FindActionByKey` finds the earlier one, so only that one is converted, and if the switcher action is the first the second is not converted either (the first match decides); an action whose declared key includes Shift never starts the switcher, because the switcher routine strips Shift from the event only; names longer than 255 bytes are cut by `ShortString`; upper-casing of names is ASCII-only.
