# S00 exterior drawing repair

The base is `40e1f2d`. Ordinary Full Game input reproduced both reported native
aborts before the repair: a title-bar drag crossing the right/bottom edges
reached `win_DrawWindow -> o00_31AD_0647`; map scrolling followed by the shipped
spider toolbar control reached `UpdateEdit -> DrawSpider -> o00_35A6_0007`.
Read-only GDB observed the latter's horizontal offset 46 and vertical offset 54.
The original S00 instructions accept these inputs. Canonical source is unchanged.

## Inventory and attribution

`inventory.json` joins all canonical S00 entries to named providers or absorbed
callbacks and inventories rejection/diagnostic sites in every `graphics*.c`,
`font_blit.c` and `algorithms/*.c`, including additional named S00 providers.
The baseline scan has 194 rejection/diagnostic lines; the repaired scan has 158.
A file-level helper consumer join identifies possible callers, not an assertion
that every listed entry executes every rejection. Inventory mappings are not
equivalence claims.

The crashes had two distinct lower-layer causes:

* `35A6:0007/0177` blend **RAM** bitmaps. The old wrapper treated `[bp+10h]`
  as a Boolean flag and restricted `[bp+0Eh]` to 0..15. The ASM uses byte `MUL BL`
  for the destination row offset, then `SHR`/`AND` for whole-byte displacement
  and bit rotation. Its word stores can cross a plane-row byte boundary.
* `31AD:0647` copies the **VGA CPU aperture**. The old wrapper rejected exterior
  framebuffer coordinates before the canonical clip/no-intersection decision.
  Cache storage and visible storage had separate owners. The source uses one
  aperture, clipping first, then mode-1 latch copies or a planar RAM fallback.

## Projection and retired mechanisms

`SimGraphicsDriver` now owns four 64 KiB VGA planes and the used graphics and
sequencer register state. CPU reads load all four latches; mode-1 writes copy
those latches through the map mask. Mode-0 supports rotation, set/reset, logical
operations and bit-mask merging. SDL presentation decodes visible rows from the
same planes; screen dimensions do not constrain CPU aperture addresses.

| Canonical scope | Native projection | Retired restriction/mechanism |
| --- | --- | --- |
| `31AD:0647`, L066F–L0833 | `graphics_tile_upload.c` | display bounds, cache alignment/range guards, detached cache planes |
| `31AD:186A/18BA` | same file | fixed transfer size, plane-index/range assumptions; preserves original small-count quirk |
| `31AD:1A8F` | `ega_map_readback.c` and shared read-plane service | end-of-aperture rejection; restores low-byte busy bookkeeping |
| `31AD:0550`, L058A–L05CA | `graphics_capture_source.c` | visible/cache split, exterior zero padding, resource-specific capture selection, duplicate aperture-only API |
| `31AD:1950` | `graphics_misc_source.c` | framebuffer-bounded host copy; uses forward/reverse latch copies |
| raw rectangle, pattern, line, 1/4-plane bitmap sinks | `graphics.c`, `graphics_bitmap_source.c`, `graphics_misc_source.c` | host viewport clipping and screen-sized line delta guard; canonical `m1D8E` remains the clip owner |
| `35A6:0007/0177/02FD/0406` | `graphics_s00_raster_source.c` | Boolean row argument, shift limit, alignment/header-shape assumptions, guessed buffer extents |

The old raster/capture generations were retired through `tools/workspace.py`;
the public module paths contain their replacements. There is no legacy source
mode or compatibility adapter. Explicit-size host/test APIs retain real RAM
capacity checks. Null services, absent owners, malformed resources, unsupported
CGA/Tandy profiles, font-resource validation and non-VGA algorithm restrictions
remain explicit. They are not reclassified as fixed by this repair.

## Permanent controls and scope

`portable/whole_program/platform/tests/run_graphics_vga_tests.py` executes 127
locked original-instruction cases: RAM blend/copy outputs, complete tile planes,
partial-clip callback data, exterior captures, uploads and readback wraparound.
It compares relevant register state and low-byte busy state for the tested VGA
entries. Independent hardware controls cover masks, latches, ALU and presentation;
negative controls retain short-resource rejection and show that the old shape
predicate excludes tested sprite inputs. The prior 64-row pattern extent test
remains permanent. No original executable bytes enter production sources.

`portable/tests/runtime/run_edges.py` supplies independent ordinary-input launches
for right/bottom window drag, left window drag and map-edge/spider drawing.
It requires current build pins, complete input delivery, observed exterior source
calls and window/map state, a meaningful frame, normal exit and no fault. The
map case holds shipped Ctrl+Home scrolling until the canonical upper/left limits
are observed, then uses the spider toolbar control. Pointer-at-screen-edge
scrolling also reached the limits in exploration but stalled in the pre-existing
input polling loop; this separate input-refresh issue is not claimed fixed.
existing VGA, Save, Load, logo and drag flows remain required checks.

These are bounded instruction and ordinary-input witnesses. Whole-game DOS/native
frame identity is not claimed. Historical CPU/IRQ residue, malformed RAM resources,
arbitrary register preconditions, source row-table adjacency outside normal clipped
inputs and the complete register epilogues of every pre-existing pixel projection
are outside this closure. No speculative owner or source-algorithm change is made.
