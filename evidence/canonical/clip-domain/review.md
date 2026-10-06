# Clip generation: the window-count premise is insufficient

The original clipping caller can write the trailing sentinel beyond its
256-record temporary before its overflow diagnostic. This is proved for
synthetic geometry, not as a reachable shipped-game failure. The storage import
`_fd_50F6_3C14` and `graphics-computed-copy-layout` gate remain unresolved.

`f_1D8E_003F` can split one rectangle into four; `f_1D8E_02BD` applies that
operation to every input list item. A stack of at most 31 windows therefore
does not imply fewer than 256 visible rectangles. Starting with a 32-by-32
background, 15 vertical and 15 horizontal one-unit bars leave 16-by-16 cells.
The bars and background occupy exactly 31 stack entries plus the sentinel.
Their coexistence through actual window-open/resize/resource paths is unproved.

`replay.py` executes the unchanged original `f_1E57_038E` and its rectangle
helpers. Window rectangle lookup, heap services and far memcpy are explicit
fixture boundaries. Both scratch allocation requests come from original
instructions and are exactly 2048 bytes. Test memory includes a 16-byte guard
after each allocation; that guard is not a proposed production owner.

With 14 bars per axis (29 windows), the caller completes and stores 225 disjoint
visible rectangles plus sentinel in the background's 1808-byte clip list.
Both scratch guards retain their marker bytes. With 15 bars per axis (31
windows), the helper emits 256 disjoint rectangles and writes sentinel word
8000 at temporary displacement 2050, from original PC `1D8E:02AD`. The observed
CPU write precedes entry to `Punt("C097: Clip overflow %d", 256)`. Execution
stops at that entry: the result needs no assumption that Punt returns, and
claims no later copy, actual allocator corruption or fatal continuation.

The neighboring positive control distinguishes this threshold from a fixture
that always crosses the buffer. Pairwise non-overlap and total visible area
are checked in both cases. Reviewed whole-module source pins, current inventory
pins and the locked original executable are checked before execution. Changed
source, changed oracle bytes or stale inventory are rejected by permanent tests.

The 2048-byte temporary is not allocation authority for `fd_50F6_3C14`.
`clip_SubExclude`, `f_1E57_08F5` and `f_1E57_0C2D` also generate their lists
before checking counts; reset/restore paths copy through the sentinel.
Closure still needs a complete supported geometry/producer bound before each
emission and the destination's initialization, lifetime and ownership contract.
The active-window bound and post-generation diagnostics alone supply neither.

Run `python evidence/canonical/clip-domain/replay.py`. The default output rotates
through `tools/workspace.py` into `to_delete/`; an explicit `--out` must be fresh
and beneath `build/`. The runner writes only a disposable receipt. Its controls
are maintained by `tests/test_clip_domain.py`; no game source or historical
object/image bytes are produced or changed.
