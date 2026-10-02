#include "control_events.h"

#include <string.h>

static int16_t wrap16(int32_t value)
{
    return (int16_t)(uint16_t)value;
}

static int32_t div_dos(int32_t numerator, int32_t denominator)
{
    /* C99 signed division, as used by the recovered 16/32-bit expressions,
     * truncates toward zero. */
    return numerator / denominator;
}

static int point_in_triangle(const SimSetupPoint *point,
                            const SimSetupRect *rect)
{
    int32_t top = rect->top, bottom = rect->bottom;
    int32_t left = rect->left, right = rect->right;
    int32_t middle = (right + left) / 2;
    int32_t x = point->x, y = point->y;
    if (bottom == top || y >= bottom || y < top)
        return 0;
    if (div_dos((left - middle) * (y - bottom), bottom - top) + left > x)
        return 0;
    if (div_dos((middle - right) * (y - top), top - bottom) + middle < x)
        return 0;
    return 1;
}

static void bound_to_triangle(SimSetupPoint *point, const SimSetupRect *rect)
{
    int32_t top = rect->top, bottom = (int32_t)rect->bottom - 1;
    int32_t left = rect->left, right = rect->right;
    int32_t middle = (right + left) / 2;
    int32_t x = point->x, y = point->y, edge;
    if (y > bottom) y = bottom;
    else if (y < top) y = top;
    edge = div_dos((left - middle) * (y - bottom), bottom - top) + left;
    if (edge > x) x = edge;
    else {
        edge = div_dos((middle - right) * (y - top), top - bottom) + middle;
        if (edge < x) x = edge;
    }
    point->x = wrap16(x);
    point->y = wrap16(y);
}

static SimSetupTriangle *current_level(SimSetupControls *controls,
                                       SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_level
                                          : &controls->caste_level;
}

static SimSetupTriangle *presets(SimSetupControls *controls,
                                 SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? controls->mode_levels
                                          : controls->caste_levels;
}

static int16_t *selector(SimSetupControls *controls, SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_current
                                          : &controls->caste_current;
}

static int16_t *automatic(SimSetupControls *controls,
                          SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_auto
                                          : &controls->caste_auto;
}

static int16_t *percent(SimControlEventPrivateState *state,
                        SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? &state->mode_percent
                                          : &state->caste_percent;
}

static SimSetupPoint *control_point(SimSetupControls *controls,
                                    SimSetupControlKind kind)
{
    return kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_point
                                          : &controls->caste_point;
}

static void triangle_level_from_point(SimSetupTriangle *level,
                                      const SimSetupRect *rect,
                                      const SimSetupPoint *point,
                                      const SimControlEventPrivateState *state)
{
    int32_t width = state->triangle_width;
    int32_t height = state->triangle_height;
    int32_t half_width = state->triangle_width_left;
    int32_t dx = (int32_t)point->x - rect->left;
    int32_t dy = (int32_t)point->y - rect->top;
    uint32_t frac, w;
    int32_t row, delta;

    /* InitTriVars stores positive dimensions; the 8086 `sar` of an odd
     * positive width is equivalent to this division. */
    if (height <= 2 || width < 0)
        return;
    if ((uint16_t)dy > (uint16_t)(height - 2))
        frac = 0;
    else
        frac = (uint32_t)((int64_t)(height - dy - 2) * 0xffff / (height - 2));
    w = frac * (uint32_t)half_width / 0xffffu;
    row = width - (int32_t)w * 2;
    if (row <= 2) {
        level->weight = 0;
        level->mid = 0;
        level->frac = (uint16_t)frac;
        return;
    }
    delta = dx - (int32_t)w;
    if (delta >= row - 2)
        level->weight = (uint16_t)(0xffffu - frac);
    else if (delta <= 2)
        level->weight = 0;
    else
        level->weight = (uint16_t)(((uint32_t)(0xffffu - frac) *
                                    (uint32_t)delta) / (uint32_t)(row - 2));
    level->frac = (uint16_t)frac;
    level->mid = (uint16_t)(0xffffu - level->weight - level->frac);
}

