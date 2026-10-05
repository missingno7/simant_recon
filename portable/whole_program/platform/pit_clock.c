#include "pit_clock.h"

#include <limits.h>
#include <stddef.h>

#define NS_PER_SECOND UINT64_C(1000000000)
#define DOS_AUDIO_PIT_DIVISOR UINT32_C(0x00d6)
#define DOS_AUDIO_CHAIN_INTERVAL UINT32_C(0x0132)
#define DOS_BIOS_PIT_DIVISOR UINT32_C(65536)

SimTimingStatus sim_timing_clock_init(SimTimingClock *clock,
                                      uint32_t pit_input_numerator,
                                      uint32_t pit_input_denominator,
                                      uint32_t pit_divisor_counts,
                                      uint32_t interrupts_per_tick)
{
    SimTimingStatus status;
    if (clock == NULL)
        return SIM_TIMING_INVALID_ARGUMENT;
    status = sim_timing_clock_configure_rate(clock, pit_input_numerator,
        pit_input_denominator, pit_divisor_counts, interrupts_per_tick);
    if (status != SIM_TIMING_OK)
        return status;
    clock->tick_count = 0;
    clock->tick_count_enabled = 1;
    return SIM_TIMING_OK;
}

SimTimingStatus sim_timing_clock_configure_rate(SimTimingClock *clock,
                                                uint32_t pit_input_numerator,
                                                uint32_t pit_input_denominator,
                                                uint32_t pit_divisor_counts,
                                                uint32_t interrupts_per_tick)
{
    if (clock == NULL)
        return SIM_TIMING_INVALID_ARGUMENT;
    if (pit_input_numerator == 0 || pit_input_denominator == 0 ||
        pit_input_numerator < pit_input_denominator ||
        pit_divisor_counts == 0 || interrupts_per_tick == 0)
        return SIM_TIMING_INVALID_CLOCK;
    clock->pit_input_numerator = pit_input_numerator;
    clock->pit_input_denominator = pit_input_denominator;
    clock->pit_divisor_counts = pit_divisor_counts;
    clock->interrupts_per_tick = interrupts_per_tick;
    clock->pit_fraction = 0;
    clock->ns_fraction = 0;
    return SIM_TIMING_OK;
}

SimTimingStatus sim_timing_clock_init_audio(SimTimingClock *clock,
                                            uint32_t pit_input_numerator,
                                            uint32_t pit_input_denominator)
{
    return sim_timing_clock_init(clock, pit_input_numerator,
                                 pit_input_denominator, DOS_AUDIO_PIT_DIVISOR,
                                 DOS_AUDIO_CHAIN_INTERVAL);
}

SimTimingStatus sim_timing_clock_init_bios(SimTimingClock *clock,
                                           uint32_t pit_input_numerator,
                                           uint32_t pit_input_denominator)
{
    return sim_timing_clock_init(clock, pit_input_numerator,
                                 pit_input_denominator, DOS_BIOS_PIT_DIVISOR, 1);
}

void sim_timing_set_tick_count_enabled(SimTimingClock *clock, int enabled)
{
    if (clock != NULL)
        clock->tick_count_enabled = enabled != 0;
}

SimTimingStatus sim_timing_advance_nanoseconds(SimTimingClock *clock,
                                               uint64_t elapsed_nanoseconds)
{
    uint64_t seconds, nanos, whole_clocks, fractional_numerator;
    uint64_t fractional_denominator, rate_remainder, per_second_fraction;
    uint64_t period_clocks, elapsed_clocks, completed_ticks;

    if (clock == NULL)
        return SIM_TIMING_INVALID_ARGUMENT;
    if (clock->pit_input_numerator == 0 || clock->pit_input_denominator == 0 ||
        clock->pit_divisor_counts == 0 ||
        clock->interrupts_per_tick == 0)
        return SIM_TIMING_INVALID_CLOCK;

    seconds = elapsed_nanoseconds / NS_PER_SECOND;
    nanos = elapsed_nanoseconds % NS_PER_SECOND;
    rate_remainder = clock->pit_input_numerator % clock->pit_input_denominator;
    if (seconds > UINT64_MAX /
        (clock->pit_input_numerator / clock->pit_input_denominator))
        return SIM_TIMING_OVERFLOW;
    whole_clocks = seconds *
        (clock->pit_input_numerator / clock->pit_input_denominator);
    fractional_denominator = NS_PER_SECOND * clock->pit_input_denominator;
    if (rate_remainder != 0 &&
        seconds > UINT64_MAX / (rate_remainder * NS_PER_SECOND))
        return SIM_TIMING_OVERFLOW;
    per_second_fraction = seconds * rate_remainder * NS_PER_SECOND;
    if (clock->ns_fraction > UINT64_MAX - per_second_fraction ||
        nanos > (UINT64_MAX - clock->ns_fraction - per_second_fraction) /
                clock->pit_input_numerator)
        return SIM_TIMING_OVERFLOW;
    fractional_numerator = per_second_fraction +
        nanos * clock->pit_input_numerator + clock->ns_fraction;
    if (whole_clocks > UINT64_MAX - fractional_numerator / fractional_denominator)
        return SIM_TIMING_OVERFLOW;
    whole_clocks += fractional_numerator / fractional_denominator;
    clock->ns_fraction = fractional_numerator % fractional_denominator;

    if (clock->pit_divisor_counts > UINT64_MAX / clock->interrupts_per_tick)
        return SIM_TIMING_INVALID_CLOCK;
    period_clocks = (uint64_t)clock->pit_divisor_counts *
                    clock->interrupts_per_tick;
    if (whole_clocks > UINT64_MAX - clock->pit_fraction)
        return SIM_TIMING_OVERFLOW;
    elapsed_clocks = whole_clocks + clock->pit_fraction;
    completed_ticks = elapsed_clocks / period_clocks;
    clock->pit_fraction = elapsed_clocks % period_clocks;
    if (clock->tick_count_enabled)
        clock->tick_count = (clock->tick_count + completed_ticks) & UINT32_MAX;
    return SIM_TIMING_OK;
}

uint32_t sim_timing_tick_count(const SimTimingClock *clock)
{
    return clock == NULL ? 0 : (uint32_t)clock->tick_count;
}

