# PTR-1 pointer-form controls: map cursor and InvertPatch

Work stayed in `build/workers/ptr_map/`. The frozen whole-module source for S13 is
`base.c` (SHA-256 `1ace9a2985696a7c254c9cfcfafc504be9126f07c47672c6bf79e3e2a570e801`); the S12 base is `cursor-base.c`
(SHA-256 `daa607847c4c0364358a7b57d3f790dd9981e284bf2cedd01fa1fb3ac4df918a`). Canonical sources, manifest, evidence and promotion
journal were not edited.

The S13 listing at `S13:384C:128D` shows both resolution loops using a common `i * 4`
offset to read adjacent words from `g_2A42` and write the local `pts` members at
`BP + SI - 0x16` and `BP + SI - 0x14`; the call passes the array base with `LEA`.
Prior residue controls covered coordinate algebra, local stages, products, registers,
and prototypes. These new controls tested a used `struct Pt *point` set by `pts + i`
or `&pts[i]`, then a second form with direct `(pts + i)->field` and
`(&pts[i])->field` writes. Horizontal/vertical store order varied independently in
the two loops.

The S12 control used the local Win16 `DrawMapCursor` semantic source, whose formulas
scale `MapPnt.y` and `MapPnt.x` by `mapYsize` and `mapXsize`. Its DOS listing reads the
corresponding far scale words at `50F6:050A` and `50F6:0508`. Four controls assigned a
real `int far *scale` by `fd_50F6_0508 + index` or `&fd_50F6_0508[index]` separately for
the vertical and horizontal computations.

Results:

- `results.json` (S13 used member pointer): 16 variants; 16 compiled; 0 target exact; 16 preserve all accepted peers/data; 4 distinct emitted bodies; base score [1, 61, 221, 1], base length 260.
- `direct-results.json` (S13 direct member pointer): 16 variants; 16 compiled; 0 target exact; 16 preserve all accepted peers/data; 4 distinct emitted bodies; base score [1, 61, 221, 1], base length 260.
- `cursor-results.json` (S12 far scale pointer): 4 variants; 4 compiled; 0 target exact; 4 preserve all accepted peers/data; 1 distinct emitted bodies; base score [1, 21, 128, 5], base length 210.
- Total new variants: **36 / 40**. No variant matched, so
  `promote.py --verify-only` was not applicable.
- Every generated module variant compiled and preserved every other accepted claim and
  private data placement in its module. Changing only `pts + i` to `&pts[i]` emitted the
  same body in the used-pointer S13 controls; the direct S13 member forms also emitted
  the same body for both address expressions. Reversing stores changed the S13 body but
  did not close its residue. All four S12 pointer-initializer combinations emitted the
  same body.
- `search-invert.log` and `search-cursor.log` retain target-only aligned diagnostics for
  each frozen base and a representative pointer variant. Both searches returned 1
  because neither target was exact. The S13 base remains 260 bytes for the 261-byte
  target and has a five-vs-five but mismatched relocation set. Failed matches are
  compiler diagnostics only; they do not establish compiler exclusion.

Generators: `run_invert.py`, `run_invert_direct.py`, and `run_cursor.py`. `variants.json`,
`direct-variants.json`, and `cursor-variants.json` retain source hashes and factor settings;
`hashes.json` records SHA-256 for every generator, frozen source, generated variant,
gate result, search transcript, and this report.
