# Proposed tape retirement after sound-off parity

Proposal only,2026-11-14. Nothing in this round is retired or committed.
The owner-approved observer contract now passes all18 original/canonical lanes:
26,128/26,128 state entries and152/152 checkpoint frames. It also compares eight
additional scalar yard ID holders, for1032 views per entry. Raw keyboard words
and animation IDs remain diagnostic. [Lane results](identity-results.json) and
the [ID proof](animation-identity.md) define the measured claim; sound-on audio
equivalence and general unsupported device profiles are separate.

## Proposed gameplay upper-layer test

Replace the current v10 replay integration with:

```powershell
python portable/tests/acceptance/ideal_check.py --sound-off --build BUILD --out FRESH_OUTPUT --jobs 3
```

Its pass condition is complete state and checkpoint-frame equality on all18
lanes, correct shipped no-sound configuration, BIOS-rate PIT throughout, no sound
ISR and no device writes. Missing entries/checkpoints, invalid profile/pins,
unrecognized observations or nonzero child exit must fail. Inputs remain tick
scripts, immutable assets/save, and a constant per-executable profile. Reference
state is compared after execution; it is never supplied to the game.

Measured current cost:483.47s wall (8.06min),1327.59s summed lane time with
three workers. This includes native observer preparation and all comparisons;
references are cached. Budget about8-9min on this machine, with ordinary load
variation. First few lanes overlapped the end of the regression suite, so this
is a measured integration run, not an isolated benchmark. Reference refresh
costs247.03s wall with three recorders and606.48s summed capture time; it is not
part of an ordinary native check. Fresh native build31.76s; DOS observer
build189.92s. The current check still links unused legacy test hooks; splitting
them may change these costs and must be measured again.

Until the owner authorizes and reviews retirement, step_check remains the
existing upper-layer regression. This proposal does not switch it silently.

## What goes

Retire replay behavior and its production/test wiring, then remove dead tools
using `python tools/workspace.py` with the reviewed exact path list:

* Per-site clock answer/count tapes, synthetic virtual-clock overrides and
  associated `--clock-tape` application options. Keep the fixed service-site
  census that admits real reads to Q: a static address binding is not a tape.
* Chronological service-order replay, tape-positioned physical input delivery
  and old clock/pump/query ordinal enforcement. Gameplay uses the tick script's
  stable equal-time order and the actual ideal clock transaction instead.
* Replayed ISR counts/completions/schedules and foreground sound-entry/call
  boundary tapes. Preserve actual ISR execution and observation needed for
  audio tests. Preserve the native fast/slow timer fix and timer notifications.
* Device-status answer replay for DSP/MPU readiness and song completion.
  Device providers must answer on their own logical timeline.
* Per-event IRQ CX/DX-context replay. Keep the fixed per-executable DGROUP
  profile and the documented keyboard observer projection.

Concrete areas to split/remove: replay sections of
`portable/whole_program/platform/sdl3/test_observer.inc` and `audio_tape.inc`,
their host/input/application options and fields, queue-runtime IRQ-context
callbacks, provider branches gated by audio-timer replay, and replay wrappers
in native_observer.c. Split the observer build/link helper out of step_check
before removing that legacy driver. full_inputs.py, replay parts of
audio_timer.py, sound_services.py, device_services.py, step_repeat.py and their
replay-only tests then become deletion candidates. sound_calls.py and source
boundary binders also contain diagnostics: retain or move the observation-only
parts required by the separate audio check instead of deleting shared decoders.

The compact recorder should stop emitting unused order/clock-answer/sound-call
replay sidecars. Replace its sound-off `.timer == E` assertion with an observed
zero sound-ISR coverage count before removing that sidecar. Static real-code
bindings, instructions and PIC/IRQ execution remain; no instruction skipping
or substituted game results are introduced.

## What stays

Keep ideal_build and its source pins/readable patches, compact/native read-only
observers, ideal_check/reference validation, state schemas and SaveRec coverage,
runtime_views reasons, both narrow observer helpers and their negative controls,
raw ID/event diagnostics, exact frame/palette/cursor checks, tick recipes,
modifier-read bindings, US keyboard proof, and constant machine profiles.
Keep the independent DOS/native clock vectors, actual fast/slow/restart ISR
regressions and omitted-notification negative control. Keep production idle/yield
and logical-clock behavior. DMA/AdLib/status-only limits remain explicit.

Keep historical reports, first-difference findings, reference identities and
audio-glitch evidence needed to challenge earlier claims. Old generated tapes
can move to ignored to_delete only in the authorized retirement change; they
are not silently rewritten as new references. Replace old replay-specific
negative controls with actual timeline/order/IF/profile/observer controls,
without dropping their underlying coverage.

## Audio verification separately

Continue to expose audio-content.py, audio_commands.py and their observation
formats. The retained v10 content result is9 equal and9 different lanes; neither
this no-sound result nor this proposal resolves those sound-on differences.

Prepare a no-replay playback corpus on both DOS executables and native using
supported shipped sound configuration (initially mode6). Tick-scripted normal
game actions must exercise selected songs, effects, overlapping/looping voices,
start/stop/restart and fast/slow transitions through the real source paths.
Observe ordered OPL/channel content, decoded sample bytes/rates/volume/loop
metadata, actual emitted contributions and start/stop/progress. Reuse the
content comparator with its explicit16-fast-PIT-period timing tolerance;
retain exact raw OUT/PCM diagnostics and never hide interior byte differences.
Keep the provider fixture's DMA rejection as a separate unsupported-mode test.

Before deleting the sole remaining producer of a useful audio observation,
move that observation into this playback check and demonstrate equivalent
coverage. Keep the current v10 audio diagnostic workflow available until its
replacement exists. Known DOS heap-move/IRQ output glitches remain reported
differences, not content substitutions or a universal waiver. Audio readiness
must be reported independently from the gameplay upper test.

## Reviewable retirement sequence

First extract a no-replay observer build and the separate audio observation
path. Then remove replay readers/writers, fields/options, dead imports and
tests in one reviewed change, moving retired files with workspace.py. Update
the upper-test entry point, READMEs, platform.json and known_findings together.
Run a fresh native build, all port suites, all18 sound-off lanes, independent
clock/observer controls and the separate playback checks. Report coverage and
new wall times, confirm no replay input paths remain and no task processes are
left, and present the concrete diff for the owner's decision. No step of that
retirement sequence is performed in this round.
