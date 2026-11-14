# Full-run audio content findings

All 18 lanes complete with 26,128 state entries and 152 checkpoint frames equal.
Audio is **9 AUDIO_EQUAL / 9 AUDIO_DIFFERENCE / 0 AUDIO_INCOMPLETE** under
`audio-content-v1`, with a bound of 16 fast PIT periods (one slow IRQ, 2.87 ms).
Every row compares the whole requested run. Raw OUT order is diagnostic.

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

The three requested first DAC byte differences are independently proved
DOS in-flight heap-relocation reads; see [sample-relocation.md](sample-relocation.md).
Their actual unequal bytes remain differences. Ant canonical at 749 and long-run
original at 2359 have additional same-position byte differences not separately
probed here. The other first placement/progress differences follow the existing
sound-marker scheduling gaps; they are not attributed to a port producer defect.
No larger tick bound or byte exception is used to make these rows equal.

`stream-triage.json` pins each complete content comparison, raw diagnostic,
reference, output and sound-order diagnostic. Normal-play audio is not closed
for all lanes by this result.
