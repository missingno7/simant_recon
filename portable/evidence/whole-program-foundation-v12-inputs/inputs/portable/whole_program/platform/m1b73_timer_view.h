#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_TIMER_VIEW_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_TIMER_VIEW_H

#include "../types/timer.h"

/* Borrowed typed aliases for the canonical root:m1FD2 source owner. The
 * 0x91B0 DOS ring offset in g_5FF2.ticks is retired in the native lane; event
 * record storage is supplied separately by the event-provider owner. */
typedef struct PortableM1B73TimerQueueView {
    int16_t *count;        /* g_5FF2.r.left */
    int16_t *write_index;  /* g_5FF2.r.top */
    int16_t *read_index;   /* g_5FF2.r.right */
    int16_t *capacity;     /* g_5FF0 */
} PortableM1B73TimerQueueView;

int portable_m1b73_get_source_timer_queue_view(
    PortableM1B73TimerQueueView *view);

#endif
