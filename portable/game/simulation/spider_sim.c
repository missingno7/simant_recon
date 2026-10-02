#include "spider_sim.h"

#include "movement.h"

#include <stddef.h>

static const int8_t turn_tab[8][8] = {
    {0, 1, 1, 1, 7, 7, 7, 7}, {0, 1, 2, 2, 2, 2, 0, 0},
    {1, 1, 2, 3, 3, 3, 3, 1}, {2, 2, 2, 3, 4, 4, 4, 4},
    {3, 3, 3, 3, 4, 5, 5, 5}, {6, 6, 4, 4, 4, 5, 6, 6},
    {7, 7, 7, 5, 5, 5, 6, 7}, {0, 0, 0, 0, 6, 6, 6, 7}
};
static const int8_t move_dx[8] = {0, 3, 4, 3, 0, -3, -4, -3};
static const int8_t move_dy[8] = {-4, -3, 0, 3, 4, 3, 0, -3};
static const int8_t scan_dx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
static const int8_t scan_dy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};
static const int8_t target_dx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
static const int8_t target_dy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};

static int16_t wrap16(int value)
{
    uint16_t bits = (uint16_t)value;
    return bits < 0x8000u ? (int16_t)bits : (int16_t)(bits - 0x10000u);
}

static int16_t sr1(SimRng *rng, uint16_t limit)
{
    uint16_t value = 0;
    (void)sim_rng_s1(rng, limit, &value);
    return (int16_t)value;
}

static int push(SimSpiderTickEffects *effects, SimSpiderEventKind kind,
                int a, int b, int c, int d, int e)
{
    SimSpiderEvent *event;
    if (effects->count >= SIM_SPIDER_EVENT_CAPACITY) {
        effects->overflow = 1;
        return 0;
    }
    event = &effects->events[effects->count++];
    event->kind = (uint16_t)kind;
    event->values[0] = (int16_t)a;
    event->values[1] = (int16_t)b;
    event->values[2] = (int16_t)c;
    event->values[3] = (int16_t)d;
    event->values[4] = (int16_t)e;
    return 1;
}

static int valid_a(int x, int y)
{
    return x >= 0 && x <= 127 && y >= 0 && y <= 63;
}

static int distance_squared(int x1, int y1, int x2, int y2)
{
    int dx = x2 - x1;
    int dy = y2 - y1;
    return dx * dx + dy * dy;
}

static int s_get_distance(int x1, int y1, int x2, int y2)
{
    int dx = y2 - y1;
    int dy = x2 - x1;
    if (dx < 0) dx = -dx;
    if (dy < 0) dy = -dy;
    return dx + dy;
}

static int find_a_ant(const SimGameWorld *world, int x, int y, int life)
{
    int i;
    int count = world->ants_a.count;
    if (count < 0 || count > SIM_A_ANT_CAPACITY)
        return -1;
    for (i = count - 1; i >= 0; --i) {
        if (world->ants_a.x[i] == (uint8_t)x &&
            world->ants_a.y[i] == (uint8_t)y &&
            world->ants_a.type[i] == (uint8_t)life)
            return i;
    }
    return -1;
}

static int found_ant(const SimGameWorld *world, const SimSpiderState *spider,
                     const SimSpiderTickState *tick)
{
    int x = spider->x16 >> 4;
    int y = spider->y16 >> 4;
    int i;

    if (spider->aux_mode == 7) {
        for (i = world->ants_a.count - 1; i >= 0; --i) {
            if (world->ants_a.type[i] != 0 &&
                distance_squared(x, y, world->ants_a.x[i], world->ants_a.y[i]) <= 800)
                return i;
        }
        if (tick->player_control == 0 && world->current_ant_plane == 1 &&
            distance_squared(x, y, world->me_x, world->me_y) <= 800)
            return -1;
        return -2;
    }

    for (i = 0; i < 20; ++i) {
        int life;
        y += scan_dy[(uint16_t)spider->direction & 7u];
        x += scan_dx[(uint16_t)spider->direction & 7u];
        if (!valid_a(x, y) || distance_squared(spider->x16 >> 4,
                                                spider->y16 >> 4, x, y) > 400)
            return -2;
        life = world->life_a[x][y];
        if (life != 0) {
            if (life == 0xff || life == 0xfe)
                return -1;
            i = find_a_ant(world, x, y, life);
            if (i >= 0)
                return i;
        }
    }
    return -2;
}

