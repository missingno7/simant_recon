#include "movement.h"

#include <stddef.h>

static const int8_t dx8[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
static const int8_t dy8[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };

int16_t sim_get_dir(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    const int32_t dx = (int32_t)x2 - x1;
    const int32_t dy = (int32_t)y2 - y1;

    if (dx == 0) {
        if (dy == 0) return 0;
        return dy < 0 ? 1 : 5;
    }
    if (dx > 0) {
        if (dy < 0) return 2;
        if (dy == 0) return 3;
        return 4;
    }
    if (dy > 0) return 6;
    if (dy == 0) return 7;
    return 8;
}

int32_t sim_get_dis(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    const int32_t dx = (int32_t)x2 - x1;
    const int32_t dy = (int32_t)y2 - y1;
    return dx * dx + dy * dy;
}

int16_t sim_tile_can_be_moved_on(const SimWorldTiles *world,
                                 int16_t plane, int16_t x, int16_t y,
                                 int16_t from_plane, int16_t from_x,
                                 int16_t from_y, int16_t digging)
{
    int tile;
    int dig = 0;
    int ok = 0;

    if (world == NULL) return 0;
    if (plane <= 1) {
        if (x < 0 || x > 127 || y < 0 || y > 63) return 0;
        tile = world->surface[x][y];
        return tile <= (world->terrain_set ? 0x90 : 0x53);
    }

    if (x < 0 || x > 63 || y < 0 || y > 63) return 0;
    tile = plane == 2 ? world->nest_b[x][y] : world->nest_r[x][y];
    if (tile <= 0x18 || (tile >= 0x30 && tile <= 0x31)) {
        ok = 1;
    } else if (digging && ((tile >= 0x20 && tile <= 0x2e) ||
                           (tile >= 0x1c && tile <= 0x1f))) {
        ok = 1;
        dig = 1;
    }

    if (ok && y <= 1 && from_plane == plane) {
        if (!digging) {
            if (y == 0) {
                if (from_x != x || from_y != y) ok = 0;
            } else if (from_x != x && !from_y) {
                ok = 0;
            }
        } else if (dig) {
            if (from_x != x) {
                ok = 0;
            } else if (y == 0) {
                const int below = plane == 2 ? world->nest_b[x][1] : world->nest_r[x][1];
                if (below >= 0x20 && below <= 0x2e) ok = 0;
            }
        } else if (y == 0 && (from_x != x || from_y != y)) {
            ok = 0;
        }
    }
    return (int16_t)ok;
}

int16_t sim_get_my_rand_dirs(const SimWorldTiles *world,
                             const SimMoveContext *context,
                             int16_t plane, SimGridPos current,
                             SimGridPos target, SimRandDirBias *bias,
                             SimMoveTrace *trace)
{
    uint8_t ok[8] = { 0 };
    int16_t best = -1;
    int16_t right, left;
    int32_t threshold;
    int i;
    const int16_t digging = context != NULL && context->mode == 2;

    if (trace != NULL) trace->tile_query_count = 0;

    if (context == NULL || bias == NULL || world == NULL) return -2;
    threshold = sim_get_dis(current.x, current.y, target.x, target.y);
    if (threshold <= 0) return -1;

    best = -2;
    for (i = 0; i < 8; ++i) {
        const int16_t nx = (int16_t)(current.x + dx8[i]);
        const int16_t ny = (int16_t)(current.y + dy8[i]);
        if (nx == context->previous.x && ny == context->previous.y) continue;
        {
            const int16_t moved = sim_tile_can_be_moved_on(
                world, plane, nx, ny, context->from_plane,
                context->from.x, context->from.y, digging);
            if (trace != NULL && trace->tile_query_count < 8) {
                SimTileQuery *q = &trace->tile_queries[trace->tile_query_count++];
                q->plane = plane;
                q->x = nx;
                q->y = ny;
                q->from_plane = context->from_plane;
                q->from_x = context->from.x;
                q->from_y = context->from.y;
                q->digging = digging;
                q->result = moved;
            }
            if (moved) {
                best = (int16_t)i;
                ok[i] = 1;
            }
        }
    }
    if (best < 0) return best;

    best = -1;
    right = left = bias->direction;
    if (bias->rot == 0) {
        for (i = 0; i < 8; ++i) {
            if (ok[right]) {
                best = right;
                bias->direction = (int16_t)(sim_get_dir(current.x, current.y,
                                                       target.x, target.y) - 1);
                bias->rot = 1;
                break;
            }
            if (ok[left]) {
                best = left;
                bias->direction = (int16_t)(sim_get_dir(current.x, current.y,
                                                       target.x, target.y) - 1);
                bias->rot = -1;
                break;
            }
            right = (int16_t)((right + 1) & 7);
            left = (int16_t)((left - 1) & 7);
        }
    } else {
        for (i = 0; i < 8; ++i) {
            if (bias->rot > 0) {
                if (ok[right]) break;
            } else if (ok[left]) {
                right = left;
                break;
            }
            right = (int16_t)((right + 1) & 7);
            left = (int16_t)((left - 1) & 7);
        }
        if (i < 8) {
            const int32_t distance = sim_get_dis(
                (int16_t)(current.x + dx8[right]),
                (int16_t)(current.y + dy8[right]), target.x, target.y);
            if (distance <= threshold) {
                bias->direction = (int16_t)(sim_get_dir(current.x, current.y,
                                                       target.x, target.y) - 1);
                bias->rot = 0;
            }
            return right;
        }
    }
    return best;
}
