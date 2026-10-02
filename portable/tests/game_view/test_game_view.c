#include "../../ui_model/windows/game_view.h"
#include "../../game/session.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_profile0_viewport_and_generated_scene(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimSession session = SIM_SESSION_INITIALIZER;
    const SimNewGameConfig config = {1, 0, 11, 8};
    PortableGameViewState state = {0, -1, 0, 0, 0, 0};
    PortableGameView view;
    PortableGameViewRenderResult result = {0, 0};
    PortableFramebuffer framebuffer;
    uint8_t pixels[640 * 400];
    PortableRect original_clip = {10, 10, 630, 390};
    PortableRect narrow_clip = {100, 60, 200, 100};
    unsigned x, y;

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_load(&registry, PORTABLE_GAME_VIEW_WINDOW_ID) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_recalculate(&registry,
           PORTABLE_GAME_VIEW_WINDOW_ID, NULL) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "assets", &database, &registry) ==
           SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x12345678u, 0x87654321u) ==
           SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    state.pheromone_mode = session.world.source_state_07be;

    assert(registry.slots[0].window.objects[4].rect.left == 64);
    assert(registry.slots[0].window.objects[4].rect.top == 41);
    assert(registry.slots[0].window.objects[4].rect.right == 416);
    assert(registry.slots[0].window.objects[4].rect.bottom == 330);
    assert(portable_game_view_resolve(&registry, &session.world, &state, &view) ==
           PORTABLE_GAME_VIEW_OK);
    assert(view.map.plane == session.world.current_ant_plane);
    assert(view.map.columns == 22 && view.map.rows == 19);
    assert(view.map.camera_x == session.world.me_x - 11);
    assert(view.map.camera_y == session.world.me_y - 9);
    if (view.map.camera_x < 0) assert(view.map.camera_x == 0);
    if (view.map.camera_y < 0) assert(view.map.camera_y == 0);

    memset(pixels, 0xa5, sizeof pixels);
    assert(portable_framebuffer_init(&framebuffer, 640, 400, 640, pixels) ==
           PORTABLE_RENDER_OK);
    portable_framebuffer_set_clip(&framebuffer, original_clip);
    assert(portable_game_view_render(&session.world, &view, &session.tileset, &framebuffer,
                                     &result) == PORTABLE_GAME_VIEW_OK);
    assert(result.cells_drawn == 22u * 19u);
    assert(result.cells_with_life > 0);
    printf("scene plane=%d me=%d,%d camera=%d,%d cells=%zu life=%zu\n",
           view.map.plane, session.world.me_x, session.world.me_y,
           view.map.camera_x, view.map.camera_y,
           result.cells_drawn, result.cells_with_life);
    assert(memcmp(&framebuffer.clip, &original_clip, sizeof original_clip) == 0);
    for (y = 0; y < 400; ++y) {
        for (x = 0; x < 640; ++x) {
            if (x < 64 || x >= 416 || y < 41 || y >= 330)
                assert(pixels[y * 640 + x] == 0xa5);
        }
    }

    memset(pixels, 0xa5, sizeof pixels);
    portable_framebuffer_set_clip(&framebuffer, narrow_clip);
    assert(portable_game_view_render(&session.world, &view, &session.tileset, &framebuffer,
                                     &result) == PORTABLE_GAME_VIEW_OK);
    assert(result.cells_drawn == 22u * 19u);
    assert(memcmp(&framebuffer.clip, &narrow_clip, sizeof narrow_clip) == 0);
    for (y = 0; y < 400; ++y) {
        for (x = 0; x < 640; ++x) {
            if (x < 100 || x >= 200 || y < 60 || y >= 100)
                assert(pixels[y * 640 + x] == 0xa5);
        }
    }

    sim_session_close(&session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

static void test_requires_actual_recalculated_window(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimGameWorld world;
    PortableGameViewState state = {0, -1, 0, 0, 0, 0};
    PortableGameView view;
    memset(&world, 0, sizeof world);
    world.selected_map_plane = 2;
    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_game_view_resolve(&registry, &world, &state, &view) ==
           PORTABLE_GAME_VIEW_WINDOW_NOT_READY);
    assert(portable_window_registry_load(&registry, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_game_view_resolve(&registry, &world, &state, &view) ==
           PORTABLE_GAME_VIEW_WINDOW_NOT_READY);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

static void test_plane_bounds_and_camera_edges(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimGameWorld world;
    PortableGameViewState state = {0, -1, 0, 0, 0, 0};
    PortableGameView view;
    memset(&world, 0, sizeof world);
    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_load(&registry, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_recalculate(&registry, 0, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);

    world.selected_map_plane = 0;
    world.me_x = world.me_y = 0;
    assert(portable_game_view_resolve(&registry, &world, &state, &view) ==
           PORTABLE_GAME_VIEW_OK);
    assert(view.map.camera_x == 0 && view.map.camera_y == 0);
    world.selected_map_plane = 2;
    world.me_x = world.me_y = 63;
    assert(portable_game_view_resolve(&registry, &world, &state, &view) ==
           PORTABLE_GAME_VIEW_OK);
    assert(view.map.camera_x == 42 && view.map.camera_y == 45);
    world.selected_map_plane = 3;
    assert(portable_game_view_resolve(&registry, &world, &state, &view) ==
           PORTABLE_GAME_VIEW_OK);
    assert(view.map.camera_x == 42 && view.map.camera_y == 45);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    test_profile0_viewport_and_generated_scene();
    test_requires_actual_recalculated_window();
    test_plane_bounds_and_camera_edges();
    puts("default game viewport tests passed");
    return 0;
}
