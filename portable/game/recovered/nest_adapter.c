#include "nest_adapter.h"

#include <stdlib.h>
#include <string.h>

/* Implemented by recovered_native_adapters.c. Both the generated helpers and
 * this transition must consume the same state-bound generator. */
extern void recovered_rng_bind(SimRng *rng);

static _Thread_local SimRecoveredNestBinding *active_binding;

void sim_recovered_nest_bind(SimRecoveredNestBinding *binding)
{
    if (binding == NULL || binding->rng == NULL || binding->request == NULL ||
        binding->trace == NULL || active_binding != NULL)
        abort();
    binding->status = SIM_NEST_INVALID_ARGUMENT;
    binding->calls = 0;
    memset(binding->trace, 0, sizeof(*binding->trace));
    active_binding = binding;
    recovered_rng_bind(binding->rng);
}

SimNestStatus sim_recovered_nest_unbind(SimRecoveredNestBinding *binding)
{
    SimNestStatus status;
    if (binding == NULL || active_binding != binding)
        return SIM_NEST_INVALID_ARGUMENT;
    status = binding->status;
    active_binding = NULL;
    return status;
}

static void import_source_state(SimGameWorld *world, SimNestRuntime *runtime)
{
    memcpy(world->tiles.surface, MapA, sizeof(MapA));
    memcpy(world->tiles.nest_b, MapB, sizeof(MapB));
    memcpy(world->tiles.nest_r, MapR, sizeof(MapR));
    memcpy(world->exit_b, ExitMapB, sizeof(ExitMapB));
    memcpy(world->exit_r, ExitMapR, sizeof(ExitMapR));
    memcpy(world->life_a, LifeA, sizeof(LifeA));
    memcpy(world->life_b, LifeB, sizeof(LifeB));
    memcpy(world->life_r, LifeR, sizeof(LifeR));
    memcpy(world->hole_b, HoleMapB, sizeof(HoleMapB));
    memcpy(world->hole_r, HoleMapR, sizeof(HoleMapR));
    world->tiles.terrain_set = TERRAINset;
    world->current_ant_plane = MePlane;
    world->me_x = MeLocX;
    world->me_y = MeLocY;
    world->me_type = fd_50F6_04C2;
    world->me_direction = fd_50F6_0496;

    runtime->alarm_drop_state = fd_50F6_104E;
    runtime->alarm_indicator = fd_3D57_07BE;
    runtime->theme_index = fd_50F6_0228;
    runtime->theme_last_tick = fd_50F6_0214;
    runtime->invalidate_right = fd_50F6_0FB6;
    runtime->invalidate_bottom = fd_50F6_0FFA;
    runtime->dug_b_x_sum = fd_50F6_1068;
    runtime->dug_b_y_sum = fd_50F6_1082;
    runtime->dug_r_x_sum = fd_50F6_108E;
    runtime->dug_r_y_sum = fd_50F6_10A2;
    runtime->dug_b_count = fd_50F6_0224;
    runtime->dug_r_count = TilesDugR;
    runtime->dug_b_x_average = fd_50F6_10B2;
    runtime->dug_b_y_average = fd_50F6_10C0;
    runtime->dug_r_x_average = fd_50F6_0200;
    runtime->dug_r_y_average = fd_50F6_020E;
    runtime->entrance_b_surface_x = fd_3D57_02AC[0];
    runtime->entrance_b_surface_y = fd_3D57_02AC[1];
    runtime->entrance_r_surface_x = fd_3D57_02B0[0];
    runtime->entrance_r_surface_y = fd_3D57_02B0[1];
    runtime->entrance_b_nest_x = fd_3D57_02A4[0];
    runtime->entrance_b_nest_y = fd_3D57_02A4[1];
    runtime->entrance_r_nest_x = fd_3D57_02A8[0];
    runtime->entrance_r_nest_y = fd_3D57_02A8[1];
}

