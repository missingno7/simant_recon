# Native integration proof boundaries

The historical tag `dos-semantic-oracle-v1` is immutable input. Native proofs
below do not change its EXACT or BEHAVIOR_EXACT categories. Each comparison is
finite and applies to the input versions and observables recorded in its report.
Source changes require review and a relevant rerun before a current claim.

The [41-suite native gate](../tests/evidence/native-unit-gate-41-20261002.json)
adds the EndGame flow and resource-backed view checks to the previous gate.
It compiles 52 shared translation units and records the actual SDL host run.
These are native regression checks, not original-DOS equivalence proofs.

| Native boundary | Evidence | Current limit |
| --- | --- | --- |
| SDL3 input, indexed presentation and clock | Real SDL queue tests and independent BMP inspection of 224,000 pixels | Host boundary only; CPU-exported framebuffer, no DOS VGA comparison |
| GetMyRandDirs | 322,720 original-DOS comparisons; return, rot/dir and ordered tile-query arguments | Controlled archived domains, including 100,000 random cases |
| TileCanBeMovedOn | 18,440 original-DOS comparisons | Direct map/neighbor and boundary domains |
| EnterNest and digging helpers | 5,937 original-DOS comparisons | Directed, dirt/grass and random state; host requests captured |
| ExitNest and yellow movement | 128 direct ExitNest comparisons and 5,000 integrated yellow-movement comparisons | Recorded plane/state domain; pickup, dropping and population service closure remain separate |
| SpiderScan | Corrected 10,146 original-DOS comparisons; independent corpse-base and corpse-ring state | Earlier report retained as superseded mapping evidence; laser output is a typed host request |
| MoveSpider | 10,146 original-DOS comparisons, including actual scan and RNG | Route queries and presentation effects use the stated service boundary |
| Ant list/player primitives | 5,043 original-DOS comparisons | List capacity, rebuild, life placement and health; not full ant simulation |
| CountAnts | Seven directed original-DOS comparisons | Population bins, queen-loss gates, RNG and ordered song/report requests |
| Database/LZSS/FindIndex | All 840 records loaded; 205 original decodes; 1,454 lookup probes | Three reserved one-past matches require the explicit compatibility interface |
| Scenario/dialog windows | 141,192 original hit-test comparisons plus load/recalc controls | Same-window constraints; actual EGA profile, no unimplemented autosizing |
| Startup window registry | Every object in five startup windows compared at load and after original Recalc | Lookup preserves current coordinates; recalculation is explicit |
| Bitmap/font primitives | Packed resource 2500, eight transparency shifts, FONT2 widths and glyph raster compared to original DOS | Physical VGA presentation excluded |
| Ground/life tile raster | All asset frames tested; 140 original-DOS scratch-raster comparisons | Normalized EGA readback; physical graphics-controller behavior excluded |
| Map cell composition | 272 original-DOS selection/command comparisons with the proven tile raster | Profile 0/8, 16-pixel cells; full window presentation separate |
| Terrain/MakeMap | 950 passing original-DOS cases from 953 attempts | Three seed-zero DOS nonterminations recorded separately; lion state is zero in this boundary |
| Water | 50 original-DOS operation-sequence cases, including 800 initial drop placements | Rain is a caller input; sound and invalidation are ordered host requests |
| Feeding and AddFood | 126 original-DOS comparisons | Health, map/food counter, Q15 placement, RNG and ordered sound requests |
| Colony scent and alarm smoothing | 360 original-DOS comparisons across five helpers | Full scent grids and distinct smoothing scratch state; whole DoSmells orchestration separate |
| Audio sample decoder | All 57 original-DOS sample records compared byte for byte | PCM decoding and logical sound mapping; playback rate, mixing and music remain separate |
| initControls | Original-DOS startup comparison of presets, geometry, levels and ordered close requests | Loaded, closed windows 18/19; existing animation handles are null |
| RandWorld | 12 original-DOS comparisons with full generated maps, lists, RNG and counters | Scenarios 0/1, nest sizes 1/1, default terrain, listed seeds; NewGame resource composition separate |
| RNG | Original-DOS helper comparisons plus separately counted exhaustive recurrence checks | Invalid zero divisors rejected explicitly; unsigned/signed helper domains recorded in the suite |
| DoAntSim scheduler | Source call-order and counter unit tests | Full simulation services remain required; no placeholder service may stand in for a game rule |
| Edit object-4 command | Eight DOS/native comparisons from resource-backed NewGame state; 371 mapped fields, ordered service arguments/results, clock and RNG | Controlled quick-release boundary on planes 0–3; physical SDL press/release and double-click pumping have separate integration tests |
| CalcScore | 63 DOS/native comparisons of the long return and eight score components | Numeric scoring only; game-over modal and subsequent NewGame/MenuQuit flow remain separate |

