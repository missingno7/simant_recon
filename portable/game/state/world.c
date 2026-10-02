#include "world.h"

#include <string.h>

void sim_world_clear_arrays(SimGameWorld *world)
{
    if (world == 0)
        return;

    memset(world->tiles.surface, 0, sizeof world->tiles.surface);
    memset(world->life_a, 0, sizeof world->life_a);
    memset(world->tiles.nest_b, 0, sizeof world->tiles.nest_b);
    memset(world->tiles.nest_r, 0, sizeof world->tiles.nest_r);
    memset(world->exit_b, 0, sizeof world->exit_b);
    memset(world->exit_r, 0, sizeof world->exit_r);
    memset(world->life_b, 0, sizeof world->life_b);
    memset(world->life_r, 0, sizeof world->life_r);
    memset(world->pheromone_aux, 0, sizeof world->pheromone_aux);
    memset(world->pheromone_a, 0, sizeof world->pheromone_a);
    memset(world->pheromone_b_nest, 0, sizeof world->pheromone_b_nest);
    memset(world->pheromone_b_trail, 0, sizeof world->pheromone_b_trail);
    memset(world->pheromone_r_nest, 0, sizeof world->pheromone_r_nest);
    memset(world->pheromone_r_trail, 0, sizeof world->pheromone_r_trail);
    memset(world->ants_a.type, 0, SIM_A_ANT_CAPACITY);
    memset(world->ants_a.mode, 0, SIM_A_ANT_CAPACITY);
    memset(world->ants_a.state, 0, SIM_A_ANT_CAPACITY);
    memset(world->ants_b.type, 0, SIM_B_ANT_CAPACITY);
    memset(world->ants_b.mode, 0, SIM_B_ANT_CAPACITY);
    memset(world->ants_b.state, 0, SIM_B_ANT_CAPACITY);
    memset(world->ants_r.type, 0, SIM_R_ANT_CAPACITY);
    memset(world->ants_r.mode, 0, SIM_R_ANT_CAPACITY);
    memset(world->ants_r.state, 0, SIM_R_ANT_CAPACITY);
    memset(world->build_black, 0, sizeof world->build_black);
    memset(world->build_red, 0, sizeof world->build_red);
}

void sim_world_init_sim_vars(SimGameWorld *world)
{
    if (world == 0)
        return;
    world->selected_map_plane = 0;
    world->simulation_speed_index = 1;
    world->health_warning_threshold = 30;
    world->colony_health_warning_threshold = 30;
    world->current_experiment_tool = 0;
    world->experience_flags[0] = 0;
    world->experience_flags[1] = 0;
    world->world_state_flag = 0;
}