static void export_source_state(const SimGameWorld *world,
                                const SimNestRuntime *runtime)
{
    memcpy(MapA, world->tiles.surface, sizeof(MapA));
    memcpy(MapB, world->tiles.nest_b, sizeof(MapB));
    memcpy(MapR, world->tiles.nest_r, sizeof(MapR));
    memcpy(ExitMapB, world->exit_b, sizeof(ExitMapB));
    memcpy(ExitMapR, world->exit_r, sizeof(ExitMapR));
    memcpy(LifeA, world->life_a, sizeof(LifeA));
    memcpy(LifeB, world->life_b, sizeof(LifeB));
    memcpy(LifeR, world->life_r, sizeof(LifeR));
    memcpy(HoleMapB, world->hole_b, sizeof(HoleMapB));
    memcpy(HoleMapR, world->hole_r, sizeof(HoleMapR));
    TERRAINset = world->tiles.terrain_set;
    MePlane = world->current_ant_plane;
    MeLocX = world->me_x;
    MeLocY = world->me_y;
    fd_50F6_04C2 = world->me_type;
    fd_50F6_0496 = world->me_direction;

    fd_50F6_104E = runtime->alarm_drop_state;
    fd_3D57_07BE = runtime->alarm_indicator;
    fd_50F6_0228 = runtime->theme_index;
    fd_50F6_0214 = runtime->theme_last_tick;
    fd_50F6_0FB6 = runtime->invalidate_right;
    fd_50F6_0FFA = runtime->invalidate_bottom;
    fd_50F6_1068 = runtime->dug_b_x_sum;
    fd_50F6_1082 = runtime->dug_b_y_sum;
    fd_50F6_108E = runtime->dug_r_x_sum;
    fd_50F6_10A2 = runtime->dug_r_y_sum;
    fd_50F6_0224 = runtime->dug_b_count;
    TilesDugR = runtime->dug_r_count;
    fd_50F6_10B2 = runtime->dug_b_x_average;
    fd_50F6_10C0 = runtime->dug_b_y_average;
    fd_50F6_0200 = runtime->dug_r_x_average;
    fd_50F6_020E = runtime->dug_r_y_average;
    fd_3D57_02AC[0] = runtime->entrance_b_surface_x;
    fd_3D57_02AC[1] = runtime->entrance_b_surface_y;
    fd_3D57_02B0[0] = runtime->entrance_r_surface_x;
    fd_3D57_02B0[1] = runtime->entrance_r_surface_y;
    fd_3D57_02A4[0] = runtime->entrance_b_nest_x;
    fd_3D57_02A4[1] = runtime->entrance_b_nest_y;
    fd_3D57_02A8[0] = runtime->entrance_r_nest_x;
    fd_3D57_02A8[1] = runtime->entrance_r_nest_y;
}

void o25_3BA4_1035(void)
{
    SimGameWorld world = { 0 };
    SimNestRuntime runtime = { 0 };

    if (active_binding == NULL || active_binding->calls != 0) abort();
    active_binding->calls = 1;
    import_source_state(&world, &runtime);
    active_binding->status = sim_enter_nest_with_tick_provider(
        &world, active_binding->rng, &runtime, active_binding->request,
        active_binding->trace, active_binding->event_sink,
        active_binding->event_context, active_binding->tick_count_provider,
        active_binding->tick_count_context);
    if (active_binding->status == SIM_NEST_OK)
        export_source_state(&world, &runtime);
}

SimNestStatus sim_recovered_nest_apply(RecoveredState *state, SimRng *rng,
                                       const SimNestRequest *request,
                                       SimNestTrace *trace)
{
    return sim_recovered_nest_apply_with_tick_provider(
        state, rng, request, trace, NULL, NULL);
}

SimNestStatus sim_recovered_nest_apply_with_tick_provider(
    RecoveredState *state, SimRng *rng, const SimNestRequest *request,
    SimNestTrace *trace, SimNestTickCountProvider tick_count_provider,
    void *tick_count_context)
{
    RecoveredBindingFrame frame;
    SimRecoveredNestBinding binding;
    if (state == NULL || rng == NULL || request == NULL || trace == NULL)
        return SIM_NEST_INVALID_ARGUMENT;
    recovered_bind_begin(&frame, state);
    binding.rng = rng;
    binding.request = request;
    binding.tick_count_provider = tick_count_provider;
    binding.tick_count_context = tick_count_context;
    binding.trace = trace;
    binding.event_sink = NULL;
    binding.event_context = NULL;
    binding.status = SIM_NEST_INVALID_ARGUMENT;
    binding.calls = 0;
    sim_recovered_nest_bind(&binding);
    o25_3BA4_1035();
    (void)sim_recovered_nest_unbind(&binding);
    recovered_bind_end(&frame, state);
    return binding.status;
}