The native unit gate is `python portable/tests/run.py --host`. Its report lives
under ignored `build/portable/tests/`; original-DOS differential producers and
retained reports live beside each suite. No original assets, DOS executables,
compiler binaries or generated native binaries are redistributed.

Large ant modules are also being tested through mechanical source reuse under
`research/source-reuse` and `tools/recover_source.py`. Generated diagnostic
objects enter only explicitly selected diagnostic integration builds. That path must preserve shared aliases,
16-bit arithmetic and MSC return behavior, and replace scaffolds with proven
semantics before it can become a production core.

The next2 source profile has now passed three consecutive 256-tick DOS
comparisons (768 ticks), with 370 nonpointer globals, both RNG states and
ordered host arguments checked at every tick. See the
[current next2 replay](../research/core-proof/original-256-tick-summary-next2-lazy-clock-final-20261002.json).
The original captures retain their earlier profile provenance; next2 has the
same header and 23 game bodies, with separately recorded initializer changes.
The full-state fixtures are research inputs, never native startup data.
This replay uses the explicit static two-sample EnterNest clock lane. The live
lazy clock provider has separate source-order controls and SDL integration
checks; the replay does not certify a physical-clock input domain.

The [resource-backed startup comparison](../tests/core/evidence/randyard-session-startup-next2-20261002.json)
separately checks 146 ranges, both 32-value RNG tails and the final game-RNG
seed. It executes real resource initialization and NewGame, with no DOS
snapshot hydration. Pointer-valued resources and the stated UI boundary stay
outside that comparison. Source DATA overlaps now share backing storage, and
the scalar initializer audit records exact-span readable declarations.

The [43-suite native gate](../tests/evidence/native-unit-gate-43-20261002.json)
and the real SDL host checks pass at their pinned input versions. They are
unit/integration checks, separate from DOS behavioral proof. Window opening,
picture modals, ribbon text and live actions require their own host contracts;
passing the simulation fixture does not certify those interactive services.

The [current proof audit](../research/native-proof-triage-20261002.md) separately
tracks reports whose inputs still match, reports preserved for earlier input
versions, and reports with incomplete dependency pins. A passing archived run
does not automatically certify a changed native implementation.

The [longer headless run](../tests/core/evidence/long-run-smoke-next2.json)
completed 2,687 no-input ticks before reaching the unsupported `EndGameDialog`
service. The source trigger was red-queen extinction. This identifies a normal
game-over integration task; it is not a 4,096-tick pass or a DOS differential.
The host acknowledged typed presentation requests without rendering them.

The SDL smoke receipts retain executable/source identities, logical time,
RNG and final state checksums. Pointer-normalized checksums remove only native
pointer fields for diagnostics; they are not a DOS equivalence gate. Unbound
Tab injection is a test-only event driver and does not prove modal dismissal.

The original Edit mouse producer, the historical MSC-compiled source checks,
and the [portable-native code-4 differential](../tests/input/evidence/native-process-edit-code4-lazy-clock-20261002.json)
are distinct proof lanes. The 49-case MapAreaEvent report is a DOS/MSC source
comparison with a separate event-DTO check; it is not a portable-native gameplay
differential. The native eight-case suite initializes the DOS VM from native
pre-call semantic state and compares the resulting state. It never uses a DOS
snapshot to initialize native NewGame.

