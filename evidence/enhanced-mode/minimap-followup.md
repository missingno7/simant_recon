# Native MAP device: source anchors and proof boundary

Source anchors, read without changing the reconstruction:

* `src/ui/minimap.c`: `OpenMiniMapWin`, `Mini_DrawMapI`,
  `DrawMiniMapCursor`. The first held check follows the complete initial draw.
  Object 1401 uses source scales and nest padding before `CenterEdit` (the
  portable semantic alias of `f_0250_0FC4`). Selection alone does not close the
  outer window loop. The source desktop-click dispatcher can close 1400.
* `src/ui/view_dialog_helpers.c`: `myButton` services sound and returns
  `StillDown`. This supplies a shared external input seam without modifying
  the minimap translation unit or its game logic.
* `src/ui/yellow_commands.c`: `processEdit` checks `myButton` after a source
  double-click delay before entering AntMenu/MagnifyMenu. A native release
  before that decision previously prevented a fast click from opening a menu.
* `src/ui/experiment_menu.c`: `DoExpMenu` owns its root/submenu transition,
  selected substate, accept/cancel and return value. It consumes the low window
  byte of proximity notifications and `win_GetProxEvent`; its existing
  `ButtonHeldInit` and `ButtonHeld` calls provide safe completed-window seams.
* `src/window/events.c`: FBxx calls `win_update_proximity_event`; `win_GetEvent`
  prefetches the next event. Consequently submenu acceptance must wait until
  the source consumes the proximity notification, rather than queuing an
  acceptance that could close the window before the substate is recorded.
* `src/ui/intro_credits.c`: About's first input advances its sequence; a single
  close request must persist until the source's own exit condition is reached.
* `src/simulation/life_tiles.c`: the existing target-mode completion entries
  restore the saved pause state. A synthetic Pause toggle would lose that
  distinction, so native cancellation calls those entries at an outer seam.

The native minimap shares Map's semantic colour cells, native camera indicator
and masked icons. Comparing the actual yellow indicator pixels prevents a
fallback to the smaller hidden source viewport when the native view shows more
world. The original cursor still belongs to the source transaction.
The native painter does not read back a VGA
plane, change source rectangles, assign a view origin, or implement centring.
The popup and pointer adapters live in `portable/`; native menu labels and
states continue to come from source resources/publications.

Native-to-source point conversion must preserve the half-open rectangle.
`MulDiv` rounds its quotient: the final native pixel could become exactly the
source right/bottom edge. `OpenMiniMapWin` then rejects it before reaching its
next held check, so a close queued only at that check never arrives. The
adapter now floors the positive offset. Edge/corner tests check exact source
arguments and interactive return; the earlier immutable executable fails the
corner case and is retained separately as a negative control.

Nest maps have another rejected interval: source `multiplier == 64` subtracts
32 from the full 128-column hit coordinate. Native blank side gutters therefore
count as outside. Their native half-open bounds use ceiling at columns 32 and
96 so floor-mapped source x stays in 0–63 at fractional DPI. The tests derive
the valid interval by enumerating the mapping and check both usable edges and
both gutters on both nest planes in all three modes. The immutable pre-gutter
build fails both gutter cases and is retained as a second negative control.
Both old gutter lanes resumed with zero centring calls: the detected defect
is the native selection result instead of cancellation, not source liveness.
The earlier exclusive-edge corner negative, separately, did not return.

The compatibility-window audit found `panel_for_logical` returning
`16 + (id >> 8)` for unknown IDs while `u.windows` has sixteen entries. That
was an out-of-bounds workspace index. Unknown owners now return -1 and retain
their compatibility host. Their modal focus is explicit instead of depending
on that invalid slot. The sweep includes About, Population, source Help and
File prompts, in addition to native menus and content clients.

The final menu probe initially posted outside-cancel messages to a closed
source scenario window (0300), which also has the caption `SimAnt`. A hardware
watchpoint traces the resulting mouse fields to a translated host event; an
entry trace identifies SDL window 4, logical 0300, shown/open false. The probe
now selects the native frame by its menu bar and asserts visibility. All 31
comparisons then pass on the identical production executable, with all mouse
views and verdict classifications retained. The original failure and the
focused follow-up are separate receipts. No runtime input-normalization trial
was promoted.

Receipts and asset-derived captures belong under ignored
`build/workers/enhanced-menus/`, not in git. The final receipt lists source/tool
hashes, private-desktop audits and every item. Passing these checks establishes
the described native/source transactions and bounded recovery in the recorded
states; it does not establish DOS pixel equality or whole-game equivalence.
