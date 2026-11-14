# Independent audio stream findings

The table records the final independent state/frame/audio verdicts. Sound placement is untested from the coverage-ending entry. Raw post-detachment traces remain available, but are not interpreted as covered equivalence.

| Scenario / lane | State | Frames | Audio | First audio entry / layer | Sound coverage ends |
|---|---|---|---|---|---|
| ant-commands/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 598 / DIRECT_DAC_SAMPLE_PRODUCTION | - |
| ant-commands/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 704 / OPL_DSP_ORDERING | - |
| experiment/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| experiment/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| full-game/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_INCOMPLETE | 178 / SOUND_PLACEMENT_OUTSIDE_DOMAIN | 178 |
| full-game/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 618 / DIRECT_DAC_SAMPLE_PRODUCTION | - |
| interactive-play/original | EQUAL 2000/2000 | EQUAL 19/19 | AUDIO_INCOMPLETE | 832 / DIRECT_DAC_SAMPLE_PRODUCTION | 1001 |
| interactive-play/canonical | EQUAL 2000/2000 | EQUAL 19/19 | AUDIO_INCOMPLETE | 678 / SOUND_PLACEMENT_OUTSIDE_DOMAIN | 678 |
| load-from-save/original | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_DIFFERENCE | 992 / OPL_DSP_ORDERING | - |
| load-from-save/canonical | EQUAL 1000/1000 | EQUAL 5/5 | AUDIO_EQUAL | - / NONE | - |
| long-run/original | EQUAL 3000/3000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 2099 / OPL_DSP_ORDERING | - |
| long-run/canonical | EQUAL 3000/3000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 2099 / OPL_DSP_ORDERING | - |
| new-game-save/original | EQUAL 64/64 | EQUAL 2/2 | AUDIO_EQUAL | - / NONE | - |
| new-game-save/canonical | EQUAL 64/64 | EQUAL 2/2 | AUDIO_EQUAL | - / NONE | - |
| quick-game/original | EQUAL 2000/2000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 1760 / OPL_DSP_ORDERING | - |
| quick-game/canonical | EQUAL 2000/2000 | EQUAL 13/13 | AUDIO_DIFFERENCE | 1917 / OPL_DSP_ORDERING | - |
| random-17/original | EQUAL 2000/2000 | EQUAL 9/9 | AUDIO_INCOMPLETE | 1130 / SOUND_RESOURCE_CALL_ORDER_COVERAGE | 1130 |
| random-17/canonical | EQUAL 2000/2000 | EQUAL 9/9 | AUDIO_INCOMPLETE | 1073 / SOUND_RESOURCE_CALL_ORDER_COVERAGE | 1073 |

First OPL/DSP ordering differences are in the unmasked `snd_opl_write_regs` index/data transaction. First DAC sample differences are produced by `sample_timer.asm:out_sb` / `whole_audio_provider.c:interrupt` before ISA/DSP emulation. The five sound-call mismatches are audio coverage findings, never game-state failures. The captured IRQ inside the reaper is outside the tested domain; resource-call evidence is retained without further investigation.

`stream-triage.json` retains first port/value writes, responsible code, trusted-prefix signatures and device substream hashes, full observed signatures and exact capture identities. Its full post-detachment first write may be later than the coverage loss. No raw data or view is reclassified or removed.
