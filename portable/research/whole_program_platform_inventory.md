# Whole-program platform-boundary inventory

Static audit date: 2026-10-03. The source basis is the immutable `dos-semantic-oracle-v1` checkpoint (see `docs/dos-semantic-oracle-v1.md`). This scan found **29 frozen ASM modules / 350 PROC bodies**, plus **15 C source files** with explicit hardware/runtime references (69 matched source lines).

## Classification rule

A procedure is marked `hardware_interrupt_or_dos_service` when its own PROC body contains a recognized BIOS/DOS interrupt, port I/O, interrupt-flag operation, or IRET. Procedures with `LES`/`LDS`, segment overrides, or DS/ES/SS loads but no direct hardware/service instruction are marked `dos_segmented_memory_abi`. Other procedures are `portable_algorithm_candidate`; that means only “no direct signal found in its local body,” not portable proof. C entries preserve exact matching source lines. Far pointers alone are not treated as hardware: they are routine in the DOS memory model. The scan recognizes explicit inline ASM, listed interrupts, port I/O, interrupt flags, selected absolute BIOS/ROM reads, and `_segment`/`FP_SEG`/`FP_OFF`/`MK_FP` operations. It is lexical and is not a callgraph.

## Source-defined assembly inventory

| Module | PROC bodies | Direct boundary signals | Source hash |
|---|---:|---|---|
| `src/root/m1699.asm` | 5 | none detected | `26d9a76b86a8854105e905a11b59b83f84cac821edec495900bd296b2914a5fb` |
| `src/root/m16B5.asm` | 9 | none detected | `a38a5b8c6c44549a99a501b7931279b3c597e516d79238216c27e479f399bc8a` |
| `src/root/m194D.asm` | 3 | int10 | `8becfaafd57faf7e3bfb7e7150d4438bf8d78e1319aa90618f76a2be89175c0f` |
| `src/root/m1959.asm` | 2 | none detected | `73186753eaea7bcf17b6419094a21937299b1cba5be10a79e7a513794d408f56` |
| `src/root/m195A.asm` | 29 | int21 | `b634ca4916d811140f6a06b29f731bd323d49f5c50a76ef3afee38a7f23f6a81` |
| `src/root/m1B05.asm` | 6 | none detected | `3124ef4a45c572a54529bd5a57cd9225b40fdcafadd63c6b06cb748683cacca4` |
| `src/root/m1B4E.asm` | 16 | int10 | `a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2` |
| `src/root/m1B73.asm` | 51 | int15, int21, int33, port-io, cli/sti, iret | `3097a6b03ff1d8bdfa7d573632d9905de88d754c8b1e047de4014c4f186cb848` |
| `src/root/m1F58.asm` | 9 | int16, cli/sti | `9f314c6e964bcb0955c1f3e976819bdbeddf048781c1bb257c30b2c0b25d49d2` |
| `src/root/m1F66.asm` | 6 | int21 | `b477ccb8ce87afd98692cbf32dc11d4f0bb9df1000e3a6334ffc5ab8076f33b3` |
| `src/root/m1FBD.asm` | 1 | none detected | `5e32f1c409a2fc20cb7bba200a3d2fd11e43edc0b7e2b8781ca91415a1a43417` |
| `src/root/m24FA.asm` | 4 | none detected | `e538d0a8df93c3bd7ba3aabccc9a48faa6f643b7f8489c3c379c0d23ad9ac412` |
| `src/root/m2650.asm` | 2 | none detected | `8b86e1416ac34675a6f638ed8a17d8e5e3092e155e314cebc807a75711a410d8` |
| `src/root/m283E.asm` | 3 | port-io, cli/sti | `c7fc07dbb9830dfad40597e5fe377c4a62bc9d3551a80aef602dad3925daa0c5` |
| `src/root/m28BC.asm` | 5 | int21, port-io, cli/sti, iret | `361f33c1d86502fef4d43559cb7f424e350eee3fe8a31881ed3c21b4d865f7a5` |
| `src/root/m29BF.asm` | 11 | port-io | `bb40cbd77f380b56c0ab0c27d41f08b40f63deb3b8c14f53b15e3d526fa753ac` |
| `src/root/m2CFB.asm` | 0 | none detected | `d12d1eedb44a03197c55abf8701ee5f6dfc71a4472ab66d610ae68a3da79d981` |
| `src/S00/m3126.asm` | 7 | none detected | `be7a4a3b0fd9c56c47be50d20c60b0c2835002b7721bd913d36f8183be47ce5a` |
| `src/S00/m31AD.asm` | 44 | int10, port-io | `5d2ad69ff4affb4be4242e82187065cc5e0b3502cc0cc3e00ad3802ccee2656e` |
| `src/S00/m31AD_2AB4.asm` | 6 | port-io | `3ef3979a3c35e9e36c4ddc48408bc4cac601ad26f4728e044012a489f831fd55` |
| `src/S00/m35A6.asm` | 5 | none detected | `0e563a69e0bc7a2ea11d7b963a9b0be7fbd3479e5dac1ed9985c47ffc533db73` |
| `src/S01/m3126.asm` | 40 | port-io | `ac99ea7821999d034e64201798d49dfaf64632f34e5f5dee428c9b6dec01a44a` |
| `src/S01/m328E.asm` | 4 | none detected | `610b108145bbf912a6c1b11b454eaf54a7c6053624db8b7de8f2c672dce34351` |
| `src/S01/m32B5.asm` | 5 | none detected | `b8db05f10b37941e1a9cfa60f5dc87180e6075576703f29fc7b7557273b17394` |
| `src/S02/m3126.asm` | 27 | none detected | `4291e4084ff26dcee75016b03c1b8d8412129a97ad00787b41ac567c16f5178b` |
| `src/S03/m3126.asm` | 32 | none detected | `b0b9d296f23b4f8a5b4706008b21b6ad96429636da11bf22ddb2126ee362f2ff` |
| `src/S03/m3253.asm` | 2 | none detected | `5f67726c1477bfb28285078c835fef3b8e1b9a7e1ad19ce34e225b76366b8165` |
| `src/S03/m3258.asm` | 7 | none detected | `45182b0559f08e760e025fb1066203150637414c29e221ba7e6e5cea0bd30034` |
| `src/S21/m39C7.asm` | 9 | int10, port-io | `537d7b811340a7615c2d49e8eb5253953937bd1b037344ecbaba246c27f338bd` |

