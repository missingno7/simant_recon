#ifndef SIMANT_PORTABLE_AUDIO_DAC_MIXER_H
#define SIMANT_PORTABLE_AUDIO_DAC_MIXER_H

#include "intent.h"

enum {
    /* Source m28BC programs PIT channel 0 with divisor 0x64 for this mode. */
    PORTABLE_DAC_MODE1_PIT_DIVISOR = 0x64,
    PORTABLE_DAC_MODE1_SAMPLE_RATE = 11932,
    PORTABLE_DAC_MODE1_CHANNELS = 2
};

typedef enum PortableDacMixerStatus {
    PORTABLE_DAC_MIXER_OK = 0,
    PORTABLE_DAC_MIXER_INVALID_ARGUMENT,
    PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE,
    PORTABLE_DAC_MIXER_RESOURCE_ERROR,
    PORTABLE_DAC_MIXER_OUT_OF_MEMORY
} PortableDacMixerStatus;

typedef struct PortableDacSfxProfile {
    int16_t sound_id;
    int16_t instrument_id;
    int16_t sample_object_id;
    int16_t note;
    int16_t priority;
    int16_t velocity;
    int16_t sample_tune;
    uint8_t sample_octave;
    uint8_t sample_looped;
    uint16_t sample_loop;
    uint16_t step_8_8;
    uint8_t volume_row;
    uint8_t source_channels;
} PortableDacSfxProfile;

/* Bounded exact source table profiles: SFX IDs 0,1,2,3,4,55 through the
 * DOS DAC mode-1 instrument map. master_volume is the source g_7502 value;
 * no default volume is inferred here.
 */
PortableDacMixerStatus portable_dac_sfx_profile(int16_t sound_id,
                                                uint16_t master_volume,
                                                PortableDacSfxProfile *profile);

/* Render one isolated, non-looping mode-1 DAC SFX through the source 8.8
 * channel step, volume table, two-channel average, and PC-speaker threshold.
 * Output is U8 logic level (0/255), one byte per original PIT tick.
 */
PortableDacMixerStatus portable_dac_render_sfx(PortableDatabase *database,
                                              int16_t sound_id,
                                              uint16_t master_volume,
                                              uint8_t **pcm,
                                              size_t *pcm_size,
                                              PortableDacSfxProfile *profile);
void portable_dac_free_pcm(uint8_t *pcm);

#endif
