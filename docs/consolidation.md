# Consolidation of the active reconstruction

The active source authority is `src/program.json` and its whole canonical TUs.
DOS and SDL3 consume that same inventory. Published checkpoints are immutable;
active reconstruction is corrigible. Git preserves old workflows and source,
including mistakes subsequently corrected; no compatibility build path is kept.

This is a **canonical semantic checkpoint**, named
`canonical-semantic-oracle-v2`. It is not `functional-source-oracle-v1`: independent
DOS linking, complete address/storage closure, game comparison and human
acceptance remain pending. Native execution is a tested preview with explicit
semantic exceptions, not a full DOS/native equivalence claim.

## Architecture

```
                         src/program.json
                          canonical src/
                                |
                  +-------------+--------------+
                  |                            |
             dos/build.py               portable/build.py
          period compile/link        whole-TU native ABI conversion
             DOS metadata             current platform.json services
                  |                            |
            independent DOS                 SDL3
```

There are now 191 canonical TUs: 127 historical modules and 64 typed storage units.
`tools/promote.py` is their sole writer; it updates historical acceptance metadata
and the shared inventory together. Evidence records why current source is
accepted and is never a source substitution mechanism. Normal exact promotions
must preserve current strict definitions and their declaration context; reviewed
revisions retain static completeness and predecessor identity checks.

The native build converts all 162 canonical C TUs and compiles 161. Physical
DOS segment:offset heap code is an explicit platform boundary. Three native data
units read actual symbolic ASM declarations and initializers. Current files are
compiled directly as 78 platform services. The builder checks current source
pins and input stability, and refuses linking on required conversion/compile
failure. There is no previous-source mode, body-picker or alternate owner plan.

## Source corrections promoted directly

The 29 reviewed semantic definitions below now live directly in their canonical
TUs. Each has a strict static receipt covering complete CFG, data widths,
signedness, pointer arithmetic, calls/order and effects; every remaining
instruction difference has a codegen-only classification. Differential tests
and source mutation controls corroborate that conclusion. A finite contract
alone cannot preserve the status.

| Canonical TU | Current strict semantic definitions |
| --- | --- |
| [`src/root/m0250.c`](../src/root/m0250.c) | `f_0250_1018`, `f_0250_129E`, `DrawBalloons` |
| [`src/root/m0CDB.c`](../src/root/m0CDB.c) | `SpiderScan` |
| [`src/root/m0E2E.c`](../src/root/m0E2E.c) | `LessonDone` |
| [`src/root/m171C.c`](../src/root/m171C.c) | `f_171C_09CC`, `f_171C_0ADC`, `f_171C_0FBC`, `f_171C_0CF4` |
| [`src/root/m1986.c`](../src/root/m1986.c) | `FindIndex` |
| [`src/root/m1C62.c`](../src/root/m1C62.c) | `f_1C62_0415` |
| [`src/root/m1E57.c`](../src/root/m1E57.c) | `f_1E57_038E` |
| [`src/root/m20E8.c`](../src/root/m20E8.c) | `f_20E8_0903` |
| [`src/root/m23AE.c`](../src/root/m23AE.c) | `win_UnlockWin` |
| [`src/root/m23E6.c`](../src/root/m23E6.c) | `f_23E6_0000` |
| [`src/root/m2505.c`](../src/root/m2505.c) | `f_2505_0453` |
| [`src/root/m259D.c`](../src/root/m259D.c) | `win_DrawBitMap` |
| [`src/root/m2815.c`](../src/root/m2815.c) | `f_2815_0165` |
| [`src/root/m284A.c`](../src/root/m284A.c) | `f_284A_0138` |
| [`src/root/m29D6.c`](../src/root/m29D6.c) | `f_29D6_000A` |
| [`src/S10/m35F5.c`](../src/S10/m35F5.c) | `o10_35F5_0384` |
| [`src/S12/m384C.c`](../src/S12/m384C.c) | `DrawMapCursor` |
| [`src/S13/m384C.c`](../src/S13/m384C.c) | `InvertPatch` |
| [`src/S15/m384C.c`](../src/S15/m384C.c) | `o15_384C_0239` |
| [`src/S23/m39C7.c`](../src/S23/m39C7.c) | `win_PrintStyleTextInRect`, `DisplayCard` |
| [`src/S24/m39C7.c`](../src/S24/m39C7.c) | `drawHistGraph` |
| [`src/S25/m3BA4.c`](../src/S25/m3BA4.c) | `o25_3BA4_1035`, `o25_3BA4_1686` |

