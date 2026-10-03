# Graphics-formula candidate: write-reachability review

**Disposition: unadmitted; write reachability remains open.** This review covers the candidate intervals `DGROUP:2100..2107`, `DGROUP:68AC..68B3`, and `DGROUP:68B4..68B5`. The separate original-only probe confirms their 18 pre-instruction contents against the selector and mask predicates. We have not recovered the original declaration or translation unit, proven values after startup, or established the complete allocated extent. The historical debt ledger remains unchanged.

Run `python work/source-only-dos/graphics-formula-write-review.py` to recreate the read-only receipt at `build/workers/dos_graphics_formula_write_review/receipt.json`. The probe pins its source/evidence inputs, checks the named C writer shapes and overflow-guard order, and computes the real-mode linear distance from the clip buffer to the first candidate interval. It reads no original executable, image bytes, or build image. Its output is a source reachability result, not a candidate admission packet.

The separate original-only check is `python work/source-only-dos/graphics-formula-initial-state-research.py`; its value-free result is `graphics-formula-initial-state-research-v1.json`. It reads just the 18 candidate bytes from the locked image in the research VM before any guest instruction and tests typed predicates, without emitting the values or importing the research code into a guarded source-only probe.

## Evidence split

1. **Initial contents and consumer bounds.** All 8 selector predicates, 8 one-bit residue-mask predicates, and 2 packed-parity predicates pass against the original pre-instruction image. Reversed plane order, low-bit byte masks, and an odd-width low-nibble mask are rejected. The selector consumers index by `x & 7`; the one-bit mask consumer indexes by `width & 7`; and the packed mask consumer indexes by `width & 1`. Because a future source owner may use mutable arrays, this result describes initial values only; it does not claim immutability.
2. **Normal-read names and bindings.** Both selector consumers name `_g_2100` symbolically. The byte and packed masks are read by absolute `SS:[BX+68AC]` and `SS:[BX+68B4]` operands, respectively. The reviewed normal-startup and driver-frame evidence supports `SS=DGROUP` for those audited calls, but it does not supply historical symbol names for the two mask tables or establish their original storage declarations.
3. **Write and layout geometry.** The clip-copy route below remains unresolved for all three candidate intervals. Typed initial-value agreement does not close post-startup mutation, arbitrary alias reachability, or the longer copy paths, and it does not establish the historical owner/extent or admit these arrays.

## Relevant source path

The source-owned `g_5AAC` slot is a mutable near pointer to a far `Rect` list. Canonical root `m1E57.c` assigns it null, `&g_5A9C`, a locked handle payload, the FAR_BSS clip buffer, or the saved clip-stack payload (`clip_SetWin`, `f_1E57_0296`, include/exclude routines, and `clip_Pop`). `clip_Push` saves the pointer’s current list into a DOS handle. These assignments do not themselves point at the formula intervals, but some copies through the FAR_BSS buffer have variable lengths.

The current registered evidence for `f_1E57_038E` is a whole-module behavior-exact source at `evidence/behavior/functions/f_1E57_038E/contracts/window-valid-v1/module.c`, pinned by `work/source-only-dos/static-completeness/f_1E57_038E.json`. Its contract covers 265 recorded valid inputs: window stacks through 31, valid IDs through 44, and sorted rectangles in the documented domain. It excludes invalid IDs, malformed allocator state, and stacks above 31. The registered body allocates 256-rectangle working lists, checks generated counts against 256, and calls `Punt` before later operations. This evidence supports its accepted finite valid domain; it does not prove every malformed/error continuation terminates.

The unresolved copy path is explicit in canonical `src/root/m1E57.c`:

- `clip_SetWin` (lines 120–140) and `f_1E57_0296` (158–179) scan sentinel-terminated lists from handle payloads, compute a variable `size`, then copy that many bytes to `fd_50F6_3C14`.
- `clip_Pop` (473–496) scans its saved handle payload and copies the variable list length to the same FAR_BSS buffer.
- `clip_SubInclude`, `f_1E57_08F5`, `clip_SubExclude`, and `f_1E57_0C2D` (296–437) set `g_5AAC` to `fd_50F6_3C14` and copy `(n + 1) << 3` bytes. Their `n >= 256` guards call `Punt` before the copy; these C declarations do not establish `Punt` as non-returning.

The symbol map places the FAR_BSS destination at `50F6:3C14`, linear `0x54B74`, and DGROUP at `55B3:0000`, linear `0x55B30`. The three candidate intervals are 12,476, 30,824, and 30,832 bytes after the clip-buffer start. A generated-list copy of `(n + 1) << 3` first intersects them at these counts:

| Candidate interval | Distance from `50F6:3C14` | First intersecting `n` |
|---|---:|---:|
| `55B3:2100..2107` | 12,476 bytes | 1,559 |
| `55B3:68AC..68B3` | 30,824 bytes | 3,852 |
| `55B3:68B4..68B5` | 30,832 bytes | 3,853 |

All three thresholds fit in the source's signed 16-bit count and the copy-length argument's 16-bit range. This gives concrete possible write spans; it does not prove such lists are reachable. The sentinel-copy paths also have no accepted maximum length in this review. A path that produces or retains an over-limit handle and later reaches `clip_SetWin`, `f_1E57_0296`, or `clip_Pop` is not excluded by the registered valid-domain contract.

The exact unresolved writer is therefore:

```text
g_5AAC / generated or saved clip handle
  -> sentinel scan or generated-list count
  -> variable-length copy to FAR_BSS 50F6:3C14
  -> any candidate interval if the copy spans its recorded threshold above
```

There is no source evidence here proving the required length can occur, and no evidence excluding it on malformed or `Punt`-return paths. The candidate intervals remain unadmitted while that route is unresolved.

## Other writer evidence and limits

The companion formula probe records direct selector/mask reads and no direct writes or initialized pointer declaration naming these candidate intervals. Its 229-site assembly `MOVS` inventory and the broader typed-destination review found fixed video/DGROUP destinations, stack objects, DOS allocations, EMS windows, and indexed FAR_BSS arrays with separate bounds. Those findings do not close the variable clip-list path above, and the generic assembly copy inventory is not itself an arbitrary-pointer exclusion proof.

The formula provider is still a test-owned functional hypothesis. No original table bytes were copied into source; no debt values were inferred from a neighbor gap. Because source initializer/TU ownership is unknown and writes are not fully excluded, this review makes no claim that the candidate intervals are immutable source tables. No canonical source, tool, manifest, promotion journal, or historical debt disposition was changed.
