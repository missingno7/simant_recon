#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_COUNTDOWN_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_COUNTDOWN_H

#include <stdint.h>

/* Lightweight m208F source adapter; intentionally avoids Timer/Rect and
 * graphics headers so ordinary recovered TUs can include it safely. */
void portable_m1b73_source_countdown_wait(int16_t source_ticks);
void portable_m1b73_source_countdown_write(int16_t source_ticks);
int16_t portable_m1b73_source_countdown_is_zero(void);

#endif
