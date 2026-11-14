# Step-based scenario observations

The expanded interactive corpus and its action/keyboard-layout limits are in
[`dos/scenarios/corpus.md`](../../../dos/scenarios/corpus.md).
Current findings are retained as failing lanes in `known_findings.json`.
Historical measurements and first-divergence evidence for this expansion are in
`build/workers/corpus/RESULT.md`.

`step_check.py` replays stored DOS references in a compiled native observer.
It starts neither DOSBox-X nor GDB. Each scenario has independent original and
canonical lanes; native consumes that executable's own clocks, device answers and actual IRQ
transitions and compares its state, checkpoint frames and audio observations.

```powershell
python portable/tests/acceptance/step_check.py
```

The command prints one stable line per scenario. Missing references, assets or
builds report `no reference` and exit 0. A state, frame or audio difference, or incomplete replay,
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
`build/reference/<scenario>/<executable-sha256>-service-samples-v8/`. Original assets and generated
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
Every v8 reference records that result and environment pin; record and check
both require proved US. All eighteen references are recorded under US for v8. Historical CZ243 captures and their neutrality proofs are retired, with
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

## Admission and service contract

There is one chronological sequence of observed services:

* Each TickCount return, countdown operand sample and input-enqueue BIOS stamp.
* Completed `snd_service_and_test_stopped` AX and `snd_port_read_byte` AL returns.
  These device answers share the per-site RLE stream and service ordinal.
* The actual input_event_count MOV sample and window-pump entry.
* The BIOS INT16 queue sample: every peek and each successful blocking pop.
* Held-button, keyboard-scan and scroll-lock operand samples, and entry to
  edit_scroll_and_redraw, including its unclocked edge-scroll iterations.
* DoAntSim entry and return, separating input phases from state observations.

`observer.txt.order` stores one byte per service: clock IDs bind to the trace's
`O` definitions; IDs 246-249 are scroll-call/button/scan/scroll-lock samples,
250/251 are simulation entry/return, 252/253 BIOS peek/pop,
and 254/255 queue sample/window pump. Per-site RLE separately preserves every
sampled value. h identifies song completion and j a sound-port byte read; both
are observed at each executable's reachable source-function RETF. DOS call
sites bind to immutable original code or independent canonical OMF fixups;
native call sites bind to the observer wrappers by instruction disassembly. No clock value is interpolated, inferred from native state or
selected to obtain equality.

V6 timing (retained by `service-samples-v8`) holds each scripted key or mouse transition from
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
`clock_reads + pumps + queries + 2*step - phase`. In v6 the historical
`clock_reads` field counts all sampled-return reads, including h/j device
answers; it is not elapsed time. Native admits through the normal
SDL adapter at precisely this boundary. The parser refuses a v6 IRQ whose
coordinates differ from its hold, and checks refuse pre-v8 references. A missed
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

The v6 tapes also retain AX/BX/CX/DX at scan-processor entry (or INT15/AH=4F
while the hook is disabled) and pointer-callback entry. Keyboard admission now
supplies captured CX/DX to the ordinary native scan projection through an
optional test hook. Each staged raw SDL event carries its own pair; the
projection still constructs and queues every Event, including its BIOS stamp.
Physical pointer coordinates retain their existing translation. Missing or
out-of-word keyboard context is a coverage error, never a native-zero fallback.
A pre-v8 reference is refused; its timing cannot be upgraded from expected state.

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
RNG state or saved records. The v6 recorder changes only synthetic-input timing
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

Each lane has three verdicts. **State**: every view classified `game_state`,
per entry; the observer stops at the first difference. **Frames**: the checkpoint
pictures, attribute map and DAC, exact. **Audio**: the views classified `audio`
(MIDI/voice playback progress and driver state), per entry, reported as
`audio=AUDIO_EQUAL|AUDIO_DIFFERENCE first=N`; an audio difference does not stop
the state comparison, because game logic sees audio only through the
device-status queries the tape replays (contract v6). V8 additionally replays observed sound-timer executions and compares every
raw sound-device OUT per interval ending at an entry. Audio-progress views
remain in the verdict without reclassification. The schedule-off control
restores the previous seven first-entry MIDI/voice differences and a first-entry
command difference. Final per-lane signatures and first differences are pinned
in `known_findings.json`; detailed attribution is in
[`native-audio-schedule`](../../../evidence/canonical/native-audio-schedule/README.md).
Address-valued sound selectors (output routine pointers, the volume-table offset)
are `runtime` views. All 152 checkpoint pictures are equal after the Yard
position-table adjacency repair
([`native-yard-offsets`](../../../evidence/canonical/native-yard-offsets/README.md)).

