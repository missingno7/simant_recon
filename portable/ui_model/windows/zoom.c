#include "zoom.h"

#include <limits.h>
#include <string.h>

static int16_t dos_add(int16_t a, int16_t b)
{
    return (int16_t)((uint16_t)a + (uint16_t)b);
}

static int16_t dos_sub(int16_t a, int16_t b)
{
    return (int16_t)((uint16_t)a - (uint16_t)b);
}

static int16_t dos_remainder(int16_t a, int16_t b)
{
    /* MSC 16-bit signed remainder truncates quotient toward zero. */
    int32_t q = (int32_t)a / (int32_t)b;
    return (int16_t)((int32_t)a - q * (int32_t)b);
}

static int16_t dos_grid(int16_t value, int16_t grid)
{
    if (grid != 0)
        value = dos_sub(value, dos_remainder(value, grid));
    return value;
}

static int rect_equal(const PortableWindowRect *a, const PortableWindowRect *b)
{
    return a->left == b->left && a->top == b->top &&
           a->right == b->right && a->bottom == b->bottom;
}

PortableWindowZoomStatus portable_window_zoom_state_from_resource(
    PortableWindowZoomState *state, const PortableWindowResource *resource,
    PortableWindowRect runtime_window_rect, uint16_t runtime_flags)
{
    if (state == NULL || resource == NULL || resource->record_bytes == NULL ||
        resource->record_size < 0x24 || resource->objects == NULL ||
        resource->count == 0)
        return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;

    memset(state, 0, sizeof(*state));
    state->window_rect = runtime_window_rect;
    state->frame_rect.left = resource->objects[0].offsets[0];
    state->frame_rect.top = resource->objects[0].offsets[1];
    state->frame_rect.right = resource->objects[0].offsets[2];
    state->frame_rect.bottom = resource->objects[0].offsets[3];
    state->flags = runtime_flags;
    state->min_width = (int16_t)((uint16_t)resource->record_bytes[0x18] |
        ((uint16_t)resource->record_bytes[0x19] << 8));
    state->min_height = (int16_t)((uint16_t)resource->record_bytes[0x1a] |
        ((uint16_t)resource->record_bytes[0x1b] << 8));
    state->grid_x = (int16_t)((uint16_t)resource->record_bytes[0x20] |
        ((uint16_t)resource->record_bytes[0x21] << 8));
    state->grid_y = (int16_t)((uint16_t)resource->record_bytes[0x22] |
        ((uint16_t)resource->record_bytes[0x23] << 8));
    return PORTABLE_WINDOW_ZOOM_OK;
}

