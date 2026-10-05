# Current S03 owned-address proof

`replay.py` reads the canonical complete `src/S03/m3126.asm` and
`src/S03/m3258.asm` modules. It derives test-owned negative whole-module copies
by replacing exactly four `linebuf` LEAs and eight `xlat_tabs` LEAs with their
reviewed historical literals. It requires those symbolic instructions to exist
in the canonical sources and records each replacement. No historical worker
snapshot, old Git checkout, original executable, or retired generator is used.

Run from any working directory after installation:

```powershell
python D:\Prog\simant_recon\evidence\canonical\s03-owned-addresses\replay.py --out build/s03-address-proof-fresh
```

Relative output paths are resolved against the repository root, located by
`layout/toolchain.json`. `--out` must be absent or an empty directory beneath
`build/`; omitting it creates a fresh directory beneath `build/proofs/`.
Prior receipts are preserved. The runner does not write canonical sources,
inventory, layout, or this evidence directory.

The current hash-pinned MASM 5.10, RTLink/Plus 4.00 and 6.10, MS-DOS Player,
and DOSBox-X prerequisites come from `layout/toolchain.json` and current
`tools/compiler.py`. Complete positive and negative module objects retain the
same declarations, public order, lengths, all other code/data bytes, and ordered
existing fixups; the positives add four and eight own-code offset fixups.

Both real linkers link those complete objects with test-owned boundary providers
and an operand checker. The checker executes in DOSBox-X and reads the twelve
actual linked LEA displacement fields. It executes no game procedure or boundary
stub. Three controlled placements give these expected results under each linker:

| Line-buffer/table offsets in their linked paragraph frames | Historical literals | Canonical symbolic references |
|---|---|---|
| 0 / 8 | 8 incorrect operands | Pass |
| 0 / 12 | Pass | Pass |
| 32 / 40 | 12 incorrect operands | Pass |

Four test prefix bytes make the table offset 12 because the preceding complete
4824-byte S03A contribution leaves S03C's paragraph-frame offset at 8. The last
case puts a 32-byte test contribution before each module. Maps independently
confirm actual segment starts and offsets.

`summary.json` is the compact receipt. It pins the detailed `receipt.json`, the
runner, canonical inputs, staged whole sources, and negative recipes. The detailed
receipt additionally pins the current compiler/parser, toolchain configuration,
tools, objects, link inputs, maps, executables, and runtime logs, and records all
twelve linked operands in each of twelve cases.

This proof covers these two source-owned code-address relationships. It does not
establish a standalone DOS game link or game execution, prove external storage
ownership, admit additional assembly, or identify SimAnt's historical linker
version. Broader reconstruction gates remain in force.
