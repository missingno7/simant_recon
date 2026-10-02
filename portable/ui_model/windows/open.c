#include "open.h"

#include <stdlib.h>
#include <string.h>

static int valid_window_id(const PortableWindowRegistry *registry,
                           int16_t window_id)
{
    return registry != NULL && window_id >= 0 && (window_id & 0xff) == 0 &&
           (uint16_t)(window_id >> 8) < registry->window_count &&
           (uint16_t)(window_id >> 8) < PORTABLE_WINDOW_REGISTRY_SLOTS;
}

static PortableWindowRegistrySlot *get_loaded_slot(
    PortableWindowRegistry *registry, int16_t window_id)
{
    if (!valid_window_id(registry, window_id)) return NULL;
    if (!registry->slots[(uint16_t)window_id >> 8].loaded) return NULL;
    return &registry->slots[(uint16_t)window_id >> 8];
}

static void add_event(PortableWindowOpenResult *result,
                      PortableWindowOpenEventKind kind, int16_t window_id)
{
    if (result->event_count < PORTABLE_WINDOW_OPEN_MAX_EVENTS) {
        result->events[result->event_count].kind = kind;
        result->events[result->event_count].window_id = window_id;
        result->event_count++;
    }
}

static int order_find(const PortableWindowOpenScene *scene, int16_t window_id)
{
    uint16_t i;
    for (i = 0; i < scene->open_count; ++i)
        if (scene->order[i] == window_id) return (int)i;
    return -1;
}

static void order_remove(PortableWindowOpenScene *scene, uint16_t index)
{
    uint16_t i;
    if (index >= scene->open_count) return;
    for (i = index; i + 1 < scene->open_count; ++i)
        scene->order[i] = scene->order[i + 1];
    scene->open_count--;
    scene->order[scene->open_count] = PORTABLE_WINDOW_OPEN_NONE;
}

static void order_front(PortableWindowOpenScene *scene, int16_t window_id)
{
    int old = order_find(scene, window_id);
    uint16_t i;
    if (old >= 0) order_remove(scene, (uint16_t)old);
    for (i = scene->open_count; i > 0; --i) scene->order[i] = scene->order[i - 1];
    scene->order[0] = window_id;
    scene->open_count++;
    scene->front_window_id = window_id;
}

static PortableWindowRect origin_rect(const PortableWindowObject *object)
{
    PortableWindowRect rect;
    rect.left = object->offsets[0];
    rect.top = object->offsets[1];
    rect.right = object->offsets[2];
    rect.bottom = object->offsets[3];
    return rect;
}

static void set_origin(PortableWindowObject *object, PortableWindowRect origin)
{
    object->offsets[0] = origin.left;
    object->offsets[1] = origin.top;
    object->offsets[2] = origin.right;
    object->offsets[3] = origin.bottom;
}

static PortableWindowOpenStatus recalculate(PortableWindowRegistry *registry,
                                            int16_t window_id,
                                            const int16_t args[4],
                                            int16_t *inner_status)
{
    PortableWindowRegistryStatus status =
        portable_window_registry_recalculate(
            registry, (int16_t)((uint16_t)window_id >> 8), args);
    *inner_status = (int16_t)status;
    if (status == PORTABLE_WINDOW_REGISTRY_OK) return PORTABLE_WINDOW_OPEN_OK;
    if (status == PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY)
        return PORTABLE_WINDOW_OPEN_UNSUPPORTED_GEOMETRY;
    if (status == PORTABLE_WINDOW_REGISTRY_NOT_LOADED)
        return PORTABLE_WINDOW_OPEN_NOT_LOADED;
    return PORTABLE_WINDOW_OPEN_REGISTRY_ERROR;
}

