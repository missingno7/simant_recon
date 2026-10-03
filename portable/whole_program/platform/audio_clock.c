#include "audio_clock.h"

uint64_t portable_whole_audio_mode1_steps_from_ns(uint64_t elapsed_ns)
{
    const uint64_t seconds = elapsed_ns / UINT64_C(1000000000);
    const uint64_t nanoseconds = elapsed_ns % UINT64_C(1000000000);
    const uint64_t numerator = PORTABLE_WHOLE_AUDIO_MODE1_PIT_NUMERATOR;
    const uint64_t denominator = PORTABLE_WHOLE_AUDIO_MODE1_PIT_DENOMINATOR;
    const uint64_t whole_numerator = seconds * numerator;
    const uint64_t fractional_numerator =
        (whole_numerator % denominator) * UINT64_C(1000000000) +
        nanoseconds * numerator;

    return whole_numerator / denominator +
           fractional_numerator / (denominator * UINT64_C(1000000000));
}
