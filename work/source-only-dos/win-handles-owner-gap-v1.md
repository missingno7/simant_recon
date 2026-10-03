# `win_handles` owner/extent gap v1

**Disposition: fail closed; no provider or runtime fixture admitted.** The original address and four-byte entry stride are grounded, but no exact DOS owner declaration or extent is recovered. The nearest independently verified linker allocation is runtime `__bufin`; it begins after the table address and does not own the preceding bytes.

## Address, type, and lifetime

`layout/symbols.json` registers `win_handles` at `55B3:9230` with grounding from the indexed 4-byte table loads in `root:2505`; `g_9230` is only its legacy alias. The four canonical declarations (`src/root/m20E8.c:30`, `m23AE.c:33`, `m22BF.c:62`, `m2505.c:37`) are all unsized `extern char far * far * near win_handles[]`. This describes a near table whose elements are 16:16 far pointers to far master pointers (Ralloc handles), four bytes per entry. It does not state a dimension or owner. The address getter `f_2505_0006` returns the dereferenced window pointer (`src/root/m2505.c:39-44`), so pointees escape to callers under lock discipline.

The actual direct table users are:

| Function | Direct effect | Source |
|---|---|---|
| `win_LoadWindow` | stores the handle | `src/root/m20E8.c:36-47` |
| `f_23AE_0069` | tests, reads, and reloads the handle | `src/root/m23AE.c:41-76` |
| `win_UnlockWin` | reads and clears on final discard | `src/root/m23AE.c:131-174`; body is a scaffold in this TU, with registered behavior evidence in `evidence/behavior/functions/win_UnlockWin/contracts/window-valid-v1/module.c` |
| `win_IsWinOpen` | reads and clears if the Ralloc lock returns null | `src/root/m22BF.c:483-500` |
| `f_2505_0006` | reads and dereferences | `src/root/m2505.c:39-44` |
| `win_Recalc` | reads and locks the handle | `src/root/m2505.c:294-310` |

`win_LoadAllWindows` reaches `win_LoadWindow` for each loader index (`src/root/m20E8.c:98-137`). `win_LockInit` resets only `g_8CF2[45]` and `g_8DA6[45]`, not `win_handles` (`src/root/m23AE.c:7-24`), so the missing owner's initial-zero/lifetime role is also unresolved.

## Index domain and resource producer/guard gap

The only explicit attempted slot check is in `f_23AE_0069`: it converts `(win >> 8)` to signed `char`, calls `Punt` when below 0 or above 40, then continues into `win_handles[n]` (`src/root/m23AE.c:47-57`). `Punt` is declared `void` and its recovered body displays the error and calls the alert path without a nonreturn contract (`src/root/m1C62.c:46-59`); this cannot be relied on as an index guard. Other direct or indirect table paths lack that check, including `win_UnlockWin`, `win_IsWinOpen`, `f_2505_0006`, `win_Recalc`, `win_IsWinLocked`, and `f_2505_04D7`. `f_2505_04D7` also has an explicit `win >= 0x2800` bypass before its table getter (`src/root/m2505.c:265-270`). The checked `f_2505_0453` admits the same range before locking (`m2505.c:243-262`).

The sole canonical assignment to `win_numOfWindows` is `win_numOfWindows = p[0]` from resource `(0x80,0)` (`src/root/m20E8.c:115-123`; confirmed by repository-wide source search). There is no sign or maximum check. The subsequent loop passes `i << 8` to `win_LoadWindow` while `i < win_numOfWindows` (`m20E8.c:134-136`). In the same loader, `purge` is only 0x28 bytes and is copied from resource `(0x83,0)` as 0x28 bytes, then indexed by `i`; this is not a count guard and an oversized count reads past the local array.

The DB path supplies no format-level cap: `db_LoadObject` obtains a `size` output from `DBRecall` but never validates or returns it (`src/root/m1A53.c:80-100`). `DBRecall` derives record length from the DB header and calls a generic hook (`src/root/m19A9.c:71-134`); it has no resource-0x80 schema check. The only installed hook found is `f_0000_0000`, which transforms type-5 sound samples and does not validate type-0 window data (`src/root/m277E.c:81`, `src/root/m0000.c:39-54`). No source producer/schema or count guard was found for the three resource-0x80 words. The window stack's 31-entry capacity (`src/root/m1E57.c:12,54-69`) limits stack depth, not the identifier/index supplied by the loader, public window APIs, or matching event codes.

Parallel storage cannot supply the missing owner extent: `g_8CF2[45]` and `g_8DA6[45]` are separately accepted lock/cache arrays (`m23AE.c:7-8`); `win_offsets` is initialized for 45 slots and populated by a fixed 0x140-byte copy (`m20E8.c:98-110`); `win_drawHooks` is cleared for 0xB4 bytes (`m20E8.c:106`). These are distinct owners and do not authorize the same dimension for `win_handles`. If slot 40 is a legitimate ordinary index, its four-byte entry gives a 164-byte minimum requirement for that access; it is not proof of the array extent.

## Independent linker allocation check

The accepted runtime scanner was rerun with `python tools/runtime.py verify`. It reports authentic `llibcr.lib::_file.c` near communal `__bufin`, 512 bytes, at DGROUP `55B3:92E4`, derived from two agreeing fixup anchors (`_file.c _DATA+0x6` and `_DATA+0x0`). Parsing the pinned library OMF independently confirms `_file.c` has a near `COMDEF __bufin` of length 512; it is the only communal in the pinned `llibcr.lib` and `libh.lib` members. This proves the runtime communal's own extent `[92E4,94E4)`. It does not prove the preceding interval `[9230,92E4)` belongs to `win_handles`: the 0xB4 address difference happens to equal 45 four-byte entries, but adjacency/common membership of `__bufin` supplies no preceding declaration, segment bound, or table owner. `g_94E4` at the far end is likewise only a following symbol, not a table owner/bound.

The reviewed cross-version decision `evidence/cross_version/decisions.json` at `root:55B3:9230` supports the Win16 name `_win_handles` and API correspondence; its note that Win16 entries are locked pointers provides no DOS declaration or extent. No original game OMF, MAP, or debug declaration identifying the DOS array owner/extent was found in the repository evidence inventory. Thus neither Win16 naming nor the new `__bufin` linker evidence closes the DOS owner gap.

**Required evidence still missing:** either a source-grounded functional array extent with a proven index domain across the loader and consumers, or an original DOS declaration/allocation anchor supplying the extent. Recovering the historical producing TU/order is not required for a functional source owner. The current audit proves neither route; do not infer 41/45 entries from checks, adjacent storage, or harness ranges.
