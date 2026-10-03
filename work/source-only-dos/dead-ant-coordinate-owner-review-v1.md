# Dead-ant coordinate-ring storage review

Status: source-only research in ignored scratch. Canonical files, tools, tests, mandatory packets, and Git state were not modified.

## Source ownership and extent

`DeadAntHere` in `src/root/m0894.c` is the source-functional owner. It advances the saved ring index, reads the prior x/y bytes, then writes the new coordinates at the same ring slot in both terrain branches. The canonical declarations are `unsigned char far [100]`; S09 exposes unsized unsigned-byte address views only in its persistent SaveRec table.

Each array has one `1 x 100` SaveRec row (100 bytes). The two adjacent registered symbols begin exactly at the measured end offsets; their bases do not establish the extents. Whole-module OMF and runtime fixtures independently measure/check the 100-byte byte arrays.

The source scan covered 127 canonical module sources plus 29 strict-effective sources (157 unique source paths). Registry scan: no alternate exact-base aliases and no registered symbol inside either half-open extent.

## Lifecycle and failure domain

DeadAntHere increments the saved signed-int ring cursor and only wraps values >=100 to zero before indexing either array. Valid indices therefore rotate through 0..99, but there is no negative-index guard. The cursor is a separate two-byte SaveRec record. No array or cursor reset appears in InitSimYard/RandYard; LoadGame calls RandYard before loading records but does not clear these arrays. SaveRec reads are in-place and sequential: a short read may mutate a byte-array prefix before the error branch skips successful-load postprocessing. Corrupt/partial saved indices and coordinates remain unchecked.

The arrays and ring index have no source reset in `InitSimYard`/`RandYard`; startup tentative-definition zero-fill is a separate clean-runtime result. `LoadGame` calls its yard reset helper before sequential SaveRec reads. A short read may mutate a prefix of a record before the length check fails and bypasses the successful-load rebuild path. Loaded ring/index/coordinate contents are not validated. Negative ring indices and byte coordinates outside `MapA` bounds remain unchecked source/layout concerns; this review establishes storage extent, not safety for arbitrary malformed saves.

## Whole-module compile and runtime controls

Fresh msc600ax control/candidate contribution comparison: True. The fresh control hash does not match the manifest object hash, so this probe does not claim historical object reproducibility. Segment payloads/extents, publics, local publics, and ordered fixups are preserved; the external-name set is unchanged, with the two requested scope changes. External-name ordering equal: False. The source candidate adds two far byte-array communals.

| Linker | Unsigned byte/base/extent | SaveRec byte view | Wrong base | 101-byte extent | Signed view | Initialized owner |
|---|---|---|---|---|---|---|
| rtlink400 | PASS | PASS | FAIL | FAIL | FAIL | FAIL |
| rtlink610 | PASS | PASS | FAIL | FAIL | FAIL | FAIL |

No game module stubs or original code bytes were linked. The deliberately malformed loaded-index/layout domain remains unclosed.
