# Step-based scenario observations

The expanded interactive corpus and its action/keyboard-layout limits are in
[`dos/scenarios/corpus.md`](../../../dos/scenarios/corpus.md).
New findings are retained as failing lanes; the original three recipes remain
equal. Measurements and first-divergence evidence for this expansion are in
`build/workers/corpus/RESULT.md`.

`step_check.py` replays stored DOS references in a compiled native observer.
It starts neither DOSBox-X nor GDB. Each scenario has independent original and
canonical lanes; native consumes that executable's own clocks and actual IRQ
transitions and compares only with its state observations.

```powershell
python portable/tests/acceptance/step_check.py
```

The command prints one stable line per scenario. Missing references, assets or
builds report `no reference` and exit 0. A state difference or incomplete replay
exits 1. `--build`, `--out`, `--original`, `--canonical`, `--reference-root`,
`--steps` and `--timeout` select explicit builds, outputs, references and controls.
The default build is `build/current/portable` (built as in `portable/README.md`);
the default output is `build/current/tests/steps`. The upper-layer test runs this
command and fails when any scenario's outcome differs from `known_findings.json`
(open findings, pinned per lane; unlisted scenarios must be equal in both lanes).
A fix updates that file in the same commit.
Prior output is retired with `tools/workspace.py`. Checks never record.

## Record references

```powershell
python portable/build.py --out build/current/portable
python portable/tests/acceptance/build_observer.py --out build/current/observer
python portable/tests/acceptance/step_record.py --observer build/current/observer/observer-build.json
```

Recording defaults to every scenario and both executables. `--target original`
or `--target canonical` selects one. `--out SCRATCH` records an explicit repeat;
`--steps` and `--cycles` are measured recording controls, stored in its manifest.
Compatible references are reused. An older service contract requires explicit
retirement with `tools/workspace.py` and recording again. References live at
`build/reference/<scenario>/<executable-sha256>-service-samples-v5/`. Original assets and generated
references stay ignored.

Recipes with `saved_game` also require `saved_game_sha256`: recording validates
that immutable setup input, and native checks install a disposable copy before
launch. `--scratch-root build/workers/corpus` on record/check keeps binding
captures and short native asset paths in that worker. The recorder rejects an
observer built from a different `compact_observer.inc`; rebuild it or select
the current pinned observer. For video QA, `dos/run.py --capture-directory`
can place captures outside the guest drive so a CAPTURE directory does not
change File > Open's list rows.

The acceptance-only observer link translates DOS recipe modifier/Escape names
to SDL names and supplies SDL's held-modifier field from the recorded physical
transitions. The existing platform still constructs and projects each SDL
event. It does not supply expected game state. The platform uses physical SDL
scancodes and the US BIOS translation relation, including modifier precedence,
unsupported combinations and legacy INT16 filtering.

`dos/run.py` overlays the hash-pinned
[`keyboard-environment.conf`](../../../dos/scenarios/keyboard-environment.conf)
onto the selected toolchain runner entry (also when replaced by the observer).
It captures `KEYB`'s effective-layout query and refuses a non-US environment.
Every v5 reference records that result and environment pin; record and check
both require proved US. All eighteen references were re-recorded under US for
v5. Historical CZ243 captures and their neutrality proofs are retired, with
provenance in `build/workers/keys/RESULT.md` and the v4 retirement inventory in
`build/workers/quiet-inputs/v4-inventory.json`.

`key_bios_probe.py --layout us|cz243 --out build/workers/NAME` regenerates the
standalone BIOS experiment. `key_bios_us.json` and `key_bios_cz.json` retain 582
cases each with runner/probe/source provenance. No game is involved. Run
`python -m unittest portable.tests.acceptance.test_key_bios` for the compiled
production-key-path regression and its spurious-Ctrl+8 negative control.

Recipes request 64 entries for new-game-save, 2,000 for quick-game (including
A/B Save As inputs), and 3,000 for unattended long-run, at normal game speed.
The observer stops at the requested entry; script exits are safety bounds.
Each entry retains 1,024 FNV-1a fingerprints: 307 SaveRec records and 717 runtime
views. Full ordered state frames are retained at entry 1, every 256 entries and
the final entry. The fingerprint comparison has the usual hash-collision limit.
One first-megabyte frame binds relocated code and the BIOS INT16 callback.

Manifests pin executable, recipe, script, schema, observer, command and outputs,
including the chronological service stream. Canonical receipts also pin their
build report and objects. Original clock sites bind against immutable original
function bytes. Canonical sites bind independently against their own MAP and
OMF fixups, with CodeView extents or reachable object instructions. Native
addresses and extents come from PE DWARF. Required readers are `capstone`,
`pefile` and `pyelftools`. Unresolved bindings remain failures.

