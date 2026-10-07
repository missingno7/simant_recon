#include "m1b73_queue_runtime.h"
#include "canonical_mouse_input_data.h"

#include "m1b73_mouse_state.h"
#include "m1b73_queues.h"
#include "../types/timer.h"

#include <stdlib.h>
#include <string.h>

extern void f_1B73_030F(int16_t bx, int16_t es, int16_t ax,
                        int16_t cx, int16_t dx);
extern int16_t f_1B73_0D4B(int16_t mode);
#include "portable/whole_program/types/input_queue.h"

static PortableM1B73QueueRuntime *active_runtime;
extern uint8_t g_4362, g_4363, g_4364, g_4368, g_4369;
extern uint8_t g_53BD;

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
    ++g_434E;
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

    /* 09FF calls the source mouse-event handler with AL=1 and BL=buttons;
     * 0445 writes that pair to g_9120 before running the callback filter. */
    return portable_m1b73_mouse_callback(mouse, 1,
        (uint8_t)*state->button_state, x, y) == PORTABLE_M1B73_MOUSE_OK;
}

static int read_mouse_buttons(void *context, uint16_t *buttons)
{
    PortableM1B73QueueRuntime *runtime = require_runtime(context);
    if (buttons == NULL || runtime->mouse->state == NULL ||
        runtime->mouse->state->button_state == NULL)
        return 0;
    *buttons = runtime->mouse->driver_buttons;
    return 1;
}

static int set_keyboard_hook(void *context, int enabled)
{
    (void)require_runtime(context);
    kbd_hook_on = (uint8_t)(enabled != 0);
    g_53BD = kbd_hook_on;
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
    memset(&operations, 0, sizeof(operations));
    operations.context = runtime;
    operations.resolve_timer_callback = portable_m1b73_queue_runtime_resolve_timer;
    operations.prepare_cursor_change = prepare_cursor_change;
    operations.refresh_cursor = refresh_cursor;
    operations.warp_source_pointer = warp_source_pointer;
    operations.read_mouse_buttons = read_mouse_buttons;
    operations.set_keyboard_hook = set_keyboard_hook;
    operations.set_cursor_mode = set_cursor_mode;
    operations.scan_state_table = g_53CD;
    operations.events = events;
    active_runtime = runtime;
    runtime->bound = 1;
    runtime->last_cursor_tick = sim_timing_tick_count(events->input_host->bios_clock);
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
    int carry;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound ||
        event == NULL)
        return -1;
    if (event->kind != HOST_EVENT_KEY_DOWN && event->kind != HOST_EVENT_KEY_UP)
        return 0;
    if (!kbd_hook_on || !runtime->mouse->event_pump_active)
        return 0;
    scan = (uint8_t)(event->key >> 8);
    if (scan >= sizeof(g_53CD))
        return -1;
    if (event->extended) {
        carry = portable_m1b73_queue_runtime_scan_byte(runtime, 0xe0, 0, 0);
        if (carry < 0)
            return -1;
        /* E0 is its own IRQ09 before the actual scan, normally a duplicate
         * break with CF clear. Flush its old BIOS buffer now, so a later
         * carry-set key can retain only the key produced by its own IRQ. */
        if (!carry) {
            runtime->events->input_host->key_head = 0;
            runtime->events->input_host->key_count = 0;
        }
    }
    /* SDL has no interrupted DOS register/segment context. The explicit
     * projection below accepts real words for differential controls. Native
     * zero residue remains a documented raw-state limitation. */
    carry = portable_m1b73_queue_runtime_scan_byte(runtime,
        (uint8_t)(scan | (event->kind == HOST_EVENT_KEY_UP ? 0x80 : 0)), 0, 0);
    if (carry < 0)
        return -1;
    runtime->events->input_host->suppress_bios_key = (uint8_t)!carry;
    return 1;
}

