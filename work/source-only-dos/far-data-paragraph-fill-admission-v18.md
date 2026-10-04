# Functional FAR_DATA paragraph-fill review

Root accepts the twelve-byte `far_data` disposition as generated segment
alignment for the standalone source build. No C object owns these twelve bytes.
The historical 113-byte ledger and original-byte identity remain unchanged.

The accepted root:1F80 source has one 100-byte paragraph-aligned FAR_DATA
contribution. Its independent manifest-basename recompilation matches the
accepted object. The historical source placement ends at 50F54 and the next
FAR_BSS paragraph starts at 50F60. The source/range-map/SEGDEF evidence therefore
accounts for the complete twelve-byte gap, without inferring a hidden field
from zero contents. The generated U094 object is checked again for the same
100-byte, paragraph-aligned, public FAR_DATA contribution before discharge.

Natural MSC fixtures contrast a 100-byte static far array with a 112-byte array,
each followed by the same one-byte far communal. Both independently selected
RTLink profiles insert twelve bytes after the first extent and zero after the
second while preserving the following FAR_BSS start. All four links have clean
diagnostics, asserted map ranges and actual nonempty EXEs. No original bytes,
patched objects or padding owner enter these controls.

This is a source-built alignment explanation, not proof of the exact historical
linker release or an instruction to force the original numerical layout. The
selected-linker and runtime component identities must match the reviewed
controls. The raw v2 candidate and executed probe stay unchanged; the admitted
contract separately records this decision. The three common-tail overlap bytes
are explicitly outside this admission and remain debt.
