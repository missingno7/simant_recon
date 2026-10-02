# DOS semantic oracle v1

Checkpoint tag: **`dos-semantic-oracle-v1`**. This historical tree is the read-only
reference for portable development on a separate branch. The original inputs
remain local, hash-locked prerequisites; the tag contains no original executable,
game resource archives, or historical tool binaries.

The simulation/game behavior needed for the port is closed and oracle-backed,
while some final historical compiler/linker identities remain intentionally
separate proof debt. Behavioral closure refers to the finite reviewed domains
and explicitly named logical service boundaries below. It is not a universal
formal proof or a claim of 100% byte-matching decompilation.

## Proof categories

| Category | Functions | Historical code bytes |
|---|---:|---:|
| EXACT C | 1,244 | 237,521 |
| EXACT genuine assembly | 367 | 50,441 |
| BEHAVIOR_EXACT | 29 | No historical byte ownership conferred |
| UNRESOLVED known game functions | 0 | — |

The 1,640 known game functions reconcile to 1,611 EXACT plus 29 BEHAVIOR_EXACT.
The 90 exactly accepted historical runtime members are separate from this game
count. Existing bytes, extents, fixups, relocation sets/order, peer and private
data gates remain in force. The only additional historical data ownership in
this phase is the strictly promoted 16-byte S03 low-nibble table.

The 29 registered contracts have **533,385 original/candidate comparisons**:
336,944 directed/exhaustive and 196,441 randomized invocations, with zero
unexplained mismatches or execution errors. They include 322,720 GetMyRandDirs,
10,146 SpiderScan, and 10,809 EnterNest cases. The per-function source, oracle,
suite/runner identities, seeds, observables, compiled mutants, helper certificates
and limitations are authoritative in `evidence/behavior/manifest.json` and its
immutable function packets. Supplemental terrain, clock, wrapper and failure-path
probes retain separate accounting.

UI and rendering contracts compare logical requests, pointed text/rectangle/font
or bitmap contents, ordering and caller-consumed state. Explicitly certified
providers separate DOS raster, hardware input, private clipping/timer queues and
resource storage from caller semantics. They do not claim execution or pixel
equivalence for an omitted backend. Real window geometry/handle/allocator paths
and simulation-critical helper/state/RNG paths execute where the contract requires
them. Replacing any boundary in the port must preserve its recorded contract.

## Validation and binary identity

- Full historical validation PASS: 314 discovered unit tests, two skips, all 48
  historical compiler probes, accepted modules, runtime and FAR_BSS gates.
- Fresh hybrid rebuild PASS and byte-identical to the original DOS executable.
- Complete behavioral evidence validation PASS for all 29 registrations.
- Read-only checkpoint readiness audit PASS, with disjoint supplemental gap
  ranges, explicit data dispositions and pinned source/validation input trees.

Original and hybrid SHA-256:
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.

Production toolchain identities are pinned in `layout/toolchain.json`: MSC
6.00/6.00A/6.00AX profiles and genuine MASM tools, under the pinned MS-DOS Player.
Behavioral execution uses Unicorn 2.1.4. Compiler instrumentation remains a
research tool and never replaces the production binaries used for acceptance.

Validation logs, receipts, case totals and source-tree digests are in
`work/takeover/behavioral-oracle/checkpoint-inputs.json` and
`checkpoint-readiness.json`. The hybrid's derived provenance stays under `build/`;
its identity, gate log and receipt are retained in the checkpoint. Archived proof
inputs have byte-preserving Git attributes so checkout cannot change their hashes.

## Remaining historical proof debt

**15,355 code bytes** remain historically unowned: 15,039 in the 29 behavioral
function extents, plus 316 outside them. The latter consists of 54 bytes in seven
callable/layout spans, 246 bytes currently classified as LINK_FILL, and a 16-byte
text prefix. The supplemental wrapper/empty-return behavior has original-backed
evidence; missing entry references do not establish dead code. No extent was
trimmed and no exact ownership is inferred from these dispositions.

**113 data/layout bytes** remain unowned: 110 bytes in eight literal spans plus a
three-byte section/common-tail overlap. Meaningful graphics tables, partially
typed UI state, unknown fields, timer-compatible relocated data and uncertain
runtime/linker contributions remain distinguished. Each byte range has a reviewed
reason preventing historical ownership in `data-debt-disposition-approved-v1.json`.
Unknown values are not declared harmless or silently discarded during porting.

**17,001 RTLink manager/linker bytes** remain a separate historical whole-EXE
proof level. The byte-identical hybrid is an explicit hybrid, not proof that the
original historical linker has been recovered.

Prior exhausted searches, failed gates and compiler-internal evidence remain
archived. They are diagnostic unless the registry or historical promotion journal
records acceptance. A later portable edit must not change these sources merely
to simplify SDL3 integration.

## Portable development

Continue on `codex/portable-sdl3`. Use the tag as the source and behavioral oracle.
The first playable path is the reconstructed NewGame/scenario flow, logical map
window/events and DoAntSim cadence inside one SDL3 host window. Explicit host
interfaces replace DOS video/input/timing/files/memory/audio mechanisms. Keep
16-bit arithmetic, RNG consumption, map/ant state and logical timing under
differential regression; presentation refresh must not change simulation ticks.
