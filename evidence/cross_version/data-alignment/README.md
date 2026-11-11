# DOS addresses and original Win16 data names

This package asks which DOS SimAnt data addresses correspond to public data names
in the original Win16 symbol inventory. The answer is a set of auditable naming
claims, not a reconstruction of every object's original type, owner or extent.
Only a row with `delta: 0` names an object; other rows are supporting addresses.

The current result has **664 rows: 586 object bases and 78 supporting
addresses**. There are **101 Tier A and 61 Tier B object names not currently
registered under the Win16 name**. The registry already supplies 424 shared names.
The full change ledger, including corrections to earlier claims, is [ROUND2.md](ROUND2.md).

## Reproduce

From the DOS repository root, with Python 3.10 or newer and Capstone 5.0.3:

```powershell
python evidence/cross_version/data-alignment/run.py build/scratch/data-alignment
```

The destination must be a fresh directory strictly below `build/scratch/`. The
command refuses to overwrite it or write elsewhere. For another run, choose a
different fresh destination. Python bytecode-cache writes are disabled before
local imports. Capstone is read from `C:/tools/capstone-5.0.3` when present;
otherwise version 5.0.3 must be available in the Python environment.

The command decodes the original executables again, reconstructs control flow,
selects the current function cohort, extracts references, discovers pointer
tables, runs blind and seeded matching, and writes every intermediate observation
under the destination. No generated intermediate in this package, another output
directory or the Win16 reconstruction is an analysis input. The published JSON
files are read only after inference, as comparison targets. JSON uses explicit LF
line endings so byte equality survives a fresh Git checkout. Success requires both
structural and byte-for-byte equality of all four JSON artifacts, including row
summaries, and ends with:

```text
Blind calibration: 413 correct / 0 wrong / 11 missed; 0 stolen
```

`reproduction.json` records equality and wall time. `inputs.json` records every
input hash, the Python and Capstone versions, script hashes and the cohort digest.
`calibration.json` records each stage. `references.json`, `value-flows.json`,
`windows-import-uses.json` and the per-stage documents retain original instruction
sites and the observations needed to challenge a claim.

The final clean run reproduced all four artifacts byte-for-byte in **43.290
seconds** on this machine. Transfer controls, row uniqueness and summaries,
LF output, and refusal to overwrite an existing output directory were checked.

## Files and inputs

| File | Responsibility |
| --- | --- |
| `run.py` | Input locations, executable identities, cohort, isolated output and comparisons |
| `binary.py` | DOS/NE readers, loader fixups, entry/import resolution, CFG and reference extraction |
| `alignment.py` | Ordered references, save schema, layout, pointer contents, terminal candidates and calibration |
| `data_kinds.py` | Whole-value flows, initialized tables and strings, interior contents, indexed references and API uses |
| `reporting.py` | Tiers, publication exclusions, summaries, spacings and coverage |
| `matches.json` | Published address/name/delta rows with evidence and readable summaries |
| `object-sizes.json` | One next-public spacing observation per object-base row |
| `rejected.json` | Conflicting whole-value assignments, platform-state proposals and unsupported deltas |
| `coverage.json` | Status of all 852 Win16 data publics, Windows import evidence and map-pointer diagnostics |
| `ROUND2.md` | Complete changes against the preceding publication and seven registration cases |

All external data inputs are declared at the top of `run.py`:

| Input | What is read |
| --- | --- |
| `D:/Prog/simantw_recon/assets/SIMANTW.EXE` | Original NE bytes, segments, fixup chains, entry bundles and imports |
| `D:/Prog/simantw_recon/evidence/symbols/inventory.json` | Original Win16 public names, coordinates and code bounds |

The DOS inputs are `assets/SIMANT.EXE`, `layout/functions.json`,
`layout/symbols.json` and `evidence/cross_version/decisions.json`. No reconstructed
game source, Win16 analysis tools, cached disassembly or original game resource
files are needed. The executable identities are checked:

