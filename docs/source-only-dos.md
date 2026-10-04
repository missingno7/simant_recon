# SOURCE_ONLY_DOS

The active milestone is a standalone DOS executable compiled from the frozen
reconstruction. SDL3 integration is paused at
`portable-sdl3-v17-paused-20261003` (`c850830006e0b7d456bb500bf101dd432bbe8ee3`).
Existing native source, providers, runtime evidence and v17 packages are retained.
Human acceptance of the DOS build is required before further major SDL3 work.

`dos-semantic-oracle-v1` freezes the accepted semantic contributions only. The
next major milestone, `functional-source-oracle-v1`, requires zero original-byte
fallback, zero unresolved imports and layout dependencies, a successful independent
RTLink build, DOSBox-X runtime validation/comparison, and human acceptance. Storage
and layout hypotheses cannot be frozen to make preflight pass.

Before substantial changes, check whether they recover existing logic, resolve a
representation/platform contract, or invent a replacement. Prefer recovered
source, keep one logical state owner, and expose unknown contracts as failing
work items. A DOS build must work without the original executable as an ingredient.
Confidence comes primarily from source, differential function/state/RNG evidence
and data layout; emulator use and the user's normal-use comparison complete the
integration gate. Do not turn a crash into new gameplay, guessed state or a
successful no-op service.

After that gate, keep SDL3 lowering mechanical and its platform boundary thin.
Preserve the internal game window system inside one host window. Convert useful
deterministic ASM to C only with strong differential evidence for outputs, memory,
callbacks and state; retain the ASM oracle. Refactoring and window redesign follow
the faithful port. Preserve unique evidence, but keep superseded implementations
out of active builds and use Git identities, hashes and compact receipts instead
of repeated source-tree archives.

## Authorities and build paths

| Path | Authority and limitation |
|---|---|
| `src/`, `layout/manifest.json`, historical promotion evidence | Exact C, genuine symbolic ASM and reconstructed data. Only `promote.py` writes canonical sources/ownership. Exactness is a contribution-level claim, not an independent executable build. |
| `evidence/behavior/manifest.json`, pinned function packets | Frozen finite behavioral registrations. Their status alone does not close static completeness. |
| `work/source-only-dos/static-completeness/index-v1.json` | Strict, root-reviewed CFG/data/width/call/effect receipts for all 29 imported implementations. A contract-only or unresolved verdict blocks the independent link. The separate DrawBalloons correction preserves the failing original-source verdict. |
| `tools/link.py` | Placement/provenance diagnostic. Deliberately copies explicitly labelled original debt into `SIMANT.HYBRID.EXE`. Hybrid SHA equality does **not** prove a source-only executable. |
| `tools/rtlink.py` | Historical link research. Existing trials use zero code/data stubs for missing contributions and are not runnable reconstructions. Their objects and executable are excluded from SOURCE_ONLY_DOS. |
| `tools/source_only_dos.py` | Separate source-only preparation/compilation and fail-closed input report. Uses canonical complete files, substitutes only the pinned reviewed behavioral definitions, retains function order and original DOS hardware/runtime semantics. No hybrid collector, original loader, zero-stub generator or object patcher. |
| `portable/tools/recover_source.py`, Next10 recipes | Earlier selected-source experiments, native models and adapters. Preserved research, not DOS source authority. |
| `portable/tools/whole_program.py`, whole application | Current whole-source native conversion with original main and shared state. Paused integration work; conversion success and native replays do not prove complete DOS integration. |
| `portable/platform/`, native providers and sidecars | Platform replacements, runtime compatibility and pointer/ABI conversions, subject to their specific evidence. They are not inputs to the DOS target. |

The functional conceptual source is the exact reconstruction **plus** reviewed
semantic closure. SOURCE_ONLY_DOS does not create a second interpretation of game
algorithms. Historical compiler spelling, link order, RTLink version and byte
identity remain a separate proof track.

## Reproduce the inventory and compilation

```powershell
python tools/source_only_dos.py --out build/source-only-dos
python tools/source_only_dos.py --out build/source-only-dos --compile --jobs 4 --reuse
```

Until independent linking is complete these commands return failure, even if all
TUs compile. `build-report.json` records the actual state. Preparation alone is
not compilation; compilation is not linking; linking is not execution; execution
is not human acceptance. `runnable` stays `NOT_EXECUTED` until actual execution.

`--link --linker rtlink400` requests the separate independent link after its
source/data/layout preflight is clean. `rtlink610` is the alternative. Incomplete
inputs are refused before the linker runs. A successful link still reports
`LINKED_NOT_EXECUTED`, with human acceptance pending.

Generated whole module files and objects live under the chosen ignored build
directory. They are derived inputs, not canonical promotions. Every behavioral
definition is imported from its registered, hash-checked module snapshot or an
explicitly reviewed and pinned same-module correction. Its
reviewed definition replaces the canonical candidate in place; canonical TU
declarations, other functions and data remain intact. Name aliases come only from
the existing reviewed symbol registry. Unreviewed scaffolds fail preparation.
Explicit storage contracts may assign a functional owner in a generated TU;
they require separate source bounds, whole-object controls and runtime allocation
evidence. This never changes a frozen historical declaration or its proof level.

