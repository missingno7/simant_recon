# RandWorld differential evidence

These reports compare the native `sim_worldgen_rand_yard` path with a fresh
execution of the original DOS `RandWorld` in the Unicorn-based harness. Each
report contains its exact input rows, compared ranges, source and harness
hashes, oracle identity, per-side observation hashes, and mismatch details.

The original image is `assets/SIMANT.EXE`, SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.
All game helpers and the S-RNG execute from that image. Only the player
selection request and map invalidation are modeled host boundaries.

| Report | Domain | Result | SHA-256 |
| --- | --- | --- | --- |
| `randworld-session-sweep-20261002.json` | 8 cases: scenarios 0/1, seeds `5a31`, `1227`, `52f7`, `7e29` | 0 mismatches | `425b1621d3da2eea2ff515c4b7004a928e411f256de8612d1008929d7716fe7c` |
| `randworld-session-edge-8000-20261002.json` | 2 cases: scenarios 0/1, seed `8000` | 0 mismatches | `610f5936b70b4f3dba5017b98442464be3c89bb96563fe2140ad0de0cfa31ed8` |
| `randworld-session-edge-ffff-20261002.json` | 2 cases: scenarios 0/1, seed `ffff` | 0 mismatches | `8b3125a6be755840f6dae1e55de103cbb6b8d21dbcb6c44402578724707bfa9b` |

These are the current post-setup reports. Each pins
`setup.c` SHA-256 `a9493a4a6b842740177b8da0c57a5619573225780218cfe3a62375647f6ddc50`.
The original `randworld-seed-sweep-20261002.json` and `randworld-edge-*-20261002.json`
files are retained as earlier dated runs; their translation-unit inputs predate
the final `setup.c` preset-order correction and they are superseded by the
`randworld-session-*` reports above.

All cases use black/red nest sizes 1/1, terrain selector 0, and map arguments
11/8. The sine table is placed in a test-owned far arena and referenced by
the original `fd_50F6_0B22` far pointer. The default caller prestate is after
`ClrArrays` and the `RandYard` scalar assignments; poisoned inactive ant
coordinates and the conditional `InitYelloAnt` state are included.

To reproduce a report, invoke `python portable/tests/worldgen/run_dos_diff.py`
for each listed seed with `--scenarios 0,1` and a new output path. The current
seed-sweep report uses base seed `0x5a31`, `--random-count 3`, and
`--random-seed 0x523157`; the edge reports use `0x8000` and `0xffff`.
Reproduction rebuilds
the native snapshot DLL with the GCC path and command recorded in the JSON
report. The report's rows preserve the exact input seeds and per-case hashes.

This is bounded evidence for the recorded domain. It does not claim coverage
of other nest sizes, terrain selectors, scenarios, resource providers, or
non-default `DigOut` paths. The earlier `default-smoke7.json` build-only
diagnostic used an invalid fixture which wrote sine-table values over the
far-pointer symbol; it is not evidence and is intentionally not retained here.
