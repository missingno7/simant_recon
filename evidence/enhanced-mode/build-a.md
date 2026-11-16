# Ordinary native windows: build A evidence and reproduction

The implementation is host code in portable/whole_program/; canonical sources,
headers, layouts and top-level test registrations are unchanged. The approved
simple model supersedes the old phase 2 split/tab workspace. Current contracts
and owner registrations are in [phase2.md](../../docs/enhanced-mode/phase2.md).

Picture controls use the verified HCEGANT/SHARED immutable asset catalog.
enhanced/picture_controls.inc contains rectangle metadata, not pixels. Crops
come from original DOS Obj rectangles relative to their picture objects:

| Window | Picture object / asset | Controls |
|---|---|---|
| 0000 | Obj 3 / 15000 | 0005..0010 |
| 0100 | Obj 4 / 14000 | 0105..0118 |
| 1900 | Obj 4 / 7010 | 1907..1911, excluding value-only fields |

The active yard row is 7010; 7011 is its textual explanation strip. The normal
tool icon is picture 5107, independently named by the source draw hooks.
The DOS Info slot has no picture; its native button uses the text name Info.
No Win16 glyph bytes, asset-derived image or game file is added to Git.
The [resource census recipe](inspect_sources.py) regenerates resource-derived
output under ignored scratch with local original resources.

The action registry validates a catalog/event whitelist before enqueueing.
Alternate map/world/menu codes remain distinct. P11 maps a native threshold
selection to a source meter coordinate after preparation; source computes the
accepted quantized threshold. N03 calls the existing complete scroll operation
at an outer seam and retains source clamping/XOR stepping. Paint, movement,
attachment, persistence and zoom call no game or source-clock routine. B/C
clients retain current presentation and compatibility transactions in owned
native frames. The world renderer reads phase 1 snapshots/assets independently
of source sprite-bank residency.

Verification commands, with a fresh successful build and fresh output paths:

    python portable/tests/enhanced/run.py --build BUILD --out NEW_REGRESSIONS
    python portable/tests/enhanced/workspace.py --build BUILD --out NEW_WINDOWS --screens NEW_SCREENS
    python portable/tests/enhanced/action_equivalence.py --build BUILD --out NEW_ACTIONS
    python portable/tests/enhanced/invariance.py --build BUILD --out NEW_PASSIVE
    python portable/tests/acceptance/run.py --build BUILD --out NEW_ACCEPTANCE --jobs 1 --scratch-root SHORT_SCRATCH

The regression runner requires both rebirth and first activation PASS.
The workspace suite checks native capability flags, movement/attachment/zoom,
snapshot preservation, serialization rejection/roundtrips, process restart and
a first inactive Caste Manual click in each layout. The nine phone images use
actual native readbacks and retained SDL texture pixels at their real client
bounds, without mock-up substitution. They do not certify full-desktop/GPU
equality or physical mixed-DPI.

The action suite compares all existing acceptance views, including every SaveRec
slice, around original current-source event delivery, actual native controls,
keyboard activation and corresponding game menu routes. Its baseline includes
documented deterministic source-owner preparation. It is not execution of the
DOS oracle. Every raw difference and unavailable precondition remains in the
receipt; source input bookkeeping is not masked because alternate original
codes differ. Positive mating/queen-placement coverage requires an eligible game.
The passive suite retains strict raw comparisons and repeat-off controls,
rather than substituting a new passing projection.

The [task receipt](../../build/workers/enhanced-build-a/RESULT.md) links exact
commands, exit codes, build identities, all differences and captures. Passing
bounded checks does not settle unavailable held/task adapters, physical
input/DPI/accessibility, raw allocator/animation tails or complete
original/canonical/native equivalence.

Final PNG inspection records missing world/editor clients in the docked readback
and a real tooltip at the frame corner. Their causes are unresolved; the native
window/model assertions did not detect them. The captions and task receipt retain
these defects, and build A remains partial.
