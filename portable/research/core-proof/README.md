# Whole-tick core proof probe

`original_tick_probe.py` makes a resource-backed world by executing original
DOS `RandWorld`, then calls original `DoAntSim` in the same VM without resetting
the world or the RNG. It saves every state range used by the existing worldgen
comparison plus the tick scheduler's counters, mode points, population and
history arrays. The entry trace records the actual DOS function entries. This is
an oracle fixture generator; it does not report a native comparison or a pass.

Reproduce the current fixture with:

```powershell
python portable/research/core-proof/original_tick_probe.py --cycles 0,31,63
```

The frozen DOS image completes each call for seed `0x5a31`, scenario `0`.
Cycle 0 is the ordinary tick path, cycle 31 reaches `DoSmells`, and cycle 63
reaches both `FeedAnts` and `DoSmells`. At cycle 63 the trace reaches
`Feedback`, `RunTutor`, `SetDefaultWindPrompt`, and `EditMessage`, which need
ordered UI providers in a native harness. The original run reaches gameplay
children such as `DoWater`, `DoAntLions`, `MoveSpider`, `DoPillar`, `DoAntSimA`,
`DoAntSimR`, `DoAntSimY`, and `DoAntMoveY`; these require real stateful native
implementations.

The generated 15-TU source set is sufficient to compile its individual source
files, but a whole-tick executable still has unresolved reachable symbols.
Several are real gameplay dependencies (for example `AddFood`, `MakeBlkQueen`,
`MapToYard`, `processExp`, and list/tile helpers); they cannot be recorded as
presentation providers. The current generator set also omits `src/S08/m35F5.c`,
which defines `AddFood` and `MakeBlkQueen`. `o25_3BA4_1035` (`EnterNest`) remains
an explicit source scaffold in generated `S25_m3BA4.c`; it needs the separately
proven native binding before a path entering it can count. The native
`GetMyRandDirs` and S-RNG adapters exist, but the generated closure must bind
them against this same recovered state and preserve the DOS draw order.

Before claiming any differential result, the harness must compare all changed
game globals, arrays, counters, RNG state, and ordered host intents. A game
symbol that is neither source-defined nor bound to a real native implementation
must stop the run as unsupported. Integer promotions remain an audit item for
the source-reuse compiler output.
