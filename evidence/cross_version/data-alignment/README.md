# DOS addresses and original Win16 data names

This package asks which data addresses in the DOS SimAnt executable correspond to
public data names in the Win16 release's original symbol inventory. It records
evidence for names, including competing interpretations. It does not rename source
or establish the original C type, owning file, or complete allocation of an object.

The result contains **389 new object-name candidates: 300 Tier A and 89 Tier B**.
It also includes 131 names already shared by the DOS registry and Win16 inventory.
There are 595 rows: 520 object bases and 75 supporting interior addresses. Only a
row with `delta: 0` names an object. The total tier counts, including existing names
and interior addresses, are 483 A and 112 B.

## Reproduce

From the DOS repository root, with Python 3.10 or newer and Capstone 5.0.3:

```powershell
python evidence/cross_version/data-alignment/run.py build/scratch/data-alignment
```

The destination must not exist. Use another fresh directory under `build/scratch/`
for another run. The command refuses destinations elsewhere and never overwrites
an earlier result. It disables Python bytecode-cache writes before importing the
package. The pinned Capstone installation is `C:/tools/capstone-5.0.3`; alternatively,
Capstone 5.0.3 can be available in the selected Python environment. Its version is
checked. The dependency location is declared at the top of `run.py`.

The command regenerates Win16 instruction decoding and control-flow information
from the executable. It discovers function pairs and initialized pointer tables,
runs matching with and without shared-name seeds, applies publication filters,
and writes all observations and results into the fresh destination. It reads no
generated disassembly cards, saved reference lists, tables, or other intermediates
from this package or another project.

Only after inference has finished does it read the published JSON files to compare
them with the fresh results. `matches.json` is compared in full, including every
summary and structured evidence field. Object spacings and rejected candidates
are compared as well. Success prints `Published rows: EQUAL (595 rows)` and ends
with:

```text
Blind calibration: 118 correct / 0 wrong / 13 missed; 0 stolen
```

A clean reproduction took **24.854 seconds**. All three published JSON artifacts
also matched byte-for-byte. The generated `reproduction.json`
records the measured wall time and comparison verdicts. `inputs.json` records input
and script hashes and the Python and Capstone versions. Every inference stage,
function pair, reference site and detected save-table record is available in that
output directory for inspection.

## Files and inputs

| File | Responsibility |
| --- | --- |
| `run.py` | Input locations, executable identities, study scope, fresh-output rule, orchestration and comparison |
| `binary.py` | DOS/NE readers, Win16 control-flow reconstruction and ordered data-reference extraction |
| `alignment.py` | Reference matching, pointer-table matching, layout/content checks, member checks and calibration |
| `reporting.py` | Publication filters, tiers, readable row summaries and object-spacing observations |
| `matches.json` | Published address/name/delta rows and their evidence |
| `object-sizes.json` | One spacing record for each of the 520 object-base rows |
| `rejected.json` | The conflicting yard-array base and 15 unsupported interior-address proposals excluded from publication |

The external inputs are declared at the top of `run.py`:

| Input | What is read |
| --- | --- |
| `D:/Prog/simantw_recon/assets/SIMANTW.EXE` | Original NE bytes, segment records and loader fixup chains |
| `D:/Prog/simantw_recon/evidence/symbols/inventory.json` | Original Win16 public names, their coordinates and upper bounds for code symbols |

No Win16 reconstructed source, Python tools or generated disassembly is needed.
The inventory is an input describing the original symbol file; its executable
identity is checked. Win16 source declarations are not used to infer DOS sizes.

Within the DOS repository, the command reads `assets/SIMANT.EXE`,
`layout/functions.json`, `layout/symbols.json`, and
`evidence/cross_version/decisions.json`. These provide the original DOS image,
function bounds and switch metadata, registered data boundaries, and reviewed
function correspondences. Pointer-table entries and instruction operands are read
again from the original bytes, not from a compiled reconstruction.

