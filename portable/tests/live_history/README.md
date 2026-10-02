# Live History integration evidence

## Current bounded result

`evidence/live-history-next10-build3-physical-paused-proof-20261002.json` is the final passing receipt. It exercises the SDL dummy-driver NewGame path against the captured Next10 production build. The injected sequence opens the Speed menu and pauses, opens Window → History with command `0xFD15`, presses graph buttons `0x1503`–`0x1507` to fill the four-visible-graph list and evict the oldest, then removes the first, middle, and last shown entries. It presses the graph-area object, moves while held, releases, unpauses, and completes 32 simulation ticks.

The receipt checks all nine engine History actions against their actual source-owned private UI snapshots, with unchanged RNG and completed-tick counters at each action. The graph-list states match the existing 29-event original-DOS History corpus. The menu-action trace records source pause transitions `0→1`, `1→1`, `1→0`; all menu actions occur at tick zero, and every History action occurs while paused. The source StillDown polling trace has 333 records, the host poll trace has 28 records, the menu dispatcher trace has 3 records, and the engine History trace has 9 records. Final state is unpaused at 32 completed ticks.

Scope is limited to this finite native SDL integration and its exact source-state transitions. There are no original-DOS calls in the physical sequence, and this is not a DOS-pixel, full UI, whole-game, or real-clock equivalence claim. The 29-event paired DOS/native report is a separate component receipt.

The final run took 8.412 seconds (`wall_elapsed_ns=8412202400`). Its receipt pins 261 production inputs and 9 test inputs, verifies their before/after stability, and records 14 output files including the report, event/state snapshots, traces, and screenshot. The production receipt SHA-256 is `e2a32572024f4e241a8e5f0e316dddb5189e58ec723ac8f98965292a5c48b988`; the executable SHA-256 is `a7dbe2b221bd3b2086043f0adf4de5c9d539128e2ca4dcd7116e8ce4a5023328`.

The final runner SHA-256 is `776e4bcefa0b5faeaf3c476667918d9dba2d386fe7d455bb9f3e99b4804e6a62`; the final injector SHA-256 is `0bac74ca11edae1d36136ca558268b39dee17779e7866dea1346a237e55f3269`.

## Earlier failed attempts

The immutable FAIL receipts are retained beside the final receipt. The first attempts timed out because the test link omitted `SIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1`; without that test-only define the History geometry emitter was compiled out, so the injector stayed in its wait-for-geometry phase. The host-event and ProcMenu traces show that FD15 was in fact consumed and dispatched, so the timeout was a harness setup error rather than evidence that the game menu failed to open History.

After adding the diagnostic define, a run completed the interaction but the receipt still failed two test predicates: its expected scenario-name subset omitted `add_first` and `add_to_partial_list` (four events), and it compared the menu oracle's low-byte item ID `0x15` against the full derived DOS command `0xFD15`. The final runner validates all seven named corpus scenarios (29 events total), the low-byte mapping plus the separately observed full command, and the pause-state sequence.

The earlier runner/injector contents were not archived as source snapshots before they were revised. Their immutable FAIL receipts retain the respective input hashes and captured outputs, but those reports are not reproducible from the current runner/injector files. No old source versions have been reconstructed or represented as archived.
