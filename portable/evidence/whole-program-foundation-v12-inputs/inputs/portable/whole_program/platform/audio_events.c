#include "audio_events.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static PortableWholeAudioEventQueue *bound_queue;

static PortableWholeAudioEventStatus push_event(
    PortableWholeAudioEventKind kind, unsigned channel,
    const uint8_t *sample_pcm, size_t sample_size, unsigned sample_loop,
    unsigned step_8_8, unsigned volume_row, int looped)
{
    PortableWholeAudioEventQueue *queue = bound_queue;
    PortableWholeAudioEvent *event;
    size_t slot;
    uint8_t *copy = NULL;

    if (queue == NULL || queue->initialized == 0)
        return PORTABLE_WHOLE_AUDIO_EVENT_NOT_BOUND;
    if (channel >= PORTABLE_WHOLE_AUDIO_DAC_CHANNELS ||
        (looped != 0 && looped != 1))
        return PORTABLE_WHOLE_AUDIO_EVENT_INVALID_ARGUMENT;
    if (kind == PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_START) {
        if (sample_pcm == NULL || sample_size < 2 || sample_size > UINT16_MAX ||
            sample_loop > UINT16_MAX - 2u ||
            step_8_8 == 0 || step_8_8 > UINT16_MAX || volume_row > 7u)
            return PORTABLE_WHOLE_AUDIO_EVENT_RESOURCE_INVALID;
    } else if (kind != PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_STOP) {
        return PORTABLE_WHOLE_AUDIO_EVENT_INVALID_ARGUMENT;
    }
    if (queue->count == PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY)
        return PORTABLE_WHOLE_AUDIO_EVENT_QUEUE_FULL;
    if (kind == PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_START) {
        copy = (uint8_t *)malloc(sample_size);
        if (copy == NULL) return PORTABLE_WHOLE_AUDIO_EVENT_RESOURCE_INVALID;
        memcpy(copy, sample_pcm, sample_size);
    }
    slot = (queue->head + queue->count) % PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY;
    event = &queue->events[slot];
    memset(event, 0, sizeof(*event));
    event->sequence = queue->next_sequence++;
    event->kind = kind;
    event->channel = (uint16_t)channel;
    event->sample_size = (uint16_t)sample_size;
    event->sample_loop = (uint16_t)sample_loop;
    event->step_8_8 = (uint16_t)step_8_8;
    if (queue->clock != NULL) {
        event->sample_deadline = queue->clock(queue->clock_context);
        event->timestamped = 1;
    }
    event->volume_row = (uint8_t)volume_row;
    event->looped = (uint8_t)looped;
    event->sample_pcm = copy;
    ++queue->count;
    return PORTABLE_WHOLE_AUDIO_EVENT_OK;
}

void portable_whole_audio_event_queue_init(PortableWholeAudioEventQueue *queue)
{
    if (queue == NULL) return;
    memset(queue, 0, sizeof(*queue));
    queue->initialized = 1;
}

void portable_whole_audio_event_queue_close(PortableWholeAudioEventQueue *queue)
{
    size_t i;
    if (queue == NULL) return;
    if (bound_queue == queue) bound_queue = NULL;
    for (i = 0; i < PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY; ++i)
        free(queue->events[i].sample_pcm);
    memset(queue, 0, sizeof(*queue));
}

int portable_whole_audio_event_queue_bind(PortableWholeAudioEventQueue *queue)
{
    if (queue == NULL || queue->initialized == 0 || bound_queue != NULL)
        return 0;
    bound_queue = queue;
    return 1;
}

int portable_whole_audio_event_queue_bind_clock(
    PortableWholeAudioEventQueue *queue, PortableWholeAudioClock clock,
    void *clock_context)
{
    if (clock == NULL || !portable_whole_audio_event_queue_bind(queue))
        return 0;
    queue->clock = clock;
    queue->clock_context = clock_context;
    return 1;
}

void portable_whole_audio_event_queue_unbind(PortableWholeAudioEventQueue *queue)
{
    if (bound_queue == queue) bound_queue = NULL;
    if (queue != NULL) {
        queue->clock = NULL;
        queue->clock_context = NULL;
    }
}

PortableWholeAudioEventStatus portable_whole_audio_sample_start(
    unsigned channel, const uint8_t *sample_pcm, size_t sample_size,
    unsigned sample_loop, unsigned step_8_8, unsigned volume_row,
    int looped)
{
    return push_event(PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_START, channel,
                      sample_pcm, sample_size, sample_loop, step_8_8,
                      volume_row, looped);
}

PortableWholeAudioEventStatus portable_whole_audio_sample_stop(
    unsigned channel)
{
    return push_event(PORTABLE_WHOLE_AUDIO_EVENT_SAMPLE_STOP, channel,
                      NULL, 0, 0, 0, 0, 0);
}

int portable_whole_audio_event_next(PortableWholeAudioEventQueue *queue,
                                    PortableWholeAudioEvent *event)
{
    if (queue == NULL || event == NULL || queue->initialized == 0 ||
        queue->count == 0)
        return 0;
    *event = queue->events[queue->head];
    memset(&queue->events[queue->head], 0, sizeof(queue->events[queue->head]));
    queue->head = (queue->head + 1u) % PORTABLE_WHOLE_AUDIO_EVENT_CAPACITY;
    --queue->count;
    return 1;
}

void portable_whole_audio_event_free(PortableWholeAudioEvent *event)
{
    if (event == NULL) return;
    free(event->sample_pcm);
    memset(event, 0, sizeof(*event));
}

_Noreturn void portable_whole_audio_event_fault(
    PortableWholeAudioEventStatus status)
{
    fprintf(stderr, "whole-program audio provider event failure: %d\n", (int)status);
    abort();
}
