# Bitmap storage owner v37

**Verdict: UNRESOLVED; no owner admission recommended.** `fd_50F6_1F26` is an external four-byte dimension-header view into a bitmap whose pixels begin at +4. No independently established complete source object, pixel capacity, or complete rendering domain was recovered.

The reproducible read-only audit is `audit_v37.py`; `receipt-v37.json` pins its inputs and results, `source-census-pins.json` pins all 212 inspected canonical, retained strict-effective and provider source files, and `original-disassembly.txt` retains readable original instructions. No canonical source, production provider, admission, manifest, journal, Git state or full validation was changed. No new compiler search, fixture execution, byte acceptance or runtime claim was made.

The retained v32 owner receipt and v22 resource-domain receipt were reviewed before this audit. The retained bitmap view/argument searches concern bitmap consumer lowering; they do not establish a static spider buffer declaration or length. This audit adds original relocation and callback evidence, a current provider census, explicit mode/call-order facts, and the Win16 declaration limit.

## Independent DOS evidence

`PreDrawSpider` stores `7*g_19BE` at `0250:1897` and `7*g_19C0` at `0250:18A2`. Both use the externally referenced frame word at DGROUP `7EEA`; original S27 relocation ordinal 2479 resolves that word to `50F6`. `DrawSpider` constructs offset `1F2A` at `0250:1A58` and its segment word at `1A60` has an original relocation to `50F6`. Thus the payload starts four bytes after `50F6:1F26`.

`f_1B4E_003B` reads words +0/+2 and passes +4 plus the dimensions to `g_914C`. `f_16B5_0033` also reads the dimensions and installs +4 in its line state. Neither reads a capacity field. The source `Pnt` is two DOS `int` fields; it describes that prefix only.

The original root-0250 CONST relocations to `50F6` occupy 57 separated target-frame runs. Under the established external-target-group evidence, sharing this frame is not evidence of a root-0250 far-object definition. Its bitmap reference identifies an external base, not a COMDEF declaration or length. The reconstructed/original S09 SaveRec table has no record at the bitmap base. No second registered exact-base symbol exists.

The original unrolled raster callbacks independently establish these conditional written extents:

| Graphics modes | Cell dimensions | Selector | Original callback shape | Required payload | Header + written extent |
| --- | --- | --- | --- | ---: | ---: |
| 0, 4, 8 | 16 × 16 | 1 | S00: 64 rows × 2 bytes, pitch 112/8 | 6,272 | 6,276 |
| 2 | 12 × 12 | 2 | S03: 12 rows × 6 bytes, pitch 84/2 | 3,528 | 3,532 |
| 3, 5, 7 | 16 × 16 | 3 | S01: 16 rows × 2 bytes, pitch 112/8 | 1,568 | 1,572 |

These follow the 7×7 caller loop, its tile-row advance, and the actual MOVSW/ADD DI,BX instruction counts. They are single-startup, initialized-selector tile-path extents, **not declared capacity or all-writer closure**. The next named offset `37D2` is 6,316 bytes after the bitmap base, 40 more than the largest extent above. Its zero-filled original gap is adjacency evidence only; neither 6,316 nor the extra 40 bytes is admitted as storage.

## Concrete domain and ordering limits

`g_19BE/g_19C0` start at 16 and the only source write changes both to 12 for graphics mode 2. The fixed-base aliases `fd_55B3_19BE/fd_55B3_19C0` are consumers in the census. The ordinary single-startup dimension domain is therefore 16×16 or 12×12. `LoadTiles` does not reset 12 to 16 on a subsequent call; no repeated-startup domain is asserted.

The original `LoadTiles` switch omits modes 1 and 6. Mode 1 can result from adapter detection; mode 6 is explicitly selected by `/d2`. Both have startup driver/resource paths, and the inspected source does not prove that every such path exits before map rendering. The existing functional selector owner is a far communal, which starts at zero under its startup contract. Zero is not a recovered raster case. Original `DrawSpider` at `1A26..1A3D` writes `[bp-10]` only for selectors 1, 2 or 3; the other path reaches `IDIV [bp-10]` at `1A4A` with an unassigned stack word. This is an explicit integration fact; no default, clamp, synthetic state or execution witness is supplied.

Startup installs callbacks before `LoadTiles`, which precedes application map-hook setup. The map draw calls `PreDrawSpider`, `PreDrawBalloons`, conditional `DrawSpider`, then `DrawBalloons`. `DrawSpider` performs the tile writes, installs the line destination, overlays a selected picture, then draws legs/palps through the line state. Header production is conditional on visible spider state. The later screen call also has a final-viewport-cell path with the inactive sentinel; fresh header production is not presumed on that path.

The balloon path selects font 2 (the font1 slot), constructs a separately allocated `MakeBalloon` image from font widths/heights, then allocates a separate `balbuf`. The copy callbacks intersect supplied rectangles; a consistent active spider rectangle is the seven-cell header rectangle. Those allocations and intersections do not define the static spider object's capacity. Full font/string arithmetic, malformed balloon state and computed aliases remain outside the bounded conditional result. The line assembly likewise provides a header-limited destination and a 200-word row table, without a bitmap capacity declaration.

The picture overlay selects kind 2 through `f_2662_1120`, dispatching type 3 or 0 with resource+8 and the destination header. Ordinary spider state selects `03E8..03EF` or `041A..041D`; load/save restores the selector words without the range proof required for those sets. Database order permits an earlier optional language package, shared/lrshare, then the display package; the cache is keyed by ID and kind. The prior positive-height and endpoint results apply only to the supplied HCEGANT bundle and normal spider state. MONONT, TDYGANT, LCEGANT, L256NT, earlier language records and restored/malformed state are not covered. Decoder row loops enter before termination testing, and resource widths/shifts lack a universal destination-width guard; those paths cannot be turned into a maximal-capacity claim.

## Win16 limit and exact blocker

The eligible `DrawSpider` HIGH correspondence and reviewed `PreDrawSpider` CONFIRMED decision were used only for semantic context. The recovered Win16 `data_03_spider_point` explicitly defines only the two-word `MapPoint`, declining the rest of its 6,316-byte public span. It supplies no independent DOS pixels declaration.

To close this import, recover the complete defining header-plus-pixels source object/COMDEF and its full extent, or establish an independent full source-functional writer/domain contract. The latter must recover or exclude modes 1/6, preserve the original unassigned-state behavior, and cover resource, font, restored-state, line and copy paths including specified alias effects. Current header views, conditional tile maxima, HCEGANT observations, callback clipping, zero fill and public adjacency do not supply that missing declaration/domain fact.
