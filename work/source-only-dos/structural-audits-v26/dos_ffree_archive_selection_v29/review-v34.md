# `__ffree` archive-selection probe v29

This is a root-false, unadmitted test of a small game allocator symbol contract. It uses three test-authored C sources, the pinned MSC 6.00AX compiler, stock `LLIBCR`/`LIBH`, and RTLink 4.00/6.10. No original executable or game object is an input; produced images were not executed.

The natural C case defines far `malloc`, `_ffree`, and `free`; `free` calls `_ffree`, and `main` returns without allocating. The emitted OMF confirms `__ffree` as both a `PUBDEF` and `EXTDEF` in the same object, with a self-relative code fixup to that external. The stock `LLIBCR(fmalloc.asm)` member also has a `PUBDEF __ffree` (and `__fmalloc`), so the collision is present at actual OMF symbol records, not inferred from source spelling.

With that object, RTLink 4.00 selects `fmalloc.asm`, reports `wrt0011` for duplicate `__ffree`, and maps the visible `__ffree` to the game object. RTLink 6.10 does not select `fmalloc.asm`, emits no duplicate warning, and maps `__ffree` to that same game object. Removing `main` reproduces the selection/warning contrast; those no-main trials separately retain an expected unresolved `_main` diagnostic and are not successful links.

The unique-name control has only a static `game_ffree_inner` and public `game_ffree`/`game_free`. It defines no `__ffree`, yet both RTLinks still select `fmalloc.asm` and map `__ffree` to the library. Thus the probe demonstrates the duplicate-public condition and the RTLink version contrast, but does not establish that the same-module `__ffree` self-reference is the sole archive-extraction trigger in every CRT startup configuration.

The symbolic-alias case declares/calls `_ffree`, defines a distinct `_game_ffree`, and links `DEFINE __ffree = _game_ffree`. Both linkers still select `fmalloc.asm`; each emits `wrt0053` for the DEFINE, while the map assigns `__ffree` to the game implementation. This does not establish a safe way to avoid archive lookup or justify a production source rename.

All sources, object PUBDEF/EXTDEF/fixup records, selected archive-member OMF audits, linker scripts, raw LINK logs, maps, images, compiler/linker/runner/runtime pins are in the receipt and [runs-v34](runs-v34). Reproduce with [probe_ffree_archive_selection_v29.py](probe_ffree_archive_selection_v29.py); inspect [receipt-v34.json](receipt-v34.json). Functional `__fheap` debt remains open.
