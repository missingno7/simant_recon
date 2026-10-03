#include "m1b73_timer_view.h"

#include <stddef.h>

extern struct Timer g_5FF2;
extern int16_t g_5FF0;

int portable_m1b73_get_source_timer_queue_view(
    PortableM1B73TimerQueueView *view)
{
    if (view == NULL)
        return 0;
    view->count = &g_5FF2.r.left;
    view->write_index = &g_5FF2.r.top;
    view->read_index = &g_5FF2.r.right;
    view->capacity = &g_5FF0;
    return 1;
}
