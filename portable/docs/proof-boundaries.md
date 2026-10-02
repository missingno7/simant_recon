# Native integration proof boundaries

The historical tag `dos-semantic-oracle-v1` is immutable input. Native proofs
below do not change its EXACT or BEHAVIOR_EXACT categories. Each comparison is
finite and applies to the input versions and observables recorded in its report.
Source changes require review and a relevant rerun before a current claim.

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
[current next2 replay](../research/core-proof/original-256-tick-summary-next2-lazy-clock-20261002.json).
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

The [39-suite native gate](../tests/evidence/native-unit-gate-39-20261002.json)
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
