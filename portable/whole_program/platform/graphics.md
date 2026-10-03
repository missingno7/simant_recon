# Whole-program graphics bridge (bounded S00 profile)

`graphics.{h,c}` owns one indexed host framebuffer at 640×350 EGA mode 10h by
default. Source `f_1B4E_015B` accepts source-backed 10h and 12h mode requests;
the latter selects VGA 640×480 as set by `o00_31AD_2AE5`. The source values
are `g_3DB2=640`, `g_3DB4=350 or 480`, and `g_3DB6=80`. Host stride is 640
bytes because host storage is indexed, while the DOS value 80 describes
planar storage. A mode-change callback updates the presentation host's logical
dimensions. Clip state belongs to the single framebuffer, with a bounded
nesting stack. This module owns only the source graphics pen, background,
text pen, and font reference. It does not duplicate window, game, or UI state.

The native ABI exports `f_1B4E_000D`, `f_1B4E_015B`, and `f_1B4E_0228` with
their source argument widths. `f_1B4E_0228` is the original INT 10h AX=1001h
overscan color request, not a mode setter; it records that source color for
the presentation host. Selected driver function-pointer globals bind only while an application-owned
`SimGraphicsDriver` is bound. `g_9134` is provided here as the native source
ABI callback for the whole-program lane; the older recovered-engine prototype
is a separate link target and remains untouched. The S00 `DispatchS00` table in
`src/S00/m3126.asm` has exactly 25 positions. The bounded ordinary indexed
contracts are g9128 (`o00_31AD_1659`, foreground/background), g912c and g9130
(BIOS/custom font selectors, following the source pointer-table copy and
`o00_31AD_1AE7` slot overrides), g9134
(`o00_31AD_16A9`, normalized solid rectangle with source `g_3DD2` raster
operation), g9138 (`o00_31AD_0122`, caller-owned source-pattern view), g913c
(`o00_31AD_037C`, XOR rectangle with source Set/Reset color 0x0f), g9154
(`o00_31AD_1206`, whose nonzero `g_5AAE` branch is reported
unsupported), g9158 (`o00_31AD_1213`, direct bounded MSB-first one-bit
transfer), and g9170 (`o00_31AD_1499`, source-derived x-canonicalized
Bresenham walk). Its x-major and y-major ties advance the minor coordinate
only when accumulated error is strictly greater than `floor(major/2)`; the
vertical case uses a separate byte-column loop. The g434* check only hides a
cursor whose bounds overlap the line and does not clip line geometry. Native
storage writes remain bounded by the framebuffer clip. Source `g_3DD2`
values 0, 08h, 10h, and 18h map to replace, AND,
OR, and XOR on indexed pixels; nonzero operations outside that reviewed set
fail explicitly. The tie rule was compared with the original for all octants,
reversed endpoints, degenerate and edge cases, plus deterministic randomized
coordinates; this is a normalized VGA-write contract, not hardware plane
emulation. Slot 11 and slot 12
remain distinct. Fill and bitmap drawing use existing software framebuffer
primitives. `f_1B4E_000D` alone applies the source `g_41C0` palette map;
S00 fill/line/bitmap callbacks consume the resulting color bits directly, so
they do not apply a second mapping. `g_9138` reads the original 256-byte
pattern region through a caller-owned source view; no pattern bytes are copied
into platform code. `g_912c`/`g_9130` update the source font metrics in the
same order as the S00 table and its explicit CGA overrides. BIOS glyph bytes
remain an external host font-provider input; missing or truncated spans are
reported explicitly. The 6-pixel high-character fold
path is explicitly unsupported; it is not replaced by guessed glyph data.
`PortableFont` remains for the separate proportional resource-font format;
it is not wired into this fixed-cell BIOS glyph boundary because the formats
and metrics differ.

The table-to-slot mapping is pinned in
`evidence/graphics-s00-driver-table-proof-20261003.md`. It records the
`f_1B4E_0165` 25-far-pointer copy through `g_3DF8`, the `g_20FC` S00 table,
and the two later font-slot writes. Other S00 entries retain their exact
source target in `sim_graphics_driver_slots()` and report `provided=0`. The default empty
function at `f_1B4E_000C` is not installed as a renderer. The 25 S01 targets
are exposed as inventory only; that driver contains MDA/Hercules hardware
operations and is not emulated. This bridge does not claim VGA register
side effects, BIOS branches outside the selected mode and overscan calls,
clipping notifications, or whole-program drawing output.

The selected field converter in `graphics_source_convert.py` removes mapped
field `extern` declarations in a converted source TU and rewrites those
references to `SIM_GRAPHICS_SOURCE_g_*` accessors backed by the single bound
owner. It defines no duplicate graphics data globals. The selected source
callback globals are typed function pointers and null while no owner is bound.

Run the native contracts with
`python portable/tests/whole_program/platform/run_graphics_test.py`; the
bounded original-DOS pattern/XOR receipt is produced by
`python portable/tests/whole_program/platform/run_graphics_s00_pattern_dos_diff.py --report <new-path>`. The native tests
check source mode dimensions versus host stride, callback binding, source
field reads/writes, palette nibble mapping including a non-involution double-map
contrast, clipping, fill, line, and XOR behavior,
bitmap/font bounds, text pen updates, and explicit unsupported results. This
is a native contract test, not a DOS differential rendering receipt.
