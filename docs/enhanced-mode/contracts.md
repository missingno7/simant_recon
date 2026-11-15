# Presentation contracts (phases 0 and 1)

The approved [design and complete component/action catalogs](../enhanced-mode.md)
are the authority. This is an opt-in preview with a phase 1 native world, not the docking workspace.
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
| Cards/help | Current card and previous ring, observed modal owner. Private draw-produced link tables and immutable text/style catalog are marked unavailable; empty arrays never mean successfully decoded content. No DisplayCard/DoWinHelp call during reading. |
| History/status | All ten 64-sample source series in documented data order, ring start/count, last OverallScore and copied edit status. No CalcScore. Draw-private graph selection and eight score metrics are explicitly unavailable. Label remapping remains the action catalog's `(g&1)*5+(g>>1)`. |
| Dialogs | Current front owner/flags, bounded copied Obj type/flags/rect/bitmap/text from resident native window reference views. No locking or resource loads; nonresident views stay unavailable. Text has truncation flags. This is an observation, not a guessed wait schema. `request_schema_available=0` blocks result injection. The token tracks observed owner/modal transitions, not yet every same-owner nested request. |
| Logical state | Full source stack copied independently of panel focus/layout. Native data never reopens a logical window. |

Unavailable fields are integration work for phases 1/5. They are not proof that
an opaque private source state is absent or a prompt accepts arbitrary Return,
Escape, Close or timeout. No native layout manager, file picker or controller
support is implemented by these contracts.

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
unproved routes return `ENHANCED_NEEDS_ADAPTER`. U never becomes a guessed action.

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
is active, a game tool owns interaction, a pending lifecycle menu command exists,
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

The following remain fail-closed rather than receiving approximate adapters:
N03 pan and all tile/held/brush/allocation gesture transactions; card-link IDs;
nested context/proximity results; source lifecycle/file/dialog result bridges;
unknown compatibility actions. A nonempty sample transcript or task token is
refused today. The design's complete per-action source entry, prerequisites,
effects and retained driving rules are the contracts for that later work.

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
and equality of the complete semantic world at that wait. Only the phase 3
activation regression remains XFAIL; XPASS still fails that registration. A missing
precondition, timeout, crash or missing observation is an error, never XFAIL.
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
mutation must fail the comparison. Missing observations fail. No enhanced layout
exists yet, so layout-change coverage is deferred explicitly.

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
build, retain their result.json, and include the strict expected-failure status.
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
