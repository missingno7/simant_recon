#include "../../whole_program/platform/audio_events.h"
#include "../../whole_program/platform/whole_audio_provider.h"
#include "../../audio/dac_mixer.h"
#include "../../audio/intent.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Link controls: the direct-event provider never uses DB-backed SFX lookup. */
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

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #x); \
    return 1; \
} } while (0)

typedef struct ScriptClock {
    uint64_t values[4];
    size_t next;
} ScriptClock;

static uint64_t clock_read(void *context)
{
    ScriptClock *clock = (ScriptClock *)context;
    return clock->values[clock->next++];
}

static unsigned sequencer_calls;

static int16_t sequencer_delay(void)
{
    ++sequencer_calls;
    return 3;
}

int main(void)
{
    PortableWholeAudioEventQueue queue;
    PortableWholeAudioProvider provider;
    ScriptClock clock = { { 2, 6, 9, 9 }, 0 };
    uint8_t original[] = { 0, 0xff, 0xff, 0 };
    uint8_t rendered[8];
    uint8_t timer_samples[6];
    PortableWholeAudioEvent event;
    int16_t source_divider = 2;

    portable_whole_audio_event_queue_init(&queue);
    CHECK(portable_whole_audio_event_queue_bind_clock(&queue, clock_read, &clock));
    CHECK(portable_whole_audio_sample_start(0, original, sizeof(original), 0,
                                            0x100, 0, 0) ==
          PORTABLE_WHOLE_AUDIO_EVENT_OK);
    original[1] = 0; /* The source resource may be released or reused now. */
    CHECK(portable_whole_audio_sample_stop(0) == PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(portable_whole_audio_event_next(&queue, &event));
    CHECK(event.sequence == 0 && event.sample_deadline == 2 && event.timestamped);
    CHECK(event.sample_pcm[1] == 0xff); /* queue owns a snapshot */
    portable_whole_audio_provider_init(&provider);
    CHECK(portable_whole_audio_provider_apply(&provider, &event) ==
          PORTABLE_WHOLE_AUDIO_PROVIDER_OK);
    CHECK(provider.scheduler.voices[0].end == 2);
    CHECK(provider.scheduler.voices[0].step_8_8 == 0x100);
    CHECK(provider.scheduler.voices[0].position == 0);
    portable_whole_audio_event_free(&event);
    portable_whole_audio_provider_close(&provider);
    portable_whole_audio_event_queue_close(&queue);

    /* Re-run from a fresh timeline; start/stop land at sample indexes 2 and 6. */
    clock.next = 0;
    portable_whole_audio_event_queue_init(&queue);
    CHECK(portable_whole_audio_event_queue_bind_clock(&queue, clock_read, &clock));
    portable_whole_audio_provider_init(&provider);
    CHECK(portable_whole_audio_sample_start(0,
          (const uint8_t[]){ 0, 0xff, 0xff, 0 }, 4, 0, 0x100, 0, 0) ==
          PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(portable_whole_audio_sample_stop(0) == PORTABLE_WHOLE_AUDIO_EVENT_OK);
    CHECK(portable_whole_audio_provider_render(&provider, &queue, rendered,
                                               sizeof(rendered)) ==
          PORTABLE_WHOLE_AUDIO_PROVIDER_OK);
    CHECK(rendered[0] == 0 && rendered[1] == 0);
    CHECK(rendered[2] == 0xff && rendered[3] == 0xff);
    CHECK(rendered[6] == 0 && rendered[7] == 0);
    CHECK(provider.sample_cursor == 8);
    CHECK(provider.scheduler.voices[0].pcm == NULL);
    memset(&event, 0, sizeof(event));
    event.sequence = 1; /* duplicate of consumed stop */
    event.kind = PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_STOP;
    CHECK(portable_whole_audio_provider_apply(&provider, &event) ==
          PORTABLE_WHOLE_AUDIO_PROVIDER_BAD_EVENT_ORDER);
    event.sequence = 2;
    event.kind = (PortableWholeAudioEventKind)99;
    CHECK(portable_whole_audio_provider_apply(&provider, &event) ==
          PORTABLE_WHOLE_AUDIO_PROVIDER_UNSUPPORTED_EVENT);

    portable_whole_audio_provider_close(&provider);
    portable_whole_audio_event_queue_close(&queue);

    portable_whole_audio_event_queue_init(&queue);
    portable_whole_audio_provider_init(&provider);
    sequencer_calls = 0;
    portable_whole_audio_provider_set_sequencer(&provider, &source_divider,
                                                 sequencer_delay);
    CHECK(portable_whole_audio_provider_render(&provider, &queue, timer_samples,
                                               sizeof(timer_samples)) ==
          PORTABLE_WHOLE_AUDIO_PROVIDER_OK);
    CHECK(sequencer_calls == 2); /* initial 2 PIT ticks, then 3 more */
    CHECK(source_divider == 2);
    portable_whole_audio_provider_close(&provider);
    portable_whole_audio_event_queue_close(&queue);
    puts("PASS: timestamped source event queue and whole-program DAC provider");
    return 0;
}
