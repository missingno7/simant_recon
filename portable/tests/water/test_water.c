#include "../../game/simulation/water.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_add_row_and_ant_drowning(void)
{
    SimGameWorld world;
    SimRng rng = {0x1357, 1};
    SimWaterState state;
    SimWaterTrace trace;
    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    world.ants_b.count = 4;
    world.ants_b.y[0] = 9; world.ants_b.type[0] = 0x08;
    world.ants_b.y[1] = 9; world.ants_b.type[1] = 0x00;
    world.ants_b.y[2] = 9; world.ants_b.type[2] = 0x60;
    world.ants_b.y[3] = 8; world.ants_b.type[3] = 0x18;
    world.ants_r.count = 1;
    world.ants_r.y[0] = 9; world.ants_r.type[0] = 0x20;
    world.tiles.nest_b[0][9] = 0x1f;
    world.tiles.nest_b[1][9] = 0x20;
    world.tiles.nest_b[2][9] = 0x4e;
    world.tiles.nest_b[3][9] = 0xff;
    world.tiles.nest_r[0][9] = 0x1e;
    assert(sim_water_add_row(&world, &rng, &state, 9, &trace) == SIM_WATER_OK);
    assert(world.tiles.nest_b[0][9] == 0x4e);
    assert(world.tiles.nest_b[1][9] == 0x4f);
    assert(world.tiles.nest_b[2][9] == 0x7d);
    assert(world.tiles.nest_b[3][9] == 0x2e);
    assert(world.tiles.nest_r[0][9] == 0x4e);
    assert(world.ants_b.mode[0] == 0x11);
    assert(world.ants_b.mode[1] == 0);
    assert(world.ants_b.mode[2] == 0);
    assert(world.ants_b.mode[3] == 0);
    assert(world.ants_r.mode[0] == 0x11);
    assert(trace.count == 128);
    assert(trace.intents[0].kind == SIM_WATER_INTENT_MAP_INVALIDATION);
    assert(trace.intents[0].first == 2 && trace.intents[0].second == 0 && trace.intents[0].third == 9);
    assert(trace.intents[1].first == 3 && trace.intents[1].second == 0 && trace.intents[1].third == 9);
    assert(trace.intents[126].first == 2 && trace.intents[126].second == 63);
    assert(trace.intents[127].first == 3 && trace.intents[127].second == 63);
}

static void test_drop_row(void)
{
    SimGameWorld world;
    SimRng rng = {0x2468, 0x12345678};
    SimWaterState state;
    SimWaterTrace trace;
    uint16_t before;
    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    world.tiles.nest_b[2][63] = 0x4e;
    world.tiles.nest_r[4][63] = 0x4e;
    world.tiles.nest_b[3][63] = 0x7d;
    before = rng.s_state;
    assert(sim_water_drop_row(&world, &rng, &state, 63, &trace) == SIM_WATER_OK);
    assert(world.tiles.nest_b[2][63] < 8);
    assert(world.tiles.nest_r[4][63] < 8);
    assert(world.tiles.nest_b[3][63] == 0x4e);
    assert(rng.s_state != before);
    assert(trace.count == 128);
    assert(sim_water_drop_row(&world, &rng, &state, 64, &trace) == SIM_WATER_INVALID_ARGUMENT);
}

static void test_place_drop_preserves_obstacle(void)
{
    SimGameWorld world;
    SimRng rng = {0xdead, 0x87654321};
    SimWaterState state;
    SimWaterTrace trace;
    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    memset(world.tiles.surface, 0x20, sizeof world.tiles.surface);
    memset(world.pheromone_a, 0x33, sizeof world.pheromone_a);
    memset(world.pheromone_aux, 0x44, sizeof world.pheromone_aux);
    assert(sim_water_place_drop(&world, &rng, &state, 10, &trace) == SIM_WATER_OK);
    assert(state.drop_x[10] < 128 && state.drop_y[10] < 64);
    assert(world.tiles.surface[state.drop_x[10]][state.drop_y[10]] == 0x20);
    assert(world.pheromone_a[0][0] == 0x33 && world.pheromone_aux[0][0] == 0x44);
    assert(trace.count == 0);
}

int main(void)
{
    test_add_row_and_ant_drowning();
    test_drop_row();
    test_place_drop_preserves_obstacle();
    puts("water source-semantics tests passed");
    return 0;
}
