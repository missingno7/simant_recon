# Functional control, resource and terrain storage review

Root accepts the types and exact extents of 20 source-owned FAR_BSS objects
(82 bytes). The definitions are generated-build providers, with no claim about
the original COMDEF translation unit, ordering, padding or numerical addresses.
This review neither freezes missing layout assumptions nor changes canonical
source, the historical manifest or the 113-byte historical debt inventory.

The control family has two six-byte `TriLevel` records, four unsigned words,
three four-byte signed points, two twelve-byte `TriPoints` records and one
four-byte signed slope. The field ordering and arithmetic match root:0798.
`initControls` loads the knob dimensions, copies three default words to each
level and calls the two change paths; `InitTriVars` and `SetTriLatPoint` produce
the geometry. Cross-module unsigned-word array and SaveRec `{2,3}` views of the
level records agree on the same six bytes. Registered raw names are exact-base
views; there are no registered interior objects within these extents. Adjacent
flags and animation handles remain separate. The isolated runtime checks real
MSC FAR_BSS zero-fill and struct/array/save views. The shortened level and
initialized knob contrasts are compiler controls, not runtime negatives.

The UI family has three signed two-byte resource counts and three four-byte
pointer slots. Root:19DC defines the EMS pointer-to-pointer ABI with six-byte
`EmsSlot` payload rows. Root:2662 supplies the raster callback's four-argument
ABI; root:205F installs the existing driver procedures. Root:1E57 owns the clip
push/pop algorithm that copies the handle head. Resource `(0x80,0)` writes the
three count words. These are scalar owners, not allocations of the resource
payloads. Their raw aliases and all source escapes are preserved.
`win_handles`, `win_colors`, `win_drawHooks` and `win_offsets` stay unresolved:
resource counts and initialized prefixes do not prove their full extents.

`Barrier` and `TERRAINset` are signed two-byte far words. Matching complete
declarations, concrete scalar writes/reads and SaveRec `{2,1}` spans establish
their extents independently of neighboring addresses. `initStuff` reaches the
Barrier producer, and `LoadTiles` sets terrain selection before rebuilding the
overlay. Original raw aliases are exact-base views. The unsigned-view contrast
is retained as `TYPE_NEGATIVE_UNSIGNED_VIEW`, rather than mislabeled `FAIL`.
`DROPdir` and `Tindex` remain outside this admission.

The source reviews cover all 127 canonical modules and 29 effective strict
sources, including source-defined producers, reads/writes, escapes, saved spans
and registry views. Both pinned RTLink profiles independently allocate the
typed owners and execute test-owned consumers with the real MSC CRT. Source
type guards and fresh OMF guards are complementary: OMF alone cannot prove
signedness, aggregate fields or pointer depth. No original executable is a
compiler/linker input, and no game stub or original-byte fallback is supplied.

Unchecked resource counts, restored game values, geometry divisions, payload
lifetimes, and universal producer ordering remain properties of the existing
algorithms. This admission does not assert those broader domains are safe or
that full-game execution is complete. It establishes the actual scalar/record
storage and views needed by those algorithms. The wider numeric/frame,
computed-copy, fatal-path and array-owner gates remain separately enforced.
