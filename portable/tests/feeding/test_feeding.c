#include "../../game/simulation/feeding.h"
#include "../../game/simulation/spider.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_feed_gates_and_health(void)
{
    SimGameWorld world;
    SimRng rng = { 0x1357, 0 };
    SimFeedingState state = { 4 };
    SimFeedingTrace trace = { 0 };
    const int16_t *sine = sim_spider_sine_table();

    memset(&world, 0, sizeof world);
    world.health_black = 1;
    world.health_red = 0;
    world.source_state_0c18 = 1;
    world.scenario = 3;
    world.food_added_terrain = 0;
    assert(sim_feed_ants(&world, &rng, &state, sine, &trace) == SIM_FEEDING_OK);
    assert(world.health_black == 1 && world.health_red == 0);
    assert(trace.count == 0 && state.next_food_threshold == 4);
    assert(rng.s_state == 0x1357);

    world.scenario = 0;
    world.source_state_0c18 = 0;
    world.health_black = 1;
    world.health_red = 3;
    world.food_added_terrain = 4;
    assert(sim_feed_ants(&world, &rng, &state, sine, &trace) == SIM_FEEDING_OK);
    assert(world.health_black == 0 && world.health_red == 2);
    assert(trace.count == 0 && rng.s_state == 0x1357);
}

static void test_add_food_mutates_only_eligible_surface(void)
{
    SimGameWorld world;
    SimRng rng = { 0x2468, 0 };
    SimFeedingTrace trace = { 0 };
    const int16_t *sine = sim_spider_sine_table();

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 0;
    memset(world.tiles.surface, 1, sizeof world.tiles.surface);
    assert(sim_food_add(&world, &rng, sine, 150, 1, &trace) == SIM_FEEDING_OK);
    assert(trace.count == 1 && trace.events[0].kind == SIM_FEEDING_SOUND);
    assert(trace.events[0].arguments[0] == 0x20 &&
           trace.events[0].arguments[1] == 0 &&
           trace.events[0].arguments[2] == 0x7e);
    assert(world.food_center_x >= 0 && world.food_center_x < 128);
    assert(world.food_center_y >= 0 && world.food_center_y < 64);
    assert(world.food_added_terrain > 0);
}

static void test_feed_runs_food_and_sets_next_threshold(void)
{
    SimGameWorld world;
    SimRng rng = { 0x7531, 0 };
    SimFeedingState state = { 0 };
    SimFeedingTrace trace = { 0 };

    memset(&world, 0, sizeof world);
    memset(world.tiles.surface, 1, sizeof world.tiles.surface);
    world.health_black = 10;
    world.health_red = 10;
    world.food_added_terrain = 0;
    state.next_food_threshold = 1;
    assert(sim_feed_ants(&world, &rng, &state, sim_spider_sine_table(),
                         &trace) == SIM_FEEDING_OK);
    assert(trace.count == 1);
    assert(world.health_black == 9 && world.health_red == 9);
    assert(state.next_food_threshold >= 1 && state.next_food_threshold <= 50);
    assert(world.food_added_terrain > 0);
}

int main(void)
{
    test_feed_gates_and_health();
    test_add_food_mutates_only_eligible_surface();
    test_feed_runs_food_and_sets_next_threshold();
    puts("feeding source-semantics tests passed");
    return 0;
}
