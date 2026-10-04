# Delay-word source addendum v33

**Status: `ROOT_REVIEW_PENDING_UNADMITTED`; v32 remains preserved unchanged.** This source-only addendum narrows the interpretation of `fd_50F6_46D0` at `50F6:46D0`.

The natural signed-word type remains grounded by `f_208F_04D0`, which stores its signed `int delay` parameter, and `f_208F_04EE`, which passes the word by value to `WaitedEnough(..., int delay)`. This supports the word view at the access site; it does not establish a complete storage owner or runtime lifetime.

In the 156 pinned canonical plus strict-effective sources, `fd_50F6_46BC[]` is an unsized `int far` title-length view based at `50F6:46BC`; element 10 lands at `46D0`. `fd_50F6_46A8[]` is an unsized `int far` x-position view based at `50F6:46A8`; element 20 also lands at `46D0`. The registry independently records those bases and the word at `46D0`. The bases differ by ten `int` elements, so `fd_50F6_46A8[k+10]` aliases `fd_50F6_46BC[k]` wherever both indexes are accessed; their unsized declarations provide no complete extent.

`f_1FD2_0663` writes both arrays while walking `g_6054->titles` until a null pointer. `MenuData.titles` has no count field in the source type, and the writer checks no cap. Its first loop writes `fd_50F6_46BC[i]`; its second loop resets `i` and writes `fd_50F6_46A8[i]`. A resource with at least 11 non-null titles reaches both the first array overlap (`x[10]` over `length[0]`) and the title-length index 10; one with at least 21 reaches x-position index 20. The count is recorded after the first loop, so it does not bound that write. The S17 sentinel walk adds a further unsized reader view; the strict-effective menu procedure also reads both arrays through `curMenu`.

These array aliases show that v32’s scalar-focused references did not prove complete writer closure or absence of clobber. Historical ownership, game startup value, lifetime safety, and resource bounds remain open. Keep the candidate source-functional and unadmitted, and leave the wider menu resource/layout audit open. The adjacent `fd_50F6_46D2` pointer and fontHandles/table storage remain excluded.

Hashes for the frozen v32 candidate/runtime/source review and the source files/registries reviewed here are in `source-addendum-v33.json`. No new compilation, emulation, or probe was run.
