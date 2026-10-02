# DOS semantic oracle work

The 2026-10-01 phase change adds behavioral proof for the remaining hard tail.
It does not change a historical acceptance gate or turn an inexact contribution
into exact ownership. The historical checkpoint is dos-semantic-oracle-v1; its
[freeze report](dos-semantic-oracle-v1.md) records validation and residual debt.

## Categories

**EXACT** remains governed by `promote.py` and `layout/manifest.json`: bytes,
extent, symbolic fixups, relocations and required order, private data, accepted
peers, and historical toolchain evidence. Existing claims remain unchanged.

**BEHAVIOR_EXACT** requires a reviewed function contract and reproducible
differential execution of the original DOS function and the reconstructed C.
The evidence must identify initial-state domains, observables, dependency
boundaries, case counts, seeds, zero unexplained mismatches or execution errors,
and source-based negative controls. A passing modeled boundary is insufficient
unless its observable contract is itself justified. Simulation receives the
strongest state and RNG checks. A finite test domain and its limits must be
stated; randomized testing does not imply exhaustive universal verification.

**UNRESOLVED** covers every function without either accepted proof. Diagnostic
similarity and exploratory passing suites cannot change this status.

The separate behavioral registry does not own historical bytes. Its function
count must never be added to the byte-exact coverage count. Historical codegen,
data/layout, and RTLink debt retain their own accounting.

## Shared execution framework

`tools/behavior.py` reads the immutable, hash-locked original EXE into isolated
16-bit Unicorn VMs. It compiles a whole-module candidate through the established
MSC harness and first checks all already accepted peers and private data. The
candidate object is symbolically linked in a separate execution arena, preserving
its entire code segment. Defined relative calls use that arena; non-target module
entries delegate to original helpers, so scaffold implementations never execute.
This research linker never modifies an object, production binder or hybrid image.

RTLink vectors load the original overlay bytes in the VM. Overlapping overlay
calls restore the previous image at return and invalidate translated code caches.
The manager/linker reconstruction remains separate historical proof debt.

Each case initializes arguments, registers, memory and an independent callback
state. Each side starts from the same original state. Comparison includes declared
return values and ranges, ordered helper/callback arguments, changed global state
at observed calls, actual ordered IN/OUT operations, and final values at the union
of all non-stack write addresses. Caller-preserved registers and stack cleanup
are checked independently against the ABI, even when both executions fail alike.
Execution budgets, unknown interrupts and unmodeled IN ports fail closed.

Stack locals and volatile register assignments are implementation details unless
passed across an observable boundary. A callback receiving a pointer to a local
must compare its pointed semantic contents with a documented projection. This
does not permit dropping argument values, writes or call order. Dead stack stores
can differ if their values never flow into an observable effect. Synthetic runner
unit programs are plumbing controls, never game reconstruction evidence.

`Callback(..., handler=None)` records a real helper entry and executes the original
helper. Explicit handlers model a contract boundary. Model state must live in the
per-machine `state` or VM memory; a mutable closure shared between sides is invalid.
Return width, register arguments and callee stack cleanup belong to each contract.

The original CRT's `sprintf` and `vsprintf` retain private stream records that
can contain expired stack-buffer pointers after a call. The reviewed proof in
`evidence/behavior/runtime/format-cursors/format_cursor_proof.json` permits a
typed comparison of these two records only: cursor advancement from the buffer
base and remaining capacity. It applies only when both pointers refer to the
current reserved stack window. All output text and public state still compare
exactly, and the ledger retains the raw record bytes and differences. Original
runtime member ownership, defining stores before reads, different stack depths,
and stale-record poisoning support this boundary. This rule does not change
historical byte acceptance or permit arbitrary memory exclusions.

## Dependency and reproduction

Unicorn is research-only. The historical validation still runs without it; it is
required to reproduce a behavioral suite. On this Windows x64 Python runtime:

```powershell
python -m pip download unicorn==2.1.4 --only-binary=:all: --platform win_amd64 --python-version 310 --no-deps --dest build/behavior/dependencies
python -m zipfile -e build/behavior/dependencies/unicorn-2.1.4-cp37-abi3-win_amd64.whl build/behavior/deps
python -m unittest discover -s tests -p test_behavior.py -v
python tools/behavior_suites/small_contracts.py all --negative-controls
python tools/behavior_suites/lists.py --count 10000
```

The wheel SHA-256 is
`d7107500c64ce5c168fbff6bef9485b5db1350050036f4cea568650cf8bdbdf5`.
Original game and compiler binaries remain ignored local prerequisites.
Run records pin the source, object, linked code, imported harness snapshot,
oracle, historical manifest, compiler profile and flags. Suite code and the
contract review must also be pinned before behavioral registration.

The baseline inventory is in `work/takeover/behavioral-oracle/`. Exploration stays
in worker directories; only reviewed proof and source snapshots belong in
`evidence/behavior/`. Prior compiler searches and negative evidence remain intact.

## Freeze and port gate

The oracle tag requires all game behavior closed, including simulation-critical
suites, reviewed data/layout debt, full historical validation, a fresh byte-identical
hybrid, committed behavioral evidence and explicit remaining historical proof debt.
The reviewed checkpoint is tagged dos-semantic-oracle-v1. No claim of a 100%
matching decompilation is made.

After that checkpoint, SDL3 work starts on a separate branch, preserving the frozen
historical sources. The first port reproduces the DOS presentation in one SDL3
window. Platform video/input/timing/memory/file/audio interfaces remain separate
from game rules. Logical simulation ticks remain independent of presentation rate.
The DOS oracle and these contracts continue to protect portable behavior.
