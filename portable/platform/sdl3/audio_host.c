#include "audio_host.h"

#include <string.h>

int portable_sdl3_audio_host_open(PortableSdl3AudioHost *host,
                                  PortableDatabase *database,
                                  int sample_rate)
{
    if (host == NULL || database == NULL || sample_rate <= 0) return 0;
    memset(host, 0, sizeof(*host));
    if (!portable_sdl3_audio_open(&host->output, sample_rate)) return 0;
    host->database = database;
    return 1;
}

int portable_sdl3_audio_host_open_dac_mode1(PortableSdl3AudioHost *host,
                                            PortableDatabase *database,
                                            uint16_t master_volume)
{
    if (master_volume > 0x7f ||
        !portable_sdl3_audio_host_open(host, database,
                                       PORTABLE_DAC_MODE1_SAMPLE_RATE))
        return 0;
    host->source_dac_mode1 = 1;
    host->source_master_volume = master_volume;
    return 1;
}

void portable_sdl3_audio_host_close(PortableSdl3AudioHost *host)
{
    if (host == NULL) return;
    portable_sdl3_audio_close(&host->output);
    memset(host, 0, sizeof(*host));
}

PortableSdl3AudioHostStatus portable_sdl3_audio_host_process(
    PortableSdl3AudioHost *host, PortableAudioIntents *intents,
    size_t *processed)
{
    PortableAudioIntent intent;
    if (processed != NULL) *processed = 0;
    if (host == NULL || host->database == NULL || host->output.stream == NULL ||
        intents == NULL || processed == NULL)
        return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
    while (portable_audio_next_intent(intents, &intent)) {
        uint8_t *pcm = NULL;
        size_t pcm_size = 0;
        PortableAudioPcmStatus pcm_status;
        ++*processed;
        switch (intent.kind) {
        case PORTABLE_AUDIO_INTENT_SOUND:
            pcm_status = portable_audio_load_sound_pcm(host->database, intent.id,
                                                       &pcm, &pcm_size);
            if (pcm_status == PORTABLE_AUDIO_PCM_UNSUPPORTED)
                return PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_SOUND;
            if (pcm_status != PORTABLE_AUDIO_PCM_OK)
                return PORTABLE_SDL3_AUDIO_HOST_RESOURCE_ERROR;
            if (!portable_sdl3_audio_queue_u8(&host->output, pcm, pcm_size)) {
                portable_audio_free_pcm(pcm);
                return PORTABLE_SDL3_AUDIO_HOST_SDL_ERROR;
            }
            portable_audio_free_pcm(pcm);
            break;
        case PORTABLE_AUDIO_INTENT_STOP_SONG:
            host->unsupported_song_active = 0;
            break;
        case PORTABLE_AUDIO_INTENT_SONG:
            host->unsupported_song_active = 1;
            return PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC;
        default:
            return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
        }
    }
    return PORTABLE_SDL3_AUDIO_HOST_OK;
}

PortableSdl3AudioHostStatus portable_sdl3_audio_host_process_dac_mode1(
    PortableSdl3AudioHost *host, PortableAudioIntents *intents,
    size_t *processed)
{
    PortableAudioIntent intent;
    if (processed != NULL) *processed = 0;
    if (host == NULL || host->database == NULL || host->output.stream == NULL ||
        !host->source_dac_mode1 ||
        host->output.sample_rate != PORTABLE_DAC_MODE1_SAMPLE_RATE ||
        intents == NULL || processed == NULL)
        return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
    while (portable_audio_next_intent(intents, &intent)) {
        ++*processed;
        switch (intent.kind) {
        case PORTABLE_AUDIO_INTENT_SOUND: {
            uint8_t *pcm = NULL;
            size_t pcm_size = 0;
            PortableDacMixerStatus mixer_status = portable_dac_render_sfx(
                host->database, intent.id, host->source_master_volume,
                &pcm, &pcm_size, NULL);
            if (mixer_status == PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE) {
                return PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_SOUND;
            }
            if (mixer_status == PORTABLE_DAC_MIXER_OUT_OF_MEMORY)
                return PORTABLE_SDL3_AUDIO_HOST_OUT_OF_MEMORY;
            if (mixer_status == PORTABLE_DAC_MIXER_RESOURCE_ERROR)
                return PORTABLE_SDL3_AUDIO_HOST_RESOURCE_ERROR;
            if (mixer_status != PORTABLE_DAC_MIXER_OK)
                return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
            if (!portable_sdl3_audio_queue_u8(&host->output, pcm, pcm_size)) {
                portable_dac_free_pcm(pcm);
                return PORTABLE_SDL3_AUDIO_HOST_SDL_ERROR;
            }
            portable_dac_free_pcm(pcm);
            break;
        }
        case PORTABLE_AUDIO_INTENT_STOP_SONG:
            host->unsupported_song_active = 0;
            break;
        case PORTABLE_AUDIO_INTENT_SONG:
            host->unsupported_song_active = 1;
            return PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC;
        default:
            return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
        }
    }
    return PORTABLE_SDL3_AUDIO_HOST_OK;
}

PortableSdl3AudioHostStatus portable_sdl3_audio_host_song_done(
    const PortableSdl3AudioHost *host, int *done)
{
    if (done != NULL) *done = 0;
    if (host == NULL || done == NULL || host->database == NULL ||
        host->output.stream == NULL)
        return PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT;
    if (host->unsupported_song_active)
        return PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC;
    *done = 1;
    return PORTABLE_SDL3_AUDIO_HOST_OK;
}

int portable_sdl3_audio_host_queued_bytes(const PortableSdl3AudioHost *host)
{
    if (host == NULL) return 0;
    return portable_sdl3_audio_queued_bytes(&host->output);
}

const char *portable_sdl3_audio_host_error(
    const PortableSdl3AudioHost *host,
    PortableSdl3AudioHostStatus status)
{
    switch (status) {
    case PORTABLE_SDL3_AUDIO_HOST_OK:
        return "no audio host error";
    case PORTABLE_SDL3_AUDIO_HOST_INVALID_ARGUMENT:
        return "invalid SDL3 audio host argument or intent";
    case PORTABLE_SDL3_AUDIO_HOST_SDL_ERROR:
        return portable_sdl3_audio_error();
    case PORTABLE_SDL3_AUDIO_HOST_RESOURCE_ERROR:
        return host != NULL && host->database != NULL
            ? portable_db_error(host->database) : "SOUND database unavailable";
    case PORTABLE_SDL3_AUDIO_HOST_OUT_OF_MEMORY:
        return "audio sample allocation failed";
    case PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_SOUND:
        return "sound id has no supported DAC sample mapping";
    case PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC:
        return "MIDI song and instrument playback are unsupported";
    default:
        return "unknown SDL3 audio host status";
    }
}
