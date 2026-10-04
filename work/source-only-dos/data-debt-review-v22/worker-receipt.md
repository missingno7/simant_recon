# v22 bounded source ownership review

Status: `root_reviewed: false`; no admission requested or performed. This is a
read-only source and preflight review of the remaining DGROUP spans at 56FE, 5A28,
5A96, and 60B0. It does not change production sources, tools, layout, or the historical
debt ledger. No source initializer is inferred from adjacent offsets or original data.

The pinned preflight is the current 164-TU SOURCE_ONLY_DOS report. It records zero
original executable-byte inputs, 231 unresolved imports, and 66 bytes of remaining
functional data debt: 56FE/4, 5A28/2, 5A96/25, 60B0/18, 79F0/14, and the three-byte
common-tail overlap. The historical inventory remains 113 bytes. The 79F0 runtime
member question is deliberately not re-investigated here; its separate v19 receipt is
the existing evidence.

| Span | Source-owned evidence | Boundary and disposition |
|---|---|---|
| `55B3:56FE` (4 B) | `src/root/m1E57.c:12` defines and uses `int g_5702[32]`; its first word is explicitly `0x8000`. The named object begins at `5702`. | No field, declaration, initializer, or use identifies `56FE..5701`. The known initializer for `g_5702[0]` does not reach backwards. Keep all four bytes unknown; do not call them padding or extend the array by its gap. |
| `55B3:5A28` (2 B) | `src/root/m1F58.asm:8–11` starts four explicit words at `5A2A`: two pending-key words and the saved INT 23h vector. Their reads and writes name only `5A2A`, `5A2C`, `5A2E`, and `5A30`. | The 2-byte leading word has no source declaration or read/write. The following keyboard object does not establish its predecessor. Keep unknown. |
| `55B3:5A96` residual (25 B) | The original 26-byte cluster has one closed field: `g_5A97` is a one-byte `char near` display selector. The report's `resolved_source_state` records offset 1/size 1 with a first-write-dominance proof; `display-mode-selector-contract-v1.json` scopes this to a generated functional owner and makes no historical owner or initial-value claim. The remaining offsets are 5A96 (1 B) and 5A98–5AAF (24 B). Within the latter, consumers provide typed views: `g_5A9C` is an 8-byte `Rect`; static clip-list traversal from `&g_5A9C` reads the next record's `top` at 5AA6; `g_5AAC` is a four-byte near far-pointer and `g_5AAE` is its +2 segment-word view. | `5A96` and `5A98–5A9B` have no typed source field/use. For the first `Rect`, `m205F.c` stores `right` and `bottom` after an indirect `g_9130` callback, while clip/render callers read bounds; no source store establishes `left` or `top`, and the early callback's reads are not closed. The second-record `top` must be `RECT_END` for the static-list traversal, but `m1E57.c`'s `list[1].top = 0x8000` writes an allocated heap list, not the static record at 5AA6. The existing source-only clip-pointer contract establishes a functional typed pointer owner and +2 alias; it does not establish the historical owner, neighboring Rect initialization, or the complete 25-byte cluster. Keep the residual span open. |
| `55B3:60B0` (18 B) | `src/root/m1FD2.c:15–23` defines an 18-byte `struct Timer` (8-byte `Rect`, far callback, 16-bit ticks, four chars). Source-defined timer instances include `g_6004`, `g_6016`, `g_6028`, and `g_603A`. Its timer APIs accept a `struct Timer far *`; current source call sites pass `&g_6016`, `&g_6004`, and `&g_603A`. `m1B73.asm` copies nine words from that argument into a far queue slot. | The current debt report describes an 18-byte Timer-compatible shape with a real callback relocation to `f_1B73_030F`, but neither the callback value nor matching width identifies a source object at 60B0. No source names 60B0 or passes that address to the Timer APIs. That census constrains the recovered direct registration paths only; computed aliases and unowned pointer flows are not excluded, and `remaining-assembly-address-audit` is still unresolved. Do not declare the record unreachable or source-owned from the absence of an import. Keep all 18 bytes unknown. |

The timer call-site census is deliberately narrow: repository source text has three
direct `f_1B73_0B00` registrations (the three addresses above) and one
`f_1B73_0AC3` registration (`&g_6016`). `g_6028` is a defined same-sized instance but
has no other source reference. This does not make it an alias for 60B0. There is also
a useful counterexample to shape-only ownership: `g_5FF2` is declared as a `Timer` in
`m1FD2.c`, while `m1B73.asm` uses words beginning there as input-queue state. A
matching 18-byte layout is not enough to assign semantics to 60B0.

The following original-function context calls used `tools/context.py` without
`--raw`: `f_1B73_0B00`, `f_1B73_0AC3`, `f_1FD2_03EB`, and `f_1FD2_044F`. They corroborate
the passed Timer pointer and queue-copy behavior; no original data values or byte
spans were emitted or used as source material. No Win16 comparison or naming decision
was needed.

## Narrow g_5AAC functional count

The already root-reviewed `work/source-only-dos/clip-pointer-contract-v1.json` does
support closing **four functional bytes** at `5AAC..5AAF`, including the bounded
`g_5AAE` view at owner offset +2. Its explicit root scope admits a four-byte typed
owner and that subobject view. The provider declaration is
`struct Rect far * near g_5AAC;`; MSC/RTLink startup zeroes its near communal before
the source-only entry point, and the source also sets null for clip-off. The contract
has a matching four-byte near COMDEF and passes the +2 alias under both RTLink 4.00
and 6.10; the +0 alias and nonzero-initializer contrasts fail under both. Its
whole-module control makes only `g_5AAC` a near communal and preserves the live
`root:1E57` object projection. The pointer is intentionally mutable, so later setters
and saved/restored clip lists do not weaken ownership of the pointer storage itself.

That CRT-provided zero state resolves the functional source-only initial value even
if a cursor path reads/saves the pointer before an explicit `clip_Off` store. The
contract does **not** claim the original pre-CRT value, historical producer TU, or
the surrounding Rect/sentinel state. Thus the historical 113-byte debt remains
unchanged, while the functional remainder can be counted as four bytes smaller if
the parent total is defined as source-unowned storage. The current preflight JSON
still reports `dgroup_5a96` residual size 25 and its `resolved_source_state` lists
only the selector byte; it has not deducted this already admitted pointer owner.
The scope-correct count would be 21 residual bytes in that cluster and 62 total
functional bytes. This review does not edit or regenerate the preflight report.

## Reproduction and evidence limits

The source census can be repeated with `rg -n "5A28|56FE|60B0|f_1B73_0B00|f_1B73_0AC3|g_6004|g_6016|g_6028|g_603A" src -g '*.c' -g '*.asm'`. It finds the explicit Timer API callers in `src/root/m1FD2.c` and no literal references to the unknown spans. Literal absence is not treated as a computed-address proof.

Prior evidence was read before this review: `build/workers/dos_clip_data_ownership/receipt.md`,
`build/workers/dos_data_debt_ownership_review/REPORT.md`, and
`build/workers/dos_storage_reachability_review/report.md`. The latter review leaves a
broader numeric-address audit unresolved. This receipt therefore records positive
type/use views separately from ownership and reachability: no unknown span is removed,
and the original exact-data ledger remains untouched.
