#include "../../whole_program/platform/m1b73_main_input.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, NULL, (int16_t)0x91b0,
                       5, 0, 10, 0 };
int16_t g_5FF0 = PORTABLE_M1B73_EVENT_SLOTS;

static int push_ctrl(uint32_t type)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = type;
    event.key.type = type;
    event.key.key = SDLK_LCTRL;
    event.key.scancode = SDL_SCANCODE_LCTRL;
    event.key.mod = SDL_KMOD_NONE;
    return SDL_PushEvent(&event);
}

int main(void)
{
    SimTimingClock game_clock, bios_clock;
    PortableInputTimeHost host_input;
    PortableM1B73Events events;
    PortableM1B73Event records[PORTABLE_M1B73_EVENT_SLOTS] = {{0}};
    PortableM1B73Event popped;
    HostEvent host_event;
    Host *host = NULL;
    uint8_t shift_state = 0;

    if (sim_timing_clock_init_audio(&game_clock, UINT32_C(14318180), 12) !=
            SIM_TIMING_OK ||
        sim_timing_clock_init_audio(&bios_clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK)
        return 1;
    host = host_create("m1B73 main input binding", 1);
    if (host == NULL)
        return 2;
    if (portable_input_time_host_init_clocks(&host_input, host, &game_clock,
            &bios_clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&host_input) != PORTABLE_INPUT_TIME_OK ||
        !portable_m1b73_bind_source_main_input(&events, &host_input, &game_clock,
            &shift_state, records, PORTABLE_M1B73_EVENT_SLOTS))
        goto fail;

    if (f_1B73_032A() != 0 || f_1B73_032E(&popped) != -1)
        goto fail_bound;
    if (!push_ctrl(SDL_EVENT_KEY_DOWN) ||
        portable_m1b73_poll_host_event(&events, &host_event) != 1 ||
        host_event.kind != HOST_EVENT_KEY_DOWN || f_1B73_0A30(0x1d) != 1)
        goto fail_bound;
    if (!push_ctrl(SDL_EVENT_KEY_UP) ||
        portable_m1b73_poll_host_event(&events, &host_event) != 1 ||
        host_event.kind != HOST_EVENT_KEY_UP || f_1B73_0A30(0x1d) != 0)
        goto fail_bound;

    portable_input_time_host_set_keyboard_flags(&host_input, UINT8_C(0x10));
    if (f_1B73_0EEE() != 0x10)
        goto fail_bound;
    portable_input_time_host_set_keyboard_flags(&host_input, 0);
    if (f_1B73_0EEE() != 0)
        goto fail_bound;

    records[0].what = 0x1234;
    if (!portable_m1b73_event_enqueue_registers(&events, 0x0007, 0x1122,
            0x3344, 0x5566, 0x7788) || f_1B73_032A() != 1 ||
        f_1B73_032E(&popped) != 0 || popped.what != 0x1234 ||
        popped.h != 0x1122 || popped.v != 0x3344 || popped.code != 0x5566 ||
        popped.xE != (int16_t)0x7788)
        goto fail_bound;

    portable_m1b73_unbind_source_main_input(&events);
    portable_input_time_host_shutdown(&host_input);
    host_destroy(host);
    puts("PASS original m1B73 C-facing queue/key/NumLock aliases on shared SDL binding");
    return 0;

fail_bound:
    portable_m1b73_unbind_source_main_input(&events);
fail:
    portable_input_time_host_shutdown(&host_input);
    host_destroy(host);
    return 3;
}
