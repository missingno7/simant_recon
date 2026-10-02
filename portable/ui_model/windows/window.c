#include "window.h"

#include <stdlib.h>
#include <string.h>

enum {
    WINDOW_HEADER_SIZE = 0x2c,
    WINDOW_COUNT_OFFSET = 0x0c,
    WINDOW_FLAGS_OFFSET = 0x1c,
    WINDOW_OBJECT_TABLE = 0x2c,
    OBJECT_FIXED_SIZE = 0x28,
    OBJECT_SIZE_OFFSET = 0x22,
    OBJECT_GROUP_OFFSET = 0x20,
    OBJECT_TYPE_OFFSET = 0x21,
    OBJECT_FLAGS_OFFSET = 0x24,
    OBJECT_VALUE_OFFSET = 0x26,
    OBJECT_INDICES_OFFSET = 0x10,
    OBJECT_MODES_OFFSET = 0x18
};

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int16_t read_i16(const uint8_t *p)
{
    return (int16_t)read_le16(p);
}

static PortableWindowRect read_rect(const uint8_t *p)
{
    PortableWindowRect r;
    r.left = read_i16(p);
    r.top = read_i16(p + 2);
    r.right = read_i16(p + 4);
    r.bottom = read_i16(p + 6);
    return r;
}

static size_t required_fixed_size(uint8_t type)
{
    switch (type) {
    case 0: case 2: case 15: case 19: case 20: case 21: case 22:
        return 0x29;
    case 4:
        return 0x38;
    case 6: case 7: case 8:
        return 0x2a;
    case 13:
        return 0x2c;
    default:
        return OBJECT_FIXED_SIZE;
    }
}

static int bounded_string(const uint8_t *bytes, size_t start, size_t end)
{
    size_t i;
    if (start >= end) return 0;
    for (i = start; i < end; ++i)
        if (bytes[i] == 0) return 1;
    return 0;
}

static int object_layout_valid(const uint8_t *data, size_t total,
                               uint16_t offset, uint16_t size)
{
    uint8_t type;
    size_t required;
    size_t end;

    if ((size_t)offset > total || (size_t)size > total - (size_t)offset ||
        size < OBJECT_FIXED_SIZE)
        return 0;
    type = data[offset + OBJECT_TYPE_OFFSET];
    required = required_fixed_size(type);
    if (size < required) return 0;
    end = (size_t)offset + size;
    if (type == 5 || type == 9 || type == 12)
        return bounded_string(data, (size_t)offset + 0x2a, end);
    if (type == 16 || type == 17 || type == 18)
        return bounded_string(data, (size_t)offset + 0x2e, end);
    return 1;
}

