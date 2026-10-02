#include "../../audio/intent.h"
#include "../../platform/sdl3/audio_host.h"

#include <stdio.h>

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

static int check_sound_output(PortableDatabase *database)
{
    PortableSdl3AudioHost host = { 0 };
    PortableAudioIntents intents;
    size_t processed = 0;
    uint8_t *reference_pcm = NULL;
    size_t reference_size = 0;
    int done = 0;
    PortableSdl3AudioHostStatus status;
    if (!portable_sdl3_audio_host_open(&host, database, 22050)) {
        fprintf(stderr, "SDL3 audio host open failed: %s\n",
                portable_sdl3_audio_error());
        return 0;
    }
    if (portable_audio_load_sound_pcm(database, 1, &reference_pcm,
                                      &reference_size) != PORTABLE_AUDIO_PCM_OK ||
        reference_size != 752 ||
        hash_bytes(reference_pcm, reference_size) != UINT64_C(0xb993b26942e2156d)) {
        fprintf(stderr, "host sample no longer matches the pinned DOS-decoder PCM\n");
        portable_audio_free_pcm(reference_pcm);
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    portable_audio_free_pcm(reference_pcm);
    portable_audio_intents_init(&intents);
    portable_audio_intents_set_options(&intents, 1, 1, 1);
    if (!portable_audio_begin_sound(&intents, 1, 0, 10)) return 0;
    status = portable_sdl3_audio_host_process(&host, &intents, &processed);
    if (status != PORTABLE_SDL3_AUDIO_HOST_OK || processed != 1 ||
        intents.count != 0 || portable_sdl3_audio_host_queued_bytes(&host) != 752) {
        fprintf(stderr, "SFX intent was not queued exactly: status=%d processed=%zu queued=%d (%s)\n",
                status, processed, portable_sdl3_audio_host_queued_bytes(&host),
                portable_sdl3_audio_host_error(&host, status));
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    status = portable_sdl3_audio_host_song_done(&host, &done);
    if (status != PORTABLE_SDL3_AUDIO_HOST_OK || done != 1) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }

    if (!portable_audio_begin_song(&intents, 0x2afe, 0x7e)) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    processed = 0;
    status = portable_sdl3_audio_host_process(&host, &intents, &processed);
    if (status != PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC || processed != 2 ||
        intents.count != 0) {
        fprintf(stderr, "song was not rejected explicitly: status=%d processed=%zu\n",
                status, processed);
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    done = 1;
    status = portable_sdl3_audio_host_song_done(&host, &done);
    if (status != PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC || done != 0) {
        fprintf(stderr, "unsupported active song was reported done\n");
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    if (!portable_audio_stop_song(&intents)) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    status = portable_sdl3_audio_host_process(&host, &intents, &processed);
    if (status != PORTABLE_SDL3_AUDIO_HOST_OK ||
        portable_sdl3_audio_host_song_done(&host, &done) !=
            PORTABLE_SDL3_AUDIO_HOST_OK || done != 1) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    printf("PASS host_intent=sound:1 resource=kind5 pcm=752 fnv1a64=b993b26942e2156d queued=%d rate_choice=%d music=explicitly_unsupported\n",
           portable_sdl3_audio_host_queued_bytes(&host), host.output.sample_rate);
    portable_sdl3_audio_host_close(&host);
    return 1;
}

int main(int argc, char **argv)
{
    PortableDatabase database;
    if (argc != 2) {
        fprintf(stderr, "usage: sdl_intent_host_test SOUND_DATABASE_ROOT\n");
        return 2;
    }
    if (portable_sdl3_audio_host_open(NULL, NULL, 22050)) {
        fprintf(stderr, "invalid SDL3 audio host reported success\n");
        return 1;
    }
    if (portable_db_open(&database, argv[1]) != PORTABLE_DB_OK) {
        fprintf(stderr, "SOUND database open failed: %s\n",
                portable_db_error(&database));
        return 1;
    }
    if (!check_sound_output(&database)) {
        portable_db_close(&database);
        return 1;
    }
    portable_db_close(&database);
    return 0;
}
