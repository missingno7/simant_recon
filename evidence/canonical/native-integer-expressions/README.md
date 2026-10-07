# Declaration-driven integer conversion

Status: **partial closure; native-integer-expressions stays OPEN**.
Canonical game source, program inventory and DOS compiler profiles are unchanged.

`portable/canonical_native_abi/integer_frontend.py` replaces the lexical word
island parser. GCC expands macros with parse-only libc declarations; pycparser
resolves lexical declarations, typedefs, structs/anonymous unions, arrays,
functions and old-style parameters. Every source expression receives MSC16 and
MinGW LLP64 types, a category, a status and a mechanical reason. Included native
headers remain native ABI contracts. Native layout assertions are retained
verbatim, and fake declarations never enter compiled output.

The pass applies MSC integer promotions, C90 literal candidates and usual
arithmetic conversions. Eligible unsigned arithmetic, products, division/modulo,
valid shifts, mixed comparisons and conditional operands narrow before consumers.
The operation widens only after DOS operand conversion, preventing host signed
overflow. Macros are expanded once. Short-circuit/conditional boundaries and one
lvalue evaluation in compound assignment are preserved. The pass
withholds effectful lvalue addresses when RHS calls/global reads could make the
helper's address-before-RHS order observable; independent nonescaping local
scalar operands and constants have an explicit mechanical contrast.
Native build receipts
contain the complete pre-lowering expression census and input/output hashes.
The census file/line/column coordinates refer to that pre-lowering generated
TU, with a separate canonical source identifier; macro expansion coordinates
refer to each invocation. Category counts overlap and unresolved dependent
parents are counted individually rather than treated as new independent hazards.

Signed arithmetic is proved equal only when declaration/literal interval
arithmetic excludes overflow. Additional local intervals come from nonescaping
assignments, dominating integer guards and monotone counting loops; mutations,
address-taken/volatile variables, switch entries and unstructured goto flow have
explicit conservative controls. Globals retain their full declared domains.

Real-compiler counterexamples prevent universal wrap claims:

* MSC 6.00A and AX contract signed `(a*9)/3`, including `/Od`. At `a=-32768`,
  MSC returns `-32768`; forcing a word product before division returns `-10922`.
  This is compiler-dependent signed-overflow behavior.
* MSC contracts unsigned `(b*9)/3` too. At `b=32768`, MSC returns `32768`, while
  defined C16 modulo multiplication then division returns `10922`. A volatile
  word-store barrier keeps the division. Thus even defined unsigned C16 rules
  alone cannot prove equality to this target compiler. Constant-algebra domains
  and their affected children are withheld, not silently wrapped.
* Unsuffixed decimal `4000000000` contradicts the C90 candidate model:
  MSC returns false for `0 < 4000000000`; the `L`-suffixed positive contrast
  returns true under every tested profile. The unsuffixed form has an explicit
  unresolved target-literal domain. Native C11 selects signed 64-bit here;
  supported long/unsigned variants receive the appropriate MSC32 conversion.

`evidence/codegen/INT16-1-signed-contraction.json` is the permanent pinned
positive/negative compiler probe. `controls.json` summarizes actual freshly
compiled MSC 6.00A `/Od`/`/Oeg` and DOSBox-X MSC AX `/Os`/`/Oeg` execution. All
probe code is relocation-free compiler output, executed in a 16-bit Unicorn VM;
no original EXE code or patched objects are involved. The native negative lane
retains only declaration conversion. Single-evaluation controls run at O0/O2.

Unresolved expressions remain explicit: potential signed overflow and dependent
parents, target constant algebra, invalid/negative left shifts, division overflow
and trap identity, high character constants, unresolved declarations, pointer
casts/arithmetic and layout-dependent sizeof. No guessed game-input ranges or
bounded gameplay observations discharge those domains. Pointer representations
are related only through the existing native ABI; numeric pointer observers need
separate proof. The complete census belongs to ignored build output.
The preceding ABI pass erases near/far pointer spelling. Pointer descriptors
therefore do not certify physical DOS pointer widths. Pointer sizeof, casts,
arithmetic values and comparisons stay open; real near/far `sizeof(p-q)`
controls both confirm the signed-word difference result type even though
the subtraction's pointer domain is not discharged.

```powershell
python -m pip install --target build/deps/pycparser -r portable/tests/integer_semantics/requirements.txt
python portable/tests/integer_semantics/controls.py --out build/workers/NAME/integer-controls
python portable/build.py --sdk <SDL3-SDK>
python portable/tests/integer_semantics/census.py --report build/current/portable/report.json --out build/workers/NAME/census.json
```

The former island parser and its specialized replay/receipts were retired with
`tools/workspace.py`; their published provenance remains in Git at `671f8eb`.
The replacement keeps one production expression pass and permanent generic
controls. Passing runtime VGA/Save/Load/logo flows corroborates only those paths.
