# Step-based scenario observations

Both keyboard-context-v1 and anim-id-pattern-v1 are part of the **shared ideal-v1
state contract for every sound variant**. ideal_observation.py prepares the same
1032-view schema, emits both recorder configurations and validates both receipts.
The helpers, event-code/byte scope and eleven-holder allowlist are unchanged.
Both observers require both rules in ideal mode; raw observations are retained.
Sound selection changes only configuration and the variant's hardware assertions.
Sound-on identity references are under build/reference/sound-on-identity-v1;
existing sound-off-identity references remain valid. Prior raw-only sound-on
references require fresh recording with the eight additional scalar views.

The sound-off gameplay lane uses the shipped `SIMANT.CFG` selector
`Sound Mode: 0` in identical disposable copies on DOS and native. Run the
ideal-v1 recorder/checker with `--sound-off`. References are stored separately
under `build/reference/sound-off-identity/<scenario>/<exe-sha>-ideal-v1-sound-off`.
The scripts are unchanged. No original asset is edited and no game sound
decision is replaced. Checks require zero initialized/requested sound mode,
PIT divisor65536 at every DOS entry, no sound ISR and no device writes.

`keyboard-context-v1` supplies an additional observer fingerprint stream for
window_current_event, its window_previous_event copy, and input_queue[7]. Only
bytes08..0B (Event.h/v) are omitted, and only when the record's code isFAxx or
one of the scan processor's F081..F087 commands. Every other byte and every
mouse/object record compares fully. Raw hashes and snapshots stay intact.
The explicit source/type census and proof pin are in event_context.py; the bounded
HCEGANT640-wide proof is
[`normal-words.md`](../../../evidence/canonical/native-input-irq/normal-words.md).
`test_event_context.py` exhausts all codes/bytes in both C and C++, including
raw, adjacent-record, mouse/object, flags/time and payload negative controls.
Local Event copies have no global per-entry view; root:1B73::Queue0 is an18-byte
hot-box queue and is excluded from this Event rule.

`anim-id-pattern-v1` additionally observes the15 rain IDs, the two17-word swarm
arrays, and eight scalar yard ID holders by sentinel/equality pattern, assigning
ordinals by first appearance per holder per entry. All remain game_state.
The [complete use audit](../../../evidence/canonical/native-ideal-clock/animation-identity.md)
finds only same-set equality/lookup and -1 uses, no arithmetic, ordering or
SaveRec overlap. Eight previously unbound scalar views now have original
read/write instruction anchors. Raw hashes/checkpoint state remain unchanged;
new per-entry .anim-ids diagnostics report all raw words and first differences.
The combined qualified hash stream is .hash.ideal-state-v2. runtime_views.json
names each participating holder and cites the source lines. Other animation
sets receive no rule. Earlier sound-off recordings are preserved in
`to_delete/build/reference/sound-off`.

The upper-layer regression is the complete three-command replacement set:

```powershell
python -m portable.tests.acceptance.run --build build/current/portable
```

It runs these commands sequentially, with three independent lane processes per
command, validates every reference and requires all 18/18/22 lanes equal:

```powershell
python -m portable.tests.acceptance.ideal_check --sound-off --build BUILD --out FRESH_OFF --jobs 3
python -m portable.tests.acceptance.ideal_check --build BUILD --out FRESH_ON --jobs 3
python -m portable.tests.acceptance.playback_check --build BUILD --out FRESH_PLAYBACK --jobs 3 --timing-tolerance-ns 1
```

State, all 152 checkpoint frames per gameplay mode and exact per-entry raw OUT
commands must pass. Playback additionally checks all 22 lanes' ordered song/note
events, voice descriptors, rates, volume, complete decoded bytes and emitted
contributions. Only sample timestamps have the measured 1 ns bound. Metadata,
events and bytes are exact. Shipped captures contain no looping voice; retain
the synthetic loop/wrap controls. Content comparison in the gameplay checker is
still a separately labelled diagnostic, with its historical 16-fast-period
bound; the playback gate uses the absolute timeline and 1 ns bound above.

Missing references, incomplete entries, invalid profiles, missing checkpoints
and unsupported device output fail. The old known-findings policy is retired;
there is no accepted failing lane. The existing repository unittest bridge calls
this same driver under `tools/validate.py --upper-tests`. It never starts DOS.
Default output is `build/current/tests/acceptance`, retired with workspace.py
before reuse. Explicit output paths must be fresh. Results retain each command,
exit code and measured wall time; each child joins its lane pool before exit.