The [overview raster differential](../tests/render/evidence/dos-overview-selector-raster-differential.json)
compares original S00 planar output, normalized to indexed pixels, against the
native 4-by-4 selector conversion. All selectors 0–23 pass in four controlled
cases covering both converter entries and profiles 0/8. This corrects the
earlier direct-palette interpretation of selectors above 15. It establishes
the conversion boundary; full window composition and physical VGA behavior
remain separate.

The [corrected CalcScore report](../tests/dialogs/evidence/calcscore-original-dos-portable-20261002-corrected.json)
retains its original passing predecessor. Source alias review confirms that
`EndGameDialog` continues with `NewGame(0)` and calls `MenuQuit` on a negative
result. Its unresolved services concern that modal/restart/quit lifecycle.

The separate [EndGame flow comparison](../tests/dialogs/evidence/end-game-dos-native-flow-20261002.json)
matches five controlled original-DOS/native cases, including callback order,
closing, delayed SongDone, SRand2 consumption, NewGame and MenuQuit requests.
Its callbacks are controlled services. It does not certify live SDL modal
events, resource rendering, restart, save, or quit implementations. The native
resource-backed view has its own regression cases in the 41-suite gate.

The [balloon cue packet](../tests/recovered/evidence/balloon-adapter-dos/README.md)
records 164 original-DOS/native state matches and four detected negative
controls. The next3 profile supplies twelve omitted source fields while
preserving all 23 next2 generated bodies and prior field initializers. Cue
submission emits no host calls. Visible frames and the timer/RNG-driven message
selection remain separate boundaries; this packet does not replace the frozen
DrawBalloons contract. The [profile recipe](recovered-source-next3-recipe.md)
and [build-input controls](../tests/recovered/evidence/next3-profile-build-input-controls-20261002.json)
record reproduction and identity rejection checks.

The [next3 replay](../research/core-proof/original-256-tick-summary-next3-common370-20261002.json)
also passes 768 ticks over the same 370-field comparison boundary. Its twelve
new cue fields are excluded from those old captures, and no cue was activated
in the three streams. The 164-case cue packet supplies separate state evidence.

The [setup reuse proof](../tests/setup/evidence/setup_reuse_differential_report.json)
shows that initControls copies mutable DATA defaults into current levels and
only preset row zero. Rows one through three and private selectors survive
reuse. The [refreshed startup proof](../tests/core/evidence/randyard-session-startup-setup-reset-20261002.json)
checks 146 source ranges and RNG tails after that correction. These reports
retain exact input versions and preserve their predecessors.

The selected next4 controls have a [direct DOS packet](../tests/recovered/evidence/controls-next4/README.md)
and [profile recipe](recovered-source-next4-recipe.md). Their session bridge and
actual engine RandYard entry need separate integration checks; the controls
packet alone does not certify either boundary.

The [scenario flow differential](../tests/dialogs/evidence/scenario-flow-differential.json)
passes 274 cases with ordered timer/key/event calls, including signed clock
transitions. Its [SDL modal test](../tests/dialogs/evidence/scenario-modal-host.json)
checks actual resource selection, Escape, quit cleanup and framebuffer restore.
File loading after event 0x0207 is outside that modal.

The [balloon queue packet](../tests/windows/evidence/balloon-queue-v1/README.md)
compares 107 AddMsgBalloon cases and 55 DrawCurBalloons cases against DOS,
including timer/RNG ordering and a signed timer boundary. Tables in that suite
are controlled fixtures; full resource-backed balloon raster integration is
still separate.

The [matched next4 SDL EndGame smoke](../tests/live_game/evidence/end-game-modal-smoke-next4.json)
opens, renders and closes resource 0x0400 with actual SDL Escape input and
reaches the named NewGame(0) boundary. It checks production input identities
and stable dependencies. It does not prove automatic game-over triggering,
restart, save or quit; the selected source continuation is being integrated.

