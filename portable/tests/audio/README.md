# Native audio boundary

`intent.c` preserves ordered sound/song requests and the DOS driver's option
gates. The SDL3 adapter queues unsigned 8-bit mono PCM into a real SDL playback
stream. The sample decoder handles all 57 active SOUND kind-5 records. The
logical sound map covers ids 0–55 through the DOS SFX note table and the DAC
instrument table; aliases select their source sample object (for example,
sound id 0 selects object 35, id 1 selects object 1, and id 55 selects object
10). This is explicitly the DAC table profile and does not emulate runtime
device selection. Song events remain typed logical requests; MIDI song records,
bank selection, instruments and song progression are unsupported and must not
be presented as playing.

The source anchors are `src/root/m00DF.c` (`myBeginSound`, `myBeginSong`,
`mySoundIsDone`, `mySongIsDone`), `src/root/m295C.c` (`f_295C_0367` dispatch),
`src/root/m0000.c` (kind-5 sample loading and 16-byte header removal),
`src/root/m290D.c` (`f_290D_000E` nibble decoder), and
`src/data/d55B3_00B8.c` (DAC sound-id-to-sample table). The decoder is a direct
unsigned-byte transcription of the exact historical function.
`python portable/tests/audio/dos_decoder_differential.py` directly executes the
frozen DOS `f_290D_000E` in Unicorn 2.1.4 for all 57 active kind-5 records and
compares every output byte with the native decoder. Its source-only predecessor
remains in `evidence/source-only-report.json` and `reference_pcm.py`; the current
differential report is `evidence/dos-decoder-differential.json`.

The SDL stream test queues the decoded alert1 752-byte PCM buffer unchanged in
mono U8 format. 22,050 Hz is a host test choice, not a DOS hardware-rate claim.
This boundary does not reproduce the DOS sound-card allocator, DAC channel
overlap/priority, pitch/volume/tuning, loops, MIDI, runtime device selection or
timing. It establishes decoded sample equivalence, not faithful playback speed
or full sound effects. The frozen DOS `mySoundIsDone` returns 1 unconditionally;
the portable logical API preserves that result. The SDL adapter separately
exposes queue-drained status for host playback.

Inputs stay in ignored `assets/SOUND.NDX` and `assets/SOUND.DAT`; their hashes
are pinned in `tests/resources/ASSET_SHA256.md`. No original binaries or assets
are copied into this directory or the source tree.

`portable/platform/sdl3/audio_host.h` is the earlier request-oriented API. It
supports decoded one-shot SOUND requests and isolated source-profile SFX, while
MIDI song requests still return `UNSUPPORTED_MUSIC`; it has no `LIVE_DAC_SFX`
capability query or live queue/pump calls. It does not feed synthetic BIOS or
port reads to device detection.

Whole-program source playback is a separate, later API in
`portable/whole_program/platform/whole_audio_provider.{h,c}` and
`portable/platform/sdl3/whole_audio_provider.{h,c}`. Generated `m284A` drives
the original MIDI parser and cadence; generated `m295C` performs source voice
allocation; generated `m290D` sends ordered sampled-DAC start/stop events to
the native mixer. The current native backend explicitly selects sampled DAC
mode 1 and does not emulate BIOS, MPU-401, OPL, or other DOS devices. The
strict actual-song harness, `python
portable/tests/whole_program/run_generated_song_harness.py`, uses the shipped
SOUND kind-18/kind-20 song and kind-5 sample records. Its receipt records host
loader/channel setup boundaries and does not claim DOS timing or waveform
equivalence. `run_audio_provider_tests.py` separately tests the SDL3 dummy
stream bridge with a deterministic event producer; that SDL smoke is not the
actual-song harness.
