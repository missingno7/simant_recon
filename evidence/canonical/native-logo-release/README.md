# Native held-input polling boundary

The logo click hang is a platform input defect. Canonical `DialogWaitInit`
(`src/root/m00F8.c`) runs `while (StillDown()) win_FlushEvents();` when the click
advances `ShowIntro` into `CustomerIDDialog`. `StillDown` (`src/root/m1FD2.c`)
reads the mouse buttons and queries Insert, Space and Delete through
`f_1B73_0A30`. No clock or BIOS-key polling occurs in that loop.

DOS INT09 updates the scan table; INT33 callback `f_1B73_0445` stores mouse
status independently while the foreground polls. The native implementation
queried cached host scan state without servicing SDL. A held logo click thus
froze with `g_9120=0x0201`, mouse-up still pending, and no more presentations.

The native scan service now refreshes the existing shared input/time owner
before reading its scan state. This delivers asynchronous input through the
same ingestion/observer path as the other native polling services. Its existing
refresh guard prevents nested refresh recursion. Source algorithms, source
state, ABI conversion and event masks are unchanged.

Canonical DOS observation, fixed 200000 cycles and guest clock 1992-01-01
12:00, `/dV /s1`, left down at 5550 ms and up at 5750 ms:

- At 5554.314170 ms, `DialogWaitInit(15)` is entered for the customer dialog.
- At 5700.000230 ms, `StillDown` still polls with low mouse bits 1.
- INT33 callback stores `0x0201` at 5550.002515 ms, then `0x0400` at
  5750.002515 ms. The button bits clear without foreground event pumping.
- An execution trigger at `DialogWaitInit` offset +0x1A (the `TickCount` call
  after the held-state loop) is reached at 5750.582890 ms with mouse `0x0400`.
- Top source window is logo `0x0300` at 5400 ms, customer dialog `0x1E00` at
  6000 ms, and selector `0x0200` at 10000 ms after a Return at 9000 ms.

These addresses were resolved from the canonical `SOURCE.MAP` and unique VGA
clip owner pattern, not the historical executable's data layout. The observed
load base was `0x8240`; `g_9120` was linear `0x651A2`. Symbolic assembly in
`src/root/m1B73.asm` independently establishes the interrupt store contract.

The permanent regression uses ordinary SDL input plus read-only GDB startup
entry/return observations. It includes animation and late clicks, corner and
center positions, held right-click and Space, repeated clicks, and verifies
release, modal returns, complete replay injection, frame and bounded exit.
The pre-fix `center-after` run must time out after injecting mouse-down without
mouse-up; the repaired implementation must pass. No whole-game or global
DOS/native event-interleaving equivalence is claimed. Exploratory stacks,
full memory dumps and execution-trigger receipts stay in ignored worker space.
