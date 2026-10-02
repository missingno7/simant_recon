#include "../../game/recovered/nest_adapter.h"
#include "../nest/native_adapter.h"

#include <stdlib.h>
#include <string.h>

typedef struct TestTickClock {
    int32_t values[2];
    uint32_t calls;
    uint32_t fail_on_call;
} TestTickClock;

static int test_tick_count_provider(void *context, int32_t *value)
{
    TestTickClock *clock = (TestTickClock *)context;
    ++clock->calls;
    if (clock->calls == clock->fail_on_call || clock->calls > 2)
        return 0;
    *value = clock->values[clock->calls - 1];
    return 1;
}

/* The standalone test fixture is deliberately converted to the real
 * generated RecoveredState layout before reaching the production adapter. */
static int sim_recovered_nest_test_run_impl(
    SimNestTestWorld *input_output, SimRng *rng, SimNestRuntime *runtime,
    const SimNestRequest *request, SimNestTrace *trace,
    SimNestTickCountProvider tick_provider, void *tick_context)
{
    RecoveredState *state;
    SimNestStatus status;
    if (input_output == NULL || rng == NULL || runtime == NULL ||
        request == NULL || trace == NULL)
        return SIM_NEST_INVALID_ARGUMENT;
    state = (RecoveredState *)malloc(sizeof(*state));
    if (state == NULL) return SIM_NEST_INVALID_ARGUMENT;
    recovered_state_init(state);
    memcpy(state->MapA, input_output->surface, sizeof state->MapA);
    memcpy(state->MapB, input_output->nest_b, sizeof state->MapB);
    memcpy(state->MapR, input_output->nest_r, sizeof state->MapR);
    memcpy(state->ExitMapB, input_output->exit_b, sizeof state->ExitMapB);
    memcpy(state->ExitMapR, input_output->exit_r, sizeof state->ExitMapR);
    memcpy(state->LifeA, input_output->life_a, sizeof state->LifeA);
    memcpy(state->LifeB, input_output->life_b, sizeof state->LifeB);
    memcpy(state->LifeR, input_output->life_r, sizeof state->LifeR);
    memcpy(state->HoleMapB, input_output->hole_b, sizeof state->HoleMapB);
    memcpy(state->HoleMapR, input_output->hole_r, sizeof state->HoleMapR);
    state->TERRAINset = input_output->terrain_set;
    state->MePlane = input_output->current_ant_plane;
    state->MeLocX = input_output->me_x;
    state->MeLocY = input_output->me_y;
    state->fd_50F6_04C2 = input_output->me_type;
    state->fd_50F6_0496 = input_output->me_direction;
    state->fd_50F6_104E = runtime->alarm_drop_state;
    state->fd_3D57_07BE = runtime->alarm_indicator;
    state->fd_50F6_0228 = runtime->theme_index;
    state->fd_50F6_0214 = runtime->theme_last_tick;
    state->fd_50F6_0FB6 = runtime->invalidate_right;
    state->fd_50F6_0FFA = runtime->invalidate_bottom;
    state->fd_50F6_1068 = runtime->dug_b_x_sum;
    state->fd_50F6_1082 = runtime->dug_b_y_sum;
    state->fd_50F6_108E = runtime->dug_r_x_sum;
    state->fd_50F6_10A2 = runtime->dug_r_y_sum;
    state->fd_50F6_0224 = runtime->dug_b_count;
    state->TilesDugR = runtime->dug_r_count;
    state->fd_50F6_10B2 = runtime->dug_b_x_average;
    state->fd_50F6_10C0 = runtime->dug_b_y_average;
    state->fd_50F6_0200 = runtime->dug_r_x_average;
    state->fd_50F6_020E = runtime->dug_r_y_average;
    state->fd_3D57_02AC[0] = runtime->entrance_b_surface_x;
    state->fd_3D57_02AC[1] = runtime->entrance_b_surface_y;
    state->fd_3D57_02B0[0] = runtime->entrance_r_surface_x;
    state->fd_3D57_02B0[1] = runtime->entrance_r_surface_y;
    state->fd_3D57_02A4[0] = runtime->entrance_b_nest_x;
    state->fd_3D57_02A4[1] = runtime->entrance_b_nest_y;
    state->fd_3D57_02A8[0] = runtime->entrance_r_nest_x;
    state->fd_3D57_02A8[1] = runtime->entrance_r_nest_y;

    status = sim_recovered_nest_apply_with_tick_provider(
        state, rng, request, trace, tick_provider, tick_context);

    memcpy(input_output->surface, state->MapA, sizeof state->MapA);
    memcpy(input_output->nest_b, state->MapB, sizeof state->MapB);
    memcpy(input_output->nest_r, state->MapR, sizeof state->MapR);
    memcpy(input_output->exit_b, state->ExitMapB, sizeof state->ExitMapB);
    memcpy(input_output->exit_r, state->ExitMapR, sizeof state->ExitMapR);
    memcpy(input_output->life_a, state->LifeA, sizeof state->LifeA);
    memcpy(input_output->life_b, state->LifeB, sizeof state->LifeB);
    memcpy(input_output->life_r, state->LifeR, sizeof state->LifeR);
    memcpy(input_output->hole_b, state->HoleMapB, sizeof state->HoleMapB);
    memcpy(input_output->hole_r, state->HoleMapR, sizeof state->HoleMapR);
    input_output->terrain_set = state->TERRAINset;
    input_output->current_ant_plane = state->MePlane;
    input_output->me_x = state->MeLocX;
    input_output->me_y = state->MeLocY;
    input_output->me_type = state->fd_50F6_04C2;
    input_output->me_direction = state->fd_50F6_0496;
    runtime->alarm_drop_state = state->fd_50F6_104E;
    runtime->alarm_indicator = state->fd_3D57_07BE;
    runtime->theme_index = state->fd_50F6_0228;
    runtime->theme_last_tick = state->fd_50F6_0214;
    runtime->invalidate_right = state->fd_50F6_0FB6;
    runtime->invalidate_bottom = state->fd_50F6_0FFA;
    runtime->dug_b_x_sum = state->fd_50F6_1068;
    runtime->dug_b_y_sum = state->fd_50F6_1082;
    runtime->dug_r_x_sum = state->fd_50F6_108E;
    runtime->dug_r_y_sum = state->fd_50F6_10A2;
    runtime->dug_b_count = state->fd_50F6_0224;
    runtime->dug_r_count = state->TilesDugR;
    runtime->dug_b_x_average = state->fd_50F6_10B2;
    runtime->dug_b_y_average = state->fd_50F6_10C0;
    runtime->dug_r_x_average = state->fd_50F6_0200;
    runtime->dug_r_y_average = state->fd_50F6_020E;
    runtime->entrance_b_surface_x = state->fd_3D57_02AC[0];
    runtime->entrance_b_surface_y = state->fd_3D57_02AC[1];
    runtime->entrance_r_surface_x = state->fd_3D57_02B0[0];
    runtime->entrance_r_surface_y = state->fd_3D57_02B0[1];
    runtime->entrance_b_nest_x = state->fd_3D57_02A4[0];
    runtime->entrance_b_nest_y = state->fd_3D57_02A4[1];
    runtime->entrance_r_nest_x = state->fd_3D57_02A8[0];
    runtime->entrance_r_nest_y = state->fd_3D57_02A8[1];
    free(state);
    return status;
}

