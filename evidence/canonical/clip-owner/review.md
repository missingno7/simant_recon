# Clip rectangle destination: bounded owner before the first Punt

The canonical clip destination `fd_50F6_3C14` has one 256-record far owner
(2,048 bytes, eight bytes per `struct Rect`). This closes the last undefined
storage import for every execution prefix before the first `Punt` entry.
It does not resolve `graphics-computed-copy-layout`: list generation can still
overrun the separate 2,048-byte heap temporary before its overflow check, and
the reachability of such counts in shipped play remains unproved.

## Writers

The complete canonical census finds `fd_50F6_3C14` only in `root:1E57` and the
new provider. Eight functions write it, each with one whole sentinel-terminated
list:

* `clip_SubInclude`, `f_1E57_08F5`, `clip_SubExclude` and `f_1E57_0C2D` check
  `n >= 256` and call `Punt` before copying `(n + 1) * 8` bytes. Their
  no-current-clip branches copy one rectangle, or the caller list of
  `f_1E57_08F5`. Its only caller, `f_0250_5058`, passes two rectangles and a
  sentinel.
* `f_1E57_0FDC` writes one in-mode intersection: at most one rectangle and its
  sentinel.
* `clip_SetWin`, `f_1E57_0296` and `clip_Pop` copy an existing list through its
  sentinel. Window clip handles and the active clip output are stored only by
  `f_1E57_038E`, after its C097/C098/C099 checks; its first window intersects
  the one-record screen list. `clip_Push` snapshots the current list.

The current list pointer `g_5AAC` is assigned only to null, the screen list,
the owner base or, transiently inside these loops, a bounded handle list. The
cursor callback and menu code save and restore it; display drivers and the
other C users only read it. No assembly or C reader stores through it.
Therefore, by induction over writes, every list reachable as a copy source or
in the owner has at most 255 rectangles plus its sentinel unless `Punt` has
already been entered. The owner is zero-initialized and every reader follows
a whole-list write or reads the separately owned screen list.

## Original controls

`replay.py` executes unchanged original `clip_SubExclude`, its rectangle
helpers and `Punt`. Heap services and far memcpy are explicit fixture
boundaries; only scalar observations are published.

* 255 disjoint input rectangles: the call completes and copies exactly 2,048
  bytes, sentinel at record 255; bytes after the owner are unchanged.
* 256 rectangles with guard zero: the heap temporary is overrun first, then
  execution reaches `Punt("CL074...")` before any destination write.
* 256 rectangles with guard one: original `Punt` returns and the caller copies
  2,056 bytes, eight beyond the owner. This returning-`Punt` continuation is
  the retained negative contrast and is outside the admitted domain, as for the
  sample free list and database slot owners.

`Punt`'s guard is a private static set only by `Punt`; with guard zero it ends
in `o15_384C_0152`, which calls `exit`. The owner claims no historical defining
unit, communal order, placement, the 2,708-byte historical gap to the next
recovered symbol, or any behavior after a fatal diagnostic.

## Native consequence

The native build previously replaced the array with a host pointer, injected
reservations and introduced new allocation-failure branches. It now compiles
the canonical 256-record owner directly, and `native-clip-allocation-policy`
is retired with its temporary rewrite.

```powershell
python evidence/canonical/clip-owner/replay.py
python -m unittest tests.test_clip_owner
```
