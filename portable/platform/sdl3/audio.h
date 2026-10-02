#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H

#include <stddef.h>
#include <stdint.h>

typedef struct PortableSdl3Audio {
    void *stream; /* SDL_AudioStream, kept opaque outside the platform layer. */
    int sample_rate;
    int owns_subsystem;
} PortableSdl3Audio;

/* Open a mono unsigned-8-bit stream. `sample_rate` is the decoded stream rate;
 * the DOS sample table does not establish one portable hardware rate. */
int portable_sdl3_audio_open(PortableSdl3Audio *audio, int sample_rate);
void portable_sdl3_audio_close(PortableSdl3Audio *audio);
int portable_sdl3_audio_queue_u8(PortableSdl3Audio *audio,
                                 const uint8_t *pcm, size_t pcm_size);
int portable_sdl3_audio_queued_bytes(const PortableSdl3Audio *audio);
int portable_sdl3_audio_done(const PortableSdl3Audio *audio);
const char *portable_sdl3_audio_error(void);

#endif
