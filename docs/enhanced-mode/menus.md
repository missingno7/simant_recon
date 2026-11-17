# Native proximity menus and visible waits

Enhanced mode starts with `--windows` alone. `SIMANT_ENHANCED_CONTRACTS=0`
explicitly selects the faithful comparison host; `SIMANT_ENHANCED_WORKSPACE=0`
retains the earlier hosted-window presentation. The default change applies to
bare `--windows`, not a restricted `--windows=ID,...` selection.

Implementation and organisation are ours. Canonical source is unchanged.
The local [delivery receipt](../../build/workers/enhanced-menus/RESULT.md)
records build identity, final results, unmasked differences and limitations.

## Proximity transactions

`AntMenu`, `EditScentMenu`, `EditToolsMenu` and `MapToolsMenu` still call the
original `win_DoProxMenu`. A native wrapper marks that transaction; after its
original `win_Open`, selected-item setup and `ButtonHeldInit`, one shared
owner-drawn Win32 `TrackPopupMenuEx` presents the source objects. Visible,
selectable and selected flags come from those objects; the source
`lastProxObj` supplies the initial proximity check. A native choice enters the
original event queue as that original object, at its source rectangle centre.
Cancellation supplies the transaction's non-item outcome. The original loop
closes its window and computes the result. `AntMenu` retains its own command
tables, Shift Recruit 1000, Alt spider variant and call to `YellowCommand`.
There is no native implementation of those commands.
The originating native focus is restored after the source modal transaction
finishes, including a following compatibility Help dialog, so ordinary game keys
still work after menu selection or cancellation.

DOS and the inspected Win16 databases use **bitmap labels and type-1 hit
objects** for these menus, rather than textual menu items. The native strings
are explicit transcriptions of their shipped bitmaps, indexed by bitmap ID and
item position in `proximity_labels.inc`. They are not described as recovered
text fields. [The evidence recipe](../../evidence/enhanced-mode/menus.md)
reproduces the bitmaps and hashes for review. Ordinary game-menu-bar strings
continue to come directly from the separate source menu resource.

| Source owner | Presentation and transaction |
|---|---|
| 0600, World Scent (N07) | Six source choices, including OFF, and the source initial check; returns to `EditScentMenu`. |
| 0700, ant commands (P03/P05/P10) | Recruit 5/10, Release 1/2/All, Exchange, Help; original command and modifier mapping. |
| 0800, unnested queen (P04/P10) | Dig Hole, Start Brood, Help; original eligibility checks and birth transaction. |
| 2000, spider (P05/P07/P08/P10) | Chase, Hunt, Exchange, Help; Alt Hunt remains the source's alternate command. |
| 0A00 / 0B00, Quick/Full Game Tools | Experimental choice, or the original nonselectable Full Game explanation; Escape/outside cancellation. |
| 1D00, Magnify (P09) | The same native popup presents the actual source-printed caste, behavior and carrying values. A read-only font-output tap copies them. Native completion ends the original held inspection; its original return value and cleanup remain. |

The source proximity and Magnify clients are kept hidden while their native
popup owns presentation. Unknown/unavailable menu presentation falls back to
the visible compatibility client. The experimental cascading `DoExpMenu`
(0900, 0C00–1100) retains its source presentation and mouse/keyboard tracker;
it is not a second implementation of experiment-tool selection.

## Placement and actor lifetime

World gestures retain the screen point of their actual native mouse-down.
Each queued semantic intent carries its own point through source owner
preparation and queue flushing. Panel commands retain the current cursor;
ordinary source keyboard commands sample it when forwarded. A later native
focus, camera move or pointer move cannot replace the retained point.

Proximity menus appear eight pixels from that point. Native menu placement and
the shared prompt helper keep them inside the work area of the monitor holding
the point. New compatibility dialogs/inspectors are also placed there, rather
than using scaled DOS desktop coordinates. Exchange and Chase are source
targeting modes, not modal dialogs: a small nonactivating, click-through native
prompt shows the actual `EditMessage` text beside the retained point for that
source tool's lifetime. Queen placement and post-death colony selection use the
same prompt presentation and retain their original Yard wait/input validation.

DOS evidence is `object_attributes.c::win_DoProxMenu` forwarding click h/v to
`win_Open`; `lifecycle.c::win_Open` recalculates parameter anchors and applies
`WIN_FLAG_KEEP_ON_SCREEN`, restoring the original offsets on close. The inspected
Win16 `AntMenu` also forwards its mouse-event x/y. Its reconstructed code is
corroboration, not a DOS oracle. Native monitor/work-area placement is our
adaptation of that pointer anchoring and screen-bound rule.

During a nested source wait the publisher retains its last complete published
world scene, with current source prompt text copied separately. Paints use the
immutable native asset catalog. Temporary source life removal, discarded tile
banks and intermediate overlay redraws therefore do not erase the native player
or spider. This freezes presentation during the wait; it does not simulate
through it or insert entities into source state. Release of a world gesture is
delivered through the existing source mouse device even after a different
logical owner becomes front, including the final `ButtonHeldEnd` cleanup.

## Wait inventory and step C

Bare `--windows` hosts all 45 source window slots. Non-native clients remain
visible source raster clients and receive native pointer/keyboard input. Native
content has explicit exceptions for source overlays and synchronous waits.

