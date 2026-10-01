# S25 `o25_3BA4_1035` focused search

No candidate closed the target. The 281-byte body remains 92 instructions; the baseline's
20-byte frame and all ten far-pointer stack words match. Its only residue is the register
choice for the last field pointer: candidate `LES BX,[BP-10h]` / `PUSH ES:[BX]` at 110B/110E,
original `LES SI,[BP-10h]` / `PUSH ES:[SI]`. The two differing operand bytes begin at
target offset +0xD7. Other accepted S25 claims and `CONST`/`_DATA` passed in every row.

Seed: `1035-base.c`, SHA-256 (LF-normalized) `b8edf99f8db14d7cd2d4a4ee611c6de7177e005fb794dcb48e83824302c3ac40`. It is the frozen phase-next S25
whole-module draft (`sources.json` pins the same hash and manifest identity). The phase-next
field lifetime, view, folded-read and optimizer series were not repeated.

The new semantic lead was separate pointer lifetimes for the same real global at the earlier
draw call and later DigMyTile argument, with one initialization before the coordinate update.
A near-call scalar value-result control tested the post-update argument value. Pointer aliases
preserve the referenced object and read point; none changed the target into an exact match.
The early draw-call pointer is the negative contrast: it leaves the original two operand bytes
unchanged. No exact source or rule follows from these controls.

| Variant | Compile | Target | Other accepted claims | Private data | Source SHA-256 (LF-normalized) |
|---|---:|---|---|---|---|
| `base` | yes | bytes differ (first at +0xd7, 2 differing) | all exact | exact | `b8edf99f8db14d7cd2d4a4ee611c6de7177e005fb794dcb48e83824302c3ac40` |
| `early-call-pointer` | yes | bytes differ (first at +0xd7, 2 differing) | all exact | exact | `6fc85b5d512274619573b3571f0b79c3680f410a6e0d084b83cdf50baa29f871` |
| `dig-call-pointer` | yes | length 284 != target 281; bytes differ (first at +0x4, 89 differing); relocation set differs (6 vs 6) | all exact | exact | `4712fe5f19e1515e312230890f7a926e21772b929f85176e1f6ba79e15616451` |
| `dig-pointer-before-coordinate-write` | yes | length 291 != target 281; fixup at +0x117 crosses the extent end; bytes differ (first at +0x4, 134 differing); relocation set differs (5 vs 6) | all exact | exact | `d583361178ef094f42807dc50e200937570764385965e46a4277a7a0be203280` |
| `dig-call-value` | yes | length 282 != target 281; bytes differ (first at +0xcf, 71 differing); relocation set differs (6 vs 6) | all exact | exact | `8d695abcff3d2df69b3d75c47b649683cc0d1353942a0bebdc1353e351f78b14` |
| `one-pointer-two-phases` | yes | length 284 != target 281; bytes differ (first at +0x4, 89 differing); relocation set differs (6 vs 6) | all exact | exact | `fa6772e6bd790642df52f12e8290af6f7268933c5797e76d285da25050c51336` |

Whole-module checks used `modctx.resolve` and `variants.run(jobs=2, claims_only=True)` for
S25:3BA4, including all currently accepted claims and both private-data placements. The
optional `o25_3BA4_1686` returned-local series was not rerun: its prior result-flow/lifetime
controls already cover those broad forms and no new listing-grounded lead emerged.
