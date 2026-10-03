# Whole-source SDL3 application

`portable/tools/whole_program.py --compile --link` mechanically converts all
98 original C/data translation units, preserving function order. The DOS
heap/EMS module is replaced at its platform boundary by native resource handles.
The generator checks the frozen historical tree and records every source
conversion. A relocatable core is diagnostic; its unresolved imports are retained.

`portable/whole_program/application.c` owns the native host lifecycle and calls
`dos_game_main` from the converted original entry module. The original source
controls startup, menus, dialogs, updates and simulation. Native services borrow
the same framebuffer, resources, handle registry, input queues and clocks.
There is no second game-state session in this application.

The default source arguments are `/dE` and `/s1`. Original `ReadConfig` runs
before these arguments override its display and sound choices. `/dV` selects
the implemented VGA logical presentation; other legacy display/sound profiles
are rejected explicitly. Physical DOS drive resets, overlay loading and hardware
interrupt installation are retired at named host boundaries.

To attempt a complete executable link after a stable generator run:

```powershell
python portable/tools/build_whole_application.py --out build/whole-application-v1
```

This command fails on unresolved symbols and records the real linker diagnostics.
It checks current migration inputs, generated source identities and core identity.
The v6 application linked successfully with zero unresolved symbols: 97 converted
translation units plus 109 native providers. Its bounded original-main run passed
cursor resource setup, then exposed a split between root and overlay menu storage.
The preserved v6 receipt records a failure and no captured frame. Later source
repairs require a fresh generation, link and runtime test.
The v8 application produced the original SimAnt intro at 640 by 350 pixels.
A scripted Return key passed the intro and exposed a missing customer-dialog
string. This was traced to a native preflight wrapper that lost the original
closed descriptor number: DOS reuses that number for the first retained data
file, and the original loader reads registration text from its trailer. The
correction preserves the descriptor reuse through the virtual DOS I/O table.
The intro capture recorded zero outer game-loop iterations; it is startup
evidence only.
The completed executable must be tested separately before claiming working game
flows. Syntax compilation, a relocatable link and a startup frame are different
checks; none establishes complete gameplay.

The application supports `--assets PATH`, `--bios-fonts PATH`, and `--seed N`.
Successful builds snapshot the converted source and native providers under
`inputs/`, and create separate `runtime-assets` and `runtime-bios-fonts` copies
beside the executable. These are the default resource directories. Source
configuration/dump/save writes stay in the runtime copy. The hash-pinned
historical assets remain the oracle inputs.
`--smoke-ms N --frame PATH` is a bounded startup check: it services original
source waits and captures a presented source frame, or fails if no source frame
was presented. It does not bypass startup dialogs or claim a completed NewGame.

`--headless` explicitly selects SDL's dummy video/audio drivers. The reusable
runner records the executable identity, frame identity, runtime asset changes,
and verifies that original assets did not change:

```powershell
python portable/tools/run_whole_startup.py --application build/whole-application-v6/simant-whole-sdl3.exe --out build/workers/whole_program/new-startup-run
```

`--input-script PATH` accepts ordered keyboard transitions, one per line:
`6000 down Return`, then `6050 up Return`. Times are milliseconds after entering
original main; key names use SDL names and contain no spaces. Comments begin
with `#`. These events enter the normal SDL input boundary. The script does not
call source functions or alter game state directly. The runner accepts the same
option and records the script hash. A completed script or captured frame alone
does not prove that a scenario initialized or simulation advanced.

Pointer transitions use logical coordinates: `11000 move 344 100`,
`11200 mouse-down Left 344 100`, and `11400 mouse-up Left 344 100`.
The host converts these to window coordinates before enqueueing actual SDL
events, and ordinary input polling converts them back. EGA/VGA round-trip
controls and invalid-operation controls are recorded separately. The reusable
Quick Game replay is `portable/tests/whole_program/application_input/quick-game-v1.txt`.

The v9 original-main replay passed intro/customer dialogs and captured the
source scenario selector, with zero outer game-loop iterations. The v10 click
entered `NewGame` and exposed a word-array spelling of a text Handle that had
escaped the sidecar adapter. Both reads now use the existing +0x2a sidecar,
with a compile-time field-offset assertion. The v11 EGA run passed that point
and reached animation capture at y=431 outside the visible 350-line framebuffer.
That original video-memory contract is under investigation; this is still
explicit runtime debt, not a completed-game claim.
The v12 VGA debugger replay selected Quick Game through SDL, completed 84
original outer-loop iterations, and captured the playfield and source controls.
Direct v12 runs reported heap corruption during dialog closure; this difference
is recorded in `portable/evidence/whole-application-runtime-progress-v1.json`.
The run does not establish direct-run stability, tutorial/full-game coverage,
or save/load correctness.

The selected-source prototype in `build/portable/simant-sdl3.exe` remains a
separate executable with its previously recorded scope. Whole-program evidence
does not retroactively broaden its claims. Historical `EXACT` and
`BEHAVIOR_EXACT` evidence remains at the frozen oracle checkpoint.