The report inventories source/evidence and generated-file hashes, actual compiled
TUs, toolchain files/headers/runners, third-party runtime libraries, function
dispositions, semantic substitutions, missing symbols, duplicate publics and
unresolved data. Third-party MSC/RTLink components must be explicitly pinned;
none may be extracted from the game executable.

The build process denies reads from `assets/` and known original/hybrid executable
names. Hash pinning rejects a renamed full original image. Compiler inputs are
source text and pinned tool/header files. The target never calls `exe.load()`,
`link.collect()` or the historical trial generator. Any denied oracle access makes
the build fail. The four original-byte input counters must all remain zero:
game code, game data, fallback/debt and executable fragments.

## Outstanding integration work

All 1,640 known game functions in the effective source-only set have strict
semantic dispositions: 1,244 exact C, 367 genuine ASM and 29
BEHAVIOR_EXACT_CONFIRMED. The
[strict audit](../work/source-only-dos/static-completeness/README.md) maps all
original paths, widths, constants, state accesses and ordered effects. It found
and corrected DrawBalloons's unsigned allocation widening; the historical source
registration remains explicitly unresolved in that separate review. The build
does not silently preserve a behavioral status because its finite tests pass.
This does not close data integration.
The frozen 113-byte historical data disposition inventory includes live graphics
tables and partially typed state, as well as unresolved layout/runtime boundaries.
Those assessments are inventory metadata only; their byte strings are never
emitted as initializers by this target. Meaningful fields need grounded source
representations; a different link layout may resolve layout-only gaps without
reproducing historical padding. Unknown state cannot be silently zero-filled.

The fresh compiled symbol report is the concrete worklist for state ownership,
private-data aliases and compiler/runtime bindings. Consumer extern declarations
are hypotheses, not definitions. Multiple names for the same storage must bind
to one source owner. Preserve the original DOS allocator, interrupt, video and
window implementations; do not import native substitutes to make DOS link.

The current compilation passes all 127 canonical TUs plus 24 reviewed data-only
providers. Symbol-address joins provide 121
code aliases and thirteen exact-base data aliases without rewriting objects. Reviewed generated
ASM bindings expose eight names in existing storage: S00's memory-size table and
dispatch pointer, S02's save-rectangle flag, and the timer countdown word shared
with root:208F, plus four sample-channel/volume-table views in the recovered audio
module. Three C TUs additionally expose five existing private objects. Their
complete reviewed-body control objects and exported objects have identical code,
data, debug segments, segment definitions and relocations; only the five public
records differ. No storage or initializer is added.

The reviewed `c-data-bindings-v1.json` joins 26 consumer names to those owners and
other already public C objects. Thirteen views refer to array elements or Timer
fields inside an existing object; the others start at their existing owner. Each
binding checks source identity, public location, accepted contribution extent,
view bounds and the reviewed consumer address. No C references or types are
rewritten to get these aliases. Source-built near/far controls executed under
DOSBox-X verify RTLink 4.00/6.10 `DEFINE owner + offset`, with separate wrong-near
and wrong-far contrasts. This is a linker contract, not a game runtime proof.

Ten history arrays now have one functional owner in generated S24 under
`history-storage-bindings-v1.json`. Their signed-word declarations, ClearHistory's
64-entry writes, HistUpdate's index mask, graph pointer-table views, score reads
and S09's ten `{2,64,&array}` records establish the observable 128-byte extent of
each array. The declaration edit adds ten far COMDEF records (1,280 bytes of
linker allocation) and changes no compiled segment byte, public or symbolic fixup.
No source initializer or game operation is introduced. Original object ownership,
communal order and unused historical padding are not claimed. Canonical extern
declarations and historical FAR_BSS accounting stay frozen; the general worklist
does not automatically become definitions.

`history-storage-probe.py` compiles, links and executes test-owned fixtures under
both RTLink versions. Zero-fill and first/last word access pass with the pinned
MSC runtime startup; a nonzero initializer is detected by each runtime control.
Separate fixtures reproduce the byte extern/word owner declarations, SaveRec
addresses and initialized graph pointers, check the first/last serialized words,
and call the overlay word owner. Both linkers pass. The canonical byte externs
only form addresses; they do not index those symbols or apply pointer arithmetic.
This establishes the period DOS address ABI, not a modern cross-TU type policy.
The bare ASM entry with an overlay owner fails under RTLink 4.00 and passes under
6.10. That counterexample is retained in `history-storage-contract-v1.json`;
only the MSC startup and byte/word view contracts authorize the generated history
owners. The link gate checks the selected linker and runtime hashes against those controls.

The remaining 315 imports are data: 310 FAR_BSS names and five requiring
storage/reachability investigation. None remains inside an accepted data
placement. These are link ingredients
missing from the source-built target, distinct from the historical 113-byte debt.
The report retains consumers, source declarations and possible accepted storage
owners per missing name; an ownership candidate is not an accepted definition.

