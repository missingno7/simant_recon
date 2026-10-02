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

The native unit gate is `python portable/tests/run.py --host`. Its report lives
under ignored `build/portable/tests/`; original-DOS differential producers and
retained reports live beside each suite. No original assets, DOS executables,
compiler binaries or generated native binaries are redistributed.

Large ant modules are also being tested through mechanical source reuse under
`research/source-reuse` and `tools/recover_source.py`. Generated diagnostic
objects do not enter the game build. That path must preserve shared aliases,
16-bit arithmetic and MSC return behavior, and replace scaffolds with proven
semantics before it can become a production core.
