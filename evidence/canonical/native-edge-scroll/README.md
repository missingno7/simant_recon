# Native Quick Game edge-scroll delivery

The seed-0 human recording is retained verbatim as
`portable/tests/runtime/edge-user.txt` (814 input events). The pre-repair
`40e1f2d` native executable freezes after `7958 move 374 480`. Its INT33
adapter already clamps source coordinates to `(374,476)`, so fixing screen
bounds alone cannot release the loop. Three actual GDB attachments observe
all threads: the main thread remains in `UpdateEdit <- f_0250_0D10 <-
f_00F8_01BE <- dos_game_main`, with replay_next 814 and outer loop 4, and
does not reach its 20-second smoke deadline. Samples inside f_0250_13A6,
f_0250_5058 and DrawEditGraphs exclude a blocked SDL/audio thread.

Canonical `src/root/m00F8.c:f_00F8_01BE` reads ISR-owned `g_9122/g_9124`
and calls `f_1B73_0EEE` each iteration. Exact canonical `m1B73.asm:0445`
writes the pointer state independently of foreground code. In DOS, input and
timer IRQs arrive while this loop executes. Native keyboard-flag queries
formerly read cached flags without pumping pending mouse/timer events.
The original/canonical ISR mechanism is matched historical source; no source
algorithm, canonical manifest or inventory changes are warranted.

The platform now delivers at keyboard flags/scans, event and mouse queries,
timer reads and presentation using `portable_input_time_host_refresh_clock`.
This is the sole host ingestion boundary; old separate BIOS/event ingestion
paths are removed. Callback reentry and observer ingestion are guarded. The
boundary borrows the platform's existing CLI/STI flag instead of adding
another IF owner. Real time is capped at one refresh per millisecond;
deterministic mode uses the configured quantum at outer refreshes only.
This supersedes the narrow held-scan-only delivery rule; its logo/drag
regressions remain meaningful and are retained.

Host pointer motion/buttons, state queries and warps use the visible screen
range (VGA `0..639 x 0..479`) before diagnostics and input projection. The
source INT33 adapter retains its tighter `0..636 x 0..476` limits. An edge
hold requires no further motion events; moving away must reach the source
through an eligible service while it scrolls.

`run_edge.py` checks both the exact recording and a Quick Game replay that
holds the map-window perimeter and all four screen edges, then moves away.
Read-only GDB observations tie frames to the active source scroll invocation
and require its returns, resumed outer progress, complete replay injection
and bounded smoke exit. Real-time and deterministic runs are separate checks.
The existing input IRQ control adds IF-off, recursion, 1 ms rate and virtual
poll controls while retaining the 2,304-step canonical instruction matrix.

Commands (each explicit output must be fresh):

```powershell
python portable/tests/runtime/run_edge.py --report build/current/portable/report.json
python portable/tests/runtime/run_edge.py --report build/current/portable/report.json --deterministic --out build/workers/NAME/edge-clock
python portable/tests/input_irq/run.py --build build/current/portable
```

`receipt.json` records minimal retained build/fixture identities and results.
Raw debugger traces and exploratory runs remain ignored. The scope is
foreground service-boundary delivery and observed edge starvation;
arbitrary pure-memory polling, full PIC/CPU interleavings, mickey sensitivity,
DOS pixel equality and simulation timing equivalence remain unproved. The
`native-input-hardware-context` contract stays open. No `graphics*.c` changes.