The generated drivers replace 16 literal `3DFCh` operands with references to the
accepted `_g_3DFC` row-offset buffer in `src/root/m1B4E.asm`. Two S00 near callback
offsets likewise refer to their existing procedures. The pinned transformations
are in `work/source-only-dos/source-bindings-v1.json`. Canonical ASM remains intact.
For each bound derived TU, compilation builds a source control and
checks unchanged segment extents, data, existing publics and relocations, and every
byte outside the 18 reviewed address operands. Added fixups must have the correct
target, frame, width and addend. DGROUP framing is explicit, including scoped
`ASSUME SS:DGROUP` at indexed SS operands; an ordinary MASM `OFFSET` or group
expression alone can still select the wrong frame. Negative source contrasts
test wrong frames, the wrong timer word, unrelated instruction changes, changed C
initializers, invalid interior views and wrong communal type/extent/initialization.

`farbss-source-review-v1.json` is a research worklist, not new DOS state. Direct
reading of the reconstructed S09 SaveRec table confirms serialization extents for
29 earlier source-view candidates; eight further candidates lack that anchor.
Ten of these candidates are the separately reviewed history arrays described
above. The other 19 saved candidates and eight without save anchors still need
consumer bounds, pointer escapes, DOS type/COMDEF measurements and initialization
review. Save length alone does not establish an object's full storage extent.

`farbss-mechanical-worklist-v2.json` preserves a compact inventory from the
Luna mechanical scan. It recognizes declarations for 430 of 469 registered
50F6 names; unsupported syntax leaves 39 unknown. Beyond history, 204 save rows
match a complete declaration's mechanical size. Ignoring S09's explicitly
nonassertive target-only byte declarations leaves 195 consistent type candidates
and nine conflicts. These are review candidates, with no definitions admitted:
object boundaries, indirect pointer uses, initialization and compiler controls
still need evidence. The full derivative inventory stays in ignored build output.

Fixed code offsets, numeric data operands and segment/group framing still need a
broader semantic audit, which remains a link gate. Exact instruction bytes at an
original placement do not imply correct operands after an independent link.

The audit also includes initialized C addresses. In root:1FD2 the source object
spelled `Timer g_5FF2` is used by the ASM input queue as a different set of views.
Its word at +12 (`_g_5FFE`) is initialized to literal `0x91B0`; enqueue/dequeue load
it into SI and index seven 16-byte event slots. No accepted source placement owns
that DGROUP buffer. The reviewed generated module now owns a typed seven-element
near Event array and initializes the descriptor field symbolically. Exclusive
enqueue/dequeue access establishes seven 16-byte slots and six usable pending
records. The accepted MSC startup clears the entire original queue interval
before main, which matters because enqueue leaves the first word untouched.
Whole-module checks account for the one changed pointer field/fixup, the new
112-byte near communal and the exact changed compiler debug contributions. Both
linkers pass actual queue execution controls; nonzero initialization, capacity
eight, a shifted pointer and wrong segment framing are detected. Original COMDEF
TU/order and padding remain unclaimed.

Three reads in root:1B73 already run with ES=DGROUP but had `_DATA` offset frames.
The generated scoped ES assumption now frames exactly those three relocations in
DGROUP. All instruction bytes and other fixups remain unchanged. Shifted `_DATA`
fixtures fail with the original frame and pass with the reviewed one under both
linkers. The wider numeric-address and frame audit remains an explicit link gate.

Nine far word scalars now have source-functional owners: HealthB/HealthR and
FoodB/FoodR/Cycle in S08's world-reset module, BpopT/RpopT in CountAnts's module,
and AntsEatenByLions/InitialLions in their reset/regeneration module. Complete
consumer and persistent SaveRec address views support each two-byte extent.
Fresh whole-module controls preserve every segment byte, extent, public and
ordered fixup, changing only the nine external scopes to far communals. Clean
MSC-startup fixtures verify word and save-record byte views on both linkers,
with wrong type/extent/alias/initializer contrasts. The combined five-owner S08
edit is verified as a whole module on every build. These allocations resolve
twelve imports including existing exact-base aliases; they do not establish
historical COMDEF module identity, order or full-game save/load integration.

The next scalar batch supplies seven InitSimVars words in S08 and five
ResetYellowVars words in S22. Each has complete integer consumers, a constructor
or reset assignment and an exact two-byte persistent SaveRec view. The S08
extension pins and preserves its previously admitted five-owner binding; the
fresh whole-module proof covers all twelve commons together. The S22 proof
changes only five external scopes. Its `fd_50F6_0C38` member is serialized and
written but has no direct C reader; the evidence does not invent one. Both
linkers pass typed word/BYTE views and reject alias/initializer contrasts. There
are now 21 source-owned far word scalars; this batch resolves thirteen imports.

Two further data-only providers own three independent mouse words and five
allocator objects. The latter are two unsigned near words and three near objects
holding four-byte far `Block` pointers. Complete reads/writes, DOS allocation
output-pointer escapes, teardown behavior and original startup-clear containment
support their types and lifetimes. Actual MSC startup tests on both linkers check
zero entry, byte/word overlap and offset/segment halves, with wrong type, extent
and initializer contrasts. These eight allocations resolve eight more of the
original 46 storage/reachability cases, leaving fifteen open at that checkpoint. They claim no
original TU, communal ordering or aggregate.