```powershell
python portable/tests/acceptance/step_repeat.py REFERENCE REPEAT --out build/current/tests/repeat-result.json
```

Only same-executable DOS repeats establish `ORIGINAL_DOS_NONDETERMINISTIC`.
A native difference under another executable's clocks does not establish
reconstruction damage.

## Admission and clock contract

There is one chronological sequence of observed services:

* Each TickCount return, countdown operand sample and input-enqueue BIOS stamp.
* The actual input_event_count MOV sample and window-pump entry.
* The BIOS INT16 queue sample: every peek and each successful blocking pop.
* Held-button, keyboard-scan and scroll-lock operand samples, and entry to
  edit_scroll_and_redraw, including its unclocked edge-scroll iterations.
* DoAntSim entry and return, separating input phases from state observations.

`observer.txt.order` stores one byte per service: clock IDs bind to the trace's
`O` definitions; IDs 246-249 are scroll-call/button/scan/scroll-lock samples,
250/251 are simulation entry/return, 252/253 BIOS peek/pop,
and 254/255 queue sample/window pump. Per-site RLE separately preserves every
clock value. No clock value is interpolated, inferred from native state or
selected to obtain equality.

V5 (`service-samples-v5`) holds each scripted key or mouse transition from
its scheduled emulated time until the next eligible recorded service boundary.
Atomic providers complete their sample first; that cached result cannot change.
Entry boundaries admit before their bodies. StillDown (247) is a completed
result at RETF / native function exit, after its nested scan samples.
DoAntSim's entry snapshot finishes before admitting transitions after that entry.
At an IF-disabled boundary the transition stays pending until a later eligible
boundary; IF is never forced.

The foreground then waits at that exact PC and stack depth while normal device
latency, PIC arbitration, BIOS INT 9, IRQ12 / PS/2 and guest handlers run. The
hold ends only after actual handler entry and return to that foreground PC and
stack. No software call substitutes for an IRQ. Due transitions are serialized
there in script order, including nested enqueue stamps. Hardware typematic
expiry is held too. Due script transitions run first; a due release cancels an
expired repeat through the real keyboard release path. A still-held repeat
uses KEYBOARD_AddKey and the same PIC / INT 9 path and is recorded explicitly.
The keyboard repeat scheduler is the only device timing hook; repeat rates,
BIOS handlers, scan generation and queue handling remain the real ones. `U raise` / `U return`
records prove the hold; `I` retains the scheduled time and `D` the actual handler
registers and completed-service coordinates. A missing handler fails recording.

Each actual key IRQ or pointer callback records completed clock, pump and query
counts plus simulation entry/phase. The single ordinal is
`clock_reads + pumps + queries + 2*step - phase`. Native admits through the normal
SDL adapter at precisely this boundary. The parser refuses a v5 IRQ whose
coordinates differ from its hold, and checks refuse v4 references. A missed
boundary, wrong service, phase or input coordinate fails replay. Positive
completion requires consumed clock, service and input tapes; a first state
difference leaves the remaining tape for investigation.

This tests synthetic player actions at service boundaries. It does **not** test
an input arriving mid-raster or between unsampled pointer comparisons and menu
mutations. Those outcomes depend on DOS CPU speed and interrupt placement, and
are outside the faithful port's behavioural contract: native has no matching
intra-raster interrupt position. No state view is excluded to obtain equality.
The explicit v4-style early/late IRQ control is retained by
`python portable/tests/mouse_services/run.py --build build/current/portable`;
its unchanged edge-scroll body still produces different outcomes within one
service interval. Evidence and all eighteen v5 lanes are recorded in
`build/workers/quiet-inputs/RESULT.md`.

The v5 tapes also retain AX/BX/CX/DX at scan-processor entry (or INT15/AH=4F
while the hook is disabled) and pointer-callback entry. Keyboard admission now
supplies captured CX/DX to the ordinary native scan projection through an
optional test hook. Each staged raw SDL event carries its own pair; the
projection still constructs and queues every Event, including its BIOS stamp.
Physical pointer coordinates retain their existing translation. Missing or
out-of-word keyboard context is a coverage error, never a native-zero fallback.
A v4 reference is refused; its timing cannot be upgraded from expected state.

These are handler-entry words, not necessarily raw interrupted foreground
registers: the DOS IRQ wrapper loads DX with DGROUP before kbd_process_scan.
Replaying an independently captured machine-service argument is input replay;
neither expected hashes nor reference game state select its value. Ordinary
execution keeps its explicit CX/DX=0. The
[consumer audit](../../../evidence/canonical/native-input-irq/interrupted-registers.md)
lists copies, guarded coordinate readers and two unfiltered modal readers.
It leaves normal-play observability across all modes/placements undecided;
there is no globally-unused-field claim or state-classification relaxation.

