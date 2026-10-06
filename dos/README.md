# Independent DOS linking and execution

`python dos/build.py --jobs 4 --link` is the canonical path. It accepts only
`src/program.json`, refuses unresolved storage, semantic gates or initialized
data, and refuses linker warnings. A diagnostic result cannot satisfy this gate.

`dos/diagnostic.py` compiles the same canonical sources and runs the same real
RTLink routine. Additional inputs are explicit provisional **storage-only** C
providers under ignored `build/workers/` or `build/scratch/`. Their object publics
must cover exactly the current undefined imports; code, imports, fixups, duplicate
owners, extra definitions and canonical-source replacements are rejected. Original
game executables and assets cannot enter either compilation/link path.

Provider manifests use this shape (every provider needs its own assumption):

```json
{
  "schema": "simant-diagnostic-providers-v1",
  "providers": [{
    "source": "build/workers/worker/task/storage.c",
    "source_sha256": "<SHA256 of this explicit C source>",
    "symbols": ["_unresolved_storage"],
    "assumption": "Describe provisional capacity, type, initialization and ownership."
  }]
}
```

```powershell
python dos/diagnostic.py --providers build/workers/worker/task/providers.json --out build/workers/worker/link-trial --cache build/current/dos --jobs 4
python dos/run.py --build-report build/workers/worker/link-trial/build-report.json --out build/workers/worker/runtime-trial --seconds 15
python dos/run.py --original --out build/workers/worker/original-trial --seconds 15
```

Outputs must be fresh. `--cache` reuses a canonical compilation only through the
existing source/context/object hash checks. Reports retain every unresolved
execution contract and initialized-data range, source/object identities and
assumptions. They carry `target: DIAGNOSTIC_DOS` and `closure_eligible: false`.
No provider can be promoted automatically or consumed by the canonical CLI.
An explicit empty provider list is allowed when every storage import has a
canonical owner; remaining diagnostic gates still stay visible and block closure.

The shared linker recipe uses the documented `NOEXTDICTIONARY` command. RTLink
4.00's extended dependency dictionary pulls LLIBCR's `fmalloc.asm` despite the
canonical allocator overrides and reports duplicate `__ffree`. Searching the
ordinary public dictionary resolves the canonical self-external call correctly
and omits six unnecessary CRT members. A natural C compiler/linker regression
retains that self-external and reproduces the duplicate with `EXTDICTIONARY`.
Objects, libraries and images are never patched; every linker warning remains
fatal, with no acknowledgment option. The compact proof is
`evidence/canonical/diagnostic-link/runtime-dictionary.json`.
Unreferenced aliases are omitted from linker DEFINE commands to avoid spurious
DEFINE warnings; their inventory and audit remain intact.

perturbation experiment. Use independent provider files to make the contrast
meaningful; inspect actual map addresses before claiming any placement changed.
It inserts no padding and changes no canonical algorithm or object.

`dos/run.py` requires either a successful diagnostic build receipt with a matching
MZ hash or explicit `--original`. These executions use separate fresh directories
and the pinned DOSBox-X. Only listed, hash-pinned resources are staged. `INSTALL.EXE`
is an inert runtime fixture because `main` opens it five times to check DOS file
handle availability; the runner never executes it. It captures a guest start
marker, text output, real DOS `IF ERRORLEVEL` exit code and a bounded execution
receipt. `--argument /dV` and `--argument /sN` pass individual DOS command tokens.
`--visible` enables a visible runtime; `--prepare-only` prepares the isolated
config/batch and prints the command without executing it.
`--trace-runtime` enables the pinned DOSBox-X's documented `[log]` video, INT10,
executable and file I/O categories. It records the log identity and relevant
video lines without instrumenting guest code. Compare the complete original and
diagnostic logs before interpreting the lines as gameplay milestones.

A timeout means only that DOSBox-X was still executing at the bound. It does not
prove boot, VGA mode, successful interaction, simulation, sound, save/load or
behavioral equality. Those require separately recorded observations. Neither
original nor diagnostic execution can publish canonical closure.

