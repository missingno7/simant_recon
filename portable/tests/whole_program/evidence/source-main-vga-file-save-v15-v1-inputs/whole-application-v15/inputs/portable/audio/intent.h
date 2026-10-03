#ifndef SIMANT_PORTABLE_AUDIO_INTENT_H
#define SIMANT_PORTABLE_AUDIO_INTENT_H

#include <stddef.h>
#include <stdint.h>

#include "../game/resources/database.h"

enum { PORTABLE_AUDIO_QUEUE_CAPACITY = 64 };

typedef enum PortableAudioIntentKind {
    PORTABLE_AUDIO_INTENT_SOUND = 1,
    PORTABLE_AUDIO_INTENT_SONG = 2,
    PORTABLE_AUDIO_INTENT_STOP_SONG = 3
} PortableAudioIntentKind;

typedef enum PortableAudioPcmStatus {
    PORTABLE_AUDIO_PCM_OK = 0,
    PORTABLE_AUDIO_PCM_UNSUPPORTED,
    PORTABLE_AUDIO_PCM_RESOURCE_ERROR,
    PORTABLE_AUDIO_PCM_OUT_OF_MEMORY,
    PORTABLE_AUDIO_PCM_INVALID
} PortableAudioPcmStatus;

typedef struct PortableAudioIntent {
    uint64_t sequence;
    PortableAudioIntentKind kind;
    int16_t id;
    int16_t arg_a;
    int16_t arg_b;
} PortableAudioIntent;

typedef struct PortableAudioIntents {
    PortableAudioIntent queue[PORTABLE_AUDIO_QUEUE_CAPACITY];
    size_t head;
    size_t count;
    uint64_t next_sequence;
    int driver_ready;
    int sounds_enabled;
    int songs_enabled;
    int dropped_count;
} PortableAudioIntents;

void portable_audio_intents_init(PortableAudioIntents *audio);
void portable_audio_intents_set_options(PortableAudioIntents *audio,
                                        int driver_ready,
                                        int sounds_enabled,
                                        int songs_enabled);
int portable_audio_begin_sound(PortableAudioIntents *audio,
                               int16_t id, int16_t arg_a, int16_t arg_b);
int portable_audio_begin_song(PortableAudioIntents *audio,
                              int16_t id, int16_t arg);
int portable_audio_stop_song(PortableAudioIntents *audio);
int portable_audio_next_intent(PortableAudioIntents *audio,
                               PortableAudioIntent *intent);

/* Source f_290D_000E: each kind-5 SOUND resource contains a 16-byte delta
 * table followed by packed high-nibble/low-nibble deltas. All 57 shipped
 * sample records are decoded with the DOS unsigned-byte accumulator behavior.
 */
/* Sound ids resolve through the source SFX-note/DAC tables. This selects the
 * DAC resource identity only; it does not process the source note/volume args
 * or infer a device sample rate. */
PortableAudioPcmStatus portable_audio_load_sound_pcm(PortableDatabase *database,
                                                      int16_t sound_id,
                                                      uint8_t **pcm,
                                                      size_t *pcm_size);
void portable_audio_free_pcm(uint8_t *pcm);
PortableAudioPcmStatus portable_audio_load_sample_pcm(PortableDatabase *database,
                                                       int16_t sample_object_id,
                                                       uint8_t **pcm,
                                                       size_t *pcm_size);
int portable_audio_dac_sample_for_sound_id(int16_t sound_id,
                                           int16_t *sample_object_id);
int portable_audio_sound_supported(int16_t sound_id);
int portable_audio_song_supported(void);
int portable_audio_sound_done(void);
int portable_audio_song_done(const PortableAudioIntents *audio,
                             int driver_song_done);

#endif
