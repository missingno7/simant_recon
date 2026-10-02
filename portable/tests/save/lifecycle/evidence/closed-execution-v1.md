# Closed execution identity for the save/load lifecycle differential

This is a separate 15-case paired run using the unchanged semantic runner `run_lifecycle_diff.py`. The wrapper snapshots the execution inputs before calling `load_native()` or constructing `PreparedPair`, then snapshots them again after all original-DOS and native cases finish. The full semantic case results are embedded in `closed-execution-v1.json`; the original `paired-report-v1.json` remains unchanged.

The before/after closure records include all 213 loaded Python module files (including the Unicorn package), Python executable/version, GCC executable/version and GCC `-MM` command/output/dependency hashes, the MSC 6.00AX compiler tool files and 55 pinned include files, DOSBox-X runner, the oracle and all 16 local asset files, and repository source/evaluator/profile inputs. The recorded pins all match, there are zero input changes, and no Python module was first loaded during execution.

All 15 scenarios pass: 6 save and 9 load cases, including partial read and complete load with both post-rebuild StopSong outcomes. Native build hash, prepared-pair object/link/oracle identity, scenario callback traces, final state, and raw row-byte effects are in the embedded semantic report. The exact native DLL is locally retained/ignored and identified by SHA-256; the report and pinned source/compiler inputs permit rebuilding it.

This remains a bounded lifecycle-boundary diagnostic. File and UI operations plus the source reset/rebuild helpers are controlled callbacks; the cases compare ordering, callback arguments/results, lifecycle state, and raw per-row bytes. It does not establish live filesystem semantics, endian conversion/whole-file codec behavior, or full game-state reset/rebuild behavior.

Reproduce from the repository root using a new report path (existing reports are never overwritten):

```powershell
python portable/tests/save/lifecycle/run_lifecycle_closure.py --report build/workers/save_lifecycle/replay-closed.json
```
