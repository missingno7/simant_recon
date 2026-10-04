# v35 append-only clarification

The original loaded value is known: the locked original image contains zero at all five FAR_BSS addresses when loaded. This is an observed image-initial value; it does not establish the value at first game read or later. It is not evidence of original designer intent and not a permanent-zero claim. The proposed C objects remain mutable.

The synthetic boundary guard only verifies its own test policy: an exact two-byte raw view at offset zero is accepted, and an offset-one/two-byte view is rejected before it dereferences memory. It does not prove any historical object's extent. The prospective two-byte size is supported by the natural signed `int far` declarations and the fresh MSC 6.00AX COMDEF records. The source-wide target-typed accesses and v34's concrete provider/index/frame/SaveRec alias frontiers provide separate no-overlap evidence; they do not convert a candidate extent into historical COMDEF identity.

The normalized storage contract is root-false. Each target is modeled as a mutable, uninitialized source-state `int far` whose isolated RTLink startup value is zero. The unchanged layout gates still apply to any future placement or admission. The original defining TU and historical extent remain open.

For `fd_50F6_0FB6` and `fd_50F6_0FFA`, `RandWorld`, S22 `SetAlarmDropState`, and the two `SetMapPlane*` callers pass the words as right/bottom endpoints to active `InvalEuMap`. It clamps to 127/63 and iterates inclusively; zero bounds can reduce the request to cell `(0,0)` when the viewport predicate permits. No setup writer was found. The image-initial values are zero, but the value at first use, later runtime values, and intended map size remain unknown. This is a concrete behavior/setup gap, not a basis to relabel the observed uses as arbitrary offsets.

Full-game alias clobber closure, first-use order, and lifetime remain open under the existing gates. Current pinned game C sources and the reviewed original-frame sweep found no concrete target writer; this does not assert that the words remain zero for the full game lifetime.
