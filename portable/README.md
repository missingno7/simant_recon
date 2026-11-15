# Canonical SDL3 build

The approved [enhanced Windows design](../docs/enhanced-mode.md) and
[phase 0 API/verification contracts](../docs/enhanced-mode/contracts.md) now live
in the repository. `SIMANT_ENHANCED_CONTRACTS=1` enables copied semantic
publications and the discrete action executor; it does not enable a new UI.
The existing `--windows` hybrid still has strict phase 1 rebirth and phase 3
activation-click expected failures. Inspectors in the approved mode are always
live; native layouts and immutable art remain later phases. Register
`portable/tests/enhanced/run.py` and `portable/tests/enhanced/invariance.py`
after the fresh native build, using `--build BUILD --out FRESH_PATH` for each.

`build.py` consumes the complete current `src/program.json` inventory. It
converts whole canonical C translation units and symbolic assembly data, then
compiles the explicit platform services in `platform.json`. Lowering classifications and exception deletion conditions
are in `layout/repository.json`. It does not select
historical candidate bodies or apply source correction/storage overlays.

```powershell
python portable/build.py --out build/current/portable
python portable/tests/native_database/run.py --conversion build/current/portable --out build/current/tests/database
python portable/tests/native_rng/run.py --report build/current/portable/report.json --out build/current/tests/rng
python portable/tests/native_simulation/run.py --native-build build/current/portable --out build/current/tests/simulation --random-count 128
python portable/tests/runtime/run.py --report build/current/portable/report.json --flow vga
python portable/tests/runtime/run.py --report build/current/portable/report.json --flow save
python portable/tests/runtime/run_load.py --report build/current/portable/report.json
python portable/tests/runtime/run_edge.py --report build/current/portable/report.json
python portable/tests/audio/run.py
python -m portable.tests.acceptance.run
```

The upper-layer regression runs sound-off gameplay (18 lanes), sound-on
gameplay (18 lanes), and playback (22 lanes) on the shared program-read clock.
Every lane must have equal state, exact checkpoint frames and raw audio commands;
playback also requires exact ordered music events, metadata, decoded and emitted
bytes, with a 1 ns sample timestamp bound. Missing references fail the check.
`tools/validate.py --upper-tests` reaches the same driver through the existing
test bridge. The two narrow observation rules retain raw Event and animation-ID
diagnostics; see the [acceptance contract](tests/acceptance/README.md) and
[identity proof](../evidence/canonical/native-ideal-clock/animation-identity.md).
The only execution inputs are tick recipes, game assets/save and a fixed machine
profile. Retired service, clock, ISR, device-answer and per-event register tapes
are preserved in ignored `to_delete/`; historical reports remain evidence.

`run_edge.py` is a required port suite: Quick Game edge holds must stay within
61 scroll steps per game second, release must return to the outer loop, and
the seed-0 human replay must exit normally. Gate registration needed: run
`python portable/tests/runtime/run_edge.py --report build/current/portable/report.json`
once after the fresh native build; its default output is `build/current/edge`
and a nonzero exit is a failure. Also retain the deterministic control using
`--deterministic --out FRESH_PATH`. The shared virtual 59.940476 Hz display
grid applies in both modes; physical presentation does not set game time.

The sound-off check runs unpaced, opens no playback device and renders no PCM.
Headless deterministic runs omit derived screen conversion/upload while keeping
the same internal input refresh; checkpoint images still read every pixel of the
source VGA aperture. Each entry retains all 1,032 binary view fingerprints and
the raw keyboard/animation diagnostics. Native locations are resolved once per
invocation, and every pinned DOS reference is validated independently.
`timings.json` separates observer build/preparation and lane phases; each lane's
`result.json` includes observer counters, steps/s and simulated-time/wall-time.
Add `--sample-native` for an optional Windows native sampler. All children and
sampler threads are joined. `--scratch-root PATH` selects a short disposable
asset directory when the default path exceeds the original file-dialog domain.

A mismatch reports the first entry and named view. Rerun with `--dump-entry N`
to write `native.frame.N` with the complete bytes of every view. Compare a pair
of full dumps with:

```powershell
python portable/tests/acceptance/inspect_ideal_dump.py DOS_FRAME NATIVE_FRAME --schema CHECK_OUTPUT/native-views.json --field VIEW_NAME
```

If the reference has no full dump at N, record a diagnostic DOS prefix ending
at N into fresh scratch output with `step_record.py --steps N`; never replace
the pinned reference. These raw byte diagnostics do not apply the two reviewed
observer projections. Entry timestamps are retained as a separate diagnostic:
the unchanged Save scenario already has one transient DOS/native poll-phase
difference, so timestamp equality is not a new gameplay verdict.

Default output is recreated after moving the previous result to ignored `to_delete/`.
Explicit experiment output must be fresh. Defaults use MinGW GCC under `C:/msys64/mingw64`
and the local SDL3 SDK under `build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32`;
`--cc`, `--sdk` and `--out` override these locations. Game databases/fonts/CFG
are local prerequisites. The SDL3 runtime and hardware BIOS fonts are copied to
the result; historical executable bytes are not native runtime resources.

Run the result from the repository:

```powershell
build/current/portable/simant-canonical.exe
```

For a Windows 64-bit drop-in playtest package:

```powershell
python portable/package.py
```

Extract `build/current/playtest/simant-sdl3-playtest-win64.zip` into a copy of
the DOS game folder, retaining its `simant-sdl3-fonts/` directory. Launch
`Play-SimAnt-SDL3.cmd`. It leaves display and sound selection to the original
`SIMANT.CFG` and source command-line rules, then records `simant-sdl3.log`; no Python,
compiler, DOSBox or separate SDL installation is required. The package contains
the current executable, SDL3 DLL, build identity receipt and licensed font support, but no original game
data, configuration or saves. The original startup needs an `INSTALL.EXE` file
to open; the launcher creates an empty probe only when absent and preserves any
existing installer. Prefer a short folder path for the original file dialogs.

Every Windows launch creates `diagnostics/simant-YYYYMMDD-HHMMSS-PID/` under
`SDL_GetPrefPath("SimAnt", "SDL3")` (normally `%APPDATA%/SimAnt/SDL3/`).
`--diagnostics-dir=PATH` chooses another root.
`session.log` includes the build revision and final executable SHA from the
build-time `simant-build-id.txt` receipt, command line, asset directory,
`SIMANT.CFG`, seed and exit status/reason. Keep the receipt beside the executable.

Launch `Play-SimAnt-SDL3-debug.cmd` or pass `--debug` to save stderr and SDL log
output in `debug.log`, and real keyboard/mouse input in `input.txt`. The input
observer runs after SDL logical-coordinate conversion and before DOS key
filtering. Scripted events are tagged and excluded from recording; all launches
keep a bounded 200-event crash tail. Wheel and unsupported extra mouse-button
events are comments because the game ignores them. Press **F12** in debug mode
to save `capture-NNNN/screenshot.bmp`, its exact presented RGB8 palette and the
outer game-loop counter. Repeats do not create extra captures. Ordinary launches
retain the existing F12 behavior. The snapshot uses the last completed
presentation, not a framebuffer still being drawn.

Unhandled Windows exceptions and CRT aborts produce `crash.txt`, a best-effort
`crash.dmp` with the faulting thread's exception/context, and the exact executable
as `simant-crashed.exe`. DbgHelp is loaded from the Windows system directory and
initialized before gameplay. A prestarted writer thread dumps the copied context
without entering SDL or game cleanup. Stack names use DbgHelp; source lines are
best effort (system DbgHelp may not read MinGW DWARF). The preserved `-g` executable
also supports offline GDB/addr2line analysis. Forced termination cannot write a dump.

