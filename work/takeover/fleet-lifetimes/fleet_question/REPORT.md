# `f_1C62_0415` question dialog search

No candidate closed the 649-byte target. The pinned whole-module seed is the prior
`question-loop-order-v2.c` draft, copied to `question-base.c` (653-byte target body); its
manifest identity is recorded in `question-results.json`. The module compiler context is
`msc600ax /AL /Os /Oe /Og /Gs /Zd`.

The baseline frame is 78 bytes, matching the target, but its body is 653 bytes / 272
linear instructions against 649 / 274. The remaining mismatch is still in the loop-local
layout and control flow: candidate `j` and `count` split across BP-4/BP-C where the original
reuses those homes by phase; at 046C the candidate reloads BP-4 while the original uses AX,
and the first and draw-loop compare branches differ (`JL` candidate versus `JG` original).
`slots.py`/`diag.py` also show the c/v home merge and a missing draw-loop index reload.
The earlier loop-order, coordinate, and storage series were not repeated.

Seed SHA-256 (LF-normalized): `1a75da44054b48e33e02b0dc551e9e690d1b0797b5e2cfe2e3e6e26ad3b632d4`. Manifest SHA-256: `60ed22e4b8b38cdb62a0c441c507d2ed9940435ecbcaaee6d1289d76c5a7a5d6`.

New controls followed three source-grounded leads:

- `0x900` is the real object-ID base passed to drawing, key fallback, and cleanup calls.
  Four shared-local initialization placements preserve the argument values, but each grows
  the target to 658 bytes and loses accepted peer `f_1C62_06A6` at the whole-module gate.
- `sel` is the real default-key state: the original initializes BP-12 to -1 before setup,
  then passes its address to `o10_35F5_0A63`, which reads and updates the value for later key
  events. Keeping the initialization early as a declaration initializer leaves the baseline
  residue unchanged. Moving the single initialization to just before the input loop preserves
  state across calls and all accepted peers/data, but still gives a 653-byte mismatch.
- A returned-event snapshot before cleanup tests a result live across cleanup calls; copying
  only at the final return is its contrast. The early snapshot grows the target to 659 bytes,
  and these result-local variants lose `f_1C62_06A6`. Splitting the first-phase spacing
  accumulator from the later key variable also leaves the target inexact and loses that peer.

All controls compiled. Every private-data placement (`_DATA`, `CONST`, `_BSS`) is exact in
every row. A peer loss rejects that row even when its target/body distance changes.

| Variant | Target verdict | Other accepted claims | Private data | Source SHA-256 (LF-normalized) |
|---|---|---|---|---|
| `base` | length 653 != target 649; bytes differ (first at +0x52, 543 differing); relocation set differs (18 vs 18) | all exact | exact | `1a75da44054b48e33e02b0dc551e9e690d1b0797b5e2cfe2e3e6e26ad3b632d4` |
| `object-id-early-shared` | length 658 != target 649; bytes differ (first at +0xd, 612 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `6a0cadb888053617354ddf201645d5054c8cb7bf249d11036e531da000ddf183` |
| `object-id-declarator-init` | length 658 != target 649; bytes differ (first at +0xa, 615 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `27afce3258d0c6fabe330d53ad4694372b7cf2b62760c8fa204c4e6ca2d79d89` |
| `object-id-before-draw` | length 658 != target 649; bytes differ (first at +0x5, 540 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `b80894020b4d67770cef3a494266cb8dc405d8a5dbd510c76ab9916efc4a5cdc` |
| `object-id-before-key` | length 658 != target 649; bytes differ (first at +0x52, 528 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `c7dd693c27af190f47f0564b7db62a1ce8f1db956f181d1dd884b4879f5f424d` |
| `default-key-declarator-init` | length 653 != target 649; bytes differ (first at +0x52, 543 differing); relocation set differs (18 vs 18) | all exact | exact | `ac6b9d372515ee8bf04b432af2427c6bb30ba1b2af1b3ac7a7e4ada255beadd6` |
| `default-key-before-input-loop` | length 653 != target 649; bytes differ (first at +0x8, 628 differing); relocation set differs (18 vs 18) | all exact | exact | `ef55e73e5d593c09d9086492ff0488b68933c06c67cb28755b3474ee64c22bb5` |
| `return-snapshot-before-cleanup` | length 659 != target 649; bytes differ (first at +0x52, 540 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `e3dd36e44dcdb752ad719c6bc56b08dcfb041629c96d784f46f979190294dc05` |
| `return-snapshot-register` | length 659 != target 649; bytes differ (first at +0x52, 540 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `f7e73ae60b8550155d71807ecec798fbad6548b9ea8d3d433b961a64c3607a83` |
| `return-snapshot-after-cleanup` | length 653 != target 649; bytes differ (first at +0x52, 543 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `14b21c165b60be761b704643b12b92395a0e3880f60df77a95216dca8eaca5f3` |
| `split-spacing-and-key` | length 653 != target 649; bytes differ (first at +0x5, 553 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `3266c00847836d7e4f4d5661e6c0e6d27e39709db86872a07bb95f3822695e0a` |
| `split-spacing-and-key-register` | length 653 != target 649; bytes differ (first at +0x5, 553 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `a5fdc985e5ce5453245eadc4f70235831f24c8205d271a6f3890bffb9fdfc590` |
| `split-spacing-and-key-inner` | length 653 != target 649; bytes differ (first at +0x5, 553 differing); relocation set differs (18 vs 18) | failed: f_1C62_06A6 | exact | `6a263e3ab1366ab4e9b4141c41999067bc470ce9419d90f94d44e0521bf5bbf7` |

Whole-module checks used `modctx.resolve` and `variants.run(jobs=2, claims_only=True)` for
root:1C62. No candidate was exact, so no `search.py` refinement or `promote.py` call was
made. The generator and every compiled source are retained alongside this report.
