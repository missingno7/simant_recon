#include "m1b73_queues.h"

#include "../types/timer.h"

#include <string.h>
#include <stdlib.h>

#include "portable/whole_program/types/input_queue.h"
extern uint16_t g_9120;
extern int16_t g_9122;
extern int16_t g_9124;

PortableM1B73QueueSet portable_m1b73_queue_set = {
    .queues = {
        { &canonical_mouse_queue0.capacity, &canonical_mouse_queue0.count, canonical_mouse_queue0.records, 5 },
        { &canonical_mouse_queue1.capacity, &canonical_mouse_queue1.count, canonical_mouse_queue1.records, 48 },
        { &canonical_mouse_queue2.capacity, &canonical_mouse_queue2.count, canonical_mouse_queue2.records, 48 },
        { &canonical_mouse_queue3.capacity, &canonical_mouse_queue3.count, canonical_mouse_queue3.records, 10 }
    }
};

static const uint8_t descriptor_event_masks[
    PORTABLE_M1B73_QUEUE_HOTBOX_DISPATCH_COUNT] = { 0xff, 0xff, 0x1e };
static PortableM1B73QueueServices active_services;
static uint8_t services_bound;

static int record_contains(const uint8_t *record, int16_t x, int16_t y)
{
    int16_t left, top, right, bottom;
    uint16_t bits;
    bits = (uint16_t)((uint16_t)record[0] | ((uint16_t)record[1] << 8));
    memcpy(&left, &bits, sizeof(left));
    bits = (uint16_t)((uint16_t)record[2] | ((uint16_t)record[3] << 8));
    memcpy(&top, &bits, sizeof(top));
    bits = (uint16_t)((uint16_t)record[4] | ((uint16_t)record[5] << 8));
    memcpy(&right, &bits, sizeof(right));
    bits = (uint16_t)((uint16_t)record[6] | ((uint16_t)record[7] << 8));
    memcpy(&bottom, &bits, sizeof(bottom));
    return x >= left && x <= right && y >= top && y <= bottom;
}

static uint16_t record_condition(const uint8_t *record)
{
    return (uint16_t)((uint16_t)record[16] |
                      ((uint16_t)record[17] << 8));
}

int portable_m1b73_queues_bind(const PortableM1B73QueueServices *services)
{
    if (services == NULL || services->dispatch_record == NULL ||
        services_bound != 0)
        return 0;
    active_services = *services;
    services_bound = 1;
    return 1;
}

void portable_m1b73_queues_unbind(void)
{
    services_bound = 0;
    active_services.context = NULL;
    active_services.dispatch_record = NULL;
}

PortableM1B73QueueStatus portable_m1b73_queue_dispatch(void)
{
    PortableM1B73QueueEvent event;
    uint8_t queue_index;
    event.status = g_9120;
    event.x = g_9122;
    event.y = g_9124;
    for (queue_index = 0;
         queue_index < PORTABLE_M1B73_QUEUE_HOTBOX_DISPATCH_COUNT;
         ++queue_index) {
        PortableM1B73Queue *queue =
            &portable_m1b73_queue_set.queues[queue_index];
        uint8_t record_index;
        if ((descriptor_event_masks[queue_index] &
             (uint8_t)(event.status >> 8)) == 0)
            continue;
        if ((*queue->count) > (*queue->capacity) ||
            (*queue->count) >= queue->allocated_record_count)
            return PORTABLE_M1B73_QUEUE_BAD_COUNT;
        for (record_index = 0; record_index < (*queue->count); ++record_index) {
            const uint8_t *record = queue->records[record_index];
            int keep_scanning;
            if ((record_condition(record) & event.status) == 0 ||
                !record_contains(record, event.x, event.y))
                continue;
            if (services_bound == 0 || active_services.dispatch_record == NULL)
                return PORTABLE_M1B73_QUEUE_PROVIDER_MISSING;
            keep_scanning = active_services.dispatch_record(
                active_services.context, queue_index, record_index, record,
                &event);
            if (keep_scanning == 0)
                return PORTABLE_M1B73_QUEUE_OK;
            /* f_1B73_0CEF reloads these globals after every callback. */
            event.status = g_9120;
            event.x = g_9122;
            event.y = g_9124;
        }
    }
    return PORTABLE_M1B73_QUEUE_OK;
}

void f_1B73_0CB3(void)
{
    if (portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_OK)
        abort();
}

void f_1B73_0AA3(void)
{
    (*portable_m1b73_queue_set.queues[0].count) = 0;
    (*portable_m1b73_queue_set.queues[1].count) = 0;
    g_5FF2.r.bottom = (int16_t)0x1f00;
    g_5FF2.fn = f_1B73_0CB3;
}
