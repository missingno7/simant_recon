#include "population.h"

#include <stddef.h>
#include <string.h>

void sim_population_effects_reset(SimPopulationEffects *effects)
{
    if (effects != 0)
        memset(effects, 0, sizeof *effects);
}

static int valid_counts(const SimGameWorld *world)
{
    return world->ants_a.count >= 0 && world->ants_a.count <= SIM_A_ANT_CAPACITY &&
           world->ants_b.count >= 0 && world->ants_b.count <= SIM_B_ANT_CAPACITY &&
           world->ants_r.count >= 0 && world->ants_r.count <= SIM_R_ANT_CAPACITY;
}

static void count_list(const uint8_t *types, int16_t count, int16_t bins[32])
{
    int16_t index;
    for (index = (int16_t)(count - 1); index >= 0; --index) {
        uint8_t type = types[index];
        if (type != 0)
            ++bins[type >> 3];
    }
}

static int event_reservation(const SimGameWorld *world, int red_lost,
                             int black_lost)
{
    int per_loss = world->scenario <= 1 ? 3 : 2;
    return per_loss * (red_lost + black_lost);
}

static int add_event(SimPopulationEffects *effects, uint16_t kind,
                     int16_t a, int16_t b, int16_t c)
{
    SimPopulationEffect *event;
    if (effects->count >= SIM_POPULATION_EFFECT_CAPACITY) {
        effects->overflow = 1;
        return 0;
    }
    event = &effects->events[effects->count++];
    event->kind = kind;
    event->values[0] = a;
    event->values[1] = b;
    event->values[2] = c;
    return 1;
}

static void add_loss_events(SimPopulationEffects *effects, uint16_t song,
                            int16_t report, int second_report)
{
    (void)add_event(effects, SIM_POPULATION_MUSIC, (int16_t)song, 0x7e, 0);
    (void)add_event(effects, SIM_POPULATION_REPORT, 0, report, 1);
    if (second_report)
        (void)add_event(effects, SIM_POPULATION_REPORT, 0,
                        (int16_t)(report + 1), 1);
}

SimPopulationStatus sim_population_count_ants(SimGameWorld *world, SimRng *rng,
                                              SimPopulationEffects *effects)
{
    int16_t bins[32] = { 0 };
    int16_t black[6];
    int16_t red[6];
    int16_t red_total, black_total;
    int16_t player_bin;
    int16_t previous_black_queen, previous_red_queen;
    int black_lost, red_lost, use_graph_random;
    uint16_t graph_draw = 0;

    if (world == 0 || rng == 0 || effects == 0)
        return SIM_POPULATION_INVALID_ARGUMENT;
    if (!valid_counts(world) || world->player_caste_type < 0 ||
        world->player_caste_type > 0xff)
        return SIM_POPULATION_INVALID_STATE;

    count_list(world->ants_a.type, world->ants_a.count, bins);
    count_list(world->ants_b.type, world->ants_b.count, bins);
    count_list(world->ants_r.type, world->ants_r.count, bins);
    if (world->player_mode == 0) {
        uint16_t caste = (uint16_t)world->player_caste_type;
        if (world->player_death_plane != 0)
            caste |= 0x80u;
        player_bin = (int16_t)(caste >> 3);
        ++bins[player_bin];
    }

    black[0] = bins[0];
    black[1] = (int16_t)(bins[1] + bins[2] + bins[3] + bins[5]);
    black[2] = (int16_t)(bins[6] + bins[7] + bins[9]);
    black[3] = bins[4];
    black[4] = bins[8];
    black[5] = bins[12];
    red[0] = bins[16];
    red[1] = (int16_t)(bins[18] + bins[19] + bins[21] + bins[17]);
    red[2] = (int16_t)(bins[23] + bins[22] + bins[25]);
    red[3] = bins[20];
    red[4] = bins[24];
    red[5] = bins[28];
    black_total = (int16_t)(black[1] + black[2] + black[3] + black[4] + black[5]);
    red_total = (int16_t)(red[1] + red[2] + red[3] + red[4] + red[5]);

    previous_black_queen = world->population_black[5];
    previous_red_queen = world->population_red[5];
    black_lost = previous_black_queen != 0 && bins[12] == 0 &&
                 world->population_new_game == 0;
    red_lost = previous_red_queen != 0 && bins[28] == 0 &&
               world->population_new_game == 0;
    /* The graph update sits inside the source's RED queen-loss block. */
    use_graph_random = red_lost && world->scenario == 2 &&
        world->population_lifetime_graph_enabled == 1 &&
        world->lifetime_graph_preset[0] == 0x0b &&
        world->lifetime_graph_preset[1] == 8;

    if (effects->count > SIM_POPULATION_EFFECT_CAPACITY || effects->overflow)
        return SIM_POPULATION_EFFECTS_FULL;
    if (event_reservation(world, red_lost, black_lost) >
        (int)(SIM_POPULATION_EFFECT_CAPACITY - effects->count))
        return SIM_POPULATION_EFFECTS_FULL;
    if (use_graph_random && !sim_rng_s1(rng, 6, &graph_draw))
        return SIM_POPULATION_RNG_ERROR;

    memcpy(world->ants_by_type, bins, sizeof bins);
    memcpy(world->population_black, black, sizeof black);
    memcpy(world->population_red, red, sizeof red);
    world->total_population_red = red_total;
    world->total_population_black = black_total;

    /* 0AEC is the black-colony block: PlaceBlackQueen creates types 60/68,
     * hence bins 12/13. 0AFA is red: PlaceRedQueen creates E0/E8, bins 28/29. */
    if (black_lost) {
        add_loss_events(effects, 0x2b0c, 0x271a, world->scenario <= 1);
        if (world->scenario <= 1) {
            world->population_selection_pending = 1;
            world->population_selection_colony = 0;
        }
    }
    if (red_lost) {
        add_loss_events(effects, 0x2b0d, 0x271c, world->scenario <= 1);
        if (world->scenario <= 1) {
            world->population_selection_pending = 1;
            world->population_selection_colony = 1;
        }
    }
    if (use_graph_random)
        world->lifetime_graph[graph_draw][0] = 0x14;
    world->population_new_game = 0;
    return SIM_POPULATION_OK;
}
