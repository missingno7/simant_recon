# Consumed register returns

`census.py` preprocesses all converted C TUs and canonical declarations with GCC
and parses them with pycparser. The cached dependency is `build/deps/pycparser`.
It resolves code aliases, distinguishes discarded statements from consumed
expressions, builds conservative return CFGs, enumerates implicit declarations
and undeclared runtime calls, and records consumed ASM and indirect call sites.
Constant loops, switch defaults, labels, goto, break and continue have explicit
controls. Parse failures remain failures. Parse-only libc headers and opaque
inline ASM do not establish expression/layout/hardware equivalence.

```powershell
python portable/build.py
python portable/tests/return_abi/census.py --build build/current/portable --out build/workers/user/return-census --verify
python -m unittest discover -s tests -p test_native_register_returns.py -v
```

The output directory must be fresh. `--verify` rejects any compiled consumed
void, implicit-int or missing result path. It also checks finite initialized
function-pointer tables. The heap TU is recorded but is not native-compiled;
its failure continuations remain explicit debt. Dynamic bindings and the DOS
register contracts of ASM are separately reviewed in
`evidence/canonical/native-register-returns/census.json`.

The conversion loads reviewed register contracts and rejects changed function
tokens. R1's constant AX zero and two final-call AX results become explicit
native C returns. Canonical sources, callers and RNG algorithms stay canonical.
The permanent negative controls cover the old void-result defect, implicit-int,
bare/partial returns, source drift and unreviewed empty functions. When a default
native build exists, the tests rerun the whole-TU census and require no unresolved
compiled consumed result; without that build, this one control is explicitly skipped.
