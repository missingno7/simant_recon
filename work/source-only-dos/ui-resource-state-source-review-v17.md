# DOS UI resource and adjacent FAR_BSS owner review

This scratch review uses the canonical 127 translation units and the 29 effective whole-module sources selected by `work/source-only-dos/static-completeness/index-v1.json` (156 unique source paths). The guarded audit records every source hash and matching reference. It reads no original executable/object/image bytes and changes no canonical source, layout, manifest, or promotion state.

## Closed scalar subfamily: resource counts

`win_numOfWindows`, `win_numOfColors`, and `win_numOfGroups` are far signed 16-bit `int` objects (2 bytes each). `win_LoadAllWindows` reads words 0, 1, and 2 from resource `(0x80,0)` into them. The source establishes width but does not bound the values in those words.

## Separate adjacent pointer subfamily

`fd_50F6_3B4C` is the far pointer-to-pointer root returned by `f_2CFB_0002`; the cache allocates `g_389E * 6` bytes for `EmsSlot` rows and indexes the allocated table. `fd_50F6_3B58` is a four-byte far callback slot selected with the graphics driver and called with `(src,dst,shift,flag)`. `fd_50F6_3B5C` is a four-byte `Handle` head for the linked clip-push stack; `clip_Push` stores the old head in each allocated node and `clip_Pop` restores it. The source types/operations and large-model pointer ABI establish 4-byte extents; the fresh MSC OMF probe checks the exact 2/4-byte shapes.

The candidate provider is `providers/ui-resource-state.c`. It owns only those six scalar/pointer objects. The compile/link probe checks startup zeroes, typed reads/writes, the callback call, EMS slot indirection, and handle-head round-trip. Wrong-width and initialized-owner negatives run under RTLink 4.00 and 6.10; the near-pointer contrast is an OMF-only negative because the linker does not check C pointer-type consistency. These are functional storage controls, not a claim about historical communal order or placement.

## Resource arrays remain unresolved

- `win_drawHooks`: `win_LoadAllWindows` clears exactly `0xB4` bytes and the indexed entries are far callbacks, establishing a 45-entry initialized prefix (180 bytes). `win_SetWinDrawHook` stores the callback and `win_DrawWindow` calls it for phases 1/2. Source does not cap every index or prove no caller writes beyond that prefix; no exact maximum extent is claimed.
- `win_offsets`: `win_LoadAllWindows` initializes 45 `Rect` records (360 bytes) and copies a fixed `0x140` bytes (40 records) from resource 9. Window load/open/close and drawing code read/write rows by `win >> 8`. The window count driving loading comes unchecked from resource 0x80. The 45-row source initialization is a minimum touched prefix, not a proven upper bound.
- `win_colors`: each accessed record has six `char` fields. Resource 0x80 supplies `win_numOfColors`; resource 0x81 supplies the bytes copied to this table using the unchecked product `win_numOfColors * 6`. No source producer/schema or count validation bounds that product, so the storage extent remains unknown.

`win_handles` remains unresolved as recorded in `work/source-only-dos/win-handles-owner-gap-v1.md`; the resource-derived window count does not bound it in source. This review does not borrow its extent from neighboring symbols or from the other tables.

The code loads resources `(g_5A97,9)`, `(0x80,0)`, `(0x81,0)`, and `(0x83,0)` through `db_LoadObject`. The source has generic `db_SaveObject`/`DBAdd` code, but no call that writes resource IDs `0x80`, `0x81`, or `0x83`, and no schema for their external records. `DBRecall`/`db_LoadObject` expose record bytes without validating these resource fields. The three `win_num*` objects and the three adjacent `fd_50F6_3B4C/3B58/3B5C` objects do not appear in the S09 SaveRec table, so no SaveRec lifetime/extent evidence is claimed for them.

The source-call closure preserves aliases: display code calls `f_21FA_00EE` for `win_SetColorNum` and `f_21FA_08E2` for `win_DrawWindow`; the symbol registry maps these identities to the named implementations. `win_SetWinDrawHook` has seven direct canonical registrations in `src/root/m00BA.c` for IDs `0`, `0x100`, `0x1500`, `0x1200`, `0x1300`, `0x1900`, and `0x500`; it stores callback values that `win_DrawWindow` later calls indirectly. `win_colors[color]` yields a row pointer retained in `m21FA.c`'s static `colorEntry`. `win_offsets` is read/written by indexed `Rect` copies and passed as the destination of the resource bulk copy. The adjacent EMS root is dereferenced for cache-row access; the raster slot is indirect-called; the clip head is copied into and restored from allocated stack nodes. These concrete escapes are in the report's per-line inventory.

## Registry and lifetime boundaries

The report records each target's registered base names and every registered symbol whose address lies strictly inside the source candidate extent. Alias names at the same base are recorded separately from interior views; following symbols and address gaps are not used to set sizes. The three resource arrays are checked over their measured minimum prefixes, but these views do not turn those minima into accepted exact extents.

`win_num*` values are loaded during window initialization and used for the process lifetime. `win_drawHooks` is reset during that initialization and can be replaced by hook registration. `win_offsets` is reset, resource-seeded, then updated as windows open/close. `win_colors` is resource-loaded and read by color lookup/drawing. The EMS table root exists after EMS initialization, points to an allocation sized from available EMS pages, and is used by the page-cache loop. The raster callback slot is set by display-driver selection. The clip handle head tracks push/pop nodes with a separate depth check. No array count or numeric value bound follows from these lifetimes.

Machine-readable pins, source hits/escapes, registry views, compiler OMF facts, and all RTLink cases are in `../../build/workers/dos_v17_fresh/uires/UIRES.V17.JSON`. The probe source is `ui-resource-owner-probe-v17.py`.

Fresh run pins and positive/negative compiler/RTLink results are recorded in `../../build/workers/dos_v17_fresh/uires/UIRES.V17.JSON`.

## v17 durable candidate evidence

The durable provider is `providers/ui-resource-state.c`; the adapted guarded
probe is `ui-resource-owner-probe-v17.py`. Its fresh report is
`../../build/workers/dos_v17_fresh/uires/UIRES.V17.JSON` and contains the
recomputed 127-canonical plus 29-effective (156-unique) source inventory,
registry views, compiler/runtime pins, provider and probe hashes, and raw case
logs. The requested/effective compiler flags are `/AL /Os /Gs` and
`/AL /Os /Gs /EM`.

For both RTLink 4.00 and 6.10, `typed_startup_and_roundtrip` returned `PASS`,
`wrong_scalar_width_guard` returned `FAIL`, and
`initialized_owner_zero_startup_guard` returned `FAIL`. Those expected and
actual classes are retained per case rather than reduced to a pass summary.
Every case also requires a generated EXE and map, all six owner names in the
map, and no unresolved linker diagnostics. These remain isolated test-owned
fixtures; no game objects or stubs are linked. The report keeps
`root_reviewed=false` and `admitted=false`, and the unresolved resource-array
and `win_handles` limits above remain open.
