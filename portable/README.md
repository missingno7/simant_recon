# Native SDL3 port

This branch starts from `dos-semantic-oracle-v1` (`66e85041ee54f59774ae0fd5a08b37ffbcf77172`).
The historical `src/`, layout, validation tools and proof packets remain read-only.
Native work lives here. The DOS checkpoint preserves 1,611 EXACT functions and
29 separately registered BEHAVIOR_EXACT contracts; it is not a 100% matching
decompilation.

## Current integration state

The SDL3 executable renders the original scenario-selection resource inside a
resizable 640×350 logical window with nearest-neighbor scaling. Its geometry,
packed bitmap decoding, transparency merge and font metrics have direct DOS
comparison evidence. Scenario selection reaches the original logical event
codes and starts actual resource-backed native world initialization. The
`--newgame-view` mode opens that world directly in the original edit viewport.
The full colony update loop and game UI are still being integrated; this build
does not yet provide a playable game.
The native movement implementation has passed 322,720 direction-selection and
18,440 tile-predicate comparisons against fresh original DOS executions.
Database decoding loads all 840 shipped records, including 205 compressed records.
World generation, ant initialization, water, spider behavior and the original
scenario/window model execute natively. [Proof boundaries](docs/proof-boundaries.md) distinguish
original-DOS comparisons from unit checks and list known corrections in progress.
Missing required services return an explicit failure; they must
not be replaced with no-op hooks to make startup appear complete.

## Build prerequisites

Use MinGW-w64 GCC (this workstation has GCC 12.2.0) and Python 3.10 or newer.
`SIMANT_CC` can select the compiler. SDL3 is a project-local dependency downloaded
from the [official 3.4.16 release](https://github.com/libsdl-org/SDL/releases/tag/release-3.4.16).
The SDK archive is pinned by SHA-256:
`9828bb735cf8a007bcf0ac5aa9f01f3fcb54b7ca67c932e775c905c5d5053a60`.
It is extracted under ignored `build/sdl3-sdk/`; no SDK binaries are committed.

From the repository root:

```powershell
python portable/build.py --setup-sdk
python portable/build.py
build/portable/simant-sdl3.exe --scenario-screen
build/portable/simant-sdl3.exe --newgame-view
python portable/tests/run.py --host
python portable/tools/verify_evidence.py
```

Original resources remain in ignored `assets/`. Their identities are recorded in
`tests/resources/ASSET_SHA256.md`. No original executable or asset archive is
redistributed with the port. A native build receipt records its compiler, SDK,
source inputs, frozen oracle commit and executable hash under `build/portable/`.
The development modes use fixed startup TickCount samples for reproducibility.
They render a static initialized world until the complete simulation is wired.
An optional CMake project is provided for systems with an installed SDL3
development package; this workstation uses the verified MinGW build script.

## Boundaries

- `game/state` stores typed logical state, preserving the original x-major grids.
- `game/simulation` owns 16-bit arithmetic, RNG consumption and game rules.
- `game/resources` decodes resource indexes/storage into owned ordinary bytes.
- `ui_model/windows` owns resource geometry and logical window/object actions.
- `render` draws into an indexed framebuffer without SDL dependencies.
- `platform/host.h` defines host input/presentation/time services.
- `platform/sdl3` implements those services; SDL events do not advance simulation.

The original loop and outstanding native subsystems are tracked in
`docs/simulation-dependencies.md`. In particular, `MacTickCount` is three times the
original logical tick; presentation refresh must not become the simulation clock.
Simulation tests invoke the frozen DOS oracle directly rather than using a second
native implementation as expected output for differential evidence. Unit tests
are labeled separately and do not establish DOS equivalence. Native proof records remain separate
from the frozen historical acceptance registry.
