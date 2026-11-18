# Frozen Map and relocated dispatch bytes

Updated 2026-11-18. Supersedes the earlier unresolved raster investigation in
this file. The native abort is repaired at the faithful S00 conversion boundary;
the historical dirty cache and its visible striped band are retained. No
canonical game source or source pins changed.

## Established machine behaviour

Object 010E toggles the frozen Map background in Full and Experimental games.
`DrawMapSpider` marks column zero in up to five cache rows with FF. The frozen
generator preserves a mark without life at that cell. A subsequent exposed-window
redraw can pass it to `gfx_planar_map128_pack2`. Ordinary original-game mouse
replays establish this path in both modes; the band persists until unfreeze.

The original S00 packer shifts **AL** twice, wrapping FF to FC. Four XLATs read
`g_1F9E + FC..FF`, original DGROUP `55B3:209A..209D`. This starts two bytes
into `DispatchS00[0]`: its segment word, followed by slot 1's callback offset.
The symbolic facts are raster segment **31AD**, small-font callback offset
**166A**, and an observed reference load paragraph **0824**. Relocation gives
`31AD + 0824 = 39D1`, hence lookup bytes `D1 39 6A 16` (little endian).
The native converter derives these bytes from address facts and executes the
original rotate, mask and duplicate operations. It does not store pixels as a
stripe, use a host function pointer, or read outside a native table.

The ordinary 640 table ends at 2001; the intervening objects are the 320 table
(2002..2065), attribute data (2066..2077), capacity dwords (2078..2097), then
DispatchS00 (2098..20FB). The FF lookup crosses several objects, not just the
next table. See [data adjacency T09](../../docs/data-adjacency.md#t09--frozen-map-ff-reads-relocated-dispatch-data).

The first-column cell at reference load 0824 displays indexed scanlines
`1 5 6 11`, `5 6 11 6`, repeated twice. Five dirty rows form a four-pixel by
20-pixel band. Original Full and Experimental videos retain it for respectively
332 and 325 frames before scripted unfreeze. Those are bounded observations,
not an intrinsic expiry time. Different loads change output; 082C changes the
second scanline. Production explicitly selects this documented reference machine
at the video boundary and clears the binding on reset/unbind.

## Scope and canonical layout debt

The admitted source domain is **0..24 plus FF for 640 consumers** 0000, 0137,
04D8 and 06A3. The 320 consumers still reject FF. Colours 25, 26, 63, 64, 127
and 254, invalid spans/nulls and unbound/unsupported layouts fail before any
destination write. Ordinary 0..24 conversion does not require a layout binding.

The fresh working canonical DOS layout places the raster at segment **3075**,
so its reference-load crossing reads `99 38 6A 16`. Its observed band differs
from the original in exactly 30 pixels at the 32-second Full checkpoint. The
same explicit native profile interface admits that documented layout for
differential controls; production startup never selects it. Original and
canonical captures are compared separately without masking or recolouring.
This is unresolved link-layout debt. This scenario is **not three-way
FRAME_EQUAL**. The 320 crossing also depends on following masks whose canonical
placement differs; no ordinary 320 display observation or FF support is claimed.

## Reproduction and retained evidence

The read-only investigation packet is
`D:/Prog/simant_recon/build/workers/map-cache/`: read `REPORT.md` and
`evidence-index.json` (original identity
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`).
Its scripts include `inspect_image.py`, `cache_state.py`, `packer_oracle.py`,
`final_analysis.py`, `native_mouse2.py` and the ordinary `original-drag.scr` /
`experimental-drag.scr`. Indexed dumps, original videos and complete
pack-in/pack-out buffers are ignored game-derived evidence, never copied into
tracked source. `canonical-layout.json`, `canonical-lookup.json`,
`canonical-state.json` and `pixels.json` retain the original/canonical distinction.
Earlier native failures remain under the investigating checkout's
`build/workers/enhanced-menus/ui-final-sweep-{full,experimental}/`; they establish
the previous abort, not a current failure.

The repair report is `build/workers/map-cache-2/REPORT.md` in the worktree.
Its `portable-final/report.json` pins production inputs and tools;
`focused-complete2/report.json` records test/source hashes, complete buffer counts,
negative controls and GUI receipts. Reproduce into fresh worktree output:

```powershell
python portable/tests/hidden_desktop.py portable/build.py --out build/workers/map-cache-2/NEW-build --jobs 6
python portable/whole_program/platform/tests/run_map_frozen_cache_tests.py --build build/workers/map-cache-2/NEW-build --out build/workers/map-cache-2/NEW-tests --gui --evidence D:/Prog/simant_recon/build/workers/map-cache
python portable/tests/hidden_desktop.py portable/tests/enhanced/sweep.py --build build/workers/map-cache-2/NEW-build --out build/workers/map-cache-2/NEW-sweep --modes full,experimental
```

The focused runner installs `hidden_desktop.py` itself. It compares every byte
of 28,800 FF instruction outputs (every source position, both nibble parities,
every ordinary neighbour, four 640 consumers, loads 0824/082C/0924), plus 400
ordinary outputs across all six transforms and both miniature profiles. Original
DrawMapSpider/DrawMapFoot instructions produce zero/five/eight/clipped-edge
footprints at controlled positions for both source widths (1,024 complete rows).
Bitmap drawing and allocator boundaries are explicit callbacks in those isolated
producer controls; they do not claim normal-play foot reachability.
Optional retained captures check 315 Full, 325 Experimental and 315 canonical
outputs, including their 10/12/10 FF buffers. No destination bytes are masked.

GUI lanes use the same production executable for bare and enhanced
Full/Experimental freeze/move/unfreeze. Bare input is a mouse replay; enhanced
input clicks the actual 010E HWND, moves the Map, clicks again and exercises a
Pause roundtrip (host time for external input; bare and observer lanes retain
deterministic virtual time). A separate observer over the same production objects repeats
both flows. Every intercepted native buffer is compared
with locked original instructions at the reference profile; source, complete
cache and both RNG states are checked for conversion-time immutability. The
second 010E is followed by further loop iterations and no FF pack inputs. Complete
enhanced sweeps separately exercise input recovery through Pause controls.
These are converter-buffer and interaction claims; they do not assert a new
synchronized whole-game scanout comparison. Only application frame captures are
used. Private-desktop receipts and all bounded/joined child results remain in
ignored output; no desktop screenshot is taken.
