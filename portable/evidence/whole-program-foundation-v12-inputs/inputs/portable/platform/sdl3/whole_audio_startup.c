#include "whole_audio_startup.h"

#include "../../whole_program/platform/audio_native_mode1.h"

#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>

static void attach_source_sequencer(void *context, uint16_t pit_divisor,
                                    uint16_t chain_reload,
                                    int16_t *source_divider,
                                    int16_t (*source_tick)(void))
{
    PortableSdl3WholeAudio *audio = (PortableSdl3WholeAudio *)context;
    portable_sdl3_whole_audio_set_sequencer(audio, source_divider, source_tick);
    if (source_tick != NULL && source_divider != NULL) {
        audio->source_timer_active = 1;
        audio->source_pit_divisor = pit_divisor;
        audio->source_chain_reload = chain_reload;
        if (audio->source_timer_observer != NULL)
            audio->source_timer_observer(audio->source_timer_observer_context,
                                         pit_divisor, chain_reload);
    } else if (audio->source_timer_active != 0) {
        audio->source_timer_active = 0;
        audio->source_pit_divisor = 0;
        audio->source_chain_reload = 0;
        if (audio->source_timer_observer != NULL)
            audio->source_timer_observer(audio->source_timer_observer_context,
                                         0, 0);
    }
}

static uint8_t read_speaker_latch(void *context)
{
    PortableSdl3WholeAudio *audio = (PortableSdl3WholeAudio *)context;
    return audio->provider.speaker_level != 0 ? 0x03u : 0u;
}

static void clear_source_output(void *context, uint8_t value)
{
    PortableSdl3WholeAudio *audio = (PortableSdl3WholeAudio *)context;
    PortableWholeAudioEvent event;
    size_t i;
    if ((value & 0x03u) != 0 || audio == NULL || audio->active == 0 ||
        audio->output.stream == NULL ||
        !SDL_ClearAudioStream((SDL_AudioStream *)audio->output.stream)) {
        fprintf(stderr, "failed to clear native source mode-1 speaker output\n");
        exit(72);
    }
    for (i = 0; i < audio->provider.pending_count; ++i)
        portable_whole_audio_event_free(&audio->provider.pending[i]);
    audio->provider.pending_count = 0;
    while (portable_whole_audio_event_next(audio->events, &event))
        portable_whole_audio_event_free(&event);
    portable_dac_live_scheduler_close(&audio->provider.scheduler);
    portable_dac_live_scheduler_init(&audio->provider.scheduler);
    audio->provider.speaker_level = 0;
}

PortableWholeAudioStartupStatus portable_sdl3_whole_audio_start_source(
    PortableSdl3WholeAudio *audio, int16_t requested_source_mode,
    int16_t (*source_initializer)(int16_t mode, int16_t flag),
    int16_t *active_source_mode)
{
    PortableWholeAudioStartupStatus status;
    if (active_source_mode == NULL || source_initializer == NULL)
        return PORTABLE_WHOLE_AUDIO_STARTUP_INVALID_ARGUMENT;
    if (requested_source_mode != 1)
        return portable_whole_audio_startup_initialize(
            requested_source_mode, audio != NULL && audio->active != 0,
            source_initializer, active_source_mode);
    if (audio == NULL || audio->active == 0)
        return PORTABLE_WHOLE_AUDIO_STARTUP_OUTPUT_UNAVAILABLE;
    if (!portable_sdl3_whole_audio_bind_source_services(audio))
        return PORTABLE_WHOLE_AUDIO_STARTUP_OUTPUT_UNAVAILABLE;
    status = portable_whole_audio_startup_initialize(
        requested_source_mode, 1, source_initializer, active_source_mode);
    if (status != PORTABLE_WHOLE_AUDIO_STARTUP_SELECTED) {
        portable_whole_audio_mode1_unbind();
        return status;
    }
    return status;
}

void portable_sdl3_whole_audio_set_source_timer_observer(
    PortableSdl3WholeAudio *audio, PortableSdl3SourceTimerObserver observer,
    void *context)
{
    if (audio == NULL) return;
    audio->source_timer_observer = observer;
    audio->source_timer_observer_context = context;
    if (observer != NULL && audio->source_timer_active != 0)
        observer(context, audio->source_pit_divisor, audio->source_chain_reload);
}

int portable_sdl3_whole_audio_bind_source_services(
    PortableSdl3WholeAudio *audio)
{
    PortableWholeAudioMode1Host host;
    if (audio == NULL || audio->active == 0) return 0;
    host.attach_sequencer = attach_source_sequencer;
    host.read_speaker_latch = read_speaker_latch;
    host.write_speaker_latch = clear_source_output;
    host.context = audio;
    return portable_whole_audio_mode1_bind(&host);
}

void portable_sdl3_whole_audio_unbind_source_services(void)
{
    portable_whole_audio_mode1_unbind();
}
