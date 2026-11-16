# Native content implementation: reproduction and claim boundary

Authored implementation evidence, 2026-11-16. This records port presentation
choices and source entry references; it does not claim recovered native code.
No game-derived raster, database payload or acceptance reference is tracked.

## Inputs and ownership

- Approved shape/capability/relocation table:
  `build/workers/enhanced-style/mockups/README.md`; tracked policy:
  `docs/enhanced-mode/style.md`.
- Source Map transformation/colours/background:
  `src/ui/map_window.c`; Yard scene and handler: `src/ui/yard_window.c`.
- Source allocation geometry/tracker/preset/release:
  `src/ui/colony_controls.c`. The two original triangle widths differ; source
  triWidth/triHeight/slope are shared temporaries, not interchangeable geometry.
- Source card record decoding/private link tables:
  `src/ui/info_cards.c`; graph selectors/order: `src/ui/history_window.c`.
- Source score calculation/output/Continue and queen-placement loop:
  `src/ui/view_commands.c`. Queen placement waits for 1902 inside its own call;
  it is not a second YardArea dispatch. Without Shift one valid click places one
  queen and returns even when queens remain stored.
- Source world/experimental trackers, menu and handlers remain canonical.
  `portable/whole_program/enhanced/actions.c` projects native pointer samples
  only at original device/event seams. Callback mask zero updates mouse state
  without creating an extra event. The source dispatcher still owns feedback,
  double-click classification and the complete transaction.

`portable/build.py` appends three small read-only observers to converted TUs;
their paths/hashes are recorded in each build report. They copy private links,
graph state and background mode after original code has produced them. A
font_PrintStr wrapper observes original score-field numbers after the real call.
The PlaceQueenInYard wrapper marks only the existing original synchronous wait.
No canonical source is rewritten for this implementation.

## Reproduce

Use fresh paths and locally verified assets/toolchains:

```powershell
python portable/build.py --out build/workers/NAME/native --jobs 8
python portable/tests/enhanced/run.py --build build/workers/NAME/native --out build/workers/NAME/regressions
python portable/tests/enhanced/workspace.py --build build/workers/NAME/native --out build/workers/NAME/shell --screens build/workers/NAME/shell-screens
python portable/tests/enhanced/action_equivalence.py --build build/workers/NAME/native --out build/workers/NAME/actions
python portable/tests/enhanced/content.py --build build/workers/NAME/native --out build/workers/NAME/content --screens build/workers/NAME/screens
python portable/tests/enhanced/invariance.py --build build/workers/NAME/native --out build/workers/NAME/passive
python portable/tests/acceptance/run.py --build build/workers/NAME/native --out build/workers/NAME/acceptance --jobs 1 --scratch-root build/workers/NAME
```

The final task directory additionally retains the one-round command/log/exit
receipt and all twenty existing port-suite invocations. Exploratory builds and
focused probes are labelled separately; they do not replace the final round.

## Positive and negative controls

The action matrix retains 1,024 existing raw views and 307 SaveRec records, with
the existing gameplay verdict policy unchanged. It compares the current-source
original event route to actual HWND control/menu/keyboard input and reports all
raw differences. The additional held-tool fixture supplies four observations
at original myButton queries, including a repeated held sample. Removing that
sample in a separate scent lane must change SaveRec. The existing offline
one-byte SaveRec mutation must also be detected. Recruit requires the real
YellowCommand(1); eligible queen placement uses the shipped four-key queen
cheat through source keyboard input as common setup, then original 1910/1902
transactions. There are no debug writes to game variables.

Content checks observe original camera/levels/card/task completion. The value
domain check independently enumerates each editor while its original geometry
is current and compares all six combo item sets against source conversion.
The edited-triangle capture occurs after the original tracker has changed its
levels and before the real release. Repaint captures compare const publications.
The queued-value/Map regression reproduces a dropped second action on the
pre-correction build and requires both the original percentage result and
camera movement after the fix; discrete coordinates cannot overwrite the live
pointer request waiting behind them.
Full passive invariance is a separate strict all-raw test, including repeat-off,
source clock and sound commands. Its failures must stay failures, with exact
entry/view diagnostics; agreeing SaveRec/RNG cannot substitute for a raw pass.

These are bounded native event-path and presentation checks. They are not an
original-DOS enhanced action matrix, historical pixel equality, every Full Game
branch, arbitrary resource safety, mixed-DPI hardware or accessibility proof.
The original/canonical/native 58-lane acceptance suite is reported separately.
Step C compatibility dialogs and rejected general result/transcript APIs remain
explicit in `docs/enhanced-mode/build-b.md`.

## Recorded result

The task receipt is `build/workers/enhanced-build-b/RESULT.md`. The complete round
is `verification-final.json`; later presentation-only checks are retained in
`verification-visual.json` and `verification-review.json`, with distinct pinned
builds. Twenty port suites and 58 acceptance lanes pass. The full action run
passes 100/101 rows; 010D keyboard times out in startup before state.0 and passes
an isolated recheck. The delivery layout checks pass both triangle actions,
18 content cases and ten window scenes. The startup failure is not erased.

Delivery passive invariance remains a strict failure: all nine comparisons,
including repeat-off, differ at every one of 128 entries. Only the clip rectangle
workspace, raw window order, fd_50F6_37FA and (in some lanes) mode knob animation
index differ. All 943 gameplay-verdict views, including 307 SaveRec records,
agree; source clock and sound commands agree. The 704 established schema
omissions remain unchanged. `passive-summary.json` records exact per-lane counts;
`review-invariance/result.json` retains entry/view and first-byte diagnostics.
These facts do not identify the cause or turn the raw failure into a pass.
