# Native DoAntMoveY differential tests

`run_dos_diff.py` invokes the frozen DOS `DoAntMoveY` entry in a fresh Unicorn16 machine for each input, then runs the native typed implementation through `native_adapter.c`. The harness compares observed scalar state, movement/nest maps, Life maps, exit-map results, B-ant list state, and ordered logical callback arguments. The DOS oracle remains the expected behavior; native runs do not consume a separate RNG stream.

The archived `evidence/dos-differential-5000.json` records a deterministic 5,000-case corpus (seed `0xD04A`), spanning movement modes 0–4 and surface/B-nest starting planes, with randomized valid obstacles, occupied cells, path delay, direction/rotation state, and ant type. Its oracle SHA-256 and historical manifest SHA-256 identify the inputs used. Re-run with:

```powershell
python portable/tests/yellow/run_dos_diff.py --count 5000 --seed 0xD04A --report build/portable/yellow-diff.json
```

This is a bounded differential result, not a universal behavioral-equivalence claim. It does not exercise all transitions and excludes branches whose gameplay services remain explicitly unimplemented and fail closed in the native API, including `TryMyDropOrLift`, target removal, `ExitNest`, and selected population/alarm side effects. Extend directed inputs and close those services before making a broader claim.