PortableWindowStatus portable_window_decode(const PortableDbRecord *record,
                                             PortableWindowResource *window)
{
    uint16_t count;
    size_t table_end;
    size_t i;
    uint8_t *data;
    PortableWindowObject *objects;

    if (window == NULL || record == NULL || record->data == NULL)
        return PORTABLE_WINDOW_BAD_ARGUMENT;
    memset(window, 0, sizeof(*window));
    if (record->kind != 0 || record->id < 0 || record->id > 0xff)
        return PORTABLE_WINDOW_WRONG_RESOURCE;
    if (record->size < WINDOW_HEADER_SIZE)
        return PORTABLE_WINDOW_TRUNCATED;
    data = record->data;
    count = read_le16(data + WINDOW_COUNT_OFFSET);
    if (count == 0 || count > 256)
        return PORTABLE_WINDOW_BAD_LAYOUT;
    table_end = WINDOW_OBJECT_TABLE + (size_t)count * 4u;
    if (table_end > record->size)
        return PORTABLE_WINDOW_TRUNCATED;
    objects = (PortableWindowObject *)calloc(count, sizeof(*objects));
    if (objects == NULL)
        return PORTABLE_WINDOW_OUT_OF_MEMORY;

    for (i = 0; i < count; ++i) {
        const uint8_t *entry = data + WINDOW_OBJECT_TABLE + i * 4u;
        uint16_t offset = read_le16(entry);
        uint16_t size;
        const uint8_t *source;
        int k;

        if ((size_t)offset < table_end || (size_t)offset > record->size ||
            record->size - (size_t)offset < OBJECT_SIZE_OFFSET + 2u) {
            free(objects);
            return PORTABLE_WINDOW_BAD_LAYOUT;
        }
        source = data + offset;
        size = read_le16(source + OBJECT_SIZE_OFFSET);
        if (!object_layout_valid(data, record->size, offset, size)) {
            free(objects);
            return PORTABLE_WINDOW_BAD_LAYOUT;
        }
        objects[i].resource_offset = offset;
        objects[i].resource_size = size;
        objects[i].rect = read_rect(source);
        for (k = 0; k < 4; ++k)
            objects[i].offsets[k] = read_i16(source + 8 + k * 2);
        objects[i].group = source[OBJECT_GROUP_OFFSET];
        objects[i].type = source[OBJECT_TYPE_OFFSET];
        objects[i].flags = read_le16(source + OBJECT_FLAGS_OFFSET);
        objects[i].value = read_le16(source + OBJECT_VALUE_OFFSET);
        for (k = 0; k < 4; ++k) {
            objects[i].indices[k] = read_i16(source + OBJECT_INDICES_OFFSET + k * 2);
            objects[i].modes[k] = read_i16(source + OBJECT_MODES_OFFSET + k * 2);
        }
        objects[i].resource_bytes = source;
    }

    window->resource_id = record->id;
    window->count = count;
    window->rect = read_rect(data);
    window->flags = read_le16(data + WINDOW_FLAGS_OFFSET);
    window->record_bytes = data;
    window->record_size = record->size;
    window->objects = objects;
    return PORTABLE_WINDOW_OK;
}

void portable_window_release(PortableWindowResource *window)
{
    if (window == NULL) return;
    free(window->objects);
    memset(window, 0, sizeof(*window));
}

const char *portable_window_status_string(PortableWindowStatus status)
{
    switch (status) {
    case PORTABLE_WINDOW_OK: return "ok";
    case PORTABLE_WINDOW_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_WINDOW_WRONG_RESOURCE: return "not an ordinary window record";
    case PORTABLE_WINDOW_TRUNCATED: return "truncated window record";
    case PORTABLE_WINDOW_BAD_LAYOUT: return "invalid window resource layout";
    case PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT:
        return "constraint requires an external window or unsupported input";
    case PORTABLE_WINDOW_OUT_OF_MEMORY: return "out of memory";
    }
    return "unknown window error";
}

static int16_t *rect_axis(PortableWindowRect *rect, unsigned axis)
{
    switch (axis) {
    case 0: return &rect->left;
    case 1: return &rect->top;
    case 2: return &rect->right;
    default: return &rect->bottom;
    }
}

static int16_t rect_component(const PortableWindowRect *rect, unsigned kind)
{
    switch (kind) {
    case 0: return rect->left;
    case 1: return rect->top;
    case 2: return rect->right;
    default: return rect->bottom;
    }
}

static void normalize_rect(PortableWindowRect *rect)
{
    int16_t swap;
    if (rect->left > rect->right) {
        swap = rect->left; rect->left = rect->right; rect->right = swap;
    }
    if (rect->top > rect->bottom) {
        swap = rect->top; rect->top = rect->bottom; rect->bottom = swap;
    }
}