PortableWindowZoomStatus portable_window_zoom_constrain(
    const PortableWindowZoomState *state, const PortableWindowZoomBounds *bounds,
    int mode, PortableWindowRect *rect, size_t iteration_limit)
{
    PortableWindowRect old;
    int16_t dx, dy;
    size_t iteration;

    if (state == NULL || bounds == NULL || rect == NULL ||
        (mode != 0 && mode != 1) || iteration_limit == 0)
        return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
    if (mode) {
        dy = dos_sub(rect->bottom, state->window_rect.bottom);
        dx = dos_sub(rect->right, state->window_rect.right);
    } else {
        dy = dos_sub(rect->top, state->window_rect.top);
        dx = dos_sub(rect->left, state->window_rect.left);
    }
    old = *rect;
    for (iteration = 0; iteration < iteration_limit; ++iteration) {
        int done = 0;
        int16_t previous_dx = dx, previous_dy = dy;
        int16_t width = dos_sub(rect->right, rect->left);
        int16_t height = dos_sub(rect->bottom, rect->top);
        int16_t gx, gy;

        if (rect->left < bounds->screen_right &&
            !((state->flags & PORTABLE_WINDOW_ZOOM_SOURCE_FLAG_1000) &&
              rect->right > bounds->screen_right) &&
            width < bounds->screen_right) {
            if (rect->right >= 0 && width >= state->min_width &&
                !((state->flags & PORTABLE_WINDOW_ZOOM_SOURCE_FLAG_1000) && rect->left < 0)) {
                if (rect->top <= bounds->screen_bottom &&
                    !((state->flags & PORTABLE_WINDOW_ZOOM_SOURCE_FLAG_1000) &&
                      rect->bottom > bounds->screen_bottom)) {
                    if (rect->top > bounds->desktop_top && height >= state->min_height)
                        done = 1;
                    else
                        dy = dos_add(dy, 1);
                } else {
                    dy = dos_sub(dy, 1);
                }
            } else {
                dx = dos_add(dx, 1);
            }
        } else {
            dx = dos_sub(dx, 1);
        }
        gx = dos_grid(dx, state->grid_x);
        gy = dos_grid(dy, state->grid_y);
        if (mode) {
            rect->left = dos_add(state->window_rect.left, 0);
            rect->top = dos_add(state->window_rect.top, 0);
            rect->right = dos_add(state->window_rect.right, gx);
            rect->bottom = dos_add(state->window_rect.bottom, gy);
        } else {
            rect->left = dos_add(state->window_rect.left, gx);
            rect->top = dos_add(state->window_rect.top, gy);
            rect->right = dos_add(state->window_rect.right, gx);
            rect->bottom = dos_add(state->window_rect.bottom, gy);
        }
        if (!rect_equal(&old, rect))
            done = 0;
        else if (!done && previous_dx == dx && previous_dy == dy)
            return PORTABLE_WINDOW_ZOOM_NO_PROGRESS;
        old = *rect;
        if (done)
            return PORTABLE_WINDOW_ZOOM_OK;
    }
    return PORTABLE_WINDOW_ZOOM_ITERATION_LIMIT;
}

static int append(PortableWindowZoomStep *steps, size_t capacity, size_t *count,
                  PortableWindowZoomStepKind kind, int16_t win,
                  PortableWindowRect rect)
{
    if (*count >= capacity) return 0;
    steps[*count].kind = kind;
    steps[*count].window_id = win;
    steps[*count].rect = rect;
    ++*count;
    return 1;
}