The 128 external SS operands in S00Ă˘â‚¬â€śS03 now have scoped DGROUP frames. The
source-wide audit covers 127 canonical files, all 29 registered module snapshots
and corrected DrawBalloons. CRT startup and interrupt CFG dominance establish
SS=DGROUP at every audited driver entry. Signed operand tuples, whole-object
comparisons and shifted-origin controls on both linkers reject partial site sets,
different targets and unrelated relocation changes. A subsequent bounded review
corrects ten module-local operands using exact `_DATA` displacements and source
anchors. Both linkers distinguish paragraph-relative frames from DGROUP offsets
in shifted-layout fixtures; whole objects preserve all bytes and unrelated ordered
fixups. The `g_5A9C` segment/offset pair remains a separate investigation.

The pattern-bank owner in root:1B4E consists of sixteen accepted 16-byte records.
A zero-byte public at its start and three symbolic S00 operands replace the
literal `41D0h` base. Selector/phase arithmetic bounds every read within 256 bytes;
the existing `g_4220` view is at byte 80. Both shifted-linker controls exercise all
256 test-owned bytes and detect wrong frames and shifted bases. Original source
table bytes remain unchanged; no data-debt initializer is supplied.

Two 100-byte water coordinate arrays extend the existing population-owner binding.
Initialization and simulation loops bound entries 0Ă˘â‚¬â€ś99, and two `{1,100,&array}`
SaveRec records establish their byte views. Reset/load ordering is accounted for,
including failed partial loads. The combined whole-TU check preserves all code,
data, debug and ordered fixups and adds only the two far commons.

The additional data-only providers supply four render scalars (including the
one-byte `g_94E4`), three allocator far words and two far-stored far pointers,
eight signed RandYard words, a 24-byte monochrome prefix, and a four-byte clip-list
pointer. The clip segment-word name is a bounded `+2` alias; two yard names share
their existing exact-base registry aliases. Source dataflow, reset/SaveRec views,
pointer halves and lifetimes support these types; both linkers pass MSC startup
contracts with explicit negative controls. Whole-source debug deltas in the yard
and monochrome research experiments are retained as counterexamples, so their
functional owners use separate providers. These allocations bring the original
46 storage/reachability cases to eight remaining. All 113 historical data-debt
bytes remain explicit, including adjacent clip fields and initializer questions.

The monochrome `g_8ED8` payload's producer count is unavailable in supplied
resources, and its indexed driver base remains unresolved. The window-handle
table lacks a proven allocation extent. Database normal paths establish four
124-byte records, but an allocation failure can continue with slot `-1` after
`Punt`; that separate layout dependence is not closed by a four-record owner.

Two further providers supply the database index's far-stored far pointer and
signed search cursor, and seven signed spider/corpse counters. The index pointer
addresses an eight-byte entry whose first four bytes have file-offset and far-data
views; empty-index and teardown paths preserve its existing stale value. The
counter review accounts for reset, load and SaveRec byte views. `DeathCnt` is
seeded by KillSpider and is not reset by InitSpider. Word-width, signedness,
zero-fill and byte-view controls pass under both linkers. These nine FAR_BSS
owners do not resolve the database slot `-1` layout dependency or prove the
unchecked `Scycle` drawing index safe for arbitrary loaded state.

The lion/sow/pillar provider owns five ten-byte lion lists, two signed pillar
words, a six-word pillar map and four three-word sow arrays. Original zero-fill
research accounts for their preinstruction state, including sow slot zero:
InitSow only initializes slots two and one. Typed reads/writes and SaveRec byte
views establish each extent, and both linkers pass the word and byte-view
fixtures with five negative controls apiece. Loaded indices, directions and
coordinates remain unchecked by the original algorithms. The provider adds no
reset, initializer, game code or historical communal-order claim.

The generated root mouse TU also corrects the single `g_5A9C` SEG operand at
`MOUSE_TEXT:0133`. Its OFFSET companion is already DGROUP-relative; changing
the SEG target/frame to DGROUP preserves all bytes, extents and ordered unrelated
fixups, including the three earlier ES corrections. Both linkers pass the
shifted-group pointer-word check and explicitly fail the old `_DATA` SEG frame
before dereference. The minimal fixture does not execute the whole mouse TU;
earlier full-fixture timeouts remain recorded. Rectangle ownership and initial
fields remain a separate unresolved data gate.

Six signed spider control words and five signed x/y Point objects now have
separate functional owners. Their exact SaveRec bases, typed operations, resets,
partial-load behavior and aliases are accounted for. MSC emits the same communal
shape for a Point and four raw bytes, so source type review is an independent
gate. Both linkers pass typed/byte views and reject shifted aliases, widths,
signedness and nonzero-initializer controls. Unchecked loaded target indices and
coordinates remain separate algorithm constraints; no range checks are invented.