The JSON file lists every PROC symbol (72 direct hardware/interrupt/service bodies; 154 segmented-memory ABI bodies; 124 local algorithm candidates), per-procedure signal tags, and hashes. A list of clean bodies is not a native link report.

## C/inline boundary references

The scan excludes comments, retains matched source text, and associates a line with the enclosing parsed function body where one can be identified (macro-expanded bodies and file-scope segment declarations may have no ordinary function owner).

- `src/root/m0093.c`: 9 matched lines in `(file scope or macro body)`, `GetRRandSeed`, `SRand1`
- `src/root/m015B.c`: 2 matched lines in `PlaceQueenInYard`
- `src/root/m10F7.c`: 7 matched lines in `DoLifeExchange`, `DropMyEgg`, `DropMyFood`, `DropMyRock`
- `src/root/m171C.c`: 1 matched lines in `f_171C_0034`
- `src/root/m277E.c`: 11 matched lines in `f_277E_01FA`, `f_277E_0760`, `f_277E_0958`, `f_277E_0965`
- `src/root/m284A.c`: 3 matched lines in `(file scope or macro body)`, `f_284A_0013`, `f_284A_067F`
- `src/root/m293A.c`: 8 matched lines in `f_293A_002D`, `f_293A_0059`
- `src/root/m29D6.c`: 4 matched lines in `f_29D6_000A`, `f_29D6_00D9`
- `src/root/m29F0.c`: 8 matched lines in `f_29F0_000A`, `f_29F0_0012`, `f_29F0_001A`, `f_29F0_0022`, `f_29F0_002A`, `f_29F0_0038`
- `src/S05/m35F5.c`: 2 matched lines in `AntMenu`
- `src/S09/m35F5.c`: 1 matched lines in `o09_35F5_03C6`
- `src/S12/m384C.c`: 4 matched lines in `o12_384C_12D3`
- `src/S15/m384C.c`: 3 matched lines in `o15_384C_0125`
- `src/S22/m39C7.c`: 2 matched lines in `YellowCommandKey`, `processEdit`
- `src/S22/m3BBD.c`: 4 matched lines in `DropWall`, `ExpDig`, `ExpIncSmell`, `IncFoodHere`


## Source-family symbol coverage

The JSON `source_service_families` entries expand subsystem modules to their exact parsed PROC symbols and identify current native route/status. These lists are actionable denominator slices, not claim of one-to-one implementations. The explicit unmatched work is summarized in the service table above.

## Existing native boundary services and uncovered work

Historical INT instructions, port writes, far pointers and vector setup are retained in the JSON as source evidence. They are not a requirement to recreate DOS hardware or operating-system mechanisms. The port should preserve the game-visible contract behind those operations through typed native APIs.