After a crash or problem, ZIP the newest diagnostics folder. To approximately
reproduce a debug session with the same game data and configuration, use the seed
in `session.log`: `simant-canonical.exe --seed N --input-script input.txt`.
Production uses one [ideal-machine clock](whole_program/platform/README.md#ideal-machine-clock-native-clock-v1).
`--deterministic` runs the same read rule unpaced; scripts and `--seed` support
repeatable native regression observations. Physical input remains external, and
this records input rather than a full machine snapshot. Debug logs grow during play and can include local paths and config.

```powershell
python portable/tests/diagnostics/run.py --report build/current/portable/report.json
```

The first manual playtest ([report](../evidence/canonical/validation/manual-playtest.json))
found broken sound, a logo-click hang and a non-640x480 display. All three had
platform-boundary root causes and are fixed: the host forced `/s1` and `/dE`
instead of letting the canonical config select VGA and Sound Blaster mode 6, the
native audio had no SB/OPL device emulation, and held-input polling did not deliver
host input. Later fixes cover register-return contracts, the virtual DOS drive,
oracle BIOS fonts, canonical text and cursor owners, DOS adjacency spans,
cross-TU pointer widths and five 16-bit word intermediates (see git history and
`evidence/canonical/behavior-attribution/`). The build is a candidate for a second
manual playtest; full DOS/native behavior equivalence is not claimed.

The independent source-clock, input, observer and presentation controls are:

```powershell
python -m unittest discover -s portable/tests/acceptance -t .
python portable/tests/acceptance/run_virtual_audio_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
python portable/tests/acceptance/ideal_rule_check.py --out build/workers/NAME/clock-rules
python -m portable.tests.acceptance.ideal_pit_edge_check --out build/workers/NAME/pit-edges
python portable/tests/acceptance/ideal_internal_refresh_check.py --out build/workers/NAME/internal-refresh
python portable/tests/idle_yield/run.py --out build/workers/NAME/idle-yield
python portable/tests/input_irq/run.py --build build/current/portable --out build/workers/NAME/input-irq
python portable/tests/mouse_services/run.py --build build/current/portable --out build/workers/NAME/mouse-services
python portable/tests/runtime/run_windows.py --report build/current/portable/report.json --out build/workers/NAME/windows
python portable/tests/runtime/run_modern.py --report build/current/portable/report.json --out build/workers/NAME/modern
```

Acceptance discovery includes the complete upper-layer regression. Explicit worker
outputs must be fresh; replace `NAME` with a task directory. The three lanes can
also be run separately as documented in the acceptance README.

The application locates the adjacent resources and runs the converted original
main. The platform application owns SDL lifecycle, presentation, input injection
for tests and host resources; startup dialogs and the simulation remain in game
source. See [runtime checks](tests/runtime/README.md) for fresh writable resource
copies and the Save/Load trace requirements.

## Desktop policy

Ordinary executable launches stage the supported English VGA resources and initial
`SIMANT.CFG` into `%APPDATA%/SimAnt/SDL3/games/<installation-id>/`. The private
DOS C: volume holds saves and configuration; the installation and original asset
folder are read-only inputs. Existing user files are preserved. The installation
ID is a stable hash of the absolute resource-folder path: moving an installation
selects another volume. Copy existing `.ANT` saves into that volume to import them.
`session.log` records both resource source and active volume. `--user-dir PATH`
overrides the per-user base for game volumes; diagnostics have their own override.

`--portable` explicitly mounts adjacent resources in place. `--assets PATH` also
selects in-place storage, for existing portable setups and disposable test copies.
These modes write saves into that folder and need writable game files. The packaged
`.cmd` launchers are legacy portable launchers: they also create the documented
installer probe and redirected launcher log beside the executable. Direct executable
launches require neither of those installation-folder writes. Diagnostic logs use
the per-user location in all modes unless explicitly overridden.

Before entering the game, startup checks the ten immutable resource files against
the supported shipped set's SHA-256 identities and bounds the original CFG parser's
six words. Missing, unreadable, modified or corrupt resources stop with a named
error (a message box in windowed mode, stderr/status 70 headless). Other editions
or custom resource sets are not supported by this preflight. Resource staging
reports permission and disk-space failures. Runtime save errors still use the
game's own error dialog and dirty-state policy; short host writes are completed
or returned as an error, never accepted as a complete save. No partial-write
atomicity or recovery of an overwritten old save is claimed.
File-selector timestamps use the file date's daylight-saving rule, rather than
the current day's bias.

Focus loss and minimisation do **not** pause, mute or reset the machine clock:
simulation and sound continue, as on a DOS machine with no focus concept. Restore
does not alter game state. SDL releases physical keyboard keys on focus loss; the
host also releases a held pointer button when focus leaves the application, so a
lost mouse-up cannot leave tracking stuck. This is an input-release policy, not
an auto-pause setting. Fast retains the source's timing waits; Ultra bypasses host
pacing, retains every machine quantum, and can consume a core. Audio playback and
physical display refresh never set the simulation rate. A virtual VGA write
charges the next shared machine refresh boundary; a source pass can cross more
than one boundary when it polls between drawing operations. Ultra's machine audio can run ahead
of physical playback; it does not promise wall-tempo sound.

Close and Alt+F4 on the main window enter the game's File > Quit path once gameplay
has begun, including its Save/Discard/Cancel prompt. A current game modal must be
finished before the queued Quit is handled; repeated closes do not dismiss it.
Before gameplay, close exits directly. Hosted child close boxes retain the game's
logical-window close policy. A crash produces the diagnostic report/dump, with no
attempt to save potentially damaged game state.

The classic 640x480 screen keeps its aspect ratio. At 1x or larger it uses nearest
integer scaling with black margins; below 1x it fits the entire image with linear
filtering. SDL maps mouse coordinates through the same transform after resize,
maximise, fullscreen and display/pixel-density changes. **Alt+Enter** toggles
borderless desktop fullscreen on the main window. `--windows` remains supported:
its child windows and modern map retain their separate presentation/input policy.

Keys use US **physical positions**, independent of the OS layout: for example the
US Y position produces `y` on a German layout, and US Shift+2 produces `@`.
IME composition and Unicode text are not game input. Use US key positions when
entering filenames; only the original DOS character set is supported. Plain Alt
and F10 retain their DOS key meaning (the hosted native menu also has Windows menu
navigation); Alt+Tab, Alt+F4, Alt+Space, Ctrl+Escape and Windows-key chords are not
forwarded into the DOS keyboard. Global shortcut delivery remains OS-owned.

```powershell
python portable/tests/desktop/run.py --build build/current/portable --out build/workers/NAME/desktop
```

This runs real and dummy SDL presentation/mouse/keyboard checks plus read-only
distribution, per-user file preservation, corrupt/missing resource, unwritable
destination and injected disk-full/short-write controls. A real multi-monitor,
mixed-DPI and IME desktop still requires a hardware playtest; injected SDL checks
do not establish those physical-environment results.

`portable/tests/desktop/windowed.py --build BUILD --out FRESH` measures the real
window at title/play/pause/modal/Fast/Ultra and in hosted mode, then joins every
child. Its input recipe uses `# clock: host-ms`: timestamps schedule external
SDL inputs by elapsed host time so prompt responses remain reliable at Ultra.
The default script clock remains machine milliseconds; `bios-ticks` is unchanged.
`quit` injects an ordinary SDL quit request (and can be cancelled by the game),
whereas the existing test-only `exit` ends a run directly. No script-clock choice
changes the machine read rule.

`canonical_native_abi/` contains bounded type/ABI conversions: fixed-width words,
near/far pointer spelling, owner views, callbacks and packed wire/native layouts.
`semantic-spans.json` records proven cross-owner DOS storage requirements. The
builder extracts the participating definitions into packed native groups, exports
their original names as offset aliases, and asserts every full member's size and
position. Initializers remain canonical; access expressions remain unchanged.
Independent SaveRec and literal-index censuses reject missing spans and undeclared
consumers. Record 28 and the six-word options/record 100 block use this mechanism.
`python tests/test_semantic_spans.py` exercises option read/write views, block I/O,
and missing-span, missing-owner, wrong-size and split-storage negative controls.
The final expression pass uses GCC preprocessing and pycparser to resolve
declarations, fields, calls and expanded macros under MSC16/native integer rules.
Unsigned operations and proved bounded signed expressions retain word semantics
before consumers. Five reviewed routines additionally preserve instruction-proven
signed word intermediates through a source-pinned [site inventory](../evidence/canonical/native-word-intermediates/README.md).
Signed overflow elsewhere, invalid shifts and pointer/layout effects remain
explicit debt; per-TU receipts include every expression and its mechanical reason.
Install the parser once with `python -m pip install --target build/deps/pycparser -r
portable/tests/integer_semantics/requirements.txt`. The fake libc headers are parse-only.
The same pass preserves MSC's per-expression order of unsequenced effects using
an [object-backed site inventory](../evidence/canonical/native-evaluation-order/README.md).
Typed effect temporaries retain calls, stores and deferred postincrements in the
recorded order. New sites fail closed; existing C sequence boundaries stay local.
Each build retains the pre-expression whole TUs under `expression-inputs/` for
reproducible disabled-pass controls.

```powershell
python -m unittest portable.tests.evaluation_order.test_evaluation_order
python portable/tests/evaluation_order/census.py --report build/current/portable/report.json --out build/workers/eval-order/native-census-check
python portable/tests/evaluation_order/run.py --report build/current/portable/report.json --out build/workers/eval-order/rng-order-check
```

`whole_program/platform/` implements DOS/BIOS services. The small
`whole_program/algorithms/` files project genuine canonical assembly algorithms
that a native C compiler cannot assemble; they are not an alternative C game
model. Header views and native registries borrow canonical ordinary owners.

Current native execution is a preview with explicit unresolved contracts.
Audio follows CFG Sound Mode 6 through canonical C and a readable translation of
the canonical timer/mixer ASM. Guest DSP/OPL commands reach the device emulator;
SDL receives stereo S16 PCM. Set `SIMANT_AUDIO_TRACE` to an existing directory to
record DOS-format OUT traces. The bounded command comparison and remaining limits
are documented in [the audio review](../evidence/canonical/native-audio-device/review.md).
All ordinary storage, including the clip rectangle destination, now compiles
from canonical owners without native reservations; the canonical icon Handle
slot is resolved only for the locked VGA mode.
FindIndex's one-past guard is a semantic exception. Window omitted-slot zeroing
has a reviewed shipped-resource/observer domain but differs in raw state.
The native heap provider now reports zero discarded sizes and restores an
allocation through the same handle, corroborated against bounded original
execution. Shared metadata and wider heap histories remain unproved. See the [allocator proof](../evidence/canonical/allocator-fixtures/README.md).
Unsupported font extents, malformed window bindings and zoom/allocation domains
remain explicit in `platform.json`. Lowering classifications and exception deletion conditions
are in `layout/repository.json`. Passing build and bounded tests do not close
those issues or establish complete DOS/native equality.

Published historical checkpoints live in Git. Current sources and validations
are described in [the canonical architecture](../docs/canonical-source.md) and
[the consolidation report](../docs/cleanup.md).


### Enhanced phase 1 native world preview

With `SIMANT_ENHANCED_CONTRACTS=1 --windows`, the complete Game Window and yard
clients use native-owned shipped artwork and semantic snapshots. No hosted
texture is uploaded beneath either canvas. `SIMANT_ENHANCED_WORLD=0` retains the
hybrid comparison while keeping publication enabled. Classic without the
contract variable keeps its existing behavior. This does not create docking,
command panels or native lifecycle dialogs.

Both terrain sets, both life banks, all 252 HCEGANT/SHARED pictures and FONT2
are decoded once after the shipped-file verifier, before DOS main. A required
asset/format failure aborts startup. Music may freely release source sprite
banks. Source draw producers continue hidden, including their RNG/timer work;
native repaint reads only completed generations. Nearest-neighbor scaling is
the default; wheel zoom uses integer steps above 100%, and enhanced zoom/pan
changes only the presentation camera. `--smooth-zoom` remains optional.

See [phase 1 ownership, source seams and scope](../docs/enhanced-mode/phase1.md).
Fresh verification and phone-capture commands:

```powershell
python portable/tests/enhanced/run.py --build BUILD --out FRESH_REGRESSIONS
python portable/tests/enhanced/invariance.py --build BUILD --out FRESH_INVARIANCE
python portable/tests/enhanced/capture.py --build BUILD --out FRESH_CAPTURES --regressions FRESH_REGRESSIONS
```

The first requires rebirth PASS and activation XFAIL. The second retains every
raw difference, including baseline variability; a nonzero result must be read
as differences, not silently treated as full invariance. The capture runner
checks source preconditions, compares independent asset decoding, and writes
asset-derived PNGs only to ignored scratch.
