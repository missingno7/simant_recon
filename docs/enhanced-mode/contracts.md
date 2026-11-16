# Enhanced presentation contracts

The approved [design and complete component/action catalogs](../enhanced-mode.md)
are the authority. These are the phase 0/1 contracts; the
[phase 2 workspace](phase2.md) is the current Windows shell when `--windows`
is enabled. Select `SIMANT_ENHANCED_WORKSPACE=0` for the retained host described here.
Set `SIMANT_ENHANCED_CONTRACTS=1` to enable publication and semantic submissions.
Classic without that variable does not publish or execute enhanced intents.

## Snapshot ownership and source seams

`portable/whole_program/enhanced/snapshot.h` defines pointer-free world,
overview/yard, panels/allocation, cards/help, history/status and dialog records.
`enhanced_snapshot()` returns a const publication; `enhanced_snapshot_copy()`
copies it into caller-owned storage. Reads never call the game, allocate source
resources, read source time, change a plane, decode via `DoCalcTile`, or consume
RNG. All three planes and six half-resolution scent maps are copied directly;
canonical sprite-bank residency is absent from the world model. Phase 1 supplies
[independent immutable art, source-output taps and a renderer](phase1.md).

One engine/UI thread owns publication in phase 0. A pointer remains valid until
the next source seam; copy if a paint needs longer storage. The two publication
buffers are not a cross-thread synchronization API. A monotonic 64-bit generation
identifies each completed publication. Repaints read the current generation;
they do not publish. Inspectors must always use the latest publication: Freeze
is excluded by the owner decision.

The port linker wraps the outer `ui_pump_events_edge_scroll` and external
`DoEvent` entries. DoEvent alone is conditional on pending guest input, so the
outer pump admits semantic intents even when idle. They publish before and after
the outer invocation and never execute new intents in recursive invocations.
The existing `f_1B28_0069` event-poll hook also publishes at a source modal owner
or the established animation/picture/save-confirmation owners 1A00/1E00/2100.
Build B also publishes at leased command and wrapped queen-placement waits,
and after completed original world/triangle tracker draws.
Those are synchronous source wait/poll boundaries after preceding operations;
they do not invoke drawing or advance a second simulation. Ordinary tracker polls
do not publish incomplete world edits. `EnhancedSeam` records the producer.
Canonical draw calls, queue operations, timing and resource lifetime continue.

Snapshot field provenance:

| Family | Canonical inputs and limits |
|---|---|
| World | MapA/B/R, LifeA/B/R, PherMap*, MapPlane/MapPnt/editTileRect, terrain/layer, player and spider coordinates. Array order remains `[x][y]`. No copied VGA, sprite bank, cache or art. The completed source draw publishes picture IDs/poses, leg/palp endpoints, the selected balloon/text and rectangle operations. No composite bytes are copied. |
| Overview/yard | MapMode/transform, YardMode, YMapPnt/CurYardPnt, YMapPopB/R, queen/colony counts and placement mode. Red population uses the existing proven 32+160-byte semantic span, copying its two named owners. No native recount or isometric conversion. Completed source animation sets publish selected picture IDs, positions, priorities and removals; opaque handle tokens resolve through the existing passive provider API. |
| Panels | Auto/Manual, exact TriLevel words, preset and units selection, population vectors, health/warning values, source options/speed/tool/pause. OptionStates uses the existing six-word semantic span; byte-defined words use memcpy. No conversion or normalization. |
| Cards/help | Current card/previous ring and private picture/text link tables, copied by an appended read-only observer in the converted TU. Independently owned CARD/TEXT/STYL/title resources. No DisplayCard/DoWinHelp during reading. General help replacement remains step C. |
| History/status | All ten 64-sample series, ring start/count, private graph selections/colors and OverallScore. Eight score percentages observed from the original formatted field output after the real font_PrintStr. No second CalcScore or guessed formula. Quick Game empire fields remain N.A. |
| Dialogs | Current front owner/flags, bounded copied Obj type/flags/rect/bitmap/text from resident native window reference views. No locking or resource loads; nonresident views stay unavailable. Text has truncation flags. This is an observation, not a guessed wait schema. `request_schema_available=0` blocks result injection. The token tracks observed owner/modal transitions, not yet every same-owner nested request. |
| Logical state | Full source stack copied independently of panel focus/layout. Native data never reopens a logical window. |

Remaining unavailable task schemas are integration work for step C. They are not proof that
an opaque private source state is absent or a prompt accepts arbitrary Return,
Escape, Close or timeout. The host/content are described in [builds A/B](phase2.md)
and [build B](build-b.md). Native file-picker and general controller bridges remain unavailable.

## Semantic action queue and execution

`actions.h` exposes `EnhancedIntent`, ordered `EnhancedGestureSample`, catalog
lookup, `enhanced_submit()` and a delivery ledger. Submitting only copies native
data into a bounded FIFO (32). It never calls canonical code. Monotonic caller
serials prevent duplicate delivery; full queues reject without claiming success.
No native HWND, focus, client dimensions or panel ID enters an intent.

