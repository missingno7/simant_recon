#include "m1b73_events.h"

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(sizeof(PortableM1B73Event) == 16,
               "DOS Event ABI is eight 16-bit words");
_Static_assert(offsetof(PortableM1B73Event, what) == 0 &&
               offsetof(PortableM1B73Event, message) == 2 &&
               offsetof(PortableM1B73Event, x4) == 4 &&
               offsetof(PortableM1B73Event, modLo) == 6 &&
               offsetof(PortableM1B73Event, modHi) == 7 &&
               offsetof(PortableM1B73Event, h) == 8 &&
               offsetof(PortableM1B73Event, v) == 10 &&
               offsetof(PortableM1B73Event, code) == 12 &&
               offsetof(PortableM1B73Event, xE) == 14,
               "DOS Event fields preserve original order and widths");

static PortableM1B73Events *active_events;

static int16_t signed_word(uint16_t bits)
{
    int16_t value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

void portable_m1b73_events_init(PortableM1B73Events *events,
                                PortableInputTimeHost *input_host,
                                SimTimingClock *clock,
                                int16_t *source_capacity,
                                int16_t *source_count,
                                int16_t *source_write_index,
                                int16_t *source_read_index,
                                uint8_t *source_shift_state,
                                PortableM1B73Event *source_records,
                                uint16_t source_record_slots)
{
    if (events == NULL)
        return;
    memset(events, 0, sizeof(*events));
    events->input_host = input_host;
    events->clock = clock;
    events->source_capacity = source_capacity;
    events->source_count = source_count;
    events->source_write_index = source_write_index;
    events->source_read_index = source_read_index;
    events->source_shift_state = source_shift_state;
    events->source_records = source_records;
    events->source_record_slots = source_record_slots;
}

int portable_m1b73_events_bind(PortableM1B73Events *events)
{
    if (events == NULL || events->input_host == NULL || events->clock == NULL ||
        events->source_capacity == NULL || events->source_count == NULL ||
        events->source_write_index == NULL || events->source_read_index == NULL ||
        events->source_shift_state == NULL ||
        events->source_records == NULL || !events->input_host->bound)
        return 0;
    if (active_events != NULL && active_events != events)
        return 0;
    active_events = events;
    events->bound = 1;
    return 1;
}

void portable_m1b73_events_unbind(PortableM1B73Events *events)
{
    if (events != NULL && active_events == events) {
        active_events = NULL;
        events->bound = 0;
    }
}

int portable_m1b73_event_enqueue_registers(PortableM1B73Events *events,
                                           uint16_t ax, uint16_t cx,
                                           uint16_t dx, uint16_t bx,
                                           uint16_t es)
{
    PortableM1B73Event *event;
    uint16_t next, capacity, write_index, read_index, count;
    uint32_t bios_ticks;
    uint16_t keyboard_flags;
    uint8_t modeled_bios_flags;
    if (events == NULL || !events->bound || events != active_events ||
        events->input_host == NULL || events->clock == NULL ||
        events->source_capacity == NULL || events->source_count == NULL ||
        events->source_write_index == NULL || events->source_read_index == NULL ||
        events->source_shift_state == NULL ||
        events->source_records == NULL)
        return 0;
    if (*events->source_capacity <= 0 || *events->source_count < 0 ||
        *events->source_write_index < 0 || *events->source_read_index < 0)
        return 0;
    capacity = (uint16_t)*events->source_capacity;
    write_index = (uint16_t)*events->source_write_index;
    read_index = (uint16_t)*events->source_read_index;
    count = (uint16_t)*events->source_count;
    if (capacity < 2 || capacity > PORTABLE_M1B73_EVENT_SLOTS ||
        capacity > events->source_record_slots || write_index >= capacity ||
        read_index >= capacity || count >= capacity)
        return 0;
    /* The original ring reserves one of its seven slots to distinguish full
     * from empty; its maximum queued count is therefore six. */
    next = (uint16_t)(write_index + 1u);
    if (capacity <= next)
        next = 0;
    if (next == read_index)
        return 0;
    if (!portable_input_time_host_current_modifiers(&modeled_bios_flags))
        return 0;
    /* The shared SDL host owns the modeled low BDA keyboard-flag byte; the
     * adjacent BIOS byte has no source-backed host equivalent here. */
    keyboard_flags = modeled_bios_flags;
    /* f_1B73_036E samples the BIOS data area clock, not m1B73's private
     * TickCount counter. */
    bios_ticks = f_1F58_0006();
    event = &events->source_records[write_index];
    /* f_1B73_036E does not write source Event.what; retain that slot word. */
    event->message = signed_word((uint16_t)(keyboard_flags |
        ((*events->source_shift_state & UINT8_C(0x80)) != 0 ? 1u : 0u)));
    event->x4 = signed_word((uint16_t)bios_ticks);
    event->modLo = (uint8_t)ax;
    event->modHi = (uint8_t)(ax >> 8);
    event->h = signed_word(cx);
    event->v = signed_word(dx);
    event->code = signed_word(bx);
    event->xE = signed_word(es);
    *events->source_write_index = (int16_t)next;
    *events->source_count = (int16_t)(count + 1u);
    if ((ax & UINT16_C(0x0a00)) != 0)
        *events->source_shift_state &= UINT8_C(0x7f);
    return 1;
}

uint16_t portable_m1b73_event_count(const PortableM1B73Events *events)
{
    if (events == NULL || events->source_count == NULL ||
        *events->source_count < 0)
        return 0;
    return (uint16_t)*events->source_count;
}

int16_t portable_m1b73_event_dequeue(PortableM1B73Events *events,
                                     PortableM1B73Event *event)
{
    uint16_t count, capacity, read_index, next;
    if (events == NULL || event == NULL || events->source_count == NULL ||
        events->source_read_index == NULL ||
        events->source_capacity == NULL || events->source_records == NULL)
        return -1;
    if (*events->source_count < 0 || *events->source_capacity <= 0 ||
        *events->source_read_index < 0)
        return -1;
    count = (uint16_t)*events->source_count;
    if (count == 0)
        return -1;
    capacity = (uint16_t)*events->source_capacity;
    read_index = (uint16_t)*events->source_read_index;
    if (capacity < 2 || capacity > PORTABLE_M1B73_EVENT_SLOTS ||
        capacity > events->source_record_slots || read_index >= capacity)
        return -1;
    *event = events->source_records[read_index];
    count = (uint16_t)(count - 1u);
    *events->source_count = (int16_t)count;
    next = (uint16_t)(read_index + 1u);
    if (capacity <= next)
        next = 0;
    *events->source_read_index = (int16_t)next;
    return signed_word(count);
}

int portable_m1b73_poll_host_event(PortableM1B73Events *events,
                                   HostEvent *event)
{
    if (events == NULL || !events->bound || events != active_events ||
        events->input_host == NULL)
        return -1;
    return portable_input_time_host_poll_event(events->input_host, event);
}

int portable_m1b73_poll_mouse(PortableM1B73Events *events,
                              HostInputState *state)
{
    if (events == NULL || !events->bound || events != active_events ||
        events->input_host == NULL)
        return 0;
    return portable_input_time_host_get_input_state(events->input_host, state);
}

static PortableM1B73Events *require_events(void)
{
    if (active_events == NULL || !active_events->bound ||
        active_events->clock == NULL || active_events->input_host == NULL)
        abort();
    return active_events;
}

uint32_t TickCount(void)
{
    PortableM1B73Events *events = require_events();
    if (portable_input_time_host_refresh_clock(events->input_host) !=
        PORTABLE_INPUT_TIME_OK)
        abort();
    return sim_timing_tick_count(events->clock);
}

int16_t f_1B73_032A(void)
{
    return signed_word(portable_m1b73_event_count(require_events()));
}

int16_t f_1B73_032E(void *event_record)
{
    PortableM1B73Events *events = require_events();
    if (event_record == NULL)
        abort();
    return portable_m1b73_event_dequeue(events,
        (PortableM1B73Event *)event_record);
}

void f_1B73_0511(void)
{
    sim_timing_set_tick_count_enabled(require_events()->clock, 0);
}

void f_1B73_0518(void)
{
    sim_timing_set_tick_count_enabled(require_events()->clock, 1);
}

void f_1B73_030F(int16_t bx, int16_t es, int16_t ax,
                 int16_t cx, int16_t dx)
{
    /* A full source ring is the original f_036E no-op path. */
    (void)portable_m1b73_event_enqueue_registers(require_events(),
        (uint16_t)ax, (uint16_t)cx, (uint16_t)dx,
        (uint16_t)bx, (uint16_t)es);
}

void portable_m1b73_event_enqueue_four_word_command(
    int16_t bx, int16_t es, int16_t ax, int16_t cx)
{
    /* The four source callsites enqueue command events whose Event.v is not
     * read by their reachable consumers. The fifth DOS stack word is not
     * represented by C; normalize only this unobserved field to zero. */
    f_1B73_030F(bx, es, ax, cx, 0);
}
