#include "terrain.h"

#include <stddef.h>

/* RT5 and RT3 are the original typed terrain pattern data from d3D57.c. */
static const uint8_t rock5[150] = {
    0x00,0x5b,0x54,0x55,0x00,0x5b,0x5c,0x5c,0x56,0x00,0x5a,0x5c,0x5c,0x5e,0x55,
    0x59,0x5d,0x5c,0x5c,0x56,0x00,0x59,0x58,0x58,0x57,0x00,0x00,0x5b,0x54,0x55,
    0x00,0x5b,0x5c,0x5c,0x56,0x5b,0x5c,0x5c,0x5f,0x57,0x5a,0x5f,0x58,0x57,0x00,
    0x59,0x57,0x00,0x00,0x00,0x00,0x00,0x5b,0x54,0x55,0x5b,0x54,0x5c,0x5f,0x57,
    0x5a,0x5f,0x58,0x57,0x00,0x59,0x57,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x5b,0x54,0x54,0x54,0x55,0x59,0x5d,0x5c,0x5c,0x56,
    0x00,0x59,0x5d,0x5c,0x56,0x00,0x00,0x59,0x58,0x57,0x5b,0x54,0x54,0x54,0x55,
    0x59,0x5d,0x5c,0x5f,0x57,0x00,0x5a,0x5c,0x56,0x00,0x5b,0x5c,0x5f,0x57,0x00,
    0x59,0x58,0x57,0x00,0x00,0x00,0x00,0x5b,0x54,0x55,0x00,0x5b,0x5c,0x5f,0x57,
    0x5b,0x5c,0x5c,0x56,0x00,0x59,0x5d,0x5c,0x5e,0x55,0x00,0x59,0x58,0x58,0x57
};

static const uint8_t rock3[54] = {
    0x5b,0x54,0x55,0x5a,0x5c,0x56,0x59,0x58,0x57,0x5b,0x55,0x00,0x59,0x5e,0x55,
    0x00,0x59,0x57,0x5b,0x54,0x55,0x59,0x58,0x57,0x00,0x00,0x00,0x5b,0x55,0x00,
    0x59,0x57,0x00,0x00,0x00,0x00,0x5b,0x55,0x00,0x5a,0x56,0x00,0x59,0x57,0x00,
    0x5b,0x55,0x00,0x5a,0x5e,0x55,0x59,0x58,0x57
};

static const uint8_t plug_v[4][5] = {
    {0x6b,0x6c,0x6c,0x6c,0x6d},
    {0x71,0x78,0x64,0x78,0x72},
    {0x71,0x79,0x74,0x79,0x72},
    {0x6e,0x6f,0x6f,0x6f,0x70}
};

static const uint8_t plug_h[5][4] = {
    {0x6b,0x6c,0x6c,0x6d},
    {0x71,0x76,0x77,0x72},
    {0x71,0x64,0x64,0x72},
    {0x71,0x76,0x77,0x72},
    {0x6e,0x6f,0x6f,0x70}
};

static const uint8_t knob[5][5] = {
    {0x40,0x41,0x41,0x41,0x42},
    {0x43,0x4e,0x4e,0x4e,0x44},
    {0x43,0x4e,0x4c,0x4e,0x44},
    {0x43,0x4e,0x4e,0x4e,0x44},
    {0x46,0x47,0x47,0x47,0x49}
};

static const uint8_t penny[3][3] = {
    {0x28,0x29,0x2a}, {0x2b,0x2c,0x2d}, {0x2e,0x2f,0x30}
};

static const uint8_t clip[3][3] = {
    {0x00,0x31,0x32}, {0x33,0x34,0x35}, {0x36,0x37,0x00}
};

static const int8_t dx8[8] = {0,1,1,1,0,-1,-1,-1};
static const int8_t dy8[8] = {-1,-1,0,1,1,1,0,-1};
static const uint8_t lion_ring[8] = {1,2,4,7,6,5,3,0};
static const uint8_t sow_tiles[8] = {0x72,0x73,0x71,0x70,0x72,0x73,0x71,0x70};

static uint16_t rand1(SimRng *rng, uint16_t range)
{
    uint16_t value = 0;
    (void)sim_rng_s1(rng, range, &value);
    return value;
}

static void fill_map(SimGameWorld *world, int x1, int x2,
                     int y1, int y2, uint8_t tile)
{
    int x, y;
    for (x = x1; x <= x2; ++x)
        for (y = y1; y <= y2; ++y)
            world->tiles.surface[x][y] = tile;
}