BIOS queries are observed at DOSBox's atomic CB_INT16 callback, filtered by the
source INT16 return PCs. Observing the later game-function RETF is incorrect:
a key can arrive after the BIOS sampled an empty queue but before RETF. Queue
count uses its MOV instruction for the same reason. The first-megabyte frame
binds the INT16 vector, STI/FE38/IRET callback stub and source INT16 instructions.
State observation never writes guest code, registers, clocks, input queues,
RNG state or saved records. The v5 recorder changes only synthetic-input timing
and pauses foreground instruction execution while the actual devices deliver.

Clock count alone does not locate inputs relative to non-clock input queries.
Pump/read fences and per-site position barriers are absent. In tape mode the
captured services replace host time and interrupt scheduling; the platform
admits through its ordinary adapter without advancing a second host timeline
or running an application idle/presentation callback inside a sampled read.
No tape option means ordinary platform refresh, audio and presentation.
`platform/sdl3/test_observer.inc` keeps the optional host hooks together.
GCC entry instrumentation on the two unchanged converted input-reader TUs
observes StillDown exit and edit_scroll_and_redraw entry, including calls within the same
TU that linker wrapping cannot intercept. Their source hashes and compiler
flag are retained in the observer build receipt; bodies and arguments remain
canonical. Only the separate observation/comparison object uses `-O2 -fno-lto`;
game compilation and link optimization flags remain unchanged. Other profiling callbacks do not advance the service stream.

Menus disable the game's scan hook. The observer records those actual scans
at BIOS INT15/AH=4F while disabled, and at kbd_process_scan while enabled.
Script submission time is retained separately and never substitutes for IRQ
delivery. Unpaired or unsupported scans are explicit coverage failures.
`input-admission.json` retains actual native service/site coordinates and phase.

## State verdicts and controls

Every SaveRec and every available view classified as game state in
`runtime_views.json` participates in the verdict. Unproven influence stays game
state. Presentation, audio and runtime views are separate diagnostics; address,
handle and callback views remain excluded. The live pending input-queue view is
an explicit coverage gap; its raw backing storage remains reported.

| Verdict | Evidence |
| --- | --- |
| `ORIGINAL_EQUAL_ALL` | Both native lanes equal their own complete requested reference |
| `PORT_INTRODUCED` | Native with canonical inputs differs from canonical DOS |
| `RECONSTRUCTION_INTRODUCED` | Canonical lane equals; original lane differs |
| `UNATTRIBUTED` | Replay or coverage is incomplete, without an independent port finding |

The observer stops at the first game-state difference. It reports names,
hashes, a native frame and byte differences from the nearest retained DOS frame.
A frame from another entry is labelled and is not exact expected bytes for the
differing entry. The admission report retains the earlier Event.v findings and
their original evidence. With handler-register replay, repeated complete checks
now give `ORIGINAL_EQUAL_ALL` in all three scenarios: new-game-save 64/64,
quick-game 2000/2000 and long-run 3000/3000 in each executable's own lane.
There is no next first difference inside these finite tapes. Results per
scenario are tracked in `evidence/port/verification-matrix.json`.

```powershell
python -m unittest portable.tests.acceptance.test_native_acceptance portable.tests.acceptance.test_full_inputs
python portable/tests/acceptance/run_virtual_audio_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
```

Controls cover split storage, state-only stopping, malformed/RLE clocks, normal
SDL delivery, nested enqueue stamps and wrong chronological order. `--disable
clock` consumes captured values but substitutes deterministic host values for
state-reaching MacTickCount after entry 1; startup and main's three pacing calls
keep their tape. After the deliberate clock perturbation, order equality is no
longer required of that negative trajectory. It stops on game-state differences
at entry 2. `--disable input` removes delivery and is not a successful state
control when entries are missing.
`--disable irq-context` keeps delivery and clocks but suppresses captured
CX/DX: new-game-save again stops at original 39 / canonical 36 and quick-game
at 659 / 660, all on window_current_event; long-run remains equal. Compiled
controls check distinct context words on successive raw events, disabled
replay, malformed words and the unchanged nested enqueue stamp/order.

```powershell
python portable/tests/acceptance/step_check.py --disable irq-context --out build/current/tests/steps-control
python portable/tests/acceptance/step_check.py --steps 8 --out build/current/tests/steps-prefix
python portable/tests/acceptance/step_check.py --steps 8 --disable clock --out build/current/tests/steps-clock-control
```
