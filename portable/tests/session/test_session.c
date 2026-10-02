#include "../../game/session.h"
#include "../../game/render/map.h"
#include "../../render/primitives.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int released_animation_count;

static void release_animation(void *resource)
{
    assert(resource == &released_animation_count);
    ++released_animation_count;
}

static void test_open_and_new_game(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    PortableDatabase window_database = { 0 };
    PortableWindowRegistry window_registry = { 0 };
    const SimNewGameConfig config = { 1, 0, 11, 8 };
    uint8_t pixels[16 * 16];
    PortableFramebuffer framebuffer;
    SimMapView view;
    SimMapDrawCommand command;
    uint16_t first_s;
    uint32_t first_c;
    int16_t x, y;
    int rendered = 0;

    SimSessionStatus open_status;
    assert(portable_db_open(&window_database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&window_registry, &window_database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    open_status = sim_session_init(&session, "assets", &window_database,
                                   &window_registry);
    if (open_status != SIM_SESSION_OK)
        fprintf(stderr, "session open: %s (%d)\n",
                sim_session_status_string(open_status), (int)open_status);
    assert(open_status == SIM_SESSION_OK);
    assert(session.shared_open && session.window_database == &window_database &&
           session.window_registry == &window_registry && session.tileset_open);
    assert(session.world.tick_count_delays[0] == 21);
    assert(session.world.tick_count_delays[1] == 7);
    assert(session.world.tick_count_delays[2] == 0);
    assert(session.world.tick_count_delays[3] == -1);
    assert(session.feeding.next_food_threshold == 0x28);
    assert(session.tileset.ground_resource.record.size == 0x8000u);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_BAD_ARGUMENT);
    assert(sim_session_seed_startup(&session, 0x12345678u, 0x87654321u) ==
           SIM_SESSION_OK);
    first_s = sim_rng_get_s_seed(&session.rng);
    first_c = sim_rng_get_c_seed(&session.rng);
    assert(sim_session_seed_startup(&session, 1, 1) ==
           SIM_SESSION_ALREADY_STARTED);
    {
        SimNewGameConfig invalid = config;
        invalid.scenario = 4;
        assert(sim_session_new_game(&session, &invalid) == SIM_SESSION_BAD_ARGUMENT);
        assert(!session.new_game_ready);
    }

    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(session.new_game_ready);
    assert(session.world.scenario == 1);
    assert(session.world.map_plane == 2);
    assert(session.world.selected_map_plane == 2);
    assert(session.world.current_ant_plane == 2);
    assert(session.worldgen_effects.count == 2);
    assert(session.worldgen_effects.events[0].kind ==
           SIM_WORLDGEN_PLAYER_SELECTION);
    assert(session.worldgen_effects.events[1].kind ==
           SIM_WORLDGEN_MAP_INVALIDATE);
    assert(session.controls[SIM_SETUP_MODE_CONTROL].active);
    assert(session.controls[SIM_SETUP_CASTE_CONTROL].active);
    assert(session.setup_controls.mode_rect.left == 136);
    assert(session.setup_controls.mode_rect.top == 344);
    assert(session.setup_controls.mode_rect.right == 247);
    assert(session.setup_controls.mode_rect.bottom == 440);
    assert(session.setup_controls.caste_rect.left == 392);
    assert(session.setup_controls.caste_rect.top == 344);
    assert(session.setup_controls.caste_rect.right == 501);
    assert(session.setup_controls.caste_rect.bottom == 440);
    assert(session.world.map_focus[1][0] == session.world.me_x);
    assert(session.world.map_focus[1][1] == session.world.me_y);
    assert(memcmp(session.sine_q15, sim_spider_sine_table(),
                  sizeof session.sine_q15) == 0);
    assert(sim_rng_get_s_seed(&session.rng) != first_s);
    assert(sim_rng_get_c_seed(&session.rng) != first_c);

    /* The loaded shared ground atlas must render actual generated world tiles. */
    memset(pixels, 0, sizeof pixels);
    assert(portable_framebuffer_init(&framebuffer, 16, 16, 16, pixels) ==
           PORTABLE_RENDER_OK);
    memset(&view, 0, sizeof view);
    view.plane = 1;
    view.pheromone_mode = -1;
    view.columns = 1;
    view.rows = 1;
    view.cell_step_x = 16;
    view.cell_step_y = 16;
    view.ega_profile = 0;
    for (x = 0; x < SIM_WORLD_WIDTH && !rendered; ++x) {
        for (y = 0; y < SIM_WORLD_HEIGHT && !rendered; ++y) {
            view.camera_x = x;
            view.camera_y = y;
            if (sim_map_select_cell(&session.world, &view, 0, 0, &command) !=
                SIM_MAP_OK)
                continue;
            if (sim_map_render_cell(&session.world, &view, 0, 0,
                                    &session.tileset, &framebuffer) == SIM_MAP_OK)
                rendered = 1;
        }
    }
    assert(rendered);

    /* NewGame continues both startup streams and closes a previously-owned
     * control animation before installing the refreshed control projection. */
    session.controls[SIM_SETUP_MODE_CONTROL].animation_resource =
        &released_animation_count;
    session.controls[SIM_SETUP_MODE_CONTROL].release_animation =
        release_animation;
    released_animation_count = 0;
    first_s = sim_rng_get_s_seed(&session.rng);
    first_c = sim_rng_get_c_seed(&session.rng);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(released_animation_count == 1);
    assert(session.controls[SIM_SETUP_MODE_CONTROL].animation_resource == NULL);
    assert(sim_rng_get_s_seed(&session.rng) != first_s);
    assert(sim_rng_get_c_seed(&session.rng) != first_c);
    assert(session.world.tick_count_delays[0] == 21);
    assert(session.world.tick_count_delays[1] == 7);
    assert(session.world.tick_count_delays[2] == 0);
    assert(session.world.tick_count_delays[3] == -1);
    assert(session.feeding.next_food_threshold == 0x28);

    session.controls[SIM_SETUP_MODE_CONTROL].animation_resource =
        &released_animation_count;
    session.controls[SIM_SETUP_MODE_CONTROL].release_animation =
        release_animation;
    session.controls[SIM_SETUP_CASTE_CONTROL].animation_resource =
        &released_animation_count;
    session.controls[SIM_SETUP_CASTE_CONTROL].release_animation =
        release_animation;

    sim_session_close(&session);
    assert(!session.resources_ready && session.window_registry == NULL &&
           session.window_database == NULL && !session.shared_open &&
           !session.tileset_open);
    assert(released_animation_count == 3);
    portable_window_registry_destroy(&window_registry);
    portable_db_close(&window_database);
}

static void test_missing_resources_fail_closed(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    PortableDatabase window_database = { 0 };
    PortableWindowRegistry window_registry = { 0 };
    assert(portable_db_open(&window_database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&window_registry, &window_database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "build/portable/no-such-assets",
        &window_database, &window_registry) == SIM_SESSION_DATABASE_ERROR);
    assert(!session.resources_ready);
    portable_window_registry_destroy(&window_registry);
    portable_db_close(&window_database);
}

int main(void)
{
    test_open_and_new_game();
    test_missing_resources_fail_closed();
    puts("session startup/NewGame integration passed");
    return 0;
}
