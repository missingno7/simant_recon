# Bounded native audio queue, 2026-11-15

The queue presentation policy fixes the persistent startup/stall backlog without
changing the native-clock-v1 game clock, ISR work, source events or synthesis.
The full investigation and commands are in the new follow-up section of
`build/workers/audio-backend/RESULT.md`. [receipt.json](receipt.json) pins builds,
observations and verification. No canonical or desktop source changed.

## Cause and policy

The game pacing epoch precedes resource/device initialization. Previously the
device began consuming its four silent periods as soon as source time produced
one 10 ms block. During startup catch-up, about 278 ms of source time then ran
in 10 ms of physical time. This queued roughly 320–330 ms. Equal subsequent
producer/consumer rates preserved that lag. A native move modal loop drained
the queue and then appended the whole catch-up interval, leaving 950–960 ms;
a one-second debugger-style suspension raised it to 1,950–1,960 ms.

`portable/platform/sdl3/audio.c` now retains the newest four completed blocks
in a presentation ring. First consumption waits for one device period of
balanced physical/source production, allowing one source quantum of tolerance.
An early balanced observation is revoked if catch-up resumes. After a producer
service gap exceeding five periods, presentation pauses during catch-up and
requires four **new** source blocks before restarting, so already-heard PCM
cannot be replayed. Minimize/restore needs no desktop hook.

The target is four device periods; the bound is five, including the pending
partial block. On excess, the stream lock makes clearing and requeuing only
the newest four blocks atomic. This drops the oldest queued prefix once, with
an intentional short discontinuity. It does not consume/resample old audio to
discard it, wait for queue drain, change source time or run future game work.
The renderer still processes every event, including PCM that presentation drops.
Physical consumption performs observations only.

On the measured device each block is 480 frames at 48 kHz: 40 ms target and
50 ms bound. Other device period sizes scale the policy. This is SDL input-queue
latency, excluding unknown hardware buffering and acoustic/FM attack delay.

## Session evidence

The 95-second recipe covers title, Quick Game, actual Ant Menu sound effects,
modal holds, minimize/restore, a native `SC_MOVE` loop and a debugger-style
whole-process suspension. Window PID/title and rectangles are recorded; the
native move really moved the main SimAnt window. Each action is released and
each child joined. A separate quiet 120-second session has no interruptions.

For the counterfactual baseline, the same freshly built source and renderer
objects are relinked with only presentation `begin`/`service` made no-ops. This
restores first-block start, silent priming and unbounded append. Both versions
use identical source-level diagnostics, including actual first sample emission.
It reproduces the delay measured on commit 5a9ddfa; it is not a second game or
sound sequencer and is never a shipped mode. Both 95-second runs contain exactly
the same **1,089 ordered source trigger coordinates/arguments** (1,076 OPL
key-ons and 13 sample starts).

| Phase | Prior queue | Bounded queue |
| --- | ---: | ---: |
| Title, Quick Game, modal Ant Menu | 320–330 ms | usually 30–40 ms |
| Minimized/restored | 320–330 ms | usually 20–30 ms in this run |
| After native move | 950–960 ms | 30–50 ms |
| After debugger suspension | 1,950–1,960 ms | 20–50 ms |

The measured queue plus partial block never exceeds 50 ms at observation points.
The quiet 120-second session has a 39 ms median, zero steady-play overflow
corrections and zero underruns/missing bytes. It has one 10 ms startup alignment
trim. The 95-second run under concurrent test load has two one-block corrections
outside the injected interruptions (42.803 and 79.983 s), plus the startup
rebuild and one restart per injected stall. These nonzero counts are retained.

The native move deliberately blocks production for about a second. The bounded
run records 98 starvation requests between its last pre-move and first post-move
observations (64.999–66.012 s), and zero increments elsewhere. The prior large
buffer masks part of that stall and records 63. No claim is made that audio can
continue rendering source decisions while the game thread is frozen. Recovery
removes the persistent backlog instead of preserving it. The debugger suspension
also freezes the audio thread; its hardware silence is not a callback underrun
measurement.

## Trigger to queue head

The optional `SIMANT_AUDIO_QUEUE_TRACE` records physical/game trigger time,
source sample setup **and first mixer contribution**, OPL key-on frame, stream
epoch/offset, queue-head arrival brackets, discarded events and pending close
events. A setup alone cannot count as a sample reaching the head. Head arrival
is bracketed by successive consumption observations: at most 0.979 ms wide for
the measured bounded sample effects and 2.127 ms for music events.

| Source event | Prior head-arrival bracket | Bounded bracket |
| --- | ---: | ---: |
| First sample, game 26.756 s | 326.109–326.952 ms | 42.207–42.963 ms |
| First post-move sample, game 67.101 s | 961.820–962.474 ms | 47.824–47.903 ms |
| First post-breakpoint sample, game 76.141 s | 1,962.049–1,962.706 ms | 47.972–48.039 ms |

All 13 sample starts reach their first-contribution queue head: bounded upper
arrival estimates range 37.046–48.978 ms, median 44.988 ms. OPL key-on median
falls from 331.989 to 40.029 ms; bounded p95 is 48.593 ms and maximum observed
upper bound is 50.027 ms. The bounded run explicitly discards 38 music onset
markers while trimming/catching up; they are not reported as zero-latency plays.
All source events and FM state still execute. No ear or acoustic latency test
was possible.

## Verification

Fresh final build `build/workers/audio-backend/latency-verified/` has stable
input pins and executable SHA256
`d7c319c0c266d795c27700ab68967884d8bbdfa4bd4245dce20da2af303344d4`.

* Upper regression: 18/18 sound-off, 18/18 sound-on and 22/22 playback, unchanged
  references and 1 ns sample bound. Both deterministic variants render zero
  frames and open no device queue.
* All 18 port suites pass, including database, RNG, 194-case simulation,
  VGA/Save/Load, diagnostics, hosted/modern windows, clocks, input and audio.
* Audio suite uses real SDL queue/PCM with controlled device time. It checks
  startup catch-up, revoking premature readiness, retaining newest PCM in order,
  zero steady-state starvation, one oldest-prefix trim, and fresh-content stall
  restart. Omitting the gate or bound fails the same fixture.
* The 26 audio/content/timeline controls, repository audit and whitespace check
  pass. Normal CPU remains in the measured approximately 2–4% of one-core band;
  the receipt/report retain both CPU pairs and sampling limitations.

The quiet paired CPU sample is 2.16% before and 2.88% after; under concurrent
port test load it is 2.64% before and 3.84% after. These bounded process samples
meet the requested band, without claiming numerically identical CPU usage.

Reproduce in fresh output directories:

```powershell
python portable/build.py --out build/workers/audio-backend/recheck
python portable/tests/acceptance/run.py --build build/workers/audio-backend/recheck --out build/workers/audio-backend/recheck-acceptance
python portable/tests/audio/run.py --out build/workers/audio-backend/recheck-audio
python portable/tests/audio/unbounded_control.py build/workers/audio-backend/recheck build/workers/audio-backend/recheck-control
python portable/tests/audio/measure_latency.py build/workers/audio-backend/recheck-control build/workers/audio-backend/recheck-before --interruptions
python portable/tests/audio/measure_latency.py build/workers/audio-backend/recheck build/workers/audio-backend/recheck-after --interruptions
python portable/tests/audio/latency_metrics.py --before build/workers/audio-backend/recheck-before --after build/workers/audio-backend/recheck-after --out build/workers/audio-backend/recheck-metrics.json
```

The supported renderer still runs only for physical playback. Observation files,
game assets, payloads and generated PCM remain under ignored `build/`. No commits
were made by this task.
