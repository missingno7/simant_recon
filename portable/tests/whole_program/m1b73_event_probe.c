#include "../../whole_program/platform/m1b73_events.h"
#include "../../whole_program/platform/m1b73_timer_view.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, NULL, (int16_t)0x91b0,
                       5, 0, 10, 0 };
int16_t g_5FF0 = PORTABLE_M1B73_EVENT_SLOTS;

static int push_event(uint32_t type)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = type;
    if (type == SDL_EVENT_KEY_DOWN) {
        event.key.type = type;
        event.key.key = SDLK_A;
        event.key.mod = SDL_KMOD_NONE;
    } else {
        event.button.type = type;
        event.button.button = SDL_BUTTON_LEFT;
        event.button.x = 21.0f;
        event.button.y = 31.0f;
    }
    return SDL_PushEvent(&event);
}

int main(void)
{
    SimTimingClock clock;
    PortableInputTimeHost input_host;
    PortableM1B73Events events;
    PortableM1B73Event record;
    PortableM1B73Event records[PORTABLE_M1B73_EVENT_SLOTS];
    PortableM1B73TimerQueueView queue_view;
    uint8_t source_shift_state = UINT8_C(0x80);
    HostEvent host_event;
    HostInputState mouse;
    Host *host = NULL;
    uint32_t before;
    int i;

    if (sim_timing_clock_init_bios(&clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK)
        return 1;
    clock.tick_count = UINT32_C(0x12343456);
    host = host_create("m1B73 event boundary probe", 1);
    if (host == NULL) {
        fprintf(stderr, "host_create: %s\n", host_error());
        return 2;
    }
    if (portable_input_time_host_init(&input_host, host, &clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&input_host) != PORTABLE_INPUT_TIME_OK)
        goto fail;
    memset(records, 0, sizeof(records));
    if (!portable_m1b73_get_source_timer_queue_view(&queue_view) ||
        queue_view.count != &g_5FF2.r.left ||
        queue_view.write_index != &g_5FF2.r.top ||
        queue_view.read_index != &g_5FF2.r.right ||
        queue_view.capacity != &g_5FF0 || g_5FF2.ticks != (int16_t)0x91b0)
        goto fail_input;
    portable_m1b73_events_init(&events, &input_host, &clock,
        queue_view.capacity, queue_view.count, queue_view.write_index,
        queue_view.read_index, &source_shift_state, records,
        PORTABLE_M1B73_EVENT_SLOTS);
    if (!portable_m1b73_events_bind(&events))
        goto fail_input;

    if (TickCount() != UINT32_C(0x12343456) || f_1B73_032A() != 0)
        goto fail_events;
    portable_input_time_host_set_keyboard_flags(&input_host, UINT8_C(0x20));
    SDL_SetModState(SDL_KMOD_LSHIFT | SDL_KMOD_CTRL);
    records[0].what = (int16_t)UINT16_C(0x6677);
    if (!portable_m1b73_event_enqueue_registers(&events, 0x0201, 0x1357,
                                                 0x2468, 0x1122, 0x3344) ||
        f_1B73_032A() != 1 || source_shift_state != 0)
        goto fail_events;
    for (i = 1; i < PORTABLE_M1B73_EVENT_MAX_COUNT; ++i) {
        clock.tick_count += 1;
        if (!portable_m1b73_event_enqueue_registers(&events,
                (uint16_t)(0x0200 + (uint16_t)i), (uint16_t)i,
                (uint16_t)(i + 1), (uint16_t)(i + 2), (uint16_t)(i + 3)))
            goto fail_events;
    }
    if (f_1B73_032A() != PORTABLE_M1B73_EVENT_MAX_COUNT ||
        portable_m1b73_event_enqueue_registers(&events, 1, 2, 3, 4, 5))
        goto fail_events;
    memset(&record, 0, sizeof(record));
    if (f_1B73_032E(&record) != PORTABLE_M1B73_EVENT_MAX_COUNT - 1)
        goto fail_events;
    if (record.what != (int16_t)UINT16_C(0x6677) ||
        (uint16_t)record.message != UINT16_C(0x0027) ||
        (uint16_t)record.x4 != UINT16_C(0x3456) ||
        (uint16_t)(((uint16_t)record.modHi << 8) | record.modLo) !=
            UINT16_C(0x0201) ||
        (uint16_t)record.h != UINT16_C(0x1357) ||
        (uint16_t)record.v != UINT16_C(0x2468) ||
        (uint16_t)record.code != UINT16_C(0x1122) ||
        (uint16_t)record.xE != UINT16_C(0x3344) ||
        f_1B73_032A() != PORTABLE_M1B73_EVENT_MAX_COUNT - 1)
        goto fail_events;
    for (i = 0; i < PORTABLE_M1B73_EVENT_MAX_COUNT - 1; ++i) {
        if (f_1B73_032E(&record) !=
                PORTABLE_M1B73_EVENT_MAX_COUNT - i - 2)
            goto fail_events;
    }
    if (f_1B73_032A() != 0)
        goto fail_events;
    if (f_1B73_032E(&record) != -1 || f_1B73_032A() != 0)
        goto fail_events;

    before = TickCount();
    f_1B73_0511();
    if (sim_timing_advance_nanoseconds(&clock, UINT64_C(1000000000)) !=
            SIM_TIMING_OK || TickCount() != before)
        goto fail_events;
    f_1B73_0518();
    if (sim_timing_advance_nanoseconds(&clock, UINT64_C(1000000000)) !=
            SIM_TIMING_OK || TickCount() == before)
        goto fail_events;
    if (!push_event(SDL_EVENT_KEY_DOWN) ||
        !push_event(SDL_EVENT_MOUSE_BUTTON_DOWN))
        goto fail_events;
    if (portable_m1b73_poll_host_event(&events, &host_event) != 1 ||
        host_event.kind != HOST_EVENT_KEY_DOWN ||
        portable_m1b73_poll_host_event(&events, &host_event) != 1 ||
        host_event.kind != HOST_EVENT_MOUSE_DOWN ||
        !portable_m1b73_poll_mouse(&events, &mouse))
        goto fail_events;

    portable_m1b73_events_unbind(&events);
    portable_input_time_host_shutdown(&input_host);
    host_destroy(host);
    puts("PASS m1B73 queue/tick adapter: six-slot ring, DOS record fields, shared SDL event consumer");
    return 0;

fail_events:
    portable_m1b73_events_unbind(&events);
fail_input:
    portable_input_time_host_shutdown(&input_host);
fail:
    if (host != NULL)
        host_destroy(host);
    return 3;
}
