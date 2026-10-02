#include "../../game/simulation/population.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void append_type(SimAntList *list, uint8_t value)
{
    list->type[list->count++] = value;
}

static void test_bins_populations_and_player(void)
{
    SimGameWorld world;
    SimRng rng = { 0x1234, 0 };
    SimPopulationEffects effects;
    int bin;

    memset(&world, 0, sizeof world);
    sim_population_effects_reset(&effects);
    world.player_mode = 0;
    world.player_caste_type = 0x20;
    for (bin = 0; bin < 32; ++bin) {
        uint8_t type = (uint8_t)(bin << 3);
        if (type == 0)
            type = 1;
        if (bin % 3 == 0)
            append_type(&world.ants_a, type);
        else if (bin % 3 == 1)
            world.ants_b.type[world.ants_b.count++] = type;
        else
            world.ants_r.type[world.ants_r.count++] = type;
    }
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    for (bin = 0; bin < 32; ++bin)
        assert(world.ants_by_type[bin] == (bin == 4 ? 2 : 1));
    assert(world.population_black[0] == 1);
    assert(world.population_black[1] == 4);
    assert(world.population_black[2] == 3);
    assert(world.population_black[3] == 2);
    assert(world.population_black[4] == 1);
    assert(world.population_black[5] == 1);
    assert(world.total_population_black == 11);
    assert(world.population_red[0] == 1);
    assert(world.population_red[1] == 4);
    assert(world.population_red[2] == 3);
    assert(world.population_red[3] == 1);
    assert(world.population_red[4] == 1);
    assert(world.population_red[5] == 1);
    assert(world.total_population_red == 10);
    assert(effects.count == 0);
}

static void test_player_death_plane_and_gate(void)
{
    SimGameWorld world;
    SimRng rng = { 1, 0 };
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    sim_population_effects_reset(&effects);
    world.player_mode = 0;
    world.player_caste_type = 0x40;
    world.player_death_plane = 1;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    assert(world.ants_by_type[24] == 1);
    world.player_mode = 1;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    assert(world.ants_by_type[24] == 0);
}

static void test_new_game_suppresses_prior_queen_loss(void)
{
    SimGameWorld world;
    SimRng rng = { 0x8001, 0 };
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    sim_population_effects_reset(&effects);
    world.population_black[5] = 1;
    world.population_red[5] = 1;
    world.population_new_game = 1;
    world.population_selection_pending = 8;
    world.population_selection_colony = 9;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    assert(effects.count == 0);
    assert(world.population_new_game == 0);
    assert(world.population_selection_pending == 8);
    assert(world.population_selection_colony == 9);
    assert(rng.s_state == 0x8001);
}

static void test_ordered_queen_loss_and_selection(void)
{
    SimGameWorld world;
    SimRng rng = { 0x8001, 0 };
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    sim_population_effects_reset(&effects);
    world.scenario = 0;
    world.population_black[5] = 1;
    world.population_red[5] = 1;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    assert(effects.count == 6);
    assert(effects.events[0].kind == SIM_POPULATION_MUSIC);
    assert(effects.events[0].values[0] == 0x2b0c && effects.events[0].values[1] == 0x7e);
    assert(effects.events[1].kind == SIM_POPULATION_REPORT);
    assert(effects.events[1].values[1] == 0x271a);
    assert(effects.events[2].kind == SIM_POPULATION_REPORT);
    assert(effects.events[2].values[1] == 0x271b);
    assert(effects.events[3].values[0] == 0x2b0d);
    assert(effects.events[4].values[1] == 0x271c);
    assert(effects.events[5].values[1] == 0x271d);
    assert(world.population_selection_pending == 1);
    assert(world.population_selection_colony == 1);
}

static void test_scenario_two_black_loss_consumes_sr1(void)
{
    SimGameWorld world;
    SimRng rng = { 0x8001, 0 };
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    sim_population_effects_reset(&effects);
    world.scenario = 2;
    world.population_black[5] = 1;
    world.population_red[5] = 1;
    world.population_lifetime_graph_enabled = 1;
    world.lifetime_graph_preset[0] = 0x0b;
    world.lifetime_graph_preset[1] = 8;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_OK);
    assert(rng.s_state == 0x1bf7);
    assert(world.lifetime_graph[1][0] == 0x14);
    assert(world.lifetime_graph[0][0] == 0);
    /* CountAnts writes 0184, which is red-grid 0164 at byte offset 32.
     * Yard simulation must see this population effect through its own view. */
    assert(world.build_red[3][0] == 0x14);
    world.build_red[11][8] = 2;
    assert(world.lifetime_graph[9][8] == 2);
    assert(effects.count == 4);
    assert(effects.events[0].values[0] == 0x2b0c);
    assert(effects.events[1].values[1] == 0x271a);
    assert(effects.events[2].values[0] == 0x2b0d);
    assert(effects.events[3].values[1] == 0x271c);
}

static void test_effect_overflow_is_atomic(void)
{
    SimGameWorld world, before;
    SimRng rng = { 0x8001, 0 };
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    world.scenario = 0;
    world.population_black[5] = 1;
    world.population_red[5] = 1;
    before = world;
    memset(&effects, 0, sizeof effects);
    effects.count = SIM_POPULATION_EFFECT_CAPACITY - 1;
    assert(sim_population_count_ants(&world, &rng, &effects) == SIM_POPULATION_EFFECTS_FULL);
    assert(memcmp(&world, &before, sizeof world) == 0);
    assert(rng.s_state == 0x8001);
    assert(effects.count == SIM_POPULATION_EFFECT_CAPACITY - 1);
}

int main(void)
{
    test_bins_populations_and_player();
    test_player_death_plane_and_gate();
    test_new_game_suppresses_prior_queen_loss();
    test_ordered_queen_loss_and_selection();
    test_scenario_two_black_loss_consumes_sr1();
    test_effect_overflow_is_atomic();
    puts("population tests passed");
    return 0;
}