static int scan_for_ants(const SimGameWorld *world, const SimSpiderState *spider)
{
    int x = spider->x16 >> 4;
    int y = spider->y16 >> 4;
    int i, j, count = 0;
    for (i = -1; i < 3; ++i)
        for (j = -1; j < 3; ++j) {
            int tx = x + i;
            int ty = y + j;
            if (valid_a(tx, ty) && world->life_a[tx][ty] != 0)
                ++count;
        }
    return count;
}

static void dead_ant_here(SimSpiderState *spider, SimGameWorld *world,
                          SimRng *rng, int x, int y, int type)
{
    uint8_t old_tile;
    int old_x, old_y;

    ++spider->corpse_index;
    if (spider->corpse_index >= 100)
        spider->corpse_index = 0;
    old_x = spider->corpse_x[spider->corpse_index];
    old_y = spider->corpse_y[spider->corpse_index];
    old_tile = world->tiles.surface[old_x][old_y];
    if (world->tiles.terrain_set == 0) {
        if (old_tile >= 0x10 && old_tile < 0x18)
            world->tiles.surface[old_x][old_y] = (uint8_t)sim_rng_s16(rng);
        spider->corpse_x[spider->corpse_index] = (uint8_t)x;
        spider->corpse_y[spider->corpse_index] = (uint8_t)y;
        if (world->tiles.surface[x][y] < 0x18)
            world->tiles.surface[x][y] = (uint8_t)(sim_rng_s4(rng) +
                (type != 0 ? 0x14 : 0x10));
    } else {
        if (old_tile >= 8 && old_tile < 0x18)
            world->tiles.surface[old_x][old_y] = (uint8_t)((old_tile - 8) >> 2);
        spider->corpse_x[spider->corpse_index] = (uint8_t)x;
        spider->corpse_y[spider->corpse_index] = (uint8_t)y;
        old_tile = world->tiles.surface[x][y];
        if (old_tile < 4) {
            int draw = sr1(rng, 2);
            world->tiles.surface[x][y] = (uint8_t)(type != 0
                ? draw + old_tile * 4 + 0x0a : draw + (old_tile + 2) * 4);
        }
    }
    world->life_a[x][y] = 0;
}

static int set_turn(SimSpiderState *spider, int choice)
{
    if (spider->direction < 0 || spider->direction >= 8 || choice < 0 || choice >= 8)
        return 0;
    spider->direction = turn_tab[spider->direction][choice];
    return 1;
}

static void emit_refresh(const SimSpiderTickState *tick,
                         SimSpiderTickEffects *effects)
{
    (void)tick;
    (void)push(effects, SIM_SPIDER_EVENT_PLAYER_REFRESH, 0, 0, 0, 0, 0);
}

static void player_position_from_spider(SimGameWorld *world,
                                        SimSpiderState *spider,
                                        const SimSpiderTickState *tick,
                                        SimSpiderTickEffects *effects)
{
    world->me_x = (int16_t)(spider->x16 >> 4);
    world->me_y = (int16_t)(spider->y16 >> 4);
    if (tick->options[0])
        emit_refresh(tick, effects);
}

static SimSpiderTickStatus finish(SimSpiderTickEffects *effects)
{
    return effects->overflow ? SIM_SPIDER_TICK_EVENT_OVERFLOW : SIM_SPIDER_TICK_OK;
}

