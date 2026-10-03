# Strict static completeness review

`index-v1.json` covers all 29 frozen behavioral registrations. Every imported
implementation now has a root-reviewed `BEHAVIOR_EXACT_CONFIRMED` receipt. Each
receipt accounts for original control flow, arithmetic widths and constants,
pointer/state operations, ordered calls and observable effects. Differential runs
and negative controls corroborate those static comparisons; passing a finite
suite alone cannot admit a function. No receipt claims new byte-exact coverage.

The original registered `DrawBalloons` source **fails** this definition. Its
unsigned allocation expression zero-extends the wrapped 16-bit sum, whereas the
original `CWD` sign-extends it. No source-enforced dimension bound excludes that
case. `DrawBalloons-registered-source.json` retains the `UNRESOLVED` verdict.
SOURCE_ONLY_DOS imports the separately reviewed whole-module correction in
`../corrections/DrawBalloons/module.c`: `(long)(int)(n + 4)`. The unsigned value
used by the subsequent memory fill remains unchanged. The 1,009-case replay,
signed-width boundary controls and indexed stack-write/later-read matrix for all
six legal queue indices support the corrected receipt. The historical registry,
canonical sources and byte claims remain unchanged.

The four specifically requested cases (`win_PrintStyleTextInRect`,
`f_171C_0CF4`, `o10_35F5_0384`, `f_2505_0453`) have full operation/branch/call maps
and no unexplained semantics. For `o15_384C_0239`, the actual generated module
proves that the four additional stack words read by `win_Open` are identical at
the call; the conclusion does not assume the tested asset excludes mode 5.
`DisplayCard` records the compiler stack-check requirement of 122 bytes versus
118 in the original. Its confirmation requires sufficient stack; the 118–121
byte low-stack boundary differs and remains an explicit integration constraint.

Graphics receipts prove the caller algorithm and exact callback-slot ABI/order
parametrically in the same actual callee state. They do not claim that synthetic
test adapters validate physical pixels or complete driver integration. Those
storage, frame, hardware and runtime contracts are separate SOURCE_ONLY_DOS
gates.

The build checks receipt/source/evidence pins and complete root review axes.
`CONTRACT_EQUIVALENT` and `UNRESOLVED` remain function blockers, and `EXACT` also
requires explicit byte verification. A reviewed correction must be in the same
whole module with the same DOS declarations, macros, types and function order.
