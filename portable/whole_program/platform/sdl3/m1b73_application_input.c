#include "canonical_graphics_data.h"
#include "m1b73_application_input.h"
#include "canonical_mouse_input_data.h"

#include "../graphics_cursor_source.h"
#include "../m1b73_mouse_state.h"
#include "native_windows.h"
#include "../m1b73_main_input.h"
#include "../m1b73_queue_ops.h"
#include "../m1b73_queues.h"
#include "../m1b73_timer_view.h"
#include "../graphics_tile_upload.h"
#include "../../../platform/host.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

#include "portable/whole_program/types/input_queue.h"
static PortableM1B73SdlApplicationInput *active_application_input;

static uint16_t read_u16(const uint8_t *bytes)
{
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8));
}

static int bitmap_required_size(const uint8_t *resource, size_t size,
                                unsigned planes, uint16_t *width,
                                uint16_t *height)
{
    size_t row_bytes, required;
    uint16_t w, h;
    if (resource == NULL || size < 4u || width == NULL || height == NULL ||
        (planes != 1u && planes != 4u))
        return 0;
    w = read_u16(resource);
    h = read_u16(resource + 2);
    if (w == 0 || h == 0)
        return 0;
    row_bytes = ((size_t)w + 7u) / 8u;
    if (row_bytes > (SIZE_MAX - 4u) / planes / h)
        return 0;
    required = 4u + row_bytes * planes * h;
    if (required > size)
        return 0;
    *width = w;
    *height = h;
    return 1;
}

static int identity_host_to_source(void *context, int16_t x, int16_t y,
                                   int16_t *source_x, int16_t *source_y)
{
    (void)context;
    if (source_x == NULL || source_y == NULL)
        return 0;
    *source_x = x;
    *source_y = y;
    return 1;
}

static int identity_source_to_host(void *context, int16_t x, int16_t y,
                                   int16_t *host_x, int16_t *host_y)
{
    (void)context;
    if (host_x == NULL || host_y == NULL)
        return 0;
    *host_x = x;
    *host_y = y;
    return 1;
}

static int measure_cursor_resource(PortableM1B73SdlApplicationInput *binding,
                                   const uint8_t *resource, size_t *size)
{
    SimGraphicsCursorSourceBindings *b = &binding->cursor_bindings;
    return b->measure_active_resource != NULL &&
        b->measure_active_resource(b->context, resource, size);
}

static int cursor_header(void *context, const uint8_t *image,
                         const uint8_t *mask, uint16_t *width,
                         uint16_t *height)
{
    PortableM1B73SdlApplicationInput *binding =
        (PortableM1B73SdlApplicationInput *)context;
    size_t image_size = 0, mask_size = 0;
    uint16_t image_width, image_height, mask_width, mask_height;
    if (binding == NULL || !binding->bound ||
        !measure_cursor_resource(binding, image, &image_size) ||
        !measure_cursor_resource(binding, mask, &mask_size) ||
        /* The source kinds and slot names are counterintuitive: kind 7 is the
         * one-plane input stored at g_4D8E and consumed by g9154 (AND);
         * kind 8 is the four-plane input stored at g_4D92 and consumed by
         * g914C (XOR). The source ABI still names the arguments image/mask. */
        !bitmap_required_size(image, image_size, 4u,
                             &image_width, &image_height) ||
        !bitmap_required_size(mask, mask_size, 1u,
                             &mask_width, &mask_height) ||
        image_width != mask_width || image_height != mask_height)
        return 0;
    *width = image_width;
    *height = image_height;
    return 1;
}

static int hotbox_hit_test(void *context, int16_t x, int16_t y,
                           uint16_t query, uint32_t *token)
{
    (void)context;
    return portable_m1b73_queue_ops_hit_test(x, y, query, token);
}

static int source_queue_dispatch(void *context, uint16_t source_status)
{
    (void)context;
    if (((uint8_t)(source_status >> 8) &
         (uint8_t)((uint16_t)g_5FF2.r.bottom >> 8)) == 0)
        return 1;
    return portable_m1b73_queue_dispatch() == PORTABLE_M1B73_QUEUE_OK;
}

