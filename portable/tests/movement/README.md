# Native movement differential evidence

This evidence validates the portable movement implementation against fresh
invocations of the original DOS executable. It is port regression evidence;
it does not replace or extend the frozen historical `BEHAVIOR_EXACT` claim.

The native implementation is in `portable/game/simulation/movement.{h,c}`.
The runner is `run_dos_diff.py`; it builds a Windows shared library with
`C:/msys64/mingw64/bin/gcc.exe` and invokes only the original DOS lane for
expected results. The archived scenario generator is pinned to SHA-256
`f7aad88da70befc902bcc4b8f48670f43df38e90f81e45a59ef4c584090dd360`.
The recorded DOS oracle is SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`, and
the historical manifest is pinned to
`025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`.

`movement-full-322720.json` records 222,720 directed cases plus 100,000
randomized cases (seed `0x1686`). It compares the native return, rotation and
direction outputs, and ordered `TileCanBeMovedOn` query arguments against the
original function and its original helpers. It reports zero mismatches.

`tile-full-18440.json` records 13,440 directed original-helper cases plus
5,000 randomized arbitrary-map cases (seed `0x710ECAFE`). These exercise
surface/nest bounds, terrain thresholds, digging classes, entrance constraints,
and map-byte variation. It reports zero mismatches.

Reproduce both runs from the repository root:

```powershell
python portable/tests/movement/run_dos_diff.py --random-count 100000 --seed 0x1686 --report build/portable/movement-full-322720.json
python portable/tests/movement/run_dos_diff.py --tile-helper --random-count 5000 --seed 0x710ECAFE --report build/portable/tile-full.json
```

The coverage is finite and source-contract scoped. It does not prove all
possible histories, malformed state, invalid direction indices, or arbitrary
map histories; the movement corpus uses the archived controlled setup while
the separate helper corpus varies the direct map bytes and boundary cases.
