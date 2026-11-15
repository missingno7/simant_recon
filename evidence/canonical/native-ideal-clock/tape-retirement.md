# Tape retirement

Owner-authorized retirement, 2026-11-15. The upper-layer test is now
`python -m portable.tests.acceptance.run`: sound-off gameplay, sound-on gameplay,
then playback, with 18, 18 and 22 required lanes. There are no accepted failing
lanes. The previous proposal and shared-observation reports describe the
pre-retirement checkpoint and remain unchanged historical evidence.

The canonical game source is untouched. Both sides retain the ideal-clock
transaction, actual source/provider ISR execution, tick-script input delivery
and fixed executable profiles. Native providers supply their own clock/device
answers. Expected state is compared only after execution exits.

## Removed and retained

Per-site clock answer/count readers and writers, synthetic clock overrides,
chronological service-order replay, tape-positioned SDL delivery, per-event IRQ
CX/DX, replayed sound ISR schedules/completions, foreground sound-call schedules,
DSP/MPU readiness and song-done answer replacement are retired. The old check,
repeat driver, replay-only producers/tests and known findings have been moved
with the workspace retirement tool. Obsolete reference generations are moved
to ignored `to_delete/`, preserving their manifests and payloads. The scratch
`retirement-inventory.json` and `to_delete/moves.jsonl` give exact destinations.

Observation-only native linking is in `native_build.py`. It pins the production
build, replaces only test copies of the host/provider and four sound TUs, and
links read-only state/frame/voice/music hooks. It no longer profiles complete
input/sound modules or links device-answer/foreground scheduling wrappers.
`audio_bindings.py` retains independent timer instruction/IVT binders;
`audio_observer.inc` retains raw OUT/content coordinates. The source voice/music
binders, historical `sound_calls.py` decoder and all raw observation decoders stay.

The recorder no longer emits `.order`, `.timer`, `.sound`, `.sound-calls` or
per-site answer/count RLE. Its real timer entry/completion observations still
drive content diagnostics and exclude charged ISR reads. Every sound ISR adds
a positive 1 or 16 fast periods to the content counter: a complete endpoint of
zero proves exactly zero ISR entries for the retained sound-off references.
New ideal STATS additionally gives the explicit sound ISR entry count. No
`.timer == E` assertion remains. Legacy sidecars inside the two retained identity
reference roots stay hash-pinned historical payloads and are never replayed.

Keep the ideal DOS patches/pins and native logical clock; production pacing,
idle/yield and ISR/IF rules; US proof and load/DGROUP/environment profiles;
1032-view census, SaveRec and current category reasons; the two bounded observer
helpers and all their byte/code/holder negatives; raw Event/ID/OUT/PCM diagnostics;
exact frame/palette/software-cursor checks; source-clock, restart and playback
tests; synthetic loop/wrap tests and explicit unsupported hardware rejection.
Historical physical CPU-time heap/IRQ glitches remain historical evidence, not
waivers or substituted sample bytes.

The root DOS recipe JSON and millisecond scripts remain: the JSON pins the
scenario/save identity used by ideal capture, and the scripts still serve DOS
bootstrap memory/load binding and independent DOS acceptance/diagnostics. The
actual ideal recordings use `dos/scenarios/ideal-v1` tick recipes unchanged.

## Negative-control mapping

