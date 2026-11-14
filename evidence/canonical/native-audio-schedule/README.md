# Foreground sound services and exact audio streams (v9)

V9 observes every reviewed foreground operation that can access the sound
ISR's shared state. The original and canonical DOS lanes bind their own
executable instructions independently. Native executes the existing canonical
sound code and readable hardware ISR projection; there is no copied sequencer,
private voice model, countdown adjustment or desired-output selection.

The frozen [census](foreground-census.json) and its
[per-function review](foreground-census.md) enumerate 115 stable entry IDs
(95 C and 20 ASM), direct and dispatch-table paths, complete extents, native
projection coverage and IF protection. Eight ISR-only C helpers, four IRQ
entry/exit labels and one code-segment data extent are explicit exclusions.
Nine unavailable hardware leaves remain explicit coverage failures if reached.

A foreground entry appends service 245 to the chronological order and one ID
byte to `.sound`. It increments the existing service/query coordinate. Native
drains all recorded ISR completions due before that entry, then checks both
the marker order and exact function ID before executing its body. Every nested
foreground call is observed. ISR-origin calls are excluded by actual ISR
context, not IF: the source can execute STI inside the handler. Compiler entry
instrumentation covers whole unchanged canonical C modules and port/IF helpers,
including within-TU calls. The native OPL C wrapper and register leaf retain
the source's separate calls.

The entry must first match its complete bound relocated procedure in live DOS
memory. This rejects DOSBox internal COM stubs at the future game address
8240 before load; it does not use a timed arming delay. Bindings include original
symbols/whole procedure bytes, or independent canonical MAP/OMF/CodeView or
reachable extents and fixups. Source data and code are never patched.

## Shared-state qualification of the generic resource hook

`snd_expand_sample_resource` is also installed as the callback for every
DBRecall. Only `type == 5` reaches sample work. Every other 16-bit type follows
a stack-argument guard and return with no sound-state access, nested calls or
I/O. Both actual DOS procedures and all 65,536 type words are checked by the
reviewed guard proof. DOS uses SS:SP+14; a typed native observation wrapper
qualifies the same argument before calling the unchanged canonical body.

All calls, including non-PCM calls, remain in hash-pinned `.sound-calls`
diagnostics. Only the shared-state PCM path consumes ordering ID 20. No function
or view is removed; the argument predicate is independent of expected state,
resource number, output, timing or a comparison result. The diagnostic parser
also checks that PCM calls agree with the checked ID stream.

A conservative trial exposed a genuine graphics cache difference: DOS recalled
bitmap 111 for SaveGame's second slider arrow; native already held it in cache.
Their generic type-2 sound-hook invocation counts differed despite equal drawing
and audio. Exact DOS stack/code and native cache-return witnesses are in
`build/workers/audio/v9/chain/` and `v9/native-chain/`. Those trial references were
retired and all references re-recorded under the proved shared-state predicate.
The eighteen v9 captures remain unchanged. Runtime filtering after audio
placement coverage is lost never rewrites or relabels a stored reference.

## ISR completion classification

`.timer` retains every completed fast/slow hardware entry at its service ordinal.
Kind 2 means the actual independently bound `snd_timer_reentrant_exit` IRET was
executed. Other fast completions are kind 1; slow completions are kind 0.

Nesting alone cannot establish rejection. The normal fast epilogue executes
`DEC busy` immediately before IRET while IF is enabled. An IRQ in that window
has a nested hardware frame but sees busy zero and runs the full mixer. The old
v8 depth-only classifier skipped such full executions, producing a one-sample
and later countdown lag. V9 records the actual exit PC rather than inferring
that result from depth. This is an execution observation, not sampling or fitting
playback state. Independent original/canonical instruction and machine-code
controls are in `build/workers/audio/v9/late-timer/`. A late-PIC probe did not
preserve the rare phase and is explicitly not positive dynamic proof.

Native invokes the existing ISR body once per recorded full execution and its
busy guard for an observed rejected execution. It checks fast/slow identity
without overwriting native mode. A tape suppresses autonomous SDL IRQ scheduling;
ordinary play keeps the SDL clock. Schedule-off consumes the same events while
executing none and restores entry-1 MIDI/voice differences.

## Device streams and limits

Both lanes record every byte OUT to OPL 388..38B, SB 220..22F, low DMA 00..0F and
DMA pages 80..8F with service ordinal, entry and phase. Exact raw port/value order
within each entry interval participates in the audio verdict alongside every
playback-progress view. No writes or state views are masked, dropped, trimmed,
deduplicated or shifted. Missing/truncated streams or incomplete replay cannot
report equality. Decoded OPL/DSP/DMA commands, per-device subsequences and
service-coordinate drift are diagnostic; they never replace the raw comparison.
Mode 6 uses direct DAC, not DMA. Generic DMA remains unsupported.

