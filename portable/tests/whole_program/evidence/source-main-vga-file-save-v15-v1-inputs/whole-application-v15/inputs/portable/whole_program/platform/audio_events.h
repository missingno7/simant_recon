#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_EVENTS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_EVENTS_H

#include <stddef.h>
#include <stdint.h>

enum {
    PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY = 64,
    PORTABLE_WHOLE_AUDIO_DAC_CHANNELS = 2
};

typedef enum PortableWholeAudioEventKind {
    PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_START = 1,
    PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_STOP = 2
} PortableWholeAudioEventKind;

typedef enum PortableWholeAudioEventStatus {
    PORTABLE_WHOLE_AUDIO_EVENT_OK = 0,
    PORTABLE_WHOLE_AUDIO_EVENT_INVALID_ARGUMENT,
    PORTABLE_WHOLE_AUDIO_EVENT_NOT_BOUND,
    PORTABLE_WHOLE_AUDIO_EVENT_QUEUE_FULL,
    PORTABLE_WHOLE_AUDIO_EVENT_RESOURCE_INVALID
} PortableWholeAudioEventStatus;

typedef struct PortableWholeAudioEvent {
    uint64_t sequence;
    PortableWholeAudioEventKind kind;
    uint16_t channel;
    uint16_t sample_size;
    uint16_t sample_loop;
    uint16_t step_8_8;
    uint64_t sample_deadline;
    uint8_t volume_row;
    uint8_t looped;
    uint8_t timestamped;
    uint8_t *sample_pcm; /* Owned by event until next() transfers it. */
} PortableWholeAudioEvent;

typedef uint64_t (*PortableWholeAudioClock)(void *context);

typedef struct PortableWholeAudioEventQueue {
    PortableWholeAudioEvent events[PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY];
    size_t head;
    size_t count;
    uint64_t next_sequence;
    PortableWholeAudioClock clock;
    void *clock_context;
    int initialized;
} PortableWholeAudioEventQueue;

void portable_whole_audio_event_queue_init(PortableWholeAudioEventQueue *queue);
void portable_whole_audio_event_queue_close(PortableWholeAudioEventQueue *queue);
int portable_whole_audio_event_queue_bind(PortableWholeAudioEventQueue *queue);
/* Bind with a monotonic source-audio sample-index reader. Every event captures
 * the clock at its source call site; clock units are original mode-1 output
 * steps at exact rate 14,318,180/(12*214) per second.
 */
int portable_whole_audio_event_queue_bind_clock(
    PortableWholeAudioEventQueue *queue, PortableWholeAudioClock clock,
    void *clock_context);
void portable_whole_audio_event_queue_unbind(PortableWholeAudioEventQueue *queue);

/* Source m290D hooks. start() copies the already-decoded sample bytes so the
 * DB handle may be released immediately after the source callback returns.
 * `sample_loop` and `sample_size` are the source Sample fields before the
 * 2-byte ISR end/loop adjustment. */
PortableWholeAudioEventStatus portable_whole_audio_sample_start(
    unsigned channel, const uint8_t *sample_pcm, size_t sample_size,
    unsigned sample_loop, unsigned step_8_8, unsigned volume_row,
    int looped);
PortableWholeAudioEventStatus portable_whole_audio_sample_stop(
    unsigned channel);

/* Transfers ownership of event.sample_pcm to the caller; release it with
 * portable_whole_audio_event_free after applying the event. */
int portable_whole_audio_event_next(PortableWholeAudioEventQueue *queue,
                                    PortableWholeAudioEvent *event);
void portable_whole_audio_event_free(PortableWholeAudioEvent *event);

/* Adapted source code fails closed if the native event sink is not bound or
 * cannot retain the exact sample event; it never reports silent success. */
_Noreturn void portable_whole_audio_event_fault(
    PortableWholeAudioEventStatus status);

#endif
