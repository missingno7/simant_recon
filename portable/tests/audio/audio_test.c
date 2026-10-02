#include "../../audio/intent.h"

#include <stdio.h>
#include <stdlib.h>

static uint64_t hash_bytes(const uint8_t *bytes, size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t i;
    for (i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static int check_intents(void)
{
    PortableAudioIntents audio;
    PortableAudioIntent intent;
    if (portable_audio_begin_sound(NULL, 1, 0, 0) ||
        portable_audio_begin_song(NULL, 1, 0) ||
        portable_audio_song_done(NULL, 1)) return 0;
    portable_audio_intents_init(&audio);
    if (!portable_audio_begin_sound(&audio, 1, 0, 0x7e) || audio.count != 0)
        return 0;
    portable_audio_intents_set_options(&audio, 1, 1, 1);
    if (!portable_audio_begin_sound(&audio, 1, 12, 63) ||
        !portable_audio_begin_song(&audio, 0x2711, 0x7e)) return 0;
    if (!portable_audio_next_intent(&audio, &intent) ||
        intent.kind != PORTABLE_AUDIO_INTENT_SOUND || intent.id != 1 ||
        intent.arg_a != 12 || intent.arg_b != 63 || intent.sequence != 0) return 0;
    if (!portable_audio_next_intent(&audio, &intent) ||
        intent.kind != PORTABLE_AUDIO_INTENT_STOP_SONG || intent.sequence != 1) return 0;
    if (!portable_audio_next_intent(&audio, &intent) ||
        intent.kind != PORTABLE_AUDIO_INTENT_SONG || intent.id != 0x2711 ||
        intent.arg_a != 0x7e || intent.sequence != 2) return 0;
    if (portable_audio_next_intent(&audio, &intent)) return 0;
    if (!portable_audio_song_done(&audio, 1) || !portable_audio_sound_done()) return 0;
    portable_audio_intents_set_options(&audio, 0, 1, 1);
    return portable_audio_song_done(&audio, 0);
}

static int check_sound_id_mapping(void)
{
    static const struct { int16_t sound_id; int16_t sample_id; } cases[] = {
        { 0, 35 }, { 1, 1 }, { 3, 56 }, { 17, 35 }, { 18, 18 },
        { 25, 56 }, { 46, 35 }, { 53, 56 }, { 54, 56 }, { 55, 10 }
    };
    size_t i;
    int16_t sample_id;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (!portable_audio_dac_sample_for_sound_id(cases[i].sound_id,
                                                    &sample_id) ||
            sample_id != cases[i].sample_id) return 0;
    }
    return !portable_audio_dac_sample_for_sound_id(-1, &sample_id) &&
           !portable_audio_dac_sample_for_sound_id(56, &sample_id) &&
           !portable_audio_sound_supported(-1) &&
           portable_audio_sound_supported(55) &&
           !portable_audio_song_supported();
}

int main(int argc, char **argv)
{
    PortableDatabase database;
    PortableDbStatus db_status;
    PortableAudioPcmStatus audio_status;
    uint8_t *pcm = NULL;
    uint8_t *decoded;
    size_t pcm_size = 0;
    size_t decoded_size;
    uint64_t hash;
    if (argc != 2) {
        fprintf(stderr, "usage: audio_test SOUND_DATABASE_ROOT\n");
        return 2;
    }
    if (!check_intents() || !check_sound_id_mapping()) {
        fprintf(stderr, "logical audio intent/mapping contract failed\n");
        return 1;
    }
    db_status = portable_db_open(&database, argv[1]);
    if (db_status != PORTABLE_DB_OK) {
        fprintf(stderr, "SOUND database open failed: %s\n",
                portable_db_status_string(db_status));
        return 1;
    }
    audio_status = portable_audio_load_sound_pcm(&database, 1, &pcm, &pcm_size);
    if (audio_status != PORTABLE_AUDIO_PCM_OK || pcm_size == 0) {
        fprintf(stderr, "alert1 decode failed: audio status %d (%s)\n",
                (int)audio_status, portable_db_error(&database));
        portable_db_close(&database);
        return 1;
    }
    hash = hash_bytes(pcm, pcm_size);
    decoded = pcm;
    decoded_size = pcm_size;
    pcm = NULL;
    /* Expected from the DOS source decoder: initial accumulator 0x80, then
     * unsigned wrapping additions of each high/low nibble's delta byte. */
    if (decoded_size != 752 || hash != UINT64_C(0xb993b26942e2156d)) {
        fprintf(stderr, "alert1 PCM differs: bytes=%zu hash=%016llx\n",
                decoded_size, (unsigned long long)hash);
        portable_audio_free_pcm(decoded);
        portable_db_close(&database);
        return 1;
    }
    portable_audio_free_pcm(decoded);
    decoded = NULL;
    if (portable_audio_load_sample_pcm(&database, 56, &pcm, &pcm_size) !=
        PORTABLE_AUDIO_PCM_OK || pcm_size == 0) {
        fprintf(stderr, "square3 sample decode failed\n");
        portable_audio_free_pcm(pcm);
        portable_db_close(&database);
        return 1;
    }
    portable_audio_free_pcm(pcm);
    pcm = NULL;
    if (portable_audio_load_sample_pcm(&database, 57, &pcm, &pcm_size) !=
        PORTABLE_AUDIO_PCM_UNSUPPORTED) {
        fprintf(stderr, "unexpected sample coverage\n");
        portable_audio_free_pcm(decoded);
        portable_audio_free_pcm(pcm);
        portable_db_close(&database);
        return 1;
    }
    printf("PASS intent_order=3 sound=1 resource_kind=5 pcm_bytes=%zu fnv1a64=%016llx\n",
           decoded_size, (unsigned long long)hash);
    portable_audio_free_pcm(decoded);
    portable_db_close(&database);
    return 0;
}