static int render_source_cursor(void *context, PortableM1B73CursorAction action,
                                const uint8_t *image, const uint8_t *mask,
                                uint16_t width, uint16_t height,
                                int16_t x, int16_t y)
{
    PortableM1B73SdlApplicationInput *binding =
        (PortableM1B73SdlApplicationInput *)context;
    PortableM1B73MouseAsmState *state = &portable_m1b73_mouse_asm_state;
    size_t ignored;
    uint16_t checked_width, checked_height;
    int16_t mode;
    if (binding == NULL || !binding->bound ||
        state->cursor_image == NULL || state->cursor_mask == NULL ||
        *state->cursor_image != image || *state->cursor_mask != mask ||
        state->x == NULL || state->y == NULL || *state->x != x ||
        *state->y != y ||
        !measure_cursor_resource(binding, image, &ignored) ||
        !measure_cursor_resource(binding, mask, &ignored) ||
        /* f_1B73_01E1 stores its second argument in g_4D8E and its first in
         * g_4D92. Native cursor state names follow those source slots, so
         * state.image is kind 7 and state.mask is kind 8 after installation.
         * Reorder back to the public image-kind8/mask-kind7 validator ABI. */
        !cursor_header(context, mask, image, &checked_width, &checked_height) ||
        checked_width != width || checked_height != height)
        return 0;
    mode = action == PORTABLE_M1B73_CURSOR_SHOW ? 1 : 2;
    if (action != PORTABLE_M1B73_CURSOR_SHOW &&
        action != PORTABLE_M1B73_CURSOR_HIDE)
        return 0;
    (void)f_1B73_0D4B(mode);
    return sim_graphics_source_last_status() == SIM_GRAPHICS_OK;
}

static int dispatch_source_event(void *context, const HostEvent *event)
{
    PortableM1B73SdlApplicationInput *binding =
        (PortableM1B73SdlApplicationInput *)context;
    PortableM1B73MouseStatus mouse_status;
    int scan_result;
    if (binding == NULL || !binding->bound || event == NULL)
        return 0;
    if (event->kind == HOST_EVENT_QUIT) {
        binding->quit_requested = 1;
        if (binding->quit_hook != NULL)
            binding->quit_hook(binding->quit_hook_context);
    }
    scan_result = portable_m1b73_queue_runtime_scan_transition(
        &binding->queues, event);
    if (scan_result < 0)
        return 0;
    mouse_status = portable_m1b73_mouse_consume_event(&binding->mouse, event);
    if (mouse_status == PORTABLE_M1B73_MOUSE_OK ||
        mouse_status == PORTABLE_M1B73_MOUSE_INACTIVE)
        return 1;
    binding->observer_failed = 1;
    return 0;
}

static int refresh_application(void *context, SimTimingClock *clock)
{
    PortableM1B73SdlApplicationInput *binding =
        (PortableM1B73SdlApplicationInput *)context;
    uint16_t ignored_key = 0;
    int key_status;
    if (binding == NULL || !binding->bound || clock != binding->game_clock)
        return 0;
    if (binding->refreshing)
        return 1;
    binding->refreshing = 1;
    /* One quantum per outer platform poll; nested ingestion/presentation
     * and the idle hook must not consume additional virtual time. */
    if (!binding->suppress_idle_hook) host_virtual_clock_poll();
    if (!portable_input_time_host_refresh_from_sdl_monotonic(
            &binding->input_host.monotonic_refresh, clock)) {
        binding->refreshing = 0;
        return 0;
    }
    if (!portable_m1b73_queue_runtime_refresh_cursor(&binding->queues)) {
        binding->refreshing = 0;
        return 0;
    }
    /* BIOS key availability is nonconsuming. It ingests SDL events once and
     * the observer routes their mouse/key effects while retaining FIFO order
     * for the source application. */
    key_status = binding->input_host.input_time.services.key_available(
        binding->input_host.input_time.services.context, &ignored_key);
    if (key_status < 0 || binding->observer_failed) {
        binding->refreshing = 0;
        return 0;
    }
    if (binding->idle_hook != NULL && !binding->idle_hook_active &&
        !binding->suppress_idle_hook) {
        binding->idle_hook_active = 1;
        binding->idle_hook(binding->idle_hook_context);
        binding->idle_hook_active = 0;
    }
    binding->refreshing = 0;
    return 1;
}

