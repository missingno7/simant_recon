#include "../../platform/sdl3/whole_audio_provider.h"
#include "../../audio/dac_mixer.h"
#include "../../audio/intent.h"

#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "CHECK failed at %s:%d: %s (%s)\n", __FILE__, __LINE__, \
            #x, SDL_GetError()); \
    return 1; \
} } while (0)

/* Link controls for database-backed convenience functions not used by this
 * event-driven source path. */
PortableDacMixerStatus portable_dac_sfx_profile(int16_t sound_id,
                                                 uint16_t master_volume,
                                                 PortableDacSfxProfile *profile)
{
    (void)sound_id; (void)master_volume; (void)profile;
    return PORTABLE_DAC_MIXER_UNSUPPORTED_PROFILE;
}
PortableAudioPcmStatus portable_audio_load_sample_pcm(PortableDatabase *database,
                                                       int16_t object_id,
                                                       uint8_t **pcm,
                                                       size_t *pcm_size)
{
    (void)database; (void)object_id; (void)pcm; (void)pcm_size;
    return PORTABLE_AUDIO_PCM_RESOURCE_ERROR;
}
void portable_audio_free_pcm(uint8_t *pcm) { free(pcm); }
void portable_dac_free_pcm(uint8_t *pcm) { free(pcm); }

static unsigned sequencer_calls;
static int sequencer_event_status;
static const uint8_t sequencer_pcm[] = { 0, 0xff, 0xff, 0, 0, 0 };

static int16_t sequencer_tick(void)
{
    ++sequencer_calls;
    if (sequencer_calls == 1)
        sequencer_event_status = portable_whole_audio_sample_start(
            1, sequencer_pcm, sizeof(sequencer_pcm), 0, 0x100, 0, 1);
    return 3;
}

int main(void)
{
    PortableWholeAudioEventQueue queue;
    PortableSdl3WholeAudio audio;
    const uint8_t pcm[] = { 0, 0xff, 0xff, 0, 0, 0 };
    int16_t source_divider = 5;
    SDL_SetHint(SDL_HINT_AUDIO_DRIVER, "dummy");
    portable_whole_audio_event_queue_init(&queue);
    CHECK(portable_sdl3_whole_audio_open(
        &audio, &queue, PORTABLE_SDL3_WHOLE_AUDIO_MODE1_SAMPLED_DAC));
    sequencer_calls = 0;
    sequencer_event_status = -1;
    portable_sdl3_whole_audio_set_sequencer(&audio, &source_divider,
                                             sequencer_tick);
    CHECK(portable_whole_audio_sample_start(0, pcm, sizeof(pcm), 0,
                                            0x100, 0, 0) ==
          PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(portable_sdl3_whole_audio_pump(&audio, 2048) ==
          PORTABLE_SDL3_WHOLE_AUDIO_OK);
    CHECK(portable_sdl3_audio_queued_bytes(&audio.output) >= 2048);
    CHECK(audio.provider.sample_cursor >= 2048);
    CHECK(audio.provider.has_sequence && audio.provider.last_sequence == 1);
    CHECK(sequencer_event_status == PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(audio.provider.scheduler.allocator.channels[1].active == 1);
    CHECK(sequencer_calls > 400); /* Divider skips over-end source ticks. */
    CHECK(portable_whole_audio_sample_stop(0) == PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(portable_sdl3_whole_audio_pump(&audio, 3072) ==
          PORTABLE_SDL3_WHOLE_AUDIO_OK);
    CHECK(audio.provider.last_sequence == 2);
    portable_sdl3_whole_audio_close(&audio);
    portable_whole_audio_event_queue_close(&queue);
    puts("PASS: SDL3 dummy playback consumes timestamped source DAC events");
    return 0;
}
