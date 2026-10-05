# Post-reset graphics-index failure

The bounded original execution reaches the uninitialized raster loop after a
real driver-table reset and a call to the genuine empty procedure. The older
conditional witness depended on an unexplained zero-target callback returning.
That premise is unnecessary for this distinct graphics-index failure prefix.

Current whole source orders `f_1B4E_0025` before the graphics database open,
cursor setup, driver installation and font callback. The replay executes the
actual reset, verifies all 25 slots contain `1B4E:000C`, then directly calls
original `OpenIndex` with a test-owned `hcegant` path and mode-zero selector.
It models only failed open (`-1`, errno 2) and four newline stdout characters.
Hardware detection, prior database initialization and the full startup are
outside the executed fixture.

Original `sprintf`, `vsprintf`, `DosPunt`, `Punt`, the empty callback and the
text helpers execute unchanged. The resulting 87-character message reaches
`f_1FBD_0000` with zero font height. Its first glyph's `MOVSB; ADD DI,DX; LOOP`
performs 65,536 stores at stride 79, visiting every DGROUP offset. Store 15 leaves
the 1,040-byte bitmap; store 18 leaves the complete 1,324-byte data contribution.
The receipt records actual changes to watched state. Height controls 1, 8 and 13
perform exactly that many row stores and preserve those watched fields.

Execution stops before `1FBD:0098` restores DI, at the end of the first row loop.
No subsequent glyph, fatal-helper call, cleanup, exit, returning `Punt`, minus-one
record access or fifth database slot is claimed. The eight current complete TUs
also pass their normal exact or explicitly reviewed context checks. Original
instructions are validation inputs only; this constructs no game executable.

Run from any directory with a fresh repository-relative output path:

```powershell
python evidence/canonical/graphics-index-failure/replay.py --out build/graphics-index-failure
```

The database/error-path layout gates remain **SEMANTIC / PORT-BLOCKING**. This
witness prevents a blanket fatal-state-invariance or `noreturn` assumption; it
does not supply a new allocation, fix the original algorithm or close those gates.
