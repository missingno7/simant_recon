# Source-owned S03 code addresses

Parent review, 2026-10-05: accepted through normal whole-TU verification and
promotion. No function status changes and no new storage declaration.

`S03:3126` owns the 320-byte `linebuf` at its code contribution's start. Four
LEAs in `o03_3126_0C1E` formerly encoded literal offset zero. `S03:3258` owns
the 1024-byte `xlat_tabs`, also at its contribution's start. Each of
`o03_3258_0690` and `o03_3258_0F04` uses its base and byte offsets 512, 256 and
768. The old literals were 12, 524, 268 and 780, incorporating the historical
contribution's paragraph-frame origin. Canonical assembly now names these
already-owned objects directly.

Fresh historical verification preserves all 39 exact functions, complete code
extents (4824/6055 bytes), code-data extents (320/1024 bytes), the 250 private
DATA bytes, public order, and relocation ordering. All existing fixups remain
identical in order. The only new object references are twelve ordinary
same-code-segment offset16 fixups. No algorithm, branch, memory extent, object
bytes or final image is patched.

An independent reviewer tested complete objects with real RTLink/Plus 4.00 and
6.10. The parent then ran the installed current-source reproducer independently.
All twelve cases meet their expected outcomes. At the historical offsets both
forms pass. At table origin 8, the old form has eight wrong LEA operands. Moving
both owners to offsets 32/40 gives twelve wrong old operands. Symbolic references
pass in every placement. DOSBox-X executes only the fixture checker, which reads
the actual linked displacement fields; it executes no game procedure or provider.

`src/program.json` records each owner extent and operand's own-object offset.
Promotion, canonical publication, historical validation and DOS compilation
require the corresponding OMF frame/target/addend. The regression test verifies
that whole modules restored to the old literal spelling still match the original
historical placement but fail this independent-address contract.

Full `tools/validate.py` passed, including 48 compiler probes and the runtime
proofs. DOS preflight compiled/verified 190 units, checked all 63 storage units
and these twelve references, and correctly refused linking with twelve imports
and ten semantic gates outstanding. No original-byte fallback is used.

The broader numeric-address/segment-frame audit remains open. This acceptance
closes these two proven source-owned address relationships; it does not establish
an independently linked or executed DOS game. `summary.json` and `receipt.json`
retain the parent's run, with current source and runner pins.
