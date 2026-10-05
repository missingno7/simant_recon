#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_RUNTIME_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_RUNTIME_H

#include "m1b73_events.h"
#include "m1b73_mouse.h"
#include "m1b73_queue_ops.h"

#include <stdint.h>

typedef int (*PortableM1B73GraphicsCursorMode)(
    void *context, uint8_t mode, int16_t *source_ax);

/* One application-lifetime adapter joining the real input/event, mouse, and
 * graphics owners. Canonical ASM cells own the scan table, hook flag and
 * cursor counter; this object owns provider bindings only. */
typedef struct PortableM1B73QueueRuntime {
    PortableM1B73Events *events;          /* borrowed shared event/timing owner */
    PortableM1B73MouseProvider *mouse;    /* borrowed active SDL mouse owner */
    void *graphics_context;
    PortableM1B73GraphicsCursorMode graphics_cursor_mode;
    uint8_t bound;
} PortableM1B73QueueRuntime;

/* Binds only after the same SDL input owner, source event/timer owner, and
 * mouse provider are live. The graphics callback must be the actual
 * source-backed D4B mode renderer (for example the graphics cursor adapter),
 * not a test success stub. */
int portable_m1b73_queue_runtime_bind(
    PortableM1B73QueueRuntime *runtime,
    PortableM1B73Events *events,
    PortableM1B73MouseProvider *mouse,
    void *graphics_context,
    PortableM1B73GraphicsCursorMode graphics_cursor_mode);
void portable_m1b73_queue_runtime_unbind(
    PortableM1B73QueueRuntime *runtime);

/* The source keyboard table stores 0 for down and 0x80 for up. This receives
 * events already removed from the shared SDL queue; it never polls the host a
 * second time. Returns 1 when an in-domain keyboard transition was consumed,
 * 0 for disabled/non-key events, and -1 for an unsupported scan code. */
int portable_m1b73_queue_runtime_scan_transition(
    PortableM1B73QueueRuntime *runtime, const HostEvent *event);

/* Source f_1B73_09E9 coordinate command, exposed to the original source ABI
 * wrapper. Returns failure when its active mouse/hot-box provider fails. */
int portable_m1b73_queue_runtime_warp_source(int16_t x, int16_t y);
/* Source f_1B73_0196 cursor-hide transition reused by display callbacks. */
int portable_m1b73_queue_runtime_prepare_cursor_change(void);
void f_1B73_0196(void);

int portable_m1b73_queue_runtime_resolve_timer(
    void *context, const struct Timer *timer,
    PortableM1B73SourceQueueCallback *callback,
    void **callback_context);

#endif