The complete approved catalog is registered in `catalog.inc`, including L/E/T/H/U
classifications and canonical entries. The L classification remains a candidate:
phase 0 uses the established original event route for S06 instead of assuming a
direct SetPause contract. H returns `ENHANCED_HOST_ONLY` without source execution;
unproved routes return `ENHANCED_NEEDS_ADAPTER`. The original percent-looking N08 glyph now retains the audited 010E event; its semantic name remains unsettled and no new gameplay meaning is invented.

Currently executable discrete routes (integer parameter domains):

| IDs | Parameter | Source event / deterministic prelude |
|---|---|---|
| S06 | 0: toggle | FD41; no logical raise |
| S07 | 0..3: Slow/Normal/Fast/Ultra | FD43..FD46; no logical raise |
| S08..S13 | 0: toggle | FD31..FD36; no logical raise |
| N01 | 1..3: surface/black/red | FD26..FD28; no logical raise |
| N02 | 0..3: yard/house/strategic/graphic | FD21..FD24; no logical raise |
| N05 | 0..3: player/spider/black queen/red queen | 000B..000E; ToTop Edit, then Open Edit to finish source flush |
| N06 | 0..4: black nest/trail, alarm, red nest/trail | 0109/0A/0B/0C/0D; ToTop Map, then Open Map to finish source flush |
| A01 / B01 | 0: Auto, 1: Manual | 1204/05 or 1304/05; complete OpenModeWindow/OpenCasteWindow |
| A02 / B02 | 0..2: preset 1..3 | 1206..08 / 1306..08; same owner preparation |
| A04 / B04 | 0: toggle units | 120F / 130F; same owner preparation |
| I03 | 0..9: source series button order | 1503..150C; OpenHistoryWindow |

Build A adds the exact alternate event routes used by relocated controls and the
full game menu. `enhanced_event_binding`/`enhanced_submit_event` validate a fixed
catalog whitelist: session S01/S03/S04/S05/S14, N07/N08/N09/N10, P11, Y02/Y03/Y04/
Y05, E01, I04/I05 and K01/K02, as well as the discrete actions above. These are
original event entries, not independently implemented handlers or completed native
dialog/task bridges. Step C waits/results still use compatibility clients; live
trackers use the build B adapter. Map-plane 0106..08 remains distinct from world
0008..0A. Native menus use the shared relocated routes documented in [build B](build-b.md),
while original Yard/House transitions remain distinct. UI callbacks only retain intent data.

The additional `source_event`, `h`, `v` and `modifiers` fields retain an audited
source alternative and canonical pointer coordinates where needed, never HWNDs or
native client geometry. P11's native meter request uses percentage h and v=-1;
the executor converts it through the source 0011/0012 meter rectangle after owner
preparation, preserving integer quantization. The original coordinate form remains
available to compatibility controls. Buffered gestures/general task schemas remain unavailable.

`enhanced_submit_pan(dx,dy)` admits bounded N03 deltas. At the outer source seam,
its L route calls the complete existing `edit_scroll_and_redraw` operation without
an unnecessary owner raise or a new game event code. This is the same operation
reached by source Ctrl-arrow/edge navigation; its original clamp and XOR stepping
are retained. A middle drag commits one delta on release. Zoom, attachment,
window moves/resizes and extra-plane camera movement never call that operation.

The source owner preparation is deliberately explicit in the transcript: it can
draw, consume RNG, invoke hooks and flush. Same action and initial canonical
state always choose the same preparation. `win_Open`'s converted six-argument
ABI supplies zero original parameters, preserving unsupplied source values.
Both seam wrappers forward the converted `incoming_si` word, preserving the
existing caller-frame contract used by keyboard menu events. The ordinary
`DoEvent -> win_Events -> win_GetEvent` path still runs generic
selection/feedback/double-click classification and the original handler.
No bare ProcModeEvent/ProcCasteEvent call skips those effects.

At the outer source seam the executor defers if gameplay is unavailable, a modal
is active, a pending lifecycle menu command exists,
or the source ring has no room. Menu routes read the existing source disabled
bit. One intent executes per outer invocation. An object route finishes all owner
preparation/queue flushing before enqueueing the retained event once. The source
enqueue success is exposed by `portable_m1b73_try_enqueue_command`; failure is
recorded as a rejection rather than reported as delivery. A failed owner prelude
also rejects without an automatic retry.

The owner lease runs through the original outer DoEvent tail. Legacy native
close/raise/resize/menu requests remain pending while leased, so an SDL callback
cannot flush the action or switch its owner during delivery. Source lifecycle
effects still execute normally. The ledger separates submissions, preparations,
completed flushes, deliveries and rejected deliveries. Delivery is not a promise
of gameplay success: the original action may reject an absent target.

