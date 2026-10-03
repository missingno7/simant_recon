#include "m1b73_main_input.h"

#include <stdlib.h>

static PortableM1B73Events *active_source_events;
static PortableInputTimeHost *active_source_input_host;

int portable_m1b73_bind_source_main_input(
    PortableM1B73Events *events,
    PortableInputTimeHost *input_host,
    SimTimingClock *clock,
    uint8_t *source_shift_state,
    PortableM1B73Event *native_records,
    uint16_t native_record_slots)
{
    PortableM1B73TimerQueueView queue;
    if (events == NULL || input_host == NULL || clock == NULL ||
        source_shift_state == NULL || native_records == NULL ||
        active_source_events != NULL || !input_host->dual_clock_binding ||
        input_host->clock != clock || input_host->bios_clock == clock ||
        !portable_m1b73_get_source_timer_queue_view(&queue))
        return 0;
    portable_m1b73_events_init(events, input_host, clock, queue.capacity,
        queue.count, queue.write_index, queue.read_index, source_shift_state,
        native_records, native_record_slots);
    if (!portable_m1b73_events_bind(events))
        return 0;
    active_source_events = events;
    active_source_input_host = input_host;
    return 1;
}

void portable_m1b73_unbind_source_main_input(
    PortableM1B73Events *events)
{
    if (events != NULL && events == active_source_events) {
        portable_m1b73_events_unbind(events);
        active_source_events = NULL;
        active_source_input_host = NULL;
    }
}

static PortableInputTimeHost *require_source_input_host(void)
{
    if (active_source_events == NULL || active_source_input_host == NULL ||
        !active_source_events->bound || !active_source_input_host->bound)
        abort();
    return active_source_input_host;
}

int16_t f_1B73_0A30(uint16_t scan_code)
{
    int down;
    PortableInputTimeHost *host = require_source_input_host();
    if (scan_code > UINT8_C(0x7f) ||
        !portable_input_time_host_is_scan_down(host, (uint8_t)scan_code, &down))
        abort();
    return (int16_t)(down != 0);
}

int16_t f_1B73_0EEE(void)
{
    PortableInputTimeHost *host = require_source_input_host();
    return (int16_t)(portable_input_time_host_keyboard_flags(host) &
                     UINT8_C(0x10));
}