int portable_m1b73_queue_runtime_scan_byte(
    PortableM1B73QueueRuntime *runtime, uint8_t raw,
    uint16_t cx, uint16_t dx)
{
    uint8_t scan = raw & 0x7f;
    uint8_t release = raw & 0x80;
    uint8_t make = release == 0;
    uint8_t flags, command = 0;
    uint16_t width, height;
    int carry = 1;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound)
        return -1;
    /* m1B73.asm:1096-1140. E0 suppresses only the shift special case. */
    if (kbd_last_scan != 0xe0) {
        cx = (uint16_t)((cx & 0xff00) | 2);
        if (scan == 0x2a || scan == 0x36) {
            uint8_t bit = scan == 0x2a ? 2 : 1;
            if (make) shift_state |= bit;
            else shift_state &= (uint8_t)~bit;
            shift_state &= 3;
            last_shift = shift_state;
            goto done;
        }
    }
    if (g_53CD[scan] == release) {
        carry = 0; /* equal CMP, not STC: the old BIOS buffer is flushed */
        goto done;
    }
    g_53CD[scan] = release;
    if (make)
        (void)portable_m1b73_event_enqueue_registers(runtime->events,
            0, cx, dx, (uint16_t)(0xfa00 | scan), 0);
    flags = portable_input_time_host_keyboard_flags(runtime->events->input_host);
    width = (uint16_t)*runtime->mouse->screen_width;
    height = (uint16_t)*runtime->mouse->screen_height;
    /* Table 544D/5460 and L07C0: Ctrl/Alt arrows ignore make, still stop
     * their axis on break. All actions follow the make enqueue above. */
    switch (scan) {
    case 0x48: case 0x50: case 0x4b: case 0x4d:
        if (make && (flags & 0x0c)) break;
        if (scan == 0x48 || scan == 0x50) {
            uint8_t step = (uint8_t)((height >> 7) + 1);
            g_4363 = make ? (scan == 0x48 ? (uint8_t)-step : step) : 0;
        } else {
            uint8_t step = (uint8_t)((width >> 7) | 1);
            g_4362 = make ? (scan == 0x4b ? (uint8_t)-step : step) : 0;
        }
        tick_phase = 0;
        g_4364 = 0;
        carry = 0;
        break;
    case 0x4c: /* keypad 5 centers on both make and break */
        g_9122 = (int16_t)(width >> 1);
        g_9124 = (int16_t)(height >> 1);
        goto warp;
    case 0x47:
        if (make) { g_9122 = (uint16_t)g_9122 <= 8 ? 0 : 6; goto warp; }
        carry = 0; break;
    case 0x4f:
        if (make) {
            uint16_t edge = (uint16_t)(width - 1);
            g_9122 = (int16_t)((uint16_t)(edge - 8) < (uint16_t)g_9122 ? edge : edge - 6);
            goto warp;
        }
        carry = 0; break;
    case 0x49:
        if (make) { g_9124 = (uint16_t)g_9124 <= 8 ? 0 : 6; goto warp; }
        carry = 0; break;
    case 0x51:
        if (make) {
            uint16_t edge = (uint16_t)(height - 1);
            g_9124 = (int16_t)((uint16_t)(edge - 8) <= (uint16_t)g_9124 ? edge : edge - 6);
            goto warp;
        }
        carry = 0; break;
    case 0x52: case 0x39: case 0x53: {
        uint8_t button = scan == 0x53 ? 2 : 1;
        uint8_t buttons = (uint8_t)((g_9120 & (uint16_t)~button) | (make ? button : 0));
        uint8_t mask = button == 1 ? (make ? 2 : 4) : (make ? 8 : 0x10);
        if (portable_m1b73_mouse_callback(runtime->mouse, mask, buttons,
                g_9122, g_9124) != PORTABLE_M1B73_MOUSE_OK)
            return -1;
        carry = 0;
        break;
    }
    case 0x3b: /* F1: Shift-latch cursor; retains BIOS key */
        if (flags & 0x0f) shift_state = 0;
        else shift_state ^= make ? 0x80 : 0;
        if (!warp_source_pointer(runtime, g_9122, g_9124)) return -1;
        break;
    case 0x19: if (make && (flags & 0x0f) == 4) command = 1; break;
    case 0x4e: if (make && !(flags & 0x0b)) command = flags & 4 ? 2 : 6; break;
    case 0x4a: if (make && !(flags & 0x0b)) command = flags & 4 ? 3 : 7; break;
    case 0x13: if (make && (flags & 0x0f) == 4) command = 4; break;
    case 0x2c: if (make && (flags & 0x0f) == 4) command = 5; break;
    default: break;
    }
    if (command != 0) {
        /* L088A ror AH,1 => 80h; AL = command|80h; ES=0 and CL=BDA. */
        uint16_t ax = (uint16_t)(0x8080 | command);
        (void)portable_m1b73_event_enqueue_registers(runtime->events,
            ax, flags, dx, (uint16_t)(0xf080 | command), 0);
    }
    goto done;
