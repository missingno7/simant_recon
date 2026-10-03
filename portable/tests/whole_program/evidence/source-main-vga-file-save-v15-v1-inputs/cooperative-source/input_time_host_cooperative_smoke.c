#include "../../whole_program/platform/sdl3/input_time_host.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct CooperativeClock {
    SimTimingClock *clock;
    uint64_t elapsed_ns;
    uint32_t calls;
    uint32_t inject_escape_on_call;
} CooperativeClock;

static int refresh_and_maybe_inject(void *context, SimTimingClock *clock)
{
    CooperativeClock *service = (CooperativeClock *)context;
    if (service == NULL || clock != service->clock)
        return 0;
    ++service->calls;
    if (sim_timing_advance_nanoseconds(clock, service->elapsed_ns) !=
        SIM_TIMING_OK)
        return 0;
    if (service->calls == service->inject_escape_on_call) {
        SDL_Event event;
        memset(&event, 0, sizeof(event));
        event.type = SDL_EVENT_KEY_DOWN;
        event.key.type = SDL_EVENT_KEY_DOWN;
        event.key.key = SDLK_ESCAPE;
        event.key.scancode = SDL_SCANCODE_ESCAPE;
        event.key.down = true;
        if (SDL_PushEvent(&event) != 1)
            return 0;
    }
    return 1;
}

static int push_key(SDL_Keycode key, SDL_Scancode scan)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.type = SDL_EVENT_KEY_DOWN;
    event.key.key = key;
    event.key.scancode = scan;
    event.key.down = true;
    return SDL_PushEvent(&event) == 1;
}

static int push_mouse(void)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    event.button.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    event.button.button = SDL_BUTTON_LEFT;
    event.button.x = 31.0f;
    event.button.y = 27.0f;
    return SDL_PushEvent(&event) == 1;
}

int main(void)
{
    SimTimingClock clock;
    PortableInputTimeHost input;
    CooperativeClock service;
    Host *host = NULL;
    HostEvent events[3];
    uint32_t before_ticks, before_calls;
    int result = 1;

    memset(&service, 0, sizeof(service));
    if (sim_timing_clock_init_bios(&clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK)
        return 1;
    service.clock = &clock;
    service.elapsed_ns = UINT64_C(1000000000);
    host = host_create("input/time cooperative smoke", 1);
    if (host == NULL) {
        fprintf(stderr, "host_create: %s\n", host_error());
        return 2;
    }
    if (portable_input_time_host_init(&input, host, &clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_set_clock_refresh(&input,
            refresh_and_maybe_inject, &service) != PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&input) != PORTABLE_INPUT_TIME_OK)
        goto cleanup;

    /* An empty BIOS availability check now cooperatively refreshes host time. */
    before_ticks = sim_timing_tick_count(&clock);
    if (f_1F58_0038() != 0 || service.calls != 1 ||
        sim_timing_tick_count(&clock) == before_ticks)
        goto cleanup;

    /* SDL is ingested once in FIFO order. Repeated BIOS peeks do not consume
     * the first key, and the separate source event FIFO remains intact. */
    if (!push_key(SDLK_A, SDL_SCANCODE_A) || !push_mouse() ||
        !push_key(SDLK_B, SDL_SCANCODE_B))
        goto cleanup;
    if ((uint16_t)f_1F58_0038() != UINT16_C(0x1e61) ||
        (uint16_t)f_1F58_0038() != UINT16_C(0x1e61) ||
        f_1F58_0090() != (int16_t)'a' ||
        (uint16_t)f_1F58_0038() != UINT16_C(0x3062) ||
        f_1F58_0090() != (int16_t)'b')
        goto cleanup;
    if (portable_input_time_host_poll_event(&input, &events[0]) != 1 ||
        portable_input_time_host_poll_event(&input, &events[1]) != 1 ||
        portable_input_time_host_poll_event(&input, &events[2]) != 1 ||
        events[0].kind != HOST_EVENT_KEY_DOWN || events[0].key != 0x1e61 ||
        events[1].kind != HOST_EVENT_MOUSE_DOWN ||
        events[1].button != SDL_BUTTON_LEFT ||
        events[2].kind != HOST_EVENT_KEY_DOWN || events[2].key != 0x3062)
        goto cleanup;

    /* The blocking BIOS read yields through the same refresh boundary. The
     * second yield injects Escape; no event is consumed by the empty first
     * iteration, and the BIOS path returns it as ASCII 27. */
    before_calls = service.calls;
    service.inject_escape_on_call = before_calls + 2;
    if (f_1F58_0090() != 27 ||
        service.calls < service.inject_escape_on_call ||
        portable_input_time_host_poll_event(&input, &events[0]) != 1 ||
        events[0].kind != HOST_EVENT_KEY_DOWN || events[0].key != 0x011b ||
        portable_input_time_host_poll_event(&input, &events[0]) != 0)
        goto cleanup;

    result = 0;
cleanup:
    portable_input_time_host_shutdown(&input);
    host_destroy(host);
    if (result == 0)
        puts("SDL input/time cooperative smoke passed: refresh, FIFO peek, and delayed BIOS read");
    return result;
}
