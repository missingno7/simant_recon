#include "yellow.h"

#include <stddef.h>
#include <string.h>

#include "ants.h"
#include "exit_nest.h"

static const int8_t dx8[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
static const int8_t dy8[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };

static int emit(SimYellowTrace *trace, SimYellowEventKind kind,
                uint16_t count, int32_t a, int32_t b, int32_t c,
                int32_t d, int32_t e, int32_t f)
{
    SimYellowEvent *event;
    if (trace == NULL || trace->count >= SIM_YELLOW_EVENT_CAPACITY) {
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

static uint8_t *life_at(SimGameWorld *world, int16_t plane,
                        int16_t x, int16_t y)
{
    if (!valid_location(plane, x, y)) return NULL;
    if (plane <= 1) return &world->life_a[x][y];
    if (plane == 2) return &world->life_b[x][y];
    if (plane == 3) return &world->life_r[x][y];
    return NULL;
}

static int get_life(const SimGameWorld *world, int16_t plane,
                    int16_t x, int16_t y)
{
    const uint8_t *life;
    if (!valid_location(plane, x, y)) return -1;
    if (plane <= 1) life = &world->life_a[x][y];
    else if (plane == 2) life = &world->life_b[x][y];
    else if (plane == 3) life = &world->life_r[x][y];
    else return -1;
    return *life == 0 ? -1 : *life;
}

static int get_map(const SimGameWorld *world, int16_t plane,
                   int16_t x, int16_t y)
{
    if (!valid_location(plane, x, y)) return -1;
    if (plane <= 1) return world->tiles.surface[x][y];
    if (plane == 2) return world->tiles.nest_b[x][y];
    if (plane == 3) return world->tiles.nest_r[x][y];
    return -1;
}

static int is_yellow_life(int life)
{
    return life == 0xff || life == 0xfe;
}

static int is_clear_tile(const SimGameWorld *world, int16_t plane,
                         int16_t x, int16_t y)
{
    const int map = get_map(world, plane, x, y);
    const int life = get_life(world, plane, x, y);
    if (map < 0 || (life >= 0 && !is_yellow_life(life))) return 0;
    return map < (plane <= 1 ? 16 : 8);
}

static void fix_exit_map(SimGameWorld *world, int16_t plane,
                         int16_t x, int16_t y)
{
    uint8_t (*exit_map)[64];
    int best = 0;
    int i;
    if (plane != 2 && plane != 3) return;
    if (x < 0 || x > 63 || y < 0 || y > 63) return;
    exit_map = plane == 2 ? world->exit_b : world->exit_r;
    if (y < 2) {
        exit_map[x][y] = get_map(world, plane, x, y) == 0x18 ? 0xff : 0xfe;
        return;
    }
    for (i = 0; i < 8; ++i) {
        const int nx = x + dx8[i];
        const int ny = y + dy8[i];
        if (nx >= 0 && nx < 64 && ny >= 0 && ny < 64 &&
            exit_map[nx][ny] > best)
            best = exit_map[nx][ny];
    }
    exit_map[x][y] = best ? (uint8_t)(best - 1) : 0;
}

static int is_diggable(int tile)
{
    return (tile >= 0x20 && tile <= 0x2e) ||
           (tile >= 0x1c && tile <= 0x1f);
}

static SimYellowStatus set_life(SimGameWorld *world, SimRng *rng,
                                SimNestRuntime *nest_runtime,
                                SimYellowTrace *trace, int16_t plane,
                                int16_t x, int16_t y, uint8_t value)
{
    uint8_t *life = life_at(world, plane, x, y);
    SimNestStatus nest_status;
    if (life == NULL) return SIM_YELLOW_OK;
    *life = value;
    if ((plane == 2 || plane == 3) && value != 0 &&
        is_diggable(get_map(world, plane, x, y))) {
        nest_status = sim_nest_dig_my_tile(world, rng, nest_runtime,
                                           &trace->nest, plane, x, y);
        if (nest_status != SIM_NEST_OK)
            return SIM_YELLOW_UNSUPPORTED_GAMEPLAY;
        (void)emit(trace, SIM_YELLOW_EVENT_SOUND, 3, 0x13, 0, 0x3f, 0, 0, 0);
    }
    return SIM_YELLOW_OK;
}

static SimYellowStatus set_my_life(SimGameWorld *world, SimRng *rng,
                                   SimNestRuntime *nest_runtime,
                                   SimYellowTrace *trace, int16_t plane,
                                   int16_t x, int16_t y, int16_t type,
                                   int16_t direction, int16_t value)
{
    SimYellowStatus status;
    const int tail = direction ^ 4;
    if (!valid_location(plane, x, y)) return SIM_YELLOW_OK;
    status = set_life(world, rng, nest_runtime, trace, plane, x, y,
                      (uint8_t)value);
    if (status != SIM_YELLOW_OK) return status;
    if (type == 0x60 && tail >= 0 && tail < 8) {
        const uint8_t tail_value = value == 0xff ? 0xfe : (uint8_t)value;
        status = set_life(world, rng, nest_runtime, trace, plane,
                          (int16_t)(x + dx8[tail]),
                          (int16_t)(y + dy8[tail]), tail_value);
        if (status != SIM_YELLOW_OK) return status;
    }
    if (value != 0) {
        world->me_x = x;
        world->me_y = y;
        world->me_direction = direction;
        world->me_type = type;
        world->current_ant_plane = plane;
    }
    return SIM_YELLOW_OK;
}

static SimYellowStatus clear_my_life(SimGameWorld *world, SimRng *rng,
                                     SimNestRuntime *nest_runtime,
                                     SimYellowTrace *trace, int16_t plane,
                                     int16_t x, int16_t y, int16_t type,
                                     int16_t direction)
{
    uint8_t *life = life_at(world, plane, x, y);
    SimYellowStatus status;
    if (life != NULL && *life == 0xff) {
        status = set_life(world, rng, nest_runtime, trace, plane, x, y, 0);
        if (status != SIM_YELLOW_OK) return status;
    }
    if (type == 0x60) {
        const int tail = direction ^ 4;
        const int tx = x + dx8[tail & 7];
        const int ty = y + dy8[tail & 7];
        life = life_at(world, plane, (int16_t)tx, (int16_t)ty);
        if (life != NULL && *life == 0xfe)
            return set_life(world, rng, nest_runtime, trace, plane,
                            (int16_t)tx, (int16_t)ty, 0);
    }
    return SIM_YELLOW_OK;
}

static SimYellowStatus move_my_life(SimGameWorld *world, SimRng *rng,
                                    SimNestRuntime *nest_runtime,
                                    SimYellowTrace *trace, int16_t plane,
                                    int16_t x, int16_t y, int16_t type,
                                    int16_t direction)
{
    SimYellowStatus status;
    status = clear_my_life(world, rng, nest_runtime, trace,
                           world->current_ant_plane, world->me_x,
                           world->me_y, world->me_type, world->me_direction);
    if (status != SIM_YELLOW_OK) return status;
    return set_my_life(world, rng, nest_runtime, trace, plane, x, y,
                       type, direction, 0xff);
}

static int get_ant_index(const SimGameWorld *world, int16_t list,
                         int16_t index, int16_t *x, int16_t *y,
                         int16_t *type, int16_t *mode, int16_t *direction)
{
    if (list <= 1) {
        const SimAntList *ants = &world->ants_a;
        if (index < 0 || index >= ants->count) return 0;
        *x = ants->x[index]; *y = ants->y[index]; *type = ants->type[index];
        *mode = ants->mode[index]; *direction = ants->state[index];
    } else if (list == 2) {
        const SimSmallAntList *ants = &world->ants_b;
        if (index < 0 || index >= ants->count) return 0;
        *x = ants->x[index]; *y = ants->y[index]; *type = ants->type[index];
        *mode = ants->mode[index]; *direction = ants->state[index];
    } else {
        const SimSmallAntList *ants = &world->ants_r;
        if (index < 0 || index >= ants->count) return 0;
        *x = ants->x[index]; *y = ants->y[index]; *type = ants->type[index];
        *mode = ants->mode[index]; *direction = ants->state[index];
    }
    return 1;
}

static void set_ant_index(SimGameWorld *world, int16_t list, int16_t index,
                          int16_t x, int16_t y, int16_t type,
                          int16_t mode, int16_t direction)
{
    if (list <= 1) {
        SimAntList *ants = &world->ants_a;
        if (index < 0 || index >= ants->count) return;
        ants->x[index] = (uint8_t)x; ants->y[index] = (uint8_t)y;
        ants->type[index] = (uint8_t)type; ants->mode[index] = (uint8_t)mode;
        ants->state[index] = (uint8_t)direction;
    } else if (list == 2) {
        SimSmallAntList *ants = &world->ants_b;
        if (index < 0 || index >= ants->count) return;
        ants->x[index] = (uint8_t)x; ants->y[index] = (uint8_t)y;
        ants->type[index] = (uint8_t)type; ants->mode[index] = (uint8_t)mode;
        ants->state[index] = (uint8_t)direction;
    } else {
        SimSmallAntList *ants = &world->ants_r;
        if (index < 0 || index >= ants->count) return;
        ants->x[index] = (uint8_t)x; ants->y[index] = (uint8_t)y;
        ants->type[index] = (uint8_t)type; ants->mode[index] = (uint8_t)mode;
        ants->state[index] = (uint8_t)direction;
    }
}

static int best_direction(const SimGameWorld *world,
                          const SimYellowState *state,
                          int16_t plane, int16_t x, int16_t y,
                          int16_t goal_x, int16_t goal_y)
{
    int best = -1;
    int fallback = -2;
    int32_t threshold = sim_get_dis(x, y, goal_x, goal_y);
    int dir;
    const int digging = state->movement_mode == 2 ? 1 : 0;
    if (threshold > 0) {
        for (dir = 0; dir < 8; ++dir) {
            const int nx = x + dx8[dir];
            const int ny = y + dy8[dir];
            int32_t distance;
            if (!sim_tile_can_be_moved_on(&world->tiles, plane,
                    (int16_t)nx, (int16_t)ny, state->target_plane,
                    state->target_x, state->target_y, (int16_t)digging))
                continue;
            distance = sim_get_dis((int16_t)nx, (int16_t)ny, goal_x, goal_y);
            if (distance < threshold) {
                if (get_life(world, plane, (int16_t)nx, (int16_t)ny) > 0 ||
                    !is_clear_tile(world, plane, (int16_t)nx, (int16_t)ny))
                    fallback = dir;
                else
                    best = dir;
                threshold = distance;
            }
        }
    }
    if (best < 0 && threshold > 0) best = fallback;
    return best;
}

static int walk_steps(const SimGameWorld *world, const SimYellowState *state,
                      int16_t plane, int16_t x, int16_t y,
                      int16_t goal_x, int16_t goal_y, int *steps)
{
    int count = 0;
    int dir = best_direction(world, state, plane, x, y, goal_x, goal_y);
    if (dir >= 0) {
        int nx = x + dx8[dir];
        int ny = y + dy8[dir];
        while (dir >= 0 && count < 0x40) {
            dir = best_direction(world, state, plane, (int16_t)nx,
                                 (int16_t)ny, goal_x, goal_y);
            if (dir >= 0) {
                nx += dx8[dir];
                ny += dy8[dir];
            }
            ++count;
        }
    }
    *steps = count;
    return dir >= 0 ? -1 : dir;
}

static int random_best_direction(const SimGameWorld *world,
                                 const SimMoveContext *context,
                                 int16_t plane, int16_t x, int16_t y,
                                 int16_t goal_x, int16_t goal_y,
                                 SimYellowState *state,
                                 SimYellowTrace *trace)
{
    SimRandDirBias bias;
    int result;
    bias.rot = state->rotation;
    bias.direction = state->preferred_direction;
    result = sim_get_my_rand_dirs(&world->tiles, context, plane,
                                  (SimGridPos){x, y},
                                  (SimGridPos){goal_x, goal_y},
                                  &bias, &trace->movement);
    state->rotation = bias.rot;
    state->preferred_direction = bias.direction;
    return result;
}

static int path_direction(const SimGameWorld *world, SimYellowState *state,
                          int16_t plane, int16_t x, int16_t y,
                          int16_t goal_x, int16_t goal_y,
                          SimYellowTrace *trace)
{
    SimMoveContext context;
    int direction;
    int steps;
    context.mode = state->movement_mode;
    context.from_plane = state->target_plane;
    context.from.x = state->target_x;
    context.from.y = state->target_y;
    context.previous.x = state->previous_x;
    context.previous.y = state->previous_y;
    if (state->path_delay < 0) {
        direction = best_direction(world, state, plane, x, y, goal_x, goal_y);
        if (direction == -2 && state->path_delay == -2) {
            state->preferred_direction = (int16_t)(sim_get_dir(x, y,
                                                   goal_x, goal_y) - 1);
            state->path_delay = 0x10;
            state->rotation = 0;
            return random_best_direction(world, &context, plane, x, y,
                                         goal_x, goal_y, state, trace);
        }
        return direction;
    }
    direction = walk_steps(world, state, plane, x, y, goal_x, goal_y, &steps);
    if (direction == -2) {
        direction = random_best_direction(world, &context, plane, x, y,
                                          goal_x, goal_y, state, trace);
    } else {
        state->path_delay = -1;
        direction = best_direction(world, state, plane, x, y, goal_x, goal_y);
    }
    --state->path_delay;
    return direction;
}

static int yellow_direction(const SimGameWorld *world, SimYellowState *state,
                            int16_t plane, int16_t x, int16_t y,
                            int16_t goal_plane, int16_t goal_x, int16_t goal_y,
                            SimYellowTrace *trace)
{
    int16_t local_goal_x = goal_x;
    int16_t local_goal_y = goal_y;
    if (plane <= 1) {
        if (goal_plane == 2) {
            local_goal_x = state->landmark_02AC.x;
            local_goal_y = state->landmark_02AC.y;
        } else if (goal_plane > 2) {
            local_goal_x = state->landmark_02B0.x;
            local_goal_y = state->landmark_02B0.y;
        }
    } else if (goal_plane <= 1 || goal_plane != plane) {
        const SimGridPos entrance = plane == 2 ? state->landmark_02A4
                                               : state->landmark_02A8;
        local_goal_x = entrance.x;
        local_goal_y = entrance.y;
    }
    return path_direction(world, state, plane, x, y,
                          local_goal_x, local_goal_y, trace);
}

static int at_surface_hole(const SimGameWorld *world, int16_t x, int16_t y)
{
    const int tile = get_map(world, 1, x, y);
    if (tile < 0) return 0;
    if (!world->tiles.terrain_set) return tile == 0x50;
    return tile >= 0x80 && tile <= 0x8f;
}

static SimYellowStatus finish(SimYellowTrace *trace, int16_t result,
                              SimYellowMissingService missing)
{
    trace->result = result;
    trace->missing_service = (int16_t)missing;
    if (trace->overflow) return SIM_YELLOW_TRACE_OVERFLOW;
    return missing == SIM_YELLOW_MISSING_NONE ? SIM_YELLOW_OK
                                               : SIM_YELLOW_UNSUPPORTED_GAMEPLAY;
}

SimYellowStatus sim_do_ant_move_y(SimGameWorld *world, SimRng *rng,
                                  SimNestRuntime *nest_runtime,
                                  SimYellowState *state,
                                  SimYellowTrace *trace)
{
    int16_t result = 0;
    int16_t direction, x, y, target_x = 0, target_y = 0;
    int16_t target_type = 0, target_mode = 0, target_direction = 0;
    int16_t plane, type;
    int target_valid = 0;
    int32_t distance_x, distance_y;
    SimYellowStatus status;
    SimNestStatus nest_status;
    SimYellowMissingService missing = SIM_YELLOW_MISSING_NONE;

    if (world == NULL || rng == NULL || nest_runtime == NULL ||
        state == NULL || trace == NULL)
        return SIM_YELLOW_INVALID_ARGUMENT;
    memset(trace, 0, sizeof(*trace));
    if (state->move_enabled == 0) return SIM_YELLOW_OK;

    plane = world->current_ant_plane;
    x = world->me_x;
    y = world->me_y;
    type = world->me_type;

    if (state->movement_mode >= 3) {
        target_valid = get_ant_index(world, state->target_list,
                                     state->target_index, &target_x, &target_y,
                                     &target_type, &target_mode,
                                     &target_direction);
        if (!target_valid ||
            (((uint16_t)(state->caste_mask ^ target_type) & 0x00f0u) != 0)) {
            result = -2;
            goto done;
        }
        if (plane == state->target_list) {
            distance_x = (int32_t)x - target_x;
            if (distance_x < 0) distance_x = -distance_x;
            distance_y = (int32_t)y - target_y;
            if (distance_y < 0) distance_y = -distance_y;
            if (distance_x <= 1 && distance_y <= 1) {
                direction = (int16_t)(sim_get_dir(x, y, target_x, target_y) - 1);
                if (direction >= 0) world->me_direction = direction;
                (void)emit(trace, SIM_YELLOW_EVENT_EDIT_DRAW, 0, 0, 0, 0, 0, 0, 0);
                goto moved;
            }
        }
        state->target_x = target_x;
        state->target_y = target_y;
    }

    if (state->movement_mode == 1 && state->target_plane == plane) {
        const int get_dir = sim_get_dir(x, y, state->target_x, state->target_y);
        const int index = get_dir == 0 ? -1 : get_dir - 1;
        x = (int16_t)(x + (index < 0 ? 0 : dx8[index]));
        y = (int16_t)(y + (index < 0 ? 0 : dy8[index]));
        if (x < 0 || x > 0x7f) x = world->me_x;
        if (y < 0 || y > 0x3f) y = world->me_y;
        if (state->target_x == x && state->target_y == y) {
            missing = SIM_YELLOW_MISSING_TRY_DROP_OR_LIFT;
            result = -2;
            goto done;
        }
    }

    direction = (int16_t)yellow_direction(world, state, plane,
        world->me_x, world->me_y, state->target_plane,
        state->target_x, state->target_y, trace);
    if (direction < 0) {
        result = direction;
        goto done;
    }

    x = (int16_t)(world->me_x + dx8[direction]);
    y = (int16_t)(world->me_y + dy8[direction]);
    state->previous_x = world->me_x;
    state->previous_y = world->me_y;
    status = move_my_life(world, rng, nest_runtime, trace,
                          plane, x, y, type, direction);
    if (status != SIM_YELLOW_OK) return status;
    state->movement_count = (int16_t)(state->movement_count + 1);

    if (plane == 1) {
        if (state->carried_food > 0 && (type == 0x18 || type == 0x38)) {
            missing = SIM_YELLOW_MISSING_POPULATION_EFFECT;
            goto done;
        }
        if (state->alarm_drop_state != 0) {
            missing = SIM_YELLOW_MISSING_ALARM_EFFECT;
            goto done;
        }
    } else {
        /* The source calls FixExitMapB/R after MoveMyLife has advanced the
         * current ant globals, so the destination tile is recomputed. */
        fix_exit_map(world, plane, world->me_x, world->me_y);
    }

    if ((uint16_t)state->movement_count & 1u) {
        if (type == 0x40 && state->food_motion_gate == 0 &&
            state->food_stock > 0 && state->food_stock_mode == 0)
            --state->food_stock;
        sim_set_my_health(world, (int16_t)(world->me_health - 1));
    }

    if (plane == 1) {
        if (!at_surface_hole(world, state->previous_x, state->previous_y))
            goto done;
        if (state->target_plane > 1 ||
            (state->target_plane == plane && state->target_x == world->me_x &&
             state->target_y == world->me_y)) {
            (void)emit(trace, SIM_YELLOW_EVENT_EDIT_DRAW, 0, 0, 0, 0, 0, 0, 0);
            if (state->nest_tick_count > 2) {
                return SIM_YELLOW_INVALID_ARGUMENT;
            }
            {
                SimNestRequest request;
                request.tick_values[0] = state->nest_ticks[0];
                request.tick_values[1] = state->nest_ticks[1];
                request.tick_count = state->nest_tick_count;
                nest_status = sim_enter_nest(world, rng, nest_runtime,
                                             &request, &trace->nest);
                if (nest_status != SIM_NEST_OK)
                    return SIM_YELLOW_UNSUPPORTED_GAMEPLAY;
            }
            if (state->target_plane != plane || state->target_x != x ||
                state->target_y != y || world->current_ant_plane == state->map_plane)
                goto done;
            if (state->target_window_open == 0)
                (void)emit(trace, SIM_YELLOW_EVENT_ANIMATION, 0, 0, 0, 0, 0, 0, 0);
            goto moved;
        }
        goto done;
    }

    if (world->me_y == 0) {
        SimExitNestContext exit_context;
        SimExitNestStatus exit_status;
        const int16_t old_plane = world->current_ant_plane;
        (void)emit(trace, SIM_YELLOW_EVENT_EDIT_DRAW, 0, 0, 0, 0, 0, 0, 0);
        exit_context.target_plane = state->target_plane;
        exit_context.target.x = state->target_x;
        exit_context.target.y = state->target_y;
        exit_context.previous.x = state->previous_x;
        exit_context.previous.y = state->previous_y;
        exit_context.movement_mode = state->movement_mode;
        exit_context.rotation = state->rotation;
        exit_context.preferred_direction = state->preferred_direction;
        exit_context.map_plane = state->map_plane;
        exit_context.tick_values[0] = state->nest_ticks[0];
        exit_context.tick_values[1] = state->nest_ticks[1];
        exit_context.tick_count = state->nest_tick_count;
        nest_runtime->entrance_b_nest_x = state->landmark_02A4.x;
        nest_runtime->entrance_b_nest_y = state->landmark_02A4.y;
        nest_runtime->entrance_r_nest_x = state->landmark_02A8.x;
        nest_runtime->entrance_r_nest_y = state->landmark_02A8.y;
        nest_runtime->entrance_b_surface_x = state->landmark_02AC.x;
        nest_runtime->entrance_b_surface_y = state->landmark_02AC.y;
        nest_runtime->entrance_r_surface_x = state->landmark_02B0.x;
        nest_runtime->entrance_r_surface_y = state->landmark_02B0.y;
        exit_status = sim_exit_nest(world, rng, nest_runtime, &exit_context,
                                    &trace->movement, &trace->nest);
        if (exit_status != SIM_EXIT_NEST_OK) {
            missing = SIM_YELLOW_MISSING_EXIT_NEST;
            return finish(trace, SIM_YELLOW_UNSUPPORTED_GAMEPLAY, missing);
        }
        state->rotation = exit_context.rotation;
        state->preferred_direction = exit_context.preferred_direction;
        state->landmark_02A4.x = nest_runtime->entrance_b_nest_x;
        state->landmark_02A4.y = nest_runtime->entrance_b_nest_y;
        state->landmark_02A8.x = nest_runtime->entrance_r_nest_x;
        state->landmark_02A8.y = nest_runtime->entrance_r_nest_y;
        state->landmark_02AC.x = nest_runtime->entrance_b_surface_x;
        state->landmark_02AC.y = nest_runtime->entrance_b_surface_y;
        state->landmark_02B0.x = nest_runtime->entrance_r_surface_x;
        state->landmark_02B0.y = nest_runtime->entrance_r_surface_y;
        if (state->target_plane != old_plane || state->target_x != x ||
            state->target_y != y || world->current_ant_plane == state->map_plane)
            goto done;
        if (state->sound_disabled == 0)
            (void)emit(trace, SIM_YELLOW_EVENT_ANIMATION, 0, 0, 0, 0, 0, 0, 0);
        goto moved;
    }
    if (get_map(world, plane, state->target_x, state->target_y) != 0x14)
        goto done;
    if (type == 0x60 || state->target_x != world->me_x ||
        state->target_y != world->me_y)
        goto done;

    status = clear_my_life(world, rng, nest_runtime, trace, plane,
                           world->me_x, world->me_y, type,
                           world->me_direction);
    if (status != SIM_YELLOW_OK) return status;
    world->current_ant_plane = plane == 2 ? 3 : 2;
    status = set_my_life(world, rng, nest_runtime, trace,
                         world->current_ant_plane, world->me_x, world->me_y,
                         type, world->me_direction, 0xff);
    if (status != SIM_YELLOW_OK) return status;
    (void)emit(trace, SIM_YELLOW_EVENT_SOUND, 3, 1, 0, 0x7e, 0, 0, 0);
    (void)emit(trace, SIM_YELLOW_EVENT_ANIMATION, 0, 0, 0, 0, 0, 0, 0);
    if (state->message_resource != 0 && world->current_ant_plane == 3)
        (void)emit(trace, SIM_YELLOW_EVENT_MESSAGE, 3,
                   state->message_resource, 360, 0, 0, 0, 0);
    goto moved;

moved:
    result = -1;
done:
    if (state->target_window_open != 0)
        (void)emit(trace, SIM_YELLOW_EVENT_ANIMATION, 0, 0, 0, 0, 0, 0, 0);
    if (result == 0 && state->target_plane == world->current_ant_plane &&
        state->target_x == world->me_x && state->target_y == world->me_y &&
        state->movement_mode == 0)
        result = -1;
    if (result == 0) return finish(trace, result, missing);
    if (result == -2) {
        (void)emit(trace, SIM_YELLOW_EVENT_SOUND, 3, 1, 0, 0x7e, 0, 0, 0);
        (void)emit(trace, SIM_YELLOW_EVENT_ANIMATION, 0, 0, 0, 0, 0, 0, 0);
    } else if (state->movement_mode == 3) {
        missing = SIM_YELLOW_MISSING_TARGET_ANT_REMOVAL;
    } else if (state->movement_mode == 4) {
        direction = (int16_t)(sim_get_dir(target_x, target_y,
                                         world->me_x, world->me_y) - 1);
        if (direction >= 0 && (target_type & 0x70) != 0x60) {
            target_type = (int16_t)((target_type & 0x00f8) | direction);
            set_ant_index(world, state->target_list, state->target_index,
                          target_x, target_y, target_type, target_mode,
                          target_direction);
            status = set_life(world, rng, nest_runtime, trace,
                              state->target_list, target_x, target_y,
                              (uint8_t)target_type);
            if (status != SIM_YELLOW_OK) return status;
            (void)emit(trace, SIM_YELLOW_EVENT_EDIT_DRAW, 0, 0, 0, 0, 0, 0, 0);
        }
        /* EatMyFood(1): the source clears the food timer, posts its message,
         * and restores player health. Those are typed host intents plus state. */
        world->source_counter_0472 = 0;
        sim_set_my_health(world, 100);
        (void)emit(trace, SIM_YELLOW_EVENT_MESSAGE, 3,
                   state->message_resource, 120, 0, 0, 0, 0);
    }
    (void)emit(trace, SIM_YELLOW_EVENT_MAP_INVALIDATE, 3,
               world->current_ant_plane, world->me_x, world->me_y, 0, 0, 0);
    return finish(trace, result, missing);
}