The database provider owns four 124-byte OpenDBRec records and four signed handle
words. Natural union views preserve the 24-byte raw index area, far pointer halves,
20-byte index header and remaining record fields. A near-pointer contrast keeps
the total 124-byte extent but shifts the typed header; source review and runtime
controls reject it. Owners add no resets for stale fields. The slot `-1` record
and handle `[4]` accesses after a returning Punt remain two explicit unresolved
layout gates. No preceding padding or fifth handle is allocated to hide them.

The driver callback table now has one typed near array of 25 far pointers.
The source reset writes 25 two-word slots, copy moves 50 words, and all four
driver tables contain 25 entries. Twenty-three registered callback names are
four-byte views within the 100-byte owner; the two unnamed positions acquire no
new registry names. The data-only provider adds no code or initialized data.
Fresh build checks reject wrong extents, an initializer, extra allocation or
code, and out-of-range/misaligned aliases. Both linkers verify startup zeroing,
all slot offsets, reset/copy bounds and the existing symbolic `_g_3DF8` pointer
under shifted DGROUP; wrong last-slot, initializer and pointer-base controls
fail. This resolves 23 of the original 46 storage/reachability cases without
claiming the historical COMDEF-producing module.

RTLink's unsuffixed `DEFINE +12` means hexadecimal 12 (decimal 18). Production
aliases now use explicit hexadecimal suffixes. The v2 alias controls check near
and far offsets 12 and 40, detecting both shifted and unsuffixed operands.

The simplest initial linker candidate is the already available, pinned
RTLink/Plus 4.00 or 6.10 with source-built objects and its own stock manager.
Both have linked research trials. The four original overlay areas provide a
research basis for arranging modules; historical vector order and exact manager
identity are unnecessary. A production script must contain no stubs and must
resolve every import. A flattened build is a fallback only after measuring its
conventional-memory requirements. No link strategy has yet been validated for
the full source-only game.

## Native implementation classification

The paused native tree contains several kinds of handwritten code; a name match
does not establish provenance. Existing conversion/provider evidence must justify
each as original ASM translation, DOS/platform replacement, compiler/runtime
compatibility, proven pointer/ABI conversion, or reviewed BEHAVIOR_EXACT logic.
Examples already documented in the paused handover include the bitmap bridge
(ASM contract), cooperative BIOS keyboard service (platform boundary), virtual
DOS file descriptors (runtime/platform compatibility), and S26 window sidecars
(pointer-width conversion). Their finite tests do not establish universal
equivalence. Older history/control/game models remain research implementations;
they cannot override available reconstructed source semantics. Unclassified or
weakly grounded providers are suspect until reviewed. This classification audit
is not permission to delete or extend the preserved SDL3 integration.

## Validation and acceptance

Use DOSBox-X for both the original and reconstructed DOS executable with the same
resource copy, configuration, display/sound mode and input sequence. PortForge is
excluded. Runtime tests are integration sanity checks, backed primarily by the
existing function evidence. Prefer RNG/state/map/ant/population/counter/save and
ordered-service checkpoints; full-frame equality is not the whole-game gate.

Package only a clean independently linked executable and instructions, never the
hybrid or trial image. Check ordinary startup, scenarios, simulation, dialogs and
save/load, reducing divergences to source/state/ABI contracts. Deliver it for the
user's normal-use comparison and stop for human acceptance. Do not tag
`functional-source-oracle-v1` or resume major SDL3 cleanup before that acceptance.

The [initialized graphics admission](../work/source-only-dos/initialized-graphics-admission-v1.md)
owns 34 functional initial-state bytes with two mutable near providers. Eighteen
bytes follow closed consumer formulas; sixteen translate accepted S03 source
literals into a distinct color map. Complete MSC objects and both RTLink profiles
check payloads, types, publics, frames, bases and aliasing. Two mask reads and ten
other indexed reads now bind symbolic DGROUP owners, including a zero-byte
generated glyph-table label over accepted data. Whole-object checks preserve all
other bytes and ordered fixups. The functional data report has 79 unresolved
bytes; historical ownership still has 113. Variable clip copies, returning-Punt
reachability and the wider layout audit remain separate link blockers.

The [v15 FAR_BSS admission](../work/source-only-dos/far-owner-admission-v15.md)
adds seven data-only providers for 33 source-owned objects (278 bytes): list
counts, colony words, player/red locations, long counters/timer, language pointer
slots, dead-ant coordinate rings and ant/player words. Every provider has fresh
MSC object checks and both RTLink startup/view controls. The 112 required cases
retain their raw result classes; two passing width measurements and two passing
overrun diagnostics remain non-gating. Registry/address alias joins correct the
earlier missing-reset and missing-definition conclusions.

At the v15 checkpoint the lane compiled 150 complete translation units (127 canonical and
23 functional providers) and resolves 37 previously missing imports, including
four exact-base aliases. Canonical source and historical debt remain unchanged.
At that checkpoint the independent linker refused the 316 remaining imports, 79 functional
data-debt bytes and open layout cases. All 29 effective semantic bodies retain
strict BEHAVIOR_EXACT_CONFIRMED receipts. This is compile/storage progress;
functional-source-oracle-v1, DOS execution and human acceptance remain pending.

