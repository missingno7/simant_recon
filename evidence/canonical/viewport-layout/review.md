# Current viewport layout: conditional bound and unresolved gate

Result: **no correction, no admission; the global map-viewport-grid-layout gate remains unresolved**.
This current packet concerns canonical S26:m39C7 viewport setup and root:m0250
cache invalidation, shipped HCEGANT geometry for profiles 0 and 8, and the direct
root-window geometry writers described below. A successful run corroborates the
conditional static relationships; it does not prove whole-game reachability or
authorize a source correction.

The runner uses current whole module files and the current support tools, verifies
each source against src/program.json, compiles with the pinned period compiler,
and differentially executes the bodies against the original hash-locked DOS
executable. resize-receipt-current.json pins sources, both compiled objects and linked code,
program/manifest read-time hashes, assets, packet files and imported tool files.
resource-observation.json contains decoded metadata only. The receipt grants no
acceptance and records the tested boundaries explicitly.

Both runners require a fresh --out directory strictly beneath repository build/.
They locate the repository dynamically, disable import bytecode writes and do
not write evidence or canonical files. The resize runner also observes resources;
the resource runner is available for an independent metadata-only check. Runtime
requirements are the current tools/behavior.py dependencies, its pinned Unicorn
environment under build/deps/unicorn, and the current pinned compiler profile.

```
python evidence/canonical/viewport-layout/resize_probe.py --out build/current/tests/viewport
python evidence/canonical/viewport-layout/resources_probe.py --out build/workers/viewport-proof/resources
```

## Conditional cursor/control invariant

Actual original disassembly and canonical source establish the dynamic dimension
guards and the absence of a bottom cap. That alone does not show that ordinary
UI input can supply arbitrarily large resize rectangles. A sufficient narrow
premise is the **actual fresh resize control centre plus later in-screen cursor
position**, with a nonnegative menu bottom and the selected resource geometry.
The only direct source caller of o26_39C7_0671 is f_218D_02D5's event F084 branch;
it passes NULL. The resize routine therefore queries the registered F084 rectangle,
takes its centre, warps the cursor there, and computes the later delta from it.

For HCEGANT window 0, f_2505_06B9 constructs that rectangle from current root
geometry: border byte 2 and bitmap 70 kind 2's 16-by-16 extent. Thus

```
resize start Y = old root bottom - 10
raw new bottom = old root bottom + cursorY - startY = cursorY + 10
```

Missing flag 1000 is therefore insufficient by itself to establish overflow.
If the later cursor satisfies `0 <= cursorY < screenHeight`, the raw new bottom
is at most `screenHeight + 9`. The resize path's top is unchanged; the source
constraint requires it strictly below the menu bar. With a nonnegative menu
bottom, top is at least 1. Minimum root height is 280. Grid snapping truncates
the delta toward zero: a positive delta cannot exceed the raw target, and a
negative delta cannot exceed the old height. Consequently a resized root obeys

```
new root height <= max(old root height, screenHeight + 8, 280).
```

Move preserves root height. Zoom's first constraint call preserves the old
extent while moving the root; its second call targets screenHeight. With a
positive top, the targeted height is below screenHeight, and truncation of a
negative delta cannot increase the old height. Restoring zoomRect restores an
earlier root extent. These facts preserve the same conditional bound through
move, zoom and resize, provided root controls stay fresh and the listed input
premises hold. The uninitialized preliminary `r.right/r.bottom` in zoom is not
used as a height proof: mode 0 writes all four edges from the old Win rectangle
plus a translation before it returns.

## Storage consequence within that conditional domain

The pinned HCEGANT root has flags 050E, min 252-by-280, grid 16-by-16 and initial
origin `(14,22,404,357)`. Kind 9 object 0 changes the initial height to 325 for
profile 0. HCEGANT has no `(8,9)` record; profile 8 retains height 357. The SHARED
index contains neither of these root/offset records. This is a typed observation
of the pinned corpus, not a statement about language/alternate packages.

Source window constraints give root width strictly less than screen width.
For the two current 640-pixel profiles, the 16-pixel width grid preserves the
initial width's residue 4, so root width is at most 628. Shipped object constraints
give object 4 width = root width - 52, height = root height - 36. LoadTiles leaves
the tile dimensions at 16 for profiles 0 and 8. The conditional maximums are

| Domain | Root height bound | Object 4 tile bound | Largest flat word index |
|---|---:|---:|---:|
| profile 0, 640x350 | 358 | 36 columns, 21 rows | 835 |
| profile 8, 640x480 | 488 | 36 columns, 29 rows | 1155 |

The fixed cache contains indices 0..1199. These inequalities bound the two
dynamic invalidation writers' *physical footprint* without relying on a baseline
rectangle or finite passing tests. The tight observed menu-bottom-17 domain is
smaller: positions remain 22 modulo 16; root heights are 5 modulo 16, producing
rows 17..19 (profile 0) or 17..27 (profile 8), with columns 13..36. Those tight
sets are conditional on this menu/control configuration, not global reachable
dimension claims. A width beyond 40 by itself would also be insufficient to
show crossing the physical allocation: the relevant flat address is `40*y+x`.