The required executable SHA-256 values are:

- DOS: `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`
- Win16: `538fed3f0fd60a6528a5e5b20990361ac4d274c58266a81e71c24f751612589d`

### Function-pair scope

This result uses the original **691-function-pair study cohort**. Pairs come from
CONFIRMED/HIGH correspondence decisions reviewed no later than **2026-09-30**,
undated established decisions, and identical non-alias registered code names.
The cutoff describes the scope of the supporting function reviews, not the date
the executable analysis runs.

The current registry also contains 94 later reviews dated 2026-11-11. Adding those
pairs would be a larger study and would change reference counts and evidence.
They are not silently included when reproducing this publication. `run.py` checks
the selected pair list against its recorded cohort digest. A change to eligible
code registrations or earlier decisions therefore requires an explicit scope review.
The full freshly selected cohort is written as `function-pairs.json`.

## What the evidence shows

**Reference order.** Already matched references divide a paired DOS/Win16 function
into intervals. Equal reference counts and widths allow ordered candidates inside
an interval. A bounded relaxation matches a width that appears exactly once on
both sides, with stronger corroboration requirements. Multiple independent function
pairs are stronger evidence than one. Compiler transformations, added platform
state and changed control flow can change reference order, so order is not a
universal positional rule.

**Usage overlap.** The analysis compares the sets of paired functions that use each
address. A reciprocal best match with a clear margin supports a correspondence.
Usage cannot distinguish arrays that are always used together. Recognized black/red,
X/Y and A/B/R sibling families are excluded from the usage-only pass. Other evidence
is required to distinguish their members.

**Initialized pointer tables.** Both executables contain a 307-record save schema
with the same ordered element sizes and counts. The DOS table begins at
`4E4B:0000`; the Win16 table begins at `0008:9570`. Every record and the zero-count
terminators are present. Corresponding relocated pointers provide address/name
candidates independently of instruction order. Record indices in the JSON and row
summaries are **zero-based**. Equal shapes alone would not detect exchanging two
same-shaped pointer targets; function use, local layout or other evidence must
corroborate such candidates for Tier A.

**Layout spacing.** Several neighboring mappings with the same displacement support
interpolation in a local region. At least three agreeing anchors are required.
Extending one public beyond such a region also requires equal boundary distance and
matching nonzero initialized contents. The DOS and Win16 linkers generally reorder
uninitialized data, so a global displacement rule is not assumed.

**Initial contents.** Exact nonzero byte equality, with reciprocal uniqueness, can
identify initialized tables. Bytes carrying relocation obligations are excluded
from this comparison. Equality of zero-filled storage is not counted as independent
evidence. A byte comparison covers the stated span; it does not establish the type
or prove that a gap before the next public is part of the same object.

**Access widths and member offsets.** Matching byte/word/dword accesses corroborate
the proposed interpretation. Consistent interior offsets can establish an object
base when boundary spacing also agrees. A width alone is too common to identify a
variable, and a member offset alone does not establish the whole object's ownership.

The `summary` on each row is a short description derived from these observations.
The structured evidence retains exact sites, function names, record positions,
widths, distances and rival votes needed to check that description.

## Tiers

**Tier A** requires at least two substantive kinds of evidence and no unresolved
rival. Examples include a save-table position plus corresponding function use, or
an initialized drawing table whose contents and local spacing both agree. An A
classification is evidence for a recovered name, not byte-exact proof of the DOS
object's definition or owning translation unit.

**Tier B** is a plausible correspondence with limited decisive evidence, or a
candidate whose rival order votes remain recorded. Examples include a single
function's bounded reference interval and an isolated initialized-content match.
The final bounded-interval and usage-only passes remain B and never supply new
anchors for further matching. Existing shared names without fresh corroboration
also remain B rather than acquiring confidence from their spelling alone.

