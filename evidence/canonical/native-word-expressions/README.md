# Closed unsigned-word expression conversion

Parent review, 2026-10-05: installed as a mechanical native ABI conversion.
Canonical game source and ordinary state ownership are unchanged.

`portable/canonical_native_abi/word_islands.py` recognizes complete expression
spans whose DOS operand types follow from explicit scalar casts, MSC16 integer
literal types, parentheses and supported child operators. Identifiers, calls,
fields and indexes remain opaque unless an existing explicit cast supplies the
type. No function/module name or source hash selects an edit.

An unsigned 16-bit addition/subtraction with both operands independently known
to be signed/unsigned words is narrowed to `uint16_t` before its consumer.
The native intermediate fits 32-bit int; narrowing supplies the DOS modulo
65536 result. A comparison between known signed and unsigned words converts
both operands to unsigned words, as the DOS usual arithmetic conversion does.
Nonnegative small signed constants need no comparison edit. Original operand
order, single evaluation and short-circuit boundaries are preserved. Typed
32-bit peers inhibit these edits. Preprocessor and ASM regions remain opaque;
unknown/signed-only arithmetic, multiplication, division and shifts are outside
the class. Ambiguous/crossing spans stop the build's conversion.

The current whole-program scan emits two nodes in compiled root:m22BF:
`(unsigned)win + 0x100` and `(unsigned)win + 2` in win_DoProxMenu. The third is
`(unsigned)size + 15` in root:m171C, which is generated but explicitly excluded
from native compilation at the physical DOS heap platform boundary. Its original
171C:12B0..12B8 load/add/word-shift/store corroborates the same narrowing. There
is no pointer-derived or post-adapter extra edited operand in this inventory.
Each TU's `word_expressions` build receipt records exact spans, types and hashes.

The parent's installed generic runner passes eight classes times 65,536 rows
at each of GCC O0 and O2, plus single-evaluation, short-circuit, precedence,
literal-type and unsupported-syntax controls. These corroborate the static
integer relation; they do not establish general native integer equivalence.

The current-only replay consumes a successful unchanged build and its actual
complete generated menu TU. Removing exactly the two result casts in a test
copy supplies the negative control. Read-only COFF comparisons preserve all
46 peer functions and storage; the target's code changes. All 113 selected
word-valued window/event fixtures agree with original DOS execution under the
stated UI observers, whereas 21 negative fixtures differ. This is a function
entry domain, without a claim that shipped resources use high window IDs.

Same-TU calls bypass GNU wrap, so execution-only whole-TU test derivatives
replace the win_IsWinOpen observer body with the callback used in the DOS VM.
The target is untouched and never extracted. Separate unmodified complete-TU
compiles provide the peer/storage control. No object or executable is patched.

```powershell
python evidence/canonical/native-word-expressions/generic_controls.py --out build/scratch/word-controls-fresh
python portable/build.py --out build/scratch/native-word-build-fresh
python evidence/canonical/native-word-expressions/replay.py --build build/scratch/native-word-build-fresh --out build/scratch/word-probe-fresh
```

Outputs must be fresh beneath build/. Receipts retain the parent's actual runs.
The existing native-integer-promotions packet and platform manifest still expose
declaration-driven wrap, products/division, shifts, macro expressions and general
literal typing. Those remain SEMANTIC / PORT-BLOCKING; no global closure is claimed.
