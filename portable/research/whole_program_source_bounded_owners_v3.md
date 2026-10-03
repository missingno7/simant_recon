# Whole-program native state owner proposal V3

This diagnostic proposal expands portable native storage ownership from source declarations. It does not edit the frozen DOS source, the central generator, or production integration, and it does not claim that a native build now runs.

## Result

The report selects 176 groups occupying 660 native bytes:

- 154 two-byte scalar owners and 18 four-byte scalar owners are represented as typed scalar/raw-byte unions. For each group, source declarations agree on a complete `int` or `long` scalar at one address. The only additional view is the S09 save table's `unsigned char[]` view. The exact `SaveRec` `size * count` for that view equals the scalar width. Examples include `HealthR` / `fd_50F6_01FE` at `50F6:01FE` and `MapPlane` / `fd_50F6_032E` at `50F6:032E`.
- Four array owners have complete source bounds: two `unsigned char[100]` arrays at `50F6:037C` and `50F6:0404`, plus two `int[20]` arrays at `50F6:0D40` and `50F6:0D72`.

The address index is cross-checked against frozen `layout/symbols.json`; source files are cross-checked against `layout/manifest.json`. The old V2 owner report and its 87 historical-range candidates remain unchanged. V3 sizes come from source type/bounds and save-record byte counts, never from a historical gap length.

## Reproduction and checks

Run `python portable/whole_program/conversions/source_bounded_owners_v3.py` to regenerate the candidate summary. `--write` creates the immutable JSON receipt and ignored scratch header/C translation unit. The producer refuses to overwrite these V3 outputs. `--verify` rebuilds the expected content in memory and checks the receipt, header, and TU byte-for-byte.

The generated owner TU compiled with:

`gcc -std=c11 -fsigned-char -fno-builtin -fno-common -Wall -Wextra -Werror -c build/workers/whole_program/source_bounded_v3/native_owners.c -o build/workers/whole_program/source_bounded_v3/native_owners.o`

Positive controls confirm consistent aliases, exact SaveRec width matches, complete array bounds, unique owner addresses, and no registered interior symbol overlaps. Negative controls reject a wrong SaveRec width, a conflicting scalar width, an array with no complete bound, the known code address, and any address already owned by V2.

The full per-symbol source rewrite map is retained in the JSON report. Scalar consumers use the typed union member; S09's save-table consumer uses its raw-byte member. The report requires removal of the old `extern` declaration before applying each mapping. The native owner TU is not independently linkable with unrevised migrated modules: production integration still needs the central source transformer to apply these source-scoped mappings and the DOS-width scalar lowering consistently.

Remaining source groups with pointer/structure views, conflicting scalar widths, non-S09 byte views, no complete source bound, or an interior symbol remain unresolved. No generic pointer, structure, or zero-size fallback is emitted.