The v14 color-map proof retains its exact historical tool hash through a stable
research-only provenance snapshot. Its five initialized-data verification
functions have identical ASTs in the current tool. Current builds use the live
tool and recheck complete objects; no old runtime outcome is repinned as fresh.

## v16: display-selector storage and first-write dominance

The generated-only `char near g_5A97` provider owns one byte. Accepted startup
calls ReadConfig before any source-visible selector read, and every returning
mode branch writes the byte. The real config producer and MSC CRT pass 42
cases across RTLink 4.00 and 6.10 from both 00 and FF entry states. The complete
startup/first database consumer remains a static proof, not a claimed runtime
fixture. See the [root admission](../work/source-only-dos/display-mode-selector-admission-v16.md).

SOURCE_ONLY_DOS compiles 151 TUs, including 24 typed providers. Missing imports
are 315: 310 FAR_BSS and five DGROUP cases. This closes 41 of the original 46
DGROUP cases. Only offset 1 of dgroup_5a96 is functionally discharged; its other
25 bytes remain unresolved. Functional data debt is 78 bytes; historical debt
stays 113 bytes. Clip-sentinel, computed-copy, database error-path and wider
numeric/frame gates remain open. No standalone executable or runtime acceptance
is claimed.

The boundary checks 40 source-only tests plus 314 other repository tests, with
two skips, and historical validation. Probe reruns write scratch candidate
packets and cannot overwrite the admitted selector binding/contract.

## v17: typed control, resource and terrain objects

Three generated-only providers own 20 source-backed FAR_BSS objects, totaling
82 bytes: control geometry/levels, three UI resource counts plus three pointer
slots, and Barrier/TERRAINset. Whole source graphs, complete C types, saved byte
views and fresh compiler/runtime controls establish these extents. Both RTLink
profiles require clean symbol maps; an EXE emitted with unresolved warnings
cannot count as a passing control. Ant-control shortened-level and initialized-
knob negatives remain compiler-only. See the
[root admission](../work/source-only-dos/control-resource-terrain-admission-v17.md).

All 154 TUs compile, including 27 typed providers. Missing imports fall to 294:
289 FAR_BSS and five DGROUP cases. The original 46-case DGROUP inventory still
has 41 resolved cases. Functional data debt remains 78 bytes; the historical
113-byte ledger is unchanged. All 29 effective behavior implementations retain
strict static confirmation, with no contract-only or unresolved substitution.

Resource array extents, clip/default-sentinel state, computed-copy interactions,
database returning-error-path reachability and the remaining numeric/frame
audit stay explicit gates. Test-owned fixtures do not constitute game execution.
Independent linking remains refused; DOSBox-X game comparison and human
acceptance are pending. SDL3 remains paused.

The boundary checks 41 source-only tests and 314 other repository tests, with
two skips, plus historical validation. The three source-review documents were
finalized before the successful boundary; fresh execution receipts retain their
original tool/probe identities.

## v18: serialized arrays, S01 pattern view and paragraph fill

Two generated-only providers own four 50-byte swarm buffers and two six-word
population vectors: six objects, 224 bytes. Complete source graphs, typed
producers/consumers and exact SaveRec views establish the extents, including
the serialized swarm tails. Fresh MSC objects and both RTLink profiles check
zero startup, typed access, save views and wrong type, extent and base controls.
See the [serialized-state admission](../work/source-only-dos/serialized-state-admission-v18.md).

The [S01 admission](../work/source-only-dos/s01-pattern-4220-admission-v18.md)
replaces one numeric 4220h displacement with a symbolic DGROUP reference to
the existing pattern-bank view. Whole-object comparison preserves every other
byte and ordered fixup. The source bounds the index to 76h; shifted-group,
wrong-frame and +1-base controls pass their expected outcomes under both linkers.
The wider numeric-address and segment-frame audit remains open.

The [alignment admission](../work/source-only-dos/far-data-paragraph-fill-admission-v18.md)
discharges 12 bytes as linker paragraph fill after a source-owned 100-byte
FAR_DATA segment. It adds no storage. Both linkers independently reproduce
the fill with clean maps; the 112-byte contrast removes it while preserving
the following FAR_BSS address. Historical ownership debt stays at 113 bytes.

All 156 TUs compile, including 29 typed providers. Missing imports are 288:
283 FAR_BSS and five DGROUP cases. The original DGROUP inventory still has
41 of 46 cases resolved. Functional data debt is 66 bytes. All 29 effective
behavior implementations have strict static confirmation, with no contract-only
or unresolved substitution. Original-byte input counters remain zero.

The saved sound-state owner and lock/unlock clobber review remain pending;
the first fatal-path cleanup cannot yet support database or critical-error
reachability closure. Clip/default-sentinel state, resource bounds and remaining
fixed-address dependencies also block independent linking. No game executable,
DOSBox-X game comparison or human acceptance is claimed. SDL3 remains paused.

