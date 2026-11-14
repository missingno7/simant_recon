# Audit of the differing non-verdict views

`audit.json` enumerates all 29 views and their exact baseline lanes, source
causes and actions. `build/workers/presentation/RESULT.md` records the full run
history and final results. The observations use fresh builds and immutable v7
original/canonical references, with no DOS state writes or reference replacement.

Two complete runs of the same baseline binary compared every fingerprint at
every entry. Exactly four views varied: clip_rectangle_workspace,
clip_window_z_order:raw, fd_50F6_37FA, mode_knob_anim_index. All 152 picture
comparisons repeat. None of the audio/selector/memory/filename views varied.

## Uninitialised values with no output influence

`hanim_MakeAnimSet` writes count/max/objs but leaves nextId unwritten. The native
allocator uses malloc, so heap residue initializes the IDs returned by
`hanim_AddAnimObject`. DOS also does not initialize that field. Add masks to
0x7fff and checks uniqueness; callers retain the returned label and pass it to
Find/Set/Remove/Hide/Show. Rendering orders objects by priority, never ID. The
two knob globals are opaque labels, not frame indices. Their only source uses
are `src/ui/colony_controls.c` storing Add's return and passing it back to Set.
Changing the seed renames labels without changing positions, pictures, order
or buffers. There is no claim of raw ID identity.

`test_presentation_residue.py` compiles the actual canonical Add/Find/Make,
Set/reinsert, Hide/Show and removal bodies. Heap fills 00/55/FF yield the same
ordered draw-relevant fields; an invalid-label negative control fails. This
supports the source consumer proof; it does not normalize the measured IDs.

`win_raise_and_reclip` copies all 32 words of a local array after initializing
only its sentinel-terminated prefix. All z-order readers stop at 8000. Raw suffix
differences remain reported. `clip_*` temporary allocations write complete live
rectangles and only the top=8000 word in the terminator; other terminator words
and workspace suffix retain residue. Every reader checks top before using the
other fields. The 152 retained checkpoint pairs have equal live clip prefixes;
136 have raw workspace differences, all outside those prefixes. Corresponding
normal and raw z-order fingerprints are retained independently. No bytes are
masked out of the raw view or removed from a verdict. Source access sites and
the raw-byte checks are in audit.json and the worker's audit script/results.

`g_4332` only takes values 0/1: Show clears it, Hide writes one, and IRQ0 shifts
right then branches before restoring one. Both 0 and 1 shift to zero and take
the same branch. Its remaining difference is IRQ0 phase residue and converges
before any drawing decision. The independent cursor-show counter g_4352 is
write-only. Neither difference explains a picture mismatch in these tapes.

## Audio progress differs from entry 1 (audio verdict)

The service tape supplies completed song-stopped/port-read answers, clocks and
input admissions. It supplies no IRQ0 audio-execution schedule. Tape refresh
avoids ordinary application idle; native audio pumping otherwise follows host
virtual time (`portable/platform/sdl3/whole_audio_provider.c`), not the DOS
foreground's CPU cost or PIT interrupt phase. With --poll-ns 1, the native MIDI
state is still at its newly-started values at entry 1 (last event zero, status
FF, countdown five), whereas DOS has processed thousands of song ticks.
Default tempo yields delay scale 95; DOS has already processed a tempo event
and shows 107. Voice note/age/priority/instrument fields differ accordingly.
These are deterministic replay differences, not host nondeterminism or address
differences. `src/sound/midi_player.c`, midi_voices.c and device_channels.c show
their paths to note dispatch, song completion and resource loading.

The eight differing MIDI/voice views stay `audio` in `runtime_views.json` and form
the step check's separate audio verdict (`audio=AUDIO_DIFFERENCE first=1` in every
lane, pinned in `portable/tests/acceptance/known_findings.json`). They are not in
the game-state verdict: the game reads audio only through the device-status queries
the tape replays, and putting them there would stop every state comparison at
entry 1. (This audit first moved them into the game-state verdict; the supervisor
chose the separate verdict instead.) The address-valued sound selectors listed in
`audit.json` are `runtime` views. Every view remains fingerprinted.

An eventual audio replay fix needs independently observed PIT0 ISR entry and
return/admission coordinates, reload/fast-vs-slow phase and IF/PIC coalescing,
including nested sequencer resource work. A game clock return or stopped answer
does not determine these. This task does not invent that missing schedule from
desired state, nor re-time/relabel the v7 references.

## Representation and environment

The eight sound output words are source-derived assembler OFFSET selectors,
never host pointers. Canonical DOS linking places TIMER_TEXT four bytes later
than the original symbolic assembler displacements emitted by the port. The
selected SB word and its SB constant retain the same identity; the provider
compares those selectors and never executes the number. Volume-table offset
is another source logical address: subtracting its matching channel base
produces the same row. The build's canonical_audio_data.c and assembler-fixup
receipt bind these values. These are representation differences, not ASLR.

The three allocator segment/paragraph fields are DOS physical-arena bookkeeping;
native handle storage has no DOS arena and these unused scalar owners remain
zero. Native capacity is explicitly 64 MiB; startup_free_memory_bytes therefore
reports 67108864 versus each DOS environment's available conventional memory.
Both exceed the shipped startup minimum. This environment difference can appear
in the explicit memory diagnostic and is not a claim of equal allocator history.

FindIndex initializes db_index_lower_bound to zero before every search. The
difference is the residual last resource lookup; no other source consumer reads
the previous value. Different asynchronous sound/resource service histories
need not leave the same scratch bound. Save filename C strings are equal at
every retained checkpoint; original-only differences start beyond their NUL.
The source's strcpy/strrchr/read guards never consult that unused tail. The raw
100-byte view remains measured. Evidence records bounds and actual first offsets.