static void tile_frame_1(SimGameWorld *world, int x1, int x2, int y1, int y2)
{
    fill_map(world, x1, x2, y1, y1, 0x54);
    fill_map(world, x1, x2, y2, y2, 0x51);
    fill_map(world, x1, x1, y1, y2, 0x5a);
    fill_map(world, x2, x2, y1, y2, 0x5b);
    world->tiles.surface[x1][y1] = 0x53;
    world->tiles.surface[x2][y1] = 0x55;
    world->tiles.surface[x1][y2] = 0x50;
    world->tiles.surface[x2][y2] = 0x52;
}

static void tile_frame_2(SimGameWorld *world, int x1, int x2, int y1, int y2)
{
    fill_map(world, x1, x2, y1, y1, 0x51);
    fill_map(world, x1, x2, y2, y2, 0x54);
    fill_map(world, x1, x1, y1, y2, 0x5b);
    fill_map(world, x2, x2, y1, y2, 0x5a);
    world->tiles.surface[x1][y1] = 0x56;
    world->tiles.surface[x2][y1] = 0x58;
    world->tiles.surface[x1][y2] = 0x57;
    world->tiles.surface[x2][y2] = 0x59;
}

static void make_plug_v(SimGameWorld *world, int x, int y)
{
    int i, j;
    for (i = 0; i < 5; ++i)
        for (j = 0; j < 4; ++j)
            world->tiles.surface[x + i][y + j] = plug_v[j][i];
}

static void make_plug_h(SimGameWorld *world, int x, int y)
{
    int i, j;
    for (i = 0; i < 4; ++i)
        for (j = 0; j < 5; ++j)
            world->tiles.surface[x + i][y + j] = plug_h[j][i];
}

static void make_outlet_v(SimGameWorld *world, int x, int y)
{
    fill_map(world, x, x + 8, y, y + 12, 0x63);
    tile_frame_1(world, x, x + 8, y, y + 12);
    make_plug_v(world, x + 2, y + 2);
    make_plug_v(world, x + 2, y + 7);
    world->tiles.surface[x + 4][y + 6] = 0x65;
}

static void make_outlet_h(SimGameWorld *world, int x, int y)
{
    fill_map(world, x, x + 12, y, y + 8, 0x63);
    tile_frame_1(world, x, x + 12, y, y + 8);
    make_plug_h(world, x + 2, y + 2);
    make_plug_h(world, x + 7, y + 2);
    world->tiles.surface[x + 6][y + 4] = 0x65;
}

static void make_knob(SimGameWorld *world, int x, int y)
{
    int i, j;
    for (i = 0; i < 5; ++i)
        for (j = 0; j < 5; ++j)
            world->tiles.surface[x + i][y + j] = knob[j][i];
}

static void make_penny(SimGameWorld *world, int x, int y)
{
    int i, j;
    for (i = 0; i < 3; ++i)
        for (j = 0; j < 3; ++j)
            world->tiles.surface[x + i][y + j] = penny[j][i];
}

static void make_clip(SimGameWorld *world, int x, int y)
{
    int i, j;
    for (i = 0; i < 3; ++i)
        for (j = 0; j < 3; ++j)
            if (clip[j][i] != 0)
                world->tiles.surface[x + i][y + j] = clip[j][i];
}

static void make_sink(SimGameWorld *world)
{
    fill_map(world, 0x25, 0x5b, 0x1a, 0x38, 1);
    fill_map(world, 0x29, 0x44, 0x21, 0x35, 0xc2);
    fill_map(world, 0x2a, 0x44, 0x23, 0x35, 0xc1);
    tile_frame_2(world, 0x28, 0x44, 0x20, 0x35);
    fill_map(world, 0x49, 0x58, 0x21, 0x35, 0xc2);
    fill_map(world, 0x4a, 0x58, 0x23, 0x35, 0xc1);
    tile_frame_2(world, 0x48, 0x58, 0x20, 0x35);
    tile_frame_1(world, 0x25, 0x5b, 0x1a, 0x38);
    make_knob(world, 0x2c, 0x1b);
    make_knob(world, 0x3c, 0x1b);
    world->tiles.surface[0x3e][0x1d] = 0x4d;
    make_knob(world, 0x34, 0x1b);
    make_knob(world, 0x34, 0x24);
    fill_map(world, 0x34, 0x38, 0x1d, 0x26, 0x4e);
    fill_map(world, 0x34, 0x34, 0x1d, 0x26, 0x43);
    fill_map(world, 0x38, 0x38, 0x1d, 0x26, 0x44);
    world->tiles.surface[0x34][0x28] = 0x45;
    world->tiles.surface[0x38][0x28] = 0x48;
    fill_map(world, 0x36, 0x38, 0x29, 0x2a, 0xc2);
    fill_map(world, 0x39, 0x3a, 0x23, 0x2a, 0xc2);
}

