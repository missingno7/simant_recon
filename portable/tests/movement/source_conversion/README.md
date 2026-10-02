# GetMyRandDirs source conversion probe

This isolated probe mechanically extracts the `o25_3BA4_1686` function body
currently fenced as a `SCAFFOLD` in `src/S25/m3BA4.c`, then applies
`recover_source.extract_named_function` and `recover_source.transform`. The
only target-body changes are its far/near and scalar-width translations and
removal of the two scaffold-fence comments. The output translation is pinned
in `source_identity_v1.json` and is not overwritten by the extractor.

The current body remains a scaffold draft. The repository separately registers
`o25_3BA4_1686` as `BEHAVIOR_EXACT` using
`evidence/behavior/functions/o25_3BA4_1686/module.c`; that reviewed source is
not the scaffold extracted here. The frozen `S25:3BA4` manifest also lists
`o25_3BA4_1686` as scaffold and makes no per-function `EXACT` claim. The
identity sidecar records both facts; this probe changes neither registry.

The two direction/distance dependencies are the source-converted `GetDir` and
`GetDis` bodies from `src/root/m0BE8.c`, behind narrow logging aliases for the
DOS helper entry names. `TileCanBeMovedOn` in the original lane executes the
actual DOS helper. The native lane calls the already separately DOS-tested
`sim_tile_can_be_moved_on` implementation with typed `SimWorldTiles` arrays.
The scenario writer copies its actual map-byte writes into those arrays, and
the direction-step bytes come from the frozen original image. The native tile
query list is checked against the scaffold's loop and previous-cell exclusion;
the original DOS helper trace is not intercepted for this run.

Run the complete original-DOS comparison from the repository root:

```powershell
python portable/tests/movement/source_conversion/extract_source.py
python portable/tests/movement/source_conversion/run_source_conversion_diff_v3.py `
  --random-count 100000 --seed 0x1686 `
  --report portable/tests/movement/source_conversion/source-conversion-dos-diff-v3.json
```

The runner defaults to the same 222,720 directed cases and 100,000 randomized
cases as the frozen movement campaign. A smaller `--limit` can be used only for
development smoke tests; it does not replace the full write-once report.
Passing this probe compares the extracted scaffold's return and two pointed
words against fresh original DOS executions in the stated corpus. It does not
revise historical byte claims, the existing `BEHAVIOR_EXACT` packet, or the
production adapter.

`source-conversion-dos-diff-v1.json` is retained as a diagnostic-only first
attempt. Its DOS outputs all matched through the recorded stop case, but its
extra `source_contract_model` check treated an out-of-bounds neighbor as the
scenario's abstract movable bit. V2 replaces that invalid check with the
source loop's previous-cell query-shape check and uses a distinct native-library
filename so the V1 binary identity remains reproducible.

The V2 runner is retained. Its first smoke diagnostic was not saved as a
standalone receipt: it checked query shape
even for coincident targets, where the source returns before any movement
helper call. V3 accounts for the source `int` narrowing of the initial `GetDis`
result before deciding whether the loop is entered.

V3 records 322,720 comparisons with zero output or query-shape differences.
Its 18 source-input pins match before and after execution. The packet records
the GCC identity but does not provide a complete pre/post Python, Unicorn, and
compiler-subprogram identity closure. It remains an isolated finite diagnostic;
production conversion admission and actual shared-state integration are separate.
