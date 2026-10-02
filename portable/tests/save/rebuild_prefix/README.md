# Rebuild prefix differential

This packet compares the original DOS `o09_35F5_0DBB` only through (and stopping before) the actual `SetMyLife` entry against a source-derived native C extraction of the same prefix. The extracted C is generated from `src/S09/m35F5.c` and `src/root/m0250.c`; only `f_0250_0256` is a controlled typed resource-provider boundary. It does not cover `SetMyLife`, `FullCount`, window rebuilding, camera centering, prompts, or whole LoadGame.

Run `python portable/tests/save/rebuild_prefix/run_prefix_diff.py --report portable/tests/save/rebuild_prefix/reports/prefix-<name>.json`. Reports are immutable; the runner refuses an existing report. `lower_source.py --write` creates the source-derived C snapshot once and refuses to replace an existing file.

For the scalar-corrected version, use `run_prefix_diff_v4.py --report` with a
new report path. `lower_source_v4.py` verifies or creates the distinct v4 source
snapshot. The captured input closure covers the listed project inputs; it
does not include a pre/post identity of every compiler subtool or the loaded
Unicorn DLL. The report identifies the compiler command/version and native
binary. Treat this as bounded diagnostic evidence pending that execution audit.

The captured `prefix-smoke-v3.json` compares equal life maps and provider events but is marked MISMATCH because that initial comparator incorrectly required a native “stopped at SetMyLife” field (native code is the mechanically cut prefix). `prefix-full-v1.json` is retained as a DOS-runner diagnostic: its first row executed correctly, but the per-machine stop flag was not reset between cases, so 15 later inputs were never initialized/executed on DOS. These are harness/comparator failures, not semantic mismatches. Reports through `prefix-full-v4.json` use host `int` for some copied source scalars; they remain preserved as historical diagnostics. The scalar-corrected `prefix-scalar-v4-full.json` uses explicit `int16_t` globals, loop locals and overlay parameters, plus explicit little-endian scalar input/output. It also records the per-case DOS stop and final barrier/ground state. All reports remain immutable.

Supported cases require list counts `0..capacity-1` (A capacity 1000, B/R capacity 500) and every source-read coordinate in that plane's grid. Count-at-capacity is rejected because the source's inclusive `i >= 0` loop reads index `ListIndex*`, outside the corresponding array. No data is clamped or repaired. The source loops still execute index zero for count zero, and the input fixture initializes that spare element so this original behavior is compared directly.

The 16-case run includes both terrain-set branches, duplicate-coordinate list entries, poisoned input life planes, the maximum supported count (`capacity-1`), and deterministic randomized valid arrays. It compares all LifeA/B/R bytes, CurGndTileID, Barrier, resource-provider request order/value, and Barrier as observed at provider entry. Negative controls reject count-at-capacity and a coordinate outside the addressed plane. This proves only the extracted prefix on the recorded valid domain.