static void make_kitchen_wall(SimGameWorld *world)
{
    int x, y;
    fill_map(world, 0, 0x7f, 0, 0x17, 0x62);
    fill_map(world, 0, 0x7f, 0x18, 0x3f, 0);
    for (y = 0; y < 0x18; y += 8)
        for (x = 0; x < 128; ++x)
            world->tiles.surface[x][y] = 0x68;
    for (x = 0; x < 128; x += 8)
        for (y = 0; y < 0x18; ++y)
            world->tiles.surface[x][y] =
                world->tiles.surface[x][y] == 0x62 ? 0x66 : 0x67;
    for (x = 0; x < 128; ++x)
        world->tiles.surface[x][0x17] =
            world->tiles.surface[x][0x17] == 0x62 ? 0x68 : 0x69;
    make_outlet_v(world, 0x24, 2);
    make_outlet_v(world, 0x54, 2);
    world->drop_direction = 2;
}

static void make_lint_2(SimGameWorld *world, SimRng *rng,
                        int x1, int x2, int y1, int y2)
{
    int x, y;
    for (x = x1; x <= x2; ++x)
        for (y = y1; y <= y2; ++y)
            if (rand1(rng, 200) == 0)
                world->tiles.surface[x][y] = (uint8_t)(rand1(rng, 2) + 0x3e);
}

static void carpet_floor_l(SimGameWorld *world, SimRng *rng)
{
    fill_map(world, 0, 0x14, 0, 0x3f, 0x64);
    fill_map(world, 0x15, 0x15, 0, 0x3f, 0x7a);
    fill_map(world, 0x16, 0x17, 0, 0x3f, 0x7b);
    fill_map(world, 0x17, 0x7f, 0, 0x3f, 3);
    make_lint_2(world, rng, 0x17, 0x7f, 0, 0x3f);
    make_outlet_h(world, 2, 0x19);
    world->drop_direction = 1;
}

static void carpet_floor_r(SimGameWorld *world, SimRng *rng)
{
    fill_map(world, 0, 0x69, 0, 0x3f, 3);
    make_lint_2(world, rng, 0, 0x69, 0, 0x3f);
    fill_map(world, 0x6a, 0x6a, 0, 0x3f, 0x7c);
    fill_map(world, 0x68, 0x69, 0, 0x3f, 0x7b);
    fill_map(world, 0x6a, 0x7f, 0, 0x3f, 0x64);
    make_outlet_h(world, 0x71, 0x23);
    world->drop_direction = 3;
}

static void fill_map_legs(SimGameWorld *world, SimRng *rng,
                          int x1, int x2, int y1, int y2, uint8_t tile)
{
    int x, y;
    fill_map(world, x1, x2, y1, y2, tile);
    for (x = x1; x <= x2; ++x)
        for (y = y1; y <= y2; ++y)
            if (rand1(rng, 20) == 0)
                world->tiles.surface[x][y] = (uint8_t)(rand1(rng, 5) + 0x38);
    fill_map(world, x1, x1 + 3, y1, y1 + 3, 0xc0);
    fill_map(world, x2 - 3, x2, y1, y1 + 3, 0xc0);
    fill_map(world, x1, x1 + 3, y2 - 3, y2, 0xc0);
    fill_map(world, x2 - 3, x2, y2 - 3, y2, 0xc0);
}