PortableWindowStatus portable_window_recalculate(PortableWindowResource *window,
                                                 const int16_t window_args[4])
{
    size_t pass_limit;
    size_t pass;
    int changed;

    if (window == NULL || window->objects == NULL || window->count == 0)
        return PORTABLE_WINDOW_BAD_ARGUMENT;
    for (pass = 0; pass < window->count; ++pass) {
        if ((window->objects[pass].flags & 0x0040u) != 0)
            return PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT;
        window->objects[pass].rect = (PortableWindowRect){
            (int16_t)0x8000, (int16_t)0x8000,
            (int16_t)0x8000, (int16_t)0x8000
        };
    }
    pass_limit = (size_t)window->count * 4u + 1u;
    for (pass = 0; pass < pass_limit; ++pass) {
        uint16_t i;
        changed = 0;
        for (i = 0; i < window->count; ++i) {
            PortableWindowObject *object = &window->objects[i];
            unsigned axis;
            for (axis = 0; axis < 4; ++axis) {
                int16_t value;
                int16_t mode = object->modes[axis];
                int16_t *destination = rect_axis(&object->rect, axis);
                if (mode == 0) {
                    value = 0;
                } else if (mode >= 1 && mode <= 4) {
                    uint16_t reference = (uint16_t)object->indices[axis];
                    uint8_t target_resource = (uint8_t)(reference >> 8);
                    uint8_t target_object = (uint8_t)reference;
                    if (target_resource != (uint8_t)window->resource_id ||
                        target_object >= window->count)
                        return PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT;
                    value = rect_component(&window->objects[target_object].rect,
                                           (unsigned)(mode - 1));
                } else if (mode == 5) {
                    int16_t arg = object->indices[axis];
                    if (window_args == NULL || arg < 0 || arg >= 4)
                        return PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT;
                    value = window_args[arg];
                } else {
                    return PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT;
                }
                if (value != (int16_t)0x8000)
                    value = (int16_t)((uint16_t)value + (uint16_t)object->offsets[axis]);
                if (*destination != value) {
                    *destination = value;
                    ++changed;
                }
            }
        }
        if (changed == 0) break;
    }
    for (pass = 0; pass < window->count; ++pass)
        normalize_rect(&window->objects[pass].rect);
    window->rect = window->objects[0].rect;
    return PORTABLE_WINDOW_OK;
}

PortableWindowStatus portable_window_apply_origin_profile(
    PortableWindowResource *window, const uint8_t *profile, size_t profile_size)
{
    size_t offset;
    PortableWindowRect saved;
    int k;

    if (window == NULL || window->objects == NULL || profile == NULL)
        return PORTABLE_WINDOW_BAD_ARGUMENT;
    offset = (size_t)(uint16_t)window->resource_id * 8u;
    if (offset > profile_size || profile_size - offset < 8u)
        return PORTABLE_WINDOW_TRUNCATED;
    saved = read_rect(profile + offset);
    if (saved.left == (int16_t)0x8000)
        return PORTABLE_WINDOW_OK;
    for (k = 0; k < 4; ++k)
        window->objects[0].offsets[k] = rect_component(&saved, (unsigned)k);
    return PORTABLE_WINDOW_OK;
}

int portable_window_rect_contains(const PortableWindowRect *rect,
                                  PortableWindowPoint point)
{
    return rect != NULL && rect->right > point.x && rect->left <= point.x &&
           rect->top <= point.y && point.y < rect->bottom;
}

int portable_window_hit_test(const PortableWindowResource *window,
                             PortableWindowPoint point)
{
    uint16_t i;
    if (window == NULL || window->objects == NULL) return -1;
    for (i = 1; i < window->count; ++i) {
        const PortableWindowObject *object = &window->objects[i];
        if ((object->flags & PORTABLE_WINDOW_OBJECT_SELECTABLE) != 0 &&
            portable_window_rect_contains(&object->rect, point))
            return i;
    }
    return -1;
}

size_t portable_window_render_trace(const PortableWindowResource *window,
                                    int surface_ready,
                                    int draw_hook_enabled,
                                    PortableWindowRenderStep *steps,
                                    size_t capacity)
{
    size_t needed = 0;
    uint16_t i;

    if (window == NULL || window->objects == NULL ||
        (window->flags & 0x0020u) != 0)
        return 0;
    if (surface_ready) {
        if (draw_hook_enabled && needed < capacity && steps != NULL)
            steps[needed] = (PortableWindowRenderStep){PORTABLE_WINDOW_HOOK_BEFORE, 0};
        if (draw_hook_enabled) ++needed;
        for (i = 0; i < window->count; ++i) {
            if (needed < capacity && steps != NULL)
                steps[needed] = (PortableWindowRenderStep){PORTABLE_WINDOW_DRAW_OBJECT, i};
            ++needed;
        }
        if (needed < capacity && steps != NULL)
            steps[needed] = (PortableWindowRenderStep){PORTABLE_WINDOW_DRAW_FRAME, 0};
        ++needed;
    }
    if (draw_hook_enabled) {
        if (needed < capacity && steps != NULL)
            steps[needed] = (PortableWindowRenderStep){PORTABLE_WINDOW_HOOK_AFTER, 0};
        ++needed;
    }
    return needed;
}

