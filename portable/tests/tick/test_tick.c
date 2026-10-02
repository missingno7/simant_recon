#include "../../game/simulation/tick.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

enum {
    EV_FEED = 1, EV_SMELLS, EV_YARD, EV_WATER, EV_LIONS, EV_SPIDER,
    EV_PILLARS, EV_STRATEGY, EV_BLACK_ANTS, EV_BLACK_NEST, EV_RED_ANTS,
    EV_YELLOW_ANTS, EV_RED_INITIATOR, EV_MOVE_YELLOW, EV_FEEDBACK, EV_END
};

typedef struct Trace {
    unsigned events[32];
    unsigned count;
    int expect_mode_reset;
} Trace;

static void append(Trace *trace, unsigned event, SimGameWorld *world,
                   SimTickState *state)
{
    if (trace->expect_mode_reset && event == EV_FEED) {
        assert(state->mode_aux_0f06 == 0 && state->mode_aux_0f2e == 0);
        assert(state->mode_aux_0f10 == 0 && state->mode_aux_0ef6 == 0);
        assert(state->mode_point.h == -1 && state->mode_point.v == -1);
        assert(state->mode_points[0].h == -1 && state->mode_points[1].v == -1);
    }
    assert(trace->count < sizeof trace->events / sizeof trace->events[0]);
    trace->events[trace->count++] = event;
    (void)world;
}

#define CALLBACK(name, event_id) \
    static void name(SimGameWorld *world, SimTickState *state, void *context) \
    { append((Trace *)context, event_id, world, state); }

CALLBACK(feed, EV_FEED)
CALLBACK(smells, EV_SMELLS)
CALLBACK(yard, EV_YARD)
CALLBACK(water, EV_WATER)
CALLBACK(lions, EV_LIONS)
CALLBACK(spider, EV_SPIDER)
CALLBACK(pillars, EV_PILLARS)
CALLBACK(strategy, EV_STRATEGY)

static void black_ants(SimGameWorld *world, SimTickState *state, void *context)
{
    append((Trace *)context, EV_BLACK_ANTS, world, state);
    state->population_black[2] = 3;
    state->population_black[3] = 4;
}

CALLBACK(black_nest, EV_BLACK_NEST)

static void red_ants(SimGameWorld *world, SimTickState *state, void *context)
{
    append((Trace *)context, EV_RED_ANTS, world, state);
    state->population_red[19] = 0;
}

CALLBACK(yellow_ants, EV_YELLOW_ANTS)

static void red_initiator(SimGameWorld *world, SimTickState *state,
                          void *context)
{
    assert(state->history_black[0] == 7);
    append((Trace *)context, EV_RED_INITIATOR, world, state);
}

CALLBACK(move_yellow, EV_MOVE_YELLOW)
CALLBACK(feedback, EV_FEEDBACK)

static void end_game(SimGameWorld *world, SimTickState *state,
                     int source_argument, void *context)
{
    assert(source_argument == 0);
    append((Trace *)context, EV_END, world, state);
}

static SimTickServices make_services(Trace *trace)
{
    SimTickServices services;
    services.feed_ants = feed;
    services.do_smells = smells;
    services.simulate_yard = yard;
    services.do_water = water;
    services.do_ant_lions = lions;
    services.move_spider = spider;
    services.do_pillars = pillars;
    services.get_strategy = strategy;
    services.simulate_black_ants = black_ants;
    services.process_black_nest = black_nest;
    services.simulate_red_ants = red_ants;
    services.simulate_yellow_ants = yellow_ants;
    services.move_yellow_ants = move_yellow;
    services.feedback = feedback;
    services.red_initiator = red_initiator;
    services.end_game_dialog = end_game;
    services.context = trace;
    return services;
}

static void assert_trace(const Trace *trace, const unsigned *expected,
                         unsigned count)
{
    assert(trace->count == count);
    assert(memcmp(trace->events, expected, count * sizeof expected[0]) == 0);
}

