# Follow-up: code-address materialization reachability scan

This supplements `code-span-investigation.md`. Its purpose is to test a specific gap in the earlier negative evidence: a compiler may materialize a far function pointer in instructions (`offset` immediate plus a separate relocated segment, CS-derived segment, or paired stack/store writes) without leaving a contiguous raw far-pointer pair at a data address.

The scan is pinned in `code-pointer-materialization.json` and reproduced by `scan_code_materialization.py`. It decodes all 1,730 catalogued original function extents. Every matching immediate is interpreted in its own instruction segment and unit; a near branch only addresses a gap when both unit and CS frame match, while an immediate far call is checked as the ordered segment:offset pair. The probe also checks target-offset immediates for same-window `push cs` plus `push offset`, a segment immediate carrying an exact loader relocation, a nearby `mov reg,cs`, and memory-immediate writes. These are diagnostic patterns, not a complete proof against runtime-computed pointers.

## Result

| Gap offset | Raw matching immediates in known extents | In target CS frame | Exact unit/frame control transfer | Address-materialization pattern |
|---|---:|---:|---:|---:|
| root `0E2E:0931` | 5 | 0 | 0 | 0 |
| root `1C62:069E` | 1 | 0 | 0 | 0 |
| root `1E57:0008` | 603 | 31 | 0 | 0 |
| root `1E57:0EB0` | 0 | 0 | 0 | 0 |
| root `23AE:037E` | 2 | 0 | 0 | 0 |
| root `284A:0137` | 0 | 0 | 0 | 0 |
| S04 `35F5:0980` | 0 | 0 | 0 | 0 |

All five `0931` matches are near conditional/unconditional branches whose CS frames are `0BE8`, `1383`, or `1CE2`, not `0E2E`. The lone `069E` match is a branch in root frame `2662`, not `1C62`. The two `037E` matches are branch destinations in frames `0000` and `1A53`, not `23AE`. Because near transfers retain the caller's CS, none points into the corresponding root gap. The `0008` matches include far calls whose *offset* happens to be 8 but whose far-call segment is not `1E57`; none is a segment:offset match to `1E57:0008`.

The 31 same-frame occurrences of `0008` in module `1E57` are ordinary instruction operands: 25 `add`/`sub` immediates and six register `mov` immediates (the moves load `CL`, `SI`, or `CX`). Across the full image there are 13 memory-immediate writes of 8. Four are writes to local BP slots (`DrawSpider`, `DrawBalloons`, `MakeBalloon`, `f_29F4_0F46`); the others write immediate values into data or object fields. None has a paired segment component identifying `1E57:0008`; nearby segment-fixup words include `1699`, `29F4`, `55B3`, and `293A`, not `1E57`. None forms a far-pointer store. No matching offset immediate has an immediate-field loader fixup, no nearby `mov reg,cs` context exists, and no same-window CS+offset push pair or relocated target-segment materialization was found. No other gap offset occurs as an immediate in its own target frame.

Across all targets the probe finds zero exact unit/frame control transfers and zero candidate segment/CS materialization sequences. The raw `offset,segment` pair scan and full relocation scan also remain empty. These negative results address code-generated pointer construction in known function extents; they do not cover unowned caller bodies or arbitrary runtime computation.

## Source/map cross-check

The exact symbol registry has no code entry at any gap address. The source tree has no exact target-shaped function/public spelling, nor standalone hexadecimal offset literal for these addresses. The relevant module source order also leaves the gaps unexplained as explicit C:

- `src/root/m1C62.c` has `f_1C62_0415` followed by `f_1C62_06A6`; no `f_1C62_069E` source/public name.
- `src/root/m1E57.c` defines empty `f_1E57_0006` and `f_1E57_0007`, then `f_1E57_0009`; it has no offset-8 definition and no wrapper body between `clip_Push` and `clip_Pop`.
- `src/root/m23AE.c` ends its relevant source sequence at `win_LockWin`; there is no source/public label for `23AE:037E`.
- `src/root/m284A.c` defines `StopSong`, then the `f_284A_0138` scaffold; there is no source/public label at `284A:0137`.
- `src/S04/m35F5.c` implements `DrawMiniMapCursor` and `EraseMiniMapCursor` and contains their callers, but no toggle helper body/name at `35F5:0980`.

Address-shaped text elsewhere is segment-qualified and unrelated: S00 assembly has a local `L069E` label and a public ending `_0137`; S25 has `o25_39C7_0980`. Those labels do not bind to root `1C62:069E`, root `284A:0137`, or S04 `35F5:0980`. This is why literal suffix matches and overlay-linear-address comparisons are excluded from reference claims.

## Freeze implication

This follow-up reduces the likelihood that a statically initialized or instruction-materialized function pointer in a known body reaches the examined spans. It does not establish that the spans are unreachable: an unowned caller, a runtime-built pointer, or data interpreted through an unrecognized dispatch mechanism remains outside scope. Keep all candidate functions and data bytes as explicit historical debt until a positive owner/entry chain or reviewed non-semantic layout proof is found.