SimSpiderTickStatus sim_spider_tick(SimGameWorld *world, SimRng *rng,
                                    SimSpiderState *spider,
                                    SimSpiderTickState *tick,
                                    const SimSpiderTickServices *services,
                                    SimSpiderTickEffects *effects)
{
    int x, y, d, r;

    if (world == NULL || rng == NULL || spider == NULL || tick == NULL ||
        effects == NULL)
        return SIM_SPIDER_TICK_INVALID_ARGUMENT;
    effects->count = 0;
    effects->overflow = 0;
    spider->cycle2 = (int16_t)((spider->cycle2 + 1) & 0x3ff);
    x = spider->x16 >> 4;
    y = spider->y16 >> 4;

    if (tick->player_control == 1 && spider->mode != 2 && spider->mode != 3) {
        if (spider->aux_mode == 7) {
            spider->target = (int16_t)found_ant(world, spider, tick);
            if (spider->target != -2) {
                spider->mode = 2;
                spider->target_life = spider->target >= 0
                    ? world->ants_a.type[spider->target] : 0xff;
                return finish(effects);
            }
        } else if (spider->aux_mode == 8) {
            SimSpiderLaser laser;
            (void)sim_spider_scan(spider, world, rng, &laser);
            if (laser.fired)
                (void)push(effects, SIM_SPIDER_EVENT_LASER, laser.from_x16,
                           laser.from_y16, laser.to_x16, laser.to_y16, 0);
        }
        d = distance_squared(world->me_x, world->me_y,
                             spider->user_x, spider->user_y);
        if (d < 1) {
            spider->cycle = 2;
            return finish(effects);
        }
        if (services == NULL || services->route_direction == NULL)
            return SIM_SPIDER_TICK_UNSUPPORTED;
        r = services->route_direction(services->userdata, world, 1,
                                      world->me_x, world->me_y,
                                      spider->user_x, spider->user_y);
        (void)push(effects, SIM_SPIDER_EVENT_PATH_QUERY, 1, world->me_x,
                   world->me_y, spider->user_x, spider->user_y);
        if (r == -1)
            return finish(effects);
        if (r == -2) {
            r = sim_get_dir(world->me_x, world->me_y,
                            spider->user_x, spider->user_y) - 1;
            if (r < 0)
                return finish(effects);
        }
        if (!set_turn(spider, r))
            return SIM_SPIDER_TICK_UNSUPPORTED;
        if (tick->route_mode && d > 2) {
            spider->x16 = wrap16(spider->x16 + 5 * move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 + 5 * move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle + 2) & 0x3ff);
        } else {
            spider->x16 = wrap16(spider->x16 + move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 + move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle + 1) & 0x3ff);
        }
        player_position_from_spider(world, spider, tick, effects);
        return finish(effects);
    }

    if (!spider->target_mode) {
        if (world->scenario == 0)
            return finish(effects);
        if (sr1(rng, 300) != 0)
            return finish(effects);
        spider->x16 = (int16_t)(sr1(rng, 0x400) + 0x200);
        spider->mode = spider->target_mode = 1;
        spider->state_flag = 0;
        if (sr1(rng, 2)) {
            spider->y16 = 1;
            spider->direction = 4;
        } else {
            spider->y16 = 0x3ff;
            spider->direction = 0;
        }
        return finish(effects);
    }

    if ((spider->cycle2 & 3) == 0 && spider->mode < 5) {
        r = scan_for_ants(world, spider);
        if (r > 8) {
            spider->mode = 5;
            tick->death_count = 500;
            spider->cycle = 0;
            if (tick->player_control != 1) {
                (void)push(effects, SIM_SPIDER_EVENT_DIALOG, 0, 0x273e, 0, 0, 0);
                if (spider->revenge < 5)
                    ++spider->revenge;
                if (spider->revenge < 3)
                    return finish(effects);
                spider->aux_mode = spider->revenge >= 5 ? 8 : 7;
                if (spider->revenge >= 6 && sim_rng_s2(rng) == 0) {
                    spider->revenge = 0;
                    spider->aux_mode = 0;
                }
                return finish(effects);
            }
            tick->player_control = 0;
            (void)push(effects, SIM_SPIDER_EVENT_YELLOW_DEATH, 3, 0, 0, 0, 0);
            return finish(effects);
        }
        if (r > 4)
            spider->mode = 4;
    }
    if (spider->mode < 4 && spider->aux_mode == 8) {
        SimSpiderLaser laser;
        (void)sim_spider_scan(spider, world, rng, &laser);
        if (laser.fired)
            (void)push(effects, SIM_SPIDER_EVENT_LASER, laser.from_x16,
                       laser.from_y16, laser.to_x16, laser.to_y16, 0);
    }

    switch (spider->mode) {
    case 0:
        spider->cycle = 2;
        if (sr1(rng, 150) == 0)
            spider->mode = 1;
        spider->target = (int16_t)found_ant(world, spider, tick);
        if (spider->target != -2) {
            spider->mode = 2;
            spider->target_life = spider->target >= 0
                ? world->ants_a.type[spider->target] : 0xff;
            return finish(effects);
        }
        if (sr1(rng, 30) == 0 && !set_turn(spider, sr1(rng, 8)))
            return SIM_SPIDER_TICK_UNSUPPORTED;
        if (spider->aux_mode == 8) {
            SimSpiderLaser laser;
            (void)sim_spider_scan(spider, world, rng, &laser);
            if (laser.fired)
                (void)push(effects, SIM_SPIDER_EVENT_LASER, laser.from_x16,
                           laser.from_y16, laser.to_x16, laser.to_y16, 0);
        }
        break;

    case 1:
        if (spider->state_flag) {
            spider->x16 = wrap16(spider->x16 - move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 - move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle - 1) & 0x3ff);
        } else {
            spider->x16 = wrap16(spider->x16 + move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 + move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle + 1) & 0x3ff);
        }
        if (sr1(rng, 20) == 0 && !set_turn(spider, sr1(rng, 8)))
            return SIM_SPIDER_TICK_UNSUPPORTED;
        spider->target = (int16_t)found_ant(world, spider, tick);
        if (spider->target != -2) {
            spider->mode = 2;
            spider->target_life = spider->target >= 0
                ? world->ants_a.type[spider->target] : 0xff;
            return finish(effects);
        }
        if (sr1(rng, 50) == 0) {
            spider->mode = 0;
            spider->cycle = 2;
        }
        break;

    case 2:
        if (spider->target >= 0) {
            if (((uint8_t)spider->target_life ^
                 world->ants_a.type[spider->target]) & 0xf0) {
                spider->mode = 0;
                spider->target = -2;
                if (tick->player_control != 1)
                    return finish(effects);
                y = spider->y16 >> 4;
                x = spider->x16 >> 4;
                spider->user_y = (int16_t)y;
                spider->user_x = (int16_t)x;
                world->me_x = (int16_t)x;
                world->me_y = (int16_t)y;
                if (spider->aux_mode == 6)
                    spider->aux_mode = 0;
                if (tick->options[0])
                    emit_refresh(tick, effects);
                return finish(effects);
            }
        } else if (world->current_ant_plane > 1) {
            spider->mode = 0;
            spider->target = -2;
            return finish(effects);
        }
        if (spider->target < 0)
            d = s_get_distance(x, y, world->me_x, world->me_y);
        else
            d = s_get_distance(x, y, world->ants_a.x[spider->target],
                               world->ants_a.y[spider->target]);
        if (d > 64 && tick->player_control != 1) {
            spider->mode = 0;
            spider->target = -2;
            return finish(effects);
        }
        if (d < 2) {
            spider->mode = 3;
            spider->x16 = (int16_t)((spider->x16 & 0xfff0) + 8);
            spider->y16 = (int16_t)((spider->y16 & 0xfff0) + 8);
            goto eat;
        }
        if (spider->target < 0)
            d = sim_get_dir((int16_t)x, (int16_t)y, world->me_x, world->me_y);
        else
            d = sim_get_dir((int16_t)x, (int16_t)y,
                            world->ants_a.x[spider->target],
                            world->ants_a.y[spider->target]);
        if (!set_turn(spider, d - 1))
            return SIM_SPIDER_TICK_UNSUPPORTED;
        (void)push(effects, SIM_SPIDER_EVENT_SOUND, 0x2f, 0,
                   spider->target < 0 ? 0x7e : -5, 0, 0);
        if (spider->state_flag) {
            spider->x16 = wrap16(spider->x16 - 5 * move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 - 5 * move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle - 2) & 0x3ff);
        } else {
            spider->x16 = wrap16(spider->x16 + 5 * move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 + 5 * move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle + 2) & 0x3ff);
        }
        if (tick->player_control == 1)
            player_position_from_spider(world, spider, tick, effects);
        break;

    case 3:
eat:
        if (tick->player_control == 1) {
            world->me_x = (int16_t)(spider->x16 >> 4);
            world->me_y = (int16_t)(spider->y16 >> 4);
            if (spider->aux_mode == 6)
                spider->aux_mode = 0;
            if (tick->options[0])
                emit_refresh(tick, effects);
        }
        if (spider->target != -2) {
            if (spider->target >= 0) {
                if (!(((uint8_t)spider->target_life ^
                       world->ants_a.type[spider->target]) & 0xf0)) {
                    if (spider->target_life & 0x80) {
                        ++tick->red_ants_eaten;
                        spider->corpse_base = 4;
                    } else {
                        ++tick->black_ants_eaten;
                        spider->corpse_base = 0;
                    }
                    world->life_a[world->ants_a.x[spider->target]]
                                 [world->ants_a.y[spider->target]] = 0;
                    world->ants_a.type[spider->target] = 0;
                } else {
                    spider->target = -2;
                    goto done;
                }
            } else {
                int mx = (target_dx[spider->direction] + x) & 0x7f;
                int my = (target_dy[spider->direction] + y) & 0x3f;
                (void)push(effects, SIM_SPIDER_EVENT_MOVE_PLAYER_LIFE,
                           world->current_ant_plane, mx, my, world->me_type,
                           world->me_direction);
                (void)push(effects, SIM_SPIDER_EVENT_YELLOW_DEATH, 1, 0, 0, 0, 0);
                spider->corpse_base = 0;
            }
            spider->target = -2;
            spider->eat_count = spider->aux_mode >= 7 ? 11 : 50;
        }
        d = (target_dx[spider->direction] + x) & 0x7f;
        r = (target_dy[spider->direction] + y) & 0x3f;
        if (!world->tiles.terrain_set && world->tiles.surface[d][r] < 0x18)
            world->tiles.surface[d][r] = (uint8_t)(sim_rng_s4(rng) +
                                                    spider->corpse_base + 0x10);
        if (spider->eat_count > 0) {
            --spider->eat_count;
            if (spider->eat_count % 10 == 0 && sim_rng_s2(rng))
                (void)push(effects, SIM_SPIDER_EVENT_SOUND, 0x2c,
                           (sim_rng_s256(rng) << 3) + 0x2777, -5, 0, 0);
            break;
        }
        if (--spider->burp_count == 0) {
            spider->burp_count = 10;
            if (tick->options[5] && !sim_rng_s2(rng))
                (void)push(effects, SIM_SPIDER_EVENT_SOUND, 10, 0, 10, 0, 0);
        }
        dead_ant_here(spider, world, rng, d, r, spider->corpse_base);
