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
An explicit recovered-core build runs the original colony update loop through
the native SDL host. The interactive game UI is still being integrated; this
build does not yet provide a complete playable game.
The native movement implementation has passed 322,720 direction-selection and
18,440 tile-predicate comparisons against fresh original DOS executions.
Database decoding loads all 840 shipped records, including 205 compressed records.
World generation, ant initialization, water, spider behavior and the original
scenario/window model execute natively. [Proof boundaries](docs/proof-boundaries.md) distinguish
original-DOS comparisons from unit checks and list known corrections in progress.
Missing required services return an explicit failure; they must
not be replaced with no-op hooks to make startup appear complete.

The explicitly selected source-reuse profile has passed three 256-tick
consecutive differentials against DOS (768 ticks total). Every tick compares
370 nonpointer globals, both RNG states, and ordered host callback arguments.
The current [next7 tick proof](research/core-proof/original-256-tick-summary-next7-captured370-20261002.json)
records the exact profile and finite domains. It excludes the 41 next7 fields
absent from those preserved captures. A separate resource-backed
NewGame comparison covers 146 source ranges and both RNG output streams,
without hydrating the native session from a DOS memory snapshot. These checks
do not certify the remaining interactive host services; the live integration
build is still explicitly diagnostic.

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
python portable/tests/windows/render/evidence/fetch_bios_reference.py
python portable/build.py
build/portable/simant-sdl3.exe --scenario-screen
build/portable/simant-sdl3.exe --newgame-view
python portable/tests/run.py --host
python portable/tools/verify_evidence.py
```

An explicit generated profile may be linked with
`python portable/build.py --core-profile build/workers/recovered_source_next7/generated`.
First follow the [profile recipe](docs/recovered-source-next7-recipe.md) to
recreate the reviewed generated inputs. The build checks the frozen historical
checkpoint and recorded source/profile identities, and keeps the generated
modules' warning policy separate from strict native host compilation. It does
not promote a diagnostic profile into a behavioral acceptance claim.

```powershell
build/portable/simant-sdl3.exe --live-game
build/portable/simant-sdl3.exe --live-newgame --ticks 32
```

The first command starts at scenario selection; the second runs a bounded live
NewGame. Simulation uses the source logical tick schedule independently of
presentation refresh. Unsupported host services stop with the source service
name. The audio driver remains disabled while its complete native backend is
being reconstructed.

The live prototype supports quick left clicks in the Edit map area and the
source double-click command. Shift+0 (`)`) toggles pause; Shift+1 through
Shift+4 (`!`, `@`, `#`, `$`) select speed. Ctrl+numeric-keypad directions move
the camera one cell on each new key press; held-key repeat cadence is still
unverified. Menu text/state and its BIOS-font bar are rendered from the actual
SHARED resource. The nest overview uses the DOS selector-to-pixel conversion
and draws behind the front Edit window. The source yellow-ant key handler is
connected; supported and unhandled keys retain its logical result. Other
interactive UI routes remain unfinished. A bounded SDL test enters the source
game-over flow, dismisses its window, selects scenario 0x0202, and returns
through source NewGame to a simulation tick. The natural game-over trigger,
tutorial/load/save/quit routes, and complete control-window composition still
need integration checks. A separate natural-trigger host test reaches game
over at completed tick 2,879 after physical Shift+4 selects the source's fastest
speed. It dismisses EndGame, restarts scenario 0x0202, and continues to tick
3,798 before a test-only Quit event. This is a finite live-host check. The
retained SDL event tests and DOS/native click
comparison state their exact coverage in [proof boundaries](docs/proof-boundaries.md).

Original resources remain in ignored `assets/`. Their identities are recorded in
`tests/resources/ASSET_SHA256.md`. No original executable or asset archive is
redistributed with the port. A native build receipt records its compiler, SDK,
source inputs, frozen oracle commit and executable hash under `build/portable/`.
The development modes use fixed startup TickCount samples for reproducibility.
`--scenario-screen` and `--newgame-view` are static presentation modes;
`--live-game` and `--live-newgame` require the explicit recovered-core build.
BIOS font IDs use the pinned DOSBox reference-host tables generated under
`build/`; their source/license identity is retained there. They are a presentation
choice, with separate controlled glyph-provider tests, not an original BIOS claim.
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
