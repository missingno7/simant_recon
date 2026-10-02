#include "native_adapter.h"

#include <string.h>

int sim_nest_test_run(SimNestTestWorld *input_output, SimRng *rng,
                      SimNestRuntime *runtime, const SimNestRequest *request,
                      SimNestTrace *trace)
{
    SimGameWorld world;
    SimNestStatus result;
    if (input_output == 0 || rng == 0 || runtime == 0 || request == 0 || trace == 0)
        return SIM_NEST_INVALID_ARGUMENT;
    memset(&world, 0, sizeof(world));
    memcpy(world.tiles.surface, input_output->surface, sizeof input_output->surface);
    memcpy(world.tiles.nest_b, input_output->nest_b, sizeof input_output->nest_b);
    memcpy(world.tiles.nest_r, input_output->nest_r, sizeof input_output->nest_r);
    memcpy(world.exit_b, input_output->exit_b, sizeof input_output->exit_b);
    memcpy(world.exit_r, input_output->exit_r, sizeof input_output->exit_r);
    memcpy(world.life_a, input_output->life_a, sizeof input_output->life_a);
    memcpy(world.life_b, input_output->life_b, sizeof input_output->life_b);
    memcpy(world.life_r, input_output->life_r, sizeof input_output->life_r);
    memcpy(world.hole_b, input_output->hole_b, sizeof input_output->hole_b);
    memcpy(world.hole_r, input_output->hole_r, sizeof input_output->hole_r);
    world.tiles.terrain_set = input_output->terrain_set;
    world.current_ant_plane = input_output->current_ant_plane;
    world.me_x = input_output->me_x;
    world.me_y = input_output->me_y;
    world.me_type = input_output->me_type;
    world.me_direction = input_output->me_direction;

    result = sim_enter_nest(&world, rng, runtime, request, trace);

    memcpy(input_output->surface, world.tiles.surface, sizeof input_output->surface);
    memcpy(input_output->nest_b, world.tiles.nest_b, sizeof input_output->nest_b);
    memcpy(input_output->nest_r, world.tiles.nest_r, sizeof input_output->nest_r);
    memcpy(input_output->exit_b, world.exit_b, sizeof input_output->exit_b);
    memcpy(input_output->exit_r, world.exit_r, sizeof input_output->exit_r);
    memcpy(input_output->life_a, world.life_a, sizeof input_output->life_a);
    memcpy(input_output->life_b, world.life_b, sizeof input_output->life_b);
    memcpy(input_output->life_r, world.life_r, sizeof input_output->life_r);
    memcpy(input_output->hole_b, world.hole_b, sizeof input_output->hole_b);
    memcpy(input_output->hole_r, world.hole_r, sizeof input_output->hole_r);
    input_output->current_ant_plane = world.current_ant_plane;
    input_output->me_x = world.me_x;
    input_output->me_y = world.me_y;
    input_output->me_type = world.me_type;
    input_output->me_direction = world.me_direction;
    return result;
}