`--key` schedules a guest key through the pinned DOSBox-X `AUTOTYPE` command;
repeat it for a sequence. `--key-delay` defaults to five seconds and `--key-pace`
to two; `--key ,` inserts an extra pace delay. Recipes accept only listed guest
keys, never shell commands or host mapper actions. A scheduled event is not
automatically a verified game action. Timing is not a synchronization barrier.
`--saved-game build/workers/<worker>/<task>/A.ANT` copies an explicit saved game
unchanged into the fresh guest drive and pins its identity in the receipt. Only
DOS 8.3 `.ANT` names from worker/scratch space are accepted. This is runtime user
data; the game must still select and load it through its ordinary file dialog.
`--capture-video` invokes `DX-CAPTURE /V /-A /-M`, records AVI identities and
keeps audio output unverified. A timeout can leave an unfinalized but decodable
AVI. Compare corresponding screen states, not just equal host timestamps.
The commands are documented by [DOSBox-X](https://dosbox-x.com/wiki/DOSBox%E2%80%90X%E2%80%99s-Supported-Commands)
and were checked against the pinned executable's help.

This recipe dismisses the intro/registration, centers the cursor using the
game's keypad handler and activates Full Game through its space-key button path:

```powershell
python dos/run.py --original --out build/workers/worker/original-game --seconds 40 --trace-runtime --capture-video --key enter --key enter --key enter --key , --key , --key kp_5 --key space
```

Use `--build-report <diagnostic receipt>` instead of `--original` for the source
comparison. Receipts carry the canonical supported execution domain and resolved
domain contracts; launch arguments are checked against that scope. Successful
resource operations and valid state remain explicit premises. Unhandled CPU
interrupts and segment-limit messages in a runtime trace produce
`GUEST_FAULT_OBSERVED` and a nonzero runner exit even when earlier VGA entry was
valid. The exact game abort banner in `GAME.LOG` also marks failure, including
when the guest returns DOS exit code zero or runtime tracing is disabled.

## Reviewed diagnostic experiment

The current receipt is `evidence/canonical/diagnostic-link/receipt.json`.
It covers 193 unchanged canonical objects and seven provisional providers.
Both active provider sets reserve 6,276 spider bytes, meeting a measured access
lower bound; complete capacity, ownership and lifetime remain unproved.

Reproduce using fresh output paths (retire existing outputs with
`tools/workspace.py` before reusing these paths):

```powershell
python dos/diagnostic.py --providers build/workers/diagnostic_link/providers/split-seven.json --out build/workers/lead/overlay-policy/baseline --cache build/current/dos --jobs 4
python dos/diagnostic.py --providers build/workers/diagnostic_link/providers/initialized-seven.json --out build/workers/lead/overlay-policy/initialized --cache build/current/dos --jobs 4
python dos/run.py --build-report build/workers/lead/overlay-policy/baseline/build-report.json --out build/workers/lead/overlay-policy/runtime-baseline --seconds 40 --trace-runtime --capture-video --key enter --key enter --key enter --key , --key , --key kp_5 --key space
python dos/run.py --build-report build/workers/lead/overlay-policy/initialized/build-report.json --out build/workers/lead/overlay-policy/runtime-initialized --seconds 40 --trace-runtime --capture-video --key enter --key enter --key enter --key , --key , --key kp_5 --key space
python dos/run.py --original --out build/workers/lead/dos-input/original-fullgame --seconds 40 --trace-runtime --capture-video --key enter --key enter --key enter --key , --key , --key kp_5 --key space
```

The current links apply the canonical symbolic overlay-vector policy. All seven
provisional publics move in the initialized-storage contrast. Both links must
contain exactly the 136 required function vectors plus 16 vectors for referenced
naming aliases. The latter preserve calls through both source spellings; exact
historical vector count/order is not claimed. Display dispatch pointers remain
direct, preserving the original interrupt contract. The postlink map check
rejects missing or unexpected vectors.

The earlier 4,100-byte COMDEF run emits INT6 after 173 resource reads. Its image,
map and failing log remain under `seven/baseline` and
`build/workers/lead/dos-input/source-menu-owner`; `fault/undersized-providers.json`
preserves the old assumption for reproduction. A source-built resident INT6
observer validates against deliberate invalid-opcode and safe-exit controls,
but its 70-paragraph allocation perturbation avoids the fault in the unchanged
game image. It supplies no baseline CS:IP or causal explanation. Growth to
6,276 bytes also changes placement, so neither contrast proves the cause.

An unchanged-image replay with host autosave captured a more specific failure:
all 119 S06 relocation words have twice the load-base adjustment; all other
9,346 bytes match disk. A correct snapshot of the same image has a single
adjustment. The provisional spider region is entirely zero in the failed state.
See `evidence/canonical/diagnostic-link/overlay-relocation.json` for pinned
snapshots, configuration and a known-register decoder control. The observer
uses the pinned 2022.09.0 runner's autosave settings without guest allocation;
it can still affect timing. The captured display pointers entered loader vectors,
allowing timer cursor callbacks to reload the interrupted S06 before its outer
relocation pass completed. This concrete static path explains the observed shape;
no instruction trace pins the interrupt instant. Explicit vector selection fixes
that binding defect without modifying game algorithms or runtime binaries. See
`evidence/canonical/diagnostic-link/overlay-vectors.json` for the real-link controls.

No passing screen, timeout or provisional placement admits an owner or proves
sound, sustained play or complete simulation-state equality. The
canonical gate remains closed until the source contracts are established.

`evidence/canonical/diagnostic-link/save-load.json` records the later bounded
Save/Load checks: both executables save all 307 records (48,386 bytes), and both
load the same original save back into paused Full Game with matching visible
terrain. Exact keyboard recipes, file identities, I/O sequences and reviewed
frames are pinned there. The original and source required 27 and 26 up taps
respectively to select the file row; timer-driven cursor movement makes these
wall-timed recipes observations rather than deterministic automation.
Repeated-selection failures in both executables remain explicit in `load-lock.json`.

Fresh games use two tick-seeded RNG streams. RandYard stores 192 per-yard seeds;
RandWorld resets the private generator from the selected yard seed. Equal input
timestamps do not establish equal tick samples or prior RNG call histories.
SaveRec preserves yard seeds and world data but omits both live RNG states, so
loading the same save does not guarantee identical subsequent random outcomes.
The bounded original-instruction controls and existing RNG regression scope are
recorded in `evidence/canonical/diagnostic-link/rng-domain.json`.

## Deterministic acceptance

AUTOTYPE schedules keys on a host thread, so the recipes above are wall-timed.
`dos/run.py --input-script` instead uses the pinned `dosbox-x-acceptance`
runner (`layout/toolchain.json`): DOSBox-X 2026.08.31 rebuilt from the release
source with a provenance-recorded patch that schedules keys, mouse motion,
buttons, memory dumps and `exit` in emulated milliseconds. With fixed cycles
and `--fixed-clock` (guest `DATE`/`TIME` set before launch) the game's tick
counter, RNG seeds and input arrival are reproducible: repeated original runs
produce byte-identical saves.

```powershell
python dos/acceptance.py dos/scenarios/new-game-save.json --build-report <receipt> --out build/workers/<w>/<task>
```

runs a scenario for the original and a reconstructed executable and requires
byte-identical saves; differing SaveRec records are named in
`acceptance.json`. A pass is a bounded observation of that scenario only.