An ISR between instructions **inside** a foreground function remains outside
entry precision. The census gives a protection classification and reason for
every function. CLI/STI set IF rather than save or nest FLAGS. Start-song resource
loading precedes CLI; sample-note start writes before masking; a nested queue
helper's STI can precede stop-voice's final pointer clears. Even otherwise masked
updates can have an interruptible prologue. OPL index/data writes are unmasked:
DOS can place a DSP IRQ between them while native's next-entry replay places it
after the transaction. The chained input/BIOS bodies, arbitrary CPU/PIC placement,
other hardware profiles, DMA memory and PCM/time identity are not proved.

Final outcomes and first differences per lane are pinned in `receipt.json` and
`portable/tests/acceptance/known_findings.json`. The working report and exact
matrix-row facts are `build/workers/audio/RESULT.md`; the matrix itself is left
to the owner. Historical v8 measurements remain in `receipt-v8.json`.

Controls: `test_sound_services.py`, `test_sound_calls.py`, `test_audio_timer.py`,
`test_audio_commands.py`, the virtual audio/clock and ordinary audio suites,
and the full scenario checker with the schedule-off contrast.

## Independent verdicts after sound divergence

Sound-call order is an audio observation. Its first marker or function-ID
mismatch records the entry, phase, ordinal, expected/actual IDs and service
markers, then sets audio coverage incomplete. It never invokes the state/frame
replay-error handler or the global order-control bypass.

Subsequent native sound entries are ignored and recorded marker245/ID pairs are
skipped. All other markers, primitive values and input positions remain strictly
checked. Recorded ordinals stay intact. Inputs in a skipped sound-only interval
map to the preceding completed non-sound boundary; due sound IRQ completions wait
for the next actual non-sound service, as in v8. Both projections follow only the
filtered stream. Delaying those inputs until the next service entry would move
some past the foreground input test and is not the accepted implementation.

Raw command/progress observations continue after detachment, but cannot claim
covered audio equality there. The audio signature retains its valid-through entry
and first mismatch details, plus any earlier raw command difference. The exact
reaper hardware return-PC evidence is retained in [reaper-gap.md](reaper-gap.md)
as a placement class outside the tested domain. It is not pursued or repaired.

Controls modify disposable replay inputs only: `sound-order` corrupts the first
driver ID, producing audio incomplete with complete state/frames; `service-order`
also corrupts the next non-sound marker and must still fail replay after audio
detachment. `audio-timer` retains the earlier schedule-off control.

The final fresh-build run completes all 18 state/frame lanes: 26,128 entries
and all 152 checkpoints equal. Audio is 5 equal, 8 different and 5 incomplete.
A second run reproduces the exact signatures; all 52 acceptance tests pass,
including the sound-only and subsequent non-sound controls. All eighteen DOS
reference manifests are unchanged. No DOS re-recording was performed.

## Final independent lane results

| Scenario / lane | State | Frames | Audio | First audio entry / layer | Sound coverage ends |
|---|---|---|---|---|---|
| ant-commands/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 598 / DIRECT_DAC_SAMPLE_PRODUCTION | - |
| ant-commands/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 704 / OPL_DSP_ORDERING | - |
| experiment/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| experiment/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| full-game/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_INCOMPLETE | 178 / SOUND_PLACEMENT_OUTSIDE_DOMAIN | 178 |
| full-game/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 618 / DIRECT_DAC_SAMPLE_PRODUCTION | - |
| interactive-play/original | EQUAL 2000/2000 | EQUAL 19/19 | AUDIO_INCOMPLETE | 832 / DIRECT_DAC_SAMPLE_PRODUCTION | 1001 |
| interactive-play/canonical | EQUAL 2000/2000 | EQUAL 19/19 | AUDIO_INCOMPLETE | 678 / SOUND_PLACEMENT_OUTSIDE_DOMAIN | 678 |
| load-from-save/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 992 / OPL_DSP_ORDERING | - |
| load-from-save/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| long-run/original | EQUAL 3000/3000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 2099 / OPL_DSP_ORDERING | - |
| long-run/canonical | EQUAL 3000/3000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 2099 / OPL_DSP_ORDERING | - |
| new-game-save/original | EQUAL 64/64 | EQUAL 2/2 | AUDIO_EQUAL | - / NONE | - |
| new-game-save/canonical | EQUAL 64/64 | EQUAL 2/2 | AUDIO_EQUAL | - / NONE | - |
| quick-game/original | EQUAL 2000/2000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 1760 / OPL_DSP_ORDERING | - |
| quick-game/canonical | EQUAL 2000/2000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 1917 / OPL_DSP_ORDERING | - |
| random-17/original | EQUAL 2000/2000 | EQUAL 9/9 | AUDIO_INCOMPLETE | 1130 / SOUND_RESOURCE_CALL_ORDER_COVERAGE | 1130 |
| random-17/canonical | EQUAL 2000/2000 | EQUAL 9/9 | AUDIO_INCOMPLETE | 1073 / SOUND_RESOURCE_CALL_ORDER_COVERAGE | 1073 |

The first audio entry may precede sound detachment: interactive original has a
DAC-byte difference at832, then incomplete placement coverage from1001. The
exact signature and first command writes are in [stream-triage.json](stream-triage.json).
Post-detachment hashes/writes remain observed but do not establish covered audio
equivalence. Non-sound order and all state/frame checks continue strictly.
