# Window callback and rectangle array domain

The admitted handle-ID and palette proofs now resolve the specified
`window-index-resource-cross-owner-layout` contract in the existing supported
domain. The canonical 45-entry callback and rectangle owners remain unchanged.
This is an array-adjacency result, not a theorem that all low-byte object indices,
heap accesses, graphics operations or error continuations are safe.

Every nominal incoming window high byte is 0..33 under the complete
[handle-ID/lifetime proof](handle-review.md). This same value indexes callbacks
and saved rectangles. Fixed initialization additionally covers indices 0..44:
the callback clear writes 180 bytes, rectangle initialization writes 45 cells,
and the optional rectangle copy is 320 bytes within its 360-byte owner.
The original literal callback registrations select windows 0, 1, 18, 19, 21
and 25. None of these accesses reaches callback 45 or rectangle 45.

The separate [palette proof](palette-review.md) supplies its own object-pointer
and selection argument. The shipped count is 16, its copy is 96 bytes, and
selected row 63 is excluded in the reviewed nominal domain. Window count 34
also bounds preload and the purge loop within its 40-byte resource/local copy.
The pre-lock handle store is already included in the 34-cell ownership proof;
no later error is used to justify its index.

There are 22 hook/rectangle identifier occurrences across four consumer TUs
and the owner: two definitions, five externs and fifteen expressions. The
expressions are LoadWindow test/read/store; fixed initialization/copy; Open,
Close and Unlock persistence; S26 movement; hook registration; and two hook
tests/calls during drawing. Their only base uses are the bounded bulk operations.
There is no additional escaping cell/base. Registry aliases `fd_50F6_47DE` and
`fd_50F6_4892` select the same owners. Eleven count-scalar references contain
only the two resource-loader assignments plus definitions, externs and reads.

`array_gate_probe.py` binds the entire source/module/alias/registry inventory,
replays the existing handle census and palette proof, and records the combined
33-reference storage/count census. All 307 original SaveRec descriptors match
source and avoid both arrays and both count scalars. New direct writers, aliases,
address escapes, macro/ASM references and overlapping saves are rejected by
permanent regression controls.

Original `win_SetWinDrawHook` controls use its actual AX argument and four-byte
callee stack cleanup. Windows 0 and 33 write within the callback owner.
Fabricated windows 45 and -1 write at offsets 180 and -4 respectively. Those
negative effects remain explicit: the proof excludes their incoming indices;
it does not add checks, padding or overlapping owners. Existing palette-row-63,
foreign descriptor, YardMode-5 and returning-error contrasts also remain.

The K: drive example still chooses invalid object 21 in valid window 22. Its
actual first-fatal checked lookup exits; guarded returning continuation remains
a separate counterexample. Neither implies callback 45 or rectangle 45.
The high-byte proof does not make that low-byte object valid.

Remaining obligations retain their own authorities: `graphics-computed-copy-layout`
covers the unbounded clipping copies and possible physical aliases;
`map-viewport-grid-layout` covers dynamic dimensions and resize behavior.
The window review and closure graph retain unchecked object/proxy effects.
Native object/allocation, omitted-word, heap-history and index-adjacency contracts
remain open in `portable/platform.json`. No general exclusion of foreign computed
writes follows from this array-domain result.

Run `python evidence/canonical/window-domain/array_gate_probe.py` and
`python -m unittest discover -s tests -p test_supported_dispatch_domains.py`.
There are no new source owners or native adapters to retain; exploratory packets
are retired after integration.
