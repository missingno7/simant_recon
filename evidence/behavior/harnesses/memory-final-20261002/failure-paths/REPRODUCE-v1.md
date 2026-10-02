# Fresh-bootstrap reproduction, revision 1

Run from the repository root with the documented pinned compiler toolchain, Unicorn 2.1.4 runtime at `build/behavior/deps`, and original `assets/SIMANT.EXE` present:

```powershell
python evidence/behavior/harnesses/memory-final-20261002/failure-paths/reproduce-v1.py
```

The producer verifies the sibling memory harness archive index, every archived runner component, exact archived suite/source, manifest/function/symbol/toolchain hashes, the Unicorn runtime tree, and original executable hash before importing archived code. It bootstraps those archived runner files plus read-only root layout inputs under `build/workers/behavior_memory/repro-v1/bootstrap-v4`; it uses the original executable directly from `assets/SIMANT.EXE` and never copies it. Each run writes a new timestamped report under `build/workers/behavior_memory/repro-v1/runs/` and refuses output overwrite. The accepted `README.md`, earlier producer/report, registered packets, and registry are preserved.

The retained run is [report-repro-v1.json](report-repro-v1.json); pins and hashes are in [repro-v1-index.json](repro-v1-index.json). The no-space case is an actual `Punt` invocation/nonreturn boundary in both lanes. It is not represented as an allocation result.