| Retired control | Replacement that keeps the obligation |
| --- | --- |
| Clock substitution; wrong/missing PC; malformed RLE/count or missing end | `ideal_rule_check.py`: independent DOS/native golden vectors and rational endpoint tests. `test_audio_bindings.py`: shifted entry/opcode/IVT/selector mutations. `test_ideal_speed.py`: complete per-entry raw/qualified output. `test_audio_commands.py` and `test_audio_content.py`: missing/truncated trailer rejection. |
| Input removed; missed/late service admission; unclocked query positioning | `ideal_internal_refresh_check.py`: real queued SDL key held across internal writes/ISR reads and delivered by the next charged foreground read; omitted-guard negative. `input_irq/fixture.c`: IF-disabled input remains pending, enabled reads deliver in order, nested callbacks cannot reenter. Incomplete trajectories/checkpoints fail the upper driver. |
| Chronological order corrupt; nested enqueue stamp/order wrong | `idle_yield/rule.c` shared read vectors, real `input_irq` and BIOS/FIFO controls, source event timestamps; raw OUT and playback song/note/OPL-order negative controls. No stored order directs execution. |
| Per-event CX/DX suppressed or malformed | `test_timeline_contract.py`: both fixed profiles checked against the independent relocated instruction/PSP/environment; mutations fail. `test_event_context.py` exhausts C/C++ code/byte qualification, mouse/object and adjacent-record negatives. Raw physical words stay diagnostic. |
| ISR replay suppressed; malformed schedule/mode/busy completion | `ideal_rule_check.py` executes real fast/slow/restart/stop ISR code, checks rational Q partitions, omitted slow notification, early fractional edge, missing reload edge and forced-IF negatives. `audio/device_boundary.c` checks CLI coalescing, restart and device behavior. DOS timer binders retain actual busy-exit classification for observation. |
| Foreground sound placement or function ID corrupt | Actual source/provider timeline, restart and stop tests; `test_audio_playback.py` detects reordered/changed/missing song, note, instrument, volume and stop events. `test_audio_content.py` detects changed ordered OPL/sample metadata, bytes and contributions. No foreground ID schedule remains. |
| Device replay disabled | `virtual_audio_test.c` checks wall-delay and pump-partition invariance on the actual logical timeline; `audio/device_boundary.c` checks real DSP readiness, samples, timer transitions and explicit DMA rejection. Playback checks source song completion. Unsupported profiles stay open/rejected. |
| Foreground census aliases or PCM argument qualification invalid | Source instruction-bound voice/music/timer observations and their mutations, exact identity/rate/volume/payload tests, absent-event/trailer failures. The historical generic-call decoder still validates type/object words without producing any runtime input. Compiler profiling/COFF alias controls have no surviving consumer. |
| Sound-only order failure must not hide state/frame/audio findings | The native observer gathers all requested entries without reading expected hashes. Python then reports state, frames, raw commands and content independently. All required components must be complete and pass, including playback's state/frames/raw audio. |
| Old replay version admitted | Only ideal-v1 recorder/check admission remains; clock revision, US environment, profile, observer/rule receipt and pinned stream failures remain strict. No version-upgrade path manufactures expected observations. |

The isolated IRQ fixture also needed current externally driven clock stubs and
replacement of its obsolete wall-time throttle assertion with an explicit IF
hold/release test. Its 2304-step canonical instruction matrix stays identical.
The omitted-caller-word regression now uses the ideal-clock lane for its live
negative, retaining all seven focused production source-boundary checks.

## Acceptance and limits

Gameplay checks require equal state, exact checkpoint frames and exact per-entry
raw OUT bytes/order in both sound variants. Playback requires those components
plus exact ordered song/note events, voice metadata, decoded bytes and emitted
contributions. Only sample timestamps have the established 1 ns bound; no
tolerance was widened. The older 16-fast-period content comparator remains a
separately labelled gameplay diagnostic. Entry-time clocks remain diagnostic.
Shipped captures have no looping voice/wrap; the synthetic controls stay required.
Physical DOS CPU/IRQ instruction placement, analogue waveforms, arbitrary
malformed resources and unsupported devices remain outside the bounded claim.

The first complete post-removal run passed 18/18, 18/18 and 22/22 in 224.87 s.
Fresh observer linking is smaller. Final current-source suite/gate times,
registration requirements and search/process checks are recorded in
`build/workers/retire-tapes/RESULT.md` and its JSON/log receipts.

## Owner-maintained registrations

`layout/repository.json` was not edited. Replace its retired `step_check.py`
entry point with `portable/tests/acceptance/run.py` (the full 18/18/22 set).
Update `role_roots[portable/whole_program/platform/sdl3/test_observer.inc]` to
output-only frame/audio observations, and the
`platform_services_and_application` reason to describe tick scripts and output
observers. The current test bridge already reaches the new driver; no change to
`tools/validate.py` or `tests/test_native_acceptance.py` is needed. Regenerate the
status page after the registration update. The frozen registration currently
names a retired file, so the architecture gate must report that fact.

The owner-maintained verification matrix needs the new driver and independent
clock/input/profile contract, both gameplay sound variants and playback results,
the shared observer rules, raw diagnostics, exact frame/raw audio requirements,
the unchanged 1 ns sample timestamp bound, current costs, and removal of the old
known-findings/scheduling policy. Its historical rows can remain history with
clear supersession. The earlier slow-mode clock finding was repaired by the
retained native-clock-v1-irq-v3 timeline; it is not a current tape requirement.
