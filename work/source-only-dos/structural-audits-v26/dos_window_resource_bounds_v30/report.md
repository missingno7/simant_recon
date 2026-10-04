# Window resource bounds audit v30

**Disposition: keep the remaining extents open.** The census found no source-owned DOS aggregate, checked resource-count limit, or independent Win16 size anchor that can safely size all requested owners. No canonical source, manifest, promotion record, or production contract was changed.

## Scope

Read all **127 canonical translation-unit sources and 29 strict-effective sources** selected by `work/source-only-dos/static-completeness`; `source-census.json` records each source path, SHA-256, and every matching line for the window tables, count scalars, menu arrays, DB loader/recall, and resource IDs 0x80/0x81/0x83. I also ran `python tools/context.py win_LoadAllWindows` without `--raw`; it confirmed the reset, copies, raw count loads, and loop bound visible in the canonical source.

## Proven DOS behavior

- `win_LoadAllWindows` clears 0xB4 bytes of hooks, writes the sentinel to 45 `win_offsets` rows, and copies 0x140 bytes (40 `Rect`s) into the start of that table. It reads the first three words of resource (0x80, 0) directly into `win_numOfWindows`, `win_numOfColors`, and `win_numOfGroups`, copies `win_numOfColors * 6` bytes from resource (0x81, 0), then iterates to `win_numOfWindows`. It also copies a fixed 0x28-byte resource (0x83, 0) into `purge[0x28]` and indexes that local by the same loop counter. The code has no count clamp or payload-size check. See `src/root/m20E8.c:96-136`.
- `win_LoadWindow` stores the loaded object handle into `win_handles[(char)(win >> 8)]` **before** calling the lock routine that tests the slot. The lock worker tests `n > 40 || n < 0`, calls `Punt`, and then has no source-level return before accessing the table; this does not constrain the loader’s earlier store. See `src/root/m20E8.c:36-57` and `src/root/m23AE.c:47-62`.
- Resource records do carry a byte size through `DBRecall`, but `db_LoadObject` receives that size only into a local and drops it. `DBRecall` trusts the record-header size and does not validate resource 0x80’s schema. The window object parser likewise follows its declared object count and record-size words without checking a payload extent (`RepointObjects`, `src/root/m2505.c:46-59`). See `src/root/m1A53.c:80-100` and `src/root/m19A9.c:71-134`.
- Menu layout writes `fd_50F6_46BC[i]` and `fd_50F6_46A8[i]` while walking `g_6054->titles` to its null pointer, then stores the observed count in `g_604C`. No maximum check protects that sentinel walk or later reads. `struct MenuData.items[16]` sizes the item-pointer rows; `titles` remains an unsized pointer list. See `src/root/m1FD2.c:25-27` and `src/root/m1FD2.c:384-411`.
- The 156-source census found no writer or schema for resources 0x80/0x81/0x83. The generic save wrappers have no caller in the effective source set, and `DBAdd`/`DBDelete` are read-only stubs that call `Punt` (`src/root/m1A53.c:168-181`, `src/root/m19A9.c:136-144`).
- The current build report still lists all six requested tables (`_win_handles`, `_win_drawHooks`, `_win_offsets`, `_win_colors`, `_fd_50F6_46A8`, `_fd_50F6_46BC`) as unresolved with no accepted storage candidates. The existing UI-resource contract covers only the three 2-byte count scalars.

## Cross-version evidence and limits

`evidence/cross_version/decisions.json` confirms `_win_LoadAllWindows` and the identities of `_win_offsets`, `_win_drawHooks`, `_win_colors`, and the three `win_num*` words (entries at lines 342, 354, 955-1007). `_win_handles` is a HIGH name/data correspondence at `root:55B3:9230` (line 1019); its Win16 entries are locked pointers, while DOS entries are Ralloc handles. There is no reviewed Win16 pair for `fd_50F6_46A8` or `fd_50F6_46BC`.

The recovered Win16 data sources spell `win_drawHooks[45]`, `win_offsets[45]`, and `win_colors[40][6]` (`D:\Prog\simantw_recon\src\recovered\data_pack_render_state-3ea18e1e4a.c:38`, `D:\Prog\simantw_recon\src\recovered\data_pack_window_tables-bbaafa7fd3.c:19`, and `D:\Prog\simantw_recon\src\recovered\data_pack_interface_colors-7108406eb4.c:35`). Their Win16 recovery ledger says each extent was measured as the MAPSYM anchor span to the next public (`D:\Prog\simantw_recon\src\recovery.json` entries at 26644/26654, 27892/27902, 31276/31286). Those declarations support semantic/layout correspondence, but those span-derived dimensions cannot serve as independent DOS capacity evidence under the no-neighbor-gap rule. The Win16 symbol inventory also records `_win_handles` with unknown ownership and null extent; it does not close the near-table owner gap.

## Open debt by table

| Owner | Proven extent evidence | Remaining gap |
|---|---|---|
| `win_handles` (near, 4-byte entries) | Indexed loads/stores and the registered base at `55B3:9230`; consumer set is `root:20E8`, `root:22BF`, `root:23AE`, `root:2505`. | No DOS definition or dimension. Resource 0x80 count is unchecked; the Win16 table is also extent-unknown. |
| `win_drawHooks` (far callbacks) | 45 entries / 0xB4 bytes are reset; only seven static setter calls are visible and the table is indexed by `win >> 8`. | The reset is a touched prefix. Data-driven indexing still lacks an admitted DOS maximum. |
| `win_offsets` (`Rect`, 8-byte rows) | 45 sentinel writes; 40 rows copied from a type-9 object; save/restore uses a window index. | The 0x80 count is unchecked; the 0x140 copy proves only a 40-row input prefix. |
| `win_colors` (6-byte rows) | Six-byte row stride and an unchecked `win_numOfColors * 6` copy from resource 0x81. | No source schema or bound on the count or object color indices. |
| `46A8` / `46BC` (menu `int` tables) | Reads/writes are indexed by menu number; all effective consumers are in `S10:35F5`, `S17:384C`, and `root:1FD2`. | Sentinel-derived title count is uncapped; no Win16 storage owner or reviewed address pair was found. |

The admitted `window-clip-handles` contract concerns a distinct far communal, `_fd_50F6_3B60` (45 four-byte clip handles); it is not a definition or extent for the near `win_handles` table.

## Artifacts

- `build/workers/dos_window_resource_bounds_v30/source-census.json` — complete 156-source hit inventory with hashes.
- This report — conclusions and evidence anchors.

No matching search, validation run, or production edit was performed.
