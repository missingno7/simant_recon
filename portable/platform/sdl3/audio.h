#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H

#include <stddef.h>
#include <stdint.h>

typedef struct PortableSdl3Audio {
    void *stream; /* SDL_AudioStream, kept opaque outside the platform layer. */
    int sample_rate;
    int owns_subsystem;
} PortableSdl3Audio;

/* Device mix: signed 16-bit stereo at the presentation sample rate. */
int portable_sdl3_audio_open(PortableSdl3Audio *audio, int sample_rate);
void portable_sdl3_audio_close(PortableSdl3Audio *audio);
int portable_sdl3_audio_queue_frames(PortableSdl3Audio *audio,
                                    const int16_t *pcm, size_t frames);

#endif
