# `fd_50F6_1F26` owner/type/layout receipt

**Verdict: `UNRESOLVED`.** The source proves that `50F6:1F26` begins a 4-byte bitmap header and that the following bytes hold pixels. It does not identify a defining source object or establish its complete fixed capacity.

## Audited inputs

The audit verified all **127 canonical manifest sources** and all **29 strict-effective whole-module sources**, selecting the reviewed `DrawBalloons` correction. They are 156 unique paths. `receipt.json` records each source path, SHA-256, and size, plus the manifest, strict index, and strict receipt pins. The exact identifier occurs in four source inputs: canonical `src/root/m0250.c`, corrected `DrawBalloons`, and the two pinned strict root-0250 whole modules. Those are 15 use/declaration lines per input. Only the canonical line is an `extern Pnt`; the remaining hits are accesses and calls. The registry contains no second symbol at the same start. The targeted source probes for `0x1F26`, `1F26h`, and decimal `7974` found no occurrences; the `image939` token is absent from the source set. No original executable or asset bytes were read.

## What the source establishes

`Pnt` is two 16-bit `int` fields, `x` and `y`. `PreDrawSpider` stores `7*g_19BE` and `7*g_19C0`. `DrawSpider` passes the header to the bitmap/clip routines, starts its raster pointer at header+4, then visits seven rows by seven columns. The checked-in `f_1B4E_003B` assembly reads words at offsets 0 and 2 and passes offset 4 onward to the graphics callback. `f_16B5_0033` also reads the two-word dimensions before clipping the bitmap. So `Pnt` is a correct header view, but it cannot describe the complete header-plus-pixels object.

The visible initialization paths establish these raster cases:

| `LoadTiles` selector | Cell dimensions | Raster callback | Required payload | Header + payload |
| --- | --- | --- | ---: | ---: |
| 1, graphics modes 0/4/8 | 16 × 16 | S00: 64 rows × 2 bytes; 112-byte pixel width has a 14-byte row pitch | 6,272 bytes | 6,276 bytes |
| 2, graphics mode 2 | 12 × 12 | S03: 12 rows × 6 bytes; 84-pixel width has a 42-byte row pitch | 3,528 bytes | 3,532 bytes |
| 3, graphics modes 3/5/7 | 16 × 16 | S01: 16 rows × 2 bytes; 112-pixel width has a 14-byte row pitch | 1,568 bytes | 1,572 bytes |

The callback instruction counts are pinned in `receipt.json`. These are conditional extents written by the tile rasterizer, not a recovered object length.

## Why ownership stays open

The 156-source census has no complete-object definition for this identifier. `LoadTiles` does not assign its renderer selector for source-reachable modes 1 and 6, while `DrawSpider` consumes that selector in the skip calculation. The post-raster `f_2662_1120` path also overlays a selected bitmap into the same destination; its write extent depends on resource dimensions and selector state. The available `event-resource-domain-v22` review is explicitly conditional on normal HCEGANT state and says it does not prove storage capacity. No adjacent registry name or address gap was used as an object bound.

To close the frontier, recover the defining TU or a reviewed full source contract for every selector and overlay-resource domain. If the owner is meant to describe the whole object, give it one named complete type with the 4-byte header followed by a proven pixel capacity, and use a compatible header-prefix view in consumers. A data-only source provider is viable after that full extent is known; declaring only `Pnt` would allocate just the header.

The detailed pins, hit lines, callback counts, and exact missing frontier are in [receipt.json](receipt.json). The audit script is [audit.py](audit.py). No production source, manifest, journal, Git state, or frozen source was edited.
