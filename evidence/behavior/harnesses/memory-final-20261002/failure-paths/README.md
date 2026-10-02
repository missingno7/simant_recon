# Ralloc failure-path supplemental diagnostic

This supplemental bundle retains ordinary return probes and a bounded terminal `Punt` boundary probe. It does not modify or extend the registered live-state-v2 packets. The no-space allocation result is recorded as a `Punt` invocation/nonreturn boundary, never as a fabricated null return.

`report.json` pins the producer, whole-module source, runner, suite, compiler object, linked code, oracle image, Unicorn version, and manifest. The runner and suite copies referenced by the report are also retained in the sibling `../tools/` archive. `negative-omit-punt.c` is only a sensitivity mutant.

To reproduce against the retained pinned execution snapshot, run `python evidence/behavior/harnesses/memory-final-20261002/failure-paths/probe.py` from the repository root with `build/workers/behavior_memory/final-pinned-20261002/snapshot` available. The research-only `PuntBoundaryMachine` stops at the actual Punt entry and does not complete the call or perform ABI/return checks.
