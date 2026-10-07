# Held drag presentation and SDL mouse limits

Layer: SDL platform input/presentation. Canonical source is unchanged.

At baseline `c62915b`, held queries already reach the shared guarded input/time
refresh and the application idle hook. Presentation additionally requires
`g_5AAC == NULL`. That pointer is the current clip list, not a drawing-depth
counter: S26's title/resize loops keep `f_1E57_0351` active between complete XOR
outline draws, and `ProcCasteEvent` keeps `clip_SetWin` active between complete
triangle/control redraws. The old predicate therefore suppresses frames until
release. The platform now uses the low byte of `g_3DD4` for raster/cursor
exclusion at these polling yields, retaining the 16,666,667 ns rate limit and
existing refresh reentrancy guard.

An exterior title drag also reproduces a process termination under GDB. SDL
motion `(270,-28)` reaches the source unbounded and requests cursor capture
`(264,-28,287,-12)`. Its stack is:

```
exit(70)
source_g9148_capture
draw_active_cursor -> portable_m1b73_graphics_cursor_mode
render_source_cursor -> render_cursor -> run_mouse_callback
portable_m1b73_mouse_callback -> portable_m1b73_mouse_consume_event
dispatch_source_event -> ingest_host_events -> drain_host_observations
idle -> refresh_application -> portable_input_time_host_refresh_clock
f_1B73_0A30 -> StillDown -> ButtonHeld -> o26_39C7_040F
```

The source authority is `src/root/m1B73.asm:f_1B73_0046`: INT33 functions 7/8
install inclusive horizontal/vertical limits `0..width-4`, `0..height-4`.
Captured SDL events and letterbox coordinates can lie outside that range.
The host mouse event adapter now applies these driver limits before invoking
the source callback. Raster capture guards and canonical drag constraints stay
intact; direct source/keypad-generated callbacks retain their coordinates.

`portable/tests/runtime/run_drag.py` uses ordinary absolute-coordinate SDL
input and read-only GDB observations. It requires title, triangle and resize
handlers to return, multiple changing frames during each held track with active
clipping, zero busy-guard presentations, the presentation rate limit, and source
positions `(270,0)` and `(636,476)` for exterior SDL motion. It checks normal
bounded exit, all fixture events, current input/resource pins and an unchanged
disposable game directory. The unmodified baseline is a negative control:
zero tracking presentations and the exit-70 stack above. Fixed repeated runs
present about 120 title/triangle frames and 72 resize frames and exit normally.

This reproduces a native boundary termination during dragging; it does not
identify a separate access violation from the human playtest. An additional
100-second native GDB stress replay with 439 events, alternating window titles,
resize targets and both triangles, exited normally. Frame hashes include the
cursor; complete DOS pixel/state equality and arbitrary interleavings are not
claimed.
