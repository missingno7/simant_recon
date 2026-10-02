#include "decorations.h"

#include <limits.h>

static const PortableWindowDecorationMetrics *find_metric(
    const PortableWindowDecorationInput *input, int16_t object_id)
{
    size_t i;
    for (i = 0; i < input->metric_count; ++i) {
        if (input->metrics[i].object_id == object_id)
            return &input->metrics[i];
    }
    return 0;
}

static int fits_i16(int32_t value)
{
    return value >= INT16_MIN && value <= INT16_MAX;
}

static PortableWindowDecorationStatus append(
    PortableWindowDecorationStep *steps, size_t capacity, size_t *count,
    PortableWindowDecorationStep step)
{
    if (*count >= capacity)
        return PORTABLE_WINDOW_DECORATION_CAPACITY;
    steps[(*count)++] = step;
    return PORTABLE_WINDOW_DECORATION_OK;
}

static PortableWindowDecorationStatus lookup(
    const PortableWindowDecorationInput *input,
    PortableWindowDecorationStep *steps, size_t capacity, size_t *count,
    int16_t object_id, const PortableWindowDecorationMetrics **metric)
{
    PortableWindowDecorationStep step = {0};
    *metric = find_metric(input, object_id);
    if (!*metric)
        return PORTABLE_WINDOW_DECORATION_MISSING_METRIC;
    step.kind = PORTABLE_WINDOW_DECORATION_LOOKUP_SIZE;
    step.object_id = object_id;
    return append(steps, capacity, count, step);
}

static PortableWindowDecorationStatus register_icon(
    const PortableWindowDecorationInput *input,
    PortableWindowDecorationStep *steps, size_t capacity, size_t *count,
    int16_t x, int16_t y, int16_t object_id, int16_t mode,
    const PortableWindowDecorationMetrics *metric)
{
    PortableWindowDecorationStep step = {0};
    int32_t right, bottom;
    step.kind = input->show ? PORTABLE_WINDOW_DECORATION_REGISTER
                            : PORTABLE_WINDOW_DECORATION_UNREGISTER;
    step.object_id = object_id;
    step.mode = mode;
    step.x = x;
    step.y = y;
    if (input->show) {
        right = (int32_t)x + metric->width;
        bottom = (int32_t)y + metric->height;
        if (!fits_i16(right) || !fits_i16(bottom))
            return PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW;
        step.hit_rect.left = x;
        step.hit_rect.top = y;
        step.hit_rect.right = (int16_t)right;
        step.hit_rect.bottom = (int16_t)bottom;
    }
    return append(steps, capacity, count, step);
}

static PortableWindowDecorationStatus checked_add(int16_t *value, int16_t delta)
{
    int32_t result = (int32_t)*value + delta;
    if (!fits_i16(result))
        return PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW;
    *value = (int16_t)result;
    return PORTABLE_WINDOW_DECORATION_OK;
}

static PortableWindowDecorationStatus checked_sub(int16_t *value, int16_t delta)
{
    int32_t result = (int32_t)*value - delta;
    if (!fits_i16(result))
        return PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW;
    *value = (int16_t)result;
    return PORTABLE_WINDOW_DECORATION_OK;
}

