# Portable menu model

This model reads the actual menu block from `SHARED` database kind 6. Startup
in `src/S20/m39F1.c` tries id 1 outside 320-pixel mode, then id 0; 320-pixel
mode uses id 0. The current pinned assets contain id 0 (514 bytes) and not id
1. `src/S17/m384C.c:o17_384C_0039` loads the record and relocates its relative
pointer tables in place. The portable parser retains those offsets into an
owned record and bounds every string mutation by the next referenced string.

`src/root/m1FD2.c:SetMenuItemState` indexes `items[id >> 4][id & 15]` directly.
`f_1FD2_0135`, `f_1FD2_0198`, and `f_1FD2_021B` instead select a non-title item
with `(id - 1) & 15`. The two APIs remain separate because source callers rely
on that difference. `src/S11/m35F5.c:SetMenuEntries` exercises both.

The draw plan models `f_1FD2_0663` in command order: source color mode 1, the
bar fill when requested, then the titles when there are at least two. It uses
the source gap formula and returns title positions/rectangles. Text commands
retain the menu bytes and identify whether `f_1FD2_0008` must clear the first
byte's high bit and select color mode 3. `src/S17/m384C.c:o17_384C_0184`
supplies the associated region ID `index - 0x200` and rectangle dimensions.
The host still owns font/palette callbacks and raster output. The separate
`interaction.c` model implements the recovered title-targeted pull-down loop
from `src/S10/m35F5.c:o10_35F5_0384`: it builds the source dropdown and row
rectangles, selects the first enabled row, tracks pointer/key/event inputs,
and returns the source command ID. `portable_menu_interaction_init_from_bar`
connects the interaction model to a parsed resource menu and draw-plan title
rectangles; `portable_menu_title_hit` exposes the source title hit test.
Popup/context menus (`menu_index == -1`) and SDL event collection remain
host/unsupported boundaries. The finite differential does not establish full
menu-system equivalence.

`dropdown_render.c` adds a source-command plan and an indexed BIOS-font raster
executor for title-targeted dropdowns. The plan follows the S10 open order:
save area at the caller, mode 1 and the two negative-width `f_1CE2_01F8`
outline passes, then each padded row through `f_1FD2_0008`. It preserves the
source mode attributes, exact ordered rectangle arguments/colors and row text
including the high-bit state marker. Original S00 glyph code reads the
g3DE0/g3DE2 foreground/background bytes and computes their low four-plane
colors; the pattern attributes (including the disabled-row value 0x30) are
not read by that glyph path. The source primitive driver is S00
o00_31AD_16A9 (fourth g3DF8 entry); it unsigned-swaps reversed endpoints and
fills the half-open rectangle with the low color nibble. The indexed raster
executor uses those source rules and clips pixels to the saved dropdown
rectangle while restoring the caller's prior framebuffer clip. It accepts a
caller-supplied reference BIOS font: the current all-menu asset smoke uses
DOSBox Staging v0.83.0 8x14 glyphs, not a claim about the original host BIOS.
The caller still owns saving/restoring the saved pixels and applying returned
command plans; popup menus remain unsupported.

`python portable/tests/menus/run_dropdown_render_trace.py` records the direct
original-DOS primitive/text trace comparison and resource smoke receipt. Five
title-geometry profiles match the original for all mode tuples, eight outline
primitive calls and four text rows. A separate asset check rasterizes all five
enabled title menus from actual SHARED kind-6 id 0 using the pinned DOSBox
Staging reference 8x14 glyph table, verifies highlighting and exact saved
rectangle restoration. Source anchors establish the primitive coordinate and
color rules, but the receipt does not compare DOS VRAM bytes against native
pixels or claim SDL integration.

The focused model test is source-derived and checks the actual asset parser,
mutation addressing, safe string replacement, and draw-plan equations. The
separate interaction runner compares the native model with original DOS
`o10_35F5_0384` across directed key, mouse, disabled/separator, cancellation,
and forwarded-event cases; it also checks title edges and state gating against
the real SHARED menu resource. These tests do not claim complete menu-system
equivalence.

Run the reproducible strict test and create its pinned receipt with:

```powershell
python portable/tests/menus/run_menu_model.py
```

The receipt is written to `build/portable/menu-model/menu-model-test.json`.

Run the source-backed menu interaction differential with:

```powershell
python portable/tests/menus/run_menu_interaction_differential.py
```

Its pinned receipt is `portable/tests/menus/evidence/menu-interaction-differential.json`.

The dropdown command trace and real-resource raster check are run with:

```powershell
python portable/tests/menus/run_dropdown_render_trace.py
```

The receipt is `portable/tests/menus/evidence/dropdown-render-trace.json`.

Pinned inputs used by the test:

- `SHARED.NDX`: `e172f030c11f417af4b5be34dacbda9a63f157820827b40d62c08ca2c6ea7477`
- `SHARED.DAT`: `aa0d2342510f99abf57a685ea93178d9dd8d2d5be1e65b556c9b27f974012750`