int sim_recovered_nest_test_run(SimNestTestWorld *input_output,
                                SimRng *rng, SimNestRuntime *runtime,
                                const SimNestRequest *request,
                                SimNestTrace *trace)
{
    return sim_recovered_nest_test_run_impl(input_output, rng, runtime,
                                             request, trace, NULL, NULL);
}

int sim_recovered_nest_test_run_with_live_clock(
    SimNestTestWorld *input_output, SimRng *rng, SimNestRuntime *runtime,
    SimNestTrace *trace, const int32_t tick_values[2],
    uint32_t fail_on_call, uint32_t *provider_calls)
{
    const SimNestRequest empty_request = {{0, 0}, 0};
    TestTickClock clock;
    int status;
    if (tick_values == NULL || provider_calls == NULL)
        return SIM_NEST_INVALID_ARGUMENT;
    clock.values[0] = tick_values[0];
    clock.values[1] = tick_values[1];
    clock.calls = 0;
    clock.fail_on_call = fail_on_call;
    status = sim_recovered_nest_test_run_impl(
        input_output, rng, runtime, &empty_request, trace,
        test_tick_count_provider, &clock);
    *provider_calls = clock.calls;
    return status;
}

/* The direct native nest function receives SimRng explicitly. This test-only
 * binder satisfies the adapter's shared recovered-RNG boundary; the oracle
 * comparison uses the returned native RNG object for exact state checks. */
void recovered_rng_bind(SimRng *rng) { (void)rng; }