done:
        spider->mode = 0;
        if (tick->player_control == 1) {
            if (spider->aux_mode == 6)
                spider->aux_mode = 0;
            spider->user_x = (int16_t)x;
            spider->user_y = (int16_t)y;
        }
        break;

    case 4:
        if (!set_turn(spider, sr1(rng, 8)))
            return SIM_SPIDER_TICK_UNSUPPORTED;
        if (spider->state_flag) {
            spider->x16 = wrap16(spider->x16 - 5 * move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 - 5 * move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle - 2) & 0x3ff);
        } else {
            spider->x16 = wrap16(spider->x16 + 5 * move_dx[spider->direction]);
            spider->y16 = wrap16(spider->y16 + 5 * move_dy[spider->direction]);
            spider->cycle = (int16_t)((spider->cycle + 2) & 0x3ff);
        }
        if (sr1(rng, 50) == 0) {
            spider->mode = 0;
            spider->cycle = 2;
        }
        break;

    case 5:
        --tick->death_count;
        if (tick->death_count == 0) {
            spider->mode = spider->target_mode = 0;
            (void)push(effects, SIM_SPIDER_EVENT_DEATH_FRAME, x, y, 0, 0, 0);
            (void)push(effects, SIM_SPIDER_EVENT_DEATH_FRAME, x, y, 0, 0, 0);
            (void)push(effects, SIM_SPIDER_EVENT_DEATH_FRAME, x, y, 0, 0, 0);
            return finish(effects);
        }
        if (sr1(rng, 1000) < tick->death_count) {
            if (tick->death_count > 400)
                spider->cycle = (int16_t)(sr1(rng, 3) + 1);
            else
                spider->cycle = (int16_t)(sr1(rng, 2) + 2);
        }
        break;
    default:
        return SIM_SPIDER_TICK_UNSUPPORTED;
    }

    x = spider->x16 >> 4;
    y = spider->y16 >> 4;
    if (!valid_a(x, y)) {
        spider->target_mode = 0;
        if (tick->player_control == 1) {
            tick->player_control = 0;
            (void)push(effects, SIM_SPIDER_EVENT_YELLOW_DEATH, 4, 0, 0, 0, 0);
        }
    }
    if (world->tiles.terrain_set && valid_a(x, y) &&
        world->tiles.surface[x][y] > 0x90)
        spider->target_mode = 0;
    return finish(effects);
}
