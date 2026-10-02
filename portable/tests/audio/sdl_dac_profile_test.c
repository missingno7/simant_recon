#include "../../audio/dac_mixer.h"
#include "../../platform/sdl3/audio_host.h"

#include <stdio.h>

static int check_profiles(void)
{
    static const struct {
        int16_t id;
        int16_t instrument;
        int16_t sample;
        int16_t note;
        uint16_t step;
    } expected[] = {
        { 0, 0, 35, 60, 0x00cb },
        { 1, 1,  1, 60, 0x0100 },
        { 2, 2,  2, 60, 0x0100 },
        { 3, 3, 56, 60, 0x0400 },
        { 4, 4,  4, 60, 0x0100 },
        {55,10, 10,100, 0x0a10 }
    };
    PortableDacSfxProfile profile;
    size_t i;
    for (i = 0; i < sizeof(expected) / sizeof(expected[0]); ++i) {
        if (portable_dac_sfx_profile(expected[i].id, 127, &profile) !=
                PORTABLE_DAC_MIXER_OK ||
            profile.instrument_id != expected[i].instrument ||
            profile.sample_object_id != expected[i].sample ||
            profile.note != expected[i].note ||
            profile.step_8_8 != expected[i].step ||
            profile.source_channels != 2 || profile.volume_row != 0 ||
            profile.sample_looped != 0 || profile.sample_loop != 0) {
            fprintf(stderr, "source DAC profile mismatch for sound %d\n",
                    expected[i].id);
            return 0;
        }
    }
    if (portable_dac_sfx_profile(1, 0, &profile) != PORTABLE_DAC_MIXER_OK ||
        profile.volume_row != 3 ||
        portable_dac_sfx_profile(1, 128, &profile) !=
            PORTABLE_DAC_MIXER_INVALID_ARGUMENT ||
        portable_dac_sfx_profile(6, 127, &profile) !=
            PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE) {
        fprintf(stderr, "DAC volume domain or unsupported profile mismatch\n");
        return 0;
    }
    return 1;
}

static int check_render_and_sdl(PortableDatabase *database)
{
    PortableDacSfxProfile profile;
    PortableSdl3AudioHost host = { 0 };
    PortableAudioIntents intents;
    PortableSdl3AudioHostStatus host_status;
    uint8_t *pcm = NULL;
    size_t pcm_size = 0;
    size_t processed = 0;
    size_t i;
    int done = 0;
    if (portable_dac_render_sfx(database, 1, 127, &pcm, &pcm_size,
                                &profile) != PORTABLE_DAC_MIXER_OK ||
        pcm == NULL || pcm_size == 0 || profile.step_8_8 != 0x100) {
        fprintf(stderr, "source mode-1 sample rendering failed\n");
        portable_dac_free_pcm(pcm);
        return 0;
    }
    for (i = 0; i < pcm_size; ++i) {
        if (pcm[i] != 0x00 && pcm[i] != 0xff) {
            fprintf(stderr, "speaker output escaped logic levels\n");
            portable_dac_free_pcm(pcm);
            return 0;
        }
    }
    portable_dac_free_pcm(pcm);

    if (!portable_sdl3_audio_host_open_dac_mode1(&host, database, 127) ||
        host.output.sample_rate != PORTABLE_DAC_MODE1_SAMPLE_RATE) {
        fprintf(stderr, "source PIT-rate SDL stream open failed: %s\n",
                portable_sdl3_audio_error());
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    portable_audio_intents_init(&intents);
    portable_audio_intents_set_options(&intents, 1, 1, 1);
    if (!portable_audio_begin_sound(&intents, 1, 0, 0)) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    host_status = portable_sdl3_audio_host_process_dac_mode1(
        &host, &intents, &processed);
    if (host_status != PORTABLE_SDL3_AUDIO_HOST_OK || processed != 1 ||
        intents.count != 0 || portable_sdl3_audio_host_queued_bytes(&host) <= 0) {
        fprintf(stderr, "source DAC intent did not queue: status=%d processed=%zu\n",
                host_status, processed);
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    if (!portable_audio_begin_sound(&intents, 6, 0, 0)) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    host_status = portable_sdl3_audio_host_process_dac_mode1(
        &host, &intents, &processed);
    if (host_status != PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_SOUND) {
        fprintf(stderr, "unprofiled DAC sound was accepted\n");
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    if (!portable_audio_begin_song(&intents, 0x2711, 0x7e)) {
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    processed = 0;
    host_status = portable_sdl3_audio_host_process_dac_mode1(
        &host, &intents, &processed);
    if (host_status != PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC ||
        portable_sdl3_audio_host_song_done(&host, &done) !=
            PORTABLE_SDL3_AUDIO_HOST_UNSUPPORTED_MUSIC || done != 0) {
        fprintf(stderr, "unsupported song completion was misreported\n");
        portable_sdl3_audio_host_close(&host);
        return 0;
    }
    printf("PASS source_profile=sound1 rate=%d queued=%d model=isolated_mode1_logic_levels music=unsupported\n",
           host.output.sample_rate,
           portable_sdl3_audio_host_queued_bytes(&host));
    portable_sdl3_audio_host_close(&host);
    return 1;
}

int main(int argc, char **argv)
{
    PortableDatabase database;
    if (argc != 2) {
        fprintf(stderr, "usage: sdl_dac_profile_test SOUND_DATABASE_ROOT\n");
        return 2;
    }
    if (!check_profiles()) return 1;
    if (portable_db_open(&database, argv[1]) != PORTABLE_DB_OK) {
        fprintf(stderr, "SOUND database open failed: %s\n",
                portable_db_error(&database));
        return 1;
    }
    if (!check_render_and_sdl(&database)) {
        portable_db_close(&database);
        return 1;
    }
    portable_db_close(&database);
    return 0;
}
