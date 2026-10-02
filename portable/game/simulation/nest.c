#include "nest.h"

#include <stddef.h>
#include <string.h>

static const int8_t dx8[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
static const int8_t dy8[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
static const uint8_t hole_border_tiles[8] = {
    0x19, 0x1a, 0x1c, 0x1f, 0x1e, 0x1d, 0x1b, 0x18
};

static int add_event(SimNestTrace *trace, SimNestEventKind kind,
                     uint16_t count, int32_t a, int32_t b, int32_t c,
                     int32_t d, int32_t e, int32_t f)
{
    SimNestEvent *event;
    if (trace == NULL || trace->count >= SIM_NEST_EVENT_CAPACITY) {
        if (trace != NULL) trace->overflow = 1;
        return 0;
    }
    event = &trace->events[trace->count++];
    event->kind = (uint16_t)kind;
    event->argument_count = count;
    event->arguments[0] = a;
    event->arguments[1] = b;
    event->arguments[2] = c;
    event->arguments[3] = d;
    event->arguments[4] = e;
    event->arguments[5] = f;
    return 1;
}

static int valid_location(int16_t plane, int16_t x, int16_t y)
{
    if (plane <= 1)
        return x >= 0 && x <= 127 && y >= 0 && y <= 63;
    return x >= 0 && x <= 63 && y >= 0 && y <= 63;
}

static uint8_t *life_cell(SimGameWorld *world, int16_t plane,
                          int16_t x, int16_t y)
{
    if (plane <= 1) return &world->life_a[x][y];
    if (plane == 2) return &world->life_b[x][y];
    if (plane == 3) return &world->life_r[x][y];
    return NULL;
}

static uint8_t *map_cell(SimGameWorld *world, int16_t plane,
                         int16_t x, int16_t y)
{
    if (plane <= 1) return &world->tiles.surface[x][y];
    if (plane == 2) return &world->tiles.nest_b[x][y];
    if (plane == 3) return &world->tiles.nest_r[x][y];
    return NULL;
}

static int is_dirt(uint8_t value)
{
    return value >= 0x20 && value <= 0x2e;
}

static int is_grass(uint8_t value)
{
    return value >= 0x1c && value <= 0x1f;
}

static int is_diggable(SimGameWorld *world, int16_t plane,
                       int16_t x, int16_t y)
{
    uint8_t *tile;
    if (plane < 2 || x < 0 || x > 63 || y < 0 || y > 63)
        return 0;
    tile = map_cell(world, plane, x, y);
    return tile != NULL && (is_dirt(*tile) || is_grass(*tile));
}

static int r_is_dirt(uint8_t value)
{
    if (value < 0x20) return 0;
    if (value > 0x2f && value < 0x4f) return 0;
    return 1;
}

static void zap_tile(SimNestTrace *trace, int16_t plane,
                     int16_t x, int16_t y)
{
    /* ZapEuMapAt invalidates an internal DOS cache.  It does not issue the
     * host-visible InvalEuMap rectangle callback represented by this trace. */
    (void)trace;
    (void)plane;
    (void)x;
    (void)y;
}

static uint16_t get_life(SimGameWorld *world, int16_t plane,
                         int16_t x, int16_t y)
{
    uint8_t *life;
    if (!valid_location(plane, x, y)) return 0xffffu;
    life = life_cell(world, plane, x, y);
    if (life == NULL) return 0xffffu;
    return *life == 0 ? 0xffffu : *life;
}

static void set_life(SimGameWorld *world, SimRng *rng,
                     SimNestRuntime *runtime, SimNestTrace *trace,
                     int16_t plane, int16_t x, int16_t y, uint8_t value);

static void clear_life(SimGameWorld *world, SimRng *rng,
                      SimNestRuntime *runtime, SimNestTrace *trace,
                      int16_t plane, int16_t x, int16_t y, uint8_t marker)
{
    if (!valid_location(plane, x, y)) return;
    if (get_life(world, plane, x, y) == marker)
        set_life(world, rng, runtime, trace, plane, x, y, 0);
    zap_tile(trace, plane, x, y);
}

static int clear_surface_tile(const SimGameWorld *world, int16_t x, int16_t y)
{
    const uint8_t life = world->life_a[x][y];
    return (life == 0 || life == 0xfe || life == 0xff) &&
           world->tiles.surface[x][y] < 16;
}

static int clear_surface_3x3(const SimGameWorld *world,
                             int16_t center_x, int16_t center_y)
{
    int i;
    if (center_x < 1 || center_x >= 127 ||
        center_y < 1 || center_y >= 63 ||
        !clear_surface_tile(world, center_x, center_y))
        return 0;
    for (i = 0; i < 8; ++i) {
        const int16_t x = (int16_t)(center_x + dx8[i]);
        const int16_t y = (int16_t)(center_y + dy8[i]);
        if (!clear_surface_tile(world, x, y)) return 0;
    }
    return 1;
}

static int can_be_house_hole(uint8_t value)
{
    if (value == 0) return 0x86;
    if (value == 2 || value == 3) return 0x8a;
    if (value >= 0x5e && value < 0x62) return value + 0x22;
    if (value == 0x66) return 0x85;
    if (value == 0x68) return 0x84;
    return 0;
}

static void smooth_edges(SimGameWorld *world, SimRng *rng,
                         int16_t plane, int16_t x, int16_t y)
{
    uint8_t *grid;
    uint8_t value;
    int bits = 0;
    int base;

    if (x < 0 || x > 63 || y > 63) return;
    grid = plane == 2 ? &world->tiles.nest_b[0][0] : &world->tiles.nest_r[0][0];
    if (y == 0) {
        if (grid[x * 64 + y] < 0x30) grid[x * 64 + y] = 0x18;
        return;
    }
    value = grid[x * 64 + y];
    if (value < 0x20 || (value > 0x2f && value < 0x4f)) return;
    base = value > 0x4d ? 0x2f : 0;
    if (y < 2) bits = 1;
    else if (r_is_dirt(grid[x * 64 + y - 1])) bits |= 1;
    if (x > 0x3e) bits |= 2;
    else if (r_is_dirt(grid[(x + 1) * 64 + y])) bits |= 2;
    if (y > 0x3e) bits |= 4;
    else if (r_is_dirt(grid[x * 64 + y + 1])) bits |= 4;
    if (x < 1) bits |= 8;
    else if (r_is_dirt(grid[(x - 1) * 64 + y])) bits |= 8;
    if (bits) grid[x * 64 + y] = (uint8_t)(bits + base + 0x1f);
    else if (base == 0) grid[x * 64 + y] = (uint8_t)sim_rng_s8(rng);
    else grid[x * 64 + y] = 0x4e;
}

static void update_exit_map(SimGameWorld *world, int16_t plane,
                            int16_t x, int16_t y)
{
    uint8_t *map;
    uint8_t best = 0;
    int i;
    if (x < 0 || x > 63 || y < 0 || y > 63) return;
    map = plane == 2 ? &world->exit_b[0][0] : &world->exit_r[0][0];
    if (y < 2) {
        const uint8_t tile = plane == 2 ? world->tiles.nest_b[x][y]
                                        : world->tiles.nest_r[x][y];
        map[x * 64 + y] = tile == 0x18 ? 0xff : 0xfe;
        return;
    }
    for (i = 0; i < 8; ++i) {
        const int16_t nx = (int16_t)(x + dx8[i]);
        const int16_t ny = (int16_t)(y + dy8[i]);
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63) continue;
        if (map[nx * 64 + ny] > best) best = map[nx * 64 + ny];
    }
    map[x * 64 + y] = best ? (uint8_t)(best - 1) : 0;
}

static void record_dig_stats(SimNestRuntime *runtime, int16_t plane,
                             int16_t x, int16_t y)
{
    int32_t *sum_x;
    int32_t *sum_y;
    int16_t *count;
    int16_t *average_x;
    int16_t *average_y;
    if (plane == 2) {
        sum_x = &runtime->dug_b_x_sum; sum_y = &runtime->dug_b_y_sum;
        count = &runtime->dug_b_count;
        average_x = &runtime->dug_b_x_average; average_y = &runtime->dug_b_y_average;
    } else {
        sum_x = &runtime->dug_r_x_sum; sum_y = &runtime->dug_r_y_sum;
        count = &runtime->dug_r_count;
        average_x = &runtime->dug_r_x_average; average_y = &runtime->dug_r_y_average;
    }
    *sum_x += x;
    *sum_y += y;
    *count = (int16_t)(*count + 1);
    if (*count > 0) {
        *average_x = (int16_t)(*sum_x / *count);
        *average_y = (int16_t)(*sum_y / *count);
    }
}

static void dig_tile(SimGameWorld *world, SimRng *rng,
                     SimNestRuntime *runtime, int16_t plane,
                     int16_t x, int16_t y)
{
    uint8_t *grid = plane == 2 ? &world->tiles.nest_b[0][0]
                               : &world->tiles.nest_r[0][0];
    if (is_dirt(grid[x * 64 + y])) {
        grid[x * 64 + y] = (uint8_t)sim_rng_s8(rng);
        record_dig_stats(runtime, plane, x, y);
    }
    smooth_edges(world, rng, plane, x, (int16_t)(y - 1));
    smooth_edges(world, rng, plane, (int16_t)(x + 1), y);
    smooth_edges(world, rng, plane, x, (int16_t)(y + 1));
    smooth_edges(world, rng, plane, (int16_t)(x - 1), y);
    update_exit_map(world, plane, x, y);
}

static void set_hole_border(SimGameWorld *world, int16_t x, int16_t y)
{
    int i;
    for (i = 0; i < 8; ++i) {
        const int16_t nx = (int16_t)(x + dx8[i]);
        const int16_t ny = (int16_t)(y + dy8[i]);
        if (nx < 0 || nx > 127 || ny < 0 || ny > 63) continue;
        if (world->tiles.surface[nx][ny] < 0x50)
            world->tiles.surface[nx][ny] = hole_border_tiles[i];
    }
}

static void make_new_hole(SimGameWorld *world, SimRng *rng,
                          SimNestRuntime *runtime, SimNestTrace *trace,
                          int16_t plane, int16_t x)
{
    uint16_t start = 0;
    int i;
    int16_t y = 0;
    (void)add_event(trace, SIM_NEST_SRAND1, 1, 31, 0, 0, 0, 0, 0);
    if (!sim_rng_s1(rng, 31, &start)) return;
    if (world->tiles.terrain_set) {
        for (i = 0; i < 34; ++i) {
            int value;
            y = plane == 2 ? (int16_t)((start + i) % 32 + 2)
                           : (int16_t)(0x7e - (start + i) % 32);
            value = can_be_house_hole(world->tiles.surface[y][x]);
            if (value) {
                world->tiles.surface[y][x] = (uint8_t)value;
                break;
            }
        }
        if (i == 34) return;
    } else {
        for (i = 0; i < 34; ++i) {
            y = plane == 2 ? (int16_t)((start + i) % 32 + 2)
                           : (int16_t)(0x7e - (start + i) % 32);
            if (clear_surface_3x3(world, y, x)) {
                world->tiles.surface[y][x] = 0x50;
                set_hole_border(world, y, x);
                break;
            }
        }
        if (i == 34) return;
    }
    if (plane == 2) {
        world->hole_b[x] = (uint8_t)y;
        runtime->entrance_b_surface_x = y;
        runtime->entrance_b_surface_y = x;
        runtime->entrance_b_nest_x = x;
        runtime->entrance_b_nest_y = 0;
    } else {
        world->hole_r[x] = (uint8_t)y;
        runtime->entrance_r_surface_x = y;
        runtime->entrance_r_surface_y = x;
        runtime->entrance_r_nest_x = x;
        runtime->entrance_r_nest_y = 0;
    }
    dig_tile(world, rng, runtime, plane, x, 1);
}

static void dig_my_tile(SimGameWorld *world, SimRng *rng,
                        SimNestRuntime *runtime, SimNestTrace *trace,
                        int16_t plane, int16_t x, int16_t y)
{
    if (!add_event(trace, SIM_NEST_DIG_TILE, 3, plane, x, y, 0, 0, 0)) return;
    if (!is_diggable(world, plane, x, y)) return;
    if (plane == 2) {
        if (y <= 1) {
            world->tiles.nest_b[x][0] = 0x18;
            make_new_hole(world, rng, runtime, trace, plane, x);
            if (y != 1) return;
        }
    } else {
        if (y <= 1) {
            world->tiles.nest_r[x][0] = 0x18;
            make_new_hole(world, rng, runtime, trace, plane, x);
            if (y != 1) return;
        }
    }
    dig_tile(world, rng, runtime, plane, x, y);
}

SimNestStatus sim_nest_dig_tile(SimGameWorld *world, SimRng *rng,
                                SimNestRuntime *runtime, SimNestTrace *trace,
                                int16_t plane, int16_t x, int16_t y)
{
    if (world == NULL || rng == NULL || runtime == NULL || trace == NULL ||
        (plane != 2 && plane != 3) || x < 0 || x > 63 || y < 0 || y > 63)
        return SIM_NEST_INVALID_ARGUMENT;
    dig_tile(world, rng, runtime, plane, x, y);
    return trace->overflow ? SIM_NEST_TRACE_OVERFLOW : SIM_NEST_OK;
}

SimNestStatus sim_nest_make_new_hole(SimGameWorld *world, SimRng *rng,
                                     SimNestRuntime *runtime, SimNestTrace *trace,
                                     int16_t plane, int16_t nest_x)
{
    if (world == NULL || rng == NULL || runtime == NULL || trace == NULL ||
        (plane != 2 && plane != 3) || nest_x < 0 || nest_x > 63)
        return SIM_NEST_INVALID_ARGUMENT;
    make_new_hole(world, rng, runtime, trace, plane, nest_x);
    return trace->overflow ? SIM_NEST_TRACE_OVERFLOW : SIM_NEST_OK;
}

SimNestStatus sim_nest_dig_my_tile(SimGameWorld *world, SimRng *rng,
                                   SimNestRuntime *runtime, SimNestTrace *trace,
                                   int16_t plane, int16_t x, int16_t y)
{
    if (world == NULL || rng == NULL || runtime == NULL || trace == NULL ||
        (plane != 2 && plane != 3) || x < 0 || x > 63 || y < 0 || y > 63)
        return SIM_NEST_INVALID_ARGUMENT;
    dig_my_tile(world, rng, runtime, trace, plane, x, y);
    return trace->overflow ? SIM_NEST_TRACE_OVERFLOW : SIM_NEST_OK;
}

static void set_life(SimGameWorld *world, SimRng *rng,
                     SimNestRuntime *runtime, SimNestTrace *trace,
                     int16_t plane, int16_t x, int16_t y, uint8_t value)
{
    uint8_t *life;
    if (!valid_location(plane, x, y)) return;
    life = life_cell(world, plane, x, y);
    if (life != NULL) *life = value;
    if ((plane == 2 || plane == 3) && value != 0 && is_diggable(world, plane, x, y)) {
        dig_my_tile(world, rng, runtime, trace, plane, x, y);
        (void)add_event(trace, SIM_NEST_SOUND, 3, 0x13, 0, 0x3f, 0, 0, 0);
    }
    zap_tile(trace, plane, x, y);
}

static int32_t next_tick(const SimNestRequest *request, uint8_t *cursor)
{
    return request->tick_values[(*cursor)++];
}

static SimNestStatus try_ant_theme(SimNestRuntime *runtime,
                                   const SimNestRequest *request,
                                   SimNestTrace *trace)
{
    uint8_t tick_index = 0;
    (void)add_event(trace, SIM_NEST_TRY_THEME, 0, 0, 0, 0, 0, 0, 0);
    const int32_t first = next_tick(request, &tick_index);
    const int32_t threshold = runtime->theme_last_tick + 0x1c20;
    (void)add_event(trace, SIM_NEST_TICK, 0, first, 0, 0, 0, 0, 0);
    if (first >= threshold) {
        int32_t second;
        if (request->tick_count < 2) return SIM_NEST_TICK_INPUT_EXHAUSTED;
        second = next_tick(request, &tick_index);
        runtime->theme_last_tick = second;
        runtime->theme_index = (int16_t)(runtime->theme_index + 1);
        if (runtime->theme_index > 2) runtime->theme_index = 0;
        (void)add_event(trace, SIM_NEST_TICK, 0, second, 0, 0, 0, 0, 0);
        (void)add_event(trace, SIM_NEST_SONG, 2,
                        runtime->theme_index + 0x2713, 0x7e, 0, 0, 0, 0);
    }
    return SIM_NEST_OK;
}

SimNestStatus sim_enter_nest(SimGameWorld *world, SimRng *rng,
                             SimNestRuntime *runtime,
                             const SimNestRequest *request,
                             SimNestTrace *trace)
{
    SimNestStatus status;
    int16_t plane, x, y, ant_type, direction;
    int16_t next_plane, next_x, next_y;

    if (world == NULL || rng == NULL || runtime == NULL || request == NULL || trace == NULL)
        return SIM_NEST_INVALID_ARGUMENT;
    memset(trace, 0, sizeof(*trace));
    if (request->tick_count == 0) return SIM_NEST_TICK_INPUT_EXHAUSTED;

    /* Avoid partial mutation if the first tick proves that a second is needed. */
    if (request->tick_values[0] >= runtime->theme_last_tick + 0x1c20 &&
        request->tick_count < 2)
        return SIM_NEST_TICK_INPUT_EXHAUSTED;
    status = try_ant_theme(runtime, request, trace);
    if (status != SIM_NEST_OK) return status;

    plane = world->current_ant_plane;
    x = world->me_x;
    y = world->me_y;
    ant_type = world->me_type;
    direction = world->me_direction;
    if (runtime->alarm_drop_state != 0) {
        runtime->alarm_drop_state = 0;
        runtime->alarm_indicator = -1;
        (void)add_event(trace, SIM_NEST_ALARM_CLEAR, 2, 0, 1, 0, 0, 0, 0);
        (void)add_event(trace, SIM_NEST_ALARM_SELECTION, 2, 0x10, 0, 0, 0, 0, 0);
        (void)add_event(trace, SIM_NEST_MAP_INVALIDATE, 4,
                        0, 0, runtime->invalidate_right,
                        runtime->invalidate_bottom, 0, 0);
    }

    (void)add_event(trace, SIM_NEST_CLEAR_LIFE, 5,
                    plane, x, y, ant_type, direction, 0);
    clear_life(world, rng, runtime, trace, plane, x, y, 0xff);
    if (ant_type == 0x60) {
        const int back = direction ^ 4;
        clear_life(world, rng, runtime, trace, plane,
                   (int16_t)(x + dx8[back]), (int16_t)(y + dy8[back]), 0xfe);
    }

    next_plane = x > 0x40 ? 3 : 2;
    next_x = y;
    next_y = ant_type == 0x60 ? 2 : 1;
    world->current_ant_plane = next_plane;
    world->me_x = next_x;
    world->me_y = next_y;
    world->me_direction = 4;

    dig_my_tile(world, rng, runtime, trace, next_plane, next_x, next_y);
    (void)add_event(trace, SIM_NEST_SET_LIFE, 6,
                    next_plane, next_x, next_y, ant_type, 4, 0xff);
    set_life(world, rng, runtime, trace, next_plane, next_x, next_y, 0xff);
    if (ant_type == 0x60) {
        const int back = 4 ^ 4;
        set_life(world, rng, runtime, trace, next_plane,
                 (int16_t)(next_x + dx8[back]),
                 (int16_t)(next_y + dy8[back]), 0xfe);
    }
    world->me_type = ant_type;
    if (trace->overflow) return SIM_NEST_TRACE_OVERFLOW;
    return SIM_NEST_OK;
}
