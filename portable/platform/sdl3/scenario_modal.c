#include "scenario_modal.h"

#include "../../ui_model/input/input.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { SCENARIO_WINDOW_ID = 0x0200, SCENARIO_KEY_CAPACITY = 64,
       MODAL_POLL_WAIT_MS = 8 };

typedef struct ScenarioModalBinding {
    Host *host;
    const PortableScenarioModalRequest *request;
    PortableWindowRenderer renderer;
    HostPalette host_palette;
    uint16_t keys[SCENARIO_KEY_CAPACITY];
    size_t key_head, key_count;
    PortableScenarioModalStatus fault;
    uint8_t window_open;
} ScenarioModalBinding;

static int framebuffer_size(const PortableFramebuffer *fb, size_t *size)
{
    if (fb == NULL || size == NULL || fb->pixels == NULL ||
        fb->width != HOST_LOGICAL_WIDTH || fb->height != HOST_LOGICAL_HEIGHT ||
        fb->stride < (size_t)fb->width ||
        fb->stride > SIZE_MAX / (size_t)fb->height)
        return 0;
    *size = fb->stride * (size_t)fb->height;
    return 1;
}

static void fail(ScenarioModalBinding *binding,
                 PortableScenarioModalStatus status)
{
    if (binding->fault == PORTABLE_SCENARIO_MODAL_SELECTED)
        binding->fault = status;
}

static int queue_key(ScenarioModalBinding *binding, uint16_t bios_key)
{
    int16_t logical_key;
    PortableInputStatus status = portable_input_decode_bios_key(bios_key,
                                                                 &logical_key);
    size_t tail;
    (void)logical_key;
    if (status == PORTABLE_INPUT_NO_KEY ||
        status == PORTABLE_INPUT_MODIFIER_ONLY)
        return 1;
    if (status != PORTABLE_INPUT_OK) {
        fail(binding, PORTABLE_SCENARIO_MODAL_HOST_ERROR);
        return 0;
    }
    if (binding->key_count == SCENARIO_KEY_CAPACITY) {
        fail(binding, PORTABLE_SCENARIO_MODAL_INPUT_OVERFLOW);
        return 0;
    }
    tail = (binding->key_head + binding->key_count) % SCENARIO_KEY_CAPACITY;
    binding->keys[tail] = bios_key;
    ++binding->key_count;
    return 1;
}

static int drain_host_events(ScenarioModalBinding *binding)
{
    HostEvent event;
    int status;
    while ((status = host_poll_event(binding->host, &event)) > 0) {
        if (event.kind == HOST_EVENT_KEY_DOWN && !queue_key(binding, event.key))
            return 0;
        if (event.kind == HOST_EVENT_QUIT) {
            if (binding->request->quit_flag != NULL)
                *binding->request->quit_flag = 1;
            fail(binding, PORTABLE_SCENARIO_MODAL_QUIT_REJECTED);
            return 0;
        }
    }
    if (status < 0) {
        fail(binding, PORTABLE_SCENARIO_MODAL_HOST_ERROR);
        return 0;
    }
    return 1;
}

static void modal_open(void *context, uint16_t window_id)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    PortableWindowOpenResult open_result;
    PortableWindowOpenStatus open_status;
    PortableWindowRegistrySlot *slot;
    PortableWindowRegistryStatus registry_status;
    int16_t no_variadic_args[4] = {0, 0, 0, 0};
    uint16_t object;
    if (window_id != SCENARIO_WINDOW_ID || binding->fault !=
        PORTABLE_SCENARIO_MODAL_SELECTED) {
        fail(binding, PORTABLE_SCENARIO_MODAL_OPEN_ERROR);
        return;
    }
    registry_status = portable_window_registry_load(binding->request->registry,
                                                     2);
    if (registry_status != PORTABLE_WINDOW_REGISTRY_OK) {
        fail(binding, PORTABLE_SCENARIO_MODAL_REGISTRY_ERROR);
        return;
    }
    slot = &binding->request->registry->slots[2];
    if (!slot->loaded || slot->window.count == 0) {
        fail(binding, PORTABLE_SCENARIO_MODAL_REGISTRY_ERROR);
        return;
    }
    /* DoScenario calls win_Open(0x0200) with no variadic arguments. Resource
     * 2 is valid for that call only because no object reads mode-5 stack
     * arguments; do not let synthetic zero arguments conceal a dependency. */
    for (object = 0; object < slot->window.count; ++object) {
        unsigned axis;
        for (axis = 0; axis < 4; ++axis)
            if (slot->window.objects[object].modes[axis] == 5) {
                fail(binding,
                     PORTABLE_SCENARIO_MODAL_UNSUPPORTED_GEOMETRY);
                return;
            }
    }
    open_status = portable_window_open_apply(
        binding->request->registry, binding->request->open_scene,
        SCENARIO_WINDOW_ID, no_variadic_args,
        binding->request->screen_width, binding->request->screen_height,
        &binding->request->menu_rect, &open_result);
    if (open_status != PORTABLE_WINDOW_OPEN_OK) {
        fail(binding, PORTABLE_SCENARIO_MODAL_OPEN_ERROR);
        return;
    }
    binding->window_open = 1;
    if (portable_window_draw_native(&slot->window, &binding->renderer) !=
        PORTABLE_RENDER_OK) {
        fail(binding, PORTABLE_SCENARIO_MODAL_RENDER_ERROR);
        return;
    }
    if (!host_present(binding->host, binding->renderer.framebuffer->pixels,
                      binding->renderer.framebuffer->stride,
                      &binding->host_palette))
        fail(binding, PORTABLE_SCENARIO_MODAL_HOST_ERROR);
}

