# Audio content verification (v10)

The current result is **18 complete state/frame-equal lanes, 9 AUDIO_EQUAL and
9 AUDIO_DIFFERENCE**, with no incomplete audio captures. This is not an all-lane
audio-equivalence claim. The [per-lane table](stream-triage.md),
[receipt](receipt.json) and [three DAC investigations](sample-relocation.md) state
what is established and what remains different.

## Content contract

Instruction-level DOS CPU/IRQ placement is not a port requirement. V10 retains
US-pinned input/device replay and the observed ISR schedule, then judges the
whole run by content rather than per-entry OUT interleaving:

* Complete OPL register/value writes remain ordered on each channel, including
  both operators, and on the global-control stream. Cross-channel and OPL/DAC
  interleaving does not decide equality.
* Sample starts remain ordered by object, rate, volume, loop/end data and full
  decoded-payload SHA256. Physical mono mixer slot is diagnostic, not identity.
  Each voice's emitted position/byte sequence must agree through the common
  duration. Interior substitutions or missing bytes are not aligned away.
  Only a terminal duration difference bounded by the actual final-emission
  displacement is permitted. Audible start/stop use first/last contributions;
  setup-call timestamps are separate diagnostics. A regression covers a delayed
  setup callback with identical actual output.
* All 37 existing audio progress views stay compared per simulation entry.
  Unequal vectors require symmetric matching to independently observed nearby
  progress states within the same tick bound. Native observes from the first
  IRQ, including startup. No expected vector controls execution or scheduling.
* DSP reset/speaker controls participate. For each capture, the two observed
  contributions must reproduce every actual direct-DAC byte. Missing trailers,
  malformed vectors, unsupported output or incomplete replay cannot pass.

The fixed tolerance is **16 fast PIT periods = one slow sound IRQ = 2.86964 ms**
(divisor 214, clock 14318180/12 Hz). Fast and rejected IRQ entries count 1;
slow entries count 16. This is not a simulation-entry or arbitrary ordinal bound.
The otherwise equal experiment original has a 16-period OPL displacement at
entry 917, register 70h/value FFh. A 15-period negative control fails; 16 passes.
No larger bound is used to cover later scheduler gaps. See
[content-controls.json](content-controls.json).

DOS `observer.txt.content` records source-bound completed voice setup/stop,
actual two-channel contributions, complete OPL writes and per-tick progress.
Native uses read-only callbacks at the corresponding two statements in a pinned
test copy of the generated whole sample TU, plus a weak producer observation
hook. Ordinary canonical source and producer logic are unchanged. All decoded
payloads and original-derived captures remain ignored, outside Git.

`observer.txt.audio` / native `audio-commands.txt` and their exact comparison
remain intact as `audio_raw_diagnostic`. They do not decide the audio verdict.
Sound-ID mismatch no longer truncates content coverage or automatically makes
audio incomplete: the complete captured run is compared after the scheduler
filters later sound markers. Non-sound services and inputs remain strict.

## What was kept and removed

V8-style ISR counts/service coordinates are retained, with v9's actual busy-exit
IRET classification. Schedule-off still gives entry-1 content/progress failures
in both eight-entry controls, with equal state/frames and zero executed IRQs.

The **115-entry v9 foreground schedule is retained**. Its requested deletion
condition is not met: on the fresh v10 references, removing it gives a 32-fast-
period startup displacement and different per-channel music content (experiment
and load-from-save), while those state/frame lanes still finish equal. The older
full control and channel counts are retained in worker evidence; the current two
controls are pinned in `content-controls.json`. This does not prove every one of
115 entries individually minimal. No new instruction-placement replay was added.

The raw-command verdict and sound-order-as-incomplete gate were removed from
acceptance. Raw traces, the frozen census and its proven argument qualification
remain diagnostics/scheduling evidence. The old reaper/resource gap proof remains
[historical evidence](reaper-gap.md), not a reason to omit post-gap content.

All eighteen references were re-recorded under US as `service-samples-v10`.
V9 references were retired with `tools/workspace.py`; the retirement inventory
pins both versions and records any differing old observations. Stored references
were never patched or upgraded by deriving expected state/content from native.

## Results and limits

| Scenario / lane | State entries | Frames | Audio | First entry / content difference |
|---|---:|---:|---|---|
| ant-commands/original | 1000 EQUAL | 5 EQUAL | AUDIO_DIFFERENCE | 598 / SAMPLE_OUTPUT_BYTE |
| ant-commands/canonical | 1000 EQUAL | 5 EQUAL | AUDIO_DIFFERENCE | 749 / SAMPLE_OUTPUT_BYTE |
| experiment/original | 1000 EQUAL | 5 EQUAL | AUDIO_EQUAL | - |
| experiment/canonical | 1000 EQUAL | 5 EQUAL | AUDIO_EQUAL | - |
| full-game/original | 1000 EQUAL | 5 EQUAL | AUDIO_DIFFERENCE | 461 / SAMPLE_START_PLACEMENT |
| full-game/canonical | 1000 EQUAL | 5 EQUAL | AUDIO_DIFFERENCE | 618 / SAMPLE_OUTPUT_BYTE |
| interactive-play/original | 2000 EQUAL | 19 EQUAL | AUDIO_DIFFERENCE | 832 / SAMPLE_OUTPUT_BYTE |
| interactive-play/canonical | 2000 EQUAL | 19 EQUAL | AUDIO_DIFFERENCE | 778 / MUSIC_PROGRESS |
| load-from-save/original | 1000 EQUAL | 5 EQUAL | AUDIO_EQUAL | - |
| load-from-save/canonical | 1000 EQUAL | 5 EQUAL | AUDIO_EQUAL | - |
| long-run/original | 3000 EQUAL | 13 EQUAL | AUDIO_DIFFERENCE | 2359 / SAMPLE_OUTPUT_BYTE |
| long-run/canonical | 3000 EQUAL | 13 EQUAL | AUDIO_EQUAL | - |
| new-game-save/original | 64 EQUAL | 2 EQUAL | AUDIO_EQUAL | - |
| new-game-save/canonical | 64 EQUAL | 2 EQUAL | AUDIO_EQUAL | - |
| quick-game/original | 2000 EQUAL | 13 EQUAL | AUDIO_EQUAL | - |
| quick-game/canonical | 2000 EQUAL | 13 EQUAL | AUDIO_EQUAL | - |
| random-17/original | 2000 EQUAL | 9 EQUAL | AUDIO_DIFFERENCE | 1130 / OPL_PLACEMENT |
| random-17/canonical | 2000 EQUAL | 9 EQUAL | AUDIO_DIFFERENCE | 1073 / SAMPLE_OUTPUT_BYTE |

The three requested DAC cases are proved DOS heap-relocation glitches, not port
sample bugs. Their actual differing bytes remain visible under the literal
emitted-byte criterion. Additional ant canonical/long-run byte differences and
post-gap content/progress/placement differences remain first findings; they are
not declared port defects or silently accepted. Full normal-play audio closure
therefore remains open for nine lanes.

The fresh build runs all 26,128 state entries and 152 checkpoints equal. All
**61 acceptance tests** pass against the measured findings, including compiled
content/clock/IRQ controls; every ordinary README port suite plus virtual audio
and clock passes. The direct checker exits 1 for the nine reported audio findings;
that is distinct from the passing known-findings regression suite. No canonical,
include or layout source was edited, and no commit was made.

Reproduction, exact commands, current build/observer pins, controls and remaining
findings are in `build/workers/audio-content/RESULT.md` and `receipt.json`.