static void floor_tiles(SimGameWorld *world)
{
    int x, y;
    for (x = 0; x < 128; ++x)
        for (y = 0; y < 64; ++y)
            world->tiles.surface[x][y] =
                (uint8_t)((((x >> 4) + (y >> 4)) & 1) ? 0 : 1);
    for (y = 0; y < 64; y += 16)
        for (x = 0; x < 128; ++x)
            world->tiles.surface[x][y] =
                (uint8_t)(((x + y) & 0x10) ? 0x60 : 0x61);
    for (x = 0; x < 128; x += 16)
        for (y = 0; y < 64; ++y) {
            if (world->tiles.surface[x][y] < 2)
                world->tiles.surface[x][y] =
                    (uint8_t)(((x + y) & 0x10) ? 0x5e : 0x5f);
            else
                world->tiles.surface[x][y] =
                    (uint8_t)(((x + y) & 0x10) ? 0x5d : 0x5c);
        }
    world->drop_direction = 0;
}

static void add_rock_5(SimGameWorld *world, int x, int y, int shape)
{
    int i, j, k = shape * 5;
    for (i = 0; i < 5; ++i)
        for (j = 0; j < 5; ++j) {
            uint8_t tile = rock5[(k + j) * 5 + i];
            if (tile != 0 && world->tiles.surface[x + i][y + j] > 0x10)
                return;
        }
    for (i = 0; i < 5; ++i)
        for (j = 0; j < 5; ++j) {
            uint8_t tile = rock5[(k + j) * 5 + i];
            if (tile != 0)
                world->tiles.surface[x + i][y + j] = tile;
        }
}

static void add_rock_3(SimGameWorld *world, int x, int y, int shape)
{
    int i, j, k = shape * 3;
    for (i = 0; i < 3; ++i)
        for (j = 0; j < 3; ++j) {
            uint8_t tile = rock3[(k + j) * 3 + i];
            if (tile != 0 && world->tiles.surface[x + i][y + j] > 0x10)
                return;
        }
    for (i = 0; i < 3; ++i)
        for (j = 0; j < 3; ++j) {
            uint8_t tile = rock3[(k + j) * 3 + i];
            if (tile != 0)
                world->tiles.surface[x + i][y + j] = tile;
        }
}

static void add_rocks(SimGameWorld *world, SimRng *rng)
{
    int i, n = (int)rand1(rng, 3) + 2;
    for (i = 0; i < n; ++i) {
        int y = (int)rand1(rng, 0x3a);
        int x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 0);
        y = (int)rand1(rng, 0x3a); x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 1);
        y = (int)rand1(rng, 0x3a); x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 2);
        y = (int)rand1(rng, 0x3a); x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 3);
        y = (int)rand1(rng, 0x3a); x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 4);
        y = (int)rand1(rng, 0x3a); x = (int)rand1(rng, 0x7a);
        add_rock_5(world, x, y, 5);
    }
    for (i = 0; i < n * 2; ++i) {
        int y = (int)rand1(rng, 0x3c);
        int x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 0);
        y = (int)rand1(rng, 0x3c); x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 1);
        y = (int)rand1(rng, 0x3c); x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 2);
        y = (int)rand1(rng, 0x3c); x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 3);
        y = (int)rand1(rng, 0x3c); x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 4);
        y = (int)rand1(rng, 0x3c); x = (int)rand1(rng, 0x7c);
        add_rock_3(world, x, y, 5);
    }
}

static int valid_surface(int x, int y)
{
    return x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT;
}

static int is_yellow_life(uint8_t life)
{
    return life == 0xff || life == 0xfe;
}

/* IsClearTile(plane=1): GetLife maps zero and invalid cells to -1. */
static int is_clear_tile(const SimGameWorld *world, int x, int y)
{
    uint8_t tile;
    uint8_t life;
    if (!valid_surface(x, y))
        return 0;
    tile = world->tiles.surface[x][y];
    life = world->life_a[x][y];
    if (tile < 0x10 && (life == 0 || is_yellow_life(life)))
        return 1;
    return 0;
}

/* IsClear3x3's parameter names are reversed internally, but its body passes
 * (formal y, formal x) to IsClearTile. Given source call (1, x, y), the
 * resulting MapA access is still (x, y). */
static int is_clear_3x3(const SimGameWorld *world, int x, int y)
{
    int i;
    if (!is_clear_tile(world, x, y))
        return 0;
    for (i = 0; i < 8; ++i)
        if (!is_clear_tile(world, x + dx8[i], y + dy8[i]))
            return 0;
    return 1;
}

static void set_map_a(SimGameWorld *world, int x, int y, uint8_t tile)
{
    if (valid_surface(x, y))
        world->tiles.surface[x][y] = tile;
}

