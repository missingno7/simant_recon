# Current owned-code address proof

Run the self-contained current proof after canonical promotion:

```powershell
python evidence/canonical/owned-code-addresses/replay.py --out build/owned-code-address-proof-fresh
```

The runner finds the repository root through `layout/toolchain.json`. Relative
`--out` paths resolve against that root and must name an absent or empty directory
beneath `build/`; omitting the option creates a fresh `build/proofs/` directory.
Canonical sources, inventory, layout and evidence are read-only. All source,
object, linker and runtime outputs stay beneath the selected output directory.

It compiles five complete primary assembly TUs: S00:31AD, S01:3126, S02:3126,
S03:3126 and S03:3258. It also compiles and links the unchanged complete second
S00 contribution, S00:31AD@2AB4, under the same `S00B_TEXT` segment name. Real
maps verify the two S00 contributions remain concatenated in one frame with
their one-byte zero alignment fill.

Positive sources come directly from current canonical `src/`. Negative whole-TU
copies revert exactly twelve code-data LEAs and twelve callback OFFSET operands
to their reviewed historical literals. Existing instructions, declarations,
publics, extents, private data and ordered fixups stay identical; the positive
objects add only twenty-four own-code offset fixups. No original image, worker
snapshot, old Git checkout, generator or production overlay is needed.

The callbacks are used synchronously by `root:1D8E`'s rectangle clipper
`f_1D8E_0384`. Each callback OFFSET names the existing code target of the
wrapper's conditional branch. Existing public targets are anchored directly;
private targets use their wrapper's existing PUBDEF plus 24 bytes. The paired
SEG field must retain its own-segment `base16` fixup and actual MZ relocation.

Pinned MASM 5.10, RTLink/Plus 4.00 and 6.10, MS-DOS Player and DOSBox-X come from
the current toolchain configuration. Each real linker links whole positive and
negative objects at three controlled placements. Paragraph-aligned test prefixes
give these offsets in each linked code frame:

| Case | S00 / S01 / S02 / S03A / S03C origins | Historical negatives | Canonical positives |
|---|---|---|---|
| ZERO | 0 / 0 / 0 / 0 / 0 | 8 LEA and 5 callback failures | Pass |
| HIST | 4 / 0 / 0 / 0 / 12 | Pass | Pass |
| MOVE | 36 / 32 / 32 / 32 / 44 | 12 LEA and 12 callback failures | Pass |

The DOS checker reads actual linked instruction operands. It compares callback
SEG/OFFSET pairs and LEA offsets with the existing target PUBDEFs and reviewed
deltas. No game procedure or test provider stub is called. In each paired
fixture the complete MZ relocation set/order and every other linked code/data
byte must remain identical; there are no patched objects, images, trimmed
extents, or relocation waivers.

`summary.json` pins the detailed `receipt.json`, runner, canonical input sources,
whole staged sources and negative recipes. The detailed receipt additionally
pins toolchain/compiler/parser inputs, tools, complete objects, link inputs,
maps, executables and runtime logs, with all twenty-four typed site results in
each of twelve cases.

This proves the listed owned-code address relationships. It does not establish
a standalone DOS game link or game execution, external storage ownership,
additional assembly admission, or SimAnt's historical linker version. Broader
reconstruction gates remain in force.