| Scope | A object bases | B object bases | A interior rows | B interior rows |
| --- | ---: | ---: | ---: | ---: |
| New candidates | 300 | 89 | 67 | 8 |
| Existing shared names | 116 | 15 | 0 | 0 |
| Total | 416 | 104 | 67 | 8 |

## Calibration

The 131 non-alias DOS data names already shared with the Win16 inventory form the
control set. Blind matching does not use those DOS spellings as matching seeds.
Unlabelled DOS addresses and registered boundaries remain available, as do all
Win16 names. After inference, the results are compared with the hidden labels.
Each known address is counted as correct, wrong or missed. A known Win16 name
assigned to a different DOS address is counted separately as stolen.

The published blind result is **118 correct / 0 wrong / 13 missed**, with **zero
stolen names**. The copied initial method had recovered 50 controls; this package
retains only the selected method. Calibration receipts for each selected stage
are regenerated in `calibration.json`.

Blind success does not prove every new candidate. For example, an order/usage
proposal put `_yardAnimHandle` at `50F6:10DC`, despite ten shared function users.
Six consistent member offsets and the 14-byte array boundary instead support
`55B3:2A28`. The conflicting proposal is in `rejected.json`. Likewise, arithmetic
such as an unnamed private variable expressed as `__caption+1290` does not prove
ownership by that public. Unsupported rows of that kind are excluded.

## Object-size observations

`object-sizes.json` reports the next Win16 public's distance, the distance to its
mapped DOS neighbor when both DOS addresses share a frame, and the next DOS
registration's distance. Distances are decimal bytes. Null means no applicable
bound; a negative DOS neighbor distance means the objects were reordered.

| Object | DOS address | Win16 next-public distance | DOS next-registration distance |
| --- | --- | ---: | ---: |
| `_MapA` | `3E1D:0180` | 8192 | 8192 |
| `_HistGraphs` | `3D57:082A` | 40 | 40 |
| `_AltHistGraphs` | `3D57:0852` | 40 | 40 |
| `_openDBData` | `50F6:3958` | 496 | 496 |
| `_YMapPopR` | `3D57:0164` | 192 | 32 |
| `_GAME_FILE` | `4DA7:0800` | 256 | No next registration |

The `_YMapPopR` discrepancy illustrates the distinction: both save schemas describe
192 bytes, while the DOS registry divides that storage into several entries. In
the other direction, private data can sit between two Win16 publics, making their
distance larger than the named object's actual extent. These observations must
not be converted automatically into C declarations, padding or ownership claims.

## Limits and how to challenge a row

Runtime pointer values without a proven target, indices without a grounded base,
escaped stack frames, unresolved indirect control flow, differing structures and
private data between publics remain limits. Many unmatched Win16 names describe
Windows-only UI, networking or runtime state and may have no DOS counterpart.
This package does not prove live game behavior, full data layout, complete C
allocation extents, or an executable reconstruction.

To check a row, locate its DOS address and Win16 public in `matches.json`, then
inspect the cited original instruction sites, save-table index or byte span in
the fresh output. Follow rival votes and neighboring object distances as well
as the supporting observations. Verify function correspondences in
`evidence/cross_version/decisions.json`; a plausible Windows interpretation must
still agree with the DOS code.

To propose or reject a row, change the inference or publication rule in the
appropriate module and run into a new output directory. Inspect the complete
fresh JSON difference, recalibrate without shared-name seeds, and retain a
positive example and a counterexample that expose the relevant ambiguity. A
change to the review cutoff or function cohort is a new scope decision and
requires reviewing its recorded digest too. Do not change expected rows or a
digest merely to make a comparison pass.

Publishing a reviewed revision means replacing its JSON comparison targets only
after explaining every added, removed or changed row, including tier or evidence
changes. A source rename is a separate repository operation and must follow the
normal naming policy and source re-proof rules. The reproduction command itself
never updates the published targets or canonical source.