static void add_ant_lion(SimGameWorld *world, int x, int y)
{
    int i;
    int lx, ly;
    int index;
    set_map_a(world, x, y, 0x38);
    for (i = 0; i < 8; ++i) {
        lx = x + dx8[i];
        ly = y + dy8[i];
        if (is_clear_tile(world, lx, ly))
            set_map_a(world, lx, ly, (uint8_t)(lion_ring[i] + 0x30));
    }
    index = world->ant_lion_count;
    if (index < 0)
        index = 0;
    if (index >= 10)
        index = 9;
    world->ant_lions[index].x = (uint8_t)x;
    world->ant_lions[index].y = (uint8_t)y;
    world->ant_lions[index].mode = 0;
    world->ant_lions[index].seconds = 0;
    world->ant_lions[index].timer = 0;
    if (world->ant_lion_count < 9)
        ++world->ant_lion_count;
}

static void add_random_ant_lion(SimGameWorld *world, SimRng *rng)
{
    int tries;
    int x, y;
    for (tries = 0; tries < 200; ++tries) {
        /* The historical compiler evaluated the rightmost SRand1 call first
         * in each sum; the operands are kept separate to preserve that RNG
         * sequence while the resulting coordinate remains commutative. */
        x = (int)rand1(rng, 0x41) + (int)rand1(rng, 0x40);
        y = (int)rand1(rng, 0x21) + (int)rand1(rng, 0x20);
        if (is_clear_3x3(world, x, y) ||
            (is_clear_tile(world, x, y) && tries >= 100)) {
            add_ant_lion(world, x, y);
            return;
        }
    }
}

static void init_ant_lions(SimGameWorld *world, SimRng *rng, int count)
{
    int i;
    world->ant_lion_count = 0;
    world->ants_eaten_by_lions = 0;
    if (count > 10)
        count = 10;
    for (i = 0; i < count; ++i)
        add_random_ant_lion(world, rng);
    world->initial_ant_lions = (int16_t)count;
}

static void init_sow(SimGameWorld *world, SimRng *rng)
{
    int i = 2;
    int x, y;
    while (i != 0) {
        x = (int)rand1(rng, 128);
        y = (int)rand1(rng, 64);
        if (world->tiles.surface[x][y] < 16) {
            world->sow_x[i] = (int16_t)x;
            world->sow_y[i] = (int16_t)y;
            world->sow_direction[i] = (int16_t)rand1(rng, 8);
            world->sow_saved_tile[i] = world->tiles.surface[x][y];
            world->tiles.surface[x][y] = sow_tiles[world->sow_direction[i]];
            --i;
        }
    }
}

static void init_pillar(SimGameWorld *world, SimRng *rng)
{
    int i;
    world->pillar_state = 0;
    world->pillar_x = 0;
    world->pillar_y = 0;
    world->pillar_segment = 0;
    world->pillar_direction = 0;
    for (i = 0; i < 6; ++i)
        world->pillar_map[i] = 0;
    if (world->tiles.terrain_set == 0)
        init_sow(world, rng);
}

static void set_ground_tile(SimGameWorld *world, int16_t tile)
{
    int16_t resource_set = tile == 0x3e9 ? 1 : 0;
    world->tiles.terrain_set = resource_set;
    world->current_ground_tile_id = tile;
    world->overlay_type = 0;
    world->overlay_id = tile;
    if (tile == 0x3e9) {
        world->overlay_resource_set = resource_set;
        world->overlay_width = 0x90;
    } else {
        world->overlay_resource_set = resource_set;
        world->overlay_width = 0x50;
    }
}

