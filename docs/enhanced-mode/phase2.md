# Enhanced native windows: build A

This replaces the phase 2 split/tab workspace preview with the approved simple
window model. Enable `SIMANT_ENHANCED_CONTRACTS=1` and `--windows` on Windows.
`SIMANT_ENHANCED_WORKSPACE=0` retains the phase 1 comparison host; SDL dummy has
no HWND and also uses that comparison host. Classic remains unchanged.

`enhanced/workspace.{h,c}` stores ordinary window records, without tree/group/tab
nodes. `platform/sdl3/native_workspace.c` creates three owned world HWNDs and the
two fixed control-panel HWNDs. It also applies ownership, fixed frame capability,
DPI, movement and attachment policy to retained content/dialog SDL HWNDs. Those
clients keep their current presentation for steps B/C. Map and Yard command rows
are cropped out; only their source viewport remains. The overview caption is Map.
Status and other source tasks retain the source close policy and accepted outcomes.
No minimize buttons are added to game children. Only world views resize/maximize.

Drag a native caption near a main-client edge and release to attach. A hollow
outline previews the attachment. Drag away to float, retaining the remembered
floating bounds; a cancelled system move retains the old attachment. Alt+Space
provides Move, Attach to Edge and Detach. F6/Shift+F6 cycles visible windows.
Fixed panels retain their client size; main movement/resize repositions attached
windows. There are no tabs, splits, compass targets, presets or Move Panel UI.

The main frame keeps the original File, Window, View, Options and Speed resource
menus. Source strings and enabled/check bits are mirrored, including Pause/Unpause.
Window > Game is enhanced's replacement label for Edit. The approved file/window/
pause/speed accelerators submit through the same executor as menu commands; text
entry retains its keys. Window also offers Reset window layout and the two extra
world views. Native Game close hides its host view; Window > Game restores it.
Retained B/C window close still follows its original compatibility lifecycle.

The panels draw original picture crops from the shipped immutable HCEGANT catalog;
`picture_controls.inc` records original Obj geometry, with no copied asset bytes.
The normal tool picture is 5107, as used by the source draw hooks. Picture buttons
have native text names/tooltips. Health/count values and warning markers use the
semantic snapshot. Warning actions convert the selected percentage into an exact
source meter coordinate, so the source retains quantization. Focus a warning
meter and use arrows in 5-point steps, digits for deciles, or Home/End for 0/100;
mouse release uses the control's client coordinates. Queen placement and
mating eligibility are shown from current state; their waits remain source-owned.

All new game controls call `enhanced_submit_event`, which checks an explicit
catalog/event whitelist and retains the original alternate code. The executor
prepares/flushes the action's source owner before delivery. Map/Yard preparation
uses their original transitions before opening the required owner. Primary pan
uses the catalog's complete `edit_scroll_and_redraw` logic entry at an outer
source seam; native callbacks never call it. Its source XOR stepping/clamping is
retained. Primary dragging previews smooth host movement and commits the delta
on release. Extra-plane drags and all wheel zoom are passive host operations.
Worlds use immutable phase 1 art/snapshots, without source cache dependencies.

The first activation click in retained discrete content controls also submits
through the durable FIFO. Auto/Manual, allocation sets, units/help and History
series therefore finish the owner flush before one delivery. Held triangle/card/
world tool transactions remain their existing compatibility path for B/C; this
is not a claim that phase 0's unavailable gesture/task-result adapters are complete.

`%LOCALAPPDATA%\SimAnt\windows-v2.txt` stores DIP floating bounds, monitor identity,
edge/offset, host visibility and world camera/zoom. `SIMANT_WORKSPACE_LAYOUT=PATH`
isolates it for tests. The format rejects old split layouts, invalid IDs/bounds/
zoom and trailing data transactionally, preserving a rejected file for diagnosis.
Atomic replacement uses a temporary file. Recovery keeps a complete frame on an
available work area when it fits, otherwise a reachable caption. Physical mixed-DPI,
monitor hot-plug and UI Automation/screen-reader certification remain unverified.

Owner registrations (top-level tests/ and layout/ are not changed):

```powershell
python portable/tests/enhanced/workspace.py --build BUILD --out FRESH_UI --screens FRESH_SCREENS
python portable/tests/enhanced/action_equivalence.py --build BUILD --out FRESH_ACTIONS
python portable/tests/enhanced/run.py --build BUILD --out FRESH_REGRESSIONS
python portable/tests/enhanced/invariance.py --build BUILD --out FRESH_PASSIVE
```

`run.py` now requires both regressions PASS; activation is no longer XFAIL.
`workspace.py` exercises actual native capabilities, movement/attachment, keyboard,
zoom, persistence/rejection and unchanged semantic snapshots, with nine captures.
`action_equivalence.py` retains every existing acceptance view/SaveRec slice around
original current-source event delivery and actual native button/keyboard/menu routes.
It records missing preconditions and every raw difference; it does not execute the
original DOS executable. `invariance.py` retains its strict full-raw comparison,
including repeat-off controls and real native attach/detach/move/resize/zoom/reset
plus serialized roundtrips. No new masks are used. A nonzero report remains a
failure/difference, even if SaveRec/RNG and bounded gameplay projections agree.

Final build A is partial. The [task receipt](../../build/workers/enhanced-build-a/RESULT.md)
records missing world/editor clients in the docked readback, tooltip placement at
the frame corner, outstanding world-tool gestures, incomplete action outcomes and
strict raw-state differences. Passing HWND/model checks does not certify those
pixels. Neither visual defect is established as capture-only.
