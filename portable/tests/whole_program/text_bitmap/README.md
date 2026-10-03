# Original text-bitmap helper

`portable/whole_program/text_bitmap.c` is the source algorithm for
`f_1FBD_0000`; `text_bitmap_bridge.c` exports the native C ABI name and routes
the result through the single bound `SimGraphicsDriver` owner and its already
bound `g_9154` callback. It does not define a second font, framebuffer, or
graphics owner. The direct-text profile follows the existing native
`sim_graphics_f_1B4E_0081` service. The source entry is `far` with arguments
`x@+6`, `y@+8`, `far text@+0x0a` and `retf` (no argument pop); native callers
use the platform C ABI.

The `fold_lookup_window` parameter is an explicit view of bytes beginning at
source DGROUP `_g_5FBE`, not a normalized accented-character table. In the
4-pixel branch, original `m1FBD.asm` indexes it with the raw unsigned text
byte. Only the first 40 bytes are initialized as the visible literal in this
module. Larger raw indices read following DGROUP state/data and are therefore
not a portable character mapping. Bind the complete live 256-byte source state
window only when a caller actually owns it. With no such window, 4-pixel
strings containing high bytes return `UNSUPPORTED_CHARACTER`; this is an
explicit limitation, not a claim that those bytes are absent from all game
resources. The 8-pixel path indexes all 256 glyphs directly. Profile 6 takes
the source direct-text path and currently inherits its native ASCII-only
font-service limit.

The bounded original-machine source differential is
`evidence/text-bitmap-original-dos-v1.json` (131 cases, same source algorithm
and ordered bitmap/direct-text sink observations). It supplies an explicit
256-byte DGROUP window as case state; its synthetic window values establish
raw-index semantics only and are not production fold data. The native ABI
bridge test is a separate native integration check:

```powershell
python portable/tests/whole_program/text_bitmap/run_bridge_test.py
```

That test compiles the bridge and actual graphics owner, exercises 8-pixel and
4-pixel strings, checks the unsupported missing-window high-byte boundary,
and confirms bitmap output reaches the bound framebuffer. It is not an
additional DOS differential.