static void make_house_patch(SimGameWorld *world, SimRng *rng, int n)
{
    if (world->tiles.terrain_set != 1)
        set_ground_tile(world, 0x3e9);
    init_ant_lions(world, rng, 0);
    init_pillar(world, rng);

    switch (n) {
    case 0:
        make_kitchen_wall(world);
        make_sink(world);
        break;
    case 2: case 3: case 17: case 18: case 19: case 33: case 34: case 35:
        floor_tiles(world);
        break;
    case 4: case 10: case 11: case 13: case 14:
        carpet_floor_l(world, rng);
        break;
    case 5:
        carpet_floor_l(world, rng);
        fill_map(world, 0x18, 0x46, 0x14, 0x3f, 2);
        make_penny(world, 0x28, 0x2d);
        break;
    case 6:
        carpet_floor_l(world, rng);
        fill_map(world, 0x18, 0x46, 0, 0x3f, 2);
        make_penny(world, 0x20, 0x14);
        make_clip(world, 0x26, 0x37);
        break;
    case 7:
        carpet_floor_l(world, rng);
        fill_map(world, 0x18, 0x46, 0, 0x14, 2);
        make_clip(world, 0x2a, 0x0a);
        break;
    case 8:
        carpet_floor_l(world, rng);
        fill_map_legs(world, rng, 0x18, 0x36, 0x0f, 0x2d, 2);
        make_clip(world, 0x1c, 0x22);
        break;
    case 9:
        fill_map(world, 0, 0x7f, 0, 0x3f, 3);
        world->drop_direction = 2;
        break;
    case 12:
        carpet_floor_l(world, rng);
        fill_map_legs(world, rng, 0x2d, 0x5f, 8, 0x2e, 2);
        break;
    case 15:
        carpet_floor_l(world, rng);
        fill_map_legs(world, rng, 0x32, 0x64, 0x0a, 0x2d, 2);
        make_penny(world, 0x4b, 0x22);
        break;
    case 20: case 21: case 22: case 23: case 24: case 25:
    case 26: case 27: case 28: case 29: case 30: case 31:
        carpet_floor_r(world, rng);
        break;
    case 36: case 37:
        fill_map(world, 0, 0x7f, 0, 0x3f, 0);
        world->drop_direction = 2;
        break;
    default:
        make_kitchen_wall(world);
        break;
    }
}

static void make_yard_patch(SimGameWorld *world, SimRng *rng)
{
    int row, col, i, tile;
    if (world->tiles.terrain_set != 0)
        set_ground_tile(world, 0x3e8);
    for (row = 0; row < 128; ++row)
        for (col = 0; col < 64; ++col)
            world->tiles.surface[row][col] = (uint8_t)sim_rng_s16(rng);

    add_rocks(world, rng);
    init_ant_lions(world, rng, (int)sim_rng_s4(rng) + 1);
    init_pillar(world, rng);

    for (i = 0; i < 20; ++i) {
        row = (int)rand1(rng, 0x7d) + 1;
        col = (int)rand1(rng, 0x3d) + 1;
        if (world->tiles.surface[row][col] < 0x18 &&
            world->tiles.surface[row + 1][col] < 0x18 &&
            world->tiles.surface[row][col + 1] < 0x18 &&
            world->tiles.surface[row + 1][col + 1] < 0x18) {
            world->tiles.surface[row][col] = 0x20;
            world->tiles.surface[row + 1][col] = 0x21;
            world->tiles.surface[row][col + 1] = 0x22;
            world->tiles.surface[row + 1][col + 1] = 0x23;
        }
    }
    for (i = 0; i < 30; ++i) {
        row = (int)rand1(rng, 0x7d) + 1;
        col = (int)rand1(rng, 0x3d) + 1;
        if (world->tiles.surface[row][col] < 0x18 &&
            world->tiles.surface[row + 1][col] < 0x18) {
            tile = ((int)rand1(rng, 2) + 0x12) << 1;
            world->tiles.surface[row][col] = (uint8_t)tile;
            world->tiles.surface[row + 1][col] = (uint8_t)(tile + 1);
        }
    }
    for (i = 0; i < 100; ++i) {
        row = (int)rand1(rng, 0x7d) + 1;
        col = (int)rand1(rng, 0x3d) + 1;
        if (world->tiles.surface[row][col] < 0x18)
            world->tiles.surface[row][col] = 0x28;
    }
    for (i = 0; i < 128; ++i) {
        row = (int)rand1(rng, 0x7d) + 1;
        col = (int)rand1(rng, 0x3d) + 1;
        if (world->tiles.surface[row][col] < 0x18)
            world->tiles.surface[row][col] = 0x51;
    }
}

SimTerrainStatus sim_terrain_build(SimGameWorld *world, SimRng *rng,
                                   int16_t x, int16_t y)
{
    int n;
    int is_yard;
    if (world == NULL || rng == NULL)
        return SIM_TERRAIN_INVALID_ARGUMENT;
    if (x < 0 || x > 11 || y < 0 || y > 15)
        return SIM_TERRAIN_INVALID_ARGUMENT;
    n = ((int)x << 4) + (int)y;
    is_yard = n > 0x25;
    if (is_yard)
        make_yard_patch(world, rng);
    else
        make_house_patch(world, rng, n);
    return SIM_TERRAIN_OK;
}
