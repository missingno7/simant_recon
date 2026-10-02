#include "../../game/simulation/population.h"

#include <string.h>

typedef struct SimPopulationProbeInput {
    uint8_t ants_a[SIM_A_ANT_CAPACITY];
    uint8_t ants_b[SIM_B_ANT_CAPACITY];
    uint8_t ants_r[SIM_R_ANT_CAPACITY];
    int16_t count_a, count_b, count_r;
    int16_t player_mode, player_caste_type, player_death_plane;
    int16_t scenario, new_game, graph_enabled;
    int16_t graph_preset[2];
    int16_t selection_pending, selection_colony;
    int16_t previous_black_queen, previous_red_queen;
    uint8_t lifetime_graph[10][16];
    uint16_t rng_seed;
    uint16_t effect_count;
} SimPopulationProbeInput;

typedef struct SimPopulationProbeOutput {
    int16_t status;
    int16_t ants_by_type[32];
    int16_t population_black[6];
    int16_t population_red[6];
    int16_t total_black, total_red;
    int16_t new_game, selection_pending, selection_colony;
    uint8_t lifetime_graph[10][16];
    uint16_t rng_seed;
    SimPopulationEffects effects;
} SimPopulationProbeOutput;

void sim_population_probe(const SimPopulationProbeInput *input,
                          SimPopulationProbeOutput *output)
{
    SimGameWorld world;
    SimRng rng;
    SimPopulationEffects effects;

    memset(&world, 0, sizeof world);
    memset(&effects, 0, sizeof effects);
    world.ants_a.count = input->count_a;
    world.ants_b.count = input->count_b;
    world.ants_r.count = input->count_r;
    memcpy(world.ants_a.type, input->ants_a, sizeof input->ants_a);
    memcpy(world.ants_b.type, input->ants_b, sizeof input->ants_b);
    memcpy(world.ants_r.type, input->ants_r, sizeof input->ants_r);
    world.player_mode = input->player_mode;
    world.player_caste_type = input->player_caste_type;
    world.player_death_plane = input->player_death_plane;
    world.scenario = input->scenario;
    world.population_new_game = input->new_game;
    world.population_lifetime_graph_enabled = input->graph_enabled;
    world.lifetime_graph_preset[0] = input->graph_preset[0];
    world.lifetime_graph_preset[1] = input->graph_preset[1];
    world.population_selection_pending = input->selection_pending;
    world.population_selection_colony = input->selection_colony;
    world.population_black[5] = input->previous_black_queen;
    world.population_red[5] = input->previous_red_queen;
    memcpy(world.lifetime_graph, input->lifetime_graph, sizeof world.lifetime_graph);
    rng.s_state = input->rng_seed;
    rng.c_state = 0;
    effects.count = input->effect_count;

    memset(output, 0, sizeof *output);
    output->status = (int16_t)sim_population_count_ants(&world, &rng, &effects);
    memcpy(output->ants_by_type, world.ants_by_type, sizeof output->ants_by_type);
    memcpy(output->population_black, world.population_black,
           sizeof output->population_black);
    memcpy(output->population_red, world.population_red,
           sizeof output->population_red);
    output->total_black = world.total_population_black;
    output->total_red = world.total_population_red;
    output->new_game = world.population_new_game;
    output->selection_pending = world.population_selection_pending;
    output->selection_colony = world.population_selection_colony;
    memcpy(output->lifetime_graph, world.lifetime_graph, sizeof output->lifetime_graph);
    output->rng_seed = rng.s_state;
    output->effects = effects;
}
