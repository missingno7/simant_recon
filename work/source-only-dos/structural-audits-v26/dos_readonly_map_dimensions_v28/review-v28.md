# Read-only map-dimension lineage audit v28

Status: `READONLY_LINEAGE_AUDIT_COMPLETE_ROOT_REVIEW_PENDING`; `root_reviewed: false`.

The current 156-source effective graph treats both words as read-only signed `int` imports used as horizontal/vertical map limits. It does not prove either value is zero or owned by an existing larger object. Current storage-provider extents and the complete SaveRec table contain neither target.

The fresh source universe is pinned as 127 canonical U000-U126 modules plus 29 strict-effective whole modules, all 156 paths unique. Source and authority hashes are in [source-pins-v28.json](source-pins-v28.json). The full compact finding and exact frontier are in [source-audit-v28.json](source-audit-v28.json).

| Target | Source declarations | Direct reads | Direct writes | Current report |
|---|---:|---:|---:|---|
| `fd_50F6_0FB6` (50F6:0FB6) | 4 signed-int `extern` | 14 | 0 | unresolved FAR_BSS; no accepted storage candidate |
| `fd_50F6_0FFA` (50F6:0FFA) | 4 signed-int `extern` | 10 | 0 | unresolved FAR_BSS; no accepted storage candidate |

The source-owned 50-byte buffer at `0F84` occupies `[0F84,0FB6)` exactly; `0FB6` is its exclusive end. The source-owned 50-byte buffer at `0FC6` occupies `[0FC6,0FF8)`; `0FFA` begins two bytes later. Current provider proofs include no extent containing either target. `DrawSwarm` indexes these buffers only below 16. The explicit 307-row SaveRec table also has no row whose span contains either word.

Confirmed Win16 pairs cover `RandWorld`, `SetMapPlaneLocation`, `SetMapPlane`, `SetAlarmDropState`, and `InvalEuMap` as functions. They support the dimension-consumer reading, but do not pair either DOS data word with a Win16 variable. Non-raw `context.py` disassembly corroborates reads immediately before `InvalEuMap`.

The current intake remains `INCOMPLETE`, with `standalone_dos_executable: false` and `runnable: NOT_EXECUTED`. Therefore source-visible absence of stores plus adjacent-span checks do not establish CRT/BSS startup zeroing or a closed runtime write set. Both targets remain unresolved; no owner or zero initializer is proposed.
