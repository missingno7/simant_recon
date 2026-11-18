# MAP and modal input follow-up

The transient MAP transaction (N10, logical window 1400, hit object 1401) has a
native game-themed popup. It shares Map's semantic cells, masked icons and
native-camera indicator, including the actual native view's zoom and extent.
The source still draws and owns its original cursor on its hidden planes.
The popup's instructions stay visible while other panels are modal.
Press/drag/release and click-then-click select a position; Escape, an outside
click, or a drag released outside cancel. Releasing the opening click on MAP
leaves the popup open for the second click. The popup starts eight pixels from
the actual clicked point, clamps to that monitor's work area, and fits that area.

The adapter does not centre a camera or call `OpenMapYard`. `OpenMiniMapWin`
still opens, draws, processes and closes the source transaction. After its first
held-button check, a selected native point becomes an original 1401 event. The
original loop converts it using `miniMapRect`, `minimap_x_scale`,
`minimap_y_scale` and the nest padding, then calls `CenterEdit`/`UpdateEdit`.
The following original desktop-close event ends the wait. Cancellation sends
only that close event. The source implementation is unchanged.

A native world click also retains its initial press until `processEdit` makes
its first held-button decision. A physical release arriving during the source's
double-click delay therefore cannot silently skip the ant menu. This applies to
ordinary native world clicks; Shift, double-click and Experimental painting
keep their existing source input paths.

Experimental Tools' separate `DoExpMenu` tracker shares the existing themed
native popup presenter. The native device supplies original proximity hits and
FBxx notifications. The original tracker opens its own submenu, updates
`ExpSubStates`, and returns the tool. Acceptance follows the source's processing
of its submenu notification; cancellation uses the original Escape path. This
is not a second tool-command implementation.
Its device enters through the existing enhanced-input hook, so standalone SDL
host/clock/audio harnesses do not acquire a new game-layer link dependency.

Unknown compatibility window IDs are no longer converted into indices beyond
the sixteen workspace slots. Their existing source clients remain separate
SDL windows, placed near the initiating point. A source modal explicitly gains
native focus after it is shown. Population has Escape/outside-click dismissal;
About latches one native close request through the source credits sequence.
Exchange and Chase accept Escape/outside dismissal through the original
`EndLifeTransferMode`/`EndTargetMode` entries, preserving `SaveGamePaused`.

## Reproducing checks

Every registration below installs the committed `hidden_desktop.py` policy via
enhanced `common`. Explicit wrapping also works:
`install()` relaunches the whole Python command through `CreateProcessW` with
`lpDesktop`, inside a kill-on-close job. It audits the input desktop for job
windows and fails with exit 97; `Popen.lpDesktop` is not the isolation mechanism.

```powershell
python portable/tests/hidden_desktop.py portable/tests/enhanced/minimap.py --build BUILD --out FRESH_MINIMAP
python portable/tests/hidden_desktop.py portable/tests/enhanced/sweep.py --build BUILD --out FRESH_SWEEP
```

The minimap registration checks eleven cases in Quick, Full and Experimental
games: click, drag, Escape, outside click, drag outside after entering the map,
and drag away without entering it, plus the right, bottom, corner, left and top
map edges. Half-open hit intervals use floor division: rounding the last pixel
up to the source's exclusive edge would reject the hit and strand the wait.
These run on the surface and both nests. Nest maps additionally test both
blank side gutters, which count as outside rather than rejected source hits:
**111 cases** total. Native hit boundaries select only source columns 32–95
in a nest, including at fractional DPI scales. The old popup accepted a gutter
selection although the source declined to centre there. Its source loop did
return: the gutter negative detects the wrong native select/cancel result,
not an invisible wait. This differs from the exclusive-edge corner failure.
An immutable pre-fix build is retained as an expected-failure negative control.
The registration checks exact clicked-point placement and
monitor containment, visible/focused size, a captured-pixel comparison with
Map's camera indicator, retained actor publications, original
centring calls, and resumed source iterations. Captures use owned-window
`PrintWindow`/client readback, never a desktop screenshot.

The sweep takes the live HWND/HMENU census in each mode, including conditional
Manual presets and enabled Info navigation after following an actual card link.
It exercises picture links, Map/Yard/triangle/history hits with both click and
held release, player and spider command menus, recursive Tools/Scent items,
editable fields, and menu-bar commands. Each target starts in a fresh game.
Native popup return IDs are checked against the requested item. Experimental
tool and submenu state are checked in the original source variables.

An open wait must have an identified, visible, on-monitor presentation of a
usable size. Escape/outside cancellation must return to a native Pause-button
transaction and advancing source iterations within five seconds. Destructive
File items stop at their visible cancellable prompt. Disabled source items are
listed explicitly. This is a bounded live-state census, not an exhaustive walk
of every simulation outcome, every Info card or every future queen inventory.
The existing action-equivalence, menus, content, presentation, workspace,
passive-invariance, port and acceptance registrations remain separate proofs.
Source publication can precede native prompt presentation within one message
turn. The sweep allows that presentation pass to finish inside the same five
second deadline; it does not waive prompt visibility. A test-only hidden-prompt
negative verifies that a persistent missing presentation still fails.
The menu probe identifies the native application frame by its menu bar as well
as its caption: closed source selectors also retain the caption `SimAnt`.
Outside-click tests must target the frame, not one of those stale HWNDs. The
full round's old fixture failure and corrected 31-case follow-up are retained
separately; comparison views and verdict classifications did not change.

The exact registrations, every swept item/result, retained preflight failures,
private-desktop audits, build identity and delivery command are recorded in
`build/workers/enhanced-menus/RESULT.md`. Strict passive differences are reported
as differences; no acceptance reference, omission or mask is added.


## Shared test sessions and scale

The later [UI scale follow-up](ui-scale.md) scales this popup's map, camera
rectangle, labels, margins and pointer crosshair on the cursor's monitor.
`minimap.py` now links one probe and starts one game per mode for the whole
plane/case plan. Each case still sends the actual MAP button messages, observes
the original `CenterEdit` call or cancellation, compares the camera rectangle
against Map, checks retained actors/placement and verifies source-loop recovery.
Plane preparation waits for actual delivery and transaction completion. The
post-action check requires subsequent source iterations, rather than repeating
a blind startup delay for every selection. Each row and readback is retained.

The sweep reuses an interactive session when the tested source transaction left
its conservative state fingerprint unchanged. It checks every SaveRec byte,
source command/settings state, all eight Experimental substates and RNG. A
changed row starts a new disposable game. The real Pause recovery pair still
proves native input delivery and simulation-loop progress; its deliberate
advancement becomes the next reused baseline. It is outside the action-effect
fingerprint. Source preparation uses delivery/lease fences; body exchange keeps
its source settling interval. The five-second presentation deadline and the
persistent hidden-prompt negative control remain active. These are scheduling
changes, not new invariance masks or relaxed action/state comparisons.
