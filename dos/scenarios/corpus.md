# Interactive corpus (2026-11-14)

Recipes are input schedules in emulated milliseconds, not state injections.
The observer stops at the recipe's requested DoAntSim entry; the 610 s script
exit is a safety bound. References use each executable's own clocks and IRQs.
Original resources, saves, video and references remain ignored.

| Recipe | Entries | Additional coverage |
| --- | ---: | --- |
| interactive-play | 2000 | Walk, tunnel digging, food pickup/drop, physical number keys, map, minimap (including a key inside its modal loop), Yard shortcut attempt, Info link/back, title drag, resize, View/Options menus, Slow/Normal/Fast/Ultra/Normal |
| ant-commands | 1000 | Pause; Ant Menu Recruit 5, Recruit 10, Release 1/2 and Release All; follow a black queen; unpause; open Yard through the map's Yard button |
| load-from-save | 1000 | File > Open, discard prompt, original quick-game A.ANT, explicit unpause, walk/dig, physical number keys, map/edit |
| full-game | 1000 | Explicit Full Game icon, queen entering and digging the nest, founding-key attempts, Info and Yard |
| experiment | 1000 | Explicit Experimental icon, Add Food and Barriers tools, painting by click/drag, map and edit |
| random-17 | 2000 | Seeded mouse moves, single/double/right clicks, keys and window/view shortcuts |

The source save for load-from-save is the original executable's existing
quick-game reference A.ANT. Its recipe pins the SHA-256. Both DOS runs and
native receive disposable copies of that same file. The source is never saved
over. Loading pauses the game; the script clicks Pause to resume.

Canonical DOS video/screens and raw state checks are indexed in
`build/workers/corpus/RESULT.md`. Food pickup is established by MeType 16 -> 24,
and drop by 24 -> 16. The Ant Menu selections are visible in the video; at the
paused early-game start there are few eligible workers, so selecting Recruit
does not promise a larger squad. Following is independently established by
MeCmd=4, MeTargLife=102 and goal (36,10). Full Game's founding key is an attempt:
the QA run still has MeNestStarted=0. Window dragging snaps: the requested
(40,20) title drag produces (32,16); resize changes the viewport from
(64,41,416,362) to (96,57,528,394).

The pinned DOSBox configuration auto-selects the host DOS keyboard layout.
These captures log CZ/cz243: physical `key 1` produces `+` (0x2B), whereas the
native replay's US key translation produces `1` (0x31) and calls Recruit(5).
The physical number-key actions in interactive-play/load-from-save therefore
test this difference; they are **not** claims of successful DOS recruitment.
The mouse Ant Menu scenario supplies separate command coverage. Ultra is
selected through the Speed menu, with raw QA values GameSpeed=3 then 1;
it does not rely on shifted number shortcuts.
Physical Ctrl+Y is also layout-sensitive. Yard is independently checked by its
map toolbar button in ant-commands and full-game, rather than relying on that
shortcut. Their QA frames show the house and yard with the title "Yard View".

## Seeded input

Regenerate without touching the JSON recipe:

```powershell
python dos/scenarios/generate_random.py --seed 17 --out dos/scenarios/random-17.scr
```

The generator starts from `seed & 0xffffffff`, advances
`state = (1664525 * state + 1013904223) & 0xffffffff`, and chooses `state % n`.
Its algorithm is explicit and independent of Python's random library. Each
two-second action slot has one of seven operations; coordinates stay within
x=90..399, y=100..319. An Enter follows each action, and dismissal continues
after the random portion. It never requests File, Quit, DOS exit, or the pause
shortcut; the final scheduled emulator exit only bounds the run. It can enter
ordinary modal windows. It is broad input coverage, not a guarantee that every
random click activates a tool or that every subsequent native entry is reached.

New native lanes intentionally expose differences. Consult their result.json
and the worker report: STATE_DIFFERENCE and service-order failures remain
failures; no runtime view was reclassified or comparison relaxed.