The boundary passed 44 source-only tests and 314 other repository tests
(two skips), historical validation, and all 18 required storage/frame gates
plus the alignment gate under both linker profiles. Runtime fixtures are
component evidence; they do not constitute execution of the complete game.

## v19: sound-driver saved state and transition words

Three generated-only providers own five further FAR_BSS objects (22 bytes):
the seven-word saved sound-driver state, three signed control words, and the
CountAnts transition latch. Complete typed source references, the sound state's
initialized pointer alias and exact SaveRec views establish the extents. Fresh
MSC objects and both RTLink profiles check startup, typed/byte views and rejected
type, extent, initializer and base contrasts. The sound state's 28-byte and
12-byte controls preserve their passing in-bounds zero measurements while the
production gate rejects their OMF/map shapes. See the
[root admission](../work/source-only-dos/storage-admission-v19.md).

The effective build compiles 159 TUs (127 canonical plus 32 providers), with
283 imports unresolved: 278 FAR_BSS and five DGROUP cases. Functional data debt
remains 66 bytes; historical debt remains 113. The original DGROUP inventory
still has 41 of 46 cases resolved. All 29 effective behavior bodies have strict
static confirmation; all original-byte counters remain zero.

The saved-state owner supplies a prerequisite for early sound cleanup but does
not close fatal-path reachability. The independent unlock review retains the
72-site caller-pair census and 70 ordinary by-value pairs; both memory rereads
remain pending at transitive rendering/animation/invalidation callbacks. The
critical-error byte and both database layout gates remain unresolved. See the
[bounded clobber review](../work/source-only-dos/unlock-clobber-review-v19.md).

The monochrome producer's header count is signed on the selected MSC target.
The positive-header copy bound (1,016 bytes) does not establish the missing
resource's extent or cover every arithmetic selector value in the four S01
consumers. No guessed monochrome storage or frame assumption is admitted.
Independent linking remains refused. DOSBox-X game execution, human acceptance
and functional-source-oracle-v1 remain pending; SDL3 stays paused.

The boundary passed 45 source-only tests and 314 other repository tests (two
skips), historical validation, and all nineteen selected storage/frame gates
plus the alignment gate under both linker profiles. The initial gate-field
mismatch was fixed before the successful full rerun. The
[runtime heap review](../work/source-only-dos/fheap-runtime-debt-v19/README.md)
retains its fourteen-byte debt despite automatic archive selection in minimal
controls; absent direct imports alone cannot discharge it.

## v20: sound-control word owners

Six independent signed two-byte FAR objects now have a source-functional
provider. The 156-source census accounts for all 79 non-declaration references
and finds no alternate bases, interiors, numeric operands, assembly accesses,
address escapes or SaveRec views. Their extents follow complete scalar types.
Root reviewed the actual OMF objects, link logs and both public map sections;
both RTLink versions passed startup and typed/raw access plus width,
signedness, initializer and shifted-alias controls. The gate requires every
measured alias displacement and rejects missing or contradictory map evidence.
See the [root admission](../work/source-only-dos/storage-admission-v20.md).

All 160 TUs compile (127 canonical plus 33 providers). Missing imports are now
277: 272 FAR_BSS and five DGROUP cases. The original DGROUP inventory remains
41 of 46 resolved. Functional data debt remains 66 bytes, with 113 historical
bytes; all 29 effective behavioral implementations remain strictly confirmed.
Original-byte counters and denied oracle reads remain zero.

The six-word provider does not close the separate channel/voice record owners
or fatal-path cleanup. Both database returning-Punt gates, mutable unlock
rereads, graphics state/copy bounds and the wider numeric/frame audit remain
open. Independent linking is refused; full DOS execution, human acceptance and
functional-source-oracle-v1 remain pending. SDL3 remains paused.

The boundary passed 46 source-only tests, 314 other repository tests (two
skips), and historical validation. All 20 storage/frame gates and the alignment gate pass under both
linker profiles. The [replay wrapper](../work/source-only-dos/sound-control-words-v20/replay.py)
reruns the pinned component probe in a fresh unadmitted directory, preserving
the admitted research outputs; its smoke run passed all ten cases.


## v21: complete sound records and individual scalar owners

The two sound record arrays now have complete functional owners: 56 six-byte
Voice records and 33 six-byte Chan records, with independently checked long/far
pointer and signed/unsigned byte views. Copy/reset/cleanup loops and the complete
effective source/caller census establish the extents. Both linkers passed fourteen
runtime rows; two additional wrong-name links were diagnosed and never executed,
although they emitted executables. Those actual outcomes remain explicit. The
[sound admission](../work/source-only-dos/storage-admission-v21.md) is storage-only;
post-init selectors and full sound behavior remain separate requirements.

Three further providers own 44 independent scalars: sixteen movement words,
sixteen world outputs and twelve history words/longs. Each complete source view
and exact SaveRec span was reviewed. The four-byte world object 0472 retains its
signed and unsigned long views; all four source stores write zero, with no readers
or pointer escapes. Its purpose and nonzero interpretation remain unknown.
History resets retain their conditional newGame==1 behavior; generic raw loads
remain unchecked. See the [scalar admission](../work/source-only-dos/scalar-storage-admission-v21.md).
Production objects emit only the reviewed commons. The 34 scalar runtime rows,
compiler contrasts, both map sections and all expected alias/address matrices are
mandatory gates. Passing overrun diagnostics do not establish object bounds.

