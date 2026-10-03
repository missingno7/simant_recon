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
python portable/tools/run_whole_startup.py --application build/whole-application-v14/simant-whole-sdl3.exe --out build/workers/whole_program/new-startup-run
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

The v13 repairs restore the default screen clip's original sentinel entry and
make the supplied window parameters explicit. Direct 30-second Quick Game
replays now pass in EGA and VGA, each with 115 original outer-loop iterations.
The guarded VGA replay also exits normally without a handle guard hit. A direct
Full Game replay renders the surface world and map. The v14 Tutorial replay
reaches its original first instruction dialog after restoring two source-proven
AX=0 fastcall arguments. These are bounded entry-flow checks.

The direct-call arity audit now checks 7,528 calls and finds no missing required
arguments. Its 75 extra-argument findings remain diagnostic; it is not a C type
checker. The original keyboard's `MOV AH,8` behavior is also restored, with five
direct DOS/native controls. F2 consequently enters the menu path, exposing an
independent modal host-servicing stall. The v14 trace still had blank caption
bars and an exposed black map pane; later findings below narrow those issues.
Tutorial completion, interaction,
save/load and full audio/UI coverage are still open. These results and limits
are pinned in `portable/evidence/whole-application-runtime-progress-v2.json`.

The v15 application binds the bitmap-text service at video installation and
unbinds it at teardown. The v14 debugger trace had recorded five valid caption
requests rejected by that service's unbound guard. Its bitmap callback now
receives pixels after the four-byte image header, matching the original ASM
entry boundary. The focused test compares all 70 payload bytes. Fresh VGA Full
Game and EGA Quick Game runs display their original captions and menu headings;
both exit normally after 20 seconds and 54 outer-loop iterations.

BIOS key polls and blocking reads now service the existing application clock
owner. The File-menu modal consequently presents while waiting, accepts a
delayed SDL Escape, and returns to the source game loop. FIFO and nonconsuming
key-peek controls pass. The user's mouse-pointer defect is a separate 24-by-16
patch near the center of the screen; the lower-right resize icon investigated
earlier does not explain or resolve it.

The read-only v13 simulation/map packet is retained under
`portable/tests/whole_program/runtime_flow_v13/`. It records 110 DoAntSim returns
and counter advances, with repeated map and ant-array mutations. Map raster
callbacks produce indexed framebuffer pixels, and source window geometry
accounts for an overlapping map/yard layout. This narrows the earlier black-pane
concern without claiming a DOS full-frame comparison.

Fresh historical validation passes. The original assets match the oracle lock;
an older menu test's diagnostic append to RALLOC.DMP was preserved separately
and the original restored exactly. Its replacement consumer test runs against
scratch asset copies and checks the original asset hashes before and after.

The selected-source prototype in `build/portable/simant-sdl3.exe` remains a
separate executable with its previously recorded scope. Whole-program evidence
does not retroactively broaden its claims. Historical `EXACT` and
`BEHAVIOR_EXACT` evidence remains at the frozen oracle checkpoint.

The v17 drop-in package reads game resources beside its executable when no
isolated `runtime-assets` directory exists. Its DLL, BIOS fonts, licenses and
VGA launcher are bundled by `portable/tools/package_game.py`. The packaged
Full Game entry replay passes from outside the game directory. See the
[handover](handover-2026-10-03.md) for package locations and remaining work.
