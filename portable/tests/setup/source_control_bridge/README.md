# Source control events in the SDL build

`portable/game/recovered/control_adapter.c` now executes the original
`ProcCasteEvent`, `ProcModeEvent`, `IsPointInIsoTri`, `BoundPointToTri`, and
`GetTriLatDist` bodies from frozen `src/root/m0798.c`, in their original order.
`portable/tools/convert_control_events.py --verify` reproduces their include
and identity file. The recipe retains their switch cases, fallthrough, loop,
expression order, and six-byte copies. It converts DOS scalar spellings and
segment qualifiers, maps platform calls to typed providers, and translates
the existing flat three-word arrays without incompatible struct-pointer casts.
This is a selected source conversion, not a complete m0798 TU port.

The Next10 source/state files are unchanged. Actual compiled `SetTriLatPoint`
and `cvtLevels2IdealCaste` remain dependencies. Selectors borrow the caller's
`SimSetupControls` words and percentages borrow its private-state words. Other
game state belongs to the active recovered TLS image. Publication exposes
only the selected window's changed fields before each host callback. There
is no persistent duplicate selector/percentage owner.

[Production v2](evidence/production-source-controls-v2-20261002.json) passes
all 34 retained original-DOS cases and compares return status, selectors,
levels, presets, percent, caste distribution, source point projection, and
ordered service calls. Original handler captures stubbed drawing; the point
comparison uses the separately recorded source draw projection. This replay
does not execute DOS anew. Unrelated-window sentinels, re-entry rejection,
explicit drag cap, partial writes on draw/group failure, recovery, and an
outer interruption followed by a fresh call also pass. Compiler subprograms,
Python, MinGW's setjmp header, and 29 local source/header dependencies have
stable pre/post pins. Fixture stubs for unused startup leaves are not exercised.
V1 is preserved: its dependency scan omitted the event-enable macro, although
the compile enabled it and the generated include/internal header were explicitly
pinned. V2 corrects the scan without changing any implementation.

The separate [engine test](../control_engine/evidence/control-engine-source-next10-20261002T205318Z.json)
passes its 15 bounded engine cases, including resource-backed NewGame, one
actual simulation tick, ten successful events, callback-visible state, private
state lifetime across RandYard, and provider-fault cleanup/recovery.
The outer engine abort clears borrowed event aliases before unbinding TLS.

[SDL input](../../live_controls/evidence/live-source-controls-next10-v1-20261002.json)
passes ten control actions from 34 injected SDL events and 32 subsequent ticks.
Its expected multi-step state comes from the retained independently compiled
control model; the complete mouse sequence is not replayed in DOS.
[History regression](../../live_history/evidence/live-history-source-controls-build-v1-20261002.json)
also passes on this build. The shared native gate passes 50 suites and the
224,000-pixel host presentation check. These are bounded checks, not a
whole-game or DOS framebuffer equivalence claim.

Windows MinGW SEH-mode `setjmp`/`longjmp` crashed the outer-interruption probe
with `0xC0000005`. The failing v3e report and source versions remain under
`archive/v3e/`. Changing only the supplied native compiler switch
`__USE_MINGW_SETJMP_NON_SEH` makes every v4 control pass. The SDL host and engine
probe use that mode; all source/TLS/RNG/audio bindings have explicit cleanup.
This is a host control-transfer choice, not a change to recovered game logic.
The archive's recipes retain their original scratch paths; restore those paths
when reproducing them. Prior production adapter/build sources are also retained.

Drawing and other host services remain explicit providers. Unsupported services
still fail visibly. The old handwritten control model remains available for
isolated comparisons and tests; the production event adapter no longer calls it.
The frozen EXACT/BEHAVIOR_EXACT registry and DOS oracle tag are unchanged.
