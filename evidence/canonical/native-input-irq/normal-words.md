# Normal keyboard IRQ words: branch proof and its resource boundary

2026-11-14. Original instructions are authoritative. Reproduce the executable
controls with `python portable/tests/input_irq/normal_words.py --out
build/workers/irq-normal/recheck.json`, or the full `input_irq/run.py` suite.
The latter also checks the actual native scan adapter's ordinary non-E0, E0
and F0 records. No canonical source, reference tape or state classification
changes. `normal-words-proof.json` pins the reviewed sources and asset identities;
changed sources/resources invalidate the static proof until reviewed again.

## Decision

For the **supplied HCEGANT 640-wide EGA/VGA resource domain**, every possible
DOS wrapper DX and native zero take the same externally meaningful branches:
OpenMiniMapWin continues without centering/redrawing; SpecialXfer rejects the
coordinate with SND_REJECT and WindPromptStrs[10]. This includes arbitrary CH,
full CX after E0, BIOS flags in F0, partial horizontal offscreen dragging and
the signed-word discontinuity at 8000h. There is no zero-only branch in this
domain. Keeping zero is justified as a bounded representation difference;
supplying a particular original segment would add no behavioral repair here.
Raw event words still differ and remain compared with own-executable register
replay in acceptance. These words are read, not globally unused.

**The requested all-display-mode conclusion remains undecided.** The 320-wide
arithmetic has a high-segment alias that defeats a universal rejection proof.
The local assets contain HCEGANT, SHARED and SOUND only, not LCEGANT, TDYGANT,
L256NT, MONONT or LRSHARE. `driver_select.c` selects those other resources for
other modes; their reachable window geometry cannot be recovered from the
HCEGANT records. Native currently rejects those video profiles. We neither
invent their rectangles nor call an arithmetic witness a normal-play capture.
The broader hardware-context entry remains OPEN. No adapter value change is
justified by the proved domain, and the task's two proposed outcomes are not
an exhaustive dichotomy over the wider unresolved domain: zero can reject,
some DOS values can reject, and other DOS values can alias a valid cell.

## Producer and real-mode load range

The hook sites are root:1B73:0703 and 067E/0694. With load-image paragraph B,
IRQ09 supplies D=B+DGROUP; INT15 supplies D&FF00h. Neither supplies arbitrary
foreground DX. Initial FA h is `(CX&FF00h)|2`, or full CX after E0. F0 h is
the BIOS low flag byte, not foreground CX. Later FA command-path records use
post-dispatch state; the vertical proof is independent of every horizontal word.
Mouse callbacks keep pointer coordinates and are outside this argument.

Let P be `ceil(MZ load-image bytes/16)+e_minalloc`. A successful ordinary
conventional-memory load requires `0 <= B <= A000h-P`; PSP, DOS, devices and
available heap can only narrow this conservative envelope. No signed segment
assumption or fixed DOSBox load address is used. Paragraphs are physical
real-mode paragraphs, not screen pixels. MZ header bytes and relocation targets
are read from each executable, not taken from native output.

| Executable | Identity / DGROUP evidence | P | Raw D envelope | D&FF00 envelope |
| --- | --- | --- | --- | --- |
| Original SIMANT.EXE | SHA256 aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11; original relocated hook operand 55B3h | 6023h | 55B3h..9590h | 5500h..9500h |
| Current working SOURCE.EXE | current link SOURCE.MAP and hook's MZ relocation: DGROUP 5408h; exact file pin in scratch load-ranges.json | 5DC8h | 5408h..9640h | 5400h..9600h |

Both are contained in **5400h..9640h**, including the cleared-DL values. The
envelope need not assert every paragraph is runnable on every configuration.
It includes all actual possibilities, so universal rejection over it is stronger
than enumerating only one loader's observations. The recorded original D=5DD7h
and working D=5C2Ch are corroboration, not the lower/upper bound argument.
No universal <8000h assumption follows from the startup free-memory check:
EMS and conventional free blocks below a high-loaded executable matter.

## Reachable supplied-resource geometry

All coordinates below are signed 16-bit pixels; rectangles are half open.
Resource kind 0 IDs 0, 1, 20 and 25, actual object operand/mode fields, and
mode-0 kind-9 offsets establish the following. Mode 8 uses the kind-0 defaults.
`win_Recalc` / `_win_CalcObjElement` resolve those references; no use of Event
words participates in rectangle construction.

* Map and yard roots have size 516x324, flags 0406h: title dragging, no resize
  or zoom, no keep-on-screen flag. Their root (L,T) is shared by win_Swap.
  Yard default is (62,62), mode-0 yard offset is (62,18), map default (118,24).
  Yard object 1 starts (L+1,T+2); object 2 is (L+2,T+21,L+515,T+277).
  `SetYardMode(2)` calls win_YardClosed, which reads object 2 and increments
  its left edge. Thus SpecialXfer uses left L+3, top T+21. An intervening map
  rectangle uses top T+20 and is also inside the conservative bound below.
* `win_constrain_drag_rect` requires L<640, L+516>=0, T>menu_bar_rect.bottom,
  T<=H; it does not keep the right/bottom on screen. The menu bar starts at
  screen top 0 and has positive font height+3. Thus the moved root has
  -516<=L<=639 and positive T<=H. Both defaults and mode-0 offsets are positive.
  Including map/yard swaps and any earlier map rectangle, **1<=viewport top<=501**
  is a conservative envelope for H=350 or 480. Left may be -513..642; the
  rejection proof does not require an onscreen left edge.