static void modal_flush(void *context)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    if (binding->fault == PORTABLE_SCENARIO_MODAL_SELECTED)
        (void)drain_host_events(binding);
}

static int modal_get_event(void *context, PortableScenarioEvent *out)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    PortableWindowRegistrySlot *slot =
        &binding->request->registry->slots[2];
    HostEvent event;
    int status;
    if (binding->fault != PORTABLE_SCENARIO_MODAL_SELECTED) return 0;
    while ((status = host_poll_event(binding->host, &event)) > 0) {
        if (event.kind == HOST_EVENT_QUIT) {
            if (binding->request->quit_flag != NULL)
                *binding->request->quit_flag = 1;
            fail(binding, PORTABLE_SCENARIO_MODAL_QUIT_REJECTED);
            return 0;
        }
        if (event.kind == HOST_EVENT_KEY_DOWN) {
            (void)queue_key(binding, event.key);
            if (binding->fault != PORTABLE_SCENARIO_MODAL_SELECTED) return 0;
            continue;
        }
        if (event.kind != HOST_EVENT_MOUSE_DOWN || event.button != 1)
            continue;
        {
            PortableWindowPoint point = {event.x, event.y};
            int object_index = portable_window_hit_test(&slot->window, point);
            if (object_index >= 0 && object_index < 0x100) {
                out->code = (uint16_t)(SCENARIO_WINDOW_ID + object_index);
                return 1;
            }
        }
    }
    if (status < 0) {
        fail(binding, PORTABLE_SCENARIO_MODAL_HOST_ERROR);
        return 0;
    }
    host_wait_ms(MODAL_POLL_WAIT_MS);
    return 0;
}

static uint32_t modal_tick_count(void *context)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    if (binding->fault != PORTABLE_SCENARIO_MODAL_SELECTED) return 0;
    return binding->request->tick_count(binding->request->clock_context);
}

static int modal_key_available(void *context)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    if (binding->fault != PORTABLE_SCENARIO_MODAL_SELECTED) return 0;
    return binding->key_count != 0;
}

static uint16_t modal_read_key(void *context)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    uint16_t key;
    if (binding->fault != PORTABLE_SCENARIO_MODAL_SELECTED ||
        binding->key_count == 0)
        return 0;
    key = binding->keys[binding->key_head];
    binding->key_head = (binding->key_head + 1) % SCENARIO_KEY_CAPACITY;
    --binding->key_count;
    return (uint8_t)key != 0 ? (uint8_t)key : (uint16_t)(key & 0xff00u);
}

static void modal_close(void *context, uint16_t window_id)
{
    ScenarioModalBinding *binding = (ScenarioModalBinding *)context;
    PortableWindowOpenResult close_result;
    PortableWindowOpenStatus status;
    if (!binding->window_open) return;
    status = portable_window_close_apply(binding->request->registry,
                                         binding->request->open_scene,
                                         (int16_t)window_id, &close_result);
    if (status != PORTABLE_WINDOW_OPEN_OK) {
        fail(binding, PORTABLE_SCENARIO_MODAL_CLOSE_ERROR);
        return;
    }
    binding->window_open = 0;
}

static void modal_message(void *context, uint16_t code)
{
    (void)context;
    (void)printf("\nGOT Scenario %x", (unsigned)code);
    (void)fflush(stdout);
}

static int valid_request(Host *host, const PortableScenarioModalRequest *request,
                         uint16_t *result_code, size_t *pixels_size)
{
    const PortableWindowRenderer *renderer;
    if (host == NULL || request == NULL || result_code == NULL ||
        request->registry == NULL || request->open_scene == NULL ||
        !request->open_scene->initialized || request->palette == NULL ||
        request->fonts == NULL || !request->fonts->loaded ||
        request->renderer == NULL || request->tick_count == NULL ||
        request->screen_width <= 0 || request->screen_height <= 0)
        return 0;
    renderer = request->renderer;
    if (!framebuffer_size(renderer->framebuffer, pixels_size) ||
        renderer->database == NULL)
        return 0;
    return 1;
}