- DOS SHA-256: `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`
- Win16 SHA-256: `538fed3f0fd60a6528a5e5b20990361ac4d274c58266a81e71c24f751612589d`

The publication uses **890 function pairs**, selected from CONFIRMED/HIGH decisions
reviewed through 2026-11-11 and identical non-alias registered code names. The
preceding publication used 691. An intermediate run used 785; the current
decisions now supply 105 further eligible pairs. Thus the final cohort has 199
more pairs than the preceding publication. The freshly selected list must hash to
`1bb46b8ad41a303ee7d6dbd65a375869ee153653f8927e109e360a999758fea4`.
A later cohort change deliberately stops reproduction until its scope is reviewed.

## What the evidence shows

**Reference order.** Known correspondences divide each paired function into
intervals. Equal counts and widths suggest positional matches inside an interval.
A width occurring exactly once on each side provides a bounded relaxation with
stronger vote and usage requirements. The terminal indexed-reference projection
compares array accesses without intervening scalar platform state. It cannot
replace a rival mapping or supply later anchors. One function's order is weaker
than agreement across several pairs. Compiler and platform changes can reorder
accesses, so positional similarity is not universal proof.

**Usage overlap.** The sets of paired users support reciprocal candidates and
expose rivals. Usage cannot distinguish black/red, X/Y or A/B/R arrays always
used together; these families are never accepted from overlap alone. Usage counts
are conditional on the extraction population: the original order pass uses pairs
with references on both sides, while whole-value additions use distinct named
Win16 users across the cohort. A missing extracted reference is not proof of no use.

**Save schema and pointer contents.** Both originals have the same ordered
307-record size/count/far-pointer schema, at DOS `4E4B:0000` and Win16
`0008:9570`. The complete shape sequence and its terminators agree. Zero-based
record positions identify candidates independently of code order. Matching shape
does not prevent swapping two same-shaped objects, so Tier A also needs another
kind of evidence. Initialized pointer arrays are compared after translating
targets. A pointer to an array inside this schema is not a separate public pointer
variable with the same name as a Windows pointer view.

**Whole stored values.** Original call targets are resolved through DOS overlay
vectors and NE direct or movable-entry fixups. The analysis distinguishes AX's
low word and DX's high word, follows local spills, and compares return stores,
first-argument consumers and parameter stores. Matching creation and disposal
calls can identify an object even when DOS uses a four-byte far handle and Win16
uses a two-byte handle. Parameter positions assume the observed far-call frame
layout; ambiguous multiple stores are compared only with equal ordered counts.
When local addresses escape, calls invalidate slots at or above the lowest escaped
address. Raw BP copies invalidate the whole frame. Slots below all escaped
addresses are treated as disjoint local objects; unmodelled writes outside a
callee's addressed object remain a limit. Positive and negative transfer controls
exercise spills, low/high words and call invalidation on every run.

**String resources.** Equal constant IDs passed to `LoadStringAnt`, followed by
stores of the returned pointer list, identify corresponding message lists.
Consumers or layout provide separate support where available; result-only cases
remain B. This compares executable resource IDs and value flow, not the actual
resource text. Initialized near/far string-pointer arrays are also scanned for
the same ordered NUL-terminated strings; that search yielded no additional array
base. Exact initialized prompt strings do match directly inside DOS aggregates.

**Initial contents.** Exact substantial nonzero bytes are searched inside the
resident data image, including inside existing aggregate registrations. Relocated
bytes are excluded. Full spans require reciprocal uniqueness. Partial matches
need a common paired user or a unique prefix of at least 32 bytes with at least
16 nonzero bytes and six distinct byte values. An isolated content match remains
B. The matched prefix does not establish the extent of the original object.

