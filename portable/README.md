# Canonical SDL3 build

`build.py` consumes the complete current `src/program.json` inventory. It
converts whole canonical C translation units and symbolic assembly data, then
compiles the explicit platform services in `platform.json`. It does not select
historical candidate bodies or apply source correction/storage overlays.

```powershell
python portable/build.py --out build/portable-sdl3
python portable/tests/native_database/run.py --conversion build/portable-sdl3 --out build/native-database
python portable/tests/native_rng/run.py --report build/portable-sdl3/report.json --out build/native-rng
python portable/tests/native_simulation/run.py --native-build build/portable-sdl3 --out build/native-simulation --random-count 128
python portable/tests/runtime/run.py --report build/portable-sdl3/report.json --flow vga
python portable/tests/runtime/run.py --report build/portable-sdl3/report.json --flow save
python portable/tests/runtime/run_load.py --report build/portable-sdl3/report.json
```

Build output must be fresh. Defaults use MinGW GCC under `C:/msys64/mingw64`
and the local SDL3 SDK under `build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32`;
`--cc`, `--sdk` and `--out` override these locations. Game databases/fonts/CFG
are local prerequisites. The SDL3 runtime and hardware BIOS fonts are copied to
the result; historical executable bytes are not native runtime resources.

Run the result from the repository:

```powershell
build/portable-sdl3/simant-canonical.exe
```

The application locates the adjacent resources and runs the converted original
main. The platform application owns SDL lifecycle, presentation, input injection
for tests and host resources; startup dialogs and the simulation remain in game
source. See [runtime checks](tests/runtime/README.md) for fresh writable resource
copies and the Save/Load trace requirements.

`canonical_native_abi/` contains bounded type/ABI conversions: fixed-width words,
near/far pointer spelling, owner views, callbacks and packed wire/native layouts.
Its word-expression pass narrows closed explicitly typed unsigned-word results
before consumers and preserves mixed word comparisons; unknown types and general
integer expressions remain outside that class. Per-TU build receipts record edits.
`whole_program/platform/` implements DOS/BIOS services. The small
`whole_program/algorithms/` files project genuine canonical assembly algorithms
that a native C compiler cannot assemble; they are not an alternative C game
model. Header views and native registries borrow canonical ordinary owners.

Current native execution is a preview with explicit unresolved contracts.
Eleven storage imports still lack complete DOS ownership proof; the canonical
icon Handle slot also has unresolved activation and referent lifetime/extent.
FindIndex's one-past guard is a semantic exception. Window omitted-slot zeroing
has a reviewed shipped-resource/observer domain but differs in raw state.
Unsupported font extents, malformed window bindings and zoom/allocation domains
remain explicit in `platform.json`. Passing build and bounded tests do not close
those issues or establish complete DOS/native equality.

Published historical checkpoints live in Git. Current sources and validations
are described in [the canonical architecture](../docs/canonical-source.md) and
[the consolidation report](../docs/consolidation.md).
