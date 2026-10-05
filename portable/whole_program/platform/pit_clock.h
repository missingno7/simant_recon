#ifndef SIMANT_PLATFORM_PIT_CLOCK_H
#define SIMANT_PLATFORM_PIT_CLOCK_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* The BIOS timer source is modeled from rational PIT input clocks, not a
 * guessed frame rate. `pit_input_numerator/denominator` is a platform
 * assumption (nominal PC PIT crystal ratio is 14318180/12, not proven exact by
 * the game). The audio driver changes PIT divisor and chains old INT 08h only
 * after a source-provided number of mixer interrupts. */
typedef struct SimTimingClock {
    uint32_t pit_input_numerator;
    uint32_t pit_input_denominator;
    uint32_t pit_divisor_counts; /* PIT programming value 0 is represented as 65536. */
    uint32_t interrupts_per_tick; /* old INT 08h chaining interval */
    uint64_t pit_fraction;        /* clocks into the current logical tick */
    uint64_t ns_fraction;         /* numerator remainder while converting ns to PIT clocks */
    uint64_t tick_count;           /* source TickCount counter, modulo 2^32 when read */
    uint8_t tick_count_enabled;    /* INT 08h handler's tick_count_on flag */
} SimTimingClock;

typedef enum SimTimingStatus {
    SIM_TIMING_OK = 0,
    SIM_TIMING_INVALID_ARGUMENT = 1,
    SIM_TIMING_INVALID_CLOCK = 2,
    SIM_TIMING_OVERFLOW = 3
} SimTimingStatus;

/* Source values: PIT input clock is an explicit hardware assumption; audio
 * setup passes 0xD6 and 0x132 to f_28BC_046B/0488. */
SimTimingStatus sim_timing_clock_init(SimTimingClock *clock,
                                      uint32_t pit_input_numerator,
                                      uint32_t pit_input_denominator,
                                      uint32_t pit_divisor_counts,
                                      uint32_t interrupts_per_tick);
/* Changes the PIT source while preserving TickCount and its enable flag. */
SimTimingStatus sim_timing_clock_configure_rate(SimTimingClock *clock,
                                                uint32_t pit_input_numerator,
                                                uint32_t pit_input_denominator,
                                                uint32_t pit_divisor_counts,
                                                uint32_t interrupts_per_tick);
SimTimingStatus sim_timing_clock_init_audio(SimTimingClock *clock,
                                            uint32_t pit_input_numerator,
                                            uint32_t pit_input_denominator);
SimTimingStatus sim_timing_clock_init_bios(SimTimingClock *clock,
                                           uint32_t pit_input_numerator,
                                           uint32_t pit_input_denominator);
void sim_timing_set_tick_count_enabled(SimTimingClock *clock, int enabled);
SimTimingStatus sim_timing_advance_nanoseconds(SimTimingClock *clock,
                                               uint64_t elapsed_nanoseconds);
uint32_t sim_timing_tick_count(const SimTimingClock *clock);

#ifdef __cplusplus
}
#endif
#endif
