# Keyboard handler context and Event coordinate consumers

Read-only source/original-code audit, 2026-11-14. Reproduce individual original
instruction listings with `python tools/context.py FUNCTION`. Addresses below
are original module offsets, not addresses in the working DOS link. The audit
covers shipped canonical call paths, including the address-spelled aliases of
win_GetEvent. It does not assume that a high-bit event is ignored by every modal
loop. Scratch listings, the source census and measured runs are in
`build/workers/irq-context/`.

## Producer words

`input_enqueue_event` (root:1B73:036E) stores AX/CX/DX/BX/ES at offsets
+06/+08/+0A/+0C/+0E (03A6..03B2). It separately samples the BIOS flag word and
BIOS tick low word at +02/+04, and leaves +00 untouched. `input_pop_event`
(032E, 0361..0367) copies all eight words with REP MOVSW.

`kbd_process_scan` (0747) saves CX but does not save or replace DX before its
FA and F0 enqueue calls. The initial make event (07AF..07BF) clears AX and ES,
constructs FA00|scan in BX, and retains DX. At 0763 it replaces CL with 2 on
the non-E0 path, so Event.h contains `(entry_CX & FF00h)|2`; following E0 it
retains all of entry CX. The command dispatch clears CX at 07D0 and reads the
BIOS flags into CL at 07D8; its F0 command enqueue (088A..0892) retains DX,
but h is then the flags, not interrupted CX. The secondary FA enqueue at
089A..08A2 also uses that post-dispatch register state. AX/BX/ES are constructed
values on these paths. There is no additional interrupted-context Event field.
The untouched +00 word is unexplained storage, not evidence of an IRQ register.

Precision about provenance matters: the tapes capture **scan-processor entry**,
not the CPU's raw interrupted foreground registers. `kbd_int09_hook` loads DX
with relocated DGROUP at 0703 and calls 0747 at 071A. `kbd_int15_scan_hook`
loads DGROUP at 067E and clears DL at 0694 before its 0698 call. Thus DX can
be segment residue introduced by the wrapper itself. The observed 24023/23596
values are not evidence that arbitrary foreground DX reaches the queue.
While the scan hook is disabled the recorder instead captures INT15/AH=4F;
those events do not run the source scan projection or enqueue FA/F0.

F0 events in this audit are the scan processor's synthetic mouse/window action
commands. Physical INT33 callbacks are different: `mouse_event_callback`
(0445, 0461..0468) takes driver buttons and coordinates into the source cells,
then dispatches the registered descriptor callback. Those CX/DX values are
pointer coordinates and must not be replaced with keyboard register residue.

## Copies and consumers

“Excluded” below means excluded for **FA/F0 register residue** by the named
caller guard, not that the coordinate reader is globally dead. Pointer/object
events still use these readers to affect play.

