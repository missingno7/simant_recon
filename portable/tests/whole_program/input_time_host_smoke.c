#include "../../whole_program/platform/sdl3/input_time_host.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

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
    Host *host;
    HostEvent first, second;
    uint8_t modifiers = 0;
    int16_t available;

    if (sim_timing_clock_init_bios(&clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK)
        return 1;
    clock.tick_count = UINT32_C(0x89abcdef);
    host = host_create("input/time host smoke", 1);
    if (host == NULL) {
        fprintf(stderr, "host_create: %s\n", host_error());
        return 2;
    }
    if (portable_input_time_host_init(&input, host, &clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&input) != PORTABLE_INPUT_TIME_OK)
        return 3;

    portable_input_time_host_set_keyboard_flags(
        &input, PORTABLE_INPUT_TIME_HOST_NUMLOCK_MASK);
    if (!push_keydown() || !push_mouse_down())
        return 4;
    available = f_1F58_0038();
    if ((uint16_t)available != UINT16_C(0x1e61) ||
        (portable_input_time_host_keyboard_flags(&input) &
         PORTABLE_INPUT_TIME_HOST_NUMLOCK_MASK) != 0)
        return 5;
    if (TickCount() != UINT32_C(0x89abcdef) ||
        TickCount() != sim_timing_tick_count(&clock))
        return 6;
    if (!portable_input_time_host_dos_modifiers(&input, &modifiers))
        return 7;
    if (modifiers & UINT8_C(0xf0))
        return 8;

    if (portable_input_time_host_poll_event(&input, &first) != 1 ||
        portable_input_time_host_poll_event(&input, &second) != 1 ||
        first.kind != HOST_EVENT_KEY_DOWN || first.key != UINT16_C(0x1e61) ||
        second.kind != HOST_EVENT_MOUSE_DOWN ||
        second.button != SDL_BUTTON_LEFT)
        return 9;
    if (f_1F58_005A() != (int16_t)'a')
        return 10;

    portable_input_time_host_shutdown(&input);
    host_destroy(host);
    puts("SDL input/time host smoke passed; key and mouse events retained in order");
    return 0;
}
