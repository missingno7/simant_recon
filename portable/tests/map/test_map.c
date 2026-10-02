#include "../../game/render/map.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t ground_atlas[0x8000];
static uint8_t surface_frames[3][0x5000];
static uint8_t nest_frames[3][0x5000];

static SimMapView base_view(int plane)
{
    SimMapView view;
    memset(&view, 0, sizeof view);
    view.plane = (int16_t)plane;
    view.columns = 2;
    view.rows = 2;
    view.cell_step_x = 16;
    view.cell_step_y = 12;
    view.animation_base = 3;
    view.queen_frame = 5;
    view.young_frame = 7;
    view.caste_frame = 4;
    return view;
}

static void test_surface_selection_and_transparent_life(void)
{
    SimGameWorld world;
    SimMapView view = base_view(0);
    SimMapDrawCommand command;

    memset(&world, 0, sizeof world);
    view.camera_x = 63;
    view.camera_y = 63;
    view.screen_left = 20;
    view.screen_top = 30;
    world.tiles.surface[0][0] = 0x2a;
    world.life_a[0][0] = 0x22;
    assert(sim_map_select_cell(&world, &view, 1, 1, &command) == SIM_MAP_OK);
    assert(command.map_x == 0 && command.map_y == 0);
    assert(command.screen_x == 36 && command.screen_y == 42);
    assert(command.ground_tile == 0x2a && command.life_present && command.life_overlay);
    assert(command.life_frame == 0x122);
    assert(command.resource_family == SIM_MAP_RESOURCE_SURFACE);

    world.life_a[0][0] = 0;
    assert(sim_map_select_cell(&world, &view, 1, 1, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0x2a && !command.life_present && !command.life_overlay);
}

static void test_pheromone_overlay_and_fallback(void)
{
    SimGameWorld world;
    SimMapView view = base_view(1);
    SimMapDrawCommand command;

    memset(&world, 0, sizeof world);
    view.pheromone_mode = 2;
    view.camera_x = 6;
    view.camera_y = 8;
    world.tiles.surface[6][8] = 0x32;
    world.pheromone_b_trail[3][4] = 0x2f;
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0xf2 && command.pheromone_tile == 1);

    world.pheromone_b_trail[3][4] = 0x10;
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0x32 && command.pheromone_tile == 0);

    world.pheromone_b_trail[3][4] = 0x11;
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0xf1 && command.pheromone_tile == 1);

    view.pheromone_mode = 0;
    world.pheromone_a[3][4] = 0x20;
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0xf2 && command.pheromone_tile == 1);
    view.pheromone_mode = -1;
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0x32 && command.pheromone_tile == 0);
}