static void set_group_flag(PortableWindowResource *window, uint8_t group,
                           uint16_t bit, int enabled)
{
    uint16_t i;
    if (window == NULL || window->objects == NULL) return;
    for (i = 0; i < window->count; ++i) {
        PortableWindowObject *object = &window->objects[i];
        if (object->group == group) {
            if (enabled) object->flags |= bit;
            else object->flags &= (uint16_t)~bit;
        }
    }
}

void portable_window_set_group_visible(PortableWindowResource *window,
                                       uint8_t group, int visible)
{
    set_group_flag(window, group, PORTABLE_WINDOW_OBJECT_VISIBLE, visible);
}

void portable_window_set_group_selectable(PortableWindowResource *window,
                                          uint8_t group, int selectable)
{
    set_group_flag(window, group, PORTABLE_WINDOW_OBJECT_SELECTABLE, selectable);
}

void portable_window_set_group_selected(PortableWindowResource *window,
                                        uint8_t group, int selected)
{
    set_group_flag(window, group, PORTABLE_WINDOW_OBJECT_SELECTED, selected);
}

int portable_window_dialog_result(int16_t window_id, int event_code,
                                  uint8_t ascii_key, int *result)
{
    if (result == NULL || window_id != 0x2100) return 0;
    switch (event_code) {
    case 0x2103: *result = 0; return 1;
    case 0x2104: *result = 1; return 1;
    case 0x2105: *result = 2; return 1;
    }
    if (ascii_key == 'D' || ascii_key == 'd' || ascii_key == '\r') {
        *result = 0;
        return 1;
    }
    if (ascii_key == 'S' || ascii_key == 's') {
        *result = 1;
        return 1;
    }
    if (ascii_key == 0x1b || ascii_key == 'C' || ascii_key == 'c') {
        *result = 2;
        return 1;
    }
    return 0;
}

PortableScenarioAction portable_newgame_scenario_action(int result_code,
                                                        int *scenario_id)
{
    switch (result_code) {
    case 0x202:
        if (scenario_id != NULL) *scenario_id = 1;
        return PORTABLE_SCENARIO_START;
    case 0x203:
        if (scenario_id != NULL) *scenario_id = 2;
        return PORTABLE_SCENARIO_START;
    case 0x204:
        if (scenario_id != NULL) *scenario_id = 3;
        return PORTABLE_SCENARIO_START;
    case 0x206:
        if (scenario_id != NULL) *scenario_id = 0;
        return PORTABLE_SCENARIO_START;
    case 0x205:
        return PORTABLE_SCENARIO_CANCEL;
    case 0x207:
        return PORTABLE_SCENARIO_CONFIRM_TRANSFER;
    default:
        return PORTABLE_SCENARIO_UNRECOGNIZED;
    }
}

void portable_window_lock(PortableWindowState *state)
{
    if (state != NULL && state->lock_depth != UINT16_MAX) ++state->lock_depth;
}

int portable_window_unlock(PortableWindowState *state)
{
    if (state == NULL || state->lock_depth == 0) return 0;
    --state->lock_depth;
    return 1;
}

void portable_window_set_origin(PortableWindowState *state,
                               PortableWindowRect origin)
{
    if (state != NULL) state->origin = origin;
}

int portable_window_open(PortableWindowState *state)
{
    if (state == NULL || (state->flags & PORTABLE_WINDOW_OPEN) != 0) return 0;
    if ((state->flags & PORTABLE_WINDOW_MOVABLE) != 0) {
        state->saved_origin = state->origin;
        state->has_saved_origin = 1;
    }
    state->flags |= PORTABLE_WINDOW_OPEN;
    return 1;
}

int portable_window_close(PortableWindowState *state)
{
    if (state == NULL || (state->flags & PORTABLE_WINDOW_OPEN) == 0) return 0;
    state->flags &= (uint16_t)~PORTABLE_WINDOW_OPEN;
    if ((state->flags & PORTABLE_WINDOW_MOVABLE) != 0 && state->has_saved_origin) {
        state->origin = state->saved_origin;
        state->has_saved_origin = 0;
    }
    return 1;
}