Build B adds live pointer transactions for world tools/brushes, Map, Yard,
triangles and Info links. See [the detailed source ownership rules](build-b.md).
GetMousePos/StillDown/myButton and the source dispatcher own tracking and effects.
Labelled allocation choices choose original reachable triangle pixels; they
never assign game levels. The narrow PlaceQueenInYard adapter queues only its
original viewport click at that existing source wait. Context menus retain
their original clients and take mouse ownership until their real release.

Nonempty buffered sample transcripts, arbitrary task tokens, native lifecycle/
file/dialog result bridges and unknown compatibility actions remain fail-closed.
Original context/proximity dialogs remain compatibility clients for step C.

## Executable verification

Use a fresh successful build report; tests reject changed input pins. Outputs
must be new paths. Children use disposable asset copies and bounded subprocesses;
headless SDL opens no user windows. Tests never ship game files or art.

```powershell
python portable/build.py --out build/workers/NAME/portable
python portable/tests/enhanced/run.py --build build/workers/NAME/portable --out build/workers/NAME/enhanced
python portable/tests/enhanced/invariance.py --build build/workers/NAME/portable --out build/workers/NAME/passive
```

`run.py` links read-only test probes over production objects. It reproduces the
real music-enabled death/rebirth path using ordinary `erad` keyboard input, and
compares actual rendered occupied cells against ground-only rendering while both
source banks are null. Phase 1 expects entity imagery. One inactive Caste-panel
click must produce exactly one Manual handler event and leave Auto disabled;
phase 3 owns that fix. The phase 1 rebirth regression is a required PASS, with a hybrid negative control
and equality of the complete semantic world at that wait. Build A repaired first
activation; the registration now requires both regressions PASS. A missing
precondition, timeout, crash or missing observation is an error.
The two-click positive control and semantic B01 executor must pass today,
including one post-flush delivery and rejection of duplicate serials.

`invariance.py` reuses the acceptance native observer, DWARF state schema,
SaveRec projection, all named raw view fingerprints, fixed validated ideal-machine
profile and sound-command comparison. Off/on and nineteen extra snapshot copies plus native cell/overlay
rasterizations use one executable, seed and input. It compares every raw view, including
UI/front state and raw stack suffix; it applies no new value masks. The established
ideal-state-v2 sidecars are diagnostic only for this comparison. Machine boundary
timestamps and source sound commands also compare. All first and subsequent
differences are retained by entry and name, with full state dumps at entries 1/3
and byte diagnostics. An independent test projection observes all resident source
window flags/geometry, object counts/selection flags and menu-state bytes even
when enhanced publication is off. A repeated off/off lane distinguishes baseline
variability from off/on differences. An offline SaveRec fingerprint
mutation must fail the comparison. Missing observations fail. Native layout
is exercised by the additional phase 2 stationary/repeat/layout-stress group;
see [its exact coverage and owner registrations](phase2.md).

The `contracts` group toggles only publication on the existing chooser-only
host. The `native-world` group uses the same complete `--windows` arrangement in
every lane, keeps publication enabled, and toggles only `SIMANT_ENHANCED_WORLD`.
If that hosting path changes source UI/clip state, the harness reports exact views;
the six-field historical check is not substituted for a full pass.

The historical phase 0 run reports raw differences rather than full passive equality.
Current phase 1 receipts and exact differences are in the task result; the harness
continues to reject full raw equality while any named view differs.
Repeated off/off runs already differ in `clip_rectangle_workspace`, the unused
`clip_window_z_order:raw` suffix, `fd_50F6_37FA` and `mode_knob_anim_index`.
The hybrid compositor comparison additionally differs in `g_4356`,
`mouse_button_state` and `clip_saved_rectangle_total`. The fixture and exact
entry/byte reports distinguish these observations; they do not establish a
physical-desktop root cause or justify a new mask. Source UI projections, live
logical order, SaveRec and RNG comparisons remain separate reported results.
The strict raw harness returns nonzero while those differences exist.

Gate registrations requested: run both new runners once after the fresh native
build, retain their result.json, and include the required PASS status for both rebirth and first activation.
The owner runs `python tools/validate.py --upper-tests`; phase 0 does not edit
the gate or repository tooling. Existing port suites and the complete 58-lane
upper-layer regression remain independent requirements.

## Retained reproduction recipes

The [evidence manifest](../../evidence/enhanced-mode/provenance.json) pins the
small authored/text evidence copied from the approved investigation. The
[resource census recipe](../../evidence/enhanced-mode/inspect_sources.py) and
[reference audit](../../evidence/enhanced-mode/reference_audit.py) reproduce
resource-derived scratch inventories. The [initial capture recipe](../../evidence/enhanced-mode/capture_current.py),
[extra captures](../../evidence/enhanced-mode/capture_extra.py),
[tool captures](../../evidence/enhanced-mode/capture_tools.py),
[dialog trace recipe](../../evidence/enhanced-mode/trace_dialog.py), and
[historical six-field check](../../evidence/enhanced-mode/check_invariance.py)
retain their original scratch paths and prerequisites. They do not become a
replacement for the new executable regressions/full-state harness. No copied
file contains game-art pixels or decoded game asset payloads.
