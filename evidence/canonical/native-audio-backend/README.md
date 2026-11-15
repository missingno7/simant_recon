# Native audio events, 2026-11-15

The native backend consumes direct OPL2 register events and decoded sample voice
events. The canonical sound driver remains the only sequencer. No `src/`,
`include/` or `layout/` file is changed. This is a port boundary change, not a
new byte-exact reconstruction claim.

The design was written before implementation in
`build/workers/audio-backend/RESULT.md`. That report includes the complete
commands, measurements, unsuccessful integration attempts and limitations.
The compact machine-readable receipt is [receipt.json](receipt.json).

## Event boundary

`audio_native.c:snd_opl_write_regs` sends a register/value pair directly through
`PortableWholeAudioHost.opl_register`. Its old index/data OUTs and fifty status
reads are gone. Instrument selection, voice assignment, pitch, level, envelopes,
song parsing and note order remain in the canonical C driver. YMFM is the same
pinned YMF262 implementation in OPL2 compatibility mode, with the same
14,318,180 Hz crystal and one synthesis frame per 288 clocks.

The logical `sample_timer.asm` projection still advances the canonical 8.8
positions, wraps loops, clears finished voices, preserves channel order and
the over-end branch that skips output/later channels. It still owns the fast/
slow PIT transition, sequencer divider, pending IF/PIC delivery and old INT08
notifications. These operations run whether PCM is rendered or not.

At STI and timer-start boundaries the provider publishes completed canonical
voice changes: start with object, copied decoded payload, length, step, range,
loop flag, attenuation and position; stop on source removal. Each fast ISR
publishes selected positions/attenuation and, only on the original output path,
an emission event. The renderer never computes a next position, schedules a
note, loops a voice, decides completion or writes game state. Copying payloads
at start permits canonical resource relocation/release before delayed rendering.

The renderer reads the selected byte through the canonical eight volume tables,
uses 128 for inactive voices, averages with the original integer truncation,
then converts unsigned 8-bit amplitude to signed 16-bit. Position/emission
events are converted to 48 kHz PCM by zero-order hold. A skipped emission holds
the preceding sample. FM plus mono samples sum in wide integers and saturate
to S16 stereo. There is no DSP/DAC byte stream in production.

Events are ordered on game nanoseconds. Block rendering generates chip frames
preceding each register event before applying it. SDL gets only completed
48 kHz stereo blocks; its consumer observes starvation but never runs game
code. The existing device-period submission and four silent priming periods
remain. Deterministic and dummy-video/headless runs instantiate no renderer and
open no playback device. Sound mode zero also renders nothing.

The unchanged canonical mode-6 startup still calls reset/probe/readiness leaves.
A narrow fixed capability adapter answers those calls and maps speaker on/off
to sample-enable events. This is deliberately retained source ABI compatibility,
not a virtual sound card. Unsupported controls, DMA and other profiles fail.
`isa_devices.cpp/.h` were retired with `tools/workspace.py`; the ISA parser,
DAC-change queue, OPL port protocol and status-driven synthesis are removed.
The old production `SIMANT_AUDIO_TRACE` port logger is removed with them.

## Playback observation and coverage

The unchanged DOS observers/reference captures remain authoritative. No
reference was recorded, replaced or derived from native output in this work.

| Observation before | Observation now |
| --- | --- |
| Successful song start/stop, physical OPL note start/stop, configured effects | Same source B/D/N/F/H sites in disposable generated TUs |
| Sample object, step, attenuation, end, loop, complete decoded payload | Same source S site and complete payload identity |
| Actual positions and per-voice attenuated bytes at ISR emission | Same P stream, computed from live source payload/position/volume only when observation is requested |
| Sample stop/replacement/completion | Same source X and ISR completion sites |
| Absolute source event and emission time | Same native-clock-v1 rational PIT observations; unchanged 1 ns sample bound |
| Actual DOS DAC bytes reconstructed from P contributions | Retained independently on DOS |
| Native DSP output independently reconstructed from P | Replaced by source decoded payload/position/attenuation; native historical OUT is explicitly labelled a diagnostic projection |
| Native sound-card PCM rendering | Direct provider-to-renderer integration controls plus independent old/new PCM comparison |

