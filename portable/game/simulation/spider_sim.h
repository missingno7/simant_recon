#ifndef SIMANT_GAME_SIMULATION_SPIDER_SIM_H
#define SIMANT_GAME_SIMULATION_SPIDER_SIM_H

#include <stdint.h>

#include "spider.h"

typedef enum SimSpiderTickStatus {
    SIM_SPIDER_TICK_OK = 0,
    SIM_SPIDER_TICK_UNSUPPORTED = 1,
    SIM_SPIDER_TICK_INVALID_ARGUMENT = 2,
    SIM_SPIDER_TICK_EVENT_OVERFLOW = 3
} SimSpiderTickStatus;

typedef enum SimSpiderEventKind {
    SIM_SPIDER_EVENT_LASER = 1,
    SIM_SPIDER_EVENT_SOUND = 2,
    SIM_SPIDER_EVENT_DIALOG = 3,
    SIM_SPIDER_EVENT_YELLOW_DEATH = 4,
    SIM_SPIDER_EVENT_MOVE_PLAYER_LIFE = 5,
    SIM_SPIDER_EVENT_DEATH_FRAME = 6,
    SIM_SPIDER_EVENT_PLAYER_REFRESH = 7,
    SIM_SPIDER_EVENT_PATH_QUERY = 8
} SimSpiderEventKind;

typedef struct SimSpiderTickState {
    int16_t player_control; /* fd_50F6_0A06 */
    int16_t route_mode;     /* fd_50F6_0A8E */
    int16_t death_count;    /* DeathCnt */
    int32_t red_ants_eaten; /* RAntsEaten */
    int32_t black_ants_eaten; /* BAntsEaten */
    uint8_t options[6];     /* fd_3D57_07A8[0..5] */
} SimSpiderTickState;

typedef struct SimSpiderEvent {
    uint16_t kind;
    int16_t values[5];
} SimSpiderEvent;

#define SIM_SPIDER_EVENT_CAPACITY 32
typedef struct SimSpiderTickEffects {
    uint16_t count;
    uint8_t overflow;
    SimSpiderEvent events[SIM_SPIDER_EVENT_CAPACITY];
} SimSpiderTickEffects;

typedef int16_t (*SimSpiderRouteDirection)(void *userdata,
                                           const SimGameWorld *world,
                                           int16_t plane, int16_t x,
                                           int16_t y, int16_t target_x,
                                           int16_t target_y);

typedef struct SimSpiderTickServices {
    SimSpiderRouteDirection route_direction; /* o25_39C7_0CBD */
    void *userdata;
} SimSpiderTickServices;

/* One logical MoveSpider (DOS f_0CDB_00B3) tick. Calls into the independent
 * pathfinding subsystem are explicit; host-facing effects are ordered events. */
SimSpiderTickStatus sim_spider_tick(SimGameWorld *world, SimRng *rng,
                                    SimSpiderState *spider,
                                    SimSpiderTickState *tick,
                                    const SimSpiderTickServices *services,
                                    SimSpiderTickEffects *effects);

#endif
