# Whole-program sampled audio boundary

The mechanical `m290D` conversion emits ordered `SAMPLE_START` and
`SAMPLE_STOP` records only after the source DAC channel state is committed.
Each start owns a copy of the decoded sample bytes, so the original Sample
handle may be released after the callback. The event keeps the source channel,
length, loop offset, 8.8 step, volume-table row, and loop flag.

The SDL3 provider is selected explicitly as `MODE1_SAMPLED_DAC`. Its clock
reader returns a monotonic output-sample index at 11932 Hz. Outside a render
callback, it converts elapsed SDL nanoseconds to PIT samples and adds the
already-queued stream frames; this maps new source calls to the output queue's
tail. Events are committed at their captured frame, in sequence order. During
the source sequencer callback, the current provider cursor is used, so notes
produced inside a rendered block begin on the next sample boundary.

Pass the generated original `f_284A_067F` function and the address of the
generated `fd_55B3_6B42` word to
`portable_sdl3_whole_audio_set_sequencer`. The source m28BC ISR decrements
that actual word on each eligible PIT sample and reloads it from the
function's low 16-bit return value. The DOS initializer's `2` is later
overwritten to `5` by `f_284A_0013`, so the host reads the source word instead
of inventing an initial delay. This runs original MIDI sequencing and routes
its sampled-instrument channel starts/stops through the same source event sink.
The caller must bind the callback only after generated module state and song
services are initialized, and must continue pumping the SDL provider while the
game runs.

This provider renders the original two-channel sampled-DAC mixer path. BIOS
device probes, PC speaker/ISA port effects, type-2 FM/OPL voices, other hardware
families, and MIDI device output remain unsupported. The PIT rate is the
source's integer divisor-100 rate; SDL may resample it to the physical device.
No claim is made about matching a particular PC speaker or analog audio output.
