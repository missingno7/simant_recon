#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_NATIVE_MODE1_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_NATIVE_MODE1_H

#include <stdint.h>

typedef void (*PortableWholeAudioSequencerAttach)(
    void *context, uint16_t pit_divisor, uint16_t chain_reload,
    int16_t *source_divider, int16_t (*source_tick)(void));
typedef uint8_t (*PortableWholeAudioSpeakerLatchRead)(void *context);
typedef void (*PortableWholeAudioSpeakerLatchWrite)(void *context,
                                                    uint8_t value);

typedef struct PortableWholeAudioMode1Host {
    PortableWholeAudioSequencerAttach attach_sequencer;
    PortableWholeAudioSpeakerLatchRead read_speaker_latch;
    PortableWholeAudioSpeakerLatchWrite write_speaker_latch;
    void *context;
} PortableWholeAudioMode1Host;

/* Bind an already-open native sampled-DAC output before calling the original
 * f_277E_0000(1, 0). The original m28BC timer request then attaches its actual
 * f_284A_067F sequencer to that output. A source stop with divisor zero is
 * valid before setup/arming and is idempotent; stopping an armed timer detaches
 * the sequencer but retains this host binding for a later sound reconfiguration.
 * There is no DOS timer, IRQ, BIOS, or ISA device emulation in this boundary.
 */
int portable_whole_audio_mode1_bind(const PortableWholeAudioMode1Host *host);
void portable_whole_audio_mode1_unbind(void);
int portable_whole_audio_mode1_timer_armed(void);
unsigned portable_whole_audio_mode1_timer_start_count(void);
int portable_whole_audio_mode1_timer_configuration(int16_t *pit_divisor,
                                                   int16_t *sequencer_reload);

/* Native replacements for the source m28BC timer entries. */
void f_28BC_0488(int16_t pit_divisor, int16_t sequencer_reload);
void f_28BC_03CC(void);
void f_28BC_046B(int16_t pit_divisor, int16_t sequencer_reload);
void f_28BC_04E0(int16_t divisor);

/* Explicitly unsupported legacy hardware leaves, provided so a full source
 * link fails closed if an unselected device path is ever called. */
void f_283E_000A(uint8_t reg, uint8_t value);
void f_283E_0035(void);
void f_29BF_0008(int16_t base_port);
int16_t f_29BF_0139(void);
void f_29BF_00E6(int16_t reg, int16_t value);

#endif
