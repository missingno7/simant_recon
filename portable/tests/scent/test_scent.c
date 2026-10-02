#include "../../game/simulation/scent.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_nest_decay_byte_edges(void)
{
    SimGameWorld world;
    memset(&world, 0, sizeof world);
    world.pheromone_b_nest[0][0] = 0;
    world.pheromone_b_nest[0][1] = 1;
    world.pheromone_b_nest[0][2] = 255;
    world.pheromone_r_nest[63][31] = 1;
    assert(sim_scent_colony_smell_black_nest(&world) == SIM_SCENT_OK);
    assert(sim_scent_colony_smell_red_nest(&world) == SIM_SCENT_OK);
    assert(world.pheromone_b_nest[0][0] == 0);
    assert(world.pheromone_b_nest[0][1] == 0);
    assert(world.pheromone_b_nest[0][2] == 254);
    assert(world.pheromone_r_nest[63][31] == 0);
}

static void test_trail_drop_thresholds_and_rounding(void)
{
    SimGameWorld world;
    memset(&world, 0, sizeof world);
    world.pheromone_b_trail[0][0] = 7;
    world.pheromone_b_trail[0][1] = 8;
    world.pheromone_b_trail[0][2] = 9;
    world.pheromone_b_trail[0][3] = 255;
    world.pheromone_r_trail[1][0] = 1;
    world.pheromone_r_trail[1][1] = 8;
    world.pheromone_r_trail[1][2] = 255;
    assert(sim_scent_colony_smell_black_trail(&world) == SIM_SCENT_OK);
    assert(sim_scent_colony_smell_red_trail(&world) == SIM_SCENT_OK);
    assert(world.pheromone_b_trail[0][0] == 0);
    assert(world.pheromone_b_trail[0][1] == 4);
    assert(world.pheromone_b_trail[0][2] == 5);
    assert(world.pheromone_b_trail[0][3] == 128);
    assert(world.pheromone_r_trail[1][0] == 0);
    assert(world.pheromone_r_trail[1][1] == 4);
    assert(world.pheromone_r_trail[1][2] == 128);
}

static void test_smooth_alarm_boundaries_and_work_copy(void)
{
    SimGameWorld world;
    SimScentState state;
    memset(&world, 0, sizeof world);
    memset(&state, 0xa5, sizeof state);
    world.pheromone_a[0][0] = 255;
    world.pheromone_a[1][0] = 64;
    world.pheromone_a[0][1] = 32;
    world.pheromone_a[63][31] = 9;
    assert(sim_scent_smooth_alarm(&world, &state) == SIM_SCENT_OK);
    assert(state.smooth_alarm_work[0][0] == 255);
    assert(state.smooth_alarm_work[1][0] == 64);
    assert(state.smooth_alarm_work[0][1] == 32);
    assert(state.smooth_alarm_work[63][31] == 9);
    assert(world.pheromone_a[0][0] > 8);
    assert(world.pheromone_a[63][31] == 0);
}

int main(void)
{
    test_nest_decay_byte_edges();
    test_trail_drop_thresholds_and_rounding();
    test_smooth_alarm_boundaries_and_work_copy();
    puts("scent source-semantics tests passed");
    return 0;
}