* Edit object 5 has top T_edit+22; minimap root refers to that object's right+4
  and top, and has size 132x68. Its content is root+(2,2), size128x64. Flags1841h
  keep the popup onscreen and provide no title/resize/zoom control. Opening
  shifts an overflowing bottom to H; otherwise the edit anchor is positive.
  Its content therefore has **top>0 and bottom<=H<=480**. Horizontal opening
  clamps the popup to the screen (content left>=2, right<=638). While this modal
  reader runs its stored miniMapRect is the rectangle fetched by Mini_DrawMapI.
  Edit dragging, resizing and zooming cannot make its stored top nonpositive.

These envelopes intentionally include some unreachable rectangles. The proof
therefore covers all reachable positions without claiming each envelope point
is reachable. Malformed resources, edited save/layout data and integer-corrupted
window records are not normal play. Other display-resource geometry is unknown.

## Arithmetic and branch table

Write W(a) for signed interpretation of a modulo 65536. IDIV truncates toward
zero. The original SpecialXfer at S22:39C7:1607..1653 computes:

```
dy = W(v-top); dx = W(h-left)
if width == 320: dy = W(2*(dy-8)); dx = W(2*(dx+2))
y = trunc0(W(dy-67)/10)
x = trunc0(W(W(10*y)-169+dx)/28)
```

163F/1650 sign-extend AX; 1640/1651 use signed IDIV. The IMUL at 1644 retains
its low word for the following SUB/ADD. Each W above corresponds to the actual
word register intermediate; this is not evaluation in native 32-bit int.
The ordered tests are x>=0, y>=0, x<=11, y<=15. An invalid cell joins16DE,
plays reject and displays prompt10. A valid empty cell joins16A8 (prompt19).
A valid occupied cell stores YMapPnt and calls XferPatch at 169B. Which occupied
cell exists is game state; a value-only proof cannot decide that subbranch.

| Reader / mode | Value class | Branch and intermediate proof |
| --- | --- | --- |
| OpenMiniMapWin, supplied 640 | Every raw/cleared DOS D; every h including E0/F0 | PointInRect false. Positive signed D is >=5400h>bottom; negative signed D is <top. Horizontal failure may reject earlier. Continue at0813; no map conversion/center/redraw from the event. |
| OpenMiniMapWin, supplied 640 | Native v=0, h=0 or normal FA h=2 or F0 flags | v<top, so same false/continue branch. |
| SpecialXfer, width640 | Every raw/cleared DOS D; every h | Valid y requires dividend [-9,159], hence D in {W(top+67+n): -9<=n<=159}. For top1..501 this set lies in59..727, disjoint from5400h..9640h. Actual dividends over the conservative envelope are20936..32767 or -32768..-27140; y=2093..3276 or -3276..-2714. x may wrap or fail first; none can rescue y. Always16DE, reject/prompt10. |
| SpecialXfer, width640 | Native v=0, any h | dividend=-top-67=-68..-568, y=-6..-56. Always16DE, same reject/prompt10. |
| SpecialXfer, width320 | Any DOS D | y valid iff D mod8000h lies in[top+37,top+121] mod8000h. x valid iff W(10*y-169+W(2*(h-left+2))) is in[-27,335]. Both valid: prompt19 or XferPatch according to YMapPopB; otherwise16DE. These predicates decide every word for any supplied geometry. Cleared-DL D must additionally be a multiple of256. Reachability of these geometry/value combinations in missing display resources is undecided. |
| SpecialXfer, width320 | Native v=0 | For ordinary positive top<=501, doubled dy-67=-2*top-83, y<0, reject. Unknown-resource top bounds are not claimed. |
| OpenMiniMapWin, other resources | Every class | Exact predicate remains left<=signed(h)<right AND top<=signed(v)<bottom. DOS D is excluded by any positive onscreen content rectangle; whether every missing resource/placement has this property is undecided. If inside, x=trunc0(W(h-left)/scale), subtract32 for multiplier64; y=trunc0(W(v-top)/scale), and center/redraw iff0<=x<multiplier. |

Conditional low-resolution counterexample, executed in the **original**
instructions: left65/top83, h0102h, D8078h gives dx390, doubled dy58,
vertical dividend -9, y0, horizontal dividend221, x7: valid cell. Keeping h
and geometry but using v0 gives y=-24: invalid. This D is inside both loader
envelopes (original B2AC5h, working B2C70h). This is a hardware-representable
word and an arithmetic witness, **not** proof that the absent 320 resources
reach this origin. It disproves extending the 640 arithmetic argument alone.
DL-clear examples follow the same predicate; e.g. D8100h/top135 yields y15,
and an appropriate full E0 h can yield a valid x. No conclusion is hidden by
choosing only a familiar low DOSBox paragraph.

## Regression and controls

The regression executes the immutable original S22:1607..166A/16DE for every
word 5400h..9640h at both extreme vertical origins and compares the word
intermediates and actual branch destination. It then varies every non-E0 CH,
E0 boundary words and F0 words across horizontal overflow and signed-segment
edges. The complete finite interval inversion covers all 501 origins and all
65536 vertical words; invalid y excludes **all 65536 h** without an exhaustive
Cartesian-product claim. PointInRect's actual original instructions corroborate
the signed comparisons and exclusive bottom edge. Native fixture cases prove
ordinary adapter FA(h2/v0), E0 FA(h0/v0) and F0(flags/v0) remain explicit zero.

Positive pointer controls select a valid yard cell and enter a minimap rectangle;
a bottom-edge control rejects. The 320 alias is a positive contrast against the
640-only proof. Zero is **not** a negative control that takes a different branch
in the proved domain: that would contradict the result. No synthetic event is
inserted into production and no actual pointer callback changes.

Fresh build/suite and step-lane results are recorded in
`build/workers/irq-normal/RESULT.md`. All runtime-suite outputs use a short
scratch directory because the original FileSelect has a 67-character domain.
