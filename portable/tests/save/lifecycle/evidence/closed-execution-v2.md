# Closed execution identity for the save/load lifecycle differential, V2

This is a fresh 15-case run through the unchanged semantic runner `run_lifecycle_diff.py`. It retains V1 unchanged and snapshots the execution closure before `load_native()`/`PreparedPair` and after all paired original-DOS/native cases. The full semantic rows and callback/state/row-byte results are embedded in `closed-execution-v2.json`.

V2 adds the actual GCC subordinate compiler/link tools resolved by the GCC driver (`cc1`, `collect2`, `as`, and `ld`) and the Unicorn native runtime `unicorn.dll`, each captured before and after execution. It also retains all V1 closure inputs: 213 loaded Python module files, Python executable/version, GCC driver/version and `-MM` inputs/output, the MSC 6.00AX tool files and pinned headers, DOSBox-X, all local assets and oracle, and source/evaluator/profile files. The run passed all 15 scenarios with no changed inputs, no late-loaded Python modules, no missing files, and all expected compiler pins matching.

The run is diagnostic and bounded to lifecycle ordering, callback arguments/results, lifecycle fields, and raw per-row effects. File/UI/reset/rebuild helpers are controlled boundaries; it does not certify live filesystem operations, general disk decoding, endian conversion, or full game-state rebuild.

Reproduce with a new output path (the runner refuses to overwrite existing reports):

```powershell
python portable/tests/save/lifecycle/run_lifecycle_closure_v2.py --report build/workers/save_lifecycle/replay-closed-v2.json
```
