# Recovered EnterNest adapter evidence

The generated S25 translation unit calls the historical void entry `o25_3BA4_1035`. `portable/game/recovered/nest_adapter.c` provides that entry and bridges active recovered TLS globals to `sim_enter_nest`.

The adapter maps source-backed x-major MapA/B/R, ExitMapB/R, LifeA/B/R, HoleMapB/R, terrain and player fields; theme clock/index; alarm state/indicator; map invalidation bounds; entrance coordinates; and historical digging sums/counts/averages. Each is imported from the active recovered TLS binding and exported only after a successful transition. The `SimNestRuntime` is temporary transition state. The adapter binds the caller's `SimRng` and leaves it bound until the enclosing recovered tick releases it.

`nest-adapter-differential.json` records 937 fresh original-DOS `EnterNest` executions passed through the `RecoveredState` bind/import/export adapter, with zero mismatches. It includes archived directed cases and 128 dirt/grass fixtures; original SRand1/SRand4 helpers execute in the DOS lane. The report pins the DOS oracle, manifest, generated state/provenance, native sources, case runner, and compiled library.

The generated-core link probe with this adapter resolves `o25_3BA4_1035`; it still fails on 358 separate platform/service references, so this does not yet establish a complete generated `DoAntSim` tick comparison.