static int dimensions_match(Host *host, const SimGraphicsDriver *graphics)
{
    int width = 0, height = 0;
    return host_get_logical_size(host, &width, &height) &&
        width == graphics->framebuffer.width &&
        height == graphics->framebuffer.height &&
        width == g_3DB2 && height == g_3DB4 &&
        width > 0 && height > 0 && width <= INT16_MAX && height <= INT16_MAX;
}

PortableM1B73ApplicationInputStatus portable_m1b73_sdl_application_input_bind(
    PortableM1B73SdlApplicationInput *binding,
    Host *host, SimGraphicsDriver *graphics, SimSdlPaletteHost *palette,
    SimTimingClock *game_clock, SimTimingClock *bios_clock,
    const SimGraphicsCursorSourceBindings *cursor_bindings)
{
    PortableM1B73ApplicationInputStatus status =
        PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    PortableM1B73MouseServices mouse_services;
    PortableM1B73TimerQueueView queue_view;
    SimGraphicsCursorSourceBindings graphics_bindings;
    SimGraphicsStatus cursor_status;
    if (binding == NULL || host == NULL || graphics == NULL || palette == NULL ||
        game_clock == NULL || bios_clock == NULL || cursor_bindings == NULL ||
        active_application_input != NULL ||
        cursor_bindings->resolve_handle == NULL ||
        cursor_bindings->measure_active_resource == NULL ||
        graphics != sim_graphics_source_owner() ||
        graphics->pixel_storage == NULL)
        return PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    if (!dimensions_match(host, graphics))
        return PORTABLE_M1B73_APP_INPUT_HOST_GEOMETRY_MISMATCH;
    memset(binding, 0, sizeof(*binding));
    binding->host = host;
    binding->graphics = graphics;
    binding->palette = palette;
    binding->game_clock = game_clock;
    binding->bios_clock = bios_clock;
    binding->cursor_bindings = *cursor_bindings;

    if (portable_input_time_host_init_clocks(&binding->input_host, host,
            game_clock, bios_clock) != PORTABLE_INPUT_TIME_OK)
        return PORTABLE_M1B73_APP_INPUT_CLOCK_BIND_FAILED;
    if (portable_input_time_host_set_clock_refresh(&binding->input_host,
            refresh_application, binding) != PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_set_event_observer(&binding->input_host,
            dispatch_source_event, binding) != PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&binding->input_host) !=
            PORTABLE_INPUT_TIME_OK) {
        status = PORTABLE_M1B73_APP_INPUT_CLOCK_BIND_FAILED;
        goto clock_fail;
    }

    if (!portable_m1b73_get_source_timer_queue_view(&queue_view)) {
        status = PORTABLE_M1B73_APP_INPUT_EVENT_BIND_FAILED;
        goto event_fail;
    }
    if (!portable_m1b73_bind_source_main_input(&binding->events,
            &binding->input_host, game_clock, &shift_state,
            queue_view.records, queue_view.record_slots)) {
        status = PORTABLE_M1B73_APP_INPUT_EVENT_BIND_FAILED;
        goto event_fail;
    }
    binding->event_bound = 1;

    memset(&mouse_services, 0, sizeof(mouse_services));
    mouse_services.context = binding;
    mouse_services.host_to_source = identity_host_to_source;
    mouse_services.source_to_host = identity_source_to_host;
    mouse_services.cursor_header = cursor_header;
    mouse_services.hit_test = hotbox_hit_test;
    mouse_services.render_cursor = render_source_cursor;
    if (portable_m1b73_mouse_bind(&binding->mouse, host, &binding->input_host,
            &portable_m1b73_mouse_asm_state, &g_3DB2,
            &g_3DB4, &mouse_services) != PORTABLE_M1B73_MOUSE_OK)
    {
        status = PORTABLE_M1B73_APP_INPUT_MOUSE_BIND_FAILED;
        goto mouse_fail;
    }
    binding->mouse_bound = 1;
    binding->mouse.dispatch_queue = source_queue_dispatch;
    binding->mouse.dispatch_queue_context = binding;
    binding->mouse.display_busy = (uint8_t *)&g_3DD4;

    graphics_bindings = *cursor_bindings;
    graphics_bindings.graphics = graphics;
    graphics_bindings.source_shift_state = &shift_state;
    graphics_bindings.hide_rectangle_active = &g_4334;
    graphics_bindings.hide_rectangle = g_4336;
    cursor_status = sim_graphics_source_cursor_bind(&binding->graphics_cursor,
                                                    &graphics_bindings);
    if (cursor_status != SIM_GRAPHICS_OK) {
        status = PORTABLE_M1B73_APP_INPUT_GRAPHICS_CURSOR_BIND_FAILED;
        goto graphics_cursor_fail;
    }
    binding->graphics_cursor_bound = 1;
    if (!portable_m1b73_queue_runtime_bind(&binding->queues, &binding->events,
            &binding->mouse, &binding->graphics_cursor,
            portable_m1b73_graphics_cursor_mode)) {
        status = PORTABLE_M1B73_APP_INPUT_QUEUE_BIND_FAILED;
        goto queue_fail;
    }
    binding->queues_bound = 1;
    binding->bound = 1;
    binding->countdown_last_tick = sim_timing_tick_count(bios_clock);
    binding->countdown_initialized = 1;
    active_application_input = binding;
    return PORTABLE_M1B73_APP_INPUT_OK;

