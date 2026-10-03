# Four-slot database record and handle storage candidate

This source-functional provider proposes exactly two independent FAR_BSS objects:
`fd_50F6_3958` as four `OpenDBRec` records (124 bytes each, 496 bytes total) and
`db_handles` as four signed 16-bit `int` values (8 bytes total). It owns no executable
functions, initialization, neighboring storage, or original translation-unit/order claim.

The source basis for four normal slots is direct. `GetFreeHandle` at root:1A28:0224
has a one-time initialization loop and a free-slot scan, both with `i = 0; i < 4; i++`;
each tests or clears only `name[0]`. It returns the selected value 0 through 3, or -1.
The original instructions independently show the same bounds (`cmp bx,4`), multiply by
`0x7c`, load the FAR_BSS segment from the 1A28 CONST word, and access `ES:[SI+0x3958]`.
`OpenDB` likewise multiplies the returned slot by `0x7c`, adds `0x3958`, and supplies
segment `0x50f6` to the name copy. Its no-free branch calls `Punt` and then falls through
to that same computation if `Punt` returns.
`OpenDB` is its only source caller. On success, `db_SetDataBase` stores the returned slot
at `db_handles[db_numOfHandles]`, reads the same word, and increments the count.
`db_LoadObject` visits indices below that count and passes each word to `DBRecall`;
`db_CloseDataBase` decrements the count and passes the corresponding word to `CloseDB`.
The front end starts the count at zero, so ordinary successful opens consume at most the
four slots returned by `GetFreeHandle`. `db_handles` words are record indices, not file
descriptors. They remain stale after close; a later successful open overwrites the reused
front-end entry. `db_SaveObject` and `db_ReplaceObject` access `[0]` directly and therefore
preserve their active-database precondition. Original instructions for `db_SetDataBase`,
`db_LoadObject`, and `db_CloseDataBase` use `ES:[bx+0x3b50]` after loading `ES` from the
1A53 CONST word for frame 50F6. `db_handles` is thus a word array at that exact base, with
each normal slot indexed at `count*2`. The separately registered name `fd_50F6_3B50` is
its alias. A fourth word ends at `3b58`; the registered object `fd_50F6_3B58` begins there.
That adjacency is only a consistency check, not the basis for the four-word extent.

The 124-byte record type is a coherent overlay of all three canonical views. At offsets
`00..4f` is the 80-byte name. At `50..67` is a 24-byte index area: root:1986 views its
first four bytes as a far `IndexEntry *` and the next 20 as `IndexHeader`; root:19A9
uses the entry key's first four bytes as a file offset and the same 24-byte index area;
root:1A28 sees this region as `index[24]`. The next 14 bytes (`68..75`) are `DBHeader`
(`long magic`, `int count`, `long freeBytes`, `long wastedBytes`) or the reader's 14-byte
raw view. Bytes `76..77` are the index-file word / `pad[2]`; `file` is at `78..79`, and
`dirty` is at `7a..7b`. MSC 6.00AX fixture assertions and emitted OMF extent verify these
widths. The alias `fd_50F6_3B50` is registered as `db_handles`; `fd_50F6_3B58` is a distinct
registered object. Neither alias nor the next address is used to size these owners.

`OpenIndex` loads 20 bytes of `IndexHeader` at record offset `+0x54`, reads its count,
allocates `count << 3` bytes for eight-byte `IndexEntry` rows, stores the dynamic allocation's
offset/segment at `+0x50/+0x52`, and reads the rows into that allocation. `CloseIndex` reads
and frees that far pointer without clearing it. `FindIndex` takes addresses of rows through
the record pointer and returns a row pointer to `DBRecall`; its lower-bound path may read the
one-past index row when the insertion point equals `count`. That dynamic index allocation and
its one-past/failure domain are separate from `fd_50F6_3958` and are not sized by this owner.
The canonical and selected FindIndex behavior source are included in the pinned inputs.
The write-side `CreateIndex`, `DBAdd`, and `DBDelete` are empty/Punt stubs in the DOS sources;
`db_SaveObject` and `db_ReplaceObject` are the actual front-end write call paths and only pass
`db_handles[0]` into those stubs. There is no `SaveRec` function in these canonical modules.

Lifetime preserves source behavior. The original resident section-27 FAR_BSS region at
frame 50F6 is linker zero-fill before entry: `tools/farbss.py` grounds its all-zero
`50F6:0000..4BCF` range in `work/data/s27_map.md`, and `docs/exe-format.md` identifies
section 27 as the resident data extension. In code, `GetFreeHandle` initializes only the
four names' first bytes once; `CloseDB` clears only that byte. `OpenIndex` writes its
dynamic pointer and index header, and `CloseIndex` frees the pointer without clearing it.
The create-file branch does not clear the index pointer either. A reused slot can therefore
retain the stale pointer after a prior close. The owner adds no reset and does not clear stale
fields or handle words. The 24-byte raw m1A28/m19A9 view is retained as a union overlay;
a deliberately near (two-byte) index pointer still leaves the 124-byte record extent because
of that byte view, but shifts the typed header boundary and fails the typed-view control.

The no-free-slot path is explicitly unresolved and is not made safe by these normal-path
extents. If all four names are occupied, `GetFreeHandle` returns -1. `OpenDB` calls
`Punt("Out of handles.")` and then continues to index slot -1 if `Punt` returns. If that
call path returns farther, `db_SetDataBase` can store the negative result at its next
count index (including `db_handles[4]` when the count is four), increments the count,
and then calls `Punt`. Other failures can also call `Punt` before later accesses. This
candidate neither assumes `Punt` is noreturn nor supplies padding/records/handle slots
for any invalid index. The independent `-1` fixed-layout dependency remains an admission
gate for any claim that must cover that failure path.

The error word is not padded to a fifth slot: if the four-handle caller path continues after
the `Punt`, `db_handles[4]` lands at `50F6:3b58`, where the registry records a distinct
object. The record failure address is `50F6:38dc` for `db == -1`. Neither region is claimed
by this candidate.

The guarded probe compiles only this provider and test-owned controls using pinned MSC
6.00AX `/AL /Os /Gs` (`/EM` is required by the profile), then links with RTLink/Plus 4.00
and 6.10. It checks exact OMF commons, total FAR_BSS map extent, CRT-zeroed startup,
first/last fields, the 24-byte raw/typed overlay and pointer offset/segment halves. Extent,
near-index-pointer, unsigned-handle and nonzero-initializer controls are separate negatives.
It reads no game image or database asset as a compiler, linker, or runtime input. The
fixtures establish source-functional compiler/linker behavior, not historical C object
ownership or communal allocation order.

Run with a fresh output directory under `build/workers/`:

```powershell
python work/source-only-dos/database-record-state-probe.py --out build/workers/database-record-state-ax-run-5
```
