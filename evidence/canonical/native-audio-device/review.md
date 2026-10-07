# Native Sound Blaster device boundary

The native application previously forced `/s1`, ignored CFG Sound Mode 6,
rendered a binary PC-speaker gate, and aborted on OPL/DSP I/O. Its private copied
voices did not update canonical sample completion; its sequencer also ran at
the sample rate rather than m28BC's divide-by-16 cadence. A separate native ABI
defect read music/effect enable words from padding after a two-byte owner.

The replacement keeps sound selection, song parsing, voice allocation, patches,
sample decoding and note/volume arithmetic in canonical C. The audio adapter
maps the shell's DOS `07A8[1]`/`[2]` words to their existing canonical owner,
`d3D57:07AA[4]`, at byte offsets 0/2. No owner or initializer is added. The
translated m28BC hardware ISR reads and updates the existing canonical sample
channel records and uses the actual 2,048 symbolic ASM volume-table bytes. The
source's over-end skip, completion, /16 divider, slow idle ISR and repeated PIT
reload are retained. CLI/STI set IF, with one coalesced pending PIC IRQ0 edge.

Guest OUT commands reach an ISA device sink. OPL synthesis uses the pinned
BSD-3-Clause ymfm source; SB emulation handles reset/readiness, speaker enable,
mute and direct U8 DAC command 10h. FM synthesis advances before each register
write and preserves output history; DAC writes are presented at their recorded
virtual time. SDL3 receives signed 16-bit stereo at 48 kHz. Source/device state
is controlled on the source thread; SDL consumes already rendered PCM.

The old copied-event queue, linear volume approximation, mode-1 startup gate,
sample scheduler and mode-1 host have been retired through `tools/workspace.py`.
`portable/platform.json:native_audio_boundary` owns the service contract and
limits. `portable/tests/audio/` contains permanent cadence/completion, interrupt,
DSP and OPL controls and a raw-trace comparator.

## Bounded observation and limits

The original DOS `new-game-save` trace contains five DSP writes and 13,476 OPL
writes. A fresh native observation over the corresponding sound-duration window
matches their complete port/value sequences; first difference is absent. A
50-second native wall-time capture instead has additional trailing OPL writes:
native startup reaches sound roughly a second earlier. Raw logs are retained
without trimming/masking. Receipt details and final build identity are in
`receipt.json`.

DSP reset-relative and first-musical-command-relative OPL timing are assessed
separately with a 2 ms tolerance. Absolute startup equality is not established;
the OPL initialization-to-first-note interval also differs by about 21 ms.
The ISA transaction floor is one microsecond; this is not a DOS CPU emulator.
Native replay uses the established Full Game mouse fixture, while the original
scenario uses keyboard selection. This is an audio observation, not complete
input/state/save equivalence or human listening acceptance.

Mode 6 uses PIT IRQ0 and the direct DAC, not DMA. Generic DMA/device IRQs and
other hardware profiles fail explicitly. Full BIOS INT08 chain phase/reentry,
menu/save option cross-owner native ABI views, and long gameplay audio histories
remain unproved. They are not closed by this bounded command comparison.

## Dependency

ymfm: https://github.com/aaronsgiles/ymfm, commit
`81aec25ccbb98f4873a255f7551ac4dadac59b4a`, BSD-3-Clause. License and hashes are
in `portable/audio/ymfm/`. The package builder includes the license for binary
redistribution. The session sandbox cannot install under `C:/tools`, so no
installation there is claimed.

Nuked-OPL3's upstream license is LGPL-2.1. Static linking is possible, but its
distribution terms include relinking arrangements (section 6); it was not
selected. The BSD-3-Clause ymfm subset avoids introducing that dependency.
Primary license references: [Nuked-OPL3](https://github.com/nukeykt/Nuked-OPL3/blob/master/LICENSE),
[ymfm](https://github.com/aaronsgiles/ymfm/blob/81aec25ccbb98f4873a255f7551ac4dadac59b4a/LICENSE).