static void test_life_specials_and_nest_groups(void)
{
    SimGameWorld world;
    SimMapView view = base_view(2);
    SimMapDrawCommand command;

    memset(&world, 0, sizeof world);
    view.columns = 64;
    view.rows = 64;
    world.tiles.nest_b[10][11] = 0x70;
    world.life_b[10][11] = 0xff;
    assert(sim_map_select_cell(&world, &view, 10, 11, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0 && command.life_frame == 0x30e);
    assert(command.resource_family == SIM_MAP_RESOURCE_NEST);

    world.tiles.nest_b[10][11] = 0x7f;
    world.life_b[10][11] = 0xfe;
    assert(sim_map_select_cell(&world, &view, 10, 11, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0x0f && command.life_frame == 0x314);

    view.plane = 3;
    world.tiles.nest_r[10][11] = 0x85;
    world.life_r[10][11] = 0x68;
    assert(sim_map_select_cell(&world, &view, 10, 11, &command) == SIM_MAP_OK);
    assert(command.ground_tile == 0x15 && command.life_frame == 0x268);
}

static void test_composition_order_and_validation(void)
{
    SimGameWorld world;
    SimMapView view = base_view(0);
    SimMapDrawCommand commands[4];
    size_t count = 99;
    memset(&world, 0, sizeof world);
    world.tiles.surface[0][0] = 1;
    world.tiles.surface[0][1] = 2;
    world.tiles.surface[1][0] = 3;
    world.tiles.surface[1][1] = 4;
    view.camera_x = 0;
    view.camera_y = 0;
    view.screen_left = -2;
    view.screen_top = 5;
    assert(sim_map_compose(&world, &view, commands, 4, &count) == SIM_MAP_OK);
    assert(count == 4);
    assert(commands[0].ground_tile == 1 && commands[1].ground_tile == 3);
    assert(commands[2].ground_tile == 2 && commands[3].ground_tile == 4);
    assert(commands[2].screen_x == -2 && commands[2].screen_y == 17);
    assert(sim_map_compose(&world, &view, commands, 3, &count) == SIM_MAP_OUTPUT_TOO_SMALL);
    assert(count == 0);
    assert(sim_map_select_cell(&world, &view, -1, 0, commands) == SIM_MAP_INVALID_VIEW);
}

static void encode_ground_pixel(uint8_t *atlas, unsigned tile, unsigned x,
                                unsigned y, uint8_t color)
{
    unsigned plane;
    uint8_t bit = (uint8_t)(0x80u >> (x & 7u));
    for (plane = 0; plane < 4; ++plane) {
        uint8_t *word = atlas + tile * 128u + y * 8u + plane * 2u + (x >> 3);
        if ((color & (1u << plane)) != 0)
            *word |= bit;
        else
            *word &= (uint8_t)~bit;
    }
}

static void encode_life_pixel(uint8_t *frames, unsigned frame, unsigned x,
                              unsigned y, uint8_t color)
{
    unsigned plane;
    size_t offset = frame * 160u + y * 10u;
    uint8_t bit = (uint8_t)(0x80u >> (x & 7u));
    frames[offset + (x >> 3)] |= bit;
    for (plane = 0; plane < 4; ++plane) {
        uint8_t *word = frames + offset + 2u + plane * 2u + (x >> 3);
        if ((color & (1u << plane)) != 0)
            *word |= bit;
        else
            *word &= (uint8_t)~bit;
    }
}

static void test_pixel_render_and_ems_group_routing(void)
{
    SimGameWorld world;
    SimMapView view = base_view(0);
    SimMapDrawCommand command;
    PortableTileSet tileset;
    PortableFramebuffer framebuffer;
    uint8_t pixels[32 * 32];
    unsigned page;

    memset(&world, 0, sizeof world);
    memset(&tileset, 0, sizeof tileset);
    memset(ground_atlas, 0, sizeof ground_atlas);
    memset(surface_frames, 0, sizeof surface_frames);
    memset(nest_frames, 0, sizeof nest_frames);
    memset(pixels, 0, sizeof pixels);
    for (page = 0; page < 3; ++page) {
        tileset.ems_surface[page].record.data = surface_frames[page];
        tileset.ems_surface[page].record.size = sizeof surface_frames[page];
        tileset.ems_nest[page].record.data = nest_frames[page];
        tileset.ems_nest[page].record.size = sizeof nest_frames[page];
    }
    tileset.ground_resource.record.data = ground_atlas;
    tileset.ground_resource.record.size = sizeof ground_atlas;
    view.columns = 1;
    view.rows = 1;
    view.screen_left = 4;
    view.screen_top = 6;
    view.cell_step_x = 16;
    view.cell_step_y = 16;
    view.ega_profile = 8;
    world.tiles.surface[0][0] = 5;
    world.life_a[0][0] = 1; /* source frame 0101 normalizes to life frame 1 */
    encode_ground_pixel(ground_atlas, 5, 0, 0, 1);
    encode_ground_pixel(ground_atlas, 5, 1, 0, 3);
    encode_life_pixel(surface_frames[0], 1, 0, 0, 5);
    assert(portable_framebuffer_init(&framebuffer, 32, 32, 32, pixels) == PORTABLE_RENDER_OK);
    view.ega_profile = 0;
    assert(sim_map_render_cell(&world, &view, 0, 0, &tileset, &framebuffer) == SIM_MAP_OK);
    assert(pixels[6 * 32 + 4] == 5); /* masked life pixel replaces the ground */
    assert(pixels[6 * 32 + 5] == 3); /* clear mask preserves the ground */
    assert(sim_map_select_cell(&world, &view, 0, 0, &command) == SIM_MAP_OK);
    assert(command.life_frame == 0x101 && command.life_resource_frame == 1);

    /* Resource frame 130 is chunk 1/frame 2, and plane 2 selects the nest set. */
    view.plane = 2;
    view.ega_profile = 8;
    world.tiles.nest_b[0][0] = 0x72;
    world.life_b[0][0] = 0x82;
    encode_life_pixel(nest_frames[1], 2, 0, 0, 9);
    memset(pixels, 0, sizeof pixels);
    assert(sim_map_render_cell(&world, &view, 0, 0, &tileset, &framebuffer) == SIM_MAP_OK);
    assert(pixels[6 * 32 + 4] == 9);

    view.ega_profile = 1;
    assert(sim_map_render_cell(&world, &view, 0, 0, &tileset, &framebuffer) ==
           SIM_MAP_UNSUPPORTED_VIEW);
}

int main(void)
{
    test_surface_selection_and_transparent_life();
    test_pheromone_overlay_and_fallback();
    test_life_specials_and_nest_groups();
    test_composition_order_and_validation();
    test_pixel_render_and_ems_group_routing();
    puts("map tests passed");
    return 0;
}