| Reachable wait/menu/tracker | Current enhanced presentation and completion |
|---|---|
| Every `win_DoProxMenu` caller | Native popup above; original source loop and return. |
| `MagnifyMenu` / `ButtonHeldEnd` | Native values popup; native completion/release; original inspector cleanup and life return. |
| `DoExpMenu` and experiment submenus | Visible compatibility windows; original hover, Enter/Escape and release paths. |
| Map, YardArea, world tools/recruit, Behavior/Caste triangles, held History | Existing native clients and original live down/move/up trackers. |
| `PlaceQueenInYard` | Native Yard, source prompt, original pending Yard event and Shift-repeat loop. |
| `SpecialXfer` after Full Game death | Native Yard and prompt; its source message identifies the active wait, including rejection messages; source event-poll seam delivers Yard clicks without requiring the suspended outer executor. |
| `DoWinHelp` for Game/Map/Yard/Behavior/Caste/History | Temporarily shows that window's existing source help client and routes source input. The argument is an object ID; its high byte identifies the owner. Native content cannot cover the help labels. |
| Info definition held popup | Existing native TEXT popup, source held transaction and release. |
| Status / `ScoreDialog` | Existing native Status and the source Continue object; no invented Escape result. |
| Caste population, Mystery, advice/string/choice boxes | Visible compatibility clients; existing source click/Escape/held completion. |
| About, scenario/new game, save/load/file selection, quit/discard, tutorial and general dialogs | Step C retains existing compatibility/native file presentation and original input. Newly shown source clients use the shared point/monitor placement. |
| Yellow/spider/ant-lion birth, death, eating/help animation dialogs | Visible compatibility clients, original key/click or timed/audio completion; native world scene retained. |
| Source sound delays, `myDelay`, `DialogWait*` and held-release loops | Existing source timing/input services continue; no invented timeout or task-result token. |
| Source window move/resize trackers | Ordinary native window move/size UI; faithful-host/source trackers remain available in comparison mode. |

The static [census recipe](../../evidence/enhanced-mode/menu_resources.py) lists
source functions containing loops, including noninteractive loops. The table
classifies normal UI reachability; it does not claim exhaustive dynamic branch
coverage of Full Game death, mating, every Shift-repeat or malformed resources.
Step C still owns replacing dialogs/files/help with native content. Its present
boundary is visible and usable compatibility presentation, not invisible waits.

## Paint and camera review

The supervisor's off-screen painting is retained for content, panels, worlds,
popups and owner-drawn buttons, including the per-frame content path. Standard
controls use change-only setters; the 50 ms refresh invalidates only the client
and owner-drawn children. A popup-buffer copy now includes its full original
rectangle after text insets. The camera keeps the source viewport's centre in
the native view and glides toward the target. Source plane changes retain their
intentional immediate relocation.

## Registrations

Enhanced runners automatically install the private-desktop policy. The explicit
launcher below also covers every nested process, including faithful port and
acceptance runners. The corrected launcher relaunches Python with
`CreateProcessW` and `lpDesktop` in a kill-on-close job; inner runners verify
their current desktop name. Setting `Popen`'s `STARTUPINFO.lpDesktop` alone is
ineffective in CPython. The job monitor rejects input-desktop windows with exit
97; the inner audit also uses PID **and creation time** and joins descendants.
It never switches desktops. Capture uses process-owned `PrintWindow` /
`WM_PRINTCLIENT` readbacks. There is no visible-desktop fallback or desktop-wide
screenshot. Creation/audit failure stops the registration; an incompatible
graphics test must be reported and skipped.

```powershell
python portable/tests/hidden_desktop.py portable/tests/enhanced/run.py --build BUILD --out FRESH
python portable/tests/hidden_desktop.py portable/tests/enhanced/content.py --build BUILD --out FRESH
python portable/tests/hidden_desktop.py portable/tests/enhanced/workspace.py --build BUILD --out FRESH
python portable/tests/hidden_desktop.py portable/tests/enhanced/action_equivalence.py --build BUILD --out FRESH
python portable/tests/hidden_desktop.py portable/tests/enhanced/invariance.py --build BUILD --out FRESH
python portable/tests/hidden_desktop.py portable/tests/acceptance/run.py --build BUILD --out FRESH --jobs 1 --scratch-root SCRATCH
```

`action_equivalence.py` retains its existing raw schema, exclusions, gameplay
verdict policy and detector negatives. Its full registration additionally runs
`menus.py`: every ant/queen/spider/scent item, both modifier variants, Tools,
Magnify and cancellation, comparing original current-source menu choices with
real Win32 popup input. The earlier endpoint fixtures explicitly retain
`SIMANT_ENHANCED_PROXIMITY=0`; the added menu registration exercises production
native menus. `--events` remains a focused endpoint run and omits the full menu
registration. Direct menu registration:

```powershell
python portable/tests/hidden_desktop.py portable/tests/enhanced/menus.py --build BUILD --out FRESH
```

New content cases are `steady-controls`, `camera-follow`, `exchange-prompt`,
`world-help` and `placement-edges`. They check actual child paint/erase counts,
centred camera convergence with a partial first step, keyboard prompt location
and nonempty source text, visible/dismissible source help, and four work-area
corner clamps. Menu probes also check item enabled/check state, clicked-point
placement, unchanged actor scene during the wait and continued outer iterations.
Cancellation additionally requires no source command and no change in any of the
307 SaveRec records in either lane; it does not mask raw UI/input differences.
An additional Exchange menu case cancels the source target mode by forwarding X
through the actually restored native focus.
Startup, icon masking and allocation first-show/editor regressions are in the
[owner follow-up](presentation-followup.md).
Comparisons are current canonical native source paths, not a new original DOS
executable action matrix. Strict passive differences remain differences.
