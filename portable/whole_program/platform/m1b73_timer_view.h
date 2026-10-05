#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_TIMER_VIEW_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_TIMER_VIEW_H

#include "../types/timer.h"

/* Borrowed fields and records from the canonical input descriptor. */
typedef struct PortableM1B73TimerQueueView {
    int16_t *count;        /* g_5FF2.r.left */
    int16_t *write_index;  /* g_5FF2.r.top */
    int16_t *read_index;   /* g_5FF2.r.right */
    int16_t *capacity;     /* g_5FF0 */
    struct Event *records;
    uint16_t record_slots;
} PortableM1B73TimerQueueView;

int portable_m1b73_get_source_timer_queue_view(
    PortableM1B73TimerQueueView *view);

#endif
