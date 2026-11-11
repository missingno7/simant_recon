# SimAnt reconstruction

A matching reconstruction of the 1991 DOS game lives in `src/`; `src/program.json` is
its single inventory for both the DOS build and the SDL3 port.

The original `SIMANT.EXE` is the only oracle, and the goal is to rebuild it completely.
1,617 of 1,640 game functions are byte-exact today; 23 are only behaviour-reviewed, and
data ownership, layout and the original link are not reproduced yet
([progress](docs/progress.md)). `dos/build.py` links a working DOS build from this source
whose recorded replays matched the original
([receipt](evidence/canonical/validation/canonical-dos-acceptance.json)); it is a test
vehicle, not an oracle. The SDL3 port lowers the same source mechanically
([port method](docs/port-repair.md)). Working rules are in [AGENTS.md](AGENTS.md).

## Build and validation

Local prerequisites: Python 3.10+, Capstone 5.x, the hash-pinned period tools
listed in `layout/toolchain.json`, MinGW GCC, and SDL3 under
`build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32`. Original game resources
remain ignored in `assets/`; identities are in `layout/oracle.lock.json`.
[Behavioral validation](docs/behavioral-proof.md) explains the pinned Unicorn wheel.

```powershell
python tools/validate.py
python tools/canonical_behavior.py --count 16
python dos/build.py --jobs 8 --link
python portable/build.py
build/current/portable/simant-canonical.exe
```

The DOS command links `build/current/dos/link/SOURCE.EXE` from canonical source alone:
no original executable bytes. Its data layout is ours, not the original's (73 storage
units and 30 unattributed bytes are open debt), so it is not a match of the image.
`dos/acceptance.py` replays a scenario on the original and on this build and compares
simulation state, saves and sound port traffic.
Both build paths use zero original executable fallback. [Portable validation commands](portable/README.md) cover
resources, RNG, simulation, VGA and Save/Load with their supported scopes.
Bounded DOS checks now save all 307 records in both executables and load the same
original save back into paused Full Game. [Evidence and limits](docs/dos-closure.md)
separate these observations from complete state equivalence and closure.

Default runners rotate replaced outputs into ignored `to_delete/` and recreate
one deterministic `build/current/` target. Explicit experiment outputs must be
fresh, under `build/workers/<worker>/<task>/` or `build/scratch/`.
Reusable dependencies live in `build/deps/`. `to_delete/` is a manual review
safety net and is excluded from Git, production discovery and validation.

## Reconstruction workflow

```powershell
python tools/context.py FUNCTION
# Draft a whole module in build/workers/NAME/TASK/.
python tools/search.py FUNCTION build/workers/NAME/TASK/module.c
python tools/promote.py build/workers/NAME/TASK/module.c --module UNIT:SEG --claim FUNCTION --verify-only
python tools/promote.py build/workers/NAME/TASK/module.c --module UNIT:SEG --claim FUNCTION
python tools/validate.py
python tools/repository.py --write-status
```

`promote.py` is the sole canonical writer. Exact acceptance checks complete
extents, symbolic fixups, relocations, private data and accepted peers. Strict
semantic claims also require full static receipts and differential mutation
controls. Similarity and bounded passing tests cannot replace those gates.

Durable technical references: [compiler rules](docs/codegen-rules.md),
[TU evidence](docs/tu-evidence.md), [toolchain](docs/toolchain-fingerprint.md),
[EXE format](docs/exe-format.md), and [naming policy](docs/cross-version.md).
