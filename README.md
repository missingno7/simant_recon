# SimAnt reconstruction

The best reviewed reconstruction of the 1991 DOS game lives in `src/`.
`src/program.json` is the single source inventory for both historical DOS and
SDL3. Published checkpoints remain immutable; active reconstruction is corrigible.

The SDL3 executable runs the converted original main as a bounded preview.
Independent DOS linking remains blocked. See [current status](docs/status.md),
[architecture](docs/canonical-source.md), and [cleanup results](docs/cleanup.md).

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

The DOS command currently reports an explicit link refusal. It uses zero original
executable fallback. [Portable validation commands](portable/README.md) cover
resources, RNG, simulation, VGA and Save/Load with their supported scopes.

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
