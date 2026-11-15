# Phase 2: native workspace preview

Implementation organisation and layout policy are ours. Enable with
`SIMANT_ENHANCED_CONTRACTS=1` and `--windows` on Windows. The main client is a
Win32 workspace, with no presented DOS desktop or source frame geometry.
`SIMANT_ENHANCED_WORKSPACE=0` retains the phase 1 comparison host. Classic,
without enhanced contracts, retains its existing path. SDL's dummy driver has
no HWND; it retains the comparison host rather than claiming a native workspace.

## Technology and ownership

Win32 and common controls are already available through MinGW and SDL's native
HWND. This avoids a second toolkit/event loop and gives actual child-window
focus, native menus/buttons, tab controls and keyboard-operable trackbar
splitters. A version 6 common-controls/per-monitor-v2 manifest is linked as a
separate resource. The app owns real `WS_EX_TOOLWINDOW` floating HWNDs, whose
owner is the workspace root. Minimize/activation/taskbar ownership is Windows'
policy. Layout callbacks never enter canonical window/time services.

The world canvas is an owner-drawn native button: its accessible action opens
the view/layout menu; its name describes primary/read-only status, plane,
generation, zoom and camera. It has native focus feedback. Raster content uses
phase 1's `enhanced_world_cell`, immutable `enhanced_asset_cell` and
`enhanced_world_draw`, converted to a GDI DIB. No VGA/client texture is hosted
inside a workspace panel. The GDI source crop uses DIB coordinates, independently
of source window records. Only the current source plane carries completed
effectful overlays; other-plane inspectors draw published terrain/entities and
do not recall hidden producers for extra overlays.

Standard controls have documented [UI Automation support](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-controlsupport)
through Windows' [control providers](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-providersoverview).
This is the technology rationale, not a runtime accessibility certificate.
The executable UIA test requests roles, names, focusability and Invoke support.
In the development environment even an independent stock Win32 button was
reported as a generic Pane. That baseline is retained under
`evidence/enhanced-mode/windows-uia-baseline.c`. The workspace test remains
nonzero when those checks fail: HWND presence alone is not accepted as proof of
accessible roles/actions. No completed screen-reader or physical mixed-monitor
accessibility session is claimed.

## Layout and native input

`enhanced/workspace.{h,c}` is a bounded, game-independent model: split nodes,
tab leaves, eight floating subtree roots and 24 stable panel IDs. IDs 0..3 are
the primary and at most three live inspectors. Other families have one named
empty native panel each. Play pins the two command placeholders; Colony,
Research and Minimal are additional presets. Reset Layout restores Play.

Drag a native tab past eight DIP. Nine owned target windows name outer-edge,
group-edge and tab-stack destinations; a selected target also shows a preview.
Escape cancels. A release outside the workspace floats the tab. The Move panel
menu and Shift+F10 expose split/stack/outer-edge/float/collapse/hide commands
without dragging. Panels > World reopens a hidden primary; the inspector IDs
are reused, never cloned beyond three.

Six-DIP splitters are focusable native sliders. Drag them, or use arrows,
Shift+arrows and Home (equal split). Layout clamps geometry to child minimums.
At narrow widths, side groups collapse into recoverable strips; click a collapsed
tab or use its keyboard menu to expand. The remembered split ratio survives.
F6/Shift+F6 cycles visible regions, including floating ones. Ctrl+Tab and
Ctrl+Shift+Tab cycle the focused tab group. Native Tab traverses its controls.

Wheel zoom uses nearest-neighbor integer steps above 100%, and halves below it.
Canvas drag pans its own camera. Inspectors select Surface/Black nest/Red nest
through their view menu, using the same all-plane publication; there is no
Freeze mode. The primary follows source-origin/plane changes without writing
them. Its explicit plane menu submits the existing N01 semantic intent. Tile,
held and actionable pan transactions remain the phase 3 adapters; this phase
does not invent them. The primary is the sole gameplay action destination.

Native root mouse/key events are consumed before the guest boundary. Physical
layout hover/buttons/modifiers return a neutral guest pointer while the workspace
owns input. The deterministic replay state remains the existing authorized
input channel. Compatibility lifecycle/dialog HWNDs retain their established
input path. Source logical open/front/geometry and source drawing continue
independently. Layout does not call win_Open/Close/ToTop or source time. Dock
gestures and model replacement are conservatively disabled while the published
source tool owns interaction. Inspectors never submit gameplay intents.

The native Prompt placeholder is injected/selected during a source modal task
and cannot be hidden, collapsed or buried by layout/preset/tab changes. It retires
when the observed task ends. Actual chooser/dialog contents and wait-result
input retain compatibility HWNDs until phase 5; the placeholder is not a new
task-result bridge.

## Persistence and display metrics

`%LOCALAPPDATA%\SimAnt\workspace-v1.txt` is separate from `.ANT` saves.
`SIMANT_WORKSPACE_LAYOUT=PATH` selects an isolated destination, used by tests.
The versioned text format stores the tree, ratios/tab selection, collapsed
groups, hidden-panel return groups, inspector plane/camera/zoom, and floating
bounds in DIP with monitor device identity and work-area-relative position.
It stores no source plane/camera/pause/speed/logical state or game-save bytes.
The primary's camera is presentation state; source navigation may subsequently
move it as described above.

Completed operations save through a temporary file and atomic replacement.
Loading is transactional: reject unknown versions, invalid/duplicate panel IDs,
unreachable/cyclic nodes, invalid selection/ratios/preferences and trailing data.
Preserve a rejected file beside the original with a diagnostic suffix and use
Play. Child/fonts/raster metrics are recomputed on DPI changes. Floats use their
own effective DPI; restore/recovery clamps their full frame into an available
work area, including a reachable caption. Monitor removal falls back to the
current monitor while retaining the saved monitor preference.

Phone captures exercise 144/192-DPI WM_DPICHANGED paths. Those are message-driven
scale tests, not physical mixed-DPI monitor removal, Remote Desktop or system
text-size tests. Main-frame position/size and a separate app text-scale preference
are not persisted yet. Hardware validation remains explicit.

## Verification and owner registrations

Run after a fresh build, with new output directories:

```powershell
python portable/tests/enhanced/workspace.py --build BUILD --out FRESH_WORKSPACE --screens FRESH_SCREENS
python portable/tests/enhanced/run.py --build BUILD --out FRESH_REGRESSIONS
python portable/tests/enhanced/invariance.py --build BUILD --out FRESH_PASSIVE
```

The workspace suite runs 12,108 model checks, persistence/rejection controls,
normal shipped startup, real HWND operations, keyboard/float recovery/close,
snapshot-before/after checks, UIA and eight captures. Children are bounded/joined.
The retained enhanced regression fixtures explicitly select the phase 1 comparison
host; they continue to test rebirth, executor delivery and the phase 3 activation
XFAIL, rather than silently dropping their hosted-panel preconditions.

The full passive harness retains contracts/native-world controls and adds a real
Win32 workspace group with stationary, repeated and layout-stress lanes. Stress
runs dock/split/tab/float/collapse/hide/reveal/preset/reset and file roundtrips at
source seams, alongside the existing copy/raster stress. Counters require actual
native operations, successful roundtrips and zero snapshot/model errors. It still
compares every named raw view, SaveRec projection, RNG, logical/UI state, clock
and audio; no new masks. Repeated baseline differences remain failing results.

Requested registration: add `workspace.py` as a required workspace suite, retain
its UIA result and scale/hardware limits, and retain `invariance.py` as a strict
differential report. The task does not edit `tools/` or top-level `tests/` gate
registrations. Port suites and the 58-lane acceptance run remain independent.
