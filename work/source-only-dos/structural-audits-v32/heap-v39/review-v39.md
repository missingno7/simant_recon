# fdata RTLink file-order probe v39

**Status: `ROOT_REVIEW_PENDING`.**

## Result

Moving `root:171C` (`U074.OBJ`) from the 31st root object position to the first position changed mapped addresses for its four known allocator publics under both RTLinks. It did **not** change which runtime archive members were selected: RTLink 4.00 still selected `fmalloc.asm` and `fdata.asm`; RTLink 6.10 still selected `fdata.asm` without `fmalloc.asm`. Application object order therefore does not explain the observed 6.10 fdata-without-fmalloc selection in this controlled contrast.

All four runs used the same 188 hash-pinned object files, 193 symbolic aliases, runtime libraries, `NODEFLIB`, `RELOAD FAR 400`, root/data grouping, four overlay areas and linker settings. The only T.LNK variable was root FILE order. The library directive stayed in its production position before FILE entries.

| RTLink | Object order | Selected members | fmalloc | fdata | Undefined symbols | Duplicate diagnostic |
|---|---|---:|---:|---:|---:|---|
| rtlink400 | current | 112 | True | True | 15 | warning wrt0011: Public symbol '__ffree' doubly defined |
| rtlink400 | root:171C first | 112 | True | True | 15 | warning wrt0011: Public symbol '__ffree' doubly defined |
| rtlink610 | current | 115 | False | True | 15 | none |
| rtlink610 | root:171C first | 115 | False | True | 15 | none |

The selection sequence and member set match exactly between object orders for each linker. Each run remains diagnostic and incomplete: RTLink writes an image with 15 unresolved symbols; none of the generated images was executed.

## Runtime member data and public ownership

| LLIBCR member | OMF `_TEXT` length | OMF `_DATA` length | Publics of interest |
|---|---:|---:|---|
| `fmalloc.asm` | 144 | 0 | __ffree@_TEXT:0000, __fmalloc@_TEXT:0013 |
| `fdata.asm` | 0 | 14 | __fheap@_DATA:0000 |
| `initseg.asm` | 52 | 0 | __initseg@_TEXT:0000 |
| `linkseg.asm` | 54 | 0 | __linkseg@_TEXT:0000 |
| `growseg.asm` | 256 | 2 | __incseg@_TEXT:008F, __growseg@_TEXT:0000, __findlast@_TEXT:00E0, __amblksiz@_DATA:0000 |

The selected member OMF definitions show `fmalloc.asm` has 144 bytes of `_TEXT` and zero `_DATA`; `fdata.asm` has a 14-byte `_DATA` public contribution defining `__fheap` at offset 0. `initseg.asm` and `linkseg.asm` contribute 52 and 54 bytes of `_TEXT` and zero `_DATA`; `growseg.asm` contributes 256 bytes of `_TEXT` and two bytes of `_DATA`. RTLink 6.10’s maps place `fdata.asm` at `DGROUP:798E` with length `000E`, followed by zero-length `initseg.asm` / `linkseg.asm` data and two bytes from `growseg.asm` at `DGROUP:799C`; those rows are identical under both tested object orders.

The public map rows for `_malloc`, `_free`, `__ffree` and `__frealloc` resolve to `U074.C` in all four runs. Their OMF definitions remain owned by `root:171C`; only the map coordinates change when that object moves first. RTLink 4.00 continues to report `wrt0011` for the duplicate `__ffree` from selected `fmalloc.asm`. RTLink 6.10 selects no `fmalloc.asm`, so it emits no corresponding duplicate.

## Artifacts and limits

The build report SHA-256 is `0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf`; the object-set pin digest is `2ad5fc060900682e55fe686d41446a33630c259b1b70caab44636905b7e94969`. The exact current link inputs are recorded with their object, runtime library, linker and utility-library hashes in [file-order-v39.json](file-order-v39.json). It also records every selected LLIBCR, LIBH and pinned RTLink RTLUTILS member’s OMF publics, segment extents, external declarations and live fixup targets.

Complete raw CRLF logs and maps are preserved in each run directory and pinned by raw-byte SHA-256 in the JSON receipt. The generated EXE files remain unexecuted. No source or object was edited, no stubs were used, and this result makes no historical `DGROUP:79F0` placement claim. Since the order change did not alter archive selection, no extra control was run.

The four run directories are `baseline_current_order/rtlink400`, `baseline_current_order/rtlink610`, `root_171c_first/rtlink400`, and `root_171c_first/rtlink610` under this folder.