static void test_tick_trace_and_mode_population(void)
{
    SimGameWorld world;
    SimTickState state;
    Trace trace = { { 0 }, 0, 1 };
    SimTickServices services = make_services(&trace);
    static const unsigned source_dos_trace[] = {
        EV_FEED, EV_SMELLS, EV_YARD, EV_WATER, EV_LIONS, EV_SPIDER,
        EV_STRATEGY, EV_BLACK_ANTS, EV_BLACK_NEST, EV_RED_ANTS,
        EV_YELLOW_ANTS, EV_RED_INITIATOR, EV_MOVE_YELLOW, EV_FEEDBACK, EV_END
    };

    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    world.cycle = 63;
    world.world_ticks = 40;
    state.mode_state = 1;
    state.mode_population_enabled = 1;
    state.mode_aux_0f06 = 4;
    state.mode_aux_0f2e = 5;
    state.mode_aux_0f10 = 6;
    state.mode_aux_0ef6 = 7;
    state.mode_point.h = 15;
    state.mode_point.v = 16;
    state.mode_points[0].h = 17;
    state.population_black[2] = 99;
    state.population_counter_08dc = 2;
    state.population_counter_08e8 = 1;

    assert(sim_tick_do_ant_sim(&world, &state, &services) == SIM_TICK_OK);
    assert_trace(&trace, source_dos_trace,
                 sizeof source_dos_trace / sizeof source_dos_trace[0]);
    assert(world.cycle == 64 && world.world_ticks == 41);
    assert(state.population_counter_08dc == 1 && state.population_counter_08e8 == 0);
    assert(state.history_black[0] == 7);
    assert(state.history_black[1] == 0 && state.history_black[2] == 0);
    assert(state.history_red[0] == 0 && state.history_red[5] == 0);
    assert(state.simulation_complete_flag == 1);
}

static void test_cycle_wrap_and_odd_pillar_call(void)
{
    SimGameWorld world;
    SimTickState state;
    Trace trace = { { 0 }, 0, 0 };
    SimTickServices services = make_services(&trace);
    static const unsigned source_dos_trace[] = {
        EV_FEED, EV_SMELLS, EV_YARD, EV_WATER, EV_LIONS, EV_SPIDER,
        EV_STRATEGY, EV_BLACK_ANTS, EV_BLACK_NEST, EV_RED_ANTS,
        EV_YELLOW_ANTS, EV_RED_INITIATOR, EV_MOVE_YELLOW, EV_FEEDBACK
    };

    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    world.cycle = 0x1000;
    world.world_ticks = UINT32_MAX;
    state.population_red[19] = 1;
    assert(sim_tick_do_ant_sim(&world, &state, &services) == SIM_TICK_OK);
    assert_trace(&trace, source_dos_trace,
                 sizeof source_dos_trace / sizeof source_dos_trace[0]);
    assert(world.cycle == 0);
    assert(world.world_ticks == 0);
    assert(state.simulation_complete_flag == 1);

    trace.count = 0;
    world.cycle = 0;
    state.population_red[19] = 1;
    trace.expect_mode_reset = 0;
    assert(sim_tick_do_ant_sim(&world, &state, &services) == SIM_TICK_OK);
    assert(world.cycle == 1);
    assert(trace.events[0] == EV_YARD);
    assert(trace.events[3] == EV_SPIDER);
    assert(trace.events[4] == EV_PILLARS);
    assert(trace.events[5] == EV_STRATEGY);
}

static void test_missing_required_service_is_side_effect_free(void)
{
    SimGameWorld world, before_world;
    SimTickState state, before_state;
    SimTickServices services;
    Trace trace = { { 0 }, 0, 0 };
    memset(&world, 0x5a, sizeof world);
    memset(&state, 0xa5, sizeof state);
    before_world = world;
    before_state = state;
    services = make_services(&trace);
    services.move_spider = 0;
    assert(sim_tick_do_ant_sim(&world, &state, &services) == SIM_TICK_UNSUPPORTED);
    assert(memcmp(&world, &before_world, sizeof world) == 0);
    assert(memcmp(&state, &before_state, sizeof state) == 0);
    assert(trace.count == 0);
}

static void test_mode_population_helpers(void)
{
    SimTickState state;
    memset(&state, 0, sizeof state);
    state.population_black[2] = 30000;
    state.population_black[3] = 10000;
    state.population_black[4] = 8;
    state.population_black[5] = 9;
    state.population_black[1] = 10;
    state.population_black[7] = 11;
    state.population_black[12] = 12;
    state.population_black[6] = 13;
    state.population_red[2] = 1;
    state.population_red[3] = 2;
    state.population_red[19] = 1;
    assert(sim_tick_tally_mode_population(&state, 0, 0, 0) == SIM_TICK_OK);
    assert(state.history_black[0] == (int16_t)0x9c40u);
    assert(state.history_black[1] == 17 && state.history_black[2] == 10);
    assert(state.history_black[3] == 11 && state.history_black[4] == 12);
    assert(state.history_black[5] == 13);
    assert(state.history_red[0] == 3);

    state.population_counter_08dc = -2;
    state.population_counter_08e8 = 1;
    sim_tick_clear_mode_population(&state);
    assert(state.population_counter_08dc == -3);
    assert(state.population_counter_08e8 == 0);
    assert(state.population_black[2] == 0 && state.population_red[19] == 0);
}

int main(void)
{
    test_tick_trace_and_mode_population();
    test_cycle_wrap_and_odd_pillar_call();
    test_missing_required_service_is_side_effect_free();
    test_mode_population_helpers();
    puts("tick tests passed (source-derived callback contract; not full-tick equivalence)");
    return 0;
}
