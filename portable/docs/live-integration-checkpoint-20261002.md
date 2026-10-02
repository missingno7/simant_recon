# Live native integration checkpoint — 2026-10-02

The immutable DOS oracle is `dos-semantic-oracle-v1`, commit
`66e85041ee54f59774ae0fd5a08b37ffbcf77172`. It preserves 1,611 EXACT
functions and 29 separately registered BEHAVIOR_EXACT contracts. Historical
codegen, data/layout and RTLink debt remain recorded in the frozen report.
The native work below changes no historical reconstruction input.

The SDL3 prototype runs resource-backed NewGame and the recovered colony
loop in one resizable 640×350 logical window. It renders the Edit viewport,
nest overview, source window order, clipped overview cursor and resource menu
bar. Quick left clicks and double clicks reach recovered `processEdit`;
pause/speed, single-step camera keys and `YellowCommandKey` use the source
logical interfaces. The live clock samples EnterNest at its actual conditional
read sites rather than supplying two precomputed timestamps.

## Verified boundaries

- [Native gate](../tests/evidence/native-unit-gate-39-20261002.json): 39 suites
  and the real SDL host pass. The retained receipt includes the host build,
  event/clock checks and independent inspection of all 224,000 framebuffer
  pixels. Source-generation/tooling tests also pass: 17 tests.
- [Current tick replay](../research/core-proof/original-256-tick-summary-next2-lazy-clock-20261002.json):
  three preserved original DOS captures replay successfully, 768 ticks total,
  comparing 370 nonpointer globals, both RNG states and ordered host arguments
  after every tick. Its nest clock is the explicitly controlled static lane.
- [Native Edit differential](../tests/input/evidence/native-process-edit-code4-lazy-clock-20261002.json):
  eight ordinary empty-Life clicks across all four planes agree with DOS for
  371 mapped fields, ordered callbacks and both RNG states.
- [Overview conversion](../tests/render/evidence/dos-overview-selector-raster-differential.json):
  all selectors 0–23 agree with normalized DOS planar output in four cases,
  covering both converter entries and profiles 0/8. Unsupported selectors and
  profiles fail before drawing.
- [Scoring](../tests/dialogs/evidence/calcscore-original-dos-portable-20261002-corrected.json):
  63 DOS/native cases agree for the score and all eight components. The
  game-over modal and restart/quit sequence are separate integration work.

Six final 32-tick SDL runs passed against the same production executable,
SHA-256 `f612cbb6afafcea9710250ac3f2f37cc443f8a3a319fa45cd1d620f5a63c4460`:
[menu](../tests/live_game/evidence/live-menu-final-32-20261002.json),
[camera](../tests/live_game/evidence/live-camera-final-32-20261002.json),
[click](../tests/live_game/evidence/live-click-final-32-20261002.json),
[double click](../tests/live_game/evidence/live-double-click-final-32-20261002.json),
[overview](../tests/live_game/evidence/live-overview-32-20261002.json), and
[yellow keys](../tests/live_game/evidence/live-yellow-key-final-32-20261002.json).
These are live integration checks, not full-game DOS differentials.

## Remaining integration

The build retains `DIAGNOSTIC_ONLY_NOT_PRODUCTION` status. Menu mouse actions,
other selectable Edit controls, right-button hotboxes, yard overview mode,
several balloon/control/resource lifecycles and the complete audio backend
remain unfinished. Unsupported registered input returns a named diagnostic.

The longer no-input run completed 2,687 ticks before normal red-queen
extinction reached the unsupported `EndGameDialog` service. The next required
flow is its modal, followed by `NewGame(0)` and `MenuQuit` on a negative
result. Source inspection confirms this sequence; it does not contain a
high-score or name-entry step. Restart must preserve the source reset boundary
and RNG consumption rather than reinitializing every recovered global.

The generated next2 profile is reproducible using the
[pinned recipe](recovered-source-next2-recipe.md). It is deliberately kept
separate from future profile extensions so these proofs remain replayable.
Original executable/assets, SDK/compiler binaries and BIOS reference fonts
remain local ignored inputs. Native runtime snapshots are diagnostic outputs
and are never used to initialize the game.
