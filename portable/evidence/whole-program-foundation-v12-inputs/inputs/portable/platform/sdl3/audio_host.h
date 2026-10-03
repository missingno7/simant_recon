#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_HOST_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_AUDIO_HOST_H

#include "audio.h"
#include "../../audio/intent.h"
#include "../../audio/dac_mixer.h"

typedef enum PortableSdl3AudioHostStatus {
    PORTABLE_SDL3_AUDIO_HOST_OK = 0,
    PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT,
    PORTABLE_SDL3_AUDIO_HOST_SDL_ERROR,
    PORTABLE_SDL3_AUDIO_HOST_RESOURCE_ERROR,
    PORTABLE_SDL3_AUDIO_HOST_OUT_OF_MEMORY,
    PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_SOUND,
    PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC
} PortableSdl3AudioHostStatus;

typedef struct PortableSdl3AudioHost {
    PortableSdl3Audio output;
    PortableDatabase *database; /* Borrowed; caller closes it after the host. */
    int unsupported_song_active;
    int source_dac_mode1;
    uint16_t source_master_volume;
} PortableSdl3AudioHost;

/* `sample_rate` is an explicit host choice. The DOS source-derived decoder
 * does not establish the DAC's playback frequency. The database stays owned
 * by the caller and must outlive this host.
 */
int portable_sdl3_audio_host_open(PortableSdl3AudioHost *host,
                                  PortableDatabase *database,
                                  int sample_rate);
/* Open the bounded source-derived mode-1 speaker path at the integer SDL
 * approximation of the DOS PIT rate (11932 ticks/s). `master_volume` is the
 * source g_7502 value and must be in the source range 0..127. */
int portable_sdl3_audio_host_open_dac_mode1(PortableSdl3AudioHost *host,
                                            PortableDatabase *database,
                                            uint16_t master_volume);
void portable_sdl3_audio_host_close(PortableSdl3AudioHost *host);

/* Consume queued logical requests in order. SOUND decodes a real kind-5
 * resource and queues its mono U8 bytes. SONG fails explicitly because the
 * original MIDI/instrument playback is not implemented. The request that
 * returns an error is consumed and included in `processed`.
 */
PortableSdl3AudioHostStatus portable_sdl3_audio_host_process(
    PortableSdl3AudioHost *host, PortableAudioIntents *intents,
    size_t *processed);

/* Consume intents through the source-derived, isolated non-looping DAC
 * profiles. Only the explicitly supported SFX table rows are rendered;
 * songs remain unsupported. */
PortableSdl3AudioHostStatus portable_sdl3_audio_host_process_dac_mode1(
    PortableSdl3AudioHost *host, PortableAudioIntents *intents,
    size_t *processed);

/* A requested unsupported song has no truthful completion status. While one
 * is pending, this returns UNSUPPORTED_MUSIC and writes done=0. A STOP_SONG
 * request clears that state; with no unsupported song pending, done=1.
 */
PortableSdl3AudioHostStatus portable_sdl3_audio_host_song_done(
    const PortableSdl3AudioHost *host, int *done);
int portable_sdl3_audio_host_queued_bytes(const PortableSdl3AudioHost *host);
const char *portable_sdl3_audio_host_error(
    const PortableSdl3AudioHost *host,
    PortableSdl3AudioHostStatus status);

#endif