PortableWindowOpenStatus portable_window_open_scene_init(
    const PortableWindowRegistry *registry,
    const int16_t *open_order, size_t open_count,
    PortableWindowOpenScene *scene)
{
    uint16_t i;
    if (registry == NULL || scene == NULL || !registry->initialized ||
        (open_count != 0 && open_order == NULL))
        return PORTABLE_WINDOW_OPEN_BAD_ARGUMENT;
    if (open_count > PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_WINDOW_OPEN_STACK_FULL;
    memset(scene, 0, sizeof(*scene));
    for (i = 0; i < PORTABLE_WINDOW_REGISTRY_SLOTS; ++i) {
        PortableWindowRegistrySlot *slot =
            (PortableWindowRegistrySlot *)&registry->slots[i];
        if (!slot->loaded) continue;
        scene->windows[i].flags =
            (uint16_t)(slot->window.flags & ~PORTABLE_WINDOW_OPEN);
        if (slot->window.count != 0)
            scene->windows[i].origin = origin_rect(&slot->window.objects[0]);
    }
    scene->front_window_id = PORTABLE_WINDOW_OPEN_NONE;
    for (i = 0; i < open_count; ++i) {
        int16_t id = open_order[i];
        uint16_t index;
        size_t j;
        if (!valid_window_id(registry, id)) return PORTABLE_WINDOW_OPEN_INVALID_STATE;
        index = (uint16_t)id >> 8;
        if (!registry->slots[index].loaded) return PORTABLE_WINDOW_OPEN_NOT_LOADED;
        for (j = 0; j < i; ++j)
            if (open_order[j] == id) return PORTABLE_WINDOW_OPEN_INVALID_STATE;
        scene->order[i] = id;
        scene->windows[index].flags |= PORTABLE_WINDOW_OPEN;
    }
    scene->open_count = (uint16_t)open_count;
    if (open_count != 0) scene->front_window_id = open_order[0];
    scene->initialized = 1;
    return PORTABLE_WINDOW_OPEN_OK;
}

PortableWindowOpenStatus portable_window_open_apply(
    PortableWindowRegistry *registry,
    PortableWindowOpenScene *scene,
    int16_t window_id,
    const int16_t window_args[4],
    int16_t screen_width, int16_t screen_height,
    const PortableWindowRect *menu_rect,
    PortableWindowOpenResult *result)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowState *state;
    PortableWindowRect frame;
    PortableWindowOpenStatus status;
    int16_t idx, inner_status = 0;
    int dx = 0, dy = 0;
    int position_flags;
    int found;
    int16_t previous_front;

    if (registry == NULL || scene == NULL || !scene->initialized ||
        window_args == NULL || menu_rect == NULL || result == NULL)
        return PORTABLE_WINDOW_OPEN_BAD_ARGUMENT;
    memset(result, 0, sizeof(*result));
    if (!valid_window_id(registry, window_id) || screen_width <= 0 ||
        screen_height <= 0 || menu_rect->left > menu_rect->right ||
        menu_rect->top > menu_rect->bottom ||
        scene->open_count > PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_WINDOW_OPEN_INVALID_STATE;
    slot = get_loaded_slot(registry, window_id);
    if (slot == NULL)
        return valid_window_id(registry, window_id)
            ? PORTABLE_WINDOW_OPEN_NOT_LOADED : PORTABLE_WINDOW_OPEN_INVALID_STATE;
    idx = (int16_t)((uint16_t)window_id >> 8);
    state = &scene->windows[idx];
    result->already_front = (uint8_t)(scene->front_window_id == window_id);
    if (result->already_front) {
        result->frame_before_move = slot->window.rect;
        result->frame_after = slot->window.rect;
        add_event(result, PORTABLE_WINDOW_OPEN_FLUSH_EVENTS, window_id);
        return PORTABLE_WINDOW_OPEN_OK;
    }
    if (scene->open_count >= PORTABLE_WINDOW_REGISTRY_SLOTS &&
        order_find(scene, window_id) < 0)
        return PORTABLE_WINDOW_OPEN_STACK_FULL;

    status = recalculate(registry, window_id, window_args, &inner_status);
    result->registry_status = inner_status;
    if (status != PORTABLE_WINDOW_OPEN_OK) return status;
    add_event(result, PORTABLE_WINDOW_OPEN_RECALCULATE, window_id);
    frame = slot->window.rect;
    result->frame_before_move = frame;
    position_flags = (state->flags & PORTABLE_WINDOW_MOVABLE) != 0;
    previous_front = scene->front_window_id;
    if (position_flags) {
        /* win_Open saves all four origin words before any clamp movement. */
        state->saved_origin = origin_rect(&slot->window.objects[0]);
        state->has_saved_origin = 1;
        state->origin = state->saved_origin;
        add_event(result, PORTABLE_WINDOW_OPEN_SAVE_ORIGIN, window_id);
        if (frame.bottom > screen_height)
            dy = screen_height - frame.bottom;
        else if (frame.top <= menu_rect->bottom)
            dy = menu_rect->bottom - frame.top;
        if (frame.left < 0)
            dx = -frame.left;
        else if (frame.right >= screen_width)
            dx = screen_width - frame.right;
        if (dx != 0 || dy != 0) {
            PortableWindowRect moved = state->saved_origin;
            moved.left = (int16_t)(moved.left + dx);
            moved.top = (int16_t)(moved.top + dy);
            set_origin(&slot->window.objects[0], moved);
            state->origin = moved;
            result->moved = 1;
            result->move_dx = (int16_t)dx;
            result->move_dy = (int16_t)dy;
            add_event(result, PORTABLE_WINDOW_OPEN_MOVE_ORIGIN, window_id);
            add_event(result, PORTABLE_WINDOW_OPEN_RECALCULATE_AFTER_MOVE,
                      window_id);
            status = recalculate(registry, window_id, window_args, &inner_status);
            result->registry_status = inner_status;
            if (status != PORTABLE_WINDOW_OPEN_OK) return status;
        }
    }
    result->frame_after = slot->window.rect;
    /* g_62E0 moves this window to g_5702[0], then win_Open sets bit 0x0200. */
    found = order_find(scene, window_id);
    order_front(scene, window_id);
    if (found < 0 || previous_front != window_id)
        add_event(result, PORTABLE_WINDOW_OPEN_FRONT_CHANGED, window_id);
    state->flags |= PORTABLE_WINDOW_OPEN;
    slot->window.flags |= PORTABLE_WINDOW_OPEN;
    result->opened = 1;
    add_event(result, PORTABLE_WINDOW_OPEN_FLAG_SET, window_id);
    add_event(result, PORTABLE_WINDOW_OPEN_DRAW_REQUESTED, window_id);
    add_event(result, PORTABLE_WINDOW_OPEN_FLUSH_EVENTS, window_id);
    return PORTABLE_WINDOW_OPEN_OK;
}

PortableWindowOpenStatus portable_window_close_apply(
    PortableWindowRegistry *registry,
    PortableWindowOpenScene *scene,
    int16_t window_id,
    PortableWindowOpenResult *result)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowState *state;
    int16_t idx;
    int order_index;
    int was_front;
    if (registry == NULL || scene == NULL || !scene->initialized || result == NULL)
        return PORTABLE_WINDOW_OPEN_BAD_ARGUMENT;
    memset(result, 0, sizeof(*result));
    if (!valid_window_id(registry, window_id)) return PORTABLE_WINDOW_OPEN_INVALID_STATE;
    slot = get_loaded_slot(registry, window_id);
    if (slot == NULL) return PORTABLE_WINDOW_OPEN_NOT_LOADED;
    idx = (int16_t)((uint16_t)window_id >> 8);
    state = &scene->windows[idx];
    result->frame_before_move = slot->window.rect;
    result->frame_after = slot->window.rect;
    if ((state->flags & PORTABLE_WINDOW_OPEN) == 0) return PORTABLE_WINDOW_OPEN_OK;
    add_event(result, PORTABLE_WINDOW_OPEN_FLAG_CLEARED, window_id);
    state->flags &= (uint16_t)~PORTABLE_WINDOW_OPEN;
    slot->window.flags &= (uint16_t)~PORTABLE_WINDOW_OPEN;
    if ((state->flags & PORTABLE_WINDOW_MOVABLE) != 0) {
        PortableWindowRect restore = state->has_saved_origin
            ? state->saved_origin : state->origin;
        set_origin(&slot->window.objects[0], restore);
        state->origin = restore;
        state->has_saved_origin = 0;
        add_event(result, PORTABLE_WINDOW_OPEN_RESTORE_ORIGIN, window_id);
    }
    order_index = order_find(scene, window_id);
    was_front = scene->front_window_id == window_id;
    if (order_index >= 0) order_remove(scene, (uint16_t)order_index);
    if (was_front) {
        scene->front_window_id = scene->open_count != 0
            ? scene->order[0] : PORTABLE_WINDOW_OPEN_NONE;
        add_event(result, PORTABLE_WINDOW_OPEN_FRONT_RESTORED,
                  scene->front_window_id);
    }
    add_event(result, PORTABLE_WINDOW_OPEN_ERASE_REQUESTED, window_id);
    return PORTABLE_WINDOW_OPEN_OK;
}

const char *portable_window_open_status_string(PortableWindowOpenStatus status)
{
    switch (status) {
    case PORTABLE_WINDOW_OPEN_OK: return "ok";
    case PORTABLE_WINDOW_OPEN_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_WINDOW_OPEN_INVALID_STATE: return "invalid open-window state";
    case PORTABLE_WINDOW_OPEN_NOT_LOADED: return "window is not loaded";
    case PORTABLE_WINDOW_OPEN_REGISTRY_ERROR: return "window registry operation failed";
    case PORTABLE_WINDOW_OPEN_UNSUPPORTED_GEOMETRY: return "unsupported window geometry";
    case PORTABLE_WINDOW_OPEN_STACK_FULL: return "window stack is full";
    case PORTABLE_WINDOW_OPEN_OUT_OF_MEMORY: return "out of memory";
    }
    return "unknown window-open error";
}