static SimSetupPoint triangle_point_from_level(const SimSetupTriangle *level,
                                               const SimSetupRect *rect,
                                               const SimControlEventPrivateState *state)
{
    int32_t width = state->triangle_width;
    int32_t height = state->triangle_height;
    int32_t half_width = state->triangle_width_left;
    uint32_t w = (uint32_t)half_width * level->frac / 0xffffu;
    int32_t row = width - (int32_t)w * 2;
    SimSetupPoint point;
    point.y = wrap16((int32_t)((uint32_t)(height - 2) *
                    (0xffffu - level->frac) / 0xffffu) + rect->top);
    if (level->frac == 0xffffu || row < 3) {
        int32_t apex_half = ((int32_t)rect->right - rect->left) / 2;
        point.x = wrap16((rect->left + apex_half) + 2);
    } else {
        uint32_t denominator = 0xffffu - level->frac;
        point.x = wrap16((int32_t)((uint32_t)(row - 3) * level->weight /
                        denominator) + rect->left + (int32_t)w + 2);
    }
    return point;
}

static int provider_ok(int (*fn)(void *, uint16_t), void *context,
                       uint16_t arg)
{
    return fn != 0 && fn(context, arg);
}

SimControlEventStatus sim_control_process_event(
    SimSetupControls *controls, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, const SimControlEventMessage *message,
    const SimControlEventProvider *provider)
{
    uint16_t base;
    uint16_t delta;
    SimControlEventStatus result = SIM_CONTROL_EVENT_OK;
    int16_t *auto_flag, *selected;
    int16_t *percent_flag;
    SimSetupTriangle *level, *rows;
    int clip_active = 0;

    if (controls == 0 || private_state == 0 || message == 0 || provider == 0 ||
        (kind != SIM_SETUP_MODE_CONTROL && kind != SIM_SETUP_CASTE_CONTROL))
        return SIM_CONTROL_EVENT_BAD_ARGUMENT;
    if (private_state->triangle_width == 0 || private_state->triangle_height <= 2 ||
        private_state->triangle_width_left == 0 ||
        private_state->triangle_width_left > private_state->triangle_width)
        return SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
    base = kind == SIM_SETUP_MODE_CONTROL ? 0x1200u : 0x1300u;
    /* The source switches without a range guard. Unknown message codes still
     * pass through the window clip set/off pair and do nothing in the switch. */
    delta = (uint16_t)((int32_t)message->code - (int32_t)(base + 3));
    auto_flag = automatic(controls, kind);
    selected = selector(controls, kind);
    percent_flag = percent(private_state, kind);
    level = current_level(controls, kind);
    rows = presets(controls, kind);
    if (*selected < 0 || *selected > 3)
        return SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
    if (provider->clip_set_window == 0 || provider->clip_off == 0)
        return SIM_CONTROL_EVENT_PROVIDER_MISSING;
    if (!provider->clip_set_window(provider->context, base))
        return SIM_CONTROL_EVENT_PROVIDER_FAILED;
    clip_active = 1;

    if (delta == 0) {
        if (!provider_ok(provider->help, provider->context,
                         (uint16_t)(base + 14))) result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
    } else if (delta == 1) {
        if (*auto_flag == 0) {
            *auto_flag = 1;
            if (provider->set_group_visible == 0) result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
            else if (!provider->set_group_visible(provider->context, base, 4, 0))
                result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
        }
    } else if (delta == 2) {
        if (*auto_flag != 0) {
            *auto_flag = 0;
            if (provider->set_group_visible == 0) result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
            else if (!provider->set_group_visible(provider->context, base, 4, 1))
                result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
        }
    } else if (delta >= 3 && delta <= 5) {
        if (provider->select_object == 0 || provider->draw_control == 0) {
            result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
        } else if (!provider->select_object(provider->context, (uint16_t)(base + 5))) {
            result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
        } else {
            rows[*selected] = *level;
            *selected = (int16_t)(message->code - (base + 6));
            *level = rows[*selected];
            *control_point(controls, kind) = triangle_point_from_level(
                level, kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_rect
                                                      : &controls->caste_rect,
                private_state);
            if (!provider->clip_set_window(provider->context, base))
                result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
            else if (!provider->draw_control(provider->context, kind, 3,
                                              controls, (int16_t)*percent_flag))
                result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
            /* Source fallthrough from preset selection into case 2. */
            if (result == SIM_CONTROL_EVENT_OK && *auto_flag != 0) {
                *auto_flag = 0;
                if (provider->set_group_visible == 0)
                    result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
                else if (!provider->set_group_visible(provider->context, base, 4, 1))
                    result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
            }
        }
    } else if (delta == 10) {
        SimSetupRect rect;
        SimSetupPoint point = message->point;
        uint16_t object_id = (uint16_t)(base + 13);
        if (provider->get_object_rect == 0 || provider->pointer_poll == 0 ||
            provider->still_down == 0 || provider->draw_control == 0) {
            result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
        } else if (!provider->get_object_rect(provider->context, object_id, &rect)) {
            result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
        } else if (rect.bottom == rect.top || rect.right == rect.left) {
            result = SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
        } else if (point_in_triangle(&point, &rect)) {
            uint32_t samples = 0;
            SimSetupPoint last = {-1, 0};
            if (*auto_flag != 0) {
                *auto_flag = 0;
                if (provider->select_object == 0 || provider->set_group_visible == 0)
                    result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
                else if (!provider->select_object(provider->context,
                                                  (uint16_t)(base + 5)) ||
                         !provider->set_group_visible(provider->context, base, 4, 1))
                    result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
            }
            if (result == SIM_CONTROL_EVENT_OK &&
                !provider->clip_set_window(provider->context, base))
                result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
            while (result == SIM_CONTROL_EVENT_OK) {
                int down = 0;
                /* The source stores the unbounded point in `last` before
                 * mutating msg->pt through BoundPointToTri. Actual loaded
                 * setup windows keep pointer x nonnegative, making last.x=-1
                 * a first-sample sentinel despite the uninitialized last.y. */
                if (point.x != last.x || point.y != last.y) {
                    last = point;
                    bound_to_triangle(&point, &rect);
                    triangle_level_from_point(level, &rect, &point, private_state);
                    *control_point(controls, kind) = triangle_point_from_level(
                        level, &rect, private_state);
                    if (!provider->draw_control(provider->context, kind, 3,
                                                controls, (int16_t)*percent_flag)) {
                        result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
                        break;
                    }
                }
                if (provider->max_drag_samples != 0 &&
                    samples >= provider->max_drag_samples) {
                    result = SIM_CONTROL_EVENT_DRAG_LIMIT;
                    break;
                }
                ++samples;
                if (!provider->pointer_poll(provider->context, &point)) {
                    result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
                    break;
                }
                if (!provider->still_down(provider->context, &down)) {
                    result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
                    break;
                }
                if (!down) break;
            }
            /* Source commits final current triple to selected row after drag. */
            if (result == SIM_CONTROL_EVENT_OK) {
                rows[*selected] = *level;
                if (kind == SIM_SETUP_CASTE_CONTROL)
                    sim_setup_convert_ideal_caste(level, controls->ideal_caste);
            }
        }
    } else if (delta >= 12 && delta <= 14) {
        *percent_flag ^= 1;
        *control_point(controls, kind) = triangle_point_from_level(
            level, kind == SIM_SETUP_MODE_CONTROL ? &controls->mode_rect
                                                  : &controls->caste_rect,
            private_state);
        if (provider->draw_control == 0) result = SIM_CONTROL_EVENT_PROVIDER_MISSING;
        else if (!provider->draw_control(provider->context, kind, 3, controls,
                                         (int16_t)*percent_flag))
            result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
    }

    if (clip_active && !provider->clip_off(provider->context) &&
        result == SIM_CONTROL_EVENT_OK)
        result = SIM_CONTROL_EVENT_PROVIDER_FAILED;
    return result;
}

const char *sim_control_event_status_string(SimControlEventStatus status)
{
    switch (status) {
    case SIM_CONTROL_EVENT_OK: return "ok";
    case SIM_CONTROL_EVENT_BAD_ARGUMENT: return "bad argument";
    case SIM_CONTROL_EVENT_UNSUPPORTED_CODE: return "unsupported code";
    case SIM_CONTROL_EVENT_INVALID_SOURCE_STATE: return "invalid source state";
    case SIM_CONTROL_EVENT_PROVIDER_MISSING: return "provider missing";
    case SIM_CONTROL_EVENT_PROVIDER_FAILED: return "provider failed";
    case SIM_CONTROL_EVENT_DRAG_LIMIT: return "drag sample limit";
    default: return "unknown status";
    }
}