The [selected NewGame flow packet](../tests/recovered/evidence/newgame-flow-next5/README.md)
compares 128 NewGame cases and two SetDefaultWindows cases against original
DOS execution. RandYard and UI leaves are controlled callbacks. Two volatile
fastcall values are captured from the DOS lane and replayed at native service
boundaries, so that packet does not independently prove their native values.
The [16-case ABI probe](../tests/recovered/evidence/newgame-zoom-abi/report.json)
separately executes the original query and clip_Off bodies and establishes
window 0 as the implicit argument for this NewGame tutorial callsite.

The [next6 live restart smoke](../tests/live_game/evidence/newgame-202-live-smoke-forced-next6-pass.json)
uses a compile-only diagnostic engine action to enter EndGame on the test
session. Physical SDL Escape dismisses that modal; a resource-derived click
selects scenario 0x0202. Actual source NewGame/RandYard return normally, and
the child completes a simulation tick. This host check does not compare DOS
state or pixels, prove a natural game-over trigger, or cover tutorial, load,
save and quit. Its failed predecessors retain the missing dismissal,
UpdateEdit and SetMapTitle boundaries. The report pins its exact native build;
later source/profile edits make it historical evidence, not a current receipt.

The startup bridge now retains fd_50F6_0B22 from the resource-backed sine
table, matching initStuff's kind-9 object-1000 lifetime. Actual RandYard uses
that pointer through fracSIN/fracCOS. The next6/next7 explicit RNG sequencing
is documented in [compiler lowerings](compiler-lowerings.md); passing
source-order controls alone does not establish whole-RandYard equivalence.

The [next7 captured replay](../research/core-proof/original-256-tick-summary-next7-captured370-20261002.json)
passes 768 preserved DOS tick boundaries for 370 fields, both RNG streams,
and ordered callback traces. Its other 41 profile fields are explicitly
excluded. The captures were not regenerated; the report retains capture,
producer, compiler-input, object, executable, and dependency-closure identities.
It uses static nest-clock samples and does not certify live UI callbacks.

The [menu interaction packet](../tests/menus/evidence/menu-interaction-differential.json)
compares 13 original-DOS/native directed input sequences, including navigation,
disabled/separator rows, accelerators, cancellation, selection, and forwarded
events. The real SHARED resource supplies title hit geometry. Rendering and
SDL event collection have separate boundaries. The MenuQuit and zoom models
also have finite controlled-service differentials; their host implementations
must be reviewed before they are connected to live gameplay.

The [next7 natural restart smoke](../tests/live_game/evidence/natural-gameover-fast-202-live-smoke.json)
uses physical Shift+4 to select source speed 3, preserving the logical clock.
The actual simulation calls EndGame at completed tick 2,879 (world tick 2,880),
then SDL Escape and a resource-derived scenario-0x0202 click return through
source NewGame. The run continues to tick 3,798 before a test-only Quit event.
No diagnostic EndGame action is used. Native inputs remain stable and source
modal/RNG snapshots are retained. This is a bounded host integration test,
not a DOS state/pixel comparison or a save/quit implementation claim. The
earlier 58-second default-speed timeout is preserved; source pacing makes
that timeout insufficient to reach the game-over point.

The [S11 menu adapter comparison](../tests/menus/evidence/procmenu-next7-dos-differential-adapter-20261002.json)
passes 84 original-DOS/native cases. Its bridge constructs the seven-word S11
event, with command at byte 12, rather than reusing the eight-word S22 edit
event. Tests include FD-prefixed words and a wrong-layout negative control.
SetPause and SetMenuEntries execute source bodies; other host operations are
controlled leaves. This proves that finite source-dispatch boundary, not live
menu, save, quit or NewGame lifecycle behavior. The new engine action places
this bridge inside its normal state/RNG/host binding and terminal failure
boundary; its integration checks are recorded separately.

