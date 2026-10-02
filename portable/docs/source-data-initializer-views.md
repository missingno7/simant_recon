# Recovered-source DATA backing views

The native source-reuse generator now models several complete DATA extents that
were previously narrowed to the first use-site declaration. The backing type
and extent come from readable initializers in `src/data/d3D57.c` and
`src/data/d3E1D.c`; `layout/symbols.json` verifies addresses and contiguous
aliases. The generator copies each full initializer span and records the
extent basis in its provenance. It does not read original executable bytes.

The corrections preserve the 10-byte `Dx9` and `Dy9` symbols, the 9-by-8
`TurnTab`, all seven `IdealCaste` words and all 24 `ModeTabB` words. `PherMapRT`
now parses its hexadecimal `[0x800]` dimension as a 2048-byte 64-by-32 map.
Scalar module declarations for `fd_3D57_02C2`, `fd_3D57_0798`,
`fd_3D57_07C8`, and `fd_3D57_0C1A` address word zero while state retains each
complete source-backed table. Ant-list arrays retain the explicit 1001- and
501-byte DATA extents.

`fd_3D57_0164` and `fd_3D57_0184` are a single 192-byte backing: the first
32-byte initializer begins at `3D57:0164`, and the second 160-byte initializer
begins at `3D57:0184`, exactly 32 bytes later. The generated `root_m0BE8`
accesses are rewritten to rows 2 through 11 of the existing `[12][16]` byte
matrix. There is one state field; no duplicate overlapping array or casted
alias is created.

The 16-byte `fd_3D57_0B14` initializer is represented as four aligned
`struct Pt` values. `fd_3D57_0B24` retains all 18 initialized bytes in an
aligned union with an 18-byte byte view and a `struct Pt` view. The generated
S22 source uses the union's point member, avoiding a potentially unaligned
cast from a byte array. The union exists to represent source-backed storage;
it does not justify treating the 18-byte extent as a complete point array.

The setup bridge's `ideal_caste` field remains four words. It must copy exactly
those four words in both directions; the last three `IdealCaste` words belong
to recovered source DATA backing and must not be copied past the setup field.

Run `python -m unittest portable.tests.recovered.test_recover_source
portable.tests.recovered.test_source_initializer_views -v` for generator and
initializer controls. The added controls compile all 23 generated translation
units, inspect exact source-span metadata, initialize nonzero values, and
reject a deliberately shortened `Dx9` candidate. The machine-readable record
is `portable/tests/recovered/evidence/source-initializer-views.json`.

The scalar-candidate audit found a separate initializer omission: the source
scanner skipped resolved fields with no candidate dimensions before checking
their source arrays. This omitted exact-size byte-array initializers for scalar
word views, including `fd_3D57_07BE` (`uint8_t[2]` `{0xFF, 0xFF}` to an
`int16_t` scalar). The generator now applies the existing exact-byte-extent
rule to scalar candidates too. The separate `recovered_source_next2` probe
adds 35 source-backed two-byte initializers (14 nonzero), has no initializer
mismatches, and compiles all 23 selected modules plus the state support file.
Positive runtime controls check `fd_3D57_07BE == -1` and other nonzero values;
a mismatched four-byte candidate remains rejected. Full rows and hashes are in
`portable/tests/recovered/evidence/source-scalar-byte-initializers.json`.
The earlier `recovered_source_next` profile is preserved unchanged.

These tests establish source-backed DATA extents and initialization only. They
do not establish behavioral equivalence or resolve host integer-promotion and
session-bridge differences. Neither the active generated profile nor the
preserved `recovered_source_next` profile was regenerated as part of the
scalar-candidate correction.
