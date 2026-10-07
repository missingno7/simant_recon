These checks run the current canonical SDL3 executable from a successful,
unchanged build report. They copy its pinned resources into a fresh output
directory and send ordinary SDL keyboard and mouse events to the original main.

```powershell
python portable/tests/runtime/run.py --report build/current/portable/report.json --flow vga
python portable/tests/runtime/run.py --report build/current/portable/report.json --flow save
python portable/tests/runtime/run_load.py --report build/current/portable/report.json
python portable/tests/runtime/run_logo.py --report build/current/portable/report.json --repeat 2
python portable/tests/runtime/run_drag.py --report build/current/portable/report.json --repeat 2
python portable/tests/runtime/run_edge.py --report build/current/portable/report.json
```

The Save check dismisses the source success dialog with Return. The Save→Load
check selects the generated `a.ant` through the real Load dialog. It also needs
GDB with Python support; use `--gdb PATH` if GDB is elsewhere. Its trace reads
source arguments, return values and copied-file hashes without calling game
functions or writing game state. The retained fixture and trace are local to
this directory; no old test archive, generated body selection or snapshot is
imported.

Each output contains its report, logs and 640×480 frame. The Load check also
retains debugger commands and its event ledger. Every run requires complete
current input pins, unchanged original/build resources and all scripted events.
The Load check additionally requires successful source returns and 307 complete
SaveRec reads totaling 48,386 bytes. A short
fresh `--out` path may be required by the original FileSelect path domain.
For a deeply nested worktree, Save and Load accept `--output-root <checkout>`
with an explicit fresh `--out` under that checkout's `build/`. This changes
disposable output placement only; executable and input pins still use the
worktree supplied by `--project` (or the script's own project by default).

The logo regression requires GDB with Python support. It exercises clicks during
and after animation, center/corner positions, held right-click and Space, and
repeated clicks. Read-only startup traces require every `DialogWaitInit` to
return after release and both `ShowIntro` and `CustomerIDDialog` to return.
All replay events, a meaningful frame and the bounded smoke exit are required;
the cached scan-query implementation fails the `center-after` negative control.
Use `--case center-after`, `--repeat 2`, or `--visible` for focused reruns.

The BIOS font regression compiles the production text-bitmap projection and
compares the fixed ` File` output with the direct DOSBox-X return-state capture.
It cross-checks that capture against the pinned 8x14 ROM bank and requires the
prior DOSBox Staging table to fail as a negative control. Give every run a fresh
output directory:

```powershell
python portable/tests/runtime/bios_font_regression.py --out build/workers/p2-r4/font-regression
```

Passing confirms this bounded current UI/file path. It does not establish
after-load state equivalence, DOS save compatibility, resave equivalence, fixed
terrain-seed behavior or whole-game correctness. Current build limitations remain
listed in each report. The outer-loop counter is not a simulation-step counter.

The edge regression replays the exact seed-0 human freeze recording and Quick
Game holds at the map-window perimeter and all four screen edges. It requires
frames inside the active source scroll loop, returns after moving away,
resumed outer progress, every replay event and the smoke exit. Use
`--deterministic --out build/workers/NAME/edge-clock` for a separate virtual
clock control. Host observations are clamped to the visible screen before
recording; the source mouse driver then applies its tighter INT33 limits.

The drag regression observes the real title, resize and caste triangle handlers
under GDB. Each must return and present multiple distinct frames while the button
is held and the clip list remains active. Every presentation must occur outside
the raster/cursor busy guards and obey the 60 Hz interval. Captured SDL motion
above and beyond the native window must reach the source at its INT33 limits;
faults and nonzero exits retain symbolic stacks. The baseline at `c62915b`
presents zero frames in these tracking loops and exits 70 on the negative-Y
motion. Frame hashes include the cursor and do not assert DOS pixel equality.
