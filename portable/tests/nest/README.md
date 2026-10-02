# Native nest transition differential tests

`run_dos_diff.py` runs the original frozen DOS `o25_3BA4_1035` entry for each case and compares it with the native C transition. The native core uses typed world arrays and explicit `SimRng`; there is no segment emulator in the simulation implementation. Comparisons include MapA/B/R, LifeA/B/R, ExitMapB/R, HoleMapB/R, nest coordinates/type/direction, theme/alarm state, dig summaries, LFSR state, and ordered song, alarm, invalidation, sound, and SRand1 intents.

The shared helpers exposed in `portable/game/simulation/nest.h` are `sim_nest_dig_tile`, `sim_nest_make_new_hole`, and `sim_nest_dig_my_tile`. They are intended for native world generation and queen placement as well as `sim_enter_nest`.

Re-run with:

```powershell
python portable/tests/nest/run_dos_diff.py --dirt-cases 128 --random-count 5000
```

The run executes 809 archived directed source cases, 128 additional center dirt/grass cases, and 5,000 seeded randomized source cases (5,937 total), with zero mismatches. Evidence JSON pins the DOS executable, frozen manifest, case generator, runner, native sources, and compiled DLL. It records a finite differential corpus; it is not a universal proof over every possible DOS memory state. Randomized inputs use the archived suite's fixed seed and the dirt/grass cases exercise the transition's entrance/dig paths with the original SRand1/SRand4 implementations.

The focused 809-case directed result and 937-case directed-plus-dig result are retained beside the larger campaign. The 937-case evidence predates the later random campaign and includes the same native implementation. No behavioral status is asserted here; this is native-port regression evidence against the frozen oracle.
