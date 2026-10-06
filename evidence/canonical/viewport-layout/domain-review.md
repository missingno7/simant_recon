# Supported profile-8 viewport/input closure

**Verdict: PROVEN only for the narrowed domain below.** With a fresh active
F084, the per-axis cursor invariant, HCEGANT profile 8 at 640x480, 16-pixel
tiles, and a nonnegative menu bottom of 17, the viewport cache bound is 29 rows
by 36 columns (largest flat index 1155). This is supporting evidence for the
supervisor's authoritative domain update; it does not resolve the unchanged
broader `shipped-default-vga-successful-lifetime` domain.

## Supported-domain premises

The proof assumes one ordinary successful startup and nominal window/resource
lifetime, empty launch arguments, `BUG` absent or not case-insensitively equal
to `MSMOUSE`, and an initially clear `g_432A`. Mouse setup must receive
`BX != 0700h` from the **first, pre-reset INT 33h function 24h** call, so the
non-mickey path remains selected. This packet covers successful installed
driver setup; it does not claim the no-driver stub path.

The installed driver premise is operational: INT 33h functions 7/8 keep their
requested inclusive ranges effective, the standard INT 33h ABI is respected,
and every function-0Ch callback supplies bounded absolute `CX/DX`, including
button-only callbacks and callbacks after function-4 warps. At 640x480 the game
requests X `[0,636]` and Y `[0,476]`. This is an external platform premise; the
game's `_0445` handler directly copies callback coordinates. The reference is
the [Microsoft Mouse Programmer's Reference](https://www.bitsavers.org/pdf/microsoft/mouse/Microsoft_-_Microsoft_Mouse_Programmers_Reference_2nd_1991.pdf).

The resource/display premises are the pinned HCEGANT database, profile 8,
640x480, 16x16 tiles, successful resource operations, the nominal control and
save lifetime, and the guarded menu state described below. Alternate
databases/profiles, noncompliant drivers, `BUG=MSMOUSE`, driver BX `0700h`,
arbitrary entry state, corrupted descriptors, foreign API activation, computed
aliases, and exceptional continuations remain outside this result.

## Cursor sample invariant

The F084 resize branch in `src/root/m218D.c:167-169` calls resize synchronously
with a null event. `src/S26/m39C7.c:299-361` looks up F084, reads its center,
warps once to that start, sets `pt=start`, then samples shared X and Y separately
inside `ButtonHeld()`. It does not dispatch application events. The first delta
is zero. Separate reads are sufficient because the bound is per-axis.

The invariant is **not** that all samples lie on-screen. It is:

```text
sampleX in {startX} union [0,639]
sampleY in {startY} union [0,479]
```

The one raw start warp seeds each exceptional coordinate. Afterward:

* `_0445` accepts bounded absolute mouse callbacks under the driver premise.
* `_051F` timer movement clamps both axes to `[0, extent-1]`.
* `_0747` center commands set both axes to in-screen values. Horizontal edge
  commands replace X and preserve Y; vertical edge commands replace Y and
  preserve X.
* `_09F7` copies both existing globals without clamping. This includes the
  `_0747` L0803 shift/copy path and the horizontal/vertical edge paths that
  converge on L09E3.
* `_0A1B`/L0A21 button emulation copies both existing globals through `_0445`.

The probe's moved-root control uses the pinned initial width and height with root
top 470: F084 start is `(408,817)`. A left-edge command yields a modeled
sample `(6,817)`, so `deltaY=0`; that off-screen Y is exactly `startY`, not a
new unbounded delta. The timer replacement control takes `(408,817)` through a
one-up repeat and the upper clamp to `(408,479)`. The mouse replacement control
uses bounded callback coordinates `(636,476)`. These are deterministic source
and arithmetic controls, not a captured hardware-driver session.

The complete direct `_09E9` and `_0C80` caller census is guarded in
`domain-facts.json`; the menu/focus/move callers cannot run on the blocked
application stack. The raw `_09F7` and `_0A1B` replay routes remain explicitly
included. `ButtonHeld`, `StillDown`, tick polling and key-state polling do not
write cursor coordinates or dispatch application events.

## Callback and control composition

The callback facts follow the accepted
[menu-title ownership review](../../../../evidence/canonical/menu-title-owner/review.md:9).
`_0AA3` installs `_0CB3` in `g_5FFA`; `_0445` invokes it; `_0CB3` traverses
18-byte descriptors; `_0CEF` calls the descriptor callback at `+8` with event
code at `+0x0c`. `g_6004` and `g_603A` use `_030F`, the event enqueue adapter.
Cursor descriptors `g_6016`/`g_6028` use `_0D4B`, the cursor draw/save/restore
path. The sole nominal caller configuring generic `g_6016` passes `_0D4B`;
`f_1FD2_0390` has no caller. The configured VGA drawing pointers used by cursor
rendering are display primitives (`g_9168`, `g_9128`, `g_9184`), not menu/focus
warps. The package guards these bindings and rejects a callback-to-raw-warp
mutation.

F084 is generated from the **current root/window rectangle**, after applying
root border byte 2 and bitmap `0x70` size 16x16. Its rectangle center is
`(root right - 10, root bottom - 10)`. It is not built from object 4. Object 4's
separate geometry is derived by `win_Recalc` from its modes and references:
left `root left + 50`, right `root right - 2`, top `root top + 19`, bottom
`root bottom - 17`; its size is root width minus 52 and root height minus 36.
The decoded object-4 modes are `(1,2,3,4)`, references `(3,3,0,0)`, and
border byte 19. F084 placement reads the root object's separate border byte 2.

The add/remove pair uses fixed tag F084. Lookup delegates to `_0C42` and the
first-match `_0A89` tag search, so a matching tag alone is insufficient: the
nominal lifecycle must retain one active root decoration. Open removes the old
top controls before adding the new top's controls; close removes the departing
top and installs its successor; send-to-back performs the same transition.
Move, resize and zoom remove and rebuild controls after geometry changes. Root
0 is the pinned resizable HCEGANT window.

Normal `win_LoadWindow` loads allocator type 1, restores the cached object-0
origin/size and repoints objects. Demand reload routes through
`f_23AE_0069`; a reloaded window must pass through open/recalculation/control
installation before resize dispatch. Root flags `0x050e` omit the `0x1000`
translate/save-restore and `0x0800` closed-unload-offset-save branches.
`win_LoadAllWindows` is initial-only in the census, cached extents come from
the profile resource or prior bounded moves, and the reviewed SaveRec has no
window-offset/viewport entry. The probe guards stack ordering, reload type and
rebuild paths; it rejects a stale-control mutation. Unreviewed computed aliases
and corrupted control state remain excluded.

## Menu-bottom and signed arithmetic

`f_1FD2_0663` selects the current display/font state, copies the screen rectangle
through `f_1CE2_000C` (`g_5A9C`), and writes
`fd_50F6_393C.bottom = top + g_3DDC + 3`. The screen clip rectangle starts with
top zero; profile-8 display setup updates its right/bottom edges. The supported
VGA font premise is height 14 (`g_3DDC=14`, the retained VGA 8x14 primitive
sets byte `0x0e`), so the derived menu bottom is `0 + 14 + 3 = 17`. The source
formula, screen-top state, font primitive and protected mentions are guarded.
The active 14-pixel font binding remains an explicit supported-domain premise.
The probe rejects a negative-menu-bottom mutation.

DOS `int` arithmetic is signed 16-bit, `[-32768,32767]`. Given menu bottom 17,
the root top constraint is positive and at most 480. Within the corrected
cursor invariant, a preserved `startY` contributes zero delta; an in-screen Y
gives raw bottom `Y+10`. The conservative induced bounds are root height at
most 488 (and at least 280), root width positive and below 640 with residue 4
modulo 16 (at most 628), root bottom at most 968, and F084 start Y at most 958.
The sample-minus-start range is `[-958,479]`. These values and the intermediate
resize geometry fit signed 16-bit arithmetic; the proof does not rely on
unbounded integers or wraparound.

Object 4 therefore has maximum dimensions 576x452. The source producer divides
by 16 and computes `rows=(height/16)+1`, giving 36 columns and 29 rows. The
largest logical flat cache index is `40*28+35=1155`, below the 1200 cells in
`int[30][40]`. These are upper bounds, not a claim that every dimension is
attained.

## Counterexample and limits

The retained original-instruction mickey control remains an out-of-domain
counterexample: with driver absolute coordinates inside requested ranges,
`_03EE`'s `xor dx,bx` lower-Y branch reaches `(636,-32767)`. The retained resize
composition reaches 2046 rows by 36 columns, logical index 81835. Its long
callback cadence and held-button delivery are harness inputs, not a retail
driver trace or captured cache store. This rejects admitting mickey mode; it
does not contradict the narrowed non-mickey domain.

`domain_probe.py --check` replays source/resource/original-code facts and compares
them with `domain-facts.json`. The draft tests keep the mickey and clamp/writer
controls and add callback-to-raw-warp, stale-control/rebuild and negative-menu
rejection mutations. This package is evidence for scoped review, not a whole-game
memory-safety, behavior, or canonical-gate acceptance claim.