queue_fail:
    sim_graphics_source_cursor_unbind(&binding->graphics_cursor);
    binding->graphics_cursor_bound = 0;
graphics_cursor_fail:
    portable_m1b73_mouse_unbind(&binding->mouse);
    binding->mouse_bound = 0;
mouse_fail:
    portable_m1b73_unbind_source_main_input(&binding->events);
    binding->event_bound = 0;
event_fail:
    portable_input_time_host_shutdown(&binding->input_host);
clock_fail:
    memset(binding, 0, sizeof(*binding));
    return status;
}

void portable_m1b73_sdl_application_input_unbind(
    PortableM1B73SdlApplicationInput *binding)
{
    if (binding == NULL)
        return;
    if (active_application_input == binding)
        active_application_input = NULL;
    if (binding->queues_bound)
        portable_m1b73_queue_runtime_unbind(&binding->queues);
    if (binding->graphics_cursor_bound)
        sim_graphics_source_cursor_unbind(&binding->graphics_cursor);
    if (binding->mouse_bound)
        portable_m1b73_mouse_unbind(&binding->mouse);
    if (binding->event_bound)
        portable_m1b73_unbind_source_main_input(&binding->events);
    portable_input_time_host_shutdown(&binding->input_host);
    memset(binding, 0, sizeof(*binding));
}

PortableM1B73ApplicationInputStatus
portable_m1b73_sdl_application_input_service_one(
    PortableM1B73SdlApplicationInput *binding, HostEvent *event,
    int *had_event)
{
    int result;
    if (binding == NULL || event == NULL || had_event == NULL)
        return PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    if (!binding->bound)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    binding->suppress_idle_hook = 1;
    if (portable_input_time_host_refresh_clock(&binding->input_host) !=
            PORTABLE_INPUT_TIME_OK || binding->observer_failed) {
        binding->suppress_idle_hook = 0;
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    }
    result = portable_m1b73_poll_host_event(&binding->events, event);
    binding->suppress_idle_hook = 0;
    if (result < 0)
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    *had_event = result;
    return PORTABLE_M1B73_APP_INPUT_OK;
}

PortableM1B73ApplicationInputStatus
portable_m1b73_sdl_application_input_present(
    PortableM1B73SdlApplicationInput *binding)
{
    const HostPalette *palette;
    if (binding == NULL)
        return PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    if (!binding->bound)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    if (portable_input_time_host_refresh_clock(&binding->input_host) !=
        PORTABLE_INPUT_TIME_OK)
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    sim_graphics_vga_sync(binding->graphics);
    palette = sim_sdl_palette_view(binding->palette);
    if (palette == NULL)
        return PORTABLE_M1B73_APP_INPUT_PALETTE_NOT_READY;
    if (binding->graphics->framebuffer.pixels == NULL ||
        binding->graphics->framebuffer.width <= 0 ||
        binding->graphics->framebuffer.height <= 0 ||
        binding->graphics->framebuffer.stride <
            (size_t)binding->graphics->framebuffer.width ||
        !host_present(binding->host, binding->graphics->framebuffer.pixels,
                      binding->graphics->framebuffer.stride, palette) ||
        !native_windows_present(palette))
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    return PORTABLE_M1B73_APP_INPUT_OK;
}

