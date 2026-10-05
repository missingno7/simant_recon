#include "whole_audio_provider.h"

#include <stdlib.h>
#include <string.h>

void portable_whole_audio_provider_init(PortableWholeAudioProvider *provider)
{
    if (provider == NULL) return;
    memset(provider, 0, sizeof(*provider));
    portable_dac_live_scheduler_init(&provider->scheduler);
}

void portable_whole_audio_provider_close(PortableWholeAudioProvider *provider)
{
    size_t i;
    if (provider == NULL) return;
    for (i = 0; i < provider->pending_count; ++i)
        portable_whole_audio_event_free(&provider->pending[i]);
    portable_dac_live_scheduler_close(&provider->scheduler);
    memset(provider, 0, sizeof(*provider));
}

void portable_whole_audio_provider_set_sequencer(
    PortableWholeAudioProvider *provider, int16_t *source_divider,
    int16_t (*tick)(void))
{
    if (provider == NULL) return;
    provider->sequencer_tick = tick;
    provider->sequencer_divider = tick != NULL ? source_divider : NULL;
}

PortableWholeAudioProviderStatus portable_whole_audio_provider_apply(
    PortableWholeAudioProvider *provider, PortableWholeAudioEvent *event)
{
    PortableDacLiveVoice *voice;
    unsigned index;
    if (provider == NULL || event == NULL)
        return PORTABLE_WHOLE_AUDIO_PROVIDER_INVALID_ARGUMENT;
    if (provider->has_sequence != 0 && event->sequence <= provider->last_sequence)
        return PORTABLE_WHOLE_AUDIO_PROVIDER_BAD_EVENT_ORDER;
    if (event->channel >= PORTABLE_WHOLE_AUDIO_DAC_CHANNELS)
        return PORTABLE_WHOLE_AUDIO_PROVIDER_INVALID_ARGUMENT;
    index = event->channel;
    voice = &provider->scheduler.voices[index];

    if (event->kind == PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_STOP) {
        portable_dac_free_pcm(voice->pcm);
        memset(voice, 0, sizeof(*voice));
    } else if (event->kind == PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_START) {
        if (event->sample_pcm == NULL || event->sample_size < 2 ||
            event->step_8_8 == 0 || event->volume_row > 7 ||
            event->looped > 1 || event->sample_loop > UINT16_MAX - 2u ||
            (event->looped != 0 && event->sample_loop + 2u >= event->sample_size))
            return PORTABLE_WHOLE_AUDIO_PROVIDER_RESOURCE_ERROR;

        /* Source f_295C_01EC stops the selected channel before starting a new
         * sample there. The event already records that selected source slot.
         */
        portable_dac_free_pcm(voice->pcm);
        memset(voice, 0, sizeof(*voice));
        voice->pcm = event->sample_pcm;
        event->sample_pcm = NULL;
        voice->pcm_size = event->sample_size;
        voice->end = (uint16_t)(event->sample_size - 2u);
        voice->loop_start = (uint16_t)(event->sample_loop + 2u);
        voice->step_8_8 = event->step_8_8;
        voice->volume_row = event->volume_row;
        voice->looped = event->looped;
        voice->active = 1;
    } else {
        return PORTABLE_WHOLE_AUDIO_PROVIDER_UNSUPPORTED_EVENT;
    }
    provider->last_sequence = event->sequence;
    provider->has_sequence = 1;
    portable_whole_audio_event_free(event);
    return PORTABLE_WHOLE_AUDIO_PROVIDER_OK;
}

static PortableWholeAudioProviderStatus collect_events(
    PortableWholeAudioProvider *provider, PortableWholeAudioEventQueue *queue)
{
    PortableWholeAudioEvent event;
    uint64_t prior_deadline = 0;
    size_t i;
    if (provider->pending_count != 0 &&
        provider->pending[provider->pending_count - 1].timestamped != 0)
        prior_deadline = provider->pending[provider->pending_count - 1].sample_deadline;
    while (provider->pending_count < PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY &&
           portable_whole_audio_event_next(queue, &event)) {
        if (event.timestamped != 0) {
            if (provider->pending_count != 0 &&
                provider->pending[provider->pending_count - 1].timestamped != 0 &&
                event.sample_deadline < prior_deadline) {
                portable_whole_audio_event_free(&event);
                return PORTABLE_WHOLE_AUDIO_PROVIDER_BAD_EVENT_ORDER;
            }
            prior_deadline = event.sample_deadline;
        }
        provider->pending[provider->pending_count++] = event;
    }
    for (i = 1; i < provider->pending_count; ++i) {
        if (provider->pending[i - 1].sequence >= provider->pending[i].sequence)
            return PORTABLE_WHOLE_AUDIO_PROVIDER_BAD_EVENT_ORDER;
    }
    return PORTABLE_WHOLE_AUDIO_PROVIDER_OK;
}