DrawBalloons contains the corrected signed 16-bit addition before long allocation
arithmetic: `(long)(int)(n + 4)`. The unsigned implementation fails the retained
boundary controls. The active source no longer requires a correction overlay.
[Publication evidence](../evidence/canonical/publication.json) records the
whole-module admissions, definitions and verified binding changes.

Historical EXACT C/ASM source authority is retained. Nine unchanged historical
C bodies have reviewed declaration-context codegen differences after owner/view
integration; their complete instruction relations have no unexplained semantic
difference. They are not counted as current byte matches. Rectangle and window
recalculation corroboration passes 526 paired cases. Current validation records
1,235 byte-exact C functions, 367 genuine assembly functions, 29 strict semantic
definitions and those nine rebuilt historical authorities.

## Canonical ownership and symbolic views

The publication changes 43 historical source files, including 23 reviewed
binding corrections, and adds 399 objects in `src/state/` plus 34 proven commons
in six historical TUs. Definitions, extents, initial values, null pointer state,
typed views and symbolic references are current source facts. Their producer TU
or original communal order is not inferred where only functional ownership is
proved.

The later minimum icon Handle admission adds one mutable four-byte slot, bringing
the storage-unit object count to 400. Both builds consume its canonical definition;
the duplicate native definition is removed. Its referents, activation and physical
aliases remain unresolved, as recorded in the
[current source follow-up](source-followup.md).

The 193 symbolic identities comprise 121 code and 72 data aliases; 38 nonzero
views borrow proven owner interiors. They are source identities, not deprecated
API compatibility aliases. Examples include history/population arrays, Life and
world grids, database record/index state, animation/event records, window hooks
and rectangle reset spans, audio state and saved settings, clip pointers,
callback slots, language/string lists and graphics state.

The input ring is the real seven-record canonical owner `input_queue[7]`, with
16-byte DOS records and a pointer-bearing descriptor. Native conversion widens
that descriptor's pointer without creating another ring. Mouse queues borrow
source capacity/count/row owners and SaveUnder. Actual named ASM cells own scan,
shift, hook, cursor and countdown state. Four widened audio channel records
replace the invented 33-entry overlapping owner; volume bytes are one source
array with typed consumer views. Graphics scalar, palette and complete 345-byte
pattern owners come from actual ASM directives. Native resources borrow the
pattern table directly; the duplicated initializer and palette/scalar resets
are removed.

[Storage contracts](../evidence/canonical/storage.json) and
[aliases/views](../evidence/canonical/views.json) keep active shape validation and
passive historical Git provenance. Neither is an alternate semantic source.

## Retired development architecture

Removed `tools/source_only_dos.py`, `tools/dos_source_bindings.py`, the complete
SOURCE_ONLY corrections/providers/binding tree, source_override and behavioral
source selection. DOS compiles canonical source directly. The old hybrid image
linker, original-byte stubs and reuse wrappers, their tests and obsolete build
documents are removed. Original executable bytes remain permissible only as
validation oracle inputs, never game build fallback.

Removed `portable/tools/whole_program.py`, selected-module/NextN production
paths, old source profiles, duplicate generators/conversion plans, CMake
prototype build, manual game/UI models, and duplicated snapshots/research/test
archives. `native_owners`, `source_state_owners`, `source_bounded_additive`,
parallel grid/history/world/database/RNG/scheduler/audio ownership and their
build-time generators are retired. Ordinary state now comes from canonical C
or source-derived ASM owners. Dead migration helpers/branches and unused
renderer/window headers are deleted; the last font and unproved storage services
are placed under the actual platform directory.

