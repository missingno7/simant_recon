# Enhanced build B: native content

Build B keeps the approved ordinary-window model and replaces the game-content
interiors on Windows. The subsequent [menu repair](menus.md) makes bare
`--windows` enable enhanced mode, adds native proximity menus and makes source
waits visible. `SIMANT_ENHANCED_CONTRACTS=0` explicitly selects the faithful host;
`SIMANT_ENHANCED_WORKSPACE=0` retains the phase 1 comparison host. The build B
receipts below describe their identified historical builds.
The implementation and organisation are ours, not recovered historical code.
The later [owner follow-up](presentation-followup.md) replaces the percentage
lists described in this historical receipt with editable numeric fields,
corrects first-show state, gates startup visibility and preserves icon masks.

The [task receipt](../../build/workers/enhanced-build-b/RESULT.md) records the
delivered build identity, final verification, limitations and owner screenshots.
Ignored captures require local verified game assets. The tracked evidence is
[the reproduction guide](../../evidence/enhanced-mode/build-b.md).

## Windows and paints

All content below is painted with GDI from const semantic publications and the
independently owned immutable asset catalog. No client takes pixels from hosted
VGA planes. Original drawing still runs hidden, including effectful redraws,
animation/cache work, random choices, resource lifetimes and formatted score
output. A native repaint neither invokes those operations nor advances source
time. Fixed clients retain their natural DIP sizes when attached.

| Window | Native content and original input |
|---|---|
| Map, 512 x 256 | CTab/HTab/LTab/CTabR terrain/life/scent cells, spider picture and host-visible view rectangle; original 0102 map transaction for click/drag. The source background toggle uses its cached logical colour cells, not a raster plane. |
| Yard/House/Strategic/Graphic, 512 x 226 | Phase 1 immutable scene and source-selected animation poses. Original 1902 YardArea transactions. Queen placement retains its separate original source wait. |
| Behavior/Caste, 210 x 170 | Triangle, source knob/levels, labelled percentage choices, Auto/Manual, conditional Set 1-3, units/help and three bar indicators. Original 120D/130D trackers and original discrete controls. |
| History, 320 x 179 | Chronological source ring samples, original ten series buttons and original held value-display transaction. Private source selection slots and colours are copied; graph scales/layout are native presentation choices. |
| Info, 320 x 200 | Shipped CARD pictures, native MacRoman TEXT, resource title, source links, Previous and Top Card. Host-only scrolling keeps full text reachable. Definition links retain the source held popup wait with native text. |
| Status, 318 x 186 | Original eight observed percentages, Quick Game N.A. fields, OverallScore and Continue. No invented close/cancel. Continue clicks the original source task control. |

Private card links, graph selection/colours and Map freeze state are read by
small observers appended to the port's converted original TUs. They access
file-static data without changing an original statement, calling drawing or
loading/locking source resources. The build report records observer paths and
hashes. Score values are tapped after the real source font_PrintStr for the
eight specific score fields; the source still computes and formats each value.
CARD/TEXT/STYL/title records are independently decompressed with the existing
native database reader, owned and freed alongside the phase 1 art.

## Source transactions

Win32 callbacks retain semantic requests. The outer source seam prepares the
original owner, finishes its queue flush and inserts one original object event.
Pointer coordinates are evaluated after that preparation: world pixels, Map
cells or original hit-object offsets. The native input provider updates the
existing source device with callback mask zero, so it does not generate a
second hit command. The canonical event dispatcher, feedback, click history,
GetMousePos, StillDown, myButton and release tails remain in charge.

Left input in the primary Game view performs original world actions, including
held tools, brushes, recruit and double-clicks. Middle-drag performs the existing
N03 navigation transaction; extra-view middle pan and all zoom are host state.
Original gameplay keyboard input is forwarded from the primary view after the
approved shell accelerators. A context menu takes device/capture ownership until
its real mouse-up; no synthetic neutral-position reset follows an action.

Each triangle uses its own original dimensions, sharing the source's temporary
geometry variables only while that editor is active. At completed editor draws,
the engine enumerates the source integer triangle with IsPointInIsoTri,
BoundPointToTri and GetTriLatDist into local output words. The UI offers exactly
the percentages reachable on that grid, including its gaps. A value choice
selects the nearest original pixel with that displayed percentage and delivers
the original triangle event. It does not write levels, presets or IdealCaste.
The original tracker and release tail do all of those updates.

PlaceQueenInYard has a synchronous event wait rather than YardArea's ordinary
dispatch. A wrapper marks that original call while it runs. Only a Yard viewport
click can enter that wait, from its existing event-poll seam. The original
eligibility, isometric conversion, patch updates and Shift-repeat loop remain.
The adapter never calls YardArea recursively or fabricates a placement result.

