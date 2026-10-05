# Current canonical simulation differential

Build the current canonical native program first, then run:

```powershell
python portable/tests/native_simulation/run.py --native-build build/current/portable --out build/current/tests/simulation --random-count 128
```

The native lane links the complete object list from the current build receipt.
Its `DoAntMoveY` and `DoAntSimY` implementations are the converted whole canonical
`src/S25/m3BA4.c` translation unit. Their ordinary state, maps, Life grids and
tables are the actual canonical owners in that same native build. The source RNG
is initialized and read through its actual canonical accessors. The oracle lane
executes the locked original DOS functions and their original helpers.

The default corpus has 66 directed and 128 seeded random cases. It covers bounded
surface movement modes 0/1/2, blocked alternatives, occupied Life cells, health
updates, terminal callback order, and `DoAntSimY` health/death and queen RNG
rejection paths on all three planes. It compares declared state and map ranges,
RNG state, and ordered callback names and argument words.

The listed draw, target, sound, message, death and timer observer bodies are
explicit boundaries in both lanes. Their callee side effects are excluded.
Egg creation, nest exit, complete tick histories, platform backends and whole-game
equality remain outside this finite corpus. All compared storage extents retain
their canonical DOS widths, including the two-byte health-warning flag.

Three controls compile the complete current native S25 TU with one scoped source
mutation: change the movement counter step, swap terminal callback coordinates,
or consume one extra RNG draw in `DoAntSimY`. Each must produce a state or callback
discrepancy while completing normally. Reports pin the current program, canonical
sources, generated whole TUs, full native object list, services, fixture files and
oracle, and reject changes during the run.

The fixture has no runtime dependency on archived cases, extracted bodies,
selected-body native implementations, or retired model state providers.