Every SaveRec and every available view classified as game state in
`runtime_views.json` participates in the verdict. Unproven influence stays game
state. Presentation and runtime views are separate diagnostics, audio views the audio verdict; address,
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
their original evidence. All nine scenarios are equal in state and frames in
both lanes; open findings are pinned in `known_findings.json`.

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

## Device-status replay (v6)

The acceptance-only native link runs the real sound query (retaining side
effects), then substitutes the recorded completed answer. With no tape it
returns the real SDL/provider result. `--disable devices` consumes these samples
but returns the live native answer, providing a full-game negative control.
No expected state, fingerprint or desired branch selects a device answer.
This isolates driver/hardware timing, just as clock replay isolates host time;
it does not prove native audio timing or sound output equivalent to DOS.
The census, limitations and per-lane results are in
`build/workers/tape-devices/RESULT.md`.

The retained host-event FIFO is independent of the game's BIOS and hotbox
queues. IRQ dispatch already consumes each event before its retained copy is
released. Tape admission releases those copies just as ordinary application
idle does. Ordinary ingestion stops polling SDL while this FIFO is full, so a
large batch resumes after draining instead of aborting. No buffer was enlarged.


## Checkpoint pictures (v7)

V7 retains v6 service/input timing and per-entry state fingerprints unchanged,
and adds read-only VGA scanout at the same DoAntSim entry, before admitting
post-entry transitions. Capture entry 1, every 256 entries, the last entry,
and the first entry at/after the first command of each commented script section.
The manifest lists those comment times and actual entries (or null when the
bounded scenario ends first). No extra drawing or presentation is requested.

`observer.txt.screen.ENTRY` is SAF7: 24 little-endian u32 metadata words,
16 attribute-map bytes, 256 RGB DAC entries in the recorded DAC bit depth,
256 validity bytes, 16 projected RGB8 colors, 32 INT33 mask words and
640x480 indexed pixels (one byte per pixel). `frame_check.py` defines the
header fields and validates the complete extent. The whole file is hash-pinned.
DOS reads interleaved host VGA planes directly, avoiding CPU aperture reads
that would disturb latches. It applies retrace-latched display start, page,
stride, address shift, byte skip, panning and plane-enable registers. Unsupported
modes, split screens and preset/doubled scanlines fail closed. Native copies its
single aperture and DWARF-bound app.palette; no sync, poll, draw or write occurs.
F12 captures the last completed presentation and is deliberately not used here.

The native observer also writes `native.frame.ENTRY` at each picture checkpoint
while state comparison is active. It contains the exact already-read view bytes
behind that entry's fingerprint row, including separate diagnostics. It invokes
no game code and stops emitting state frames after the first verdict difference;
subsequent picture capture remains independent. This permits byte-level audits
of unused tails and opaque IDs without a new DOS observation or state mutation.

The game draws its own software cursor into both apertures through the source
cursor draw/restore callbacks. The separate INT33 driver's cursor is hidden or
inhibited at every recorded checkpoint; v7 verifies and retains its actual
visibility, position, hotspot and shape masks. A visible INT33 driver is an
explicit coverage error. Compare the entire picture including the game cursor;
**no rectangle or other pixels are masked**. Cursor source state is already
included in the per-entry state views.

Each lane reports `frames` beside its game-state verdict and writes `frames.json`.
A frame difference never stops simulation/state comparison. State comparison retains its first-difference boundary and exact snapshot, while
frame/service replay continues to the requested end; any missing checkpoints
and incomplete service tail are explicit.
Every differing checkpoint includes indexed/visible pixel counts, half-open
bounding boxes, DAC/attribute/projected-palette indices and a PNG triple
`frame-ENTRY-{dos,native,diff}.png`. Magenta marks RGB differences and amber
index-only differences. Unused DAC differences still fail exact comparison.
Native unwritten DAC slots are reported explicitly, including differences from
DOS BIOS defaults; no expected palette bytes are supplied to native.
`known_findings.json` pins frame signatures (including a digest of every
checkpoint row and both raw frame hashes) separately from state signatures;
controls reject both improvements and regressions until the pins are reviewed.

