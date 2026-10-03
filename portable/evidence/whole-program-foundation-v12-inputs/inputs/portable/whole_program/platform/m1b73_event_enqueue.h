#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_EVENT_ENQUEUE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_EVENT_ENQUEUE_H

#include <stdint.h>

/* Minimal source-C ABI surface: keep unrelated BIOS/event record declarations
 * in their owners, since this adapter is only for m1B73_030F callsites. */
void f_1B73_030F(int16_t bx, int16_t es, int16_t ax,
                 int16_t cx, int16_t dx);
void portable_m1b73_event_enqueue_four_word_command(
    int16_t bx, int16_t es, int16_t ax, int16_t cx);

#endif