Native execution uses the ordinary ideal clock and actual provider scheduling.
Tick scripts under `dos/scenarios/ideal-v1` preserve file order at equal tick
thresholds. Constant executable profiles bind DOS load/environment and the
INT09 wrapper's DGROUP operand once. The profile checker independently checks
those words against the relocated DOS dump. No expected state is opened by the
native process: the output-only observer gathers every entry, then Python
compares after exit. No source instructions or game results are substituted.

Sound-off requires shipped CFG Mode 0, BIOS-rate PIT, no device writes and zero
sound ISR entries. Each ISR contributes a positive count (fast=1, slow=16) to
the read-only content endpoint. Zero periods proves zero ISR entries, including
in retained references. New recorder STATS also reports the explicit entry count.
The obsolete `.timer == E` assertion is gone.

## Record references

```powershell
python portable/tests/acceptance/build_observer.py --out build/workers/NAME/observer
python portable/tests/acceptance/step_record.py --sound-off --build build/current/portable --observer build/workers/NAME/observer/observer-build.json
python -m portable.tests.acceptance.playback_check --record --build build/current/portable --observer build/workers/NAME/observer/observer-build.json --out build/workers/NAME/recording
```

The recorder supports ideal-v1 only. Existing sound-off-identity and
sound-on-identity-v1 references remain hash-pinned and unmodified. Recording
validates the effective US keyboard environment, immutable executable, saved
input, schema, observer and independent instruction bindings. Old versions must
be moved with `python tools/workspace.py PATH...` before recording again.
The original millisecond scripts remain for DOS bootstrap/load binding and
independent DOS diagnostics; the game runs tick recipes during ideal capture.

The compact observer emits state hashes, full state/checkpoint frames, raw input
register diagnostics, audio OUT and decoded/emitted content plus ideal-clock
diagnostics. It no longer emits `.order`, `.timer`, `.sound` or `.sound-calls`,
nor per-site answer/count RLE. Pinned legacy sidecars inside retained reference
directories remain historical payloads, validated for identity and never replayed.
`sound_calls.py` is a read-only historical diagnostic decoder. Timer and content
instruction binders live in `audio_bindings.py`, `audio_content.py` and
`audio_playback.py`. `native_build.py` links observation-only source copies;
canonical sources and the production generated game TUs stay unchanged.

## Controls and scope

Run `python -m unittest discover -s portable/tests/acceptance -t .` and the
source-clock/input suites in `portable/README.md`. Replacement mapping:

| Retired replay control | Retained/replacement obligation |
| --- | --- |
| Clock substitution, wrong PC, RLE counts, missing tape end | Independent DOS/native read-rule vectors, rational endpoints; complete observer rows/trailers and instruction-binding mutations |
| Service-order corruption and nested enqueue stamps | Tick-script order, actual input-IRQ/FIFO/IF controls, internal-refresh omitted-guard negative; raw audio/event order negatives |
| Input removed or late/missed boundary | Actual charged-read admission and IF-disabled input controls; no-input/incomplete observations cannot pass |
| Per-event IRQ CX/DX disabled or malformed | Fixed profile mutation checks plus exhaustive keyboard-context C/C++ qualification, mouse/object/adjacent-byte negatives and raw words retained |
| ISR schedule suppressed, wrong fast/slow/busy completion | Actual fast/slow/restart/stop ISR tests, rational Q partition, missing slow notification, early/reload-edge and forced-IF negatives |
| Foreground sound placement or function-ID corruption | Real provider timeline and restart tests; ordered song/note/OPL and complete sample-content negatives |
| Device-answer replacement disabled | Autonomous ISA/device timeline, real DSP status/song completion and explicit unsupported-profile/DMA negatives |
| Foreground census/alias/argument failures | Source-bound voice/music/timer instruction mutations, exact metadata/payload and missing observer-event controls; historical call decoder remains |
| State-only stop / independent frame and audio completion | Output-only observer gathers every entry; Python compares state, frames and audio independently; each required result must be complete |
| Old version admitted | ideal-v1/revision, profile, observer/rule receipt and pinned-stream admission failures |

The full mapping with concrete test references is in
[`tape-retirement.md`](../../../evidence/canonical/native-ideal-clock/tape-retirement.md).
Historical DOS heap/IRQ glitches, first differences, measurements and reference
identities remain evidence; ideal time gives computation zero cost. No waveform,
analogue device, unsupported hardware, arbitrary malformed-resource or complete
CPU-interrupt-placement equivalence is claimed.

## Checkpoint pictures and view policy

Capture entry 1, every 256 entries, the final entry and the first entry after
each script section. No extra drawing or polling is requested. Native raw state
dumps retain startup selection and `--dump-entry N`; all entry hashes and
checkpoint scanouts remain unconditional, including after any mismatch.

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