PortableWindowZoomStatus portable_window_zoom_toggle(
    PortableWindowZoomState *state, const PortableWindowZoomBounds *bounds,
    const PortableWindowZoomResidue *residue,
    int16_t window_id, const int16_t *open_windows, size_t open_window_capacity,
    const PortableWindowRect *open_object_rects,
    PortableWindowZoomStep *steps, size_t step_capacity, size_t *step_count,
    size_t iteration_limit)
{
    PortableWindowZoomState next;
    PortableWindowZoomStep pending[520];
    size_t n = 0, i, sentinel = open_window_capacity;
    PortableWindowRect r, saved;
    PortableWindowZoomStatus status;

    if (state == NULL || bounds == NULL || residue == NULL || open_windows == NULL ||
        open_object_rects == NULL || steps == NULL ||
        step_count == NULL || step_capacity > SIZE_MAX / sizeof(*steps))
        return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
    *step_count = 0;
    if (window_id == (int16_t)0x8000) return PORTABLE_WINDOW_ZOOM_OK;
    if (!(state->flags & PORTABLE_WINDOW_ZOOM_ENABLED)) {
        if (step_capacity < 2) return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
        steps[0] = (PortableWindowZoomStep){PORTABLE_ZOOM_LOCK, window_id, {0,0,0,0}};
        steps[1] = (PortableWindowZoomStep){PORTABLE_ZOOM_UNLOCK, window_id, {0,0,0,0}};
        *step_count = 2;
        return PORTABLE_WINDOW_ZOOM_DISABLED;
    }
    if (open_window_capacity > 520) return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
    for (i = 0; i < open_window_capacity; ++i)
        if (open_windows[i] == (int16_t)0x8000) { sentinel = i; break; }
    if (sentinel == open_window_capacity || sentinel == 0)
        return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;

    next = *state;
    if (next.flags & PORTABLE_WINDOW_ZOOMED) {
        if (!next.has_zoom_rect) return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
        next.frame_rect = next.zoom_rect;
        next.flags &= (uint16_t)~PORTABLE_WINDOW_ZOOMED;
        saved = next.window_rect;
        r = residue->unzoom_obj_rect;
    } else {
        next.zoom_rect = next.frame_rect;
        next.has_zoom_rect = 1;
        r.left = 0;
        r.top = bounds->desktop_top;
        r.right = residue->first_rect_right;
        r.bottom = residue->first_rect_bottom;
        status = portable_window_zoom_constrain(&next, bounds, 0, &r, iteration_limit);
        if (status != PORTABLE_WINDOW_ZOOM_OK) return status;
        next.window_rect = r; /* The original stores mode-0 result before mode 1. */
        r.bottom = bounds->screen_bottom;
        r.right = bounds->screen_right;
        status = portable_window_zoom_constrain(&next, bounds, 1, &r, iteration_limit);
        if (status != PORTABLE_WINDOW_ZOOM_OK) return status;
        next.window_rect = r;
        next.flags |= PORTABLE_WINDOW_ZOOMED;
        next.frame_rect.left = r.left;
        next.frame_rect.top = r.top;
        next.frame_rect.right = dos_sub(r.right, r.left);
        next.frame_rect.bottom = dos_sub(r.bottom, r.top);
        saved = residue->saved_rect;
    }

#define EMIT(k, w, q) do { if (!append(pending, 520, &n, (k), (w), (q))) \
    return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT; } while (0)
    EMIT(PORTABLE_ZOOM_LOCK, window_id, saved);
    EMIT(PORTABLE_ZOOM_RECALCULATE, window_id, next.window_rect);
    EMIT(PORTABLE_ZOOM_REBUILD_CLIPS, window_id, next.window_rect);
    EMIT(PORTABLE_ZOOM_WINDOW_CALLBACK, window_id, next.window_rect);
    if (next.flags & PORTABLE_WINDOW_ZOOMED) {
        EMIT(PORTABLE_ZOOM_CLIP_SET, window_id, next.window_rect);
        EMIT(PORTABLE_ZOOM_CLIP_RESTORE, window_id, saved);
    } else {
        EMIT(PORTABLE_ZOOM_CLIP_RESTORE, window_id, saved);
        EMIT(PORTABLE_ZOOM_OBJECT_RECT_QUERY, window_id, r);
    }
    EMIT(PORTABLE_ZOOM_UNLOCK, window_id, saved);
    EMIT(PORTABLE_ZOOM_CLIP_PUSH, window_id, saved);
    EMIT(PORTABLE_ZOOM_RESET_CLIP, window_id, saved);
    EMIT(PORTABLE_ZOOM_CLIP_POP, window_id, saved);
    EMIT(PORTABLE_ZOOM_CLIP_EXCLUDE, window_id, r);
    for (i = sentinel; i-- > 1;) {
        EMIT(PORTABLE_ZOOM_CLIP_PUSH, open_windows[i], saved);
        EMIT(PORTABLE_ZOOM_OBJECT_RECT_QUERY, open_windows[i], open_object_rects[i]);
        EMIT(PORTABLE_ZOOM_CLIP_INTERSECT, open_windows[i], open_object_rects[i]);
        EMIT(PORTABLE_ZOOM_DRAW_WINDOW, open_windows[i], open_object_rects[i]);
        EMIT(PORTABLE_ZOOM_CLIP_POP, open_windows[i], saved);
    }
    EMIT(PORTABLE_ZOOM_CLIP_SET, window_id, saved);
    EMIT(PORTABLE_ZOOM_DRAW_WINDOW, open_windows[0], saved);
    EMIT(PORTABLE_ZOOM_BORDER_08EA, window_id, saved);
    EMIT(PORTABLE_ZOOM_BORDER_0831, window_id, saved);
#undef EMIT
    if (n > step_capacity) return PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT;
    memcpy(steps, pending, n * sizeof(*steps));
    *step_count = n;
    *state = next;
    return PORTABLE_WINDOW_ZOOM_OK;
}
