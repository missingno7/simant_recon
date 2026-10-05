#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_WHOLE_AUDIO_PROVIDER_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_WHOLE_AUDIO_PROVIDER_H

#include "audio_events.h"
#include "audio_mixer_service.h"

typedef enum PortableWholeAudioProviderStatus {
    PORTABLE_WHOLE_AUDIO_PROVIDER_OK = 0,
    PORTABLE_WHOLE_AUDIO_PROVIDER_INVALID_ARGUMENT,
    PORTABLE_WHOLE_AUDIO_PROVIDER_BAD_EVENT_ORDER,
    PORTABLE_WHOLE_AUDIO_PROVIDER_UNSUPPORTED_EVENT,
    PORTABLE_WHOLE_AUDIO_PROVIDER_RESOURCE_ERROR
} PortableWholeAudioProviderStatus;

typedef struct PortableWholeAudioProvider {
    PortableDacLiveScheduler scheduler;
    PortableWholeAudioEvent pending[PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY];
    size_t pending_count;
    uint64_t last_sequence;
    uint64_t sample_cursor;
    int16_t (*sequencer_tick)(void);
    int16_t *sequencer_divider;
    uint8_t has_sequence;
    uint8_t speaker_level;
    uint8_t in_render;
} PortableWholeAudioProvider;

/* This provider consumes only source m290D's two-channel sampled-DAC events.
 * It does not emulate DOS ports, BIOS services, MIDI, OPL, or device probing.
 */
void portable_whole_audio_provider_init(PortableWholeAudioProvider *provider);
void portable_whole_audio_provider_close(PortableWholeAudioProvider *provider);
/* Optional original m28BC timer hook. Pass the generated source's
 * fd_55B3_6B42 word and f_284A_067F. The ISR decrements that actual source
 * word every PIT sample and reloads it with the callback's low 16-bit return
 * value after zero. This preserves per-song initialization (which overwrites
 * the assembly's initial value).
 */
void portable_whole_audio_provider_set_sequencer(
    PortableWholeAudioProvider *provider, int16_t *source_divider,
    int16_t (*tick)(void));

/* Apply one already-dequeued event. PCM ownership transfers from event to the
 * provider on a start and is freed on replacement/close. Sequence numbers
 * must be strictly increasing so ordering errors fail closed.
 */
PortableWholeAudioProviderStatus portable_whole_audio_provider_apply(
    PortableWholeAudioProvider *provider, PortableWholeAudioEvent *event);

/* Render exactly one source mode-1 PIT sample as unsigned 8-bit audio. The
 * scheduler's speaker gate changes only when the original ISR would reach
 * out_speaker; an over-end skip holds its previous physical gate level.
 */
PortableWholeAudioProviderStatus portable_whole_audio_provider_render_tick(
    PortableWholeAudioProvider *provider, uint8_t *sample);

/* Drain source events and render `count` PIT samples. Timestamped events are
 * committed at their captured sample index; untimestamped deterministic test
 * events commit at the current sample boundary. Events remain ordered when
 * multiple callbacks fall within a render block.
 */
PortableWholeAudioProviderStatus portable_whole_audio_provider_render(
    PortableWholeAudioProvider *provider, PortableWholeAudioEventQueue *queue,
    uint8_t *samples, size_t count);

#endif
