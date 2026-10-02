#include "../../game/timing.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define PIT_NUM UINT32_C(14318180)
#define PIT_DEN UINT32_C(12)
#define AUDIO_PERIOD (UINT64_C(0x00d6) * UINT64_C(0x0132))
#define NS_PER_SEC UINT64_C(1000000000)

static void test_audio_rational_clock(void)
{
    SimTimingClock a, split;
    uint64_t ten_audio_ticks = AUDIO_PERIOD * 10;
    uint64_t ns = (ten_audio_ticks * NS_PER_SEC * PIT_DEN + PIT_NUM - 1) / PIT_NUM;
    assert(sim_timing_clock_init_audio(&a, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    assert(sim_timing_clock_init_audio(&split, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&a, ns) == SIM_TIMING_OK);
    assert(sim_timing_tick_count(&a) == 10);
    assert(sim_timing_mac_tick_count(&a) == 30);

    /* Splitting elapsed host time must preserve exact rational phase. */
    assert(sim_timing_advance_nanoseconds(&split, ns / 3) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&split, ns / 3) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&split, ns - 2 * (ns / 3)) == SIM_TIMING_OK);
    assert(split.tick_count == a.tick_count);
    assert(split.pit_fraction == a.pit_fraction);
    assert(split.ns_fraction == a.ns_fraction);
}

static void test_audio_rate_differs_from_restored_bios(void)
{
    SimTimingClock audio, bios;
    uint64_t two_audio_periods_ns =
        (AUDIO_PERIOD * 2 * NS_PER_SEC * PIT_DEN + PIT_NUM - 1) / PIT_NUM;
    assert(sim_timing_clock_init_audio(&audio, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    assert(sim_timing_clock_init_bios(&bios, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&audio, two_audio_periods_ns) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&bios, two_audio_periods_ns) == SIM_TIMING_OK);
    assert(audio.tick_count == 2);
    assert(bios.tick_count == 1);
    /* This near-boundary positive/negative pair rejects a fixed 18.2Hz shortcut. */
}

static void test_tick_counter_freeze_is_separate_from_game_pause(void)
{
    SimTimingClock clock;
    uint64_t period_ns = (AUDIO_PERIOD * NS_PER_SEC * PIT_DEN + PIT_NUM - 1) / PIT_NUM;
    assert(sim_timing_clock_init_audio(&clock, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    sim_timing_set_tick_count_enabled(&clock, 0);
    assert(sim_timing_advance_nanoseconds(&clock, period_ns * 2) == SIM_TIMING_OK);
    assert(sim_timing_tick_count(&clock) == 0);
    assert(sim_timing_simulation_permitted(1, 0) == 0);
    assert(sim_timing_simulation_permitted(1, 1) == 1);
    sim_timing_set_tick_count_enabled(&clock, 1);
    assert(sim_timing_advance_nanoseconds(&clock, period_ns) == SIM_TIMING_OK);
    assert(sim_timing_tick_count(&clock) == 1);
}

static void test_timer_reprogram_preserves_tick_count(void)
{
    SimTimingClock clock;
    uint64_t audio_period_ns =
        (AUDIO_PERIOD * NS_PER_SEC * PIT_DEN + PIT_NUM - 1) / PIT_NUM;
    uint64_t bios_period_ns =
        (UINT64_C(65536) * NS_PER_SEC * PIT_DEN + PIT_NUM - 1) / PIT_NUM;
    assert(sim_timing_clock_init_audio(&clock, PIT_NUM, PIT_DEN) == SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&clock, audio_period_ns) == SIM_TIMING_OK);
    assert(clock.tick_count == 1);
    assert(sim_timing_clock_configure_rate(&clock, PIT_NUM, PIT_DEN, 65536, 1) == SIM_TIMING_OK);
    assert(clock.tick_count == 1);
    assert(sim_timing_advance_nanoseconds(&clock, bios_period_ns) == SIM_TIMING_OK);
    assert(clock.tick_count == 2);
}

static void test_source_deadlines_pause_catchup_and_presentation(void)
{
    SimTimingScheduler scheduler = {0, 0, 0};
    assert(sim_timing_speed_delay(0) == 21);
    assert(sim_timing_speed_delay(1) == 7);
    assert(sim_timing_speed_delay(2) == 0);
    assert(sim_timing_speed_delay(3) == -1);
    assert(sim_timing_take_due(&scheduler, 100, 0, 0, 0) == 1);
    assert(scheduler.deadline_mac == 121);
    assert(sim_timing_take_due(&scheduler, 162, 0, 0, 0) == 2);
    assert(scheduler.deadline_mac == 163);
    assert(sim_timing_take_due(&scheduler, 162, 1, 0, 0) == 1);
    assert(scheduler.deadline_mac == 169);
    assert(sim_timing_take_due(&scheduler, 168, 1, 0, 0) == 0);
    assert(sim_timing_take_due(&scheduler, 169, 1, 0, 0) == 1);
    assert(sim_timing_take_due(&scheduler, 1000, 1, 1, 0) == 0);
    assert(sim_timing_take_due(&scheduler, 1000, 1, 1, 1) == 1);
    assert(sim_timing_take_due(&scheduler, 1000, 2, 0, 0) == 1);
    assert(sim_timing_take_due(&scheduler, 1000, 3, 0, 0) == 1);
    assert(sim_timing_presentation_due(2, 7));
    assert(sim_timing_presentation_due(3, 8));
    assert(!sim_timing_presentation_due(3, 7));
}

static void test_invalid_configs_and_wrap_comparison(void)
{
    SimTimingClock clock;
    assert(sim_timing_clock_init_audio(&clock, 0, PIT_DEN) == SIM_TIMING_INVALID_CLOCK);
    assert(sim_timing_clock_init(&clock, PIT_NUM, PIT_DEN, 1, 0) == SIM_TIMING_INVALID_CLOCK);
    assert(sim_timing_deadline_reached(2, UINT32_MAX - 1));
    assert(!sim_timing_deadline_reached(UINT32_MAX - 1, 2));
}

int main(void)
{
    test_audio_rational_clock();
    test_audio_rate_differs_from_restored_bios();
    test_tick_counter_freeze_is_separate_from_game_pause();
    test_timer_reprogram_preserves_tick_count();
    test_source_deadlines_pause_catchup_and_presentation();
    test_invalid_configs_and_wrap_comparison();
    puts("timing tests passed");
    return 0;
}
