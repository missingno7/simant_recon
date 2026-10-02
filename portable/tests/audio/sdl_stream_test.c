#include "../../audio/intent.h"
#include "../../platform/sdl3/audio.h"

#include <stdio.h>

int main(int argc, char **argv)
{
    PortableSdl3Audio audio = { 0 };
    PortableDatabase database;
    uint8_t *pcm = NULL;
    size_t pcm_size = 0;
    if (argc != 2) {
        fprintf(stderr, "usage: sdl_stream_test SOUND_DATABASE_ROOT\n");
        return 2;
    }
    if (portable_sdl3_audio_open(NULL, 22050) ||
        portable_sdl3_audio_done(NULL) ||
        portable_sdl3_audio_queue_u8(NULL, NULL, 0)) {
        fprintf(stderr, "invalid SDL3 audio context reported success\n");
        return 1;
    }
    if (portable_db_open(&database, argv[1]) != PORTABLE_DB_OK) {
        fprintf(stderr, "SOUND database open failed: %s\n",
                portable_db_error(&database));
        return 1;
    }
    if (portable_audio_load_sound_pcm(&database, 1, &pcm, &pcm_size) !=
        PORTABLE_AUDIO_PCM_OK) {
        fprintf(stderr, "alert1 sample decode failed: %s\n",
                portable_db_error(&database));
        portable_db_close(&database);
        return 1;
    }
    if (!portable_sdl3_audio_open(&audio, 22050)) {
        fprintf(stderr, "SDL3 audio open failed: %s\n",
                portable_sdl3_audio_error());
        portable_audio_free_pcm(pcm);
        portable_db_close(&database);
        return 1;
    }
    if (!portable_sdl3_audio_queue_u8(&audio, pcm, pcm_size)) {
        fprintf(stderr, "SDL3 audio queue failed: %s\n",
                portable_sdl3_audio_error());
        portable_sdl3_audio_close(&audio);
        portable_audio_free_pcm(pcm);
        portable_db_close(&database);
        return 1;
    }
    printf("PASS sdl3_stream=mono_u8 source=alert1 decoded_bytes=%zu queued_bytes=%d\n",
           pcm_size, portable_sdl3_audio_queued_bytes(&audio));
    portable_sdl3_audio_close(&audio);
    portable_audio_free_pcm(pcm);
    portable_db_close(&database);
    return 0;
}
