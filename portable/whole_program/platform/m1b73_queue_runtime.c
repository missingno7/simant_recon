#include "m1b73_queue_runtime.h"

#include "m1b73_mouse_state.h"
#include "m1b73_queues.h"
#include "../types/timer.h"

#include <stdlib.h>
#include <string.h>

extern void f_1B73_030F(int16_t bx, int16_t es, int16_t ax,
                        int16_t cx, int16_t dx);
extern int16_t f_1B73_0D4B(int16_t mode);
extern struct Timer g_5FF2;

static PortableM1B73QueueRuntime *active_runtime;

static int runtime_mouse_ready(const PortableM1B73MouseProvider *mouse)
{
    const PortableM1B73MouseAsmState *s;
    if (mouse == NULL || !mouse->bound || mouse->host == NULL ||
        mouse->input_host == NULL || mouse->state == NULL ||
        mouse->screen_width == NULL || mouse->screen_height == NULL)
        return 0;
    s = mouse->state;
    return s->cursor_drawn != NULL && s->cursor_event_pending != NULL &&
        s->cursor_update_lock != NULL && s->button_state != NULL &&
        s->x != NULL && s->y != NULL && s->cursor_width != NULL &&
        s->cursor_height != NULL && s->callback_count != NULL &&
        s->mouse_event_count != NULL && s->cursor_initialized != NULL &&
        s->saved_keyboard_flags != NULL && s->cursor_show_level != NULL &&
        s->hook_depth != NULL && s->mouse_mode != NULL &&
        s->cursor_image != NULL && s->cursor_mask != NULL &&
        mouse->services.host_to_source != NULL &&
        mouse->services.source_to_host != NULL &&
        mouse->services.cursor_header != NULL &&
        mouse->services.hit_test != NULL &&
        mouse->services.render_cursor != NULL;
}

static PortableM1B73QueueRuntime *require_runtime(void *context)
{
    PortableM1B73QueueRuntime *runtime =
        (PortableM1B73QueueRuntime *)context;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound ||
        runtime->events == NULL || runtime->mouse == NULL ||
        !runtime->events->bound || !runtime->mouse->bound ||
        runtime->events->input_host == NULL ||
        runtime->events->input_host != runtime->mouse->input_host)
        abort();
    return runtime;
}

static int16_t dispatch_event_queue(void *context, int16_t id,
                                   uint16_t flags, uint16_t status,
                                   int16_t x, int16_t y)
{
    (void)require_runtime(context);
    /* Original f030F loads ES:BX, AX, CX, DX and then unconditionally XORs AX
     * to zero. The real source function enqueues into the already-bound event
     * owner; zero therefore ends the source 0CB3 descriptor walk. */
    f_1B73_030F(id, (int16_t)flags, (int16_t)status, x, y);
    return 0;
}

static int16_t dispatch_cursor_timer(void *context, int16_t id,
                                     uint16_t flags, uint16_t status,
                                     int16_t x, int16_t y)
{
    (void)require_runtime(context);
    (void)flags;
    (void)status;
    (void)x;
    (void)y;
    /* This is the actual Timer.fn target; extra callback stack words are
     * ignored by the original one-word D4B body. Keep its returned AX. */
    return f_1B73_0D4B(id);
}

int portable_m1b73_queue_runtime_resolve_timer(
    void *context, const struct Timer *timer,
    PortableM1B73SourceQueueCallback *callback,
    void **callback_context)
{
    PortableM1B73QueueRuntime *runtime =
        (PortableM1B73QueueRuntime *)context;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound ||
        timer == NULL || callback == NULL || callback_context == NULL)
        return 0;
    /* Timer.fn is the source's generic void(void) pointer while these two
     * original entrypoints have their recovered C/ASM signatures. The
     * standard function-pointer conversion below is identity-only: converted
     * pointers are compared, never invoked or converted to integer/wire form.
     * The invocation itself always uses the true recovered signature above. */
    if (timer->fn == (void (*)(void))f_1B73_030F) {
        *callback = dispatch_event_queue;
    } else if (timer->fn == (void (*)(void))f_1B73_0D4B) {
        *callback = dispatch_cursor_timer;
    } else {
        return 0;
    }
    *callback_context = runtime;
    return 1;
}

