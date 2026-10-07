# Audio device boundary controls

Run `python portable/tests/audio/run.py`. The fixture provides test-owned stand-ins
for canonical externs and executes the production ISR projection and device sink.
It does not supply original executable bytes or an alternate game sequencer.

Grounding: `src/root/m28BC.asm` L00C5/out_done/L00DE/L0148/ISR0354/out_sb;
`src/root/m283E.asm` register/data writes; canonical `m29B8.c` DSP reset handshake.
Controls cover the /16 song divider, slow idle PIT cadence, one pending IRQ while
IF is clear, over-end skipped OUT and clearing the canonical `snd` field, DSP
unsigned DAC magnitude/mute/reset and scheduled writes, OPL timer/key-on/key-off,
and explicit failure of an unsupported DMA command. Tests use a sustained FM
envelope for the tone control and key-off as its negative contrast.

Canonical volume tables are emitted from m28BC's symbolic directives, not from a
linear approximation. The fixture's identity table isolates channel/mixer math.
The complete native build compiles the actual generated 2,048 source table bytes.

Set `SIMANT_AUDIO_TRACE` to an existing directory before running the native
executable. `io-sb_dsp` and `io-opl` contain `<virtual-ms> out <port> 1 <value>`;
they are observations only. Times use monotonic transport time and exact rational
PIT IRQ deadlines, with a one-microsecond ISA transaction floor. This is not a DOS
CPU emulator. Compare absolute startup and musical-command-relative times separately.

Supported audio profile: CFG Sound Mode 6 (or explicit `/s6`), OPL3 in OPL2
compatibility mode and the SB direct 8-bit DAC. `/s0` is silent. The current source
mode 6 uses PIT IRQ0 and DSP command 10h, not DMA. DMA and other audio profiles fail
explicitly. Raw saved/menu option aliases and complete native BIOS timer chaining
remain outside these controls; see `portable/platform.json`.
