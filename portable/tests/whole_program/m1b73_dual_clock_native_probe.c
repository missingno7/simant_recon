#include "../../whole_program/platform/m1b73_main_input.h"
#include "../../whole_program/platform/m1b73_timer_view.h"
#include "../../whole_program/types/timer.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

struct Timer g_5FF2 = {{0, 0, 0, 0xff}, NULL, (int16_t)0x91b0, 5, 0, 10, 0};
int16_t g_5FF0 = PORTABLE_M1B73_EVENT_SLOTS;

static uint64_t fake_now_ns;

uint64_t host_time_ns(void) { return fake_now_ns; }
int host_poll_event(Host *host, HostEvent *event)
{ (void)host; (void)event; abort(); }
int host_get_input_state(Host *host, HostInputState *state)
{ (void)host; (void)state; abort(); }
int host_is_dos_scan_down(Host *host, uint8_t scan, int *down)
{ (void)host; (void)scan; (void)down; abort(); }
void host_wait_ms(uint32_t milliseconds) { (void)milliseconds; abort(); }

static int close_to(uint32_t actual, uint32_t expected)
{ return actual >= expected - 3u && actual <= expected + 3u; }

int main(void)
{
    SimTimingClock game_clock, bios_clock, mismatch_clock;
    PortableInputTimeHost input_host;
    PortableM1B73Events events;
    PortableM1B73Event records[PORTABLE_M1B73_EVENT_SLOTS] = {{0}};
    uint8_t shift_state = 0;
    uint32_t game_before, game_after, bios_before, bios_after;
    Host *host = (Host *)(uintptr_t)1;

    fake_now_ns = 0;
    if (sim_timing_clock_init_audio(&game_clock, UINT32_C(14318180), 12) !=
            SIM_TIMING_OK ||
        sim_timing_clock_init_audio(&bios_clock, UINT32_C(14318180), 12) !=
            SIM_TIMING_OK ||
        portable_input_time_host_init_clocks(&input_host, NULL, &game_clock,
            &bios_clock) != PORTABLE_INPUT_TIME_BAD_ARGUMENT ||
        portable_input_time_host_init_clocks(&input_host, host, &game_clock,
            &game_clock) != PORTABLE_INPUT_TIME_BAD_ARGUMENT)
        return 1;
    if (portable_input_time_host_init_clocks(&input_host, host, &game_clock,
            &bios_clock) != PORTABLE_INPUT_TIME_OK ||
        !input_host.dual_clock_binding || input_host.clock != &game_clock ||
        input_host.bios_clock != &bios_clock ||
        portable_input_time_host_bind(&input_host) != PORTABLE_INPUT_TIME_OK ||
        !portable_m1b73_bind_source_main_input(&events, &input_host,
            &game_clock, &shift_state, records, PORTABLE_M1B73_EVENT_SLOTS))
        return 2;

    game_clock.tick_count = UINT32_C(0x1000);
    bios_clock.tick_count = UINT32_C(0x2000);
    sim_timing_set_tick_count_enabled(&bios_clock, 0);
    if (portable_input_time_host_refresh_clock(&input_host) !=
            PORTABLE_INPUT_TIME_OK || !bios_clock.tick_count_enabled)
        goto fail;

    f_1B73_0511();
    fake_now_ns = UINT64_C(3000000000);
    game_before = TickCount();
    bios_before = f_1F58_0006();
    if (game_before != UINT32_C(0x1000) ||
        !close_to((uint32_t)(bios_before - UINT32_C(0x2000)), 54u) ||
        game_clock.tick_count != game_before || bios_clock.tick_count != bios_before)
        goto fail;

    fake_now_ns = UINT64_C(4000000000);
    f_1B73_0518();
    game_before = (uint32_t)game_clock.tick_count;
    bios_before = (uint32_t)bios_clock.tick_count;
    (void)TickCount();
    (void)f_1F58_0006();
    game_after = (uint32_t)game_clock.tick_count;
    bios_after = (uint32_t)bios_clock.tick_count;
    if (!close_to((uint32_t)(game_after - game_before), 18u) ||
        !close_to((uint32_t)(bios_after - bios_before), 18u))
        goto fail;

    game_clock.tick_count = UINT32_MAX - 3u;
    bios_clock.tick_count = UINT32_MAX - 3u;
    fake_now_ns = UINT64_C(5000000000);
    (void)TickCount();
    (void)f_1F58_0006();
    if (game_clock.tick_count >= 64u || bios_clock.tick_count >= 64u)
        goto fail;

    if (sim_timing_clock_init_bios(&mismatch_clock,
            UINT32_C(14318180), 12) != SIM_TIMING_OK ||
        portable_input_time_host_init_clocks(&input_host, host, &game_clock,
            &mismatch_clock) != PORTABLE_INPUT_TIME_BAD_ARGUMENT)
        goto fail;

    portable_m1b73_unbind_source_main_input(&events);
    portable_input_time_host_shutdown(&input_host);
    puts("PASS dual-clock deterministic controls: BIOS continues, private disable/re-enable, rollover");
    return 0;

fail:
    portable_m1b73_unbind_source_main_input(&events);
    portable_input_time_host_shutdown(&input_host);
    return 3;
}
