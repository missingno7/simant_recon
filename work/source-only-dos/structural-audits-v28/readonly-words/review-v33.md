# FAR_BSS zero-fill and owner review v33

Status: `LOADER_BYTES_ZERO_PROVED`; `SIGNED_WORD_VIEW_LAYOUT_CONSISTENT`; `BACKING_OWNER_OPEN`; `POST-LOAD_WRITE_CLOSURE_OPEN`. `root_reviewed: false`. This is a bounded hypothesis audit; it admits no storage owner.

## Finding

The accepted historical FAR_BSS evidence closes the **image-initialization** question for all five imports: the two bytes at each target are zero in the original linker zero-fill region. The signed 16-bit scalar view is natural and size-consistent, but no accepted provider or original defining COMDEF proves that each offset is an independently owned scalar. The source census and direct-reference disassembly show no observed stores; they do not prove a closed post-load write set. In particular, they do not establish the value at first game read after all CRT/startup work, nor a lifetime-wide readonly-zero invariant.

| Target | Next registered offset | `farbss.py --list` span/status | Current source view | Original exact direct references |
|---|---:|---|---|---:|
| `50F6:04C0` | `04C2` | 2 bytes, consistent | signed `int far` | 1 read / 0 stores |
| `50F6:0B20` | `0B22` | 2 bytes, consistent | signed `int far` | 2 reads / 0 stores |
| `50F6:0F38` | `0F3A` | 2 bytes, consistent | signed `int far` | 3 reads / 0 stores |
| `50F6:0FB6` | `0FB8` | 2 bytes, consistent | signed `int far` | 12 reads / 0 stores |
| `50F6:0FFA` | `0FFC` | 2 bytes, consistent | signed `int far` | 10 reads / 0 stores |

“Consistent” is the `farbss.py` size category for a declaration that matches the gap to the next registered start. It is not COMDEF verification or a source-owned definition. The `fd_50F6_xxxx` names are address-shaped registry labels; none has another exact-offset alias. The next-start geometry and declarations make a two-byte standalone word plausible, while leaving room for an unproved composite/backing interpretation.

## Evidence checked

- `tools/farbss.py` and `docs/tu-evidence.md` define frame `50F6` as the linker-allocated FAR_BSS immediately before DGROUP. The original range is `50F6:0000` through `55B3:0000`, 19,408 bytes (`0x4BD0`); `farbss.py` checks that the whole range is zero in the linked image. All five target offsets lie inside it. Thus each target's two image bytes are `00 00`. This proves the linked initial bytes, not later CRT/game state.
- The target symbols in `layout/symbols.json` are all in frame `50F6`. Their original use contexts resolve the segment through the expected relocated CONST word: `main` reads `04C0`; S06 reads `0B20`; root:004A reads `0F38`; S08/root:015B read `0FB6` and `0FFA`. The word offsets are therefore in the zero-filled frame, not a same-numbered offset in another frame.
- `farbss.py --list` reports a two-byte gap at each target and `consistent` declaration evidence. The effective sources declare each as `extern int far`; there is no target definition in those declarations. Current intake has 59 storage-provider proofs and four owner-binding receipts; none contains any target word. The current build report still lists all five as unresolved imports.
- v32 and v28 each pin the same 156 source paths and content hashes, all rechecked against the working tree. v32 finds no named writes, address escapes, numeric target offsets, larger declared typed views, or hard-coded `50F6` assembly references for `04C0`, `0B20`, `0F38`. v28 finds the same for `0FB6`, `0FFA`. The provider extent/alias catalogs have no overlapping span. The explicit 307-payload-row SaveRec table has no overlap with any target; this closes that table's `LoadGame` write route only. The current intake remains `INCOMPLETE`, with no standalone DOS executable and `runnable: NOT_EXECUTED`.
- A read-only sweep of the original disassembly's 1,730 function-table entries across 28 units found only the direct ES-offset operands listed above, and each is a read form (`cmp`, `mov` from memory, `push`). This is a direct-reference cross-check, not pointer-alias analysis. It found no fixed-offset store to any target.
- The nearby provider checks reject known enclosing views, not just exact-name writes. Examples: the 50-byte provider at `0F84` ends exactly at `0FB6`; the provider at `0FC6` ends at `0FF8`, two bytes before `0FFA`; the registered start at `0B22` and the 04C0-adjacent arrays likewise do not overlap their preceding targets. v32 also checks the balloon index bounds that could otherwise cross `04C0`.

## Why readonly-zero and ownership remain open

The 156-source pass catches named operations and adds useful checks for declared views, accepted provider spans, aliases, known pointer escapes/arithmetic, bulk-call arguments, array bounds, and SaveRec destinations. It does not close every alias: a pointer formed from another base, an incompletely represented struct/array view, indexed far access, raw assembly, or a destination prepared outside the selected source graph can write the same physical bytes without spelling the target identifier. The original sweep above only closes direct fixed-offset operands. No positive hidden writer was found, but the present evidence does not exclude these paths.

The two dimension-like words are especially inconsistent with a permanent zero invariant. Source uses `0FB6`/`0FFA` as right/bottom map bounds, halves them for viewport coordinates, and subtracts `0FB6` from `0x80`/`0x40` scroll limits. If those meanings are right, zero through the full game lifetime would make the bounds degenerate. This is evidence that a setup path or the semantic interpretation is missing; it does not identify a writer. The audit therefore records no hidden writer as fact and does not promote a readonly-zero claim.

Closure still needs both: (1) a reviewed defining/provider extent or equivalent original definition evidence that establishes the intended object boundary and type, and (2) coverage of every pre-read and lifetime write path, including alias/indexed/bulk destinations and code outside the current incomplete source intake. The loader-zero result can be used as an initial-value fact independently of those two open claims.

## Pinned inputs

- Source census: `build/workers/dos_readonly_words_v32/source-pins-v32.json`, `build/workers/dos_readonly_map_dimensions_v28/source-pins-v28.json` (same 156 paths and hashes; both sets match current files).
- Current registry / intake / build report: `layout/symbols.json`, `work/source-only-dos/current-intake.json`, `build/source-only-dos/build-report.json`.
- Existing per-target source audits: `build/workers/dos_readonly_words_v32/source-audit-v32.json`, `build/workers/dos_readonly_map_dimensions_v28/source-audit-v28.json`.

No source, manifest, intake, journal, tools, or canonical ownership file was edited.