The complete old `work/` and `evidence/behavior/` trees are deleted. Every tracked
retired file is recoverable from Git; active static/runtime evidence is retained
under `evidence/canonical/`. Current tests import their adjacent fixtures and
compile actual current whole TUs/objects. Unique ignored/untracked research was
preserved locally under ignored `build/local-research-before-consolidation/`;
that directory has no production role.

## Why native adapters remain

Native registries hold full pointers, host file/heap handles and SDL resources.
Wire/native views preserve packed DOS fields and widths while widening pointer
slots. CRT services preserve period formatting, file modes and RNG recurrence;
PIT/host clocks preserve logical timing boundaries. SDL input, video and audio
replace physical BIOS/DOS hardware. Hardware fonts are documented local BIOS
resources, with provenance/license and hashes. The tiny genuine-ASM algorithm
projections are readable native translations of canonical assembly that modern
compilers cannot assemble, rather than another implementation of C game logic.

The original main runs startup, dialogs, menus, resource access and simulation.
The native application handles host lifecycle, presentation, event transport and
bounded test replay. Platform state may represent unavoidable host resources;
it does not synchronize a parallel simulation or ordinary game-state model.

## Remaining unknowns

Only **SEMANTIC / PORT-BLOCKING** and **HISTORICAL-BINARY-ONLY** are used for
unresolved questions. Passing native preview flows does not waive the former.

The current DOS frontier contains eleven imports: sample cleanup pointers, spider bitmap,
last filename, temporary clip buffer, overlapping menu x/width arrays,
two audio track-state arrays, mono pattern tail, window colors and window
handles. Forty-four functional data bytes remain. Twelve address/layout gates cover
assembly computed addresses, out-of-range ctype/audio selectors, graphics copies,
viewport grids, menu overlaps, database `[-1]`/handle `+4`, window resource/index
cross-owner accesses, critical-selector computed aliases and icon activation/
referent lifetime. The four-byte icon Handle slot now has a minimum canonical
owner; its former native duplicate is removed. No referent ownership follows. The precise reasons
and scopes are in [the blocker ledger](../evidence/canonical/blockers.json).

Native preview has explicit representations for those eleven symbols, including
unproved static capacities/lifetimes. They do not establish canonical ownership.
FindIndex's guard returns NULL before the original one-past ID predicate. Real
song lookup can reach that read; original allocator padding/next-header content
is not a table-owned sentinel. [Ownership probes](../evidence/canonical/native-findindex-boundary/README.md)
keep the equivalence gate open. Window omitted-slot zeroing differs in raw
state; a full source observer and 34 shipped-resource review supports the
current game's observable domain, not arbitrary caller/resources. Invalid S26
views can still fault at immediate dereferences; added allocation guards,
zoom saved-rectangle residue and larger font output domains remain unresolved.
[Window evidence](../evidence/canonical/native-window-boundary/review.md) and
`portable/platform.json` retain these limits.

Native scalar lowering fixes declared storage, parameter and cast widths; it
does not globally reproduce DOS intermediate integer promotions, wrapping,
shifts, mixed signed/unsigned comparisons or unsuffixed literal typing.
Specific adapters and current differential suites prove their bounded domains.
Completing that mechanical expression lowering/domain proof remains
SEMANTIC / PORT-BLOCKING; the canonical DOS algorithms remain source authority.
See [the static scope receipt](../evidence/canonical/native-integer-promotions/).

HISTORICAL-BINARY-ONLY includes reviewed current compiler-context residue, one
62-byte private CONST contribution containing a changed segment word, original
communal/segment and relocation ordering, linker manager/version/placement and
paragraph fill. Twelve paragraph-alignment bytes need no game initializer; two
file values erased by ordinary manager/CRT startup retain a bounded disposition
with actual independent-game clear dominance still pending. The complete
historical 113-byte debt ledger remains; together with the 62-byte context
contribution, current historical data debt is 175 bytes. Such binary-only
questions do not gate native integration.

## Validation and runnable status

