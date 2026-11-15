# Tape-free source playback check, 2026-11-15

Status: **partial; unsuitable as a retirement gate yet**. All 22 sound-on lanes
complete: **4 AUDIO_EQUAL, 18 AUDIO_DIFFERENCE, 0 AUDIO_INCOMPLETE**. Original and
canonical DOS are playback-equal at **zero** timing tolerance in all 11 scenarios.
The native first differences are 3–7 ms placement differences. No DOS glitch is
waived, no expected audio comes from native, and nothing is retired.

[receipt.json](receipt.json) records every lane, first difference and layer,
coverage, reference/executable identities, timers, and the independent DOS/DOS
comparison. Full captures and decoded payloads stay under ignored build/reference.
The detailed handoff is `build/workers/audio-playback/RESULT.md`.

## Running it

```
python -m portable.tests.acceptance.playback_check --record --observer BUILD/observer-build.json --out FRESH_RECORD_LOG --build NATIVE_BUILD
python -m portable.tests.acceptance.playback_check --build NATIVE_BUILD --out FRESH_CHECK
```

The default reference root is `build/reference/audio-playback-v1`. Recording uses
the ideal-v1 DOSBox observer, the original executable and the linked canonical DOS
build, shipped Sound Mode 6, immutable assets/save, and tick scripts. Default
binding captures are under `build/workers/dos-clock/binding-v2`; --binding-root
selects another pair. Both bindings are checked against the selected executable.
The existing ideal scripts are reused. Two additional focused scripts are under
`dos/scenarios/ideal-v1/audio-{restart,controls}.scr`.
Their JSON recipes live under dos/scenarios/audio-playback, separately from legacy
root-level corpus discovery.

An ordinary check runs only native, then opens its expected content after the
process exits. Inputs are the script, immutable resources/save, fixed DGROUP and
the ordinary ideal clock. No clock values, sound entries, IRQ schedules, contexts,
completion answers or status bytes are replayed. The old observer build helper is
still used; its replay readers are linked but receive no replay inputs. This does
not claim those readers have been removed. --native-observer can reuse an explicitly
pinned observer-build.json while another worker changes the windowed runtime.

## Observation contract

`SIMANT_AUDIO_CONTENT 2` extends the retained content format with an absolute
game-time nanosecond coordinate after phase. The old accumulated IRQ coordinate
is retained independently as isr_tick; it is not the playback clock.

| Row | Observation |
| --- | --- |
| B / D | Successful song start / active StopSong, with loaded MIDI resource identity |
| N | Physical OPL voice start: instrument, note, source velocity, channel |
| F | Physical OPL voice stop; instrument/note/velocity are resolved from that voice's preceding N |
| H | Configured effect invocation, coverage diagnostic; actual allocated output decides playback |
| S | Completed sample setup: object, fixed-point rate, attenuation row, end, loop start/flag, full decoded bytes |
| X | Explicit or ISR-observed sample completion/stop |
| P | Actual position and volume-scaled emitted byte for each mixer voice |
| O / K | Raw OPL content / DSP controls; diagnostics in playback mode |
| C / Q / E | Entry/progress/completion observations; progress fingerprints are diagnostic |

DOS sites are independently bound in each executable: whole function extents,
far-call stack ABI, the song loader's final successful RETF, and the existing
sample setup/stop and two-channel mix instruction. Full bytes/instructions are
recorded in boundary-manifest.json. Native uses read-only callbacks in disposable
copies of the generated complete song/OPL/effect/sample TUs. A disposable copy of
the native provider observes p->time_ns at event instants. No ordinary source or
producer algorithm is edited. Both observers retain the mixed-DAC reconstruction
check against actual raw DSP output; a missing or invalid capture fails.

The comparison preserves song order and note order per physical OPL channel;
independent channel interleaving does not decide equality. Silent reset calls
are not played notes. Sample identity includes all metadata and decoded payload
SHA256. All common-duration position/byte pairs are literal; an interior mismatch
is never aligned away. Only the retained bounded terminal-duration rule applies.
Every underlying content row retains its actual absolute game time.

The retained bound is **16 fast PIT periods = 2,869,638 ns**, one slow sequencer
IRQ. It is the previously stated content contract's single coarse-service
quantization allowance, not a fitted offset, a simulation-entry allowance or a
new wider bound. Audible sample starts/stops use contributions, not setup calls.
No per-lane shift is fitted. Smaller bounds can expose the common 2 ms startup
placement too; this round has not established that 16 periods is minimal for a
future native backend. Its tighter timing contract remains an open requirement.

## Coverage and findings

