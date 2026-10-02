# Save/load lifecycle differential, V1

This is a bounded paired execution of the original S09 `LoadGame` and `SaveGame` functions against the native typed lifecycle model in `portable/game/save/lifecycle.c`. The DOS VM runs the actual original entry bodies; CRT file calls, selector/prompt interactions, S09 reset/rebuild helper calls, and post-load UI calls are controlled callbacks. The report captures every normalized callback event, final lifecycle fields, every row's final bytes, compiler/evaluator/source pins, and the actual DOS helper-call arguments.

The 15 deterministic scenarios passed: save selector cancel; use-last overwrite acceptance; overwrite decline/reselect cancel; create failure; write `-1` with close/remove; positive short write; load selector cancel; dirty prompt cancel; save cancel followed by prompt cancel; failed save followed by a second prompt and load attempt; dirty save then load; load open failure; partial read; complete load where the post-rebuild activity value causes `StopSong`; and complete load where the post-rebuild value suppresses it. All complete and partial cases exercise all 307 actual `SaveRec` rows where the source flow reaches them. Full-file payload encoding/decoding is separately covered by the V3 codec/binding packet.

The source row aliases are represented in the native fixture: SaveRec row 141 (`fd_50F6_0EAC`) shares storage with `state.load_mode`, and row 100 (`fd_3D57_07A8[7]`) shares storage with `state.fd_3D57_07A8`, including `[1]`/`fd_3D57_07AA`. The final song decision is queried only after refresh/update/rebuild and observes the current aliased word. The test deliberately initializes that word differently from its post-rebuild value in both directions.

This packet does not certify live filesystem behavior or full game-state reset/rebuild. `o09_35F5_0D7A` and `o09_35F5_0DBB` are explicitly controlled helper boundaries, as are window/UI presentation calls; the report limits its claim to lifecycle ordering, callback arguments/results, names/dirty/load-mode state, and byte-level per-row read/write effects. CRT error-list text is normalized to open/write error classes, while the static read-error and successful-save messages are compared. Reads/writes use native binding bytes directly: endian conversion and whole-file serialization remain the separate V3 codec's responsibility. No filesystem is touched.

Reproduce from the repository root with a new report path (the runner refuses to overwrite an existing path):

```powershell
python portable/tests/save/lifecycle/run_lifecycle_diff.py --report build/workers/save_lifecycle/replay.json
```

The DOS harness/oracle and native DLL remain local build inputs/outputs. Their exact SHA-256 identities, the `gcc -MM` dependency graph with before/after hashes, GCC path/version, Python evaluator pins, and source pair identity are recorded in `paired-report-v1.json`. The DLL itself is not committed; rebuild it from the pinned C sources. Earlier mismatches are preserved in `evidence/precursor/mismatch-13/` and were not overwritten.