| Reader / copy | Canonical evidence; original DOS anchor | FA/F0 context and effect |
| --- | --- | --- |
| input_pop_event -> window_current_event | src/window/events.c:159; root:1B73:032E and root:218D win_translate_pending_event | Copies h/v and all other words unchanged. This is observable raw state and remains in the step verdict. |
| win_translate_pending_event | src/window/events.c:159..205; root:218D | FA/F0 have bit 15 set, so they bypass object dispatch. F0 window commands use code, and pass NULL to move/resize; they do not pass residue as a position. |
| win_GetEvent -> caller's Event | src/window/events.c:212..222; root:218D:03F1 | Copies the complete current event before pumping the next. No h/v interpretation or filtering. Copies can therefore reach modal loops. |
| window_previous_event | src/window/events.c:73..85; win_dispatch_object_event, root:218D:000C | Full copy only on object dispatch; FA/F0 excluded by the above high-bit guard. Repeat detection reads code/modifiers/time, not h/v. |
| win_FlushEvents / input_discard_queued_events | src/window/events.c:224; src/window/menu_helpers.c:487; input_pop_event caller list | Full local copies discarded. No coordinate-dependent play/presentation. |
| DoEvent / input_translate_special_key | src/ui/game_events.c:64..137,230; S19 DoEvent and input_translate_special_key | FA dispatch uses code and BIOS flags only. F0 has no matching game dispatch case. No h/v read. New shortcut events use explicit arguments, not a copy of h/v. |
| OpenMiniMapWin | src/ui/minimap.c:304..353; S04:35F5:075F | **Unfiltered h/v reader.** 07E0..0807 gets any event, tests the open window, then passes Event+8 to PointInRect. If inside, 081B..086B uses h/v to calculate a map location; 0876..0893 centers/redraws the edit view and both map cursors. These words can control view state/presentation conditional on the rectangle; there is no code check. |
| SpecialXfer | src/ui/yellow_commands.c:691..753; S22:39C7:152C | **Unfiltered h/v reader.** 15D2..1607 gets any event then reads Event+0A/+08. 1631..167C converts and checks the yard cell. A valid occupied cell writes YMapPnt and calls XferPatch (168D..169B); otherwise a reject sound/message is emitted (16A8..1709). Coordinate-dependent game and presentation branches; no code check. |
| PlaceQueenInYard | src/ui/view_commands.c:510..518; root:015B:094A | Copies h/v only when code == OBJ_YARD_VIEWPORT. Otherwise gets real pointer position. FA/F0 excluded. |
| processEdit, including replacement local Event | src/ui/yellow_commands.c:73..99; S22:39C7:0000 | Reached for edit viewport codes 4/21 in ProcEditEvent, or MapAreaEvent. Its double-click replacement must have the **same code** as the original viewport event. FA/F0 cannot replace it. Coordinates control tools/ant commands, but IRQ residue is excluded. |
| MapAreaEvent | src/ui/minimap.c:174..215; S04:35F5:025A | ProcMapEvent calls it only for OBJ_MAP_VIEWPORT. Reads/rewrites h/v, delegates to processEdit, or centers map and redraws. FA/F0 excluded. Subsequent tracking iterations overwrite h/v with GetMousePos. |
| YardArea | src/ui/yard_window.c:859; S13:384C:16EF | ProcYardEvent calls only for OBJ_YARD_VIEWPORT. Coordinates select a yard cell / transfer on double click. FA/F0 excluded. |
| ProcInfoEvent, including 320-wide modal OpenInfoWindow | src/ui/info_cards.c:534,648..691; S23:39C7:0F50 | Even the modal loop calls a routine that returns unless code == OBJ_INFO_CONTENT before either relative coordinates or the Point alias of h/v is read. FA/F0 excluded. |
| MapToYellowAnt | src/ui/map_window.c:677; S12:384C:12D3 | ProcMapEvent calls only for OBJ_MAP_YELLOW_ANT. h selects add/kill side under Ctrl+Shift. FA/F0 excluded. |
| DoWarnSetB / DoHealthSetY | src/ui/editor_menus.c:275..293; S05:35F5:0642/0684 | ProcEditEvent calls only for codes 18/17. v changes a warning threshold and redraws. FA/F0 excluded. |
| AntMenu | src/ui/editor_menus.c:218..247; S05:35F5:04D3 | Only reached through processEdit's viewport path. h/v position proximity menus; resulting menu can issue YellowCommand. FA/F0 excluded. |
| win_dispatch_desktop_click | src/window/events.c:244..268; root:218D:0451 | Only EVENT_DESKTOP_CLICK (FF00) reaches it. Point alias reads both words to close/raise windows. FA/F0 excluded. |
| list_process_click / win_ProcSliderEvent | src/window/lists_sliders.c:411..485; root:23E6:0A53/0B11 | Object dispatch only. v selects list row / scroll arrow and repaints. FA/F0 excluded. |
| win_track_move / win_track_resize | src/window/move_resize.c:200,274; S26:39C7:040F/0671 | h/v read only with a non-NULL object event. F0 command path calls with NULL and computes its start from the object rectangle. FA excluded. |
| menu_track_popup re-enqueue | src/window/menu_tracking.c:280..289,392..394; DOS function menu_track_popup | Copies h/v and payload_segment to input_enqueue_event_args only for FE high byte and another menu title. FA/F0 are discarded from the raw queue, not re-enqueued. Pointer tracking uses GetMousePos, not the queued coordinates. |
| PointInRect | root:1FD2:04E5, 04EB..0520 | Reads both words through a Point alias, signed left <= h < right and top <= v < bottom. Relevant event-bearing callers are listed above; other callers pass actual pointer positions. |

