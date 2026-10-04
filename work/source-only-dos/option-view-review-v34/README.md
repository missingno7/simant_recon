# v34 initialized option-view clarification

The six-word consumer view at 3D57:07A8 is bounded independently by the six-item
menu and the six-two-byte save/load descriptor. The accepted initializer is
`[0,1,1,1,1,0]`; sound word 2 starts enabled and ProcMenu item 0x33 toggles it.

This clarifies the structural follow-up in the immutable v33 parent receipt.
All neighboring initialized declarations are within one accepted `data:3D57`
object, whose 3,162-byte far-data contribution and publics are compiler-proven.
Their adjacency is therefore independent of cross-object link order. No new
source-only layout gate or replacement storage is warranted for this view.

The following word at 07B4 already belongs to the existing four-byte 07B2 object.
Its zero initializer is known; its DOS meaning remains unknown. Win16's seven-word
initializer corroborates the values, but does not establish a seventh DOS option.
No padding, reserved-field claim, seventh option or original declaration is inferred.

The worker receipt is preserved byte-for-byte. `consumer-view-fragment.c` contains
only an explanatory extern declaration, not a whole TU or compile/search/promotion
input. Parent independently checked 19 identities, the actual current OMF segment
and publics, menu/serializer bounds and the Win16 crosscheck. `review.py` retains
its original scratch-path assumptions and is not a cold-checkout replay tool.

No source, compiler input, admission or preflight count changes: 188 TUs, 15 imports,
46 functional data bytes, 113 historical bytes, 193 aliases, 29 strict behavioral
implementations and seven registered open layout gates. Original-byte build counters
remain zero. Independent game link, execution/comparison and human acceptance are
pending; the audio count-39 schedule remains unresolved.

Run `python work/source-only-dos/option-view-review-v34/recheck.py` for read-only
preservation integrity. Later local input drift is reported separately; no old pin
is refreshed and no compile/link/runtime acceptance is claimed.
