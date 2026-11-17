# Startup, icon masks and allocation controls

The 2026-11-17 owner follow-up keeps the original source transactions. All
changes are in the portable presentation and its regressions.

## Startup follows the source lifecycle

`CurGameType >= 0` was an invalid readiness test: initial zero is also the valid
Tutorial type. A presentation observer now records a successful return from
the source `NewGame`. That return follows `DoScenario`, successful load or
`RandYard`, `SetDefaultWindows`, centring and `UpdateEdit`. No timer decides
whether a world exists. Tutorial zero remains valid.

Both native world windows and hosted native content wait for the same published
`world_ready` snapshot. This also fixes an ordering gap between source return
and the next publication: content clients previously could show with a stale
startup snapshot. A negative source game type hides them again. A new-game
chooser during an existing game retains the source's existing world behind it.

The source startup presentation remains visible and accepts its existing input:

| Source stage | Presentation before the first successful game |
|---|---|
| `ShowIntro`, 0300 | Source title/logo client; no native world/content clients. |
| `CustomerIDDialog`, 1E00 | Source registration client. |
| `DoScenario`, 0200 | Source SELECT A GAME client, with Tutorial, Quick, Full, Experimental, Load and Cancel. This is the DOS game/scenario choice; an extra chooser is not invented. |
| Load choice, 1600 | Existing source Load Game/file client; no empty native world behind it. |
| Successful `NewGame`, including Tutorial | Native worlds, control panels and source-open content clients become eligible together after publication. |

## The source mask survives native drawing

`EnhancedArt` already preserves type-3 bitmap masks as transparent index 255.
The GDI indexed helper incorrectly replaced 255 with paper colour. A shared art
paint now preserves the destination using AND/OR masks, without a colour key
that could erase an opaque palette colour. Map spider/foot/mower icons, Info
illustrations, allocation knobs and picture controls use this drawing path.

The separate world and Yard software compositor was audited: its `image`
primitive already skips 255. Its terrain/life compositing remains unchanged.
All 252 shipped pictures are checked by the live GDI regression on a coloured
destination, alongside the existing independent decoder checks. Every masked
pixel must leave that destination unchanged; opaque pixels must match the live
palette. This includes every map, Yard and inspector picture in the catalog.

## Editable allocation percentages

Behavior and Caste use editable integer fields with a visible percent suffix.
Enter or focus loss commits. Leading/trailing whitespace and an optional `%`
are accepted; blank or malformed text restores the current source value without
submitting an action. Values are clamped to 0–100. Escape cancels an edit.
Source count/percentage display toggles retain their original action; the
editable fields continue to explicitly request percentages.

For a typed axis and percentage, the engine-side adapter enumerates the source
triangle's integer pixels. It uses the original `IsPointInIsoTri`,
`BoundPointToTri` and `GetTriLatDist`, then chooses:

1. The smallest error between the requested percentage and the source display
   formula `(level * 100 + 0x3fff) / 65535`.
2. The smallest sum of changes in the three source levels.
3. The first point in source row/column order if still tied.

The source grid has gaps. The fields display the actual quantized source result,
including any adjustment to the other two values. There is no native assignment
to levels, Auto/Manual, presets or `IdealCaste`, and no native normalization to
100. The adapter delivers the chosen original 120D/130D event; `ProcModeEvent`
or `ProcCasteEvent` performs its normal tracker, preset copy and release tail.

The original DOS control assets 4600/4620 and knob 1400, source
`DrawControlLevels`, and the retained DOS-style window captures informed the
appearance. The Win16 resource inventory corroborates the same window families
and bitmap content; it is not a DOS oracle. Native clients retain their natural
210 × 170 size, with a white bevelled triangle, yellow/brown edges, shipped
knob, colour-framed labels and a white bar panel. Bar/label colours copy the
source's `g_1B4A`/`g_1B46` through `gfx_colour_translation`. Brown captions and
owner-drawn cream/red buttons adapt this to the approved native theme. This is
an intentional adaptation, not a claim of pixel equality to DOS or Win16.

## First show is complete

The shipped 4600/4620 background already contains Set 1–3 labels. Hiding their
source hit regions does not erase those labels. Native clients had omitted that
static decoration, making it appear only after interaction. Inactive Set labels
are now painted underneath the source-driven buttons from the first frame.
Actual button visibility, enabled and selected state copies source object flags
for Help, Auto, Manual and Set 1–3. A hidden hit region stays noninteractive.

First show/reopen paints the parent and all native children once, after showing
the client. This applies to all hosted clients and owned native panels/worlds.
Together with the shared published-readiness test, it avoids stale initial
state and deferred child pixels. Later refreshes retain buffered painting and
change-only updates; standard controls do not repaint in the steady-state test.

The refresh interval is measured from **paint completion**. Previously a GDI
paint taking longer than 50 ms made the next refresh immediately due. Under
load this repeatedly repainted instead of letting source input/time polls
advance. Duplicate per-frame content paints now share the same cadence;
first show, `WM_PAINT` and explicit readbacks still paint immediately. A guard
prevents nested full refreshes. No source timing quantum or game delay changed.

## Regressions and private desktops

`portable/tests/enhanced/presentation.py` registers eight cases: Quick startup,
Tutorial startup, Load choice, first allocation frame, reopened allocation
frames, all art masks plus a real Map spider, typed percentages, and slow paint. First-frame
captures occur in the first native presentation, before any allocation input
or test-forced repaint. Visibility/check state, populated numeric fields and
source values and the static Set-label pixels are checked there. The numeric case sends 72 edits over all six
axes, split between Enter and focus loss; it observes actual source events,
all three levels, presets and `IdealCaste`, including invalid and clamped input.

```powershell
python portable/tests/hidden_desktop.py portable/tests/enhanced/presentation.py --build BUILD --out FRESH
```

Every GUI registration uses the supervisor's corrected `install()` policy.
CPython ignores `STARTUPINFO.lpDesktop`; assigning that field on `Popen` was not
a private-desktop mechanism. The launcher now relaunches the entire Python
command with **CreateProcessW + lpDesktop**, in a kill-on-close job. Inner
runners verify their own desktop name. The outer monitor rejects any job
window on the input desktop with exit 97. No desktop switch or visible fallback
is used. Captures read only process-owned windows.

Historical receipts from the first delivery are retained, but their Popen
desktop assignment is not evidence of isolation when launched from an owner's
input desktop. The follow-up receipt identifies the corrected launcher and
the new verification round. Results, screenshots, hashes and the exact start
command are in [RESULT.md](../../build/workers/enhanced-menus/RESULT.md).
