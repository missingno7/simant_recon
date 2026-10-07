# Original word-register intermediates in five native routines

The original `SIMANT.EXE` and source-only canonical DOS build agree on the
five retained witnesses. The native projection previously left their signed
word nodes `UNRESOLVED`, so host integer promotion changed the values consumed
by division, widening and comparisons. Canonical source is unchanged.

`contracts.json` records the original instruction addresses, exact preprocessed
AST expressions, occurrence counts and canonical source hashes. Reproduce the
instruction inspection with `python tools/context.py NAME` for each routine.
These are per-site machine contracts, not a new universal MSC signed-wrap rule.
In 16-bit code opcode `99` is **CWD**, despite Capstone's `cdq` spelling.

| Routine | Original operation sequence | Retained witness |
| --- | --- | --- |
| CalcScore | IMUL word at 0180; CWD at 0183 replaces the high product; IDIV BX at 0184 consumes the signed low word | /8: score component 3 is 2; total is 17401 |
| GetDis | SUB AX at 0B92/0BA4; CWD at 0B95/0BA9; long multiplication squares each signed word difference | /8: (-31846,2584,20309,18495) returns 432211082 |
| f_0250_0F2C | ADD AX at 0F79/0FAE; signed CMP/JLE | /0: viewport (0,1), height 32767 remains (0,1) |
| BalloonIsVisible | ADD AX at 4252/4275 and SUB CX,3 at 426A before signed comparisons | /9 returns 1; this witness wraps the X sum |
| BoundPointToTri | ADD AX at 06C1 before signed word /2; six word SUB operations feed full signed IMUL or CWD-widened divisors | /16: point (-4509,-11238), rect (11341,-11081,29084,-10794) becomes (-12555,-11081) |

The triangle witness first differs at its midpoint sum, not the later
interpolation. Interpolation multiplies **full signed DX:AX** after narrowing
the operands; it must not narrow the product to a word. Its final edge already
narrows through canonical `int` storage before comparison. CalcScore's other
products explicitly cast to long and likewise keep the full product.

The existing frontend computes each reviewed `+`, `-` or `*` node once in
`int64_t`, then casts its result to `int16_t` before any consumer. MinGW's signed
short conversion preserves the original signed low word. Source hash, AST
expression, count and operand-type checks fail closed when the contract drifts.
Receipts identify every applied contract and its instruction evidence. The
builder pins the inventory as an input. Unreviewed signed expressions, division
trap domains and MSC constant-algebra contractions stay explicit debt.

The original executable hash is
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.
p2-verify's canonical DOS image hash was
`cf03656a6f761e2b1bb1b41240a88d4a2bf58c78885bedc9c178cffea8d5edda`.
All five retained cases passed that original/canonical comparison. The witness
inputs and complete compared owner outputs are in the permanent fixture; its
provenance is seed `0x51A17`, random count 12. Neither executable bytes nor the
exploratory differential harness are integrated.

A sixth, directed subcase independently passes original/canonical DOS comparison:
BalloonIsVisible(0,0,-32768), viewport (0,0), width 2, height 1 returns 1 because
`y-3` wraps to 32765 before comparison. It complements the published X-sum
witness inside the same routine's unit test.

Run the focused production-object regression after a fresh native build:

```powershell
python portable/build.py
python portable/tests/word_intermediates/run.py
python -m unittest discover -s tests -p test_instruction_word_sites.py
python -m unittest discover -s tests -p test_native_word_expressions.py
```

The regression links the actual production object inventory from the successful
build report and has one unit test per routine. A freshly compiled whole-TU
negative control removes only CalcScore's product narrowing and must fail its
witness. Frontend controls require expression/count/type drift to fail and
retain the `(a*9)/3` contraction counterexample. Passing is confined to these
fixed witnesses and the reviewed instruction sites; it is no whole-program
equivalence or ordinary-gameplay reachability claim.