static int render_cursor(PortableM1B73QueueRuntime *runtime,
                         PortableM1B73CursorAction action)
{
    PortableM1B73MouseAsmState *state = runtime->mouse->state;
    int ok;
    if (state == NULL || state->cursor_image == NULL ||
        state->cursor_mask == NULL || *state->cursor_image == NULL ||
        *state->cursor_mask == NULL || state->cursor_width == NULL ||
        state->cursor_height == NULL || state->x == NULL || state->y == NULL ||
        state->cursor_update_lock == NULL ||
        runtime->mouse->services.render_cursor == NULL)
        return 0;
    ++*state->cursor_update_lock;
    ok = runtime->mouse->services.render_cursor(
        runtime->mouse->services.context, action, *state->cursor_image,
        *state->cursor_mask, *state->cursor_width, *state->cursor_height,
        *state->x, *state->y);
    --*state->cursor_update_lock;
    return ok;
}

static int prepare_cursor_change(void *context)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    PortableM1B73MouseAsmState *state = runtime->mouse->state;
    uint8_t level;
    if (state == NULL || state->cursor_event_pending == NULL ||
        state->cursor_show_level == NULL)
        return 0;
    *state->cursor_event_pending = 1;
    level = *state->cursor_show_level;
    if (level == 0)
        return 1;
    /* ASM's `jg` admits 1..127. Negative signed byte values reach Punt. */
    if (level >= UINT8_C(0x80))
        return 0;
    ++runtime->cursor_change_counter;
    if (!render_cursor(runtime, PORTABLE_M1B73_CURSOR_HIDE))
        return 0;
    *state->cursor_show_level = (uint8_t)(level - 1u);
    return 1;
}

static int refresh_cursor(void *context)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    return portable_m1b73_mouse_update_cursor(runtime->mouse) ==
        PORTABLE_M1B73_MOUSE_OK;
}

static int warp_source_pointer(void *context, int16_t x, int16_t y)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    PortableM1B73MouseProvider *mouse = runtime->mouse;
    PortableM1B73MouseAsmState *state = mouse->state;
    int16_t host_x, host_y;
    uint16_t low_buttons, source_status, event_mask;
    int found;
    uint32_t token = 0;
    int visible;

    if (state == NULL || state->x == NULL || state->y == NULL ||
        state->button_state == NULL || state->cursor_show_level == NULL ||
        state->mouse_mode == NULL)
        return 0;
    /* The source calls INT 33h function 4 only when g_4DA4 is nonzero. It
     * still updates the source-coordinate callback state when the mouse is
     * in its non-warp mode. */
    if (*state->mouse_mode != 0 &&
        (mouse->services.source_to_host == NULL || mouse->host == NULL ||
         !mouse->services.source_to_host(mouse->services.context, x, y,
                                         &host_x, &host_y) ||
         !host_warp_pointer(mouse->host, host_x, host_y)))
        return 0;

    *state->x = x;
    *state->y = y;
    low_buttons = (uint16_t)(*state->button_state & UINT16_C(0x00ff));
    /* 09FF calls the source mouse-event handler with AL=1 and BL=buttons;
     * 0445 writes that pair to g_9120 before running the callback filter. */
    source_status = (uint16_t)(UINT16_C(0x0100) | low_buttons);
    *state->button_state = source_status;
    visible = *state->cursor_show_level != 0;
    if (visible && !render_cursor(runtime, PORTABLE_M1B73_CURSOR_HIDE))
        return 0;

    if (mouse->services.hit_test == NULL)
        return 0;
    found = mouse->services.hit_test(mouse->services.context, x, y,
                                     source_status, &token);
    if (found < 0)
        return 0;
    state->active_hotbox_token = found != 0 ? token : 0;
    if (visible)
        ++*state->mouse_event_count;

    event_mask = (uint16_t)((uint16_t)((uint16_t)g_5FF2.r.bottom >> 8) << 8);
    if ((source_status & event_mask) != 0 &&
        portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_OK)
        return 0;

    if (visible) {
        if (!render_cursor(runtime, PORTABLE_M1B73_CURSOR_SHOW))
            return 0;
        if (state->cursor_drawn != NULL)
            *state->cursor_drawn = 0;
    } else if (state->cursor_drawn != NULL) {
        *state->cursor_drawn = 1;
    }
    return 1;
}

static int read_mouse_buttons(void *context, uint16_t *buttons)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    if (buttons == NULL || runtime->mouse->state == NULL ||
        runtime->mouse->state->button_state == NULL)
        return 0;
    *buttons = (uint16_t)(*runtime->mouse->state->button_state &
                          UINT16_C(0x00ff));
    return 1;
}

