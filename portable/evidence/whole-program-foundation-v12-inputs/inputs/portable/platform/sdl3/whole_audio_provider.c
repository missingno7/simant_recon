#include "whole_audio_provider.h"
#include "../../whole_program/platform/audio_clock.h"

#include <SDL3/SDL.h>
#include <stdlib.h>
#include <string.h>

enum { WHOLE_AUDIO_PUMP_CHUNK = 1024 };

static uint64_t audio_sample_deadline(void *context)
{
    PortableSdl3WholeAudio *audio = (PortableSdl3WholeAudio *)context;
    if (audio->provider.in_render != 0)
        return audio->provider.sample_cursor + 1u;
    uint64_t elapsed_ns = SDL_GetTicksNS() - audio->clock_origin_ns;
    uint64_t elapsed_samples =
        portable_whole_audio_mode1_steps_from_ns(elapsed_ns);
    int queued = portable_sdl3_audio_queued_bytes(&audio->output);
    if (queued > 0) elapsed_samples += (uint64_t)queued;
    return elapsed_samples;
}

void portable_sdl3_whole_audio_set_sequencer(
    PortableSdl3WholeAudio *audio, int16_t *source_divider,
    int16_t (*tick)(void))
{
    if (audio == NULL || audio->active == 0) return;
    portable_whole_audio_provider_set_sequencer(&audio->provider,
                                                source_divider, tick);
}

int portable_sdl3_whole_audio_open(PortableSdl3WholeAudio *audio,
                                   PortableWholeAudioEventQueue *events,
                                   PortableSdl3WholeAudioBackend backend)
{
    if (audio == NULL || events == NULL || backend !=
            PORTABLE_SDL3_WHOLE_AUDIO_MODE1_SAMPLED_DAC ||
        events->initialized == 0)
        return 0;
    memset(audio, 0, sizeof(*audio));
    portable_whole_audio_provider_init(&audio->provider);
    if (!portable_sdl3_audio_open(
            &audio->output,
            PORTABLE_WHOLE_AUDIO_MODE1_PRESENTATION_RATE)) {
        portable_whole_audio_provider_close(&audio->provider);
        return 0;
    }
    audio->events = events;
    audio->clock_origin_ns = SDL_GetTicksNS();
    if (!portable_whole_audio_event_queue_bind_clock(events,
                                                     audio_sample_deadline,
                                                     audio)) {
        portable_sdl3_audio_close(&audio->output);
        portable_whole_audio_provider_close(&audio->provider);
        memset(audio, 0, sizeof(*audio));
        return 0;
    }
    audio->active = 1;
    return 1;
}

void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *audio)
{
    if (audio == NULL) return;
    if (audio->events != NULL)
        portable_whole_audio_event_queue_unbind(audio->events);
    portable_sdl3_audio_close(&audio->output);
    portable_whole_audio_provider_close(&audio->provider);
    memset(audio, 0, sizeof(*audio));
}

PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(
    PortableSdl3WholeAudio *audio, size_t target_queued_frames)
{
    uint8_t samples[WHOLE_AUDIO_PUMP_CHUNK];
    if (audio == NULL || audio->active == 0 || audio->events == NULL ||
        target_queued_frames >
            10u * PORTABLE_WHOLE_AUDIO_MODE1_PRESENTATION_RATE)
        return PORTABLE_SDL3_WHOLE_AUDIO_INVALID_ARGUMENT;
    while ((size_t)portable_sdl3_audio_queued_bytes(&audio->output) <
           target_queued_frames) {
        size_t queued = (size_t)portable_sdl3_audio_queued_bytes(&audio->output);
        size_t count = target_queued_frames - queued;
        if (count > sizeof(samples)) count = sizeof(samples);
        if (portable_whole_audio_provider_render(&audio->provider, audio->events,
                                                 samples, count) !=
            PORTABLE_WHOLE_AUDIO_PROVIDER_OK)
            return PORTABLE_SDL3_WHOLE_AUDIO_PROVIDER_ERROR;
        if (!portable_sdl3_audio_queue_u8(&audio->output, samples, count))
            return PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR;
    }
    return PORTABLE_SDL3_WHOLE_AUDIO_OK;
}
