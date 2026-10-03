#include "../../whole_program/platform/m1b73_main_input.h"

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdio.h>

struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, NULL, (int16_t)0x91b0,
                       5, 0, 10, 0 };
int16_t g_5FF0 = PORTABLE_M1B73_EVENT_SLOTS;

static int near_18(uint32_t delta)
{
    return delta >= 15 && delta <= 22;
}

int main(void)
{
    SimTimingClock game_clock, bios_clock, mismatch_clock;
    PortableInputTimeHost input_host;
    PortableM1B73Events events;
    PortableM1B73Event records[PORTABLE_M1B73_EVENT_SLOTS] = {{0}};
    uint8_t shift_state = 0;
    uint32_t game_before, game_after, bios_before, bios_after;
    Host *host;

    fprintf(stderr, "step0\n");
    if (sim_timing_clock_init_audio(&game_clock, UINT32_C(14318180), 12) !=
            SIM_TIMING_OK ||
        sim_timing_clock_init_audio(&bios_clock, UINT32_C(14318180), 12) !=
            SIM_TIMING_OK ||
        portable_input_time_host_init_clocks(&input_host, NULL,
            &game_clock, &bios_clock) != PORTABLE_INPUT_TIME_BAD_ARGUMENT)
        return 1;
    host = host_create("m1B73 dual clock", 1);
    fprintf(stderr, "step1 %p\n", (void *)host);
    if (host == NULL)
        return 2;
    if (portable_input_time_host_init_clocks(&input_host, host, &game_clock,
            &bios_clock) != PORTABLE_INPUT_TIME_OK ||
        !input_host.dual_clock_binding || input_host.clock != &game_clock ||
        input_host.bios_clock != &bios_clock ||
        portable_input_time_host_bind(&input_host) != PORTABLE_INPUT_TIME_OK ||
        !portable_m1b73_bind_source_main_input(&events, &input_host,
            &game_clock, &shift_state, records, PORTABLE_M1B73_EVENT_SLOTS))
        goto fail;
    fprintf(stderr, "step2\n");

    game_clock.tick_count = UINT32_C(0x1000);
    bios_clock.tick_count = UINT32_C(0x2000);
    sim_timing_set_tick_count_enabled(&bios_clock, 0);
    if (f_1B73_0511(), portable_input_time_host_refresh_clock(&input_host) !=
            PORTABLE_INPUT_TIME_OK || !bios_clock.tick_count_enabled)
        goto fail_bound;
    fprintf(stderr, "step3\n");
    sim_timing_set_tick_count_enabled(&game_clock, 0);
    game_before = TickCount();
    bios_before = f_1F58_0006();
    input_host.monotonic_refresh.last_ns = host_time_ns() -
        UINT64_C(3000000000);
    bios_after = f_1F58_0006();
    game_after = TickCount();
    fprintf(stderr, "step4 %u %u %u %u\n", game_before, game_after,
            bios_before, bios_after);
    if (game_before != UINT32_C(0x1000) || game_after != game_before ||
        (uint32_t)(bios_after - bios_before) < 45 ||
        (uint32_t)(bios_after - bios_before) > 62)
        goto fail_bound;

    f_1B73_0518();
    game_before = TickCount();
    bios_before = f_1F58_0006();
    input_host.monotonic_refresh.last_ns = host_time_ns() -
        UINT64_C(1000000000);
    game_after = TickCount();
    bios_after = f_1F58_0006();
    fprintf(stderr, "step5 %u %u %u %u\n", game_before, game_after,
            bios_before, bios_after);
    if (!near_18((uint32_t)(game_after - game_before)) ||
        !near_18((uint32_t)(bios_after - bios_before)))
        goto fail_bound;

    game_clock.tick_count = UINT32_MAX - 3u;
    bios_clock.tick_count = UINT32_MAX - 3u;
    input_host.monotonic_refresh.last_ns = host_time_ns() -
        UINT64_C(1000000000);
    game_after = TickCount();
    bios_after = f_1F58_0006();
    fprintf(stderr, "step6 %u %u\n", game_after, bios_after);
    if (game_after >= 64 || bios_after >= 64)
        goto fail_bound;

    if (sim_timing_clock_init_bios(&mismatch_clock,
            UINT32_C(14318180), 12) != SIM_TIMING_OK ||
        portable_input_time_host_init_clocks(&input_host, host, &game_clock,
            &mismatch_clock) != PORTABLE_INPUT_TIME_BAD_ARGUMENT)
        goto fail_bound;

    portable_m1b73_unbind_source_main_input(&events);
    portable_input_time_host_shutdown(&input_host);
    host_destroy(host);
    puts("PASS dual clock: disabled private counter, advancing BIOS, no catch-up, rollover");
    return 0;

fail_bound:
    portable_m1b73_unbind_source_main_input(&events);
fail:
    portable_input_time_host_shutdown(&input_host);
    host_destroy(host);
    return 3;
}
