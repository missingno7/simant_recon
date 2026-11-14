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

The source save for load-from-save is the original executable's retained
quick-game A.ANT, now stored independently at `build/reference/setup/A.ANT` so
retiring a recording does not retire the recipe's immutable input. Its recipe pins the SHA-256. Both DOS runs and
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

The recording environment now pins US in `keyboard-environment.conf`, applied
by `dos/run.py` to its selected toolchain runner. Each new manifest records the
effective DOS layout from a `KEYB` query and the environment pin. The first
captures used host-selected CZ/cz243 (`key 1` became `+`, Ctrl+Y was swapped).
Both lanes of interactive-play, load-from-save, full-game and random-17 were
re-recorded because their physical digits and/or Y differ. V5 re-records all eighteen captures under pinned US and admits synthetic
transitions at completed service boundaries; every v4 capture is retired.
The earlier ten CZ captures had per-key neutrality proofs; those historical
proofs do not relabel their effective layout.
See `portable/tests/acceptance/README.md` and `build/workers/keys/RESULT.md`.

The earlier action QA above describes the retired CZ captures. The mouse Ant
Menu supplies separate recruitment coverage. Ultra was selected through the
Speed menu (GameSpeed=3 then 1). Yard is independently checked by its map toolbar
button in ant-commands and full-game; those QA frames show "Yard View".

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
