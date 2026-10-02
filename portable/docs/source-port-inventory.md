# Historical source routes into the SDL3 port

Run `python portable/tools/source_port_inventory.py --report portable/tests/recovered/evidence/source-port-inventory-v1/inventory-vN.json` with a fresh, never-used `vN` filename to create a read-only machine inventory. Versioned receipts refuse overwrite. The current receipt is `inventory-v3.json`; v1 and v2 remain as earlier immutable versions. It joins the frozen function table and manifest to the current Next10 profile, source-name registry, portable C definitions, and exact captured SDL build command. The report is inventory evidence only: it does not compile, regenerate, prove link reachability for a name match, or claim behavioral or pixel equivalence.

The porting references suggest two useful constraints. The Empires guide treats one historical C file as the unit of conversion: retain member ordering and bodies, translate ABI spellings, and route only hardware/DOS edges through named portable services. The Stunts audit keeps a full explicit mapping for every historical routine, treats name matches as candidates, and lists unmapped routines and arithmetic/width hazards instead of calling them covered. This inventory applies those constraints as route labels; it does not copy either project's code or assume the games share semantics.

## Current route counts

The frozen function registry has 1,730 rows. Of these, 1,640 join to a historical C/ASM source module (98 C and 29 ASM modules, representing 1,273 C and 367 ASM function rows); the other 90 rows are MSC runtime-library members. The current generated profile has 25 TUs and lists 434 definition names. The address/name join finds 431 generated source-body candidates and 3 generated scaffolds excluded from semantic interpretation. The profile also names 13 explicit native adapters. These counts describe where definitions or adapters can be found, not equivalence. The 25 TUs are not all complete semantic ports: source-faithful joins can retain scaffold exclusions, adaptation records, and provider boundaries.

The route table keeps five native situations apart:

- A generated source-body candidate is a frozen address/name join to a definition in the current generated TU. The row retains any profile scaffold exclusion, semantic adaptation, type-view adaptation, provider boundary, and wrapper.
- An explicit adapter has a named mapping in Next10 provenance. The source body is bypassed at that adapter route; its limit text remains in the row.
- A same-name provider candidate names a portable C definition that appears in the captured executable's compiler command. That does not establish a particular caller binding.
- A native contract model is handwritten and distinct from the historical body. The two ProcMode/ProcCaste event models are linked in the captured build and have finite control-event evidence. The MenuQuit and S26 zoom models are currently unlinked. The History renderer model is present in the captured Next10 build command; the S24 generated source body is recorded separately. A legacy `UNINTEGRATED_MODELS` set also lists the history-render TU, so the report preserves that set membership separately from the captured command’s linked status.
- A missing route has no matching generated body, declared adapter, mapped model, or same-name provider definition. A compiler-runtime row remains a compiler-runtime row rather than being mislabeled as a missing game port.

There are 1,103 source functions with no native route under those conservative rules. Another 353 function starts have multiple symbol-name candidates without a unique generated-body join. The JSON preserves all candidate names and addresses so that overlays, aliases, and gaps remain reviewable. A candidate name is not used to resolve an ambiguous source route.

The production side of the census comes from `build/portable/simant-sdl3.build.json`, not a filesystem glob. The v3 receipt resolves and checks every one of its 261 input paths and hashes (zero missing or changed), the 81 C translation-unit paths in the exact command, the compiler executable, the SDL library, and the built executable. Eleven other portable C files are outside that command. For example, `portable/ui_model/windows/decorations.c` is a workspace draft, not a linked provider. This avoids treating a newly appearing file as part of a previously captured executable.

## Next source conversion batches

These are mechanical conversion batches that preserve each complete source TU and member order. They are ordered as useful source groups, not as proof that every external provider is already implemented. Each entry in `inventory-v3.json` includes the module’s available and unsupported named source edges; unresolved edges remain work and must not be guessed or stubbed.

1. `root:00BA`, [`m00BA.c`](../../src/root/m00BA.c), has 5 historical functions, all absent from the current profile. Preserve all five source bodies and their order, then route its 20 unsupported call edges through the explicitly mapped modules/providers.
2. `root:00F8`, [`m00F8.c`](../../src/root/m00F8.c), has 40 historical functions; one (`MapToYard`) already has a generated source-body candidate, leaving 39. Preserve the full TU and resolve its 16 unsupported edges.
3. `root:0250`, [`m0250.c`](../../src/root/m0250.c), has 53 historical functions (50 claims and 3 scaffold entries), none currently routed by the profile. Preserve all members, including scaffolded bodies; resolve 58 unsupported edges covering memory/resource/graphics dependencies without replacing their behavior with guesses.
4. Full `root:0798`, [`m0798.c`](../../src/root/m0798.c), has 18 historical functions; eight already appear in the current generated profile and ten do not. Recovering the complete module is the path to replacing the two separate linked `ProcModeEvent`/`ProcCasteEvent` handwritten model routes with source-body routes. Twelve named calls remain unsupported.

## Whole-TU backlog

The report keeps a separate largest-remaining-members ranking: `root:171C` has 61 remaining functions and nine unsupported edges; `root:0250` has 53 remaining and 58 unsupported edges; `root:22BF` has 47 remaining and 27 unsupported edges. This is a backlog view only, not dependency readiness. For example, `root:171C` has EMS, far-memory-copy, and error-handling edges that should stay explicit rather than being mapped to host `malloc` behavior.

## Arithmetic and evidence boundary

`recover_source.transform()` maps `int` to `int16_t` and `unsigned int` to `uint16_t`; it does not rewrite bare `unsigned`. The report scans selected historical source files and the 25 generated TUs for bare-`unsigned` spellings and shift expressions. This snapshot finds 165 bare-`unsigned` occurrences and 417 shift lines in historical sources, versus 3 and 172 in the generated Next10 files. These are review candidates: C integer promotion, signed shifts, and host `int` width need expression-specific analysis, not a blanket rewrite. In particular, the generator’s treatment of `unsigned int` must not be generalized to bare `unsigned`.

All 25 module records retain their source/generated hashes and adaptation metadata. The machine report includes each of the 1,730 function rows, per-module route counts and call edges, every captured build input pin, compiler/SDL/executable identities, and source/provider hashes. Source bodies, historical files, producers, build selection, engine, and live integration are unchanged by this inventory tooling.
