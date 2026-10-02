#ifndef SIMANT_GAME_SIMULATION_YELLOW_H
#define SIMANT_GAME_SIMULATION_YELLOW_H

#include <stdint.h>

#include "movement.h"
#include "nest.h"

typedef enum SimYellowStatus {
    SIM_YELLOW_OK = 0,
    SIM_YELLOW_INVALID_ARGUMENT = 1,
    SIM_YELLOW_UNSUPPORTED_GAMEPLAY = 2,
    SIM_YELLOW_TRACE_OVERFLOW = 3
} SimYellowStatus;

typedef enum SimYellowEventKind {
    SIM_YELLOW_EVENT_EDIT_DRAW = 1,
    SIM_YELLOW_EVENT_ANIMATION = 2,
    SIM_YELLOW_EVENT_SOUND = 3,
    SIM_YELLOW_EVENT_MAP_INVALIDATE = 4,
    SIM_YELLOW_EVENT_MESSAGE = 5,
    SIM_YELLOW_EVENT_TILE_QUERY = 6
} SimYellowEventKind;

typedef enum SimYellowMissingService {
    SIM_YELLOW_MISSING_NONE = 0,
    SIM_YELLOW_MISSING_TRY_DROP_OR_LIFT = 1,
    SIM_YELLOW_MISSING_TARGET_ANT_REMOVAL = 2,
    SIM_YELLOW_MISSING_EXIT_NEST = 3,
    SIM_YELLOW_MISSING_PLANE_DIG_EFFECT = 4,
    SIM_YELLOW_MISSING_POPULATION_EFFECT = 5,
    SIM_YELLOW_MISSING_ALARM_EFFECT = 6
} SimYellowMissingService;

typedef struct SimYellowEvent {
    uint16_t kind;
    uint16_t argument_count;
    int32_t arguments[6];
} SimYellowEvent;

#define SIM_YELLOW_EVENT_CAPACITY 64

typedef struct SimYellowTrace {
    uint16_t count;
    uint8_t overflow;
    int16_t result;
    int16_t missing_service;
    SimMoveTrace movement;
    SimNestTrace nest;
    SimYellowEvent events[SIM_YELLOW_EVENT_CAPACITY];
} SimYellowTrace;

/* Per-player intent kept separate from shared world/tile state.  The fields
 * correspond to the live inputs consumed by S25 DoAntMoveY; source-sized
 * integers retain their original signed 16-bit behavior. */
typedef struct SimYellowState {
    int16_t move_enabled;
    int16_t movement_mode;
    int16_t target_list;
    int16_t target_index;
    int16_t caste_mask;
    int16_t target_plane;
    int16_t target_x;
    int16_t target_y;
    int16_t previous_x;
    int16_t previous_y;
    int16_t rotation;
    int16_t preferred_direction;
    int16_t map_plane;
    int16_t health_tick_count;
    int16_t carried_food;
    int16_t player_caste;
    int16_t alarm_drop_state;
    int16_t movement_count;
    int16_t current_penalty;
    int16_t target_mode_active;
    int16_t target_window_open;
    int16_t map_warning_enabled;
    int16_t overlay_underfoot;
    int16_t food_motion_gate;
    int16_t food_stock_mode;
    int16_t food_stock;
    int16_t message_resource;
    int16_t sound_disabled;
    int16_t path_delay;
    int32_t nest_ticks[2];
    uint8_t nest_tick_count;
    uint8_t _padding;
    /* O25_3BA4_1A9F's four explicit path landmarks. */
    SimGridPos landmark_02A4;
    SimGridPos landmark_02A8;
    SimGridPos landmark_02AC;
    SimGridPos landmark_02B0;
} SimYellowState;

/* Executes one source-derived yellow-player movement update. UI/audio effects
 * are returned as typed intents. If execution reaches a gameplay helper that
 * has no native implementation, the function returns UNSUPPORTED_GAMEPLAY
 * and identifies that service instead of reporting success. */
SimYellowStatus sim_do_ant_move_y(SimGameWorld *world, SimRng *rng,
                                  SimNestRuntime *nest_runtime,
                                  SimYellowState *state,
                                  SimYellowTrace *trace);

#endif
