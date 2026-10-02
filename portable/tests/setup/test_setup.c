#include "../../game/simulation/setup.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct SetupTrace {
    unsigned cursor;
    unsigned resource_calls;
    unsigned rect_calls;
    unsigned refresh_calls;
    int fail_resource;
    int fail_rect_at;
    int fail_refresh_at;
    int wide_caste_rect;
} SetupTrace;

static int resource_size(void *context, uint16_t object_id, uint16_t kind,
                         int16_t *width, int16_t *height)
{
    SetupTrace *trace = (SetupTrace *)context;
    assert(trace->cursor++ == 0);
    ++trace->resource_calls;
    assert(object_id == 0x578u && kind == 2u);
    if (trace->fail_resource)
        return 0;
    *width = 9;
    *height = 7;
    return 1;
}

static int get_object_rect(void *context, uint16_t object_id,
                           SimSetupRect *rect)
{
    SetupTrace *trace = (SetupTrace *)context;
    unsigned expected = trace->rect_calls == 0 ? 1u :
                        trace->rect_calls == 1 ? 2u : 4u;
    assert(trace->cursor++ == expected);
    assert(object_id == (trace->rect_calls < 2 ? 0x120du : 0x130du));
    ++trace->rect_calls;
    if (trace->fail_rect_at == (int)trace->rect_calls)
        return 0;
    if (object_id == 0x120du) {
        rect->left = 20;
        rect->top = 10;
        rect->right = 120;
        rect->bottom = 60;
    } else {
        if (trace->wide_caste_rect) {
            rect->left = 0;
            rect->top = 0;
            rect->right = 400;
            rect->bottom = 1;
        } else {
            rect->left = 40;
            rect->top = 15;
            rect->right = 170;
            rect->bottom = 80;
        }
    }
    return 1;
}

static int refresh_control(void *context, SimSetupControlKind kind,
                           const SimSetupControls *controls)
{
    SetupTrace *trace = (SetupTrace *)context;
    unsigned expected = kind == SIM_SETUP_MODE_CONTROL ? 3u : 5u;
    assert(trace->cursor++ == expected);
    assert(kind == (trace->refresh_calls == 0 ? SIM_SETUP_MODE_CONTROL :
                                                   SIM_SETUP_CASTE_CONTROL));
    assert(controls->knob_width == 9 && controls->knob_height == 7);
    ++trace->refresh_calls;
    if (trace->fail_refresh_at == (int)trace->refresh_calls)
        return 0;
    return 1;
}

static SimSetupHooks make_hooks(SetupTrace *trace)
{
    SimSetupHooks hooks;
    hooks.resource_size = resource_size;
    hooks.get_object_rect = get_object_rect;
    hooks.refresh_control = refresh_control;
    hooks.context = trace;
    return hooks;
}

static void test_clear_history(void)
{
    SimSetupState state;
    unsigned i;
    memset(&state, 0xa5, sizeof state);
    sim_setup_clear_history(&state, 0);
    for (i = 0; i < sizeof state.history_series / sizeof state.history_series[0]; ++i) {
        unsigned j;
        for (j = 0; j < 64; ++j)
            assert(state.history_series[i][j] == 0);
    }
    assert(state.history_start == 0x3f && state.graph_selection == 0);
    assert(state.black_ants_eaten == 0 && state.red_ants_eaten == 0);
    assert(state.counter_0f30 == 0 && state.counter_0efc == 0);
    assert(state.history_counter_0fbc == 0 && state.history_counter_0f3e == 0);
    assert(state.history_counter_0fc2 == 0 && state.history_counter_1000 == 0);
    assert(state.value_0ada == (int32_t)0xa5a5a5a5u);
    assert(state.value_0a90 == (int16_t)0xa5a5);

    sim_setup_clear_history(&state, 1);
    assert(state.value_0ada == 0);
    assert(state.value_0a90 == 1 && state.value_0ac4 == 1);
    assert(state.value_0a9e == 0 && state.value_0ac8 == 0);
    sim_setup_clear_history(0, 1);
}

static void test_ideal_caste_uses_both_fractional_slots(void)
{
    SimSetupTriangle level = { 0x1234u, 0xabcdu, 0x7777u };
    int16_t ideal[4] = { -1, -1, -1, -1 };
    int16_t expected_mid = (int16_t)((100u * level.mid + 0x3fffu) / 0xffffu);
    int16_t expected_weight = (int16_t)((100u * level.weight + 0x3fffu) / 0xffffu);
    int16_t expected_frac = (int16_t)((50u * level.frac + 0x3fffu) / 0xffffu);
    sim_setup_convert_ideal_caste(&level, ideal);
    assert(ideal[0] == expected_mid);
    assert(ideal[1] == expected_weight);
    assert(ideal[2] == expected_frac);
    assert(ideal[3] == expected_frac);
    assert(ideal[2] != 0 && ideal[3] != 0);
}

