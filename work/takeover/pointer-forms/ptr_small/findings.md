# f_20E8_0903 pointer-form controls

The frozen whole-module seed is `seed.c`, copied from
`work/takeover/full-search/f_20E8_0903/best.c`. Its search-text SHA-256 is
`e9f7805d6d353e1d3d432cd146073bae6bb8ec0be13b20e3543a3895e2a1ef49`.
The fresh listing is retained in `context.txt`.

The target is 286 bytes. Its listing computes three field pointers from `o` in
order (`o + 4`, `o + 12`, `o + 8`), then scales each loop index by two. In the
two subtraction loops it loads `rect[i]`, carries the scaled index across a
far-pointer reload of `o`, subtracts `o[i]`, and stores through `origin[i]`.
The preserved seed is 280 bytes. Historical work had already covered the
general Boolean, common-subexpression, parameter-copy, statement-order and
symbol-name families; this pass stayed with pointer/address expressions.

The generator produced the full 40-variant budget: seven combinations replacing
the three fixed pointer additions with `&o[k]`, all 31 nonempty combinations
rewriting the five indexed pointer families as `*(p + i/j)`, and two controls
reversing the additive operand order for one side of `rect[i] - o[i]`. All 40
compiled under the inherited `msc600ax` profile and `/AL /Os /Oe /Og /Gs /Zi`.
None matches: all remain 280 bytes, with six relocation entries. The seven
fixed-base address-of forms first diverge at +5; the other 33 first diverge at
+0x77. No result is evidence for excluding compiler output.

`promote.py --verify-only` was run on each whole-module source. Every run kept
all 16 accepted peer claims exact and both private-data segments exact; each
was refused only because `f_20E8_0903` itself remains inexact. No canonical
source or manifest was changed. The search log, per-candidate gate results and
source hashes are retained in this directory (`search.log`, `gate-report.json`,
`generated.json`, and `verify-only.log`). No further pointer hypothesis is
grounded by the current listing, so this target is ready to rotate.
