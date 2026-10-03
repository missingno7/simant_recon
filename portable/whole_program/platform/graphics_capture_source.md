# S00 capture and save-size callbacks

`graphics_capture_source.{h,c}` provides the source S00 table slots `g_9140`,
`g_9144`, and `g_9148` after `sim_graphics_bind_source_abi` has installed the
single `SimGraphicsDriver` owner. The provider is separate from the common
graphics binder so it can be linked and reviewed as its own source callback
batch; `sim_graphics_source_capture_bind()` performs no owner or framebuffer
allocation of its own.

The implementation follows S00 `o00_31AD_0522`, `o00_31AD_11FB`, and
`o00_31AD_0550` in `src/S00/m31AD.asm`. Both size functions use the same
source-aligned row count, `(right-1 >> 3) - (left >> 3) + 1`, and word-height
subtraction. `g_9140` returns `4 * row_count * height + 4` modulo the source
AX word; `g_9144` returns `row_count * height + 4` modulo AX. Arithmetic
shifts and intermediate word wrap are explicit, including negative and
overflowing size-query controls. The checked capture API limits access to a
valid in-frame rectangle and buffer capacity; the source ABI callback has no
buffer length, as in the original far-pointer signature.

`g_9148` writes the source four-byte little-endian header (aligned pixel width,
height), then serializes each row in plane order 0, 1, 2, 3. Within a plane,
leftmost pixels occupy bit 7. The data is derived from the existing indexed
framebuffer; no second screen owner is created. The differential test models
the original EGA/VGA read-map register as an explicit DOS VM service: writes to
GC index 4 select the corresponding prepared plane behind the A000 aperture.
This exposes all four source planes to the original body without claiming a
hardware or complete VGA emulator.

The source ABI capture now follows `_o00_31AD_0550` around that copy. It holds
the low byte of `g_3DD4`, runs the pre-copy cursor-hide service only when the
source rectangles overlap (inclusive edges) and `g_4333` is clear, performs
the planar capture, then applies the source post-copy `g_4365/g_4331/g_4366`
branch before releasing the display-busy byte. The calls go through the shared
typed `graphics_cursor_hooks` service, which the whole-program application
binds to `f_1B73_0196`, `f_1B73_00D9`, and `f_1B73_04BB`. A required but unbound
or failing hook exits with an explicit diagnostic; the callback does not
silently capture over a visible cursor.

The source cursor rectangle uses `g_4340` as left, `g_4342` as top, `g_4346`
as right, and `g_4344` as bottom. This matches `_0DA4` stores in m1B73 and the
signed overlap comparisons in S00 `_0550`.

Validation:

`python portable/tests/whole_program/platform/run_graphics_capture_dos_diff.py --report portable/tests/whole_program/platform/evidence/s00-capture-planar-dos-native-v5.json --native-output build/workers/recovered_tick_proof/graphics_capture_v5.dll`

The v5 receipt compares five bounded planar captures, both save-size results
on those rectangles, and three wrapped AX size cases against the locked DOS
functions. Its cursor-guard cases are historical evidence for the earlier
fail-closed implementation only; they do not validate the current cursor
policy.

Current cursor-policy controls:

`python portable/tests/whole_program/platform/run_graphics_capture_cursor_policy.py --report portable/tests/whole_program/platform/evidence/s00-capture-cursor-policy-v2.json --native-output build/workers/recovered_tick_proof/graphics_capture_cursor_policy_v2.exe`

The v2 receipt executes the actual S00 `_0550` body in the DOS VM for overlap,
disjoint, lock-held, hidden, and mouse-busy cases. The three m1B73 callees are
controlled source-boundary callbacks that apply their reviewed state
transitions; the receipt checks call order and final `g_3DD4/g_4331/g_4332/g_4365`
values. A strict native probe checks the matching five branch orders,
redraw/update counters, display-busy byte preservation, and exit-70 failure
when the overlap hide hook is absent. Mouse callback internals are covered by
their separate m1B73 provider tests; this receipt does not claim full original
cursor pixels or unbounded buffer safety for the source ABI, whose signature
has no length. The earlier v1 receipt is preserved; v2 adds exact final-state
assertions.