Run `python -m unittest portable.tests.acceptance.test_frames` for frame format,
truncation, exact-pixel/cursor and unused-DAC negative controls. NumPy and Pillow
are required for comparison and review PNGs. Full triage and timing evidence:
`build/workers/frames/RESULT.md`.

Every view is fingerprinted at every entry whatever its category; the category
only decides the verdict. A reference's identity is verified against the policy
it was recorded under, then the verdict follows the current `runtime_views.json`,
the tracked and reviewed classification. Views whose category changed since
recording are listed as `policy_changes` in each lane result. Native storage
locations are resolved afresh; names, ordering, extents, sentinels and original
addresses must match exactly, or the reference must be recorded again.
Reclassifying a view needs evidence in its `reason` (for the cursor call
counters: `evidence/canonical/native-input-irq/cursor-counters.md`).

The host/system mouse pointer is a separate SDL/OS overlay, outside the indexed
texture and F12 bitmap. The read-only hook logs SDL_CursorVisible independently
(`native_host_cursor_visible`); no overlay is painted into or erased from either
reference. The current host has no SDL_HideCursor call. These headless checkpoint
checks prove the game software cursor in scanout, not final OS composition or
absence of an extra system pointer in an ordinary window.

INT33-only metadata words in native SAF7 files are UINT32_MAX (not applicable),
rather than fabricated driver state. The separate host visibility query is
reported in JSON; the game cursor itself is present in indexed pixels.

Checks run three independent scenario processes by default (`--jobs 1` is the
sequential control; `--jobs N`, 1..8, selects the bound). The observer executable
is linked once and then read-only. Each process owns its PE/DWARF readers,
scenario output and disposable asset directory. Lines remain in scenario order;
all child processes are joined before exit. This changes no service/input tape,
state stopping rule or checkpoint pixel/palette comparison.

## Sound execution and device commands (v8)

V8 retains the v7 indexed frame encoding and foreground service/input ordinal.
The hash-pinned `observer.txt.timer` sidecar records a row for every completed
sound ISR execution: `T completed-service-ordinal kind`, where kind is slow (0),
fast (1), or the nested fast busy early exit (2). Entry comments retain the
bound instruction PC and hardware-entry SS:SP. Completion requires the same
SS:SP at a bound IRET or tail jump to the saved INT08 vector. A software
PUSHF/CALL into the slow installer is not a hardware entry. Original entries
bind to their own symbols/instructions; canonical entries bind to their own MAP,
selector operands and vector-installation instructions. Reference validation
repeats these bindings and pins both audio sidecars.

Immediately before the next sampled service, native runs the existing converted
canonical sound ISR for each captured completion at the preceding ordinal, in
completion order. Nested fast entries execute the source busy guard without
sample/sequencer effects. A present tape suppresses autonomous audio-clock IRQs;
ordinary play continues to use the SDL clock. The native fast/slow identity is a
diagnostic assertion, never an expected-state assignment. No fingerprint,
countdown, song offset, note or desired result chooses the schedule. This is
replay of independently recorded executions, not fitted agreement.

This rule cannot reproduce a timer landing between foreground instructions
that access the same sound state. In the startup interval, DOS can decrement
the old countdown before `snd_load_and_start_song` resets it to five; replay
moves those ticks after that reset, before the next keyboard-scan service.
The resulting countdown phase and per-entry note-write shifts remain audio
findings. It also does not execute the chained input timer or BIOS handler,
reproduce CPU/PIC interleavings, or establish PCM/time equality.

`observer.txt.audio` and native `audio-commands.txt` retain `W ordinal step phase
port value` for every byte OUT to OPL 388..38B, SB 220..22F, low DMA 00..0F and
DMA pages 80..8F. A completion trailer is mandatory. No writes are trimmed,
masked, deduplicated or replaced by decoded notes. Compare exact port/value
order within every interval ending at a simulation entry, including startup and
empty intervals. The audio verdict includes both progress views and command
comparison; missing/truncated/incomplete streams cannot report audio equality.
`audio-commands.json` retains all entry signatures, the first raw difference
with OPL/DSP/DMA decoding, and separate service/phase drift diagnostics. Mode 6
uses direct DAC output; generic DMA remains unsupported and fails explicitly.

```powershell
python portable/tests/acceptance/step_check.py --disable audio-timer --steps 8 --out build/current/tests/steps-audio-control
python -m unittest portable.tests.acceptance.test_audio_timer portable.tests.acceptance.test_audio_commands
```