static int set_keyboard_hook(void *context, int enabled)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    runtime->keyboard_hook_enabled = (uint8_t)(enabled != 0);
    return 1;
}

static int set_cursor_mode(void *context, uint8_t mode, int16_t *source_ax)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    if (source_ax == NULL || runtime->graphics_cursor_mode == NULL)
        return 0;
    return runtime->graphics_cursor_mode(runtime->graphics_context, mode,
                                         source_ax);
}

int portable_m1b73_queue_runtime_bind(
    PortableM1B73QueueRuntime *runtime,
    PortableM1B73Events *events,
    PortableM1B73MouseProvider *mouse,
    void *graphics_context,
    PortableM1B73GraphicsCursorMode graphics_cursor_mode)
{
    PortableM1B73QueueOpsServices operations;
    if (runtime == NULL || events == NULL || mouse == NULL ||
        active_runtime != NULL || runtime->bound || !events->bound ||
        events->input_host == NULL || !events->input_host->bound ||
        mouse->input_host != events->input_host || !runtime_mouse_ready(mouse) ||
        mouse->services.source_to_host == NULL ||
        mouse->services.hit_test == NULL ||
        mouse->services.render_cursor == NULL ||
        events->source_shift_state == NULL ||
        graphics_cursor_mode == NULL)
        return 0;
    memset(runtime, 0, sizeof(*runtime));
    runtime->events = events;
    runtime->mouse = mouse;
    runtime->graphics_context = graphics_context;
    runtime->graphics_cursor_mode = graphics_cursor_mode;
    runtime->keyboard_hook_enabled = 1; /* ASM kbd_hook_on initialized true */
    memset(runtime->scan_state, 0x80, sizeof(runtime->scan_state));
    memset(&operations, 0, sizeof(operations));
    operations.context = runtime;
    operations.resolve_timer_callback = portable_m1b73_queue_runtime_resolve_timer;
    operations.prepare_cursor_change = prepare_cursor_change;
    operations.refresh_cursor = refresh_cursor;
    operations.warp_source_pointer = warp_source_pointer;
    operations.read_mouse_buttons = read_mouse_buttons;
    operations.set_keyboard_hook = set_keyboard_hook;
    operations.set_cursor_mode = set_cursor_mode;
    operations.scan_state_table = runtime->scan_state;
    operations.events = events;
    active_runtime = runtime;
    runtime->bound = 1;
    if (!portable_m1b73_queue_ops_bind(&operations)) {
        runtime->bound = 0;
        active_runtime = NULL;
        return 0;
    }
    return 1;
}

void portable_m1b73_queue_runtime_unbind(
    PortableM1B73QueueRuntime *runtime)
{
    if (runtime == NULL || runtime != active_runtime)
        return;
    portable_m1b73_queue_ops_unbind();
    runtime->bound = 0;
    active_runtime = NULL;
}

int portable_m1b73_queue_runtime_scan_transition(
    PortableM1B73QueueRuntime *runtime, const HostEvent *event)
{
    uint8_t scan;
    uint8_t value;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound ||
        event == NULL)
        return -1;
    if (event->kind != HOST_EVENT_KEY_DOWN && event->kind != HOST_EVENT_KEY_UP)
        return 0;
    if (!runtime->keyboard_hook_enabled)
        return 0;
    scan = (uint8_t)(event->key >> 8);
    if (scan >= sizeof(runtime->scan_state))
        return -1;
    value = event->kind == HOST_EVENT_KEY_DOWN ? 0 : UINT8_C(0x80);
    if (runtime->scan_state[scan] == value)
        return 0;
    runtime->scan_state[scan] = value;
    return 1;
}

int portable_m1b73_queue_runtime_warp_source(int16_t x, int16_t y)
{
    if (active_runtime == NULL || !active_runtime->bound)
        return 0;
    return warp_source_pointer(active_runtime, x, y);
}

int portable_m1b73_queue_runtime_prepare_cursor_change(void)
{
    if (active_runtime == NULL || !active_runtime->bound)
        return 0;
    return prepare_cursor_change(active_runtime);
}

void f_1B73_0196(void)
{
    if (!portable_m1b73_queue_runtime_prepare_cursor_change())
        abort();
}
