#include "ants.h"

static bool valid_surface_pos(int16_t x, int16_t y)
{
    return x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT;
}

static bool valid_nest_pos(int16_t x, int16_t y)
{
    return x >= 0 && x < SIM_NEST_WIDTH && y >= 0 && y < SIM_NEST_HEIGHT;
}

bool sim_ant_add_a(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state)
{
    SimAntList *list;
    int16_t index;

    if (world == 0 || !valid_surface_pos(x, y))
        return false;
    list = &world->ants_a;
    if (list->count < 0 || list->count >= SIM_A_ANT_CAPACITY)
        return false;
    index = list->count;
    list->x[index] = (uint8_t)x;
    list->y[index] = (uint8_t)y;
    list->type[index] = type;
    list->mode[index] = mode;
    list->state[index] = state;
    world->life_a[x][y] = type;
    list->count++;
    return true;
}

bool sim_ant_add_b(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state)
{
    SimSmallAntList *list;
    int16_t index;

    if (world == 0 || !valid_nest_pos(x, y))
        return false;
    list = &world->ants_b;
    if (list->count < 0 || list->count >= SIM_B_ANT_CAPACITY)
        return false;
    index = list->count;
    list->x[index] = (uint8_t)x;
    list->y[index] = (uint8_t)y;
    list->type[index] = type;
    list->mode[index] = mode;
    list->state[index] = state;
    world->life_b[x][y] = type;
    list->count++;
    return true;
}

bool sim_ant_add_r(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state)
{
    SimSmallAntList *list;
    int16_t index;

    if (world == 0 || !valid_nest_pos(x, y))
        return false;
    list = &world->ants_r;
    if (list->count < 0 || list->count >= SIM_R_ANT_CAPACITY)
        return false;
    index = list->count;
    list->x[index] = (uint8_t)x;
    list->y[index] = (uint8_t)y;
    list->type[index] = type;
    list->mode[index] = mode;
    list->state[index] = state;
    world->life_r[x][y] = type;
    list->count++;
    return true;
}

void sim_ants_reset_lists(SimGameWorld *world)
{
    if (world == 0)
        return;
    world->ants_a.count = 0;
    world->ants_b.count = 0;
    world->ants_r.count = 0;
}

void sim_ants_clear_b(SimGameWorld *world)
{
    if (world != 0)
        world->ants_b.count = 0;
}

void sim_ants_clear_r(SimGameWorld *world)
{
    if (world != 0)
        world->ants_r.count = 0;
}

void sim_ants_rebuild_a(SimGameWorld *world)
{
    int16_t x, y;
    int16_t count = 0;

    if (world == 0)
        return;
    world->ants_a.count = 0;
    for (x = 0; x < SIM_WORLD_WIDTH; ++x) {
        for (y = 0; y < SIM_WORLD_HEIGHT; ++y) {
            uint8_t type = world->life_a[x][y];
            if (type == 0 || type == 0xff || type == 0xfe)
                continue;
            world->ants_a.x[count] = (uint8_t)x;
            world->ants_a.y[count] = (uint8_t)y;
            world->ants_a.mode[count] = 2;
            world->ants_a.type[count] = type;
            world->ants_a.state[count] = 0;
            if (count < 997)
                ++count;
        }
    }
    world->ants_a.count = count;
}

int16_t sim_ants_count(const SimGameWorld *world)
{
    if (world == 0)
        return 0;
    return (int16_t)(world->ants_a.count + world->ants_b.count +
                     world->ants_r.count);
}

static bool valid_life_pos(int16_t plane, int16_t x, int16_t y)
{
    if (plane <= 1)
        return valid_surface_pos(x, y);
    return valid_nest_pos(x, y);
}

static void set_life(SimGameWorld *world, int16_t plane, int16_t x, int16_t y,
                     uint8_t value)
{
    if (!valid_life_pos(plane, x, y))
        return;
    if (plane == 0 || plane == 1)
        world->life_a[x][y] = value;
    else if (plane == 2)
        world->life_b[x][y] = value;
    else if (plane == 3)
        world->life_r[x][y] = value;
}

bool sim_set_my_life(SimGameWorld *world, int16_t plane, int16_t x, int16_t y,
                     int16_t type, int16_t direction, int16_t value)
{
    static const int8_t dx8[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
    static const int8_t dy8[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
    int16_t tail_direction;

    if (world == 0 || !valid_life_pos(plane, x, y))
        return false;
    set_life(world, plane, x, y, (uint8_t)value);
    if (type == 0x60) {
        tail_direction = (int16_t)((uint16_t)direction ^ 4u);
        if (tail_direction >= 0 && tail_direction < 8) {
            int16_t tail_x = (int16_t)(x + dx8[tail_direction]);
            int16_t tail_y = (int16_t)(y + dy8[tail_direction]);
            uint8_t tail_value = value == 0xff ? 0xfe : (uint8_t)value;
            set_life(world, plane, tail_x, tail_y, tail_value);
        }
    }
    if (value != 0) {
        world->me_x = x;
        world->me_y = y;
        world->me_direction = direction;
        world->me_type = type;
        world->current_ant_plane = plane;
    }
    return true;
}

void sim_set_my_health(SimGameWorld *world, int16_t health)
{
    int32_t next;

    if (world == 0)
        return;
    next = world->health_force_full ? 100 : health;
    if (next > 0)
        world->health_death = 0;
    if (next > 100)
        next = 100;
    else if (next < 0)
        next = 0;
    world->me_health = (int16_t)next;
    world->health_warning =
        (world->me_health > world->health_warning_threshold && world->me_health >= 10)
            ? 0 : 1;
}
