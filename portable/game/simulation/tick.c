#include "tick.h"

#include <stddef.h>

void sim_tick_clear_mode_population(SimTickState *state)
{
    unsigned i;
    if (state == 0)
        return;
    for (i = 0; i < 20; ++i) {
        state->population_black[i] = 0;
        state->population_red[i] = 0;
    }
    if (state->population_counter_08dc != 0)
        state->population_counter_08dc = (int16_t)(uint16_t)(state->population_counter_08dc - 1);
    if (state->population_counter_08e8 != 0)
        state->population_counter_08e8 = (int16_t)(uint16_t)(state->population_counter_08e8 - 1);
}

SimTickStatus sim_tick_tally_mode_population(SimTickState *state,
                                             SimTickSubsystem red_initiator,
                                             SimGameWorld *world,
                                             void *context)
{
    if (state == 0)
        return SIM_TICK_INVALID_ARGUMENT;
    if (state->population_red[19] < 1 && red_initiator == 0)
        return SIM_TICK_UNSUPPORTED;

    state->history_black[0] = (int16_t)(uint16_t)(state->population_black[2] + state->population_black[3]);
    state->history_black[1] = (int16_t)(uint16_t)(state->population_black[4] + state->population_black[5]);
    state->history_black[2] = state->population_black[1];
    state->history_black[3] = state->population_black[7];
    state->history_black[4] = state->population_black[12];
    state->history_black[5] = state->population_black[6];
    state->history_red[0] = (int16_t)(uint16_t)(state->population_red[2] + state->population_red[3]);
    state->history_red[1] = (int16_t)(uint16_t)(state->population_red[4] + state->population_red[5]);
    state->history_red[2] = state->population_red[1];
    state->history_red[3] = state->population_red[7];
    state->history_red[4] = state->population_red[12];
    state->history_red[5] = state->population_red[6];
    if (state->population_red[19] < 1)
        red_initiator(world, state, context);
    return SIM_TICK_OK;
}

static int services_complete(const SimTickServices *s)
{
    return s != 0 && s->feed_ants != 0 && s->do_smells != 0 &&
           s->simulate_yard != 0 && s->do_water != 0 &&
           s->do_ant_lions != 0 && s->move_spider != 0 &&
           s->do_pillars != 0 && s->get_strategy != 0 &&
           s->simulate_black_ants != 0 && s->process_black_nest != 0 &&
           s->simulate_red_ants != 0 && s->simulate_yellow_ants != 0 &&
           s->move_yellow_ants != 0 && s->feedback != 0 &&
           s->red_initiator != 0 && s->end_game_dialog != 0;
}

SimTickStatus sim_tick_do_ant_sim(SimGameWorld *world, SimTickState *state,
                                  const SimTickServices *services)
{
    int32_t next_cycle;

    if (world == 0 || state == 0)
        return SIM_TICK_INVALID_ARGUMENT;
    if (!services_complete(services))
        return SIM_TICK_UNSUPPORTED;

    next_cycle = (int32_t)world->cycle + 1;
    world->cycle = next_cycle > 0x1000 ? 0 : (int16_t)next_cycle;
    ++world->world_ticks;

    if (state->mode_state == 1) {
        state->mode_aux_0f06 = 0;
        state->mode_aux_0f2e = 0;
        state->mode_aux_0f10 = 0;
        state->mode_aux_0ef6 = 0;
        state->mode_point.h = -1;
        state->mode_point.v = -1;
        state->mode_points[0] = state->mode_point;
        state->mode_points[1] = state->mode_point;
        state->mode_points[2] = state->mode_point;
    }

    if ((world->cycle & 0x3f) == 0)
        services->feed_ants(world, state, services->context);
    if ((world->cycle & 0x1f) == 0)
        services->do_smells(world, state, services->context);
    services->simulate_yard(world, state, services->context);
    services->do_water(world, state, services->context);
    services->do_ant_lions(world, state, services->context);
    services->move_spider(world, state, services->context);
    if (world->cycle & 1)
        services->do_pillars(world, state, services->context);
    services->get_strategy(world, state, services->context);
    sim_tick_clear_mode_population(state);
    services->simulate_black_ants(world, state, services->context);
    services->process_black_nest(world, state, services->context);
    services->simulate_red_ants(world, state, services->context);
    services->simulate_yellow_ants(world, state, services->context);
    (void)sim_tick_tally_mode_population(state, services->red_initiator,
                                         world, services->context);
    services->move_yellow_ants(world, state, services->context);
    services->feedback(world, state, services->context);
    if (state->mode_population_enabled != 0)
        services->end_game_dialog(world, state, 0, services->context);
    state->simulation_complete_flag = 1;
    return SIM_TICK_OK;
}
