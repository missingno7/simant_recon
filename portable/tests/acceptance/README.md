# Step-based scenario observations

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
Default build selection prefers `build/workers/admission/native-final`, then
`build/current/portable`. Default output is `build/workers/admission/check`.
Prior output is retired with `tools/workspace.py`. Checks never record.

## Record references

```powershell
python portable/build.py --out build/workers/admission/native-final
python portable/tests/acceptance/build_observer.py --out build/workers/admission/observer
python portable/tests/acceptance/step_record.py --build build/workers/admission/native-final --observer build/workers/admission/observer/observer-build.json
```

Recording defaults to every scenario and both executables. `--target original`
or `--target canonical` selects one. `--out SCRATCH` records an explicit repeat;
`--steps` and `--cycles` are measured recording controls, stored in its manifest.
Compatible references are reused. An older service contract requires explicit
retirement with `tools/workspace.py` and recording again. References live at
`build/reference/<scenario>/<executable-sha256>-service-samples-v4/`. Original assets and generated
references stay ignored.

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
python portable/tests/acceptance/step_repeat.py REFERENCE REPEAT --out build/workers/admission/repeat-result.json
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

Each actual DOS key IRQ or pointer callback records completed clock, pump and
input-query counts plus simulation entry/phase. The query count includes held-input samples and scroll-call boundaries. Its
single service ordinal is
`clock_reads + pumps + queries + 2*step - phase`. Native admits the recorded
transition at that ordinal through normal SDL translation and the normal
keyboard/mouse adapter. An atomic read caches its result before advancing the
service counter and admitting input; delivery cannot alter a result already
sampled. Entry-only observations admit at the body's next legal input yield.
The state snapshot completes before admitting inputs recorded after entry. Any enqueue stamp caused by delivery belongs to the same
chronological stream and is checked before the interrupted service resumes.
A missed boundary, wrong service, extra read, wrong phase or wrong
input coordinate stops replay. Positive completion requires consumed clock,
service and input tapes. A first state difference intentionally leaves the
remaining reference available for investigation.

BIOS queries are observed at DOSBox's atomic CB_INT16 callback, filtered by the
source INT16 return PCs. Observing the later game-function RETF is incorrect:
a key can arrive after the BIOS sampled an empty queue but before RETF. Queue
count uses its MOV instruction for the same reason. The first-megabyte frame
binds the INT16 vector, STI/FE38/IRET callback stub and source INT16 instructions.
The observer reads guest state and never writes guest code, registers, clocks,
input queues, RNG state or saved records.

Clock count alone does not locate inputs relative to non-clock input queries.
Pump/read fences and per-site position barriers are absent. In tape mode the
captured services replace host time and interrupt scheduling; the platform
admits through its ordinary adapter without advancing a second host timeline
or running an application idle/presentation callback inside a sampled read.
No tape option means ordinary platform refresh, audio and presentation.
`platform/sdl3/test_observer.inc` keeps the optional host hooks together.
GCC entry instrumentation on the two unchanged converted input-reader TUs
observes StillDown and edit_scroll_and_redraw, including calls within the same
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
differing entry. See `build/workers/admission/RESULT.md` for current findings.

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
