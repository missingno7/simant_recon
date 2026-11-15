#include "audio.h"

#include <SDL3/SDL.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* SDL calls this under the stream lock on its consumer thread. Observe only:
 * canonical device/IRQ work must stay on the game thread and machine timeline.
 * A positive additional request is a conservative stream-underrun count (SDL
 * may slightly overestimate resampling input). It is never hidden by a refill. */
static void SDLCALL observe_consumption(void *context, SDL_AudioStream *stream,
                                       int additional, int total)
{
    PortableSdl3Audio *audio = context;
    (void)stream; (void)total;
    ++audio->requests;
    if (additional > 0) { ++audio->underruns; audio->missing_bytes += additional; }
}

void portable_sdl3_audio_performance(PortableSdl3Audio *audio, FILE *f)
{
    if (audio->stream) SDL_LockAudioStream(audio->stream);
    fprintf(f, "\"audio_block_frames\":%zu,\"audio_queue_calls\":%llu,\"audio_queued_frames\":%llu,\"audio_underruns\":%llu,\"audio_missing_bytes\":%llu,\"audio_requests\":%llu,\"audio_pending_frames\":%zu,\"audio_queue_frames\":%d,",
        audio->block_frames, (unsigned long long)audio->queue_calls,
        (unsigned long long)audio->queued_frames, (unsigned long long)audio->underruns,
        (unsigned long long)audio->missing_bytes, (unsigned long long)audio->requests,
        audio->pending_frames, audio->stream ? SDL_GetAudioStreamQueued(audio->stream)/4 : 0);
    fprintf(f, "\"audio_submission_ns\":%llu,", (unsigned long long)audio->submission_ns);
    if (audio->stream) SDL_UnlockAudioStream(audio->stream);
}

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
    spec.format = SDL_AUDIO_S16;
    spec.channels = 2;
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
    SDL_AudioSpec device;
    int device_frames;
    if (!SDL_GetAudioDeviceFormat(SDL_GetAudioStreamDevice(stream), &device, &device_frames) ||
        device.freq <= 0 || device_frames <= 0) {
        portable_sdl3_audio_close(audio);
        return 0;
    }
    audio->block_frames = ((uint64_t)device_frames * sample_rate + device.freq-1)/device.freq;
    if (!audio->block_frames || audio->block_frames > INT_MAX/4) {
        portable_sdl3_audio_close(audio); return 0;
    }
    audio->pending = calloc(audio->block_frames, 4);
    if (!audio->pending) { portable_sdl3_audio_close(audio); return 0; }
    /* Presentation latency only: four device periods absorb producer/consumer
     * phase and host scheduling jitter. No source IRQ is run into the future.
     * Start consumption with the first complete real block, after startup I/O. */
    for (unsigned i=0; i<4; ++i) {
        if (!SDL_PutAudioStreamData(stream, audio->pending, (int)audio->block_frames*4)) {
            portable_sdl3_audio_close(audio); return 0;
        }
    }
    if (!SDL_SetAudioStreamGetCallback(stream, observe_consumption, audio)) {
        portable_sdl3_audio_close(audio);
        return 0;
    }
    return 1;
}

void portable_sdl3_audio_close(PortableSdl3Audio *audio)
{
    if (audio == NULL) return;
    if (audio->stream != NULL)
        SDL_DestroyAudioStream((SDL_AudioStream *)audio->stream);
    free(audio->pending);
    if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
    memset(audio, 0, sizeof(*audio));
}

int portable_sdl3_audio_queue_frames(PortableSdl3Audio *audio,
                                     const int16_t *pcm, size_t frames)
{
    size_t pcm_size = frames * 2 * sizeof(int16_t);
    if (audio == NULL || audio->stream == NULL ||
        (pcm == NULL && pcm_size != 0) || pcm_size > INT_MAX)
        return 0;
    if (pcm_size == 0) return 1;
    while (frames) {
        size_t count = audio->block_frames - audio->pending_frames;
        if (count > frames) count = frames;
        memcpy(audio->pending + audio->pending_frames*2, pcm, count*4);
        audio->pending_frames += count; pcm += count*2; frames -= count;
        if (audio->pending_frames == audio->block_frames) {
            uint64_t started = SDL_GetTicksNS();
            if (!SDL_PutAudioStreamData(audio->stream, audio->pending, (int)audio->block_frames*4)) return 0;
            audio->submission_ns += SDL_GetTicksNS() - started;
            ++audio->queue_calls; audio->queued_frames += audio->block_frames;
            audio->pending_frames = 0;
            if (!audio->started) {
                if (!SDL_ResumeAudioStreamDevice(audio->stream)) return 0;
                audio->started = 1;
            }
        }
    }
    return 1;
}