**Local layout.** At least three agreeing pre-existing anchors establish a local
translation. Unregistered interior starts can be tested there; extending one
neighbor beyond the run requires matching nonzero contents. A two-byte scalar
also needs a paired user. This recovers sibling color tables and border bitmaps
without using their overlapping users to choose a member. DOS and Win16 reorder
uninitialized storage, so no image-wide displacement rule is assumed.

**Widths and offsets.** Compatible accesses corroborate a correspondence, but a
word width is too common to identify a variable. Interior support rows need a
consistent independently named base. Nearest-public arithmetic does not establish
ownership of private bytes between Win16 publics. This distinction corrects the
earlier yard-animation claim described in ROUND2.md.

## Tiers and counts

Tier A requires at least two substantive kinds of evidence with no unresolved
rival: for example save-schema position plus function evidence, initialized
contents plus local spacing, or corresponding creation and disposal flows. It is
naming evidence, not byte-exact proof of a complete C definition. Tier B is a
plausible candidate with limited independent support or a recorded rival.
Terminal gap/usage candidates stay B and never become anchors. A registered
spelling by itself supplies no fresh blind evidence.

| Scope | A objects | B objects | A supports | B supports |
| --- | --- | --- | --- | --- |
| Not currently registered under the Win16 name | 101 | 61 | 67 | 11 |
| All published rows | 506 | 80 | 67 | 11 |

## Calibration

The blind pass hides all **424** current shared data names as matching seeds;
unlabelled addresses and registration boundaries remain available. Afterwards,
each hidden label is counted as correct, wrong or missed. Assigning a hidden
Win16 name to another DOS address is separately counted as stolen. Every stage
below has zero stolen names.

| Stage | Correct / wrong / missed (424 controls) |
| --- | --- |
| order-blind | 334 / 0 / 90 |
| layout-blind | 410 / 0 / 14 |
| pointers-blind | 410 / 0 / 14 |
| bases-blind | 411 / 0 / 13 |
| terminal-gaps-blind | 411 / 0 / 13 |
| terminal-usage-blind | 412 / 0 / 12 |
| value-flows-blind | 412 / 0 / 12 |
| interior-contents-blind | 412 / 0 / 12 |
| layout-contents-blind | 412 / 0 / 12 |
| indexed-order-blind | 413 / 0 / 11 |

The original 131-name control set improves from **118 / 0 / 13** in the preceding
publication to **120 / 0 / 11** here. The intermediate 785-pair run, before the
new checks, gave **412 / 0 / 12** on the expanded 424-name set. Adding the remaining
105 live pairs changes candidate evidence and tiers while retaining that same
pre-enrichment calibration. The indexed projection adds the final recovered
control, `win_handles`; the platform-object exclusions retain **413 / 0 / 11**.

The additional 293 controls were accepted using the preceding method, so they
are useful regression controls rather than an independent random validation
sample. Zero wrong on controls does not prove all new rows correct: three earlier
A claims outside those controls required correction in this round. Those mistakes
and their replacements are explicit in ROUND2.md.

## Spacings and registration boundaries

`object-sizes.json` reports **distances to the next Win16 public**, the DOS
distance to that same mapped neighbor, and the distance to the next registered
DOS start. None is automatically `sizeof`. Of 586 records,
189 have equal mapped-neighbor distances, 277 have different distances,
and 120 lack a comparable mapped neighbor. Different distances often reflect BSS
reordering; they are not automatically contradictory matches.

