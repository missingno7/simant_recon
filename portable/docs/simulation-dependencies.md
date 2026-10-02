# Native simulation dependency boundary

This note maps the frozen DOS startup/game loop to the current native simulation code. It is a source-derived dependency map, not a claim that the game is playable or that the native port has a complete simulation tick.

## Original loop and clock

The DOS entry loop is `main` in [`src/root/m15F8.c`](../../src/root/m15F8.c#L93). After startup and `NewGame(1)`, each iteration performs, in order:

1. Check the window-lock invariant, increment the frame counter, run `f_0000_046F`, increment a frame statistic, and run the empty `f_15F8_0313` hook.
2. Read `MacTickCount()` as the current deadline. Run `DoAntSim()` only when `fd_50F6_047E == 0` or (`fd_50F6_0AA0 != 0` and `fd_50F6_105E < 10`). When simulation runs, add `fd_3D57_07CE[fd_3D57_07CC]` to that deadline.
3. Except at speed index 3 on three of every four frames, update open map/yard/edit windows and pump `f_00F8_01BE()` until `MacTickCount()` reaches the deadline.
4. Always pump `f_00F8_01BE()` once more and advance `fd_50F6_0A9C` modulo 64.

The selector is initialized to 1. The relevant bytes in the data object at `fd_3D57_07CC` are `01 00 15 00 07 00 00 00 FF FF 00 01 02 03`; `main` treats the word at offset `+2` as the delay array, so selected index 1 yields delay 7 in `MacTickCount` units. This is the source-level schedule; do not infer presentation refresh rate from it.

`MacTickCount` in [`src/root/m00F8.c`](../../src/root/m00F8.c#L159) is exactly `TickCount() * 3`. `TickCount` in [`src/root/m1B73.asm`](../../src/root/m1B73.asm#L820) reads a 32-bit counter incremented by the hooked INT 08h handler at [`m1B73.asm`](../../src/root/m1B73.asm#L851). The counter can be paused by the timer hook, and its interrupt path also handles keyboard/mouse cursor work. The native `game/timing.c` models that counter separately from presentation and the game's pause gate. It converts host elapsed time through an explicitly assumed rational PC PIT clock and the source audio driver's divisor/chaining interval. Controlled differential tests inject identical logical clock values into both implementations; rendering never advances simulation state.

The two apparently opaque loop calls are platform work:

- `f_0000_046F` in [`src/root/m0000.c`](../../src/root/m0000.c#L204) checks a pending sound request, conditionally stops the current song, advances song data when present, and calls `f_0000_00DE`. Keep this in an audio/event adapter.
- `f_00F8_01BE` in [`src/root/m00F8.c`](../../src/root/m00F8.c#L108) pumps `win_Events`, other input/dialog conditions, and cursor-edge scrolling. It is not a simulation callback and should sit at the host event boundary.

Thus one source simulation tick is gated by game state and followed by host/UI work. A portable loop should expose the same logical gate and schedule inputs, while allowing presentation to run independently. It must not let a render-frame count silently become the simulation tick count.

## New-game path

The DOS `NewGame` implementation is [`src/S15/m384C.c`](../../src/S15/m384C.c#L263). It obtains a scenario through `DoScenario`, sets scenario/game globals, exits any active life-transfer/target modes, sets the default wind prompt, and invokes `RandYard`. It then establishes default windows, applies plane selection, possibly starts the tutorial, centers the edit view on `MeLocX/MeLocY`, and updates the edit window. Only the world/state portion belongs in the portable simulation core; dialogs, windows, and tutorial presentation remain adapters/UI model.

The current native orchestration is [`portable/game/simulation/worldgen.c`](../game/simulation/worldgen.c). It composes real setup, yard, terrain, nest, spider, ant-list, population and player initialization code. Its required resource/control geometry hooks are platform boundaries. The original startup seeds the RNG streams once from supplied TickCount values; NewGame preserves them. The 192-entry per-yard seed table also persists between games.

The dependency chain to an actual generated starting world is:

```text
host supplies scenario + logical tick samples
  -> sim_worldgen_start_new_game
     -> clear arrays / reset scenario / setup yard resources
     -> initialize ant state
     -> generate the world (RandWorld)
        -> initialize the player/yellow ant (InitYelloAnt)
     -> copy player plane/location into map focus
```

`RandWorld` and player initialization now have native implementations. Twelve full RandWorld state comparisons against DOS pass for the recorded default-yard domain. The movement, nest, water and spider modules have separate original-DOS differential reports. Startup resource composition is being integrated through a real session; those module proofs do not establish a complete NewGame UI or a full simulation tick.

## One simulation update

The DOS `DoAntSim` body is [`src/root/m0894.c`](../../src/root/m0894.c#L174). It increments/wraps `Cycle`, advances the global simulation counter, conditionally clears mode-pop state, calls `FeedAnts` every 64 cycles and `DoSmells` every 32, then performs the ordered world/colony update:

```text
water/weather and periodic world updates
ant scent/pheromone work (odd cycles)
yellow/player and mode bookkeeping
DoAntSimA -> black-colony ants
red-colony update
DoAntSimR -> red ants
DoAntSimY -> yellow/player ants
mode population tally
DoAntMoveY -> movement and tile effects
late world/update callbacks, optional sound/UI notification
```

Those are real subsystems, not replaceable no-op hooks. `DoAntSim` touches cycle and mode counters, map/tile state, food/health, pheromone grids, multiple ant lists, player state, and callbacks for combat, death, digging, food, and resource effects. The native [`SimGameWorld`](../game/state/world.h) already has typed storage for a subset of these arrays and counters, while `movement.c` supplies low-level movement logic. There is not yet a complete native `DoAntSim` composition or a contract-complete world state for the full DOS call chain.

## Smallest honest native milestone

Current modules execute real world generation, resource decoding, map/life tile composition, RNG, nest transitions, water and spider behavior. The tests under `portable/tests/` establish their recorded module contracts. The source-reuse work additionally compiles large colony modules against shared native state, but remains outside production until its remaining dependencies and arithmetic adaptations are reviewed.

The `--newgame-view` mode now executes **NewGame world initialization and presentation** with actual assets in the source edit viewport. The complete **DoAntSim tick** is being connected through source reuse and checked against original DOS global-state snapshots. Until that comparison and host integration pass, this remains a native integration build. UI/event/audio functions in the DOS loop belong behind explicit host adapters; silent substitutes for game logic cannot establish a running faithful game.