The [next8 profile](recovered-source-next8-recipe.md) corrects the S24 history
event's host-width `unsigned` to the source ABI's 16-bit `uint16_t`. All 25 TUs
compile and 64 directed original-DOS/native callback traces match. A prior-width
control misses branches when the following event word is nonzero. State files
and the other 24 modules retain their next7 identities. The 768-tick next7
receipt is preserved as that profile's evidence, rather than renamed.

The control-window renderer has a [45-command original-DOS trace](../tests/setup/render_controls/evidence/control-window-render-trace.json)
and a [separate native raster receipt](../tests/setup/render_controls/evidence/control-window-raster.json).
The latter uses active HCEGANT geometry, fonts, colors and knob resource,
preserves caller clipping, and has no direct DOS framebuffer comparison.
Those two fixtures use different initial window geometry and are not combined
into a pixel-equivalence claim. Live composition now paints Edit contents and
each ribbon with their owning window during the back-to-front pass, so a front
window can cover them. Complete control interaction remains separate.

The [legacy save codec](../tests/save/evidence/legacy-save-codec-v1/README.md)
validates the source-derived 307-record, 48,386-byte payload mechanically with
synthetic fields. It requires every binding and prevalidates decode destinations.
The [Next9 extension](recovered-source-next9-recipe.md) adds the seven missing
state members without changing inherited members or generated module bodies.
The preserved [V2 stream packet](../tests/save/evidence/legacy-save-codec-v2/README.md)
captures actual original-DOS SaveGame writes and reproduces their 48,386-byte
stream in its stated startup domain. An independent audit found thirteen
coordinate-pair records whose V2 conversion incorrectly uses 32-bit component
width on big-endian hosts. Decode/encode round trips alone do not detect this.
The [V3 binding packet](../tests/save/evidence/legacy-save-codec-v3/README.md)
uses an independent catalog of all Next9 backing members and source-address
sentinels. Its native little-endian and forced-big-endian encodings match one
actual DOS SaveGame stream (307 writes, 48,386 bytes). Swapped bindings, wrong
point-component width, and numeric interpretation of a raw table interior
each fail the comparison. This finite binding proof does not establish the
file lifecycle or all runtime states. The codec remains outside the live build;
live filesystem/save/load services remain unfinished. V2 evidence is retained.

The [49-suite native integration gate](../tests/evidence/current/20261002/native-gate-49-menu-controls-final-20261002.json)
passes with stable compiler inputs, including dropdown command plans, active
menu title modes, and resource-backed control rasterization. Its SDL host test
compares 224,000 exported presentation pixels against the host fixture and
checks keyboard, quit, and monotonic-clock boundaries. These are native host
checks; they add no original-DOS differential cases to the frozen certificate.

The [fresh 84-case menu packet](../tests/menus/evidence/procmenu-next7-dos-differential-adapter-complete-closure-20261002.json)
pins the compiler's non-system dependency closure and records stable inputs
before and after execution. The previous receipts remain preserved. The
[21-case engine packet](../tests/menus/evidence/engine-procmenu-next7-selected-closure-20261002.json)
checks the public command boundary after one source simulation tick; menu
actions preserve RNG and tick counts and clean up their state bindings.
It explicitly retains the unsupported `StopSong` service reached by FD32.

`portable/.gitattributes` preserves byte-pinned native source and evidence
inputs during checkout. It applies only to the port tree and does not change
historical reconstruction files or their frozen identities.

The [physical menu smoke](../tests/live_menu/evidence/physical-menu-slow-final-next8-20261002.json)
passes three SDL mouse drag/release interactions: Slow, Pause, and Unpause.
It completes 32 source simulation ticks with nine injected events, exactly
30 menu-state writes and three menu-text writes, and a 700 ms pause interval.
Its 212 production inputs and test inputs remain stable before and after the
run. All state captures, geometry, events and native screenshot have distinct
artifact identities. This uses SDL's dummy driver and proves that bounded
host route; it does not compare DOS state or framebuffer bytes. Earlier
timing, assertion-count and incorrect-description receipts remain archived.
