#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_SOURCE_H

#include "m1b73_queues.h"
#include "../types/timer.h"

#include <stdint.h>

/* Source C's fd_5071_* symbols are converted to these borrowed typed views;
 * they are selectors into the one ASM queue owner, not copied records. */
PortableM1B73Queue *portable_m1b73_queue_slot(uint8_t source_slot);
extern uint16_t g_9120;
extern int16_t g_9122;
extern int16_t g_9124;
uint8_t portable_m1b73_g9120_low_byte(void);

/* Word-lowered C call surfaces for the original far ASM entrypoints. The
 * queue pointer is a native provider view; these prototypes do not claim that
 * the DOS far-pointer bit pattern is retained. */
void f_1B73_0B5B(int16_t ticks, PortableM1B73Queue *slot);
void f_1B73_0B00(struct Timer *timer, PortableM1B73Queue *slot);
void f_1B73_0AC3(struct Timer *timer, PortableM1B73Queue *slot);
void f_1B73_0BC5(int16_t ticks, PortableM1B73Queue *slot);
int16_t f_1B73_0C42(int16_t id, PortableM1B73Queue *slot,
                    struct Rect *out_rect);

#endif
