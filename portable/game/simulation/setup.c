#include "setup.h"

#include <string.h>

static const SimSetupTriangle initial_mode_levels = { 0x9999u, 0x3333u, 0x3333u };
static const SimSetupTriangle initial_caste_levels = { 0x0000u, 0x9999u, 0x6666u };

static const SimSetupTriangle mode_presets[4] = {
    { 0x9999u, 0x3333u, 0x3333u },
    { 0xffffu, 0x0000u, 0x0000u },
    { 0x0000u, 0xffffu, 0x0000u },
    { 0x0000u, 0x0000u, 0xffffu }
};

static const SimSetupTriangle caste_presets[4] = {
    { 0x0000u, 0x9999u, 0x6666u },
    { 0x7fffu, 0x3fffu, 0x3fffu },
    { 0x0000u, 0xffffu, 0x0000u },
    { 0x0000u, 0x0000u, 0xffffu }
};

void sim_setup_clear_history(SimSetupState *state, int16_t new_game)
{
    if (state == 0)
        return;

    memset(state->history_series, 0, sizeof state->history_series);
    if (new_game == 1) {
        state->value_0ada = 0;
        state->value_0a90 = 1;
        state->value_0ac4 = 1;
        state->value_0a9e = 0;
        state->value_0ac8 = 0;
    }
    state->history_start = 0x3f;
    state->graph_selection = 0;
    state->black_ants_eaten = 0;
    state->counter_0f30 = 0;
    state->counter_0efc = 0;
    state->red_ants_eaten = 0;
    state->history_counter_0fbc = 0;
    state->history_counter_0f3e = 0;
    state->history_counter_0fc2 = 0;
    state->history_counter_1000 = 0;
}

void sim_setup_convert_ideal_caste(const SimSetupTriangle *level,
                                   int16_t ideal[4])
{
    if (level == 0 || ideal == 0)
        return;
    ideal[0] = (int16_t)((100u * level->mid + 0x3fffu) / 0xffffu);
    ideal[1] = (int16_t)((100u * level->weight + 0x3fffu) / 0xffffu);
    ideal[2] = (int16_t)((50u * level->frac + 0x3fffu) / 0xffffu);
    ideal[3] = (int16_t)((50u * level->frac + 0x3fffu) / 0xffffu);
}

static int setup_triangle(SimSetupControls *controls,
                          SimSetupControlKind kind,
                          const SimSetupTriangle *level,
                          const SimSetupRect *rect)
{
    int16_t width = (int16_t)(rect->right - rect->left);
    int16_t height = (int16_t)(rect->bottom - rect->top);
    int16_t half = (int16_t)(width >> 1);
    uint32_t w;
    int32_t row;
    int32_t dot_x;
    int32_t dot_y;
    SimSetupPoint point;
    SimSetupTriangle tri = *level;
    int32_t slope;

    if (height == 0)
        return 0;
    slope = ((int32_t)half << 8) / height;
    dot_y = ((int32_t)(height - 2) * (0xffffu - tri.frac)) / 0xffffu + rect->top;
    w = (uint32_t)(uint16_t)half * tri.frac / 0xffffu;
    row = (int32_t)width - (int32_t)(w * 2u);
    if (tri.frac == 0xffffu || row < 3) {
        dot_x = (int32_t)half + rect->left + 2;
    } else {
        dot_x = ((row - 3) * tri.weight) / (0xffffu - tri.frac) +
                rect->left + (int32_t)w + 2;
    }
    point.x = (int16_t)dot_x;
    point.y = (int16_t)dot_y;

    if (kind == SIM_SETUP_MODE_CONTROL) {
        controls->mode_rect = *rect;
        controls->mode_point = point;
        controls->mode_width = width;
        controls->mode_height = height;
        controls->mode_slope = slope;
    } else {
        controls->caste_rect = *rect;
        controls->caste_point = point;
        controls->caste_width = width;
        controls->caste_height = height;
        controls->caste_slope = slope;
    }
    return 1;
}

static SimSetupStatus refresh_one(SimSetupControls *controls,
                                  const SimSetupHooks *hooks,
                                  SimSetupControlKind kind,
                                  const SimSetupTriangle *level)
{
    SimSetupRect rect;
    uint16_t object_id = kind == SIM_SETUP_MODE_CONTROL ? 0x120du : 0x130du;
    if (!hooks->get_object_rect(hooks->context, object_id, &rect))
        return SIM_SETUP_CALLBACK_FAILED;
    if (!setup_triangle(controls, kind, level, &rect))
        return SIM_SETUP_INVALID_ARGUMENT;
    if (!hooks->refresh_control(hooks->context, kind, controls))
        return SIM_SETUP_CALLBACK_FAILED;
    return SIM_SETUP_OK;
}

SimSetupStatus sim_setup_init_controls(SimSetupControls *controls,
                                      const SimSetupHooks *hooks)
{
    SimSetupControls next;
    SimSetupRect unused_rect;
    SimSetupStatus status;
    int16_t width, height;

    if (controls == 0)
        return SIM_SETUP_INVALID_ARGUMENT;
    if (hooks == 0 || hooks->resource_size == 0 ||
        hooks->get_object_rect == 0 || hooks->refresh_control == 0)
        return SIM_SETUP_UNSUPPORTED;

    /* g_1B50/g_1B4E are not reset by initControls; preserve their existing
     * source-global selections from the caller's context. */
    next = *controls;
    if (!hooks->resource_size(hooks->context, 0x0578u, 2u, &width, &height))
        return SIM_SETUP_CALLBACK_FAILED;
    if (width <= 0 || height <= 0)
        return SIM_SETUP_INVALID_ARGUMENT;
    next.knob_width = width;
    next.knob_height = height;
    if (!hooks->get_object_rect(hooks->context, 0x120du, &unused_rect))
        return SIM_SETUP_CALLBACK_FAILED;

    next.mode_auto = 1;
    next.caste_auto = 1;
    next.mode_enabled = 1;
    next.caste_enabled = 1;
    next.state_0370 = -1;
    next.state_024e = -1;
    next.mode_level = initial_mode_levels;
    next.caste_level = initial_caste_levels;
    memcpy(next.mode_levels, mode_presets, sizeof mode_presets);
    memcpy(next.caste_levels, caste_presets, sizeof caste_presets);

    status = refresh_one(&next, hooks, SIM_SETUP_MODE_CONTROL,
                         &next.mode_level);
    if (status != SIM_SETUP_OK)
        return status;
    status = refresh_one(&next, hooks, SIM_SETUP_CASTE_CONTROL,
                         &next.caste_level);
    if (status != SIM_SETUP_OK)
        return status;

    sim_setup_convert_ideal_caste(&next.caste_level, next.ideal_caste);

    *controls = next;
    return SIM_SETUP_OK;
}
