#ifndef SIMANT_WHOLE_PROGRAM_STATE_MAIN_LOOP_COUNTER_H
#define SIMANT_WHOLE_PROGRAM_STATE_MAIN_LOOP_COUNTER_H

#include <stdint.h>

/* Source root:m15F8 frame counter. It is incremented once per outer UI loop
 * and read by S06 time-window logic; the original DGROUP cell starts at zero. */
extern int32_t fd_50F6_383A;

#endif