The one byte-per-cell cache 1114 is independently protected by f_0250_129E's
fixed `x<40`, `y<30` guard. Spider and balloon cache invalidation paths use fixed
0..1199 linear guards. The full clear is exactly 0960 bytes. They provide no
extra storage after the word cache.

## Writers and consumers reviewed

* m0250:f_0250_0E15 is the only direct dimension producer: object 4 rectangle,
  signed division by tile dimensions, vertical count plus one. The draw hook
  and both m00BA opening/geometry-change callbacks refresh it. Scroll clamping
  changes 0508, not the grid's dimensions. TileIsVisible tests absolute map
  coordinates against scroll plus dimensions; ZapEuMapAt subsequently indexes
  using those absolute x/y values. No unproved relative-coordinate correction
  is supplied.
* m20E8:win_LoadAllWindows resets 45 Rects and copies the selected kind-9
  record's first 320 bytes. win_LoadWindow applies the cached origin to object
  0. win_Open's flag-1000 branch saves the old origin and translates it;
  win_Close restores it. Neither branch runs for shipped root 0's flags.
* S26:o26_040F persists object 0 x/y/width/height after a move. o26_0671 adjusts
  width/height and recalculates objects; it does not immediately write
  win_offsets. Zoom saves/restores the source zoomRect. Both move and resize
  remove and reinstall active controls through f_2505_08EA/f_2505_0831 after
  refreshing geometry.
* m23AE:win_UnlockWin writes the current origin to win_offsets during the
  conditional unload path. This can retain a previous extent; it does not
  generate a new one. No maximal extent follows from the 45-Rect owner.
* f_22BF_00DD's direct callsites change objects 1602 and 1A01. The rect-setting
  f_20E8_0903 has no direct source callsite. win_Swap callsites swap windows
  0100/1900. None of those direct paths sets root 0 geometry.
* The current S09 SaveRec table has no entry for win_offsets, 10DE, 10E0,
  110C, 1114 or 15C4. Its ordinary Load path is therefore not a direct geometry
  writer. This observation is not an exclusion of unrelated computed aliases.

## Current execution controls and their exact scope

Ten resize pairs execute original DOS code and separately compiled current whole
S26 source. In both VMs, actual DOS lock/repoint/iterative win_Recalc/unlock,
F084 rectangle lookup, f_00BA_01C3 and f_0250_0E15 run. Rendering, cursor warp,
button lifetime/delivery, unrelated control callbacks and final control-list
rebuild are explicit models. Existing resource bytes are loaded into isolated
VMs at runtime; they are never emitted into C or linked into an executable.

Eight fresh-icon/in-screen controls agree and stay in bounds, including maximum
widths and a moved root whose bottom is outside the screen. The out-of-screen
cursor control reaches 31 rows; the 96-pixel-stale icon reaches 33 rows. These
are negative contrasts for the new premises, **not shipped-resource/UI witnesses**.

Two further pairs compile current whole m0250 and demonstrate the physical
consequence under a 22-by-31 viewport. ZapEuMapAt(1,1,30) and
InvalEuMap(1,30,1,30) each write word index 1201 at historical 50F6:1F26.
That address is the separately owned spider image width `fd_50F6_1F26.x`;
1234 becomes FFFF, while its following word stays 5678. This is accidental
cross-object memory overlap under the historical layout, not evidence that
the logical map cache intends extra rows or that the source owner should be
expanded. Moving objects under independent linkage changes that accidental
effect. No padding, clamp or larger owner is proposed.

## What remains to close the gate

This packet supplies a sufficient premise, plus controls which
fail when that premise is removed. It does not discharge the global gate.

The remaining narrow obligations are: prove every later cursor sample during
resize belongs to the stated domain; prove F084 is always the fresh root control
when root 0 is active; and close menu-top and resource-selection domains. The
mouse initializer requests width/height-minus-four ranges. Keyboard repeat has
explicit lower and upper bounds. Mickey mode has an upper cap, but its Y
underflow branch uses `XOR DX,BX`, not `XOR DX,DX`; it does not prove nonnegative
Y. Do not substitute the intended cursor behavior for that actual instruction.
An upper bound alone is insufficient: the signed 16-bit subtraction of a
positive resize origin from a sufficiently negative cursor coordinate wraps to
a positive delta. This is an arithmetic counterexample, not an observed ordinary
resize trace. The common supported domain excludes command-line overrides but
does not exclude `BUG=MSMOUSE` or bind the mouse driver version, so a particular
emulator's absolute-coordinate behavior cannot close the general input premise.
The absolute handler 0445 itself writes
CX/DX directly, and programmatic 09E9 warps also store raw positions, so an
all-path bound cannot be substituted for their external/platform contracts.
Profiles using other resource packages, optional language overrides, arbitrary
function-entry states, returning failure paths and unrelated computed alias
gates remain outside this conditional proof. None is silently clamped or given
invented storage.

No declaration/body correction is proven. EXACT remains the historical authority
for the tested bodies; finite equality corroborates the static relationships
above and grants no new acceptance category. No padding, clamp or larger cache
owner follows from these controls.
