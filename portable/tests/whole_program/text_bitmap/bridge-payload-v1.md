# `f_1FBD_0000` bitmap payload boundary

The bridge now passes the pixel payload (the first byte after its width/height
header) to the bound `g_9154` callback. The original `_f_1B4E_005E` routine
provides the boundary evidence in `src/root/m1B4E.asm`, lines 161–174: it reads
the two words at `[image]` and `[image+2]`, advances `BX` by four, then passes
that advanced image pointer together with the dimensions to `_g_9154`.

The focused native test wraps the actual callback, checks the exact callback
bytes against the prepared source pixel plane, then delegates to the real
graphics owner. Its negative control verifies that the old header-prefixed
pointer cannot match the expected payload bytes. This does not claim a full
DOS drawing differential or prove caption visibility by itself.

Source pin for the original strip-header sequence:

* `src/root/m1B4E.asm` SHA-256: `a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2`

Reproduce with:

```powershell
python portable/tests/whole_program/text_bitmap/run_bridge_test.py
```
