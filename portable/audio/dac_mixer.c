#include "dac_mixer.h"

#include <stdlib.h>

typedef struct DacSourceProfile {
    int16_t sound_id;
    int16_t instrument_id;
    int16_t sample_object_id;
    int16_t note;
    int16_t priority;
    int16_t velocity;
    int16_t tune;
    uint8_t octave;
    uint16_t loop;
    uint8_t looped;
} DacSourceProfile;

/* Anchors: src/data/d55B3_00B8.c SfxNote rows 0,1,2,3,4,55 and DAC
 * instrument rows fd_55B3_0C42[0,1,2,3,4,10]; Sample metadata is from the
 * corresponding s_kick, s_alert1, s_alert2, s_square3, s_beep1, s_burp
 * initializers. This intentionally is not a guessed fallback map.
 */
static const DacSourceProfile source_profiles[] = {
    { 0, 0, 35, 60, 3, 127, -4, 5, 0, 0 },
    { 1, 1,  1, 60, 3, 127,  0, 5, 0, 0 },
    { 2, 2,  2, 60, 3, 127,  0, 5, 0, 0 },
    { 3, 3, 56, 60, 3, 127,  0, 3, 0, 0 },
    { 4, 4,  4, 60, 3, 127,  0, 5, 0, 0 },
    {55,10, 10,100, 4, 127,  0, 5, 0, 0 }
};

static const uint16_t note_steps[12] = {
    0x100, 0x10f, 0x11f, 0x130, 0x142, 0x155,
    0x169, 0x17f, 0x196, 0x1ae, 0x1c8, 0x1e3
};

static int floor_divide_by_eight(int value)
{
    if (value >= 0) return value / 8;
    return -((-value + 7) / 8);
}

static uint8_t volume_table_value(uint8_t row, uint8_t sample)
{
    const int distance = ((int)sample - 0x80) * (8 - row);
    return (uint8_t)(0x80 + floor_divide_by_eight(distance));
}

static PortableDacMixerStatus source_profile(int16_t sound_id,
                                              uint16_t master_volume,
                                              PortableDacSfxProfile *profile)
{
    const DacSourceProfile *source = NULL;
    size_t i;
    int adjusted_note;
    int octave;
    int velocity;
    int source_volume;
    unsigned step;
    if (profile == NULL || master_volume > 0x7f)
        return PORTABLE_DAC_MIXER_INVALID_ARGUMENT;
    for (i = 0; i < sizeof(source_profiles) / sizeof(source_profiles[0]); ++i) {
        if (source_profiles[i].sound_id == sound_id) {
            source = &source_profiles[i];
            break;
        }
    }
    if (source == NULL) return PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE;

    /* m295C: vel=(unsigned)vel*g_7502>>7, in a 16-bit DOS unsigned word. */
    velocity = (int)(((uint16_t)source->velocity * master_volume) >> 7);
    /* Mode 1 initialization sets fd_55B3_74C0 to 0x40 (m277E). */
    source_volume = velocity + 0x40;
    if (source_volume < 0) source_volume = 0;
    if (source_volume > 0x7f) source_volume = 0x7f;

    adjusted_note = source->note + source->tune;
    octave = adjusted_note / 12;
    step = note_steps[adjusted_note % 12];
    if (source->octave < octave)
        step = (uint16_t)(step << (octave - source->octave));
    else
        step >>= (source->octave - octave);

    profile->sound_id = source->sound_id;
    profile->instrument_id = source->instrument_id;
    profile->sample_object_id = source->sample_object_id;
    profile->note = source->note;
    profile->priority = source->priority;
    profile->velocity = source->velocity;
    profile->sample_tune = source->tune;
    profile->sample_octave = source->octave;
    profile->sample_looped = source->looped;
    profile->sample_loop = source->loop;
    profile->step_8_8 = (uint16_t)step;
    profile->volume_row = (uint8_t)((0x7f - source_volume) >> 4);
    profile->source_channels = PORTABLE_DAC_MODE1_CHANNELS;
    return PORTABLE_DAC_MIXER_OK;
}

PortableDacMixerStatus portable_dac_sfx_profile(int16_t sound_id,
                                                uint16_t master_volume,
                                                PortableDacSfxProfile *profile)
{
    return source_profile(sound_id, master_volume, profile);
}

PortableDacMixerStatus portable_dac_render_sfx(PortableDatabase *database,
                                               int16_t sound_id,
                                               uint16_t master_volume,
                                               uint8_t **pcm,
                                               size_t *pcm_size,
                                               PortableDacSfxProfile *profile)
{
    PortableAudioPcmStatus load_status;
    PortableDacMixerStatus status;
    PortableDacSfxProfile local_profile;
    uint8_t *sample_pcm = NULL;
    size_t sample_size = 0;
    uint8_t *output = NULL;
    size_t output_capacity;
    size_t output_count = 0;
    uint16_t position = 0;
    uint8_t fraction = 0;
    uint16_t end;

    if (pcm != NULL) *pcm = NULL;
    if (pcm_size != NULL) *pcm_size = 0;
    if (database == NULL || pcm == NULL || pcm_size == NULL)
        return PORTABLE_DAC_MIXER_INVALID_ARGUMENT;
    status = source_profile(sound_id, master_volume, &local_profile);
    if (status != PORTABLE_DAC_MIXER_OK) return status;
    if (profile != NULL) *profile = local_profile;
    if (local_profile.step_8_8 == 0 || local_profile.sample_looped != 0)
        return PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE;

    load_status = portable_audio_load_sample_pcm(database,
                                                 local_profile.sample_object_id,
                                                 &sample_pcm, &sample_size);
    if (load_status != PORTABLE_AUDIO_PCM_OK || sample_size < 2)
        return PORTABLE_DAC_MIXER_RESOURCE_ERROR;

    end = (uint16_t)(sample_size - 2);
    output_capacity = (((size_t)end + 1) * 256u +
                       local_profile.step_8_8 - 1u) /
                      local_profile.step_8_8 + 1u;
    output = (uint8_t *)malloc(output_capacity ? output_capacity : 1);
    if (output == NULL) {
        portable_audio_free_pcm(sample_pcm);
        return PORTABLE_DAC_MIXER_OUT_OF_MEMORY;
    }

    for (;;) {
        const uint16_t sum = (uint16_t)fraction + local_profile.step_8_8;
        uint8_t mixed_channel = 0x80;
        uint8_t speaker_level;
        fraction = (uint8_t)sum;
        position = (uint16_t)(position + (sum >> 8));
        /* The ISR's over-end branch stops a non-looping channel and jumps
         * straight to out_done. It does not call out_speaker for that tick. */
        if (position > end) break;
        mixed_channel = volume_table_value(local_profile.volume_row,
                                           sample_pcm[position]);
        /* Mode 1 runs two channels: this isolated profile occupies one; the
         * other contributes the source's inactive center value 0x80. */
        speaker_level = (uint8_t)((mixed_channel + 0x80) >> 1);
        output[output_count++] = speaker_level > 0x80 ? 0xff : 0x00;
    }

    portable_audio_free_pcm(sample_pcm);
    *pcm = output;
    *pcm_size = output_count;
    return PORTABLE_DAC_MIXER_OK;
}

void portable_dac_free_pcm(uint8_t *pcm)
{
    free(pcm);
}
