# SOURCE_ONLY_DOS

The active milestone is a standalone DOS executable compiled from the frozen
reconstruction. SDL3 integration is paused at
`portable-sdl3-v17-paused-20261003` (`c850830006e0b7d456bb500bf101dd432bbe8ee3`).
Existing native source, providers, runtime evidence and v17 packages are retained.
Human acceptance of the DOS build is required before further major SDL3 work.

## Authorities and build paths

| Path | Authority and limitation |
|---|---|
| `src/`, `layout/manifest.json`, historical promotion evidence | Exact C, genuine symbolic ASM and reconstructed data. Only `promote.py` writes canonical sources/ownership. Exactness is a contribution-level claim, not an independent executable build. |
| `evidence/behavior/manifest.json`, pinned function packets | Reviewed implementations for 29 BEHAVIOR_EXACT functions. Finite differential contracts and named backend boundaries remain their limits. |
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
definition is imported from its registered, hash-checked module snapshot. Its
reviewed definition replaces the canonical candidate in place; canonical TU
declarations, other functions and data remain intact. Name aliases come only from
the existing reviewed symbol registry. Unreviewed scaffolds fail preparation.

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

All 1,640 known game functions have semantic dispositions: 1,244 exact C,
367 genuine ASM and 29 BEHAVIOR_EXACT. This does not close data integration.
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

The first full compilation passes all 127 TUs. Symbol-address joins provide 121
code aliases and eight data aliases without rewriting objects. The remaining
512 imports are data: 432 FAR_BSS names, 33 names within accepted data placements,
and 47 requiring storage/reachability investigation. These are link ingredients
missing from the source-built target, distinct from the historical 113-byte debt.
The report retains consumers, source declarations and possible accepted storage
owners per missing name; an ownership candidate is not an accepted definition.

There is also a concrete changed-layout hazard in the original ASM: display
drivers use literal `3DFCh` to initialize/index the row-offset buffer whose
accepted source owner is `_g_3DFC` in `src/root/m1B4E.asm`. All known sites are
listed in the build report. Fixed code offsets and other numeric data operands
still need a broader semantic audit. Exact instruction bytes at an original
placement do not imply that those operands are correct after an independent link.

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
