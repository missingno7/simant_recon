# Next9 SaveRec binding validation (V4 closure refresh)

This packet refreshes V3's 307-row SaveRec source-address sentinel experiment and closes its transitive native-source pin gap. It is diagnostic evidence only; it does not register or claim production save behavior.

The native build uses the unchanged `next9_bindings_v3.c`, `next9_bindings_v3.h`, and row include. The independently derived sentinel catalog contains 410 typed state members; original DOS `SaveGame` executed 307 writes and produced a 48386-byte stream. The two positive native runs (host little endian and forced big endian) matched that stream exactly. The three negative controls failed as intended: swapping rows 48/49, widening row 48, and treating raw row 99 as numeric.

Unlike V3, V4 records GCC `-MM` local dependency closures for all five compiled variants. The closure includes `portable/game/save/legacy_codec.h`, an unconditional include of `legacy_codec.c` that V3's manually assembled pins omitted. Active C/header/include inputs, Python producers and validators, GCC and MSC compiler files, original executable, all root assets, and DOS harness inputs are pinned before/after. V3 packet files and `run_next9_bindings_v3.py` are hashed before and after and were required to remain unchanged.

Reproduce from the repository root with `python portable/tests/save/run_next9_bindings_v4.py`. It refuses to overwrite this packet and requires the reviewed Next9 provenance receipt pinned in `source-pins.json`. The profile is read-only input; no Next9 recovery or binding generator is executed. A V4-specific copy of the original DOS probe writes only under `build/workers/savegame_sentinel_v4`. The runner obtains GCC `-MM` closures, compiles/runs the two positives and three negatives, and writes a fresh V4 directory only after every assertion succeeds.

The contract remains bounded to the recorded source-address sentinel state and exact 307 DOS writer calls. It is not a general save lifecycle, file-system, or arbitrary runtime-state proof.
