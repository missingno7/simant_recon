#include "audio_voice_scheduler.h"

#include <stdlib.h>
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

static void release_voice(PortableDacLiveScheduler *scheduler, size_t index)
{
    PortableDacLiveVoice *voice = &scheduler->voices[index];
    portable_dac_free_pcm(voice->pcm);
    memset(voice, 0, sizeof(*voice));
    scheduler->allocator.channels[index].active = 0;
    scheduler->allocator.channels[index].owner_loaded = 0;
    scheduler->allocator.channels[index].sound_id = -1;
    scheduler->allocator.channels[index].sample_object_id = -1;
}

void portable_dac_live_scheduler_init(PortableDacLiveScheduler *scheduler)
{
    if (scheduler == NULL) return;
    memset(scheduler, 0, sizeof(*scheduler));
    portable_dac_voice_allocator_init(&scheduler->allocator);
}

void portable_dac_live_scheduler_close(PortableDacLiveScheduler *scheduler)
{
    size_t i;
    if (scheduler == NULL) return;
    for (i = 0; i < PORTABLE_DAC_VOICE_CHANNEL_COUNT; ++i)
        portable_dac_free_pcm(scheduler->voices[i].pcm);
    memset(scheduler, 0, sizeof(*scheduler));
}

PortableDacSchedulerStatus portable_dac_live_scheduler_start(
    PortableDatabase *database, PortableDacLiveScheduler *scheduler,
    const PortableDacVoiceRequest *request, uint16_t master_volume,
    PortableDacLiveStart *start)
{
    PortableDacSfxProfile profile;
    PortableDacMixerStatus profile_status;
    PortableAudioPcmStatus pcm_status;
    PortableDacVoiceDecision admission;
    uint8_t *pcm = NULL;
    size_t pcm_size = 0;
    size_t i;
    int16_t selected;
    if (start != NULL) {
        memset(start, 0, sizeof(*start));
        start->started_channel = -1;
        start->stopped_channel = -1;
        start->admission.selected_channel = -1;
    }
    if (database == NULL || scheduler == NULL || request == NULL || start == NULL ||
        master_volume > 0x7f)
        return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;

    /* Validate the exact source table profile before aging channels. */
    profile_status = portable_dac_sfx_profile(request->sound_id, master_volume,
                                              &profile);
    if (profile_status == PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE)
        return PORTABLE_DAC_SCHEDULER_UNSUPPORTED_PROFILE;
    if (profile_status != PORTABLE_DAC_MIXER_OK ||
        profile.instrument_id != request->instrument_id ||
        profile.sample_object_id != request->sample_object_id ||
        profile.note != request->note || profile.priority != request->priority ||
        profile.velocity != request->velocity)
        return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;

    admission = portable_dac_voice_admit_request(&scheduler->allocator, request);
    start->admission = admission;
    for (i = 0; i < admission.release_count; ++i)
        release_voice(scheduler,
                      (size_t)admission.released_owner_channels[i]);
    selected = admission.selected_channel;
    if (selected < 0) return PORTABLE_DAC_SCHEDULER_OK;

    /* f_295C_01EC unconditionally calls its channel stop operation before
     * the corresponding start function, including when the channel is idle. */
    start->stopped_channel = selected;
    release_voice(scheduler, (size_t)selected);
    pcm_status = portable_audio_load_sample_pcm(database,
                                                profile.sample_object_id,
                                                &pcm, &pcm_size);
    if (pcm_status == PORTABLE_AUDIO_PCM_OUT_OF_MEMORY)
        return PORTABLE_DAC_SCHEDULER_OUT_OF_MEMORY;
    if (pcm_status != PORTABLE_AUDIO_PCM_OK)
        return PORTABLE_DAC_SCHEDULER_RESOURCE_ERROR;
    if (pcm_size < 2 || pcm_size > UINT16_MAX) {
        portable_audio_free_pcm(pcm);
        return PORTABLE_DAC_SCHEDULER_RESOURCE_ERROR;
    }

    scheduler->voices[selected].pcm = pcm;
    scheduler->voices[selected].pcm_size = pcm_size;
    scheduler->voices[selected].end = (uint16_t)(pcm_size - 2);
    scheduler->voices[selected].loop_start =
        (uint16_t)(profile.sample_loop + 2u);
    scheduler->voices[selected].step_8_8 = profile.step_8_8;
    scheduler->voices[selected].volume_row = profile.volume_row;
    scheduler->voices[selected].looped = profile.sample_looped;
    if (!portable_dac_voice_commit_request(&scheduler->allocator, selected,
                                           request)) {
        release_voice(scheduler, (size_t)selected);
        return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;
    }
    start->started_channel = selected;
    return PORTABLE_DAC_SCHEDULER_OK;
}

PortableDacSchedulerStatus portable_dac_live_scheduler_tick(
    PortableDacLiveScheduler *scheduler, PortableDacLiveTick *tick)
{
    uint8_t channel_value[PORTABLE_DAC_VOICE_CHANNEL_COUNT] = { 0x80, 0x80 };
    size_t i;
    if (tick != NULL) memset(tick, 0, sizeof(*tick));
    if (scheduler == NULL || tick == NULL)
        return PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT;

    for (i = 0; i < PORTABLE_DAC_VOICE_CHANNEL_COUNT; ++i) {
        PortableDacLiveVoice *voice = &scheduler->voices[i];
        uint16_t sum;
        uint16_t advance;
        if (voice->pcm == NULL || scheduler->allocator.channels[i].active == 0)
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
                scheduler->allocator.channels[i].active = 0;
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
