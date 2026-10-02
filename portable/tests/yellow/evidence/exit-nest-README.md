# ExitNest transition evidence

The typed native `sim_exit_nest` transition is in `portable/game/simulation/exit_nest.c` and is called by native `DoAntMoveY` when movement reaches the top row of either nest plane. It uses the shared nest mutation API for missing holes and emits logical song intent through the nest trace.

- `exit-nest-differential-128.json` records 128 fresh executions of DOS `S25:3BA4:114E` against the native leaf: 128 matched, 0 mismatches. It varies both nest planes, existing/generated entrance holes, single ant/queen footprint, surface terrain/obstacles, and the controlled theme-tick boundary. Its requested target plane is the surface (plane 1); this does not establish the other target-plane branches.
- `doantmovey-with-exit-nest-differential-5000.json` records the 5,000-case native-vs-DOS parent-function campaign after integration. Its first 16 cases are directed exit transitions spanning both planes, hole cases, ant types, and theme timing; the remaining corpus is the seeded movement corpus.

Both reports pin the frozen DOS oracle SHA-256, historical manifest SHA-256, native library SHA-256, compiler command, and source hashes. The direct suite compares return/status, final watched world and runtime state, RNG state, movement/tile query trace, and TickCount/song callbacks. The integrated suite compares the parent function's watched maps, Life arrays, ant lists, globals, RNG state, and selected sound/edit callbacks. They are bounded differential evidence over the recorded fixtures, not a universal behavioral-equivalence claim.
