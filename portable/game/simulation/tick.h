#ifndef SIMANT_GAME_SIMULATION_TICK_H
#define SIMANT_GAME_SIMULATION_TICK_H

#include <stdint.h>

#include "../state/world.h"

typedef enum SimTickStatus {
    SIM_TICK_OK = 0,
    SIM_TICK_UNSUPPORTED = 1,
    SIM_TICK_INVALID_ARGUMENT = 2
} SimTickStatus;

typedef struct SimTickPoint {
    int16_t v;
    int16_t h;
} SimTickPoint;

/* State owned by DoAntSim/ClrModePop/TallyModePop but not yet folded into the
 * portable world arrays. It is caller-owned and must be initialized from the
 * source globals/static data before a full game tick is wired. */
typedef struct SimTickState {
    int16_t mode_state;                 /* fd_3D57_07B2 */
    int16_t mode_population_enabled;    /* fd_50F6_0376 */
    int16_t simulation_complete_flag;   /* fd_3D57_02C2 */
    int16_t mode_aux_0f06;
    int16_t mode_aux_0f2e;
    int16_t mode_aux_0f10;
    int16_t mode_aux_0ef6;
    SimTickPoint mode_point;
    SimTickPoint mode_points[3];        /* fd_50F6_0AA2,0A02,0852 */
    int16_t population_black[20];       /* fd_50F6_0D40 */
    int16_t population_red[20];         /* fd_50F6_0D72 */
    int16_t history_black[6];           /* fd_50F6_0B12 */
    int16_t history_red[6];             /* fd_50F6_0C2A */
    int16_t population_counter_08dc;
    int16_t population_counter_08e8;
} SimTickState;

typedef void (*SimTickSubsystem)(SimGameWorld *world, SimTickState *state,
                                 void *context);
typedef void (*SimTickEndGame)(SimGameWorld *world, SimTickState *state,
                               int source_argument, void *context);

/* Every unported source subsystem is a required callback. Their order follows
 * root DoAntSim; callbacks must perform their real state changes. */
typedef struct SimTickServices {
    SimTickSubsystem feed_ants;             /* FeedAnts */
    SimTickSubsystem do_smells;             /* DoSmells */
    SimTickSubsystem simulate_yard;         /* o06_35F5_0173 / DoSimYard */
    SimTickSubsystem do_water;              /* DoWater */
    SimTickSubsystem do_ant_lions;          /* f_0AD9_03D3 */
    SimTickSubsystem move_spider;           /* f_0CDB_00B3 / MoveSpider */
    SimTickSubsystem do_pillars;            /* f_0AD9_093C */
    SimTickSubsystem get_strategy;           /* f_1383_0002 / GetStrategy */
    SimTickSubsystem simulate_black_ants;    /* DoAntSimA */
    SimTickSubsystem process_black_nest;     /* o25_39C7_0000 */
    SimTickSubsystem simulate_red_ants;      /* DoAntSimR */
    SimTickSubsystem simulate_yellow_ants;   /* DoAntSimY */
    SimTickSubsystem move_yellow_ants;       /* DoAntMoveY */
    SimTickSubsystem feedback;               /* f_0E2E_000A */
    SimTickSubsystem red_initiator;          /* f_0DEF_0000 */
    SimTickEndGame end_game_dialog;          /* o14_384C_0DE5(0) */
    void *context;
} SimTickServices;

/* Source-owned suboperations. Tally's conditional red-initiator transition
 * requires a real callback when population_red[19] is below one. */
void sim_tick_clear_mode_population(SimTickState *state);
SimTickStatus sim_tick_tally_mode_population(SimTickState *state,
                                             SimTickSubsystem red_initiator,
                                             SimGameWorld *world,
                                             void *context);

/* Scheduler for the original root DoAntSim. It owns only cycle/tick counters,
 * mode-pop clearing/tallying, and ordered dispatch. Any missing service needed
 * on this tick returns UNSUPPORTED before changing state. This is not a full
 * simulation implementation until every supplied service is real. */
SimTickStatus sim_tick_do_ant_sim(SimGameWorld *world, SimTickState *state,
                                  const SimTickServices *services);

#endif