The reused corpus plays MIDI resources 10001, 11005, 11013, 11016, 20000, 20001,
20008 and 20010, including title, start and event songs. It invokes 23 configured
effects and emits 18 sample objects. Overlap, sample stop/replacement, music
start/stop/restart, and slow/fast IRQ transitions occur through normal game paths.
The receipt gives per-lane counts rather than inferring coverage from script intent.
The two focused menu experiments do **not** establish additional song restarts;
their recorded output, not their names, determines coverage.

**Looping remains unexercised.** All 58 named shipped Sample descriptors initialize
looped=0; no named source assignment enabling it was found. Every observed setup
has the loop flag clear. The comparator has a synthetic wrapped-emission/loop
metadata negative control, which is not normal-game coverage. No descriptor or
save was modified to manufacture it. Not every possible event song is exercised.

Both DOS executables agree exactly in every scenario, including emitted bytes
and absolute placement. Thus these native first differences cannot be attributed
to the old heap-move or reaper-placement artifacts. Those artifacts remain
documented in ../native-audio-schedule/{sample-relocation,reaper-gap}.md. In the
ideal machine no time elapses inside foreground instructions, so those historical
mid-instruction IRQ examples are not reproduced or silently substituted here.

The first native sample starts are 3,000,000 ns late in ant-commands, experiment,
full-game and audio-controls. Interactive-play first exceeds the bound on a note
by 4,869,638 ns; load-from-save, long-run and quick-game by 3,000,000 ns; random-17
by 7,000,000 ns. These are native timing/read-boundary findings, not proof of a
decoder, instrument or mixer algorithm error. The exact repair site is unresolved.
An actual port repair and its regression remain required; ordinary behavior fixes
in application.c/platform audio were outside this task's authorized writes.

## Coverage of the retained v8/v9/v10 checks

| Earlier observation | Replacement / reason |
| --- | --- |
| v8 ISR counts and entry/service scheduling | Actual ideal-clock PIT/IRQs; per-lane timer sidecars/counts plus independent clock/ISR fixture; scheduling replay is unnecessary |
| v9 full/busy IRET classification, nesting/context | Original timer binding/actual IRET observations retained; ideal clock permits no new elapsed nesting edge; no register-context replay |
| v9 foreground sound-entry census and generic resource callback qualification | Source B/D/N/F/H and sample S/P/X observe played content; old census/raw callbacks remain diagnostics and are not retired |
| v9 reaper/resource-order stop | Complete captures continue to end; content differences fail, never detach audio or omit post-gap content |
| v8/v9 device answers and song-completion replay | Real supported mode-6 providers on logical time; no replay answers; DMA rejection remains the independent unsupported-profile fixture |
| v10 per-channel OPL register/value ordering | Source instrument/note/velocity/channel stream; exact raw OPL stream retained only for diagnosis, permitting future synthesis backend |
| v10 sample object/rate/volume/loop/full payload | S metadata and complete original-derived decoded payload; unchanged strict identity comparison |
| v10 per-voice positions/output bytes and audible first/last contributions | P stream, absolute source event time, literal byte comparison, and independent DAC-byte reconstruction |
| v10 internal music progress fingerprints | C/Q retained as diagnostics; explicit successful song and physical-note events decide playback |
| v10 exact per-entry OUT verdict | Still written as audio_raw_diagnostic by the shared harness; does not decide playback |
| v10 schedule-off/foreground-off negative controls | Historical controls stay; new missing-event, note/instrument/volume, placement, emitted-byte, loop and completion controls test the no-replay comparator; independent omitted-notification ISR control retained |
| v8/v9/v10 game state/checkpoint frames | Separate sound-off gameplay oracle; sound-on state/frames remain diagnostics here |

Checks: 28 audio/content/timer unit controls and the shared DOS/native golden-clock,
actual timer-transition and omitted-notification negative control pass. Adding
DOS playback observations leaves 78-entry original and canonical state, raw OUT
and foreground-sound prefixes unchanged (observer-controls in receipt).

The complete cached-reference check takes **242.82 s wall with three processes**,
including schema preparation and comparisons, using a pinned existing native
observer. The earlier observer compile/link cost 6.21 s; DOS observer build cost
238.72 s. The ten-scenario recording batch took 255.59 s; the eleventh took
15.43 s separately. These measurements do not establish the requested retirement
readiness or a final optimized audio-only runtime: the shared lane still collects
state/frames and raw audio diagnostics.

The accepted native executable is pinned in the receipt. Later mixed rebuilds
during the concurrent window work failed on a GameSpeed debug-view ambiguity or
"source PIT timeline" before entry 1; they supply no accepted parity result.
The failed probes and exact limitations are retained in the detailed RESULT.md.
The final windowed runtime still needs a fresh integration run.
