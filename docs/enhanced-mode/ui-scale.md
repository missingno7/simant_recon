# Native UI scale and fixed panel sizing

The enhanced host offers **Options > UI Scale** while a game is running:
Auto (per-monitor DPI), 100, 125, 150, 175, 200, 250 and 300 percent. The
current choice is checked. `--ui-scale auto` or `--ui-scale 200` sets the
initial choice; without the option the saved choice is restored. Explicit
percentages are absolute: 200 means twice the logical size, including on a
monitor whose Windows scaling is already 150 percent. Auto follows Windows
per-monitor DPI. An unsupported or missing command-line value is an error.

Changing scale keeps the source transaction, game state, window handles,
editable text and dirty fields. Fonts, control rectangles, native captions,
menu rows, proximity menus, command prompts, minimap content and tooltips use
the new effective DPI. Source hit coordinates are obtained by the inverse
transform. World magnification combines the saved world zoom with UI scale:
100 percent world zoom at 200 percent UI scale draws each world pixel twice
as large. Windows' application frame chrome continues to follow Windows DPI.

The layout file now writes `SIMANT-WINDOWS 3`, followed by the selected scale
and the existing panel records. Version 2 layouts load as Auto; unsupported
versions and scale values are rejected. The existing layout filename is kept
so an owner does not lose saved positions during migration. Reset preserves
the selected scale.

## Full fixed clients

`ws_fixed_content` defines client sizes in logical pixels. Neither an old
saved outer rectangle nor the reset frame placeholders define a fixed
panel's content height.

| Panel | Logical client |
|---|---:|
| Map / Ant Control Panel | 944 × 200 |
| Yard Control Panel | 944 × 152 |
| Map | 512 × 256 |
| Yard | 512 × 226 |
| Behavior, Caste | 210 × 170 |
| History | 320 × 179 |
| Info | 320 × 200 |
| Status | 318 × 186 |

First open, reset, restore and live scaling calculate the required client
from that table and the effective DPI. The SDL-managed windows are sized
through SDL and checked against the resulting Win32 client; moving them
afterwards uses `SWP_NOSIZE`. This matters because changing their outer size
through Win32 alone can cause SDL's nonclient handling to change the client
again. Panels retain their fixed-size window styles. Floating captions are
kept recoverable on their monitor.

Fixed panels are not responsive layouts. A 944-pixel panel at 300 percent
requires 2832 client pixels; a smaller monitor cannot display that entire
panel at once. It is not silently shrunk or clipped to an incorrect client
size. The separately requested responsive layout and docking redesign remain
deferred for the owner's design review.

## Appearance and original comparison

Original DOS guest-video captures, taken through the oracle runner on a
private desktop, show the original surface and Yard control strips, Map,
Behavior and Caste. The native panels now use hard light/dark bevels, yellow
selection edges, earth-coloured group frames, compact labels and cream
surfaces. The control strips group view selection, commands, Map layers,
inspectors and population/health separately. All content buttons use the same
buffered owner-draw path, including the text buttons. Original picture art
retains its aspect ratio and mask and uses nearest-pixel scaling; fonts use
Tahoma at 13 logical pixels (10 for picture captions).

This is an enhanced presentation, not a claim of pixel equality with DOS.
The ignored delivery evidence includes original guest captures and before /
after captures of each native panel in
`build/workers/enhanced-menus/screens/`. No original-derived image is tracked.

An additional first-open issue affected Status: its Continue button could
become visible during the source's open transaction, before the published
owner became 1800. A native click now retains that intent until the actual
source Status window is ready, then sends pointer down/up through its hosted
input path. This preserves the source pointer and current/previous window
events as well as dismissing the original Score loop. This also makes the first-frame
scaled Status regression exercise an immediate click, before other input.

## Regression and cost registrations

Run all GUI registrations through `portable/tests/hidden_desktop.py`, whose
`install()` relaunches Python using CreateProcessW plus `lpDesktop` in a
kill-on-close job. It audits input-desktop windows and verifies each inner
runner's desktop. Never replace this with Popen's ignored `lpDesktop` field.

New registration (the supervisor owns `tests/` and its gate wiring):

```text
python portable/tests/hidden_desktop.py portable/tests/enhanced/ui_scale.py --build BUILD --out OUTPUT
```

The probe checks real HWND clients at 96/120/144 DPI and virtual work areas
1920×1040 / 2560×1400, all fixed panels after reset, child bounds, hit targets,
font sizes and non-resizable styles. It exercises 42 live scale changes,
compares every SaveRec byte and published source command/settings state,
delivers Map hits at 100/150/200/300 percent, and checks CLI precedence,
persistence and an immediate first-frame Status dismissal. Work-area and DPI
messages are injected in the probe; these are not physical mixed-monitor
certificates and do not change the owner's display configuration.

`content.py`, `menus.py` and `minimap.py` accept `--ui-scale`. Focused 200
percent registrations cover prompt bounds, menu cancellation, actor retention,
minimap drag/click/cancel, repaint suppression and camera glide.

The minimap runner now starts once per game mode and reuses the source
transaction for its 37 cases. The sweep has a persistent session protocol:
reuse is allowed only after recovery and an unchanged fingerprint of all
SaveRec bytes, command/settings state, overview (including frozen Map), card
history, graph selection, experimental substates and RNG. A
changed row starts fresh. Recovery sends native Pause twice, checking both
input delivery and restoration. Recovery waits for the actual Pause event,
its released source lease and the expected pause state, so a queued command
cancellation cannot be mistaken for recovery. Actual action-ledger / source-state readiness
replaces blind startup delays. Preparation also waits for the actual native
target to become visible and enabled: source Manual can return before the
next native presentation shows its preset buttons. A preparation timeout is
a failure, never an "unavailable" pass. The five-second modal deadline, recursive menu
coverage and hidden-prompt negative control remain. No invariance mask or
acceptance reference changes.

Exact final registration commands, results, timings, failures and desktop
closure receipts are in `build/workers/enhanced-menus/RESULT.md`. In particular,
the Full/Experimental sweeps exposed an existing unsupported map-colour path:
freezing a spider-marked source cache can feed 0xff dirty sentinels to the
25-colour faithful converter. That failure is retained, not excluded from the
sweep or treated as a successful native transaction.
