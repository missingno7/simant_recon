#include "../../whole_program/platform/sdl3/input_time_host.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct FixedRefresh {
    uint64_t elapsed_ns;
    uint32_t calls;
    int fail;
} FixedRefresh;

static int refresh_clock(void *context, SimTimingClock *clock)
{
    FixedRefresh *refresh = (FixedRefresh *)context;
    ++refresh->calls;
    return !refresh->fail &&
        sim_timing_advance_nanoseconds(clock, refresh->elapsed_ns) == SIM_TIMING_OK;
}

static int push_keydown(void)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.type = SDL_EVENT_KEY_DOWN;
    event.key.key = SDLK_A;
    event.key.mod = SDL_KMOD_NONE;
    event.key.repeat = false;
    return SDL_PushEvent(&event);
}

static int push_mouse_down(void)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    event.button.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    event.button.button = SDL_BUTTON_LEFT;
    event.button.x = 19.0f;
    event.button.y = 27.0f;
    return SDL_PushEvent(&event);
}

int main(void)
{
    SimTimingClock clock;
    PortableInputTimeHost input;
    Host *host = NULL;
    HostEvent first, second;
    FixedRefresh refresh = { UINT64_C(1000000000), 0, 0 };
    int16_t available;
    uint32_t before;
    uint8_t modifiers;
    int result = 1;

    if (sim_timing_clock_init_bios(&clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK)
        return 1;
    clock.tick_count = UINT32_C(0x89abcdef);
    host = host_create("input/time host smoke v2", 1);
    if (host == NULL) {
        fprintf(stderr, "host_create: %s\n", host_error());
        return 2;
    }
    if (portable_input_time_host_init(&input, host, &clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&input) != PORTABLE_INPUT_TIME_OK)
        goto cleanup;

    if (TickCount() != UINT32_C(0x89abcdef) ||
        TickCount() != sim_timing_tick_count(&clock))
        goto cleanup;
    /* With refresh unset, the caller-owned clock remains unchanged. */
    if (clock.tick_count != UINT32_C(0x89abcdef))
        goto cleanup;

    portable_input_time_host_set_keyboard_flags(&input, UINT8_C(0xa0));
    SDL_SetModState(SDL_KMOD_LSHIFT | SDL_KMOD_CTRL | SDL_KMOD_CAPS);
    if (dos_keyboard_modifiers() != UINT8_C(0xa6))
        goto cleanup;
    if (push_keydown() == 0 || push_mouse_down() == 0)
        goto cleanup;
    available = f_1F58_0038();
    if ((uint16_t)available != UINT16_C(0x1e61) ||
        portable_input_time_host_keyboard_flags(&input) != UINT8_C(0x86))
        goto cleanup;

    if (portable_input_time_host_poll_event(&input, &first) != 1 ||
        portable_input_time_host_poll_event(&input, &second) != 1 ||
        first.kind != HOST_EVENT_KEY_DOWN || first.key != UINT16_C(0x1e61) ||
        second.kind != HOST_EVENT_MOUSE_DOWN ||
        second.button != SDL_BUTTON_LEFT ||
        f_1F58_005A() != (int16_t)'a')
        goto cleanup;

    portable_input_time_host_shutdown(&input);
    refresh.fail = 1;
    refresh.calls = 0;
    if (portable_input_time_host_set_clock_refresh(&input, refresh_clock,
                                                   &refresh) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_refresh_clock(&input) !=
            PORTABLE_INPUT_TIME_PROVIDER_FAILED || refresh.calls != 1)
        goto cleanup_host;
    refresh.fail = 0;
    refresh.calls = 0;
    if (portable_input_time_host_bind(&input) != PORTABLE_INPUT_TIME_OK)
        goto cleanup_host;
    before = sim_timing_tick_count(&clock);
    if (TickCount() == before || refresh.calls != 1)
        goto cleanup;
    if (TickCount() == before || refresh.calls != 2)
        goto cleanup;

    {
        PortableSdlMonotonicClockRefresh monotonic;
        portable_input_time_host_shutdown(&input);
        portable_sdl_monotonic_clock_refresh_init(&monotonic);
        if (portable_input_time_host_set_clock_refresh(
                &input, portable_input_time_host_refresh_from_sdl_monotonic,
                &monotonic) != PORTABLE_INPUT_TIME_OK ||
            portable_input_time_host_bind(&input) != PORTABLE_INPUT_TIME_OK)
            goto cleanup_host;
        before = sim_timing_tick_count(&clock);
        host_wait_ms(80);
        (void)TickCount();
        if (sim_timing_tick_count(&clock) < before)
            goto cleanup;
        portable_input_time_host_shutdown(&input);
        if (portable_input_time_host_set_clock_refresh(&input, NULL, NULL) !=
                PORTABLE_INPUT_TIME_OK)
            goto cleanup_host;
    }
    if (portable_input_time_host_current_modifiers(&modifiers) != 0)
        goto cleanup_host;
    result = 0;

cleanup:
    portable_input_time_host_shutdown(&input);
cleanup_host:
    host_destroy(host);
    if (result == 0)
        puts("SDL input/time v2 passed: TickCount refresh, modifiers, and retained event order");
    return result;
}