static void test_controls_source_order_and_defaults(void)
{
    SimSetupControls controls;
    SetupTrace trace = { 0 };
    SimSetupHooks hooks = make_hooks(&trace);
    memset(&controls, 0, sizeof controls);
    controls.mode_current = 3;
    controls.caste_current = 2;

    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_OK);
    assert(trace.cursor == 6);
    assert(trace.resource_calls == 1 && trace.rect_calls == 3);
    assert(trace.refresh_calls == 2);
    assert(controls.knob_width == 9 && controls.knob_height == 7);
    assert(controls.mode_auto == 1 && controls.caste_auto == 1);
    assert(controls.mode_enabled == 1 && controls.caste_enabled == 1);
    assert(controls.mode_current == 3 && controls.caste_current == 2);
    assert(controls.state_0370 == -1 && controls.state_024e == -1);
    assert(controls.mode_level.frac == 0x9999u);
    assert(controls.mode_level.mid == 0x3333u);
    assert(controls.mode_level.weight == 0x3333u);
    assert(controls.caste_level.frac == 0);
    assert(controls.caste_level.mid == 0x9999u);
    assert(controls.caste_level.weight == 0x6666u);
    assert(controls.mode_levels[1].frac == 0xffffu);
    assert(controls.mode_levels[1].mid == 0 && controls.mode_levels[1].weight == 0);
    assert(controls.mode_levels[2].frac == 0 &&
           controls.mode_levels[2].mid == 0xffffu &&
           controls.mode_levels[2].weight == 0);
    assert(controls.mode_levels[3].frac == 0 &&
           controls.mode_levels[3].mid == 0 &&
           controls.mode_levels[3].weight == 0xffffu);
    assert(controls.caste_levels[1].frac == 0x7fffu);
    assert(controls.caste_levels[2].frac == 0 &&
           controls.caste_levels[2].mid == 0xffffu &&
           controls.caste_levels[2].weight == 0);
    assert(controls.caste_levels[3].frac == 0 &&
           controls.caste_levels[3].mid == 0 &&
           controls.caste_levels[3].weight == 0xffffu);
    assert(controls.mode_width == 100 && controls.mode_height == 50);
    assert(controls.mode_slope == 256 && controls.caste_slope == 256);
    assert(controls.mode_rect.left == 20 && controls.mode_rect.bottom == 60);
    assert(controls.caste_rect.left == 40 && controls.caste_rect.bottom == 80);
    assert(controls.ideal_caste[0] == (100u * 0x9999u + 0x3fffu) / 0xffffu);
    assert(controls.ideal_caste[1] == (100u * 0x6666u + 0x3fffu) / 0xffffu);
    assert(controls.ideal_caste[2] == (50u * 0u + 0x3fffu) / 0xffffu);
    assert(controls.ideal_caste[3] == controls.ideal_caste[2]);
}

static void test_missing_callbacks_fail_before_side_effects(void)
{
    SimSetupControls controls, before;
    SetupTrace trace = { 0 };
    SimSetupHooks hooks = make_hooks(&trace);
    memset(&controls, 0x5a, sizeof controls);
    before = controls;
    hooks.resource_size = 0;
    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_UNSUPPORTED);
    assert(memcmp(&controls, &before, sizeof controls) == 0);
    assert(trace.cursor == 0);
}

static void test_slope_retains_source_long_width(void)
{
    SimSetupControls controls;
    SetupTrace trace = { 0 };
    SimSetupHooks hooks = make_hooks(&trace);
    memset(&controls, 0, sizeof controls);
    trace.wide_caste_rect = 1;
    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_OK);
    assert(controls.mode_slope == 256);
    assert(controls.caste_slope == 51200);
}

static void test_missing_resource_fails_closed(void)
{
    SimSetupControls controls, before;
    SetupTrace trace = { 0 };
    SimSetupHooks hooks = make_hooks(&trace);
    memset(&controls, 0x5a, sizeof controls);
    before = controls;
    trace.fail_resource = 1;
    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_CALLBACK_FAILED);
    assert(trace.resource_calls == 1 && trace.rect_calls == 0);
    assert(memcmp(&controls, &before, sizeof controls) == 0);
}

static void test_later_callback_failure_does_not_publish_partial_state(void)
{
    SimSetupControls controls, before;
    SetupTrace trace = { 0 };
    SimSetupHooks hooks = make_hooks(&trace);
    memset(&controls, 0x5a, sizeof controls);
    before = controls;
    trace.fail_refresh_at = 1;
    assert(sim_setup_init_controls(&controls, &hooks) == SIM_SETUP_CALLBACK_FAILED);
    assert(trace.resource_calls == 1 && trace.rect_calls == 2);
    assert(trace.refresh_calls == 1);
    assert(memcmp(&controls, &before, sizeof controls) == 0);
}

int main(void)
{
    test_clear_history();
    test_ideal_caste_uses_both_fractional_slots();
    test_controls_source_order_and_defaults();
    test_slope_retains_source_long_width();
    test_missing_callbacks_fail_before_side_effects();
    test_missing_resource_fails_closed();
    test_later_callback_failure_does_not_publish_partial_state();
    puts("setup tests passed");
    return 0;
}
