# Source clip pointer and S00 planar bitmap boundary

`graphics_source_clip.{h,c}` is the one native owner for source DGROUP `g_5A9C`,
`g_5AAC`, and `fd_55B3_3DE6/3DE8`. The owner uses the shared four-word
`struct Rect` from `window_source_rects.h`; it does not model the DOS upper
segment word `g_5AAE` as a separate host integer. The observed initial resident
bytes for `g_5A9C` are `{0,0,349,639}` and `g_5AAC` is null. Root `m205F`
`f_205F_0004` later writes the selected logical right/bottom dimensions.

The entry point `sim_graphics_source_clip_slot()` returns the address of the
actual pointer owner (`struct Rect **`). `sim_graphics_bind_source_abi` accepts
that typed slot. `sim_graphics_source_bitmap_bind` installs source table
callbacks `g_914C` and `g_9150`; teardown uses
`sim_graphics_source_bitmap_unbind`. The source clip transform in
`graphics_clip_source_convert.py` must run before compiling every generated TU
that consumes these globals. In particular, it maps the source `int16_t *`
view's element 1 to `Rect.top`, converts the S10 save/restore local to a typed
pointer, and preserves the m1CE2/m218D byte-address views with explicit casts.

The S00 source `o00_31AD_0CF9` dispatches to its local `o00_31AD_0D06` when the
clip pointer is null, and otherwise calls root `f_1D8E_07F6`. The native
`g_914C` callback follows that same nullness branch. Its non-null branch runs the
actual generated `f_1D8E_07F6`, whose `g_9150` calls reach the native planar
sink. That root helper intersects source Rects as half-open bounds and sets the
left/right crop words for the sink. The sink consumes ordinary even-profile,
four-plane rows and maps their plane bits into one indexed framebuffer owner.
It rejects odd `g_5A97` profiles and nonzero `g_3DD2` explicitly.

Validation receipts are immutable: `portable/tests/whole_program/platform/evidence/graphics-s00-bitmap-native-v6-20261003.json`
executes the actual generated root clipper, checks the observed initial owner
state, and covers the DOS-probed 112x112 direct payload plus direct and two-region
clipped cases; `portable/tests/whole_program/platform/evidence/graphics-s00-clip-source-views-v1-20261003.json`
compiles the 11 current source consumers after the canonical view transform.
The earlier bitmap-native v1–v4 receipts are preserved; v5 is the first receipt
that compiles the generated clipper after the canonical Rect conversion.

This admits the S00 g914C/g9150 boundary for the tested modes and inputs. It does
not complete the broader driver table, save/restore slots, clip-list storage
allocation, odd source profiles, nonzero raster operations, or bounds-checked
caller bitmap spans (the source ABI carries no span length).
