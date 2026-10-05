# Current canonical behavioral validation

`src/program.json` lists the 29 `BEHAVIOR_EXACT_CONFIRMED` definitions and their
static receipts under `evidence/canonical/semantic/`. There is no parallel
behavioral source registry and no build-time body selection.

Each receipt accounts for the original algorithm, complete CFG, branches,
constants, widths, signedness, pointer arithmetic, calls and call order, state
reads/writes and observable effects. Every remaining instruction difference must
have a codegen-only explanation. A finite differential contract cannot replace
this static conclusion. Byte-exact claims retain their stricter historical gates.

## Reproduction

The runner requires pinned Unicorn 2.1.4 in ignored `build/deps/unicorn`. On the
Windows x64 Python runtime used here:

```powershell
python -m pip download unicorn==2.1.4 --only-binary=:all: --platform win_amd64 --python-version 310 --no-deps --dest build/deps/wheels
python -m zipfile -e build/deps/wheels/unicorn-2.1.4-cp37-abi3-win_amd64.whl build/deps/unicorn
python -m unittest tests.test_behavior tests.test_canonical_behavior
python tools/canonical_behavior.py --count 16 --out build/current/behavior
```

Wheel SHA-256:
`d7107500c64ce5c168fbff6bef9485b5db1350050036f4cea568650cf8bdbdf5`.
The original `SIMANT.EXE`, dialog databases and period compiler are local
prerequisites. Compact `--count 1` still includes the directed domains; `--full`
expands the large directed corpora. Reports pin the current program, whole TU,
target definition, static receipt, compiler object, bound code, oracle and live
harness. Source changes during a run invalidate its identity.

## Execution and limits

`tools/behavior.py` creates two isolated 16-bit VMs. The candidate is compiled
from the complete current canonical TU and symbolically linked into its own code
arena. Original RTLink overlays execute in the oracle VM. Non-target helper
entries delegate to original helpers; explicitly modeled callbacks remain
documented parametric boundaries. No archived candidate or scaffold executes.

Cases compare return values, state and ranges, ordered callback arguments,
actual IN/OUT operations, and final values at the union of nonstack writes.
Caller ABI checks apply independently. Unknown interrupts, unmodeled input ports
and exhausted execution budgets fail closed. Pointer arguments to stack locals
use justified content projections; volatile registers and unobservable local
homes can differ.

The proof in `evidence/canonical/runtime/format-cursors.json` permits a typed
comparison of two private CRT formatting records when their cursors point into
the current reserved stack window. Output text and public state still compare
exactly; raw record differences remain recorded.

Every target has a source-based mutation control, compiled as a whole TU with
only the target definition changed. DrawBalloons additionally observes the
allocator entry at signed 16-bit boundaries and rejects the unsigned variant.
The consolidation run passed 11,702 primary paired cases, all 29 mutation
controls, and four allocator boundary observations with two unsigned contrasts.

The current allocator-fixture repair run passes 12,130 paired cases across all
29 domains and their source mutation controls. The previous allocator history
used an invalid master-base/discard-template premise and continued an unfinished
raw allocation. Its finite persistent-history claim is superseded; the four
strict static receipts are unchanged. See [the accepted fixture review](../evidence/canonical/allocator-fixtures/README.md).

These tests corroborate the static conclusion within recorded caller domains.
They do not establish complete driver/backend integration, an independent DOS
link, or full-game runtime acceptance. Historical validation, storage/link
preflight and native integration remain separate checks.
