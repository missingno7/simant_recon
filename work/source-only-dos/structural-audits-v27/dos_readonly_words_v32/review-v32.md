# Read-only storage-lineage audit v32

Status: `READONLY_STORAGE_LINEAGE_AUDIT_COMPLETE_ROOT_REVIEW_PENDING`; `root_reviewed: false`.

This audit checks three unresolved 50F6 words against the current 156-source effective graph, accepted owner/view extents, source-shaped arrays, source address escapes, bulk API calls, and the complete 307-payload-row SaveRec table. Physical overlaps use each full two-byte target interval. No target owner or zero value is inferred from neighboring addresses or absent stores.

The source graph is pinned in [source-pins-v32.json](source-pins-v32.json); detailed evidence and the per-word frontier are in [source-audit-v32.json](source-audit-v32.json).

| Target | Declaration | Direct reads | Direct writes | Address escapes | Provider/SaveRec word overlap |
|---|---|---:|---:|---:|---|
| `fd_50F6_04C0` (`50F6:04C0`) | signed `int far` | 1 | 0 | 0 | none |
| `fd_50F6_0B20` (`50F6:0B20`) | signed `int far` | 2 | 0 | 0 | none |
| `fd_50F6_0F38` (`50F6:0F38`) | signed `int far` | 6 | 0 | 0 | none |

All accepted provider spans, source-owned scalar/history/water lists, reviewed 50F6 alias geometry, and pinned owner-binding receipt providers were checked as half-open intervals. The 307 SaveRec payload rows were resolved to registered starts and lengths, with no target-word overlap. The nearest boundaries are [04BE,04C0)/[04C2,04C4), [0B1E,0B20), and [0F36,0F38)/[0F3A,0F3C).

At 04C0, the four adjacent balloon arrays share `fd_50F6_1092`; its current admitted UI-state contract proves zero startup in RTLink400/610 fixtures, and the source only resets it to zero or increments behind the `>=6` guard. That bounds adjacent-array writes to slots 0..5 and is used only to close array-crossing paths, not to infer 04C0. The other adjacent vector writes fixed indices 0..5, and DrawSwarm indexes its post-target byte array only with nonnegative `i<16`.

The bulk-call inventory has no argument naming any target or its physical offset; nearby owner bases have no non-SaveRec address escapes or explicit +/- pointer arithmetic. The symbolic non-raw contexts confirm the consumers: `main` compares 04C0, `SimRain` compares 0B20, and the map-bound helper reads 0F38. The source graph still does not establish target backing ownership or BSS-zero. All three remain unresolved.
