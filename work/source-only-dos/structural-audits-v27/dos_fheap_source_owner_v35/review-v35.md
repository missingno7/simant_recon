# v35 `__fheap` / historical DGROUP:79F0 review

Status: `KNOWN_PINNED_RUNTIME_DATA_OWNER; HISTORICAL_DGROUP_79F0_RANGE_OPEN`. This is unadmitted evidence (`root_reviewed: false`, `admitted: false`), scoped to functional ownership and the accepted source/object graph. It does not close the historical 14-byte span or prove an original address/order.

The installed, pinned `LLIBCR.LIB` has one `__fheap` provider: member `fdata.asm` (module 51), with a 14-byte word-aligned `_DATA` segment and a public at offset 0. Its initialized bytes are `0000000000000000000000000300`. That is a pinned stock-runtime owner, not a new game C owner. The installed MSC `STARTUP/heap.inc` independently defines a 14-byte heap-list descriptor as three four-byte far pointers followed by a two-byte flags word; `_HEAP_MODIFY | _HEAP_FREE` is 3. This is strong layout/value corroboration, but the available heap include and public headers do not directly declare `__fheap`, so the report does not claim a direct C-source binding or infer the original object’s address.

A clean, source-built minimal MSC `main` with no heap API import links under RTLink 4.00 and 6.10. Both maps resolve `__fheap` to `fdata.asm`; their archive logs expose `dos\\stdalloc.asm -> malloc.asm -> fmalloc.asm -> fdata.asm`, where `fmalloc.asm` imports `__fheap`. The separately controlled source-owned `_malloc` fixture also selects `fmalloc.asm` and `fdata.asm` on both linkers even though `malloc.asm` is absent. In that contrast `fmalloc.asm` itself imports `__fheap`, but no other selected member is a direct `__fheap` importer; the archive-extraction trigger is therefore unresolved. The fixture is only a symbol-provider link control, not a recovered allocator. Neither fixture was executed.

The pinned current build report supplies 182 accepted source objects. None imports the MSC far-heap API; the accepted selected-runtime manifest likewise has no direct far-heap API import and does not select `fdata.asm`. The pinned runtime archive census finds seven `__fheap`-importing members, all outside that selected-runtime set. A bounded source/OMF census found no source literal for numeric `79F0`, no object symbol containing `79F0`, no OMF segment payload word pattern for that value, and no accepted game-object `__fheap` fixup. The scan does not inspect original executable bytes, treat unrelocated byte coincidences as references, or prove a completed whole-application runtime path.

As cross-evidence only, the preserved v28 RTLink 6.10 expected-failure partial map selects `fdata.asm` and has no selected member importing `__fheap`; that run used 178 objects, not this v35 182-object set. It was not relinked here and establishes no historical address or completed application behavior.

Disposition: account for the functional `__fheap` public as the known, pinned stock runtime data object; do not invent a game-owned duplicate. Keep the historical DGROUP:79F0 address, byte identity, ordering, and any unobserved initializer behavior open. The full application link remains incomplete. No original executable was used as compiler input, no linked image was executed, and no production, canonical, ledger, or Git files were changed.

Reproduce from the repository root with:

```powershell
python build/workers/dos_fheap_source_owner_v35/probe_fheap_source_owner_v35.py
```

The machine-readable raw receipt, input/tool pins, fixture sources/objects, link scripts, logs, maps, and unexecuted outputs are under `build/workers/dos_fheap_source_owner_v35/`.
