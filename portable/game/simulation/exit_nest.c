#include "exit_nest.h"

#include <string.h>

#include "ants.h"

static const int8_t dx8[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
static const int8_t dy8[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
static const int8_t turn_offsets[8] = { 0, 1, -1, 2, -2, 3, -3, 4 };

static int trace_add(SimNestTrace *trace, SimNestEventKind kind,
                     uint16_t count, int32_t a, int32_t b)
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
    event->arguments[2] = event->arguments[3] = 0;
    event->arguments[4] = event->arguments[5] = 0;
    return 1;
}

static SimExitNestStatus try_ant_theme(SimNestRuntime *runtime,
                                       const SimExitNestContext *context,
                                       SimNestTrace *trace)
{
    const int32_t threshold = runtime->theme_last_tick + 0x1c20;
    int tick_index = 0;

    if (context->tick_count == 0)
        return SIM_EXIT_NEST_TICK_INPUT_EXHAUSTED;
    if (context->tick_values[0] >= threshold && context->tick_count < 2)
        return SIM_EXIT_NEST_TICK_INPUT_EXHAUSTED;

    (void)trace_add(trace, SIM_NEST_TRY_THEME, 0, 0, 0);
    (void)trace_add(trace, SIM_NEST_TICK, 0,
                    context->tick_values[tick_index++], 0);
    if (context->tick_values[0] >= threshold) {
        runtime->theme_last_tick = context->tick_values[tick_index];
        runtime->theme_index = (int16_t)(runtime->theme_index + 1);
        if (runtime->theme_index > 2) runtime->theme_index = 0;
        (void)trace_add(trace, SIM_NEST_TICK, 0,
                        context->tick_values[tick_index], 0);
        (void)trace_add(trace, SIM_NEST_SONG, 2,
                        runtime->theme_index + 0x2713, 0x7e);
    }
    return trace->overflow ? SIM_EXIT_NEST_TRACE_OVERFLOW : SIM_EXIT_NEST_OK;
}

static void clear_player_life(SimGameWorld *world)
{
    uint8_t *life = NULL;
    if (world->current_ant_plane <= 1 && world->me_x >= 0 && world->me_x <= 127 &&
        world->me_y >= 0 && world->me_y <= 63)
        life = &world->life_a[world->me_x][world->me_y];
    else if (world->current_ant_plane == 2 && world->me_x >= 0 && world->me_x <= 63 &&
             world->me_y >= 0 && world->me_y <= 63)
        life = &world->life_b[world->me_x][world->me_y];
    else if (world->current_ant_plane == 3 && world->me_x >= 0 && world->me_x <= 63 &&
             world->me_y >= 0 && world->me_y <= 63)
        life = &world->life_r[world->me_x][world->me_y];
    if (life != NULL && *life == 0xff) *life = 0;

    if (world->me_type == 0x60 && world->me_direction >= 0 && world->me_direction < 8) {
        const int tail = world->me_direction ^ 4;
        const int tx = world->me_x + dx8[tail];
        const int ty = world->me_y + dy8[tail];
        if (world->current_ant_plane <= 1 && tx >= 0 && tx <= 127 && ty >= 0 && ty <= 63) {
            if (world->life_a[tx][ty] == 0xfe) world->life_a[tx][ty] = 0;
        } else if (world->current_ant_plane == 2 && tx >= 0 && tx <= 63 && ty >= 0 && ty <= 63) {
            if (world->life_b[tx][ty] == 0xfe) world->life_b[tx][ty] = 0;
        } else if (world->current_ant_plane == 3 && tx >= 0 && tx <= 63 && ty >= 0 && ty <= 63) {
            if (world->life_r[tx][ty] == 0xfe) world->life_r[tx][ty] = 0;
        }
    }
}

static int surface_not_obstacle(const SimGameWorld *world, int x, int y)
{
    int tile;
    if (x < 0 || x > 127 || y < 0 || y > 63) return 0;
    tile = world->tiles.surface[x][y];
    return world->tiles.terrain_set ? tile <= 0x5f : tile <= 0x50;
}

SimExitNestStatus sim_exit_nest(SimGameWorld *world, SimRng *rng,
                                SimNestRuntime *runtime,
                                SimExitNestContext *context,
                                SimMoveTrace *movement_trace,
                                SimNestTrace *nest_trace)
{
    SimExitNestStatus status;
    SimNestStatus nest_status;
    SimMoveContext move_context;
    SimRandDirBias bias;
    int16_t start_plane, x, y, step, direction, candidate;
    int i;

    if (world == NULL || rng == NULL || runtime == NULL || context == NULL ||
        movement_trace == NULL || nest_trace == NULL ||
        (world->current_ant_plane != 2 && world->current_ant_plane != 3) ||
        world->me_x < 0 || world->me_x > 63 || world->me_y < 0 || world->me_y > 63)
        return SIM_EXIT_NEST_INVALID_ARGUMENT;
    status = try_ant_theme(runtime, context, nest_trace);
    if (status != SIM_EXIT_NEST_OK) return status;

    start_plane = world->current_ant_plane;
    clear_player_life(world);
    y = (int16_t)(world->me_x & 0x3f);
    if (start_plane == 2) {
        if (world->hole_b[y] == 0) {
            nest_status = sim_nest_make_new_hole(world, rng, runtime, nest_trace,
                                                 2, world->me_x);
            if (nest_status != SIM_NEST_OK) return SIM_EXIT_NEST_NEST_ERROR;
        }
        x = world->hole_b[y];
    } else {
        if (world->hole_r[y] == 0) {
            nest_status = sim_nest_make_new_hole(world, rng, runtime, nest_trace,
                                                 3, world->me_x);
            if (nest_status != SIM_NEST_OK) return SIM_EXIT_NEST_NEST_ERROR;
        }
        x = world->hole_r[y];
    }

    step = world->me_type == 0x60 ? 2 : 1;
    if (context->target_plane == 1) {
        direction = sim_get_dir(x, y, context->target.x, context->target.y);
        if (direction > 0) --direction;
    } else if (start_plane == context->target_plane) {
        direction = x < 0x40 ? 2 : 6;
    } else {
        move_context.mode = context->movement_mode;
        move_context.from_plane = context->target_plane;
        move_context.from = context->target;
        move_context.previous = context->previous;
        bias.rot = context->rotation;
        bias.direction = context->preferred_direction;
        direction = sim_get_my_rand_dirs(&world->tiles, &move_context, 1,
                                         (SimGridPos){x, y}, context->target,
                                         &bias, movement_trace);
        context->rotation = bias.rot;
        context->preferred_direction = bias.direction;
        if (direction < 0) direction = (int16_t)sim_rng_s8(rng);
    }

    for (i = 0; i < 8; ++i) {
        candidate = (int16_t)((turn_offsets[i] + direction) & 7);
        {
            const int nx = x + dx8[candidate] * step;
            const int ny = y + dy8[candidate] * step;
            if (surface_not_obstacle(world, nx, ny)) {
                x = (int16_t)nx;
                y = (int16_t)ny;
                direction = candidate;
                break;
            }
        }
    }
    if (i == 8) {
        x = (int16_t)((x + step) & 0x7f);
    }
    (void)sim_set_my_life(world, 1, x, y, world->me_type, direction, 0xff);
    return nest_trace->overflow ? SIM_EXIT_NEST_TRACE_OVERFLOW : SIM_EXIT_NEST_OK;
}
