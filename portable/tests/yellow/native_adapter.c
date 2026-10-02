#include "native_adapter.h"

#include <string.h>

int sim_yellow_test_run(SimYellowTestWorld *input_output, SimRng *rng,
                        SimNestRuntime *nest_runtime,
                        SimYellowState *state, SimYellowTrace *trace)
{
    SimGameWorld world;
    SimYellowStatus status;
    if (input_output == NULL || rng == NULL || nest_runtime == NULL ||
        state == NULL || trace == NULL)
        return SIM_YELLOW_INVALID_ARGUMENT;
    memset(&world, 0, sizeof(world));
    memcpy(&world.tiles, &input_output->tiles, sizeof world.tiles);
    memcpy(world.exit_b, input_output->exit_b, sizeof input_output->exit_b);
    memcpy(world.exit_r, input_output->exit_r, sizeof input_output->exit_r);
    memcpy(world.life_a, input_output->life_a, sizeof input_output->life_a);
    memcpy(world.life_b, input_output->life_b, sizeof input_output->life_b);
    memcpy(world.life_r, input_output->life_r, sizeof input_output->life_r);
    memcpy(world.hole_b, input_output->hole_b, sizeof input_output->hole_b);
    memcpy(world.hole_r, input_output->hole_r, sizeof input_output->hole_r);
    memcpy(&world.ants_a, &input_output->ants_a, sizeof world.ants_a);
    memcpy(&world.ants_b, &input_output->ants_b, sizeof world.ants_b);
    memcpy(&world.ants_r, &input_output->ants_r, sizeof world.ants_r);
    world.current_ant_plane = input_output->current_ant_plane;
    world.me_x = input_output->me_x;
    world.me_y = input_output->me_y;
    world.me_type = input_output->me_type;
    world.me_direction = input_output->me_direction;
    world.me_health = input_output->me_health;
    world.health_warning_threshold = input_output->health_warning_threshold;
    world.health_warning = input_output->health_warning;
    world.health_death = input_output->health_death;
    world.health_force_full = input_output->health_force_full;
    world.source_counter_0472 = input_output->source_counter_0472;

    status = sim_do_ant_move_y(&world, rng, nest_runtime, state, trace);

    memcpy(&input_output->tiles, &world.tiles, sizeof world.tiles);
    memcpy(input_output->exit_b, world.exit_b, sizeof input_output->exit_b);
    memcpy(input_output->exit_r, world.exit_r, sizeof input_output->exit_r);
    memcpy(input_output->life_a, world.life_a, sizeof input_output->life_a);
    memcpy(input_output->life_b, world.life_b, sizeof input_output->life_b);
    memcpy(input_output->life_r, world.life_r, sizeof input_output->life_r);
    memcpy(input_output->hole_b, world.hole_b, sizeof input_output->hole_b);
    memcpy(input_output->hole_r, world.hole_r, sizeof input_output->hole_r);
    memcpy(&input_output->ants_a, &world.ants_a, sizeof world.ants_a);
    memcpy(&input_output->ants_b, &world.ants_b, sizeof world.ants_b);
    memcpy(&input_output->ants_r, &world.ants_r, sizeof world.ants_r);
    input_output->current_ant_plane = world.current_ant_plane;
    input_output->me_x = world.me_x;
    input_output->me_y = world.me_y;
    input_output->me_type = world.me_type;
    input_output->me_direction = world.me_direction;
    input_output->me_health = world.me_health;
    input_output->health_warning_threshold = world.health_warning_threshold;
    input_output->health_warning = world.health_warning;
    input_output->health_death = world.health_death;
    input_output->health_force_full = world.health_force_full;
    input_output->source_counter_0472 = world.source_counter_0472;
    return (int)status;
}

int sim_exit_nest_test_run(SimYellowTestWorld *input_output, SimRng *rng,
                           SimNestRuntime *nest_runtime,
                           SimExitNestContext *context,
                           SimMoveTrace *movement_trace,
                           SimNestTrace *nest_trace)
{
    SimGameWorld world;
    SimExitNestStatus status;
    if (input_output == NULL || rng == NULL || nest_runtime == NULL ||
        context == NULL || movement_trace == NULL || nest_trace == NULL)
        return SIM_EXIT_NEST_INVALID_ARGUMENT;
    memset(&world, 0, sizeof(world));
    memcpy(&world.tiles, &input_output->tiles, sizeof world.tiles);
    memcpy(world.exit_b, input_output->exit_b, sizeof input_output->exit_b);
    memcpy(world.exit_r, input_output->exit_r, sizeof input_output->exit_r);
    memcpy(world.life_a, input_output->life_a, sizeof input_output->life_a);
    memcpy(world.life_b, input_output->life_b, sizeof input_output->life_b);
    memcpy(world.life_r, input_output->life_r, sizeof input_output->life_r);
    memcpy(world.hole_b, input_output->hole_b, sizeof input_output->hole_b);
    memcpy(world.hole_r, input_output->hole_r, sizeof input_output->hole_r);
    memcpy(&world.ants_a, &input_output->ants_a, sizeof world.ants_a);
    memcpy(&world.ants_b, &input_output->ants_b, sizeof world.ants_b);
    memcpy(&world.ants_r, &input_output->ants_r, sizeof world.ants_r);
    world.current_ant_plane = input_output->current_ant_plane;
    world.me_x = input_output->me_x;
    world.me_y = input_output->me_y;
    world.me_type = input_output->me_type;
    world.me_direction = input_output->me_direction;
    world.me_health = input_output->me_health;
    world.health_warning_threshold = input_output->health_warning_threshold;
    world.health_warning = input_output->health_warning;
    world.health_death = input_output->health_death;
    world.health_force_full = input_output->health_force_full;
    world.source_counter_0472 = input_output->source_counter_0472;

    status = sim_exit_nest(&world, rng, nest_runtime, context,
                           movement_trace, nest_trace);

    memcpy(&input_output->tiles, &world.tiles, sizeof world.tiles);
    memcpy(input_output->exit_b, world.exit_b, sizeof input_output->exit_b);
    memcpy(input_output->exit_r, world.exit_r, sizeof input_output->exit_r);
    memcpy(input_output->life_a, world.life_a, sizeof input_output->life_a);
    memcpy(input_output->life_b, world.life_b, sizeof input_output->life_b);
    memcpy(input_output->life_r, world.life_r, sizeof input_output->life_r);
    memcpy(input_output->hole_b, world.hole_b, sizeof input_output->hole_b);
    memcpy(input_output->hole_r, world.hole_r, sizeof input_output->hole_r);
    memcpy(&input_output->ants_a, &world.ants_a, sizeof world.ants_a);
    memcpy(&input_output->ants_b, &world.ants_b, sizeof world.ants_b);
    memcpy(&input_output->ants_r, &world.ants_r, sizeof world.ants_r);
    input_output->current_ant_plane = world.current_ant_plane;
    input_output->me_x = world.me_x;
    input_output->me_y = world.me_y;
    input_output->me_type = world.me_type;
    input_output->me_direction = world.me_direction;
    input_output->me_health = world.me_health;
    input_output->health_warning_threshold = world.health_warning_threshold;
    input_output->health_warning = world.health_warning;
    input_output->health_death = world.health_death;
    input_output->health_force_full = world.health_force_full;
    input_output->source_counter_0472 = world.source_counter_0472;
    return (int)status;
}