All other source Event-taking loops inspected by the census use only code,
modifiers or BIOS input, or discard copies: ui_show_alert, ui_choice_prompt,
ui_prompt_save_discard_cancel, FileSelect (address-spelled o09_35F5_03C6),
DoScenario, ScoreDialog, PictureDialog, YellowHelp, DoExpMenu, win_DoProxMenu,
ui_edit_text_field and win_wait_event_or_escape. The latter passes the Event
back to its caller; it has no coordinate interpretation. Ordinary window
dispatch still runs when these loops fetch events; its readers are in the table.
Searches covered .h/.v/->h/->v, Point aliases, event-owner names, raw queue
references, complete Event copies, address-spelled GetEvent aliases, and memory
copy/compare/I/O uses. Non-Event `h` fields (animation sizes and resource handles)
are not event consumers.

## What is established about normal play

The values are **not globally unread**: OpenMiniMapWin and SpecialXfer are
normal game paths, and their original instructions read them without a code
filter. Their conditional effects above are established by original code, not
inferred from an Event field name. This prevents treating the discrepancy as a
proven irrelevant representation or removing it from state comparison.

It is **undecided** whether ordinary native zero residue versus the DOS
wrapper's actual segment residue changes visible play in these loops across
all shipped modes/window placements. In the captured runs scan-entry DX is
far above screen height when hooks are enabled; an arbitrary low foreground
DX counterexample would be invalid because the wrapper overwrites it. The
map rectangle guard can reject both representations; the yard arithmetic can
reject both as well. We have not established all reachable rectangle/origin
bounds and 16-bit intermediate values for these modal states, nor captured a
normal-play counterexample. An unguarded reader proves dependence on its
arguments, not that a particular hardware trajectory reaches a different
branch. This limitation remains OPEN. No absence-of-consumers claim is made.

## Acceptance replay rule and result

The v4 recorder already emits AX/BX/CX/DX at each scan-processor entry (or the
disabled-hook INT15 boundary) and pointer callback. All 572 admitted keyboard
transitions across the six tapes have CX/DX; no reference or recorder changed.
`step_inputs` retains these words in the chronological input tape. The optional
host observer attaches each pair to its own staged raw SDL event, and the
scan adapter asks for that pair immediately before the existing scan projection.
Physical pointer inputs continue through coordinate translation and mouse
callbacks. The existing projection decides which bits survive, constructs the
Event and runs normal enqueue/consumer paths. Ordinary execution still supplies
CX/DX=0 (normal FA h=2, v=0; F0 v=0).

This is input replay: the words come exclusively from immutable, independently
captured service input, before comparing any state. No Event, expected hash,
saved record or native game result supplies replay values; no field is masked
or reclassified. No reference state is copied into game storage. The wrapper's
register residue is an executable-specific machine boundary just as its clock
reads and IRQ service positions are. It need not be a user-controlled input.

Two fresh-build full runs agree in every lane: new-game-save 64/64, quick-game
2000/2000, long-run 3000/3000, with complete clocks/services/inputs consumed.
There is no next first game-state difference within these finite references,
and therefore no next layer to attribute. Eight-entry prefixes are equal;
clock-disabled controls still diverge at entry 2. `--disable irq-context`
restores the four Event.v stops at 39/36 and 659/660 (platform representation);
long-run remains equal. This does not establish DOS/native equivalence outside
the recorded scenarios or close the normal-play hardware-context limitation.