PortableWindowDecorationStatus portable_window_decorations_plan(
    const PortableWindowDecorationInput *input,
    PortableWindowDecorationStep *steps,
    size_t capacity,
    size_t *step_count)
{
    PortableWindowRect r;
    PortableWindowDecorationStatus status;
    const PortableWindowDecorationMetrics *m;
    size_t count = 0;
    int32_t l, t, rr, b;
    if (!input || !step_count || (!steps && capacity) ||
        (!input->metrics && input->metric_count))
        return PORTABLE_WINDOW_DECORATION_BAD_ARGUMENT;
    *step_count = 0;
    l = (int32_t)input->window_rect.left + input->margin;
    t = (int32_t)input->window_rect.top + input->margin;
    rr = (int32_t)input->window_rect.right - input->margin;
    b = (int32_t)input->window_rect.bottom - input->margin;
    if (!fits_i16(l) || !fits_i16(t) || !fits_i16(rr) || !fits_i16(b))
        return PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW;
    r.left = (int16_t)l;
    r.top = (int16_t)t;
    r.right = (int16_t)rr;
    r.bottom = (int16_t)b;

#define APPEND_REG(x_, y_, id_, mode_, metric_) do { \
    status = register_icon(input, steps, capacity, &count, (x_), (y_), \
                           (id_), (mode_), (metric_)); \
    if (status != PORTABLE_WINDOW_DECORATION_OK) goto done; \
} while (0)
#define APPEND_LOOKUP(id_, metric_) do { \
    status = lookup(input, steps, capacity, &count, (id_), &(metric_)); \
    if (status != PORTABLE_WINDOW_DECORATION_OK) goto done; \
} while (0)
#define APPEND_INTERNAL_LOOKUP(id_, metric_) do { \
    if (input->show) APPEND_LOOKUP((id_), (metric_)); \
} while (0)

    if (input->window_flags & 4) {
        m = find_metric(input, 0x64);
        if (input->show && !m) { status = PORTABLE_WINDOW_DECORATION_MISSING_METRIC; goto done; }
        APPEND_INTERNAL_LOOKUP(0x64, m);
        APPEND_REG(r.left, r.top, 0x64, (int16_t)0xf083, m);
        APPEND_LOOKUP(0x64, m);
        status = checked_add(&r.left, m->width);
        if (status != PORTABLE_WINDOW_DECORATION_OK) goto done;
    }
    if (input->window_flags & 8) {
        int16_t x, y;
        APPEND_LOOKUP(0x70, m);
        APPEND_INTERNAL_LOOKUP(0x70, m);
        x = r.right;
        y = r.bottom;
        status = checked_sub(&x, m->width);
        if (status != PORTABLE_WINDOW_DECORATION_OK) goto done;
        status = checked_sub(&y, m->height);
        if (status != PORTABLE_WINDOW_DECORATION_OK) goto done;
        APPEND_REG(x, y, 0x70, (int16_t)0xf084, m);
    }
    if (input->window_flags & 0x100) {
        int16_t icon = (input->window_flags & 0x80) ? 0x66 : 0x67;
        APPEND_LOOKUP(icon, m);
        status = checked_sub(&r.right, m->width);
        if (status != PORTABLE_WINDOW_DECORATION_OK) goto done;
        APPEND_INTERNAL_LOOKUP(icon, m);
        APPEND_REG(r.right, r.top, icon, (int16_t)0xf085, m);
    }
    if (input->window_flags & 0x10) {
        m = find_metric(input, 0x65);
        if (input->show && !m) { status = PORTABLE_WINDOW_DECORATION_MISSING_METRIC; goto done; }
        APPEND_INTERNAL_LOOKUP(0x65, m);
        APPEND_REG(r.left, r.top, 0x65, (int16_t)0xf088, m);
    }
    if (input->window_flags & 0x400) {
        APPEND_LOOKUP(0x69, m);
        status = checked_sub(&r.right, m->width);
        if (status != PORTABLE_WINDOW_DECORATION_OK) goto done;
        APPEND_INTERNAL_LOOKUP(0x69, m);
        APPEND_REG(r.right, r.top, 0x69, (int16_t)0xf082, m);
    }
    status = PORTABLE_WINDOW_DECORATION_OK;
done:
    *step_count = count;
#undef APPEND_REG
#undef APPEND_LOOKUP
#undef APPEND_INTERNAL_LOOKUP
    return status;
}

int portable_window_decoration_hit_test(
    const PortableWindowDecorationStep *steps,
    size_t step_count,
    PortableWindowPoint point,
    PortableWindowDecorationHit *hit)
{
    size_t i;
    if ((!steps && step_count) || !hit)
        return 0;
    for (i = step_count; i > 0; --i) {
        const PortableWindowDecorationStep *step = &steps[i - 1];
        if (step->kind != PORTABLE_WINDOW_DECORATION_REGISTER)
            continue;
        if (point.x >= step->hit_rect.left && point.x <= step->hit_rect.right &&
            point.y >= step->hit_rect.top && point.y <= step->hit_rect.bottom) {
            hit->object_id = step->object_id;
            hit->mode = step->mode;
            return 1;
        }
    }
    return 0;
}
