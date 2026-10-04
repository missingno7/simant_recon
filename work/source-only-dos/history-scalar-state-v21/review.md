# ClearHistory scalar-state candidate v21

**Status: `ROOT_REVIEW_PENDING_UNADMITTED`; `root_reviewed: false`.** This is a bounded SOURCE_ONLY_DOS candidate for 12 separate signed FAR scalars under `source-owned:history-scalar-state`, with provider basename `HISTOTAL`. It claims source-functional typed storage only; it does not infer the historical COMDEF-producing module, communal order, padding, or original physical placement.

The rank-3 shortlist family is **ClearHistory scalar counters and totals**. The source audit uses 127 canonical translation units plus 29 strict-effective modules, for 156 unique source paths, including the corrected effective `DrawBalloons` source. All twelve targets remain unresolved in the selection snapshot. Existing history-array and spider-counter ownership is used as an exclusion; none of the candidate spans overlaps those owners.

| Address | Source type | OMF far common `(count × element_size = bytes)` | Exact SaveRec row (line / index) |
|---|---|---:|---:|
| `50F6:04F4` | signed `int far` | `2 × 1 = 2` | `2,1` (1064 / 171) |
| `50F6:0A90` | signed `int far` | `2 × 1 = 2` | `2,1` (997 / 104) |
| `50F6:0A9E` | signed `int far` | `2 × 1 = 2` | `2,1` (996 / 103) |
| `50F6:0AC4` | signed `int far` | `2 × 1 = 2` | `2,1` (1130 / 237) |
| `50F6:0AC8` | signed `int far` | `2 × 1 = 2` | `2,1` (1129 / 236) |
| `50F6:0ADA` | signed `long far` | `4 × 1 = 4` | `4,1` (932 / 39) |
| `50F6:0EFC` | signed `long far` | `4 × 1 = 4` | `4,1` (926 / 33) |
| `50F6:0F30` | signed `long far` | `4 × 1 = 4` | `4,1` (925 / 32) |
| `50F6:0F3E` | signed `long far` | `4 × 1 = 4` | `4,1` (935 / 42) |
| `50F6:0FBC` | signed `long far` | `4 × 1 = 4` | `4,1` (934 / 41) |
| `50F6:0FC2` | signed `long far` | `4 × 1 = 4` | `4,1` (941 / 48) |
| `50F6:1000` | signed `long far` | `4 × 1 = 4` | `4,1` (940 / 47) |

Across those members, the fresh identifier scan records 174 source references, including 62 writes/increments and 39 direct readers. Each has one exact registered base name, no registered interior view within its typed span, one exact raw `SaveRec` address row, and no non-`SaveRec` address escape. The `SaveRec` table has 307 data rows before its terminator. The one non-direct initializer uses `fd_3D57_087A + 20`; every candidate row is a direct `&name` view with addend zero. Literal matches to `0x1000`/4096 are separately classified in the candidate receipt; they are masks, IDs, thresholds, extents/counts, or immediate/data expressions, not a `50F6:1000` numeric address.

The data-only provider is twelve individual tentative `int far`/`long far` definitions, no aggregate, function, or initializer. MSC 6.00AX emits exactly five `far` commons of count 2, element size 1, length 2 and seven of count 4, element size 1, length 4, with no extra live segment bytes, publics, or fixups. Signedness is supported by source/runtime evidence because the OMF common shape does not encode it.

Both RTLink 4.00 and 6.10 ran the same seven-case matrix in DOSBox-X. Typed signed startup-zero and raw `SaveRec` startup-zero positives passed; short-long, wide-int, unsigned, nonzero-initializer, and shifted-base controls all produced their expected contrast markers. All 14 link logs are clean, both map sections are preserved and checked for the required publics, and alias/target addresses satisfy the measured displacement in both sections. The shifted-base case changes only `ProbeShift0` by +2; the remaining shift aliases are exact-base controls. Verbatim run/link output, maps, object files, executables, and their pins are retained below `runtime/fixtures/` and indexed by the report.

`ClearHistory` resets five members only under `newGame == 1`; its other seven stores are unconditional within that function. Source call sites pass 0 and 1. The generic loader reads `count * size` raw bytes without validating values, so this candidate makes no claim of bounded values or universal reset lifetime. No original executable or game object bytes were read; the DOS input guard recorded no denied/oracle reads.

The raw probe and complete source audit are [report-v21.json](report-v21.json) and [source-audit-v21.json](source-audit-v21.json). The scratch provider is [history-scalar-state.c](history-scalar-state.c), the no-rerun admission normalizer is [admission-adapter-v21.py](admission-adapter-v21.py), and the normalized candidate plus its preserved pin inventory are [history-scalar-state-candidate-v21.json](history-scalar-state-candidate-v21.json) and [receipt-pins-v21.json](receipt-pins-v21.json). Root review and any production integration remain outside this worker.

Execution note: after the first scratch probe, I corrected only the source-audit scanner for MASM semicolon comments, numeric-literal classification, and the one SaveRec pointer-expression row, then reran the scratch probe before receiving the preservation instruction. That second run passed the same 14-case matrix and is the run pinned by this receipt; the first run's scratch outputs were overwritten and are not represented as preserved evidence. The adapter only reads and verifies the pinned run; it does not compile, link, rerun, or overwrite probe artifacts.
