#include "audio_mixer_service.h"

#include <string.h>

static int floor_divide_by_eight(int value)
{
    if (value >= 0) return value / 8;
    return -((-value + 7) / 8);
}

static uint8_t volume_table_value(uint8_t row, uint8_t sample)
{
    const int scaled = ((int)sample - 0x80) * (8 - row);
    return (uint8_t)(0x80 + floor_divide_by_eight(scaled));
}

void portable_dac_live_scheduler_init(PortableDacLiveScheduler *scheduler)
{
    if (scheduler == NULL) return;
    memset(scheduler, 0, sizeof(*scheduler));
}

void portable_dac_live_scheduler_close(PortableDacLiveScheduler *scheduler)
{
    size_t i;
    if (scheduler == NULL) return;
    for (i = 0; i < PORTABLE_DAC_MODE1_CHANNELS; ++i)
        portable_dac_free_pcm(scheduler->voices[i].pcm);
    memset(scheduler, 0, sizeof(*scheduler));
}

PortableDacSchedulerStatus portable_dac_live_scheduler_tick(
    PortableDacLiveScheduler *scheduler, PortableDacLiveTick *tick)
{
    uint8_t channel_value[PORTABLE_DAC_MODE1_CHANNELS] = { 0x80, 0x80 };
    size_t i;
    if (tick != NULL) memset(tick, 0, sizeof(*tick));
    if (scheduler == NULL || tick == NULL)
        return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;

    for (i = 0; i < PORTABLE_DAC_MODE1_CHANNELS; ++i) {
        PortableDacLiveVoice *voice = &scheduler->voices[i];
        uint16_t sum;
        uint16_t advance;
        if (voice->pcm == NULL || voice->active == 0)
            continue;
        if (voice->step_8_8 == 0) return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;
        sum = (uint16_t)((uint16_t)voice->fraction + voice->step_8_8);
        voice->fraction = (uint8_t)sum;
        advance = (uint16_t)(sum >> 8);
        voice->position = (uint16_t)(voice->position + advance);
        if (voice->position > voice->end) {
            if (voice->looped != 0) {
                voice->position = voice->loop_start;
            } else {
                voice->active = 0;
            }
            /* m28BC.asm L00C5 skips the whole mix/output for this PIT tick. */
            return PORTABLE_DAC_SCHEDULER_OK;
        }
        channel_value[i] = volume_table_value(voice->volume_row,
                                              voice->pcm[voice->position]);
    }

    tick->output_generated = 1;
    tick->mixed_register = (uint8_t)(((unsigned)channel_value[0] +
                                      (unsigned)channel_value[1]) >> 1);
    scheduler->speaker_enabled = tick->mixed_register > 0x80;
    tick->speaker_enabled = scheduler->speaker_enabled;
    return PORTABLE_DAC_SCHEDULER_OK;
}
