# Phase 1: immutable native world

Implementation organisation and native presentation are ours. Source semantics
come from `src/ui/edit_view.c`, `src/ui/yard_window.c`, `src/graphics/anim.c`,
`src/graphics/font_resources.c`, `src/graphics/balloons.c` and their converted
platform boundaries. The canonical files are unchanged.

Set `SIMANT_ENHANCED_CONTRACTS=1` and run `--windows`. The Game Window's entire
client is now a native world canvas; the yard/house/strategic/graphic client is
also native. They return from their native branches before any hosted upload.
The desktop, other panels and separate modal/dialog windows remain the existing
host until their planned phases. No docking workspace or new panel is added.
`SIMANT_ENHANCED_WORLD=0` selects the retained hybrid comparison without turning
off publication or the immutable catalog. Classic without the contract variable
retains its previous behavior.

## Asset ownership

`enhanced/assets.c` reads verified HCEGANT and SHARED database files with native
stdio/malloc. `desktop_files.c` invokes it only after checking the shipped SHA-256
identities and valid CFG, before entering DOS main. The decoder handles the
record and packed-picture LZSS layers separately. It owns both 32,768-byte terrain
sets, both 24,576-byte life banks, all 252 pictures and FONT2. Picture masks are
converted to native transparent indices once; terrain/life composition uses the
existing pure compositor on catalog records. Each recolour mode and the F0..FF
exception follow the DOS tile compositor's interpretation.

Accessors expose const art. Native cell composition uses neither canonical bank
handles nor the C000h terrain cache. It never loads/locks/pins a canonical asset,
calls `edit_prepare_life_tiles`, borrows VGA pixels or forces source updates.
A catalog count, format, extent, font or allocation failure is a startup error.
Music's source bank eviction remains unchanged. Native buffers and SDL textures
are presentation allocations; teardown destroys them and frees the catalog.
Active palette values remain the host's semantic palette, not a raster readback.

## Generations and effectful source output

`EnhancedWorldSnapshot` copies all three map/life planes, all six scent maps,
terrain/layer, player pose and status text. Its pure projection spells the
`DoCalcTile` display mapping over those copies; it does not call that function or
change globals temporarily. ELayerMode affects surface world terrain only;
MapMode is the distinct overview/yard selection. The food channel is copied but
is not invented as an extra DOS world-layer choice.

Completed source edit draws additionally publish:

- Shipped spider picture IDs and their final world-pixel positions.
- Each source-selected leg/palp line endpoint and color, after source RNG has run.
- The one balloon actually selected for drawing: anchor, plane, style, tail and
  copied text. The source can queue six; DrawBalloons displays at most one, so
  the native view does too.
- Source compound-color rectangle operations, including raster operation.
- Draw serial, plane, source viewport and origin describing the selection scope.

The port observes the existing viewport clip seam, buffers outputs privately,
and commits them at the matching clip-pop. It taps external picture, line and
MakeBalloon calls; every original call still executes exactly once. In particular,
it does not wrap and rerun DrawSpider/DrawPalps/DrawCurBalloons or assume linker
wrapping intercepts calls within their own translation unit. Reentrant presentation
uses the previous complete publication. Modal polls retain the last complete
source selections while map/entity arrays and immutable art stay available.

The foot/mower routine is present in the canonical edit module; the source search
finds no C call to it in the normal shipped loop. The rectangle tap records its
compound-color output if emitted; no invented actor activation or source call is
added to make it appear. This is a coverage limit, not proof that a footprint is
active in a scenario without an emitted source selection.

`hanim_RenderAnimSet` publishes yard actors after its original render/removal tail.
The mirror uses the converted two-byte-packed native record layouts, with compile
assertions (14-byte AnimSet, 54-byte AnimObj). The existing
`sim_handles_global_resolve_payload` reads real or opaque index handles without
locks, ageing, allocation or last-status writes. Only picture ID, position,
priority and logical ID survive into the pointer-free publication. Source
reinsertion, sentinel positions, hide/removal and rain/swarm RNG have already run.
Repaint does not create, move or render a canonical animation set.

## Native drawing and scope

The SDL camera draws crisp nearest-neighbor tiles at arbitrary client size;
integer wheel steps above 100% and optional smoothing are presentation choices.
Enhanced zoom and pan do not recenter MapPnt. A source window that closes on
button-down retains the original coordinate origin for its matching button-up;
the new canvas beneath it cannot reinterpret that completed chooser gesture.
This bounded fix leaves live proximity tracking and the phase 3 activation
registration unchanged. The current Game Window frame still has the existing
source compatibility resize bridge; passive workspace sizing is phase 2. This
world task does not claim layout/resize invariance. Existing explicit gameplay input
bridges can still request canonical scrolling; replacing these with the complete
phase 3 native action surface remains future work.

World tiles, entities, spider and source-selected lines use native indexed
buffers. Speech/status text uses the immutable shipped FONT2 atlas; native bubble
geometry and layout are presentation, not an original bitmap claim. Yard and
house combine their shipped left/right art with selected actors. Strategic and
graphic views project published colony populations into native geometry/style
(our presentation, not a pixel-equality claim); they do
not count colonies or run source draw routines. Source-selected effectful poses
have the recorded source visibility scope; opening a wider native view does not
run hidden producers for its newly exposed cells.

Card/link/help payloads, docking, native command panels and lifecycle/dialog
presentation are outside this world task. Their unavailable flags and existing
phase registrations remain explicit. The dialog beside the rebirth screenshot
is still a separate source modal surface; it is never baked into the world.

## Reproduction and evidence

`portable/tests/enhanced/run.py` requires the music-enabled rebirth to PASS, the
retained hybrid to lose imagery, and both waits to have identical complete
semantic world hashes. The activation bug remains a phase 3 XFAIL. Missing bug
preconditions are errors. Positive executor and duplicate-delivery controls stay
required.

`assets.py` independently parses the local verified corpus in Python and compares
5,120 native cell cases (all grounds, both terrain sets, all life/recolour codes
on three backgrounds) and every native decoded picture. It writes no asset bytes
to tracked paths. `capture.py` uses ordinary input plus the already audited N05
semantic action. Its scent fixture completes the original proximity menu before
enabling the native canvas; no source state is written by the fixture. The speech
fixture enables Silly through FD36 and captures an actual selected balloon.

`invariance.py` compares all raw acceptance views, SaveRec slices, RNG, source UI,
clock and audio commands. It now compares native view off/on with the same
hosting arrangement and publication active in both. Its stress lane performs
nineteen additional copies and native cell/overlay rasterizations at source seams.
Repeated off/off remains a control; no new masks hide baseline or native differences.
The per-entry result lists are the authority when the raw result is nonzero.

Final task receipts, exact differences, screenshot index and reproduction commands
are in `build/workers/enhanced-phase1/RESULT.md`. PNGs and decoder dumps stay under
that ignored directory. There is no whole-executable equality or full reconstructed
source completion claim here.
