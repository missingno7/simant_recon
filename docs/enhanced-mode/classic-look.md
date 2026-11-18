# Classic / Native look and caption access

Options > Look selects **Classic** or **Native** while playing. Classic is the
default. This is a host presentation setting; it does not dispatch a source
command or change the simulation. Both choices keep ordinary fixed-size
native panels. They do not introduce a DOS desktop, docking bands or a
responsive panel layout.

Classic uses the shipped, immutable FONT2 bitmap font for painted labels and
picture captions, doubled for window titles and menus. Rendering calls the
existing asset font decoder; it neither copies an original raster into code
nor changes the source's current font. Glyphs and picture art use nearest
pixel scaling. Input fields and combo boxes retain native fonts for editing
and caret behaviour. Characters outside the game's glyph set, such as the
native check mark and caption buttons, use the native fallback.

The bright frame treatment uses yellow window edges, white/cyan title bars,
pixel titles, grey faces, black/white chunky bevels and bright health colours.
The Ant panel's MAP, PAUSE and SCENT buttons form a vertical strip. Its world
selection row, Map layer row and inspectors remain native child controls with
the original IDs and source transactions. Native uses the cream/earth palette
and Tahoma labels. Selecting a look keeps window handles, typed dirty values,
source state, masks and original menu enabled/checked state.

The setting is saved with UI scale in `SIMANT-WINDOWS 4`. The next line stores
`scale native_look`, where 0 means Classic and 1 Native. Version 2 layouts load
as Auto/Classic; version 3 retains its scale and defaults to Classic. Invalid
look values are rejected. Reset preserves both scale and look.

## Measurement and spacing

Win32 caches owner-drawn menu-bar item widths. Previously UI scale changed
the drawing font but left those cached widths unchanged. Scale, look and root
DPI changes now rebuild the native menu from the same source resources. A
shared text path measures and paints using the same effective DPI and font.
Shortcut columns have their own measured width and gap; each menu item also
reserves check/arrow padding. A long bar can wrap onto another row on a narrow
work area instead of shortening its labels.

The Map-layer picture buttons have independent wider cells and real gaps;
Black Nest and Red Nest no longer touch. Captions use FONT2 in Classic and
the 10-pixel caption font in Native. The allocation `% / #` button is wide
enough at fractional scales too. Full semantic names remain available to
native control discovery even where the painted label is shorter, such as
Automatic / Manual queen drop.

## Overflow placement

Fixed clients are never reduced to fit a work area. If saved/default rectangles
would hide another panel's caption, or extend beyond the work area, the host
places the visible panels in opening order in a caption cascade on that
monitor. New panels go below earlier captions. When necessary two windows
share a caption row with separate reachable title segments. Z order follows
that same opening order. Reopening a panel gives it a fresh position in the
cascade. Actual visibility, not a timer or assumed startup delay, triggers
placement. Modal/file/help clients keep their cursor placement rules.

This prioritises reachable caption bars. Bodies can overlap, and a fixed
client larger than the work area still extends beyond it; users can bring
its caption to the front, move it or choose a smaller UI scale. The deferred
docking and responsive designs are unchanged.

## Regressions and reproduction

The new registration is ready for the supervisor; `tests/` is not edited here:

```text
python portable/tests/hidden_desktop.py portable/tests/enhanced/classic.py --build BUILD --out OUTPUT
```

It tests both looks, Auto and all seven explicit UI scales at DPI 96/120/144.
Top-level menu bounds come from actual `GetMenuItemRect` results; submenu
measurements are checked against independently obtained FONT2 / Tahoma
extents, including shortcuts. Every fixed panel's visible child controls are
checked for overlap, client containment and caption width. Status also opens
through its original transaction in all 48 combinations.

For 1280×680, 1920×1040 and 2560×1400 work areas, both looks are reset at
100/200/300 percent. The test subtracts higher process-owned window rectangles
from each caption region and requires a sufficiently wide, full-height
remaining segment whose hit test returns HTCAPTION. These injected work-area
and DPI cases do not change the owner's displays or certify physical mixed
monitor behaviour. The source-neutral look/scale/reset matrix compares all
SaveRec bytes and the complete published snapshot without new exclusions.

Private-desktop owned-window readbacks cover all nine fixed panels in both
looks at 100/200 percent, both 200-percent menu bars, the actual Look submenu,
and a reset layout at 200 percent on a 1080p work area. Original comparison
frames come from the existing DOS oracle runner's guest-video capture. No
full-desktop capture or tracked original-derived image is used. Captures,
side-by-side comparisons, exact registrations and results are in
`build/workers/enhanced-menus/screens/` and `RESULT.md`.

The 010E `%` map-toggle defect belongs to the separate map-cache worker. This
change does not edit or reinterpret the S00 converter. Full/Experimental
sweeps retain and list that row's result explicitly.
