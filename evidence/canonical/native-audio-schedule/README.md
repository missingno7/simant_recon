# Sound ISR schedule and exact command streams

Contract **service-samples-v8** retains every existing state/audio view and the
v7 indexed-frame format. References are re-recorded in the pinned US keyboard
environment for each executable; no v7 observation is retimed or relabelled.

`portable/tests/acceptance/audio_timer.py` independently binds both fast ISR
entries, the slow entry, all four IRETs and both saved-INT08 tail jumps. Original
bindings use original symbols/instructions; canonical bindings use its own MAP,
selector operands and INT08 vector-installation writes. Completion is recorded
only for a tracked hardware entry with the same SS:SP. The software slow-timer
installer path is not counted. Nested fast entries retain the canonical busy
early exit and are counted separately.

The sidecar records every completion with the number of foreground services
already completed. Native invokes the existing ISR translation immediately
before the next sampled service, once per recorded execution, in completion
order. Nested fast entries execute the busy-guard exit without sample or
sequencer effects. Autonomous SDL IRQ scheduling is disabled only with a tape;
ordinary play still uses the SDL clock. Fast/slow disagreement is diagnostic,
never repaired by overwriting native driver state.

The schedule comes solely from independently observed instructions and service
counts. Expected audio state, fingerprints, note data and native results do not
select it. It is replay, not fitted agreement. The schedule-off control consumes
the identical tape without executing it and restores the previous first-entry
MIDI/voice and command differences.

## Precision limit demonstrated at song startup

The service interval can contain both an interruptible resource-loading phase
and a later critical section resetting sound state. DOS executes two original
or three canonical slow IRQs before `snd_load_and_start_song` resets the
countdown to five. Replaying them at the next keyboard-scan service moves them
after that reset. First-checkpoint countdown is therefore DOS 13/native 11
(original) and DOS 14/native 11 (canonical).

Read-only watches and instruction probes establish the order in both
executables; their complete service, timer and command prefixes still equal
the references. The responsible foreground code is
`src/sound/midi_player.c:snd_song_reset_clock` (store 99) and
`snd_load_and_start_song` (store 5); the replay placement is
`platform/sdl3/test_observer.inc:test_service` -> `audio_tape.inc:test_audio_drain`.
This is a demonstrated acceptance-scheduling limit. It does not establish a
canonical reconstruction defect or an error in the translated sequencer.
The chained input timer/BIOS and arbitrary CPU/PIC interleavings are not replayed.

In both 64-entry new-game-save lanes all **12,527** raw port/value writes remain
identical in order when entries are concatenated. Per-entry comparison still
fails: the A0=00/B0=00 transaction crosses from DOS entry 5 into native entry 4.
It is never shifted, trimmed or normalized for acceptance. Full concrete PCs,
times, command lines, hashes and controls are retained in
`build/workers/audio/triage/RESULT.md`.

## Device observation and verdict

DOS `.audio` and native `audio-commands.txt` retain every byte OUT to OPL
388..38B, SB 220..22F, low DMA 00..0F and DMA pages 80..8F, with completed-service
ordinal, entry and phase. Missing/truncated streams cannot compare equal.
Exact raw port/value order in every interval ending at a simulation entry
participates in the audio verdict alongside all playback-progress views.
OPL register/value, DSP command/argument and DMA programming/start decoding is
diagnostic only. Separate ordinal/phase drift remains visible even when raw
commands within an entry agree. This does not compare PCM, DMA memory or elapsed
host time. Mode 6 uses the direct DAC; generic DMA remains unsupported.

Final per-lane observations and verification-matrix facts are in
`build/workers/audio/RESULT.md`; tracked signatures are in
`portable/tests/acceptance/known_findings.json`. The matrix itself is left for
the owner to edit.

Controls: `test_audio_timer.py`, `test_audio_commands.py`,
`run_virtual_audio_tests.py`, `portable/tests/audio/run.py`, and the full
`step_check.py` corpus with the schedule-off contrast.

## Final corpus outcome

All 18 US lanes retain audio differences: the first progress difference is the
countdown at entry 1, and the first exact per-entry command difference is an OPL
pitch-clear transaction at entry 4, 6, 10 or 18. All 26,128 game-state rows and
152 checkpoint frames are equal. `receipt.json` pins the per-lane facts; current
`known_findings.json` pins both progress and exact command signatures.

Later global command histories also differ outside new-game-save, including
cross-device ordering and DSP bytes. They are retained as open findings;
service batching across sample start/reload is a candidate and the translated
mixer/data boundary is not excluded. The emitter paths and exact first windows
are in `build/workers/audio/commands/LANE-TRIAGE.md` and `lane-triage.json`.
The audio verification row remains open; source reconstruction damage and full
native music/effect equivalence are not established by this run.