Shared native menus use the same original control transaction as their relocated
button/keyboard counterpart: world planes 0008-0A, Pause 000F, editor/status/info
010F/0111/0113/0114/0115, Strategic/Graphic 1909/190A. Yard/House FD21/FD22 keep
their distinct original transition. Map-plane controls remain 0106-0108, with
their original scent clearing. Tool/context/help meanings are not merged.

## Step A repairs

Attached windows retain their contents and native child controls. Capture and
display both use the native content paint, clipping around real child controls.
SDL content HWNDs receive real fixed frames before custom caption styling;
captionless compatibility flags no longer remove Info/Status titles. Captions
share soil/cream active and beige/ink inactive states, with capabilities from
the approved table. Main alone has minimize; worlds alone resize/maximize;
Status and the two panels have no invented close button.

One tracking tooltip is positioned beside the hovered control. Picture buttons
have consistent sizes/groups; the original blank Info/Mystery art slots use
consistent native information/question symbols. The distinct Help actions are
World 0006, Map 0116 and Yard 1911, invoking their different original help
contexts. They are labelled in the tooltips. There is no extra generic Help
button. Experimental tools show the current original tool picture.

## Verification and remaining boundary

Owner registrations, all with fresh output directories:

```powershell
python portable/tests/enhanced/run.py --build BUILD --out FRESH_REGRESSIONS
python portable/tests/enhanced/workspace.py --build BUILD --out FRESH_SHELL --screens FRESH_SHELL_SCREENS
python portable/tests/enhanced/action_equivalence.py --build BUILD --out FRESH_ACTIONS
python portable/tests/enhanced/content.py --build BUILD --out FRESH_CONTENT --screens FRESH_CONTENT_SCREENS
python portable/tests/enhanced/invariance.py --build BUILD --out FRESH_PASSIVE
python portable/tests/acceptance/run.py
```

The action registration retains all 1,024 existing raw views, including 307
SaveRec records. It compares original current-source event delivery with real
native buttons, menu commands and keyboard activation where an equivalent
control exists, including the new editor/History controls and six Options menu
toggles, Info link/Previous/Top Card, held History and Status Continue (101 rows total).
Additional live pointer rows cover Map, both triangles, world
single/double/zoomed input, YardArea, all six experimental held tools, alternate
fill, recruit and eligible queen placement. A coalesced held-scent negative
control must alter SaveRec; the existing offline detector mutation also remains.
This is a bounded current-source action comparison, not a DOS executable run.

The content registration captures actual native windows, checks source camera,
allocation and card changes, captures a triangle while its source tracker is
still active, checks all six offered percentage domains against the original
conversion routines, verifies a percentage choice followed immediately by a
Map click retains both queued transactions, and verifies Status Continue closes its source task.
History is also captured while its original value-display wait is held. Info
reflow uses native text hit boxes; only unchanged picture hotspots can fall back
to original geometry, so old text rectangles cannot activate unrelated words.
Capture invariance there compares the published snapshot; the independent
passive registration compares full raw source state, clock and sound commands.
Any raw difference remains a difference and is itemised in the task receipt.

The recorded full round passes twenty port suites, 58 acceptance lanes, enhanced
regressions and content/window checks. Its action result is 100/101: the remaining
keyboard lane timed out during startup before observation; an isolated recheck
passes. All wired endpoints have a passing comparison. Later presentation fixes
have separately identified builds and targeted checks, not a substituted full
round. The delivery build passes 18 content cases and ten window scenes.

Strict passive invariance remains **DIFFERENCE** in all nine comparisons, including
repeat-off controls, at all 128 entries. The differing fields are the clip
rectangle workspace, raw window order, fd_50F6_37FA and, in some lanes, the mode
knob animation index. The 943 registered gameplay-verdict views (including all
307 SaveRec records), clock and audio commands agree. These narrower agreements
do not establish raw equality. No exclusion was added; the receipt retains all
704 existing omissions, exact field/entry counts and build identities.

Step C still owns File/About/new/load/save/quit and general help/dialogs.
The [menu repair](menus.md) supersedes the context/proximity presentation gap;
remaining step C clients retain visible compatibility presentation and input.
Buffered sample transcripts and arbitrary task-result tokens remain rejected.
The Quick Game action matrix does not establish every Full Game mating,
multi-queen Shift-repeat, malformed-resource, real-time input or hardware branch.
Physical mixed-DPI, monitor hot-plug and screen-reader certification remain open.
Neither screenshot readback nor a passing bounded suite is whole-game identity.

The later [MAP/modal follow-up](minimap-followup.md) supersedes the transient
minimap compatibility client and adds the live control/menu sweep. Its own
RESULT.md identifies the final frozen build and exact verification outcomes;
the historical round above is retained as historical evidence.
