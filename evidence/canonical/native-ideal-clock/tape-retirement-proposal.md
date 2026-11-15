# Proposed replacement set before tape retirement

Proposal only, 2026-11-15. Nothing is retired, no upper-test entry point is
changed, and no commit is made. The final replacement set passes 18 sound-off
and 18 sound-on gameplay lanes plus 22 playback lanes. See
[shared observation results](shared-observation.md) and the pinned
[receipt](shared-observation.json). Both ideal-v1 variants use the same bounded
keyboard-context-v1 and animation-identity rules; raw observations remain
available. Their source-use proofs are independent of Sound Mode.

## Final replacement set and cost

Run all three commands, with fresh output directories and cached references:

```powershell
python -m portable.tests.acceptance.ideal_check --sound-off --build BUILD --out OFF_OUTPUT --jobs 3
python -m portable.tests.acceptance.ideal_check --build BUILD --out ON_OUTPUT --jobs 3
python -m portable.tests.acceptance.playback_check --build BUILD --out PLAYBACK_OUTPUT --jobs 3 --timing-tolerance-ns 1
```

References are build/reference/sound-off-identity (unchanged) and
build/reference/sound-on-identity-v1 (22 new US/ideal-clock captures). State,
checkpoint frames and raw audio must all pass. Sound-off additionally requires
shipped Sound Mode 0, BIOS-rate PIT, zero sound ISR execution and no device
writes. Playback compares metadata, decoded/emitted bytes, counts and ordered
song/note events exactly, with a 1 ns bound only on sample timestamps. Starts,
stops and song/note events actually match at zero; 14 lanes have interior sample
serialization differences of 1 ns. This retains the prior smallest measured
bound, without increasing tolerance or masking bytes.

Measured sequential process walls: sound-off 32.04 s, sound-on 84.69 s,
playback 129.41 s; combined **246.14 s (4.10 minutes)** with three lanes in
parallel inside each command. Budget **4?5 minutes** on this machine with
cached references. This includes fresh observer builds/preparation, all
comparisons and coverage reporting, and excludes a production rebuild,
reference refresh and the independent gate/port suites. The production build
was reused after all 505 input pins matched. Fresh DOS observer build cost
191.13 s; sound-on reference refresh cost 272.19 s. Scratch was routed through
a C: temporary-directory junction after D: exhausted space; timings describe
that setup and ordinary concurrent validation load, not a storage-independent
benchmark. Measure again after extracting the unused legacy link hooks.

## Coverage against the retained checks

| Obligation | Retained tape / old audio workflow | Proposed replacement and limit |
|---|---|---|
| Gameplay state | Nine recipes, both DOS executables: 18 lanes, 26,128 entries | Same corpus in each sound mode: 36 lanes, 52,256 entries; 1032 views instead of 1024, including eight additional yard ID holders |
| Rendered output | 152 checkpoint frames | 152 per mode, 304 total; exact frame/palette/cursor comparisons |
| Event context and animation IDs | Raw physical/context words can differ | Same narrow 3 Event views and 11 yard ID views in every ideal-v1 capture/check; bounded projection with original negative controls; raw diagnostics retained |
| No-sound hardware behavior | Separate sound-off evidence | 18 lanes require zero sound ISR/device writes, shipped no-sound configuration and BIOS timer; original references remain byte-identical |
| Raw audio commands | Tape has 9 equal / 9 known different lanes | 18 sound-on gameplay lanes and all 22 playback lanes exact; tape rerun retains precisely the same per-lane audio diagnostics |
| Actual playback | Old content/raw OUT and PCM diagnostics, replay timing | 11 tick recipes ? both executables, 22 lanes / 28,176 entries; exact ordered events, descriptor/PCM bytes and emitted contributions; sample-time bound 1 ns |
| Shipped content coverage | Supported sound profile and focused fixtures | DOS/native identical union: 8 MIDI identities, 23 effects, 18 sample identities; overlap in 16 lanes; source song completion and fast/slow/stop paths plus existing restart/notification regressions |
| Loops | Synthetic wrap/metadata fixture | Normal shipped descriptors observed here have zero looping voices and zero wraps; retain synthetic wrap/metadata test, no claim of a shipped loop |
| Timer/service correctness | Chronological tapes and replay-specific negatives | Independent clock vectors, actual fast/slow/restart ISR tests, omitted-notification negative, direct modifier-read admission and observer/profile/IF negatives remain required |
| Unsupported hardware | DMA/AdLib/status-only limitations | Keep explicit provider rejection and fixture negatives; this corpus does not establish general device closure |
| Historical DOS artifacts | Physical CPU-time heap-move/IRQ glitches | Preserve historical evidence; ideal computation costs zero logical time and does not reproduce those artifacts; no sample substitution or waiver |

The focused audio-controls/audio-restart recipes supplement normal gameplay;
their names do not prove a new successful menu-restart path. Actual restart
behavior is also covered by the independent source/provider tests. Presentation
and other explicitly separate diagnostic views retain their existing policy.
Entry-time clock diagnostics are not promoted to an additional acceptance gate:
the retained sound-off new-game-save lanes still have their existing entry-37
diagnostic, identical to the pre-change result; state, frames and audio pass.

## Reviewable retirement sequence

First extract the observation-only builder and link/binding helpers from
step_check.test_build. Both new checks still depend on that builder, so deleting
the old driver first would break the replacement. Move useful read-only audio
observations/decoders before deleting their sole producer. Then review an exact
removal list and use python tools/workspace.py for retired files. None of these
removals occurs in this round.

Retire per-site clock answer/count tapes, synthetic overrides and clock-tape
options; chronological service-order and tape-positioned physical input replay;
replayed ISR schedules/counts/completions and foreground call-boundary tapes;
DSP/MPU readiness and song-done answer replay; per-event IRQ CX/DX replay.
Keep constant machine/DGROUP profiles, fixed real-code service bindings and the
actual ideal-clock transaction. Providers answer on their own logical timeline.

Concrete areas to split/remove are replay sections of
portable/whole_program/platform/sdl3/test_observer.inc and audio_tape.inc,
host/input/application options and fields, queue IRQ-context callbacks,
provider replay branches and native_observer.c replay wrappers. full_inputs.py,
replay parts of audio_timer.py, sound_services.py, device_services.py,
step_repeat.py and replay-only tests become deletion candidates. Preserve the
observation-only portions of sound_calls.py and source boundary binders.

Stop emitting unused replay sidecars only after their diagnostic/coverage
consumers have migrated. Replace the sound-off .timer == E assertion with an
observed zero sound-ISR count before removing that sidecar. Do not skip source
instructions or substitute game results.

Keep ideal_build, readable patches/pins, compact/native read-only observers,
reference validation, state/SaveRec schemas, runtime-view reasons, both narrow
helpers and all negative controls, raw Event/ID/OUT/PCM diagnostics, exact frame
checks, tick recipes, source-clock tests, modifier-read bindings, US proof and
profiles. Keep production idle/yield and logical-clock behavior. Preserve all
historical reports, first differences, reference identities and glitch evidence.

In the separately authorized retirement change, update the upper-test entry
point, READMEs, platform.json and known_findings together; run a fresh native
build, gate, all port suites and this full three-command set. Replace each
replay-specific negative with an actual timeline/order/IF/profile/observer
negative that preserves its obligation. Report new wall times and confirm no
replay input paths or task processes remain before presenting the diff for
review. Current tape, old audio workflow and upper-test wiring remain intact.