| Observable contract | Native service present | Coverage | Remaining work |
|---|---|---|---|
| indexed rendering and window primitives | portable/render framebuffer, font/bitmap/tile primitives, source-backed window/layout models and SDL presentation | **partial observable contract** | Complete source-callable primitive routing and verify Rect/clip composition, copy/ROP modes, cursor/invert effects, and dispatch order across loaded object resources. The 26 callback-data names in the diagnostic catalog expose backend-selected primitive slots whose concrete source assignments must be preserved. |
| logical input, pointer capture and event queue | HostEvent/HostInputState, SDL3 event translation/cache/warp and live source event queues | **partial observable contract** | Close remaining source window/control/menu routes, capture/release state transitions, event coalescing, queue ordering and pointer feedback for every callable path. Unsupported routes remain named. |
| source time and scheduling | SDL monotonic clock, live rational BIOS TickCount projection, MacTickCount mapping and source scheduler | **bounded source routes; audit remaining callers** | Ensure all admitted callers preserve original TickCount/MacTickCount read count/order, wrap rules, wait points and source tick cadence. Audit direct BIOS/RTC/8253 consumers not yet mapped to the logical clock contract. |
| allocation, movable handles and resource lifetime | resource database, ordinary native ownership, portable memory helpers and selected recovered allocator bridge | **partial observable contract** | Complete alloc/resize/lock/unlock/purge/dispose behavior, stable handle identity, data relocation/alias lifetime and failure ordering for remaining source modules; all f_171C allocator entries are explicitly enumerated in the callable catalog. |
| filesystem and file-dialog behavior | resource/database loading and limited source-scoped file entry points | **missing source-visible paths** | Implement directory enumeration, current-directory/drive semantics, file open/read/seek/write/close error mapping and source-visible dialog ordering where those flows are admitted. The external CRT/DOS symbols are enumerated by exact name in the callable catalog. |
| audio intent and synthesis | typed audio intent queue, SDL audio host and bounded SFX/DAC paths | **partial observable contract** | Complete supported source sound/music request mapping, synthesis/playback completion state, cancellation, priority and timing. Song/MIDI and remaining device families fail explicitly. |
| C runtime and ordinary portable algorithms | native C runtime, selected far-memory helpers and mechanically translated game/runtime modules | **partial source-route mapping** | Resolve every source callable/ABI symbol in the pinned catalog; separate true CRT imports from failed translation units, ASM entry aliases and typed callback data, then link only after definitions and compatible semantics are reviewed. |

Retired mechanisms are listed per JSON row to prevent the lexical source evidence from becoming an emulation checklist. Current host adapters and generated migration providers are not complete link admission.

## ASM registry count reconciliation

The frozen manifest contains **367 ASM claims** while a strict `PROC` parse finds **350 source procedures**. Seven claims are in-body label aliases for named S21 `PROC` bodies. The 24 claims without a `PROC` spelling include those seven aliases; after matching them, **17 unaliased claims** remain: five interrupt-handler code-entry labels, ten far-jump thunk entries, one saved-state data extent, and one callback/alignment address alias. Exact source line/address entries and alias pairs are in `assembly_registry_reconciliation` in the JSON. This reconciles registry counts; it does not revise or admit historical claims.

## Fresh diagnostic callable catalog

The captured scratch migration snapshot `f613b6140289e417a89319a0a5f1895de6dd4e5e64af11f3c041f8a9ee24e749` had **242 `CALLABLE_OR_EXTERNAL_ABI` entries** (495 `GLOBAL_STATE` entries are separate). The exact name-by-name mapping in the JSON classifies every callable contract as failed C translation unit, ASM PROC, CRT/DOS runtime ABI, source-address alias, function-pointer data slot, or explicit unresolved external. Every failed-C record points to its source definition, signature, source line and generated module compile status. This is a diagnostic source catalog, not link or behavior admission; re-pin when the generator refreshes it.

The callback data aliases are especially actionable: they are typed function-pointer globals used for profile-selected drawing/blit routines and window hooks. They need native state slots and provider assignments; they are not unresolved function bodies. The three `f_2CFB_*` extern spellings are recovered by exact source offset as the named `jt_171C_*` far-jump thunks, while `f_1B73_0D4B` is the public alignment/entry alias in the source mouse module.

## Reproduction and pinned inputs

Run from repository root with Python 3: enumerate `src/**/*.asm`, parse `PROC` through matching `ENDP`, and scan all `src/**/*.c` (comments excluded) for `_asm`, recognized `int`, `in/out`, `cli/sti`, selected BIOS/ROM absolute pointer reads, and segment-pointer operators. SHA-256 values for every listed assembly module, every C file with hits, and native service implementation files are embedded in the JSON. The scanner does not edit or infer from canonical source. `docs/dos-semantic-oracle-v1.md` provides the frozen source/checkpoint provenance; it is not a claim that every PROC is currently used by the native executable.


## Native window record adapter

The source-backed native sidecar route is documented in [native_window_record_adapter.md](native_window_record_adapter.md) and implemented in `portable/whole_program/window_refs.h/.c`. The draft converter at `portable/whole_program/conversions/windows.py` maps six frozen root window TUs, preserving the original `RepointObjects` loop while redirecting table assignments to the sidecar. It models the actual load order (bind before selected runtime-field clears), rejects unresolved serialized Handles, detaches only after the original final object-table read, and replaces a fixed DOS-byte clear with an element-counted native hook clear. `portable/tests/whole_program/window_refs/run.py` strictly tests the adapter and source-shaped conversion rules. This remains a bounded native adapter/converter check, not an original-DOS differential, actual database-resource integration, or full translated-TU integration. Exact source, converter, adapter, and test pins are in the JSON `native_window_record_adapter` entry.
