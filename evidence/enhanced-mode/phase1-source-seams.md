# Phase 1 world evidence map

These are implementation/projection facts, not recovered original file boundaries.
No decoded art or game-world dumps are stored here. Reproduce with local verified
resources and `portable/tests/enhanced/capture.py` into ignored scratch.

| Native contract | Source/format anchor | Executable check |
|---|---|---|
| Native asset ownership | `desktop_files.c` verifies the shipped file identities before `enhanced_assets_load`; native stdio/malloc only | Enhanced startup receipt, decoder comparison, null-bank rebirth |
| Terrain and life | HCEGANT kind 9: 10/9 are yard/house terrain; 13/14 are nest/surface life records. See `edit_load_terrain_tiles`, `edit_prepare_life_tiles`, `edit_draw_life_and_ground_tile` | Every ground tile and life/recolour code on three backgrounds in `tests/enhanced/assets.py` |
| Pictures | Shipped HCEGANT/SHARED kind 2; record LZSS and packed-picture LZSS are separate layers; 12-byte decoded header, row-interleaved planes and optional leading mask plane | All 252 decoded pictures compared independently |
| Font | `font_ReadFont` and `font_MakeImage`: big-endian header/locations/advances, first atlas row skipped, height minus one | Actual native status and multiline speech captures |
| World cells | `DoCalcTile` presentation formulas over copied map/life/scent/player fields | All-plane native composition under extra paints; original/canonical/native acceptance remains separate |
| Spider output | `DrawSpider -> gfx_buffer_line_target / anim_bitmap_to_buffer / DrawLegs / DrawPalps -> gfx_buffer_line` | Actual source-selected body and 20 line segments in the retained spider scenario |
| Balloon output | `DrawCurBalloons / DrawSpider -> AddMsgBalloon`; `DrawBalloons -> MakeBalloon`, at most one shown | FD36 enables Silly through the ordinary source menu; capture the selected text/anchor |
| Completed overlays | `edit_set_viewport_clip -> clip_intersect_rect_list`, matching edit clip-pop | Draw serial/scope plus copied semantic outputs; no composite pixels |
| Yard actors | `Draw_SimYard -> hanim_RenderAnimSet`, after the original removal tail | Final selected art, position, priority and logical ID, no buffer pixels |
| Yard record ABI | Converted source has `#pragma pack(push,2)`, pointer width 8; AnimSet 14 bytes, AnimObj 54 bytes | Compile-time assertions and yard/house runtime captures |
| Handles | `sim_handles_global_resolve_payload` supports real master pointers and opaque 0F0F index tokens without changing manager state | Native yard capture; the earlier development reader rejection/crash is retained in scratch history |
| Closed chooser release | The source closes 0200 on down before the replayed up; legacy retargeting interpreted up through the new Game Window | Same-host native off/on raw mouse views; no source pointer/clock writes are used to repair the comparison |
| Effectful cadence | Every wrapped source call executes once; paints only read completed publications/catalog records | RNG, SaveRec, source UI, clock and sound-command comparisons |

The viewport tap deliberately captures external dependencies rather than assuming
`--wrap=DrawSpider` could intercept calls within its own translation unit. Native
repaint never reruns effectful spider, balloon or yard producers. Neither source
bank presence nor VGA terrain/image buffers enter the native pixel/key path.

The retained footprint/mower function has no C caller found in the shipped source.
The compound rectangle tap records emitted operations if reached, without invoking
that function or inventing activation. Runtime coverage of those outlines is not
claimed by a scenario in which the source emitted none.

The full raw passive check remains stricter than meaningful gameplay observations.
`hanim_MakeAnimSet` initializes count/max/objs but not nextId; arbitrary animation
IDs expose an existing unresolved allocator/history boundary. This is a candidate
explanation for some variability, not a proved cause of every observed word;
the complete raw-difference cause remains unsettled. The logical stack and
clip workspaces also contain raw data beyond their active sentinels. Off/off
variability is evidence of that baseline, not permission to mask, initialize or
ignore it in the raw result. Final exact per-view/entry differences and the
negative detector control are retained in the task's invariance receipt.

Current implementation guide: [phase 1](../../docs/enhanced-mode/phase1.md).
Task receipt and PNG index: `build/workers/enhanced-phase1/RESULT.md` and
`build/workers/enhanced-phase1/screens/README.md`.