| Win16 name | DOS address | Win16 next-public distance | DOS distance to that mapped neighbor |
| --- | --- | --- | --- |
| _PherMapA | 3E1D:D09F | 2048 | 2048 |
| _HistGraphColors | 3D57:087A | 20 | 20 |
| _HistButtStates | 3D57:088E | 20 | 20 |
| _RockTab | 3D57:08A2 | 16 | 16 |
| _WallTab | 3D57:08B2 | 16 | 16 |
| _CTabB | 3D57:048E | 24 | 24 |
| _CTabR | 3D57:04A6 | 24 | 24 |
| _bw_CTabB | 3D57:063E | 24 | 24 |
| _bw_CTabR | 3D57:0656 | 24 | 24 |
| _buffer_max_width | 55B3:673E | 2 | 2 |
| _buffer_max_height | 55B3:6740 | 48 | 48 |
| _left_wedge | 55B3:1DAA | 780 | unavailable |
| _casteAnimHandle | 50F6:37F2 | 2 | unavailable |
| _modeAnimHandle | 50F6:37F6 | 2 | unavailable |
| _yardAnimHandle | 50F6:10DA | 14 | unavailable |

The 72-byte DOS `HistGraphColors` scaffold contains the proposed 20-byte colors,
20-byte button states and two 16-byte terrain tables. The existing registration
must be split before those interior names become separate definitions.
`buffer_max_height` is a two-byte scalar followed by strings, despite its 48-byte
next-public distance. Only 16 initialized bytes are matched for `left_wedge`,
whose next Win16 public is 780 bytes away. The animation handles occupy four DOS
bytes and two Win16 bytes; the 14-byte yard public gap includes private caches.

## Remaining names and platform differences

`coverage.json` accounts for all 852 publics: 424 registered names, 101 new A
candidates, 61 new B candidates, 23 Windows-only representations and 243 unresolved
names. A B candidate is not an applied name.

These **23 names are Windows-only objects or platform state without a DOS object
of that representation**, supported by original USER/GDI/KERNEL import producers
or consumers retained in the coverage file:

`_antCursor`, `_bigFontH`, `_captureWnd`, `_clipDC`, `_clipWind`, `_digCursor`, `_dropCursor`, `_foodCursor`, `_hHelpCursor`, `_hInst`, `_lpTimerFunc`, `_magCursor`, `_mainRootWnd`, `_paletteH`, `_ribbonBarWnd`, `_rockCursor`, `_rootWnd`, `_smallFontH`, `_sprayCursor`, `_theDDEDataH`, `_updateRgn`, `_wSoundBlasterMsg`, `_win_hwnd`

This covers window/device-context/region/palette/font/cursor handles, instance
state, the timer callback, registered sound message and DDE memory state. It does
not mean the DOS game lacks analogous cursor, window, font or sound behaviour.
The Windows caste/mode bitmap caches are separate from the DOS animation handles;
their old DOS candidates are withdrawn, while they remain unresolved as complete
cross-version objects rather than receiving speculative DOS addresses.

For the five `PherMap*Ptr` views, initialized targets agree with already named
arrays, but every corresponding DOS relocated pointer found is inside the save
schema. No separate DOS pointer-variable base is established. These stay
unresolved, not Windows-only merely because no paired use was extracted.

Other limits include inlined or unpaired functions, unresolved indirect control
flow, register-derived addresses not grounded by the extractor, changed argument
layouts, zero-initialized key globals, compiler-specific runtime data and resource
contents stored outside the executables. Balloon arrays now have parameter/order
evidence, but several remain B; `CurBalloonCnt` is still unresolved. A missing
candidate never proves absence of a DOS object.

## Add or challenge a row

Start with a row's summary and its structured observations. Reproduce into a
fresh directory, inspect the listed original instructions, table records, bytes
and neighboring symbols, then check competing addresses and the whole storage
value, including far-pointer halves. For a sibling family, explain which member
the non-usage evidence selects. Record any counterexample at its original site.

Change the smallest general rule that explains the evidence in the appropriate
module, rerun both seeded and blind passes, and inspect `calibration.json` and
`rejected.json`. Keep wrong and stolen controls at zero; report tier changes,
removed rows and changed addresses explicitly. Review fresh results before
replacing the four published JSON files, and then rerun the one command from a
second fresh directory to verify exact reproduction. A new cohort also needs a
reviewed digest update. Use the repository naming/promotion workflow separately
for registrations and source changes; this package performs none.
