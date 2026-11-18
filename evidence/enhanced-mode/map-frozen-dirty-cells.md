# Frozen Map and spider cache markers

Observed during the UI-scale verification on 2026-11-18, production input
identity `4d8a788f765d54bc5e4d9bbe876c50ca42646dcecb8c6dbc85e4881b59202687`.
This records a remaining failure; it is not a new converter contract or a
claim about the original executable's displayed pixels.

## Reproduction and established source facts

The native panel's original `%` button is object 010E. In Full Game and
Experimental, the complete control sweep prepares a paused, running game,
opens the inspectors and invokes this original object. The process calls
`abort` through `require_transform` in the faithful S00 map converter. The
five-second modal observer does not turn this into a pass: both rows are
reported incomplete with exit E0000001 and their crash stacks are retained.

The canonical `src/ui/map_window.c` explains the input:

1. `DrawMapSpider` draws the picture, then marks the first cached colour in
   each of up to five rows with 0xff. These marks force a later redraw.
2. `ProcMapEvent` 010E toggles the private frozen-background flag `g_2994`.
3. With that flag set, `map_generate_surface_colours` copies the cache into
   its generated logical colour buffer and overwrites only cells containing
   current life. A dirty first-column cell without life remains 0xff.
4. `map_render_immediate` passes the generated row to
   `map_dispatch_scaled_bitmap`, reaching `gfx_planar_map128_pack2`.
5. `graphics_s00_map_tables.c` explicitly accepts only logical colours 0–24.
   It reports `SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR` and its source-facing
   wrapper aborts. This is a controlled abort, not an access violation.

A separate private-desktop diagnostic restored the old >25-iteration startup
and additional 20-iteration preparation delay. Full Game still had exactly
five invalid cells, maximum value 255, in the 8192-byte cache before 010E at
iteration 68, and still aborted. Experimental also aborted. Thus removing
blind waits is not the cause. Preparation still pauses simulation; this
diagnostic does not claim to reproduce every timing detail of the old suite.

## Why no guessed raster fallback was installed

The symbolic canonical `src/platform/video/planar_minimap.asm` implements
this lookup differently from a checked C array: two shifts of AL wrap the
byte index. For 0xff the resulting four-byte lookup starts beyond the
25-entry colour table. Given the module's symbolic layout it reaches the
dispatch-table region, including relocated function-pointer data. Neither a
transparent pixel nor colour 15 follows from that code. Determining the
original raster output requires an original-executable observation and
proven data adjacency / relocation semantics. The current investigation
has not established those output pixels.

Replacing 0xff with an arbitrary colour, discarding the `%` row, disabling
the control, restoring guessed cache values, or relaxing the unsupported
colour negative control would hide the failure. None was done. The source,
faithful converter and acceptance references remain unchanged. A future
repair needs either a justified faithful conversion extension or a clearly
specified enhanced-only treatment of this source display-cache defect,
with its own comparison and negative controls.

## Reproducible evidence

All paths below are ignored scratch under `build/workers/enhanced-menus/`:

* `ui-final-sweep-full/result.json`, row 010E, and
  `ui-final-sweep-full/full/083-010e/run.log` / `diagnostics/`.
* `ui-final-sweep-experimental/result.json`, row 010E, and
  `ui-final-sweep-experimental/experimental/081-010e/run.log` /
  `diagnostics/`.
* `diagnose_map_readiness.py`, `map-readiness-probe.c`, and
  `map-readiness-old-timing/result.json` with each mode's inventory log.
* `ui-final-freeze.json`, the production build `ui-scale-release-build/`,
  and the final report's private-desktop audit links.

The diagnostic only reads the existing handle payload before the normal
010E enqueue and adds logging. It does not alter the cache or game state.