PortableScenarioModalStatus portable_scenario_modal_run(
    Host *host, const PortableScenarioModalRequest *request,
    uint16_t *result_code)
{
    ScenarioModalBinding binding;
    PortableScenarioHost flow_host;
    PortableScenarioFlow flow = {0};
    PortableScenarioPollResult poll_result = PORTABLE_SCENARIO_RUNNING;
    PortableScenarioModalStatus status = PORTABLE_SCENARIO_MODAL_BAD_ARGUMENT;
    PortableFramebuffer *fb;
    uint8_t *underlay;
    size_t underlay_size, i;
    int restore = 0;
    if (request != NULL && request->quit_flag != NULL && *request->quit_flag)
        return PORTABLE_SCENARIO_MODAL_QUIT_REJECTED;
    if (!valid_request(host, request, result_code, &underlay_size)) return status;
    if (request->registry->database == NULL) return status;
    underlay = (uint8_t *)malloc(underlay_size);
    if (underlay == NULL) return PORTABLE_SCENARIO_MODAL_OUT_OF_MEMORY;
    memset(&binding, 0, sizeof(binding));
    binding.host = host;
    binding.request = request;
    binding.renderer = *request->renderer;
    binding.renderer.database = request->registry->database;
    for (i = 0; i < 4; ++i)
        binding.renderer.fonts[i] = portable_fonts_get(request->fonts,
                                                       (unsigned)i + 2u);
    if (request->palette != NULL)
        memcpy(binding.host_palette.rgb, request->palette->rgb,
               sizeof(binding.host_palette.rgb));
    fb = binding.renderer.framebuffer;
    memcpy(underlay, fb->pixels, underlay_size);
    flow_host = (PortableScenarioHost){
        &binding, modal_open, modal_flush, modal_get_event, modal_tick_count,
        modal_key_available, modal_read_key, modal_close, modal_message};
    if (!portable_scenario_flow_begin(&flow, &flow_host)) {
        status = PORTABLE_SCENARIO_MODAL_BAD_ARGUMENT;
        goto done;
    }
    restore = binding.window_open;
    if (binding.fault != PORTABLE_SCENARIO_MODAL_SELECTED) {
        status = binding.fault;
        goto done;
    }
    while (poll_result == PORTABLE_SCENARIO_RUNNING) {
        poll_result = portable_scenario_flow_poll(&flow);
        if (binding.fault != PORTABLE_SCENARIO_MODAL_SELECTED) {
            status = binding.fault;
            goto done;
        }
    }
    if (poll_result == PORTABLE_SCENARIO_SELECTED) {
        *result_code = flow.result_code;
        status = PORTABLE_SCENARIO_MODAL_SELECTED;
    } else {
        *result_code = flow.result_code;
        status = PORTABLE_SCENARIO_MODAL_CANCELLED;
    }
done:
    if (flow.active && binding.window_open) modal_close(&binding,
                                                        SCENARIO_WINDOW_ID);
    if (binding.fault != PORTABLE_SCENARIO_MODAL_SELECTED &&
        status != PORTABLE_SCENARIO_MODAL_BAD_ARGUMENT)
        status = binding.fault;
    if (restore) {
        memcpy(fb->pixels, underlay, underlay_size);
        if (request->redraw_background != NULL &&
            !request->redraw_background(request->redraw_context,
                                        &binding.renderer))
            status = PORTABLE_SCENARIO_MODAL_RESTORE_ERROR;
        if (!host_present(host, fb->pixels, fb->stride, &binding.host_palette))
            status = PORTABLE_SCENARIO_MODAL_HOST_ERROR;
    }
    free(underlay);
    return status;
}

const char *portable_scenario_modal_status_string(
    PortableScenarioModalStatus status)
{
    switch (status) {
    case PORTABLE_SCENARIO_MODAL_SELECTED: return "selected";
    case PORTABLE_SCENARIO_MODAL_CANCELLED: return "cancelled";
    case PORTABLE_SCENARIO_MODAL_QUIT_REJECTED: return "quit rejected";
    case PORTABLE_SCENARIO_MODAL_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_SCENARIO_MODAL_OUT_OF_MEMORY: return "out of memory";
    case PORTABLE_SCENARIO_MODAL_REGISTRY_ERROR: return "window registry error";
    case PORTABLE_SCENARIO_MODAL_UNSUPPORTED_GEOMETRY: return "unsupported window geometry";
    case PORTABLE_SCENARIO_MODAL_OPEN_ERROR: return "window open error";
    case PORTABLE_SCENARIO_MODAL_RENDER_ERROR: return "window render error";
    case PORTABLE_SCENARIO_MODAL_HOST_ERROR: return "host event/presentation error";
    case PORTABLE_SCENARIO_MODAL_INPUT_OVERFLOW: return "BIOS key queue overflow";
    case PORTABLE_SCENARIO_MODAL_CLOSE_ERROR: return "window close error";
    case PORTABLE_SCENARIO_MODAL_RESTORE_ERROR: return "background restore error";
    }
    return "unknown scenario modal status";
}
