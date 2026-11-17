# Enhanced style draft: ordinary SimAnt windows

Approved target, 2026-11-16; implementation notes in [build B](build-b.md). **Undocked
enhanced mode stays close to Windows 3.1 SimAnt**. Keep its window families,
titles, natural client sizes, triangles, graphs, cards, menus and command meanings.
Improve text/art rendering and DPI handling. Smooth scrolling and zoom belong to
world views. Move embedded command columns/rows into two ordinary control-panel
windows; do not turn the other windows into redesigned inspectors.

Review images and the per-window evidence/relocation tables are in
[`build/workers/enhanced-style/mockups/README.md`](../../build/workers/enhanced-style/mockups/README.md).
These ignored images require local game assets. They are static targets, not an
runtime capture or proof of action equivalence. Actual build B readbacks live in
`build/workers/enhanced-build-b/screens/` with their own receipts.

## Palette and rendering

Use SimAnt's earth, leaf, yellow and red cues around quiet native text surfaces.
The actual captured game palette supplies earth `#927138`, soil `#552c04`, leaf
`#006510` and yellow `#FFF304`; interface neutrals and the darker red are ours.
Preserve the indexed artwork and its transparency. Bitmap labels/fonts are
replaced with native system text, while pictures and icon shapes remain shipped art.

| Use | Foreground / background | Contrast |
|---|---|---:|
| Body | `#242B21` / `#F5F2E8` | 13.00:1 |
| Secondary text | `#59604E` / `#F5F2E8` | 5.84:1 |
| Inactive caption | `#242B21` / `#DBD6C5` | 10.01:1 |
| Active caption | `#F5F2E8` / `#552C04` | 10.72:1 |
| Links and focus | `#005C81` / `#F5F2E8` | 6.58:1 |
| Control boundaries | `#817C69` / `#F5F2E8` | 3.73:1 |
| Green/red meter cues | `#006510`, `#A02D28` / `#F5F2E8` | 6.53, 6.46:1 |
| Map emphasis | `#FFF304` / earth `#927138` | 3.89:1 |

Ratios use sRGB relative luminance; the scratch `qa.json` records the calculations.
These test solid color pairs, not every background pixel in game art. Yellow
gets a dark boundary on light content, never yellow body text on cream. Keep
numeric health/population labels and warning triangles so color is redundant.

## Text, spacing and controls

Use the platform UI font (Segoe UI on Windows), normally 12–14 DIP, with native
text measurement, antialiasing and symbol fallback. Keep the original compact
control forms; grow their labels for system text scaling rather than shrinking
text. Space in 4 DIP increments, normally 8 DIP between controls and 8–12 DIP
inside frames. Native title strips are approximately 28 DIP. The review plates
use 125% content scale; they do not certify a physical DPI configuration.

Buttons retain SimAnt's shallow rectangular bevel, shipped icon cues and original
selected/disabled meaning. Behavior and Caste retain the triangle, Auto/Manual,
allocation values, help and original Set 1–3 controls when their source group is
visible. These allocation sets are game controls, not workspace presets. History
retains its series selectors and graph; Info retains cards, Previous, Top Card
and links. Use shared commands for the menus and relocated controls. Keep world
scent, map scent, and the two help/tool contexts distinct.

## Window chrome and attachment

Each window has its own draggable title strip. Game/world windows have resize,
maximize/restore and close; Map, Yard/House, Behavior, Caste, History and Info
keep fixed natural clients and close. The original game-child flags provide no
minimize boxes; do not reinterpret DOS Lower as Minimize. Only the main frame
has the usual minimize/maximize/close trio. Original ribbons provide no close,
resize, minimize or maximize affordance, so the two new control windows retain
titles without those buttons. Status retains its source Continue task and no
invented close outcome. Full evidence and the Mac uncertainties are in the table.

Drag a title to a main-client edge: a thin outline shows the attachment bounds;
release attaches that same window, retaining title, controls and natural size.
Drag away detaches and restores its last floating bounds. Escape cancels. Fixed
windows do not stretch to consume an edge; a growing world window alone may be
resized. Adjacent attached windows remain separate windows. There are no tabs,
groups, compass, splits, collapse controls, workspace presets or Move Panel UI.

Keyboard: F6/Shift+F6 cycles windows; Tab traverses controls. Alt+Space opens the
focused window's system menu: Move; Attach to Edge > Left/Right/Top/Bottom;
Detach. Arrow keys move, Enter commits and Escape cancels. These are proposed
native system-menu entries, not extra game-menu commands. Ctrl+F4 closes only a
closable ordinary window; Alt+F4 on the main frame requests the original Quit
transaction. Persist each window's attachment edge/offset and floating bounds
in DPI-independent units; recover title strips onto a visible monitor. Store
layout separately from game saves.

World clients have no scroll bars: middle-drag pans; left input retains original
world gestures, held tools and double-clicks. Extra read-only world views also
allow left-drag pan. Wheel zooms around
the pointer; Shift+wheel pans; Ctrl+Plus/Minus and Ctrl+0 zoom/reset. These are
world-only bindings; text fields keep native editing. Preserve original source
navigation/action contracts and modal waits; passive layout never changes game
state. Smooth rendering must not add a second simulation/camera authority.

Proximity menus use the same paper, brown selection and source labels as the
native controls. Keep enabled and checked states from the source transaction.
Anchor command menus and prompts beside the initiating pointer, clamped to that
monitor's work area. Targeting prompts are nonactivating and click-through;
menu cancellation and closing compatibility dialogs restore the originating
keyboard focus. Retain the complete actor scene while a source wait is open.
The implementation and current compatibility boundary are in
[menus.md](menus.md).

Behavior/Caste retain the source's white triangle, bevelled coloured edges,
shipped knob, colour-framed labels and white bar panel. Use source bar colours
and actual object visibility/check state. Percentage inputs are editable numeric
fields, committed on Enter/focus loss and mapped to original triangle events;
show their actual quantized results. Complete the initial parent/child paint
before input. See [the owner follow-up](presentation-followup.md).

## What replaces phase 2

Keep its immutable assets, coherent snapshots and separation of native layout
from source logical lifetime. Replace the tab/split tree, dock compass, collapse,
Move Panel buttons and Play/Colony/Research/Minimal presets with the attachment
model above. Restore the full File/Window/View/Options/Speed menu and its source
enabled/check state. The review uses the source label **Unpause** because the
captured game is paused. Builds A/B implement that model; their exact test
receipts retain the raw invariance, accessibility and physical-DPI limitations.
