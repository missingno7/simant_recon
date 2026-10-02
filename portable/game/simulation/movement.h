#ifndef SIMANT_GAME_SIMULATION_MOVEMENT_H
#define SIMANT_GAME_SIMULATION_MOVEMENT_H

#include <stdint.h>

/* Native, logical game state. Coordinates index the same x-major grids as the
 * recovered game, but these types contain no DOS segment or address identity. */
typedef struct SimGridPos {
    int16_t x;
    int16_t y;
} SimGridPos;

typedef struct SimRandDirBias {
    int16_t rot;
    int16_t direction;
} SimRandDirBias;

typedef struct SimMoveContext {
    int16_t mode;
    int16_t from_plane;
    SimGridPos from;
    SimGridPos previous;
} SimMoveContext;

typedef struct SimWorldTiles {
    uint8_t surface[128][64];
    uint8_t nest_b[64][64];
    uint8_t nest_r[64][64];
    int16_t terrain_set;
} SimWorldTiles;

typedef struct SimTileQuery {
    int16_t plane;
    int16_t x;
    int16_t y;
    int16_t from_plane;
    int16_t from_x;
    int16_t from_y;
    int16_t digging;
    int16_t result;
} SimTileQuery;

typedef struct SimMoveTrace {
    uint16_t tile_query_count;
    SimTileQuery tile_queries[8];
} SimMoveTrace;

/* Direction indices are clockwise from north, 0 through 7. GetDir returns the
 * historical one-based direction (0 for coincident points). */
int16_t sim_get_dir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
int32_t sim_get_dis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);

int16_t sim_tile_can_be_moved_on(const SimWorldTiles *world,
                                 int16_t plane, int16_t x, int16_t y,
                                 int16_t from_plane, int16_t from_x,
                                 int16_t from_y, int16_t digging);

/* Returns -1 for a coincident target, -2 if no eligible move exists, or the
 * selected direction 0..7. Bias is updated using the original game rules. */
int16_t sim_get_my_rand_dirs(const SimWorldTiles *world,
                             const SimMoveContext *context,
                             int16_t plane, SimGridPos current,
                             SimGridPos target, SimRandDirBias *bias,
                             SimMoveTrace *trace);

#endif