The sound selector review exposes an actual path: `/s9` passes the parser but
indexes outside each nine-entry table. The detector overread aliases the same-TU
saved-state pointer and calls the data it targets as code. Return is unproved;
conditional later setup/cleanup accesses include cross-TU historical adjacency.
SOURCE_ONLY_DOS now reports a distinct unresolved gate. No clamp, tenth entry,
padding or original bytes hide it. See the
[root review](../work/source-only-dos/sound-selector-layout-review-v21.md).

All 164 TUs compile (127 canonical plus 37 providers). Missing imports are 231:
226 FAR_BSS and five DGROUP storage/reachability cases. The original DGROUP census
remains 41 of 46 resolved. Functional data debt is 66 bytes; historical debt is
113. All 29 effective behavior bodies remain strictly confirmed, all original-byte
counters remain zero, and canonical ownership is unchanged. Independent linking
is refused; DOS game execution, comparison, human acceptance and
functional-source-oracle-v1 remain pending. SDL3 stays paused.

The boundary passed 48 source-only tests and 314 other tests (two skips), plus
historical validation. All 21 mandatory storage/frame gates (including the four
new owner families) and the alignment gate pass under both RTLink profiles.
The sound-record replay wrapper passed all sixteen fresh component cases while
preserving the admitted outputs. Research compile contexts remain distinct from
the separately checked production provider context.


## v22: histogram ownership and bounded clip-pointer accounting

`CountAnts` now has its complete source-derived `int far[32]` histogram,
64 bytes, with data-only COMDEF validation and startup/typed/raw, shifted-base,
initializer and unsigned-view controls under both RTLinks. The full clear loop
and all consumers establish this owner; neighboring addresses are not an extent
source. The two special-selector indexes remain unchecked. See the
[admission](../work/source-only-dos/ant-histogram-admission-v22.md).

The existing four-byte `g_5AAC` far pointer and `g_5AAE` segment-word view are now
removed from functional unowned-data accounting only after actual whole-provider
and both-linker startup/alias evidence. No storage was added. The unknown Rect
fields, static sentinel and copy/layout dependencies remain open. The historical
113-byte ledger is unchanged. See the
[bounded disposition](../work/source-only-dos/clip-pointer-data-disposition-v22.md).

The refreshed database review separates ordinary callback returns from execution
of invalid zero far targets before display initialization. Ordinary ABI-preserving
returns continue to unconditional fatal exit; no actual early-return counterexample
is claimed. Both database layout gates remain unresolved. The
[root review and continuation addendum](../work/source-only-dos/database-layout-review-v22/root-review.md)
preserve the earlier observations and correct their wording.

Preflight compiles 165 TUs (127 canonical plus 38 providers), with 230 remaining
imports: 225 FAR_BSS and the five unresolved cases from the original 46-case
DGROUP inventory. Functional data debt is 62 bytes. All 29 strict effective
implementations remain confirmed, original-byte counters remain zero, and the
wider address/frame and five layout gates remain open. Independent linking is
refused, game runtime has not run, and human acceptance remains pending.

Four further storage families are under root review; their worker probes do not
change these accepted counts. SDL3 remains paused until the standalone DOS
milestone and human acceptance.

This boundary passed 363 repository tests (two skips), including 49 source-only
tests, canonical validation, and all 22 mandatory evidence gates plus alignment
under both RTLinks. The root raw histogram check reopened all 104 preserved
artifacts and independently decoded all seven compiler fixtures.


## v23: complete event record owners

Two separate `struct Event far` records now own 16 bytes each. Their eight signed
word fields, dequeue writes, dispatcher views and whole-record assignment come
from the complete source. Fresh production compilation as `EVRECS` checks the
data-only OMF owner. Both RTLinks pass all-field/zero/patterned-copy and shifted
layout controls; width, initializer, +2 and wrong-symbol controls are rejected.
Root reopened all 184 preserved artifacts and checked 14 complete raw outputs,
clean link logs, both public-map sections and actual four-byte pointer fixups.
See the [root admission](../work/source-only-dos/event-records-v23/root-admission.md).

This storage admission leaves the possible decoder overwrite of active event
state open. It does not infer Event[2] ownership from adjacent linked addresses,
historical producer identity, placement or original initializer.

Preflight compiles 166 TUs (127 canonical plus 39 providers) and reports 228
missing imports: 223 FAR_BSS and five DGROUP storage/reachability cases. Functional
data debt remains 62 bytes, historical debt 113 bytes, and all 29 strict effective
functions remain confirmed. All original-byte counters stay zero. The independent
link remains refused, game execution has not run, and human acceptance is pending.
Further owner candidates remain unadmitted until root review.

This boundary passed 364 repository tests (two skips), including 50 source-only
tests, canonical validation, and all 23 mandatory evidence gates plus alignment
under both RTLinks. The canonical manifest remains unchanged.
