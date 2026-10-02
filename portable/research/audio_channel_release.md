# Channel note-release dispatch contract

This is a focused source and executable contract for `f_295C_02E8`, which is called by `f_295C_0391` during song stop. The earlier first-pass channel packet remains preserved at [channel-release-v1.json](../tests/audio/channel_release/evidence/channel-release-v1.json). The deeper run is [channel-backend-v3.json](../tests/audio/channel_release/evidence/channel-backend-v3.json), produced by [run_backend_closure.py](../tests/audio/channel_release/run_backend_closure.py) and cross-checked against the readable native contract [channel_backend_contract.c](../tests/audio/channel_release/channel_backend_contract.c). This remains diagnostic evidence, not an acceptance registration.

## Source-derived domain

`src/data/d55B3_00B8.c` defines 56 sound-note descriptors in `fd_55B3_0A82`. Their `.sound` field addresses instrument/device rows 0 through 54; the last note descriptor maps back to row 10. Its note values are 60 and 100. The instrument maps provide valid active examples for every dispatcher kind:

| Driver kind | Active instrument map example | Device row | Output-channel setup |
| --- | --- | ---: | --- |
| 1 DAC | `fd_55B3_0C42` | 0, 10 | type 1, channel 0/1 |
| 2 FM | `fd_55B3_0D92` | 0 | type 2, channel 0/1 |
| 3 PSG3 | `fd_55B3_16C2` | 3 | type 3, channel 0/1 |
| 4 PSG4 | `fd_55B3_1572` | 3 | type 4, channel 0/1 |
| 5 PSG5 | `fd_55B3_1032` | 3 | type 5, channel 0/1 |
| 6 MIDI melodic | `fd_55B3_12D2` / `fd_55B3_1422` | 0 | type 6, channel 1/2 |
| 7 MIDI drum | `fd_55B3_12D2` / `fd_55B3_1422` | 12 | type 7, channel 10 |

The output-channel type and number examples follow the channel-construction loops in `src/root/m277E.c`; instrument rows and MIDI map arguments come from `src/data/d55B3_00B8.c`. The tests use two matching channel records plus nonmatching device/note records and a zero-type sentinel. Both matching records are deliberately released in ascending table order.

## Function behavior and dispatch

The exact source body of `f_295C_02E8(dev,note)` scans `fd_50F6_4A4E[]` to the first zero type. It matches only when the unsigned-byte `c4` note equals the input word and unsigned-byte `c3` device equals the input word; `c2` does not participate in this function's predicate. For each match, it dispatches through `g_7524[fd_50F6_0000[dev].count]`, passing `(note, channel.num, dev)`. It then stores `c4=0`, `c2=0`, and `c5=15`. The type, channel number, and device byte remain unchanged. The second call with the same nonzero note produces no extra dispatch because the matched note bytes were cleared.

`g_7524` maps kinds 1 through 7 to these real source bodies: `f_290D_026C`, `f_2815_024D`, `f_29D6_0148`, `f_29D6_015D`, `f_29D6_0197`, `f_295C_04FB`, and `f_295C_053D`. The run executes those bodies and records their actual I/O effects. For kind 1, it also runs `f_290D_026C`'s channel-owner cleanup and real `f_0000_0149` freelist append. The independent C contract predicts the resulting channel state, queued-sample count, and ordered hardware writes.

The DOS and exact MSC600AX candidate agree on all ten cases. They include kinds 1 through 7, note 100 on sound row 10, and three PCM-owner states: loaded 1, loaded 2, and null owner. Loaded-1 owned PCM voices append their sample pointer twice to the real delayed freelist when both matching channel rows refer to it, and clear both `snd` and `owner`; loaded-2 and null-owner variants clear channel pointers without enqueuing. Each kind's final channel bytes match the native contract. A repeat call with the same nonzero note produces no additional hardware writes or freelist entries. All machine output writes agree in port, width, value, and order. The exact candidate strict gate passed for this whole-module translation unit.

## Hardware boundary and port requirements

The proof provider makes only the source-required hardware readiness/readback observations deterministic: OPL status reads return zero, MIDI-ready status reads return zero with the MIDI data read returning `0xFE`, and the 29BF register readback returns the most recent byte written to its data port. The run still executes the real waiting helpers and the assembly-backed YM3812 and 29BF access routines, capturing each output operation. This does not establish physical timing, real device acknowledgement/failure behavior, or actual sound generation.

A portable implementation needs the same semantic dispatch and cleanup ordering, with explicit typed backend operations:

- stop a PCM voice and release its owner only when its loaded state is 1, then clear both PCM channel pointers;
- silence FM voice registers in source order;
- preserve PSG3's note-derived three-write sequence and PSG4/PSG5 register writes;
- send MIDI melodic note-off as command `0xD7`, channel status `0x80 + channel`, transposed note, then zero;
- send MIDI drum note-off as command `0xD7`, status `0x89`, mapped program, then zero;
- after each matched backend returns, clear channel `c4` and `c2`, and set `c5` to 15.

The receipt pins the DOS oracle, whole-module candidate, source/data closure, MSC and GCC tool files, Unicorn evaluator, Python runtime, native contract source, and before/after hashes. It is suitable as integration guidance and a repeatable dispatch regression. It does not prove full music lifecycle behavior, resource lifetime beyond the PCM freelist boundary, device timing, or a complete hardware-driver port.
