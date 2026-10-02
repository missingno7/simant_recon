#include "intent.h"

#include <stdlib.h>
#include <string.h>

void portable_audio_free_pcm(uint8_t *pcm)
{
    free(pcm);
}

static int push(PortableAudioIntents *audio, PortableAudioIntentKind kind,
                int16_t id, int16_t arg_a, int16_t arg_b)
{
    size_t slot;
    PortableAudioIntent *intent;
    if (audio == NULL) return 0;
    if (audio->count == PORTABLE_AUDIO_QUEUE_CAPACITY) {
        ++audio->dropped_count;
        return 0;
    }
    slot = (audio->head + audio->count) % PORTABLE_AUDIO_QUEUE_CAPACITY;
    intent = &audio->queue[slot];
    intent->sequence = audio->next_sequence++;
    intent->kind = kind;
    intent->id = id;
    intent->arg_a = arg_a;
    intent->arg_b = arg_b;
    ++audio->count;
    return 1;
}

void portable_audio_intents_init(PortableAudioIntents *audio)
{
    if (audio != NULL) memset(audio, 0, sizeof(*audio));
}

void portable_audio_intents_set_options(PortableAudioIntents *audio,
                                        int driver_ready,
                                        int sounds_enabled,
                                        int songs_enabled)
{
    if (audio == NULL) return;
    audio->driver_ready = driver_ready != 0;
    audio->sounds_enabled = sounds_enabled != 0;
    audio->songs_enabled = songs_enabled != 0;
}

int portable_audio_begin_sound(PortableAudioIntents *audio,
                               int16_t id, int16_t arg_a, int16_t arg_b)
{
    if (audio == NULL) return 0;
    if (!audio->driver_ready || !audio->sounds_enabled)
        return 1; /* DOS myBeginSound silently ignores disabled requests. */
    return push(audio, PORTABLE_AUDIO_INTENT_SOUND, id, arg_a, arg_b);
}

int portable_audio_begin_song(PortableAudioIntents *audio,
                              int16_t id, int16_t arg)
{
    if (audio == NULL) return 0;
    if (!audio->driver_ready || !audio->songs_enabled)
        return 1;
    if (audio->count > PORTABLE_AUDIO_QUEUE_CAPACITY - 2) {
        ++audio->dropped_count;
        return 0;
    }
    /* Source myBeginSong releases/stops the previous song before beginning. */
    return push(audio, PORTABLE_AUDIO_INTENT_STOP_SONG, 0, 0, 0) &&
           push(audio, PORTABLE_AUDIO_INTENT_SONG, id, arg, 0);
}

int portable_audio_stop_song(PortableAudioIntents *audio)
{
    if (audio == NULL) return 0;
    return push(audio, PORTABLE_AUDIO_INTENT_STOP_SONG, 0, 0, 0);
}

int portable_audio_next_intent(PortableAudioIntents *audio,
                               PortableAudioIntent *intent)
{
    if (audio == NULL || intent == NULL || audio->count == 0) return 0;
    *intent = audio->queue[audio->head];
    audio->head = (audio->head + 1) % PORTABLE_AUDIO_QUEUE_CAPACITY;
    --audio->count;
    return 1;
}

PortableAudioPcmStatus portable_audio_load_sample_pcm(PortableDatabase *database,
                                                       int16_t sample_object_id,
                                                       uint8_t **pcm,
                                                       size_t *pcm_size)
{
    PortableDbRecord record;
    PortableDbStatus status;
    uint8_t delta[16];
    uint8_t accumulator = 0x80;
    size_t samples;
    size_t i;

    if (pcm != NULL) *pcm = NULL;
    if (pcm_size != NULL) *pcm_size = 0;
    if (database == NULL || pcm == NULL || pcm_size == NULL)
        return PORTABLE_AUDIO_PCM_INVALID;
    if (sample_object_id < 0 || sample_object_id > 56)
        return PORTABLE_AUDIO_PCM_UNSUPPORTED;

    status = portable_db_load(database, sample_object_id, 5, &record);
    if (status != PORTABLE_DB_OK) return PORTABLE_AUDIO_PCM_RESOURCE_ERROR;
    if (record.size < sizeof(delta)) {
        portable_db_record_free(&record);
        return PORTABLE_AUDIO_PCM_RESOURCE_ERROR;
    }
    samples = (record.size - sizeof(delta)) * 2;
    *pcm = (uint8_t *)malloc(samples ? samples : 1);
    if (*pcm == NULL) {
        portable_db_record_free(&record);
        return PORTABLE_AUDIO_PCM_OUT_OF_MEMORY;
    }
    memcpy(delta, record.data, sizeof(delta));
    for (i = 0; i < samples; ++i) {
        uint8_t packed = record.data[sizeof(delta) + i / 2];
        uint8_t nibble = (i & 1u) == 0 ? (uint8_t)(packed >> 4) :
                                            (uint8_t)(packed & 0x0f);
        accumulator = (uint8_t)(accumulator + delta[nibble]);
        (*pcm)[i] = accumulator;
    }
    *pcm_size = samples;
    portable_db_record_free(&record);
    return PORTABLE_AUDIO_PCM_OK;
}

int portable_audio_dac_sample_for_sound_id(int16_t sound_id,
                                           int16_t *sample_object_id)
{
    /* Instrument indices and aliases from fd_55B3_0C42 in the DOS DAC table.
     * The final SFX note (index 55) uses note 100 and instrument 10 per
     * fd_55B3_0A82. Each value is the `object` member of that DAC Sample.
     */
    static const int8_t sample_ids[56] = {
        35, 1, 2, 56, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 35,
        35, 35, 18, 19, 20, 21, 22, 23, 24, 56, 26, 27, 28, 29, 30, 31,
        32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 35, 47,
        35, 49, 35, 35, 52, 56, 56, 10
    };
    if (sample_object_id != NULL) *sample_object_id = -1;
    if (sound_id < 0 || sound_id >= (int16_t)(sizeof(sample_ids) / sizeof(sample_ids[0])) ||
        sample_object_id == NULL)
        return 0;
    *sample_object_id = sample_ids[sound_id];
    return 1;
}

PortableAudioPcmStatus portable_audio_load_sound_pcm(PortableDatabase *database,
                                                      int16_t sound_id,
                                                      uint8_t **pcm,
                                                      size_t *pcm_size)
{
    int16_t sample_object_id;
    if (database == NULL || pcm == NULL || pcm_size == NULL)
        return PORTABLE_AUDIO_PCM_INVALID;
    if (!portable_audio_dac_sample_for_sound_id(sound_id, &sample_object_id)) {
        *pcm = NULL;
        *pcm_size = 0;
        return PORTABLE_AUDIO_PCM_UNSUPPORTED;
    }
    return portable_audio_load_sample_pcm(database, sample_object_id,
                                          pcm, pcm_size);
}

int portable_audio_sound_supported(int16_t sound_id)
{
    int16_t ignored;
    return portable_audio_dac_sample_for_sound_id(sound_id, &ignored);
}

int portable_audio_song_supported(void)
{
    return 0;
}

int portable_audio_sound_done(void)
{
    /* Frozen DOS sound-shell implementation returns 1 unconditionally. */
    return 1;
}

int portable_audio_song_done(const PortableAudioIntents *audio,
                             int driver_song_done)
{
    if (audio == NULL) return 0;
    if (!audio->driver_ready || !audio->songs_enabled)
        return 1;
    return driver_song_done != 0;
}
