# Source-body conversion check

This experiment executes native code extracted from the original bodies of
`f_2505_06B9` (`src/root/m2505.c`) and `f_1FD2_0883` (`src/root/m1FD2.c`). It
does not invoke the hand-authored planner under `portable/ui_model/windows`.

`extract_bodies.py` locates function definitions (skipping prototypes) and
copies their full bodies. Its only edits come from `source-conversion.json`:
strip DOS calling/storage qualifiers at the native signature, map raw window
field addresses to a typed window view, and sign-extend the source `char`
margin explicitly. The include lowers source `int` declarations to `int16_t`.
Every replacement is count-checked; body hashes and source line locations are
written into `extracted_bodies.inc`. The original branch order, calls, and
arithmetic expressions remain in the extracted functions.

The source `f_1FD2_0883` body calls typed metric, registration, and unregister
callbacks. The metric adapter looks up the actual HCEGANT kind-2 records; the
registration adapter captures the source-generated rectangle and mode. The
test runs all 135 cases from the v2 DOS differential receipt, re-executes the
hash-locked original functions, checks those fresh traces against v2, then
compares the extracted-body native trace against both.

Run with a new, not-yet-existing report path:

```powershell
python portable/tests/windows/decorations/source_conversion/run_source_conversion.py `
  --report portable/tests/windows/decorations/source_conversion/source-body-differential-v2.json
```

The command compiles the native fixture itself. It refuses an existing report
path before extraction or compilation and stores pre/post source, dependency,
GCC subtool, Python executable, and loaded Unicorn identity hashes in the
receipt. It does not modify production files, canonical historical sources,
or the v1/v2 planner receipts.
