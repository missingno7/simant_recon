#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_CLOCK_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_CLOCK_H

#include <stdint.h>

/* Source m28BC mode 1 configures the PC timer with divisor 0x00d6. The
 * established BIOS PIT oscillator is 14,318,180 Hz and channel 0 divides by
 * 12 before applying that reload. Keep the exact rational source rate for
 * deadlines; SDL requires an integer presentation rate, rounded to nearest.
 */
enum {
    PORTABLE_WHOLE_AUDIO_MODE1_PIT_DIVISOR = 0x00d6,
    PORTABLE_WHOLE_AUDIO_MODE1_PIT_BASE_DIVISOR = 12,
    PORTABLE_WHOLE_AUDIO_MODE1_PRESENTATION_RATE = 5576
};

#define PORTABLE_WHOLE_AUDIO_MODE1_PIT_NUMERATOR UINT64_C(14318180)
#define PORTABLE_WHOLE_AUDIO_MODE1_PIT_DENOMINATOR \
    (UINT64_C(12) * PORTABLE_WHOLE_AUDIO_MODE1_PIT_DIVISOR)

/* Floor the exact source output-step count at elapsed monotonic nanoseconds.
 * The rational is 14,318,180 / (12*214) steps per second; it intentionally
 * does not accumulate the 5,576 Hz SDL presentation rounding error.
 */
uint64_t portable_whole_audio_mode1_steps_from_ns(uint64_t elapsed_ns);

#endif