Projected native OUT is not claimed to be an independent DAC assertion. The
source observer still compares every common-duration position/attenuated byte,
full payload and all metadata against DOS; it retains the existing terminal
duration rule and all missing-event/content/order/volume/time/loop/completion
negatives. The new renderer is separately exercised for actual PCM, copied
payload lifetime, mute, future-event exclusion, four-voice averaging and lack of
autonomous progression. Invalid position, invalid volume, backward event time
and unsupported DMA fail explicitly. Thus source content coverage is retained
and renderer-specific checks replace the removed physical-device assertion.

No shipped looping voice was observed; the old synthetic loop/wrap comparator
controls remain. Other hardware, analogue output, arbitrary malformed resources
and physical DOS CPU/IRQ placement are not proven.

## Verification and measurements

Fresh isolated source build: **18/18 sound-off, 18/18 sound-on, 22/22 playback**.
Both deterministic sound variants render zero frames and open no physical audio
device. The run used unmodified pinned DOS references and the 1 ns sample bound.
Concurrent desktop edits invalidated earlier live-tree attempts; the report
identifies the frozen source inputs and later live integration separately.
The isolated reconstruction gate also reports VALIDATION PASS; its existing
separate code/data/layout/whole-image debt remains unchanged. Live read-only
repository audit passes. Live generated status pages were not rewritten.

The audio suite and 48 acceptance observer/unit controls pass. The port database,
RNG, 194-case simulation, VGA, Save/Load, virtual clock/audio, real PIT edge and
omitted-notification/forced-IF negatives, internal refresh, idle-yield, input IRQ,
mouse, hosted-window and modern-window checks pass. The diagnostics suite fails
before game launch because desktop startup cannot create a per-user directory
outside the writable workspace. This is recorded, not waived as a pass.

`portable/tests/audio/render_compare.py` renders immutable DOS source events
through both backends. The old backend is obtained read-only from revision
`662b078cf7f06dc93abd62122422994410c24b57`, only for the offline comparison.
For the four-second title and sample-effect windows, both stereo PCM streams
are bit-identical: RMS error **0**, maximum difference **0**, relative spectrum
L2 difference **0**. Title RMS is 336.6496; effect RMS is 4363.8884 S16 units.
WAVs and payload-bearing observations stay under ignored `build/`.
**No ear test was possible.** This proves the bounded digital renderer comparison,
not physical speaker or analogue equality.

Controlled 25-second windowed Full Game runs use identical frozen desktop
sources and scripts, mode 6, unpaused play and 86 outer loops. CPU during the
12-second-to-exit play interval is **3.72% → 2.40% of one core** (one bounded
pair, about 35.5% lower). Total process CPU is **1.344 → 1.109 seconds**.
Reported underruns/missing bytes are **0/0** in both runs. Device submission
blocks are 480 frames (10 ms); four priming periods are 40 ms. Actual exit queue
snapshots are **16,800 → 15,360 frames (350 → 320 ms)**, excluding unknown device
and hardware buffering. The nominal priming duration is not claimed as measured
end-to-end latency: the inherited startup/catch-up backlog is larger and remains
visible. Queue level never changes the game clock.

Reproduce with a fresh build/output directory:

```powershell
python portable/build.py --out build/workers/audio-backend/portable
python portable/tests/acceptance/run.py --build build/workers/audio-backend/portable --out build/workers/audio-backend/acceptance
python portable/tests/audio/run.py --out build/workers/audio-backend/audio
python portable/tests/audio/render_compare.py --build build/workers/audio-backend/portable --old-revision 662b078cf7f06dc93abd62122422994410c24b57 --out build/workers/audio-backend/wav
```
