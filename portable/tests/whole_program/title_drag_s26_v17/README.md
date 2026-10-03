# S26 title drag: v15 crash and v17 pointer fix

The retained ordinary QuickGame replay starts a title-bar drag at (215, 32), moves to (255, 105), then releases.

The v15 run faults in `o26_39C7_040F` when it reads the native-width `Win::objs` overlay. The v17 build instead reaches that handler through the registered object sidecar: front window 0 has 23 objects, its title object has type `0x12`, and the source outer rectangle is `[14, 22, 418, 379]`.

The v17 replay does not complete. Its log ends at the mouse-down; it never enqueues the scheduled move or release and the drag handler does not return. Source `ButtonHeld` starts with a two-tick countdown where it calls `TickCount`, then polls only `StillDown`. `TickCount` refreshes the clock and may pump the idle hook, so it is not accurate to say the modal loop never pumps. The move is scheduled 200 ms after down; the source countdown is two changed ticks at the configured 18.2 Hz BIOS cadence, then no further `TickCount` occurs in this loop. The SDL `StillDown` provider returns latched `left_down` and only invokes its pointer poll under `history_input_active`, which this window drag does not activate. This is the source-bounded likely explanation for the missing release, not a live measurement of the private refresh guards. The final moved rectangle is not observed.

`report.json` includes SHA-256 pins for the v15/v17 executables, copied runtime assets and fonts, v17 build report and S26 TU, replay scripts, debugger logs, and relevant source files. Executables, SDL DLLs, and game assets are deliberately excluded from this evidence folder. `s26_window_object_views_v1/fixtures/v15/` retains the exact generated TU and `dos_types.h` needed by the standalone S26 conversion compile control.
