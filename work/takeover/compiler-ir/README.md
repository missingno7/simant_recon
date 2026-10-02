# MSC 6.00AX C1 front-end capture

The research-only hook in `tools/research/capture_ir.asm` intercepts `/B2`
before C2 and dynamically discovers the C1 temporary files ending in `EX`,
`IN`, `ST`, or `SY`. `tools/compiler_ir.py` builds and runs it in DOSBox-X with
the pinned MSC 6.00AX tree, expanded pinned headers, and explicit module flags.
Each capture is isolated under `build/workers/compiler_ir/<label>/`; raw
streams, compiler logs, input hashes, and the DOSBox transcript are retained.

Example:

```powershell
python tools/compiler_ir.py capture work/takeover/full-search/o15_384C_0239/best.c `
  --label s15-base --flags /AL /Os /Og /Oe /Zi
python tools/compiler_ir.py compare build/workers/compiler_ir/s15-base `
  build/workers/compiler_ir/s15-font-predicate-equivalent `
  --out work/takeover/compiler-ir/s15-font.json
```

The expected CL diagnostic is C1042 after the capture hook returns: the
intermediates were copied and the real C2 pass was intentionally not run.
This diagnostic is an interception marker, not evidence that the source
failed a normal compile. The capture is research-only and cannot enter the
promotion path.

## Controls and findings

All captures used the pinned `msc600ax` profile and `/AL /Os /Og /Oe /Zi`;
the source was staged under a constant `UNIT.C` basename so source-path
metadata stays fixed. EX is the substantial C1 stream. IN, ST, and SY were
also retained and compared byte-for-byte. The comparison tool does not
normalize opaque records; it lists all raw differing offsets and marks the
two known `UNIT.C` strings in EX.

| Pair | C1 result | What it establishes |
|---|---|---|
| Tiny `return 1` vs `return 2` (`probes/tiny-return-one.c`, `probes/tiny-return-two.c`) | EX differs at one byte (offset 46); IN/ST/SY are identical | Positive control: a changed integer constant survives into EX while the other captured records stay fixed. |
| Tiny `return 1` vs same one-line source with extra spaces (`probes/tiny-return-one-whitespace.c`) | EX/IN/ST/SY are byte-identical | Negative control: whitespace alone does not change these streams when line count and basename stay fixed. |
| S15 base vs top-level `extern int far g_hardtail_probe;` diagnostic probe (on the existing typedef line, so `/Zi` line numbers do not shift) | Both EX streams are 3,681 bytes; 335 differing offsets. IN: 1 byte; ST: 5 bytes; SY: 178 bytes. | A declaration added before the functions changes C1 stream content even after keeping all original line numbers fixed. The differences are consistent with symbol/type and identifier-reference state reaching C1. The probe name is synthetic and diagnostic only. |
| S15 base vs equivalent reversed font predicate | EX has 3 differing bytes; IN/ST/SY are identical | C1 retains a small expression-form distinction despite equivalent result. |
| S15 base vs direct text expression instead of local `text` | EX: 3,681 vs 3,658 bytes, 1,918 differing offsets; ST: 1 byte; SY: 3,076 vs 3,055 bytes, 1,089 differing offsets; IN identical | Removing the local changes the C1 representation extensively, as expected for a real local-lifetime/source-structure change. |

Machine-readable comparisons are `tiny-one-v-two.json`,
`tiny-one-whitespace.json`, `s15-extern.json`, `s15-font.json`, and
`s15-text.json` in this directory. Raw streams and capture metadata are in the
ignored `build/workers/compiler_ir/` tree.

## Limits

These files are diagnostic C1 front-end temporaries produced from current
candidate source. They are not the original compiler's saved IR, are not C2's
optimizer/register-allocation state, and do not show what the original source
fed to C1. The additional audit in `s15-extern.json` separates locally
verified identity patterns from heuristic matches in S15. Same-line rename
controls show that external, function, and local spellings can change SY while
leaving EX identical. In a tiny positive control, adding one earlier extern
changes four EX values after `0x26`, `0x29`, or `0x3A` by +1 and explains every
changed EX byte. In S15, aligned scanning finds 274 such +1 value candidates
that cover 275 of 335 changed bytes. One apparent +256 is a false outer-marker
match: bytes `3A 29 84 00` overlap two marker patterns, and the inner `0x29`
candidate changes by +1. It is reported as ambiguous rather than normalized.

The remaining 60 differences sit beside other token values on source lines
containing branches, loops, switch tables, or `goto` structure. Their bytes
also move by +1 (with one low-byte rollover), which is consistent with
renumbered control-flow labels. The stream grammar does not identify those
fields yet, so the conclusion is **strongly consistent with identity and label
renumbering, but full EX equivalence after normalization remains unknown**.
No normalization is applied, and no new codegen rule or target-source claim
follows from these captures.

The compact comparison JSON records all 60 offsets with nearby raw bytes,
nearest C1 source-line context, and identifiers on that line which appear in
SY. Those SY names are context only; they do not prove the neighboring EX
field refers to those identifiers. Same-line extern/function/local renames
change SY spellings while leaving EX identical in the tiny controls; moving a
typedef before a function changes EX, while putting it after the function
only appends records. These controls distinguish name spelling and declaration
position effects, but do not decode the S15 residual bytes. Recreate the
same-line S15 extern source with
`python work/takeover/compiler-ir/probes/make_s15_extern.py`; tiny source
controls are stored in `probes/` rather than only under ignored build output.