PortableWholeAudioProviderStatus portable_whole_audio_provider_render(
    PortableWholeAudioProvider *provider, PortableWholeAudioEventQueue *queue,
    uint8_t *samples, size_t count)
{
    PortableWholeAudioProviderStatus status;
    size_t frame;
    if (provider == NULL || queue == NULL || (samples == NULL && count != 0))
        return PORTABLE_WHOLE_AUDIO_PROVIDER_INVALID_ARGUMENT;
    status = collect_events(provider, queue);
    if (status != PORTABLE_WHOLE_AUDIO_PROVIDER_OK) return status;
    provider->in_render = 1;
    for (frame = 0; frame < count; ++frame) {
        while (provider->pending_count != 0) {
            PortableWholeAudioEvent *event = &provider->pending[0];
            if (event->timestamped != 0 &&
                event->sample_deadline > provider->sample_cursor)
                break;
            status = portable_whole_audio_provider_apply(provider, event);
            if (status != PORTABLE_WHOLE_AUDIO_PROVIDER_OK) {
                provider->in_render = 0;
                return status;
            }
            if (provider->pending_count > 1)
                memmove(provider->pending, provider->pending + 1,
                        (provider->pending_count - 1) * sizeof(provider->pending[0]));
            --provider->pending_count;
            memset(&provider->pending[provider->pending_count], 0,
                   sizeof(provider->pending[0]));
        }
        status = portable_whole_audio_provider_render_tick(provider, &samples[frame]);
        if (status != PORTABLE_WHOLE_AUDIO_PROVIDER_OK) {
            provider->in_render = 0;
            return status;
        }
        /* The original sequencer callback can enqueue a note from this very
         * PIT frame. Capture it now so it commits at the following boundary,
         * rather than waiting for another host pump and losing timing.
         */
        status = collect_events(provider, queue);
        if (status != PORTABLE_WHOLE_AUDIO_PROVIDER_OK) {
            provider->in_render = 0;
            return status;
        }
        ++provider->sample_cursor;
    }
    provider->in_render = 0;
    return PORTABLE_WHOLE_AUDIO_PROVIDER_OK;
}

PortableWholeAudioProviderStatus portable_whole_audio_provider_render_tick(
    PortableWholeAudioProvider *provider, uint8_t *sample)
{
    PortableDacLiveTick tick;
    PortableDacSchedulerStatus status;
    if (provider == NULL || sample == NULL)
        return PORTABLE_WHOLE_AUDIO_PROVIDER_INVALID_ARGUMENT;
    status = portable_dac_live_scheduler_tick(&provider->scheduler, &tick);
    if (status != PORTABLE_DAC_SCHEDULER_OK)
        return PORTABLE_WHOLE_AUDIO_PROVIDER_RESOURCE_ERROR;
    if (tick.output_generated != 0)
        provider->speaker_level = tick.speaker_enabled != 0 ? 0xff : 0x00;
    *sample = provider->speaker_level;
    if (tick.output_generated != 0 && provider->sequencer_tick != NULL &&
        provider->sequencer_divider != NULL) {
        uint16_t countdown = (uint16_t)*provider->sequencer_divider;
        countdown = (uint16_t)(countdown - 1u);
        memcpy(provider->sequencer_divider, &countdown, sizeof(countdown));
        if (countdown == 0) {
            int16_t delay = provider->sequencer_tick();
            memcpy(provider->sequencer_divider, &delay, sizeof(delay));
        }
    }
    return PORTABLE_WHOLE_AUDIO_PROVIDER_OK;
}