void portable_m1b73_sdl_application_input_set_idle_hook(
    PortableM1B73SdlApplicationInput *binding,
    PortableM1B73ApplicationIdleHook hook, void *context)
{
    if (binding == NULL || !binding->bound)
        return;
    binding->idle_hook = hook;
    binding->idle_hook_context = context;
}

void portable_m1b73_sdl_application_input_set_quit_hook(
    PortableM1B73SdlApplicationInput *binding,
    PortableM1B73ApplicationQuitHook hook, void *context)
{
    if (binding == NULL || !binding->bound)
        return;
    binding->quit_hook = hook;
    binding->quit_hook_context = context;
}

PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_set(
    PortableM1B73SdlApplicationInput *binding, int16_t source_ticks)
{
    uint32_t now;
    if (binding == NULL)
        return PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    if (!binding->bound)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    if (portable_input_time_host_refresh_clock(&binding->input_host) !=
        PORTABLE_INPUT_TIME_OK)
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    now = sim_timing_tick_count(binding->bios_clock);
    tmr_countdown = (uint16_t)source_ticks;
    binding->countdown_last_tick = now;
    binding->countdown_initialized = 1;
    return PORTABLE_M1B73_APP_INPUT_OK;
}

PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_get(
    PortableM1B73SdlApplicationInput *binding, uint16_t *remaining)
{
    uint32_t now, elapsed;
    uint64_t dec;
    if (binding == NULL || remaining == NULL)
        return PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT;
    if (!binding->bound)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    if (!binding->countdown_initialized)
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    /* INT08 decrements tmr_countdown even while the private source TickCount
     * is disabled, so measure elapsed always-on BIOS logical ticks. Refreshing
     * the shared host owner also pumps retained SDL events and idle work. */
    if (portable_input_time_host_refresh_clock(&binding->input_host) !=
        PORTABLE_INPUT_TIME_OK)
        return PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED;
    now = sim_timing_tick_count(binding->bios_clock);
    elapsed = now - binding->countdown_last_tick;
    binding->countdown_last_tick = now;
    dec = (uint64_t)elapsed * 5u;
    tmr_countdown = dec >= tmr_countdown ? 0 :
        (uint16_t)(tmr_countdown - (uint16_t)dec);
    *remaining = tmr_countdown;
    return PORTABLE_M1B73_APP_INPUT_OK;
}

PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_store(
    int16_t source_ticks)
{
    if (active_application_input == NULL)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    return portable_m1b73_source_countdown_set(active_application_input,
                                                source_ticks);
}

PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_load(
    uint16_t *remaining)
{
    if (active_application_input == NULL)
        return PORTABLE_M1B73_APP_INPUT_UNBOUND;
    return portable_m1b73_source_countdown_get(active_application_input,
                                                remaining);
}

void portable_m1b73_source_countdown_wait(int16_t source_ticks)
{
    uint16_t remaining;
    if (portable_m1b73_source_countdown_store(source_ticks) !=
        PORTABLE_M1B73_APP_INPUT_OK)
        abort();
    do {
        if (portable_m1b73_source_countdown_load(&remaining) !=
            PORTABLE_M1B73_APP_INPUT_OK)
            abort();
    } while (remaining != 0);
}

void portable_m1b73_source_countdown_write(int16_t source_ticks)
{
    if (portable_m1b73_source_countdown_store(source_ticks) !=
        PORTABLE_M1B73_APP_INPUT_OK)
        abort();
}

int16_t portable_m1b73_source_countdown_is_zero(void)
{
    uint16_t remaining;
    if (portable_m1b73_source_countdown_load(&remaining) !=
        PORTABLE_M1B73_APP_INPUT_OK)
        abort();
    return (int16_t)(remaining == 0);
}

void f_1B73_050E(void) { }
void f_1B73_0510(void) { }

void f_1B73_09E9(int16_t x, int16_t y)
{
    if (!portable_m1b73_queue_runtime_warp_source(x, y))
        abort();
}
