#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct PortableSdl3Audio {
    void *stream; /* SDL_AudioStream, kept opaque outside the platform layer. */
    int sample_rate;
    int owns_subsystem;
    size_t block_frames, pending_frames;
    int16_t *pending;
    int started;
    uint64_t queue_calls, queued_frames, underruns, missing_bytes, requests;
    uint64_t submission_ns;
    /* Optional read-only queue/event observations; allocated only on request. */
    void *observation;
    uint64_t source_frame, stream_tail, stream_epoch;
    int16_t *recent;
    size_t recent_cursor, recent_frames;
    uint64_t recent_end;
    int timeline, gated, gate_ready, gate_reason;
    uint64_t gate_wall, gate_frame, service_wall;
    uint64_t resets, overflow_resets, stall_restarts, discarded_frames, gated_frames;
    uint64_t queue_peak_frames, start_delay_ns, opened_ns;
} PortableSdl3Audio;

/* Device mix: signed 16-bit stereo at the presentation sample rate. */
int portable_sdl3_audio_open(PortableSdl3Audio *audio, int sample_rate);
void portable_sdl3_audio_close(PortableSdl3Audio *audio);
int portable_sdl3_audio_queue_frames(PortableSdl3Audio *audio,
                                    const int16_t *pcm, size_t frames);
void portable_sdl3_audio_performance(PortableSdl3Audio *audio, FILE *file);
int portable_sdl3_audio_queue_at(PortableSdl3Audio *,const int16_t *,size_t,uint64_t);
void portable_sdl3_audio_trigger(PortableSdl3Audio *,uint64_t,unsigned,unsigned,unsigned);
void portable_sdl3_audio_observe(PortableSdl3Audio *,uint64_t);
int portable_sdl3_audio_begin(PortableSdl3Audio *,uint64_t source_frame);
int portable_sdl3_audio_service(PortableSdl3Audio *);

#endif