The table records the initial consolidation boundary. Current follow-up results
are recorded in [the source follow-up](source-followup.md), including the new
Handle view and initialized-data link guard.

| Check | Initial consolidation result and scope |
| --- | --- |
| Historical/full validator | PASS on physically cleaned tree: 127 modules, 48 compiler probes, 90 runtime members, 38 DGROUP records and 259 tests (2 skipped) |
| Strict canonical execution | PASS on physically cleaned tree: 11,702 paired cases, 29 source mutation controls, four signed balloon observations and two unsigned contrasts |
| DOS direct preflight | All 190 compiled/reused, all 63 storage contracts pass; 2,091 publics, 431 COMDEFs, 193 aliases, no audit errors or duplicates; original-byte fallback 0 |
| Independent DOS link | Correctly REFUSED on 12 imports and 10 semantic gates; no runnable DOS EXE or full-game DOSBox-X/human acceptance |
| SDL3 build | 160 canonical C + 78 native services + 3 ASM data units compile; both links pass, zero undefined symbols, 418 input pins stable |
| Compiler dependency closure | 242 scans, 400 dependencies, no retired production inputs; all 163 compiled source-derived units equal the independently staged cleanup output |
| Native database | 1,483 index queries; all 840 payloads, including 205 LZSS records; two 14-byte wire writes; both mutation/type negatives detected; FindIndex exception explicit |
| RNG vs original DOS | 3,096 rows, zero mismatches; zero-divisor failure control passes |
| Simulation vs original DOS | 194 cases, zero differences; three whole-TU source mutations detected; bounded DoAntMoveY/DoAntSimY state, RNG and call-order domains |
| Current main VGA | Exit 0, all seven scripted events, positive original outer loops, multicolor 640x480 frame |
| Current Save | Exit 0, all 27 events, source success dialog dismissed; 48,386-byte save; only expected disposable file created |
| Current Save to Load | All 45 events; SaveGame/LoadGame and both FileSelect paths succeed; all 307 reads return 48,386 bytes; save hash unchanged; all 20 checks pass |
| Platform primitives | Directory/DOS file, Windows drive and closed-startup-slot reuse checks pass |
| Window resource/helper controls | All 34 records plus missing/count-one prewrite negatives pass |

Current proof reports are under `evidence/canonical/validation/`; runnable
commands and prerequisites are in [the root README](../README.md) and
[portable README](../portable/README.md). The verified local native executable
is `build/portable-owner-current/simant-canonical.exe`.

Save/Load passing does not prove after-load state equality, DOS save compatibility
or resave equivalence. Simulation covers its declared functions/observer boundary,
not complete ticks or backend behavior. `--seed` does not fix terrain: canonical
SeedRRand also reads actual TickCount. Current original-DOS RNG checks pass,
but a passive v17 comparison had frame/save differences and did not separate
ownership changes from timing; no baseline frame/save equality is claimed.
Outer-loop counts are never presented as simulation-step counts.

## Repository size and commits

Baseline `a1938e61452a63581718aee6659829528c3b8635` has 10,280 tracked files and
507,761,301 Git-blob bytes. The initial cleaned source/proof tree had 749 files and
about 14 MB of Git-blob content: about 93% fewer files and 97% fewer bytes. Final
exact counts and boundary receipts are in the cleanup record. Build output,
original assets, compilers and preserved local research are excluded.

- `1f4e682`: reviewed semantic and typed-storage publication into canonical source.
- `c11a29b`: direct canonical DOS/behavior validation and removal of SOURCE_ONLY overlays.
- `0f88fa9`: current canonical SDL3 build and retirement of duplicate portable
  models, generators, research trees and validation snapshots.
- The checkpoint/report commit records final clean-tree validation and the tag.

`dos-semantic-oracle-v1` remains at
`66e85041ee54f59774ae0fd5a08b37ffbcf77172`; the earlier portable pause tag remains
at `c850830006e0b7d456bb500bf101dd432bbe8ee3`. Their source/tooling is available
through those immutable revisions, not active compatibility layers.