warp:
    if (!warp_source_pointer(runtime, g_9122, g_9124)) return -1;
    carry = 0;
done:
    kbd_last_scan = raw;
    return carry;
}

int portable_m1b73_queue_runtime_cursor_tick(PortableM1B73QueueRuntime *runtime)
{
    uint8_t sx, sy;
    int16_t x, y;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound)
        return 0;
    ++tick_phase;
    ++timer_busy;
    if (timer_busy != 1 || mouse_busy) goto done;
    /* INT08:888-911: deferred cursor work precedes movement. */
    if ((int8_t)g_4365 > 0) {
        if (!(runtime->mouse->display_busy && *runtime->mouse->display_busy) && !g_4333) {
            uint8_t pending = g_4331 & 1;
            g_4331 >>= 1;
            if (pending) f_1B73_04BB();
        }
    } else {
        g_4332 >>= 1;
        if (!g_4332) {
            g_4332 = 1;
            if ((g_4331 || !g_4366) &&
                !(runtime->mouse->display_busy && *runtime->mouse->display_busy) && !g_4333)
                f_1B73_00D9();
        }
    }
    sx = (uint8_t)(g_4362 + g_4368);
    sy = (uint8_t)(g_4363 + g_4369);
    if (!(sx | sy)) goto done;
    if (tick_phase == 4 || tick_phase == 10 || tick_phase == 28) ++g_4364;
    sx = g_4364 >= 8 ? 0 : (uint8_t)(sx << g_4364);
    sy = g_4364 >= 8 ? 0 : (uint8_t)(sy << g_4364);
    x = (int16_t)((uint16_t)g_9122 + (int8_t)sx);
    y = (int16_t)((uint16_t)g_9124 + (int8_t)sy);
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= *runtime->mouse->screen_width) x = *runtime->mouse->screen_width - 1;
    if (y >= *runtime->mouse->screen_height) y = *runtime->mouse->screen_height - 1;
    /* 09FF calls 0445 while timer_busy=1, so redraw is deferred. */
    if (!warp_source_pointer(runtime, x, y)) { --timer_busy; return 0; }
done:
    --timer_busy;
    return 1;
}

int portable_m1b73_queue_runtime_refresh_cursor(PortableM1B73QueueRuntime *runtime)
{
    uint32_t now, elapsed;
    if (runtime == NULL || runtime != active_runtime || !runtime->bound)
        return 0;
    now = sim_timing_tick_count(runtime->events->input_host->bios_clock);
    elapsed = now - runtime->last_cursor_tick;
    runtime->last_cursor_tick = now;
    if (!runtime->mouse->event_pump_active)
        return 1;
    while (elapsed-- != 0)
        if (!portable_m1b73_queue_runtime_cursor_tick(runtime))
            return 0;
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
