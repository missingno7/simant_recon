# Graphics selector/mask candidate — not admitted

The [formula provider](providers/graphics-formulas.c) is research only and is not
listed in any SOURCE_ONLY_DOS binding packet. The build retains all 113 bytes of
historical data-disposition debt.

Source operations support eight high-bit-first plane selectors and ten final-byte
masks: eight packed-byte width residues and two packed-nibble width parities.
The [self-contained probe](graphics-formula-probe.py) compiles exactly 18 bytes,
with publics at offsets 0, 8 and 16. Both RTLink versions pass all phase/residue/
parity and symbolic SS reads under real MSC startup, and detect reversed selector,
low-nibble mask and `_DATA`-frame contrasts under shifted DGROUP.

No direct writes or initialized source pointer tables naming these intervals were
found. The inventory also retains 229 dynamic MOVS-family sites. Their destination
reachability is not closed, so absence of indirect aliases has not been proved.
Original initializer/TU ownership is unclaimed. Further source/alias research is
required before either functional ownership or debt resolution can be admitted.

The reproducible detailed report stays in ignored
`build/workers/dos_graphics_formula_probe/report.json`; this note preserves the
candidate and its blocker, not a frozen storage assumption.
