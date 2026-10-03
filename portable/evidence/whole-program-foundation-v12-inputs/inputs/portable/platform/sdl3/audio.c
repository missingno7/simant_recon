#include "audio.h"

#include <SDL3/SDL.h>
#include <limits.h>
#include <string.h>

int portable_sdl3_audio_open(PortableSdl3Audio *audio, int sample_rate)
{
    SDL_AudioSpec spec;
    SDL_AudioStream *stream;
    if (audio == NULL || sample_rate <= 0) return 0;
    memset(audio, 0, sizeof(*audio));
    if (!SDL_WasInit(SDL_INIT_AUDIO)) {
        if (!SDL_InitSubSystem(SDL_INIT_AUDIO)) return 0;
        audio->owns_subsystem = 1;
    }
    spec.format = SDL_AUDIO_U8;
    spec.channels = 1;
    spec.freq = sample_rate;
    stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,
                                       &spec, NULL, NULL);
    if (stream == NULL) {
        if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
        memset(audio, 0, sizeof(*audio));
        return 0;
    }
    audio->stream = stream;
    audio->sample_rate = sample_rate;
    if (!SDL_ResumeAudioStreamDevice(stream)) {
        SDL_DestroyAudioStream(stream);
        if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
        memset(audio, 0, sizeof(*audio));
        return 0;
    }
    return 1;
}

void portable_sdl3_audio_close(PortableSdl3Audio *audio)
{
    if (audio == NULL) return;
    if (audio->stream != NULL)
        SDL_DestroyAudioStream((SDL_AudioStream *)audio->stream);
    if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
    memset(audio, 0, sizeof(*audio));
}

int portable_sdl3_audio_queue_u8(PortableSdl3Audio *audio,
                                 const uint8_t *pcm, size_t pcm_size)
{
    if (audio == NULL || audio->stream == NULL ||
        (pcm == NULL && pcm_size != 0) || pcm_size > INT_MAX)
        return 0;
    if (pcm_size == 0) return 1;
    return SDL_PutAudioStreamData((SDL_AudioStream *)audio->stream,
                                  pcm, (int)pcm_size);
}

int portable_sdl3_audio_queued_bytes(const PortableSdl3Audio *audio)
{
    if (audio == NULL || audio->stream == NULL) return 0;
    return SDL_GetAudioStreamQueued((SDL_AudioStream *)audio->stream);
}

int portable_sdl3_audio_done(const PortableSdl3Audio *audio)
{
    if (audio == NULL || audio->stream == NULL) return 0;
    return portable_sdl3_audio_queued_bytes(audio) == 0;
}

const char *portable_sdl3_audio_error(void)
{
    return SDL_GetError();
}
