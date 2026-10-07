# Canonical DOS storage spans in the native projection

PORT_INTRODUCED: original and canonical DOS load the six option words as
`[0,1,1,1,1,0]`; split native DATA/BSS owners previously exposed six zeros.
The origin functions are byte-exact canonical C, including SaveGame/LoadGame
and the option consumers. S14 declaration context has a separate layout-inferred
tag. The compact [proof](proof.json) retains the three-executable loaded-data
control; it does not claim every gameplay path was exercised.

The single [contract](../../../portable/semantic-spans.json) lists complete
canonical owners, positions measured by canonical MAP/OMF, declaration/COMDEF
extents, consumers, mechanisms and evidence. All 307 SaveRec entries are tiled
independently. Exactly two cross owners: record 28 is 0164[32]+0184[160]; record
100 consumes 12 bytes from the 14-byte options group
07A8[2]+07AA[4]+07AE[2]+07B0[2]+07B2[4]. The final owner's unconsumed two bytes
remain owned. No gap supplies an extent, padding, guessed owner or initializer.

The [lowering](../../../portable/canonical_native_abi/semantic_spans.py) moves
participating definitions with their canonical initializers into packed native
groups and exports aliases with the original canonical names. Every field has
offsetof/sizeof assertions. Fixed and dynamic indexes, pointer arithmetic and
SaveRec I/O expressions remain intact. The old m00DF audio view rewrite is removed.
Stale/new consumers, missing members, gaps and undeclared SaveRec/literal crossings
fail the build before compilation.

`python portable/tests/acceptance/check_span_layout.py --oracle-root <DOS-root>`
re-resolves all 739 catalog addresses against 1,344 canonical placements and
checks available COMDEF extents. `python tests/test_semantic_spans.py` runs eight
permanent controls, including removal/assert failures and real block-I/O round
trips with split-storage negatives. All 33 literal crossings, including the 29
non-audio siblings, read DOS-equal values in compiled controls. Dynamic writes
at indices 0..5 reach their canonical member aliases. Record 100's round trip
also preserves the two bytes outside its consumed extent.

Original and canonical DOS saves are equal in all 307 records. New native records
28 and 100 match both. The earlier and new native files differ only in record
100's four repaired bytes; 65 records / 8,363 bytes still differ from DOS. The final
executable reproduces the same actual save hash and loaded option vector. Raw
records 28/100 also match canonical DOS at 14/22/40/49 seconds. Native Save/Load
through GDB succeeds with all 307 reads. Equal-time state comparisons remain
diagnostic, including the first 14-second divergence and 113/220=30-versus-0.

Plain mouse-driven VGA and Save repeatedly fault after the 11.2-second mouse-down.
Late attach finds invalid text pointer 0xa7196054 in _font_StringWidth through
f_24AB_0329, win_StringSize, f_15D9_0006 and o12_384C_0B76. S12 defines
fd_55B3_299A as long (native int32_t); root15D9 writes char far* (native 64-bit
pointer), while S12/S13 read its low 32 bits. DOS long/far-pointer views are both
32 bits. This separate native pointer-owner width defect remains open. Startup-GDB
runs pass; address placement/timing is an explanatory hypothesis. An old baseline
VGA control passes. No fresh same-step original/canonical mouse replay is claimed.

Whole-game acceptance remains FAIL. Heap adjacency, unproved dynamic bounds,
within-owner wider views and twelve existing supported-domain exclusions remain
separate. This closure introduces no per-site pointer workaround.
