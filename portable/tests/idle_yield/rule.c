/* Shared golden vectors for an independent DOS ideal-machine implementation. */
#include "portable/whole_program/platform/input_time.h"
#include "portable/whole_program/platform/pit_clock.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    static const struct { const char *read; unsigned ms, tick, irqs; } vectors[] = {
        {"TickCount", 1, 0, 5}, {"TickCount", 2, 0, 10},
        {"host_ticks", 3, 0, 15}, {"portable_m1b73_source_countdown_get", 4, 0, 20},
        {"input_event_count", 5, 0, 25}, {"host_key_available", 6, 0, 30},
        {"kbd_scan_state", 7, 0, 35}, {"kbd_scroll_lock_state", 8, 0, 40},
        {"dos_keyboard_modifiers", 9, 0, 45}, {"host_read_key_blocking", 10, 1, 50},
        {"portable_m1b73_sdl_application_input_present", 10, 1, 50},
        {"portable_m1b73_source_countdown_set", 10, 1, 50},
        {"mouse_show_cursor", 10, 1, 50}, {"drain_host_observations", 10, 1, 50},
        {"portable_input_time_host_get_input_state", 11, 1, 55},
        {"mouse_refresh_cursor", 12, 1, 60}, {NULL, 12, 1, 60}
    };
    SimTimingClock clock;
    uint64_t ns = 0;
    unsigned i;
    /* Synthetic 1 MHz PIT, 10000-count IRQ chain, 200 us sound ISR. */
    assert(sim_timing_clock_init(&clock, 1000000, 1, 10000, 1) == SIM_TIMING_OK);
    for (i = 0; i < sizeof(vectors) / sizeof(vectors[0]); ++i) {
        uint64_t delta = portable_input_time_read_quantum(vectors[i].read, 1000000);
        ns += delta;
        assert(sim_timing_advance_nanoseconds(&clock, delta) == SIM_TIMING_OK);
        assert(ns == (uint64_t)vectors[i].ms * 1000000);
        assert(sim_timing_tick_count(&clock) == vectors[i].tick);
        assert(ns / 200000 == vectors[i].irqs);
    }
    assert(portable_input_time_read_quantum("TickCount", 1) == 1);
    assert(portable_input_time_read_quantum("internal_callback", 1000000) == 0);
    sim_timing_set_tick_count_enabled(&clock, 0);
    assert(sim_timing_advance_nanoseconds(&clock, 100000000) == SIM_TIMING_OK);
    assert(sim_timing_tick_count(&clock) == 1);
    puts("PASS pure golden read vectors; no SDL, wall clock, input or audio state");
    return 0;
}
