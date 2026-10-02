#include "session_bridge.h"

#include "../../game/session.h"
#include "../../ui_model/windows/game_view.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>

static void fill_session(SimSession *session)
{
    unsigned i;
    unsigned x, y;
    memset(session, 0, sizeof *session);
    for (x = 0; x < 128; ++x)
        for (y = 0; y < 64; ++y) {
            session->world.tiles.surface[x][y] = (uint8_t)(x + 3u * y);
            session->world.life_a[x][y] = (uint8_t)(x ^ y);
        }
    for (x = 0; x < 64; ++x)
        for (y = 0; y < 64; ++y) {
            session->world.tiles.nest_b[x][y] = (uint8_t)(0x20u + x + y);
            session->world.tiles.nest_r[x][y] = (uint8_t)(0x40u + x + y);
            session->world.exit_b[x][y] = (uint8_t)(x * 2u + y);
            session->world.exit_r[x][y] = (uint8_t)(x + y * 2u);
            session->world.life_b[x][y] = (uint8_t)(x ^ (y + 3u));
            session->world.life_r[x][y] = (uint8_t)(x + 5u * y);
        }
    for (x = 0; x < 64; ++x)
        for (y = 0; y < 32; ++y) {
            session->world.pheromone_a[x][y] = (uint8_t)(x + y);
            session->world.pheromone_b_nest[x][y] = (uint8_t)(x + 2u * y);
            session->world.pheromone_b_trail[x][y] = (uint8_t)(x + 3u * y);
            session->world.pheromone_r_nest[x][y] = (uint8_t)(x + 4u * y);
            session->world.pheromone_r_trail[x][y] = (uint8_t)(x + 5u * y);
            session->world.pheromone_aux[x][y] = 0xa5;
        }
    for (i = 0; i <= SIM_A_ANT_CAPACITY; ++i) {
        session->world.ants_a.x[i] = (uint8_t)i;
        session->world.ants_a.y[i] = (uint8_t)(i + 1u);
        session->world.ants_a.mode[i] = (uint8_t)(i + 2u);
        session->world.ants_a.type[i] = (uint8_t)(i + 3u);
        session->world.ants_a.state[i] = (uint8_t)(i + 4u);
    }
    for (i = 0; i <= SIM_B_ANT_CAPACITY; ++i) {
        session->world.ants_b.x[i] = (uint8_t)(i + 1u);
        session->world.ants_b.y[i] = (uint8_t)(i + 2u);
        session->world.ants_b.mode[i] = (uint8_t)(i + 3u);
        session->world.ants_b.type[i] = (uint8_t)(i + 4u);
        session->world.ants_b.state[i] = (uint8_t)(i + 5u);
        session->world.ants_r.x[i] = (uint8_t)(i + 6u);
        session->world.ants_r.y[i] = (uint8_t)(i + 7u);
        session->world.ants_r.mode[i] = (uint8_t)(i + 8u);
        session->world.ants_r.type[i] = (uint8_t)(i + 9u);
        session->world.ants_r.state[i] = (uint8_t)(i + 10u);
    }
    for (i = 0; i < 10; ++i) {
        session->world.ant_lions[i].x = (uint8_t)(i + 11u);
        session->world.ant_lions[i].y = (uint8_t)(i + 12u);
        session->world.ant_lions[i].mode = (uint8_t)(i + 13u);
        session->world.ant_lions[i].seconds = (uint8_t)(i + 14u);
        session->world.ant_lions[i].timer = (uint8_t)(i + 15u);
        session->spider.corpse_x[i] = (uint8_t)(i + 16u);
        session->spider.corpse_y[i] = (uint8_t)(i + 17u);
    }
    for (i = 0; i < 100; ++i) {
        session->spider.corpse_x[i] = (uint8_t)(i ^ 0x51u);
        session->spider.corpse_y[i] = (uint8_t)(i ^ 0xa2u);
    }
    session->world.ants_a.count = 0x123;
    session->world.ants_b.count = 0x234;
    session->world.ants_r.count = 0x345;
    session->world.ant_lion_count = 7;
    session->world.initial_ant_lions = 8;
    session->world.ants_eaten_by_lions = 9;
    session->world.pillar_map[0] = 0x2345;
    session->world.scenario = 2;
    session->world.map_plane = 3;
    session->world.simulation_speed_index = 2;
    session->world.tick_count_delays[0] = 21;
    session->world.tick_count_delays[1] = 7;
    session->world.tick_count_delays[2] = 0;
    session->world.tick_count_delays[3] = -1;
    session->world.current_ant_plane = 2;
    session->world.me_x = 21;
    session->world.me_y = 31;
    session->world.me_type = 0x66;
    session->world.me_direction = 4;
    session->world.me_health = 1234;
    session->world.world_ticks = 0x12345678u;
    session->modal_mode_105e = 17;
    session->setup_state.black_ants_eaten = 0x1234567;
    session->setup_state.red_ants_eaten = 0x7654321;
    session->setup_state.history_series[9][63] = 0x3456;
    session->setup_state.history_start = 42;
    session->setup_state.graph_selection = 3;
    session->setup_controls.mode_auto = 1;
    session->setup_controls.mode_current = 2;
    session->setup_controls.ideal_caste[3] = 77;
    session->yard_scene.boy_message_count = 0x1234567;
    session->yard_scene.yard_cycle = -7;
    session->spider.corpse_base = 4;
    session->spider.corpse_index = 73;
    session->spider.direction = 6;
    session->spider.x16 = 0x1234;
    session->spider.y16 = 0x5678;
    session->spider.target_mode = 1;
    session->spider.state_flag = 2;
    session->spider.aux_mode = 3;
    session->spider.mode = 4;
    session->spider.sine_q15 = session->sine_q15;
    session->sine_q15[3] = 0x4321;
    session->world.random_seed_grid[0] = 0x7788;
    session->world.build_black[0][0] = 0x7a;
    session->world.build_red[11][8] = 2;
    session->world.current_ground_tile_id = 1000;
    session->world.source_state_104e = session->nest_runtime.alarm_drop_state;
    session->world.source_state_07be = session->nest_runtime.alarm_indicator;
    session->nest_runtime.entrance_b_surface_x = 0x345;
}

static void test_resource_backed_new_game(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimSession session = SIM_SESSION_INITIALIZER;
    const SimNewGameConfig config = {1, 0, 11, 8};
    PortableGameViewState view_state = {0, -1, 0, 0, 0, 0};
    PortableGameView view;
    RecoveredState state;
    RecoveredState defaults;

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "assets", &database, &registry) ==
           SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x12345678u, 0x87654321u) ==
           SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(session.modal_mode_105e == -1);
    assert(portable_window_registry_load(&registry,
           PORTABLE_GAME_VIEW_WINDOW_ID) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_recalculate(&registry,
           PORTABLE_GAME_VIEW_WINDOW_ID, NULL) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(session.world.source_state_07be == -1);
    assert(session.nest_runtime.alarm_indicator == -1);
    assert(portable_game_view_resolve(&registry, &session.world, &view_state,
                                      &view) == PORTABLE_GAME_VIEW_OK);
    assert(view.map.columns == 22 && view.map.rows == 19);
    assert(sim_recovered_state_from_session(&state, &session) ==
           SIM_RECOVERED_BRIDGE_OK);
    recovered_state_init(&defaults);
    fprintf(stderr,
            "resource NewGame: plane=%d me=(%d,%d) view=%dx%d map=(%d,%d) "
            "07BE session=%d runtime=%d recovered_init=%d bounds=%d,%d\n",
            session.world.current_ant_plane, session.world.me_x,
            session.world.me_y, view.map.columns, view.map.rows,
            session.world.map_view_x, session.world.map_view_y,
            session.world.source_state_07be,
            session.nest_runtime.alarm_indicator,
            defaults.fd_3D57_07BE, state.fd_50F6_0FB6,
            state.fd_50F6_0FFA);
    assert(state.MePlane == session.world.current_ant_plane);
    assert(state.MeLocX == session.world.me_x &&
           state.MeLocY == session.world.me_y);
    assert(state.ModeAuto == session.setup_controls.mode_auto);
    assert(memcmp(state.modeLevels, &session.setup_controls.mode_level,
                  sizeof state.modeLevels) == 0);
    assert(state.fd_50F6_0C26 == session.world.world_ticks);
    assert(state.fd_50F6_0508[0] == session.world.map_view_x &&
           state.fd_50F6_0508[1] == session.world.map_view_y);
    assert(state.fd_3D57_07BE == -1);
    assert(state.fd_50F6_0FB6 == 22 && state.fd_50F6_0FFA == 19);
    assert(state.fd_50F6_105E == -1);
    assert(sim_session_from_recovered_state(&session, &state) ==
           SIM_RECOVERED_BRIDGE_OK);
    assert(session.nest_runtime.invalidate_right == 22 &&
           session.nest_runtime.invalidate_bottom == 19);
    session.world.source_state_07be = 0;
    session.nest_runtime.alarm_indicator = 0;
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(session.world.source_state_07be == 0 &&
           session.nest_runtime.alarm_indicator == 0);
    assert(session.modal_mode_105e == -1);
    sim_session_close(&session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    static SimSession session;
    static RecoveredState state;
    static RecoveredState defaults;
    RecoveredBindingFrame frame;
    const SimRecoveredProjectionEntry *manifest;
    const char *const *unmapped;
    size_t manifest_count, unmapped_count;
    fill_session(&session);
    recovered_state_init(&defaults);
    assert(sim_recovered_state_from_session(&state, &session) == SIM_RECOVERED_BRIDGE_OK);
    assert(memcmp(state.MapA, session.world.tiles.surface, sizeof state.MapA) == 0);
    assert(memcmp(state.LifeA, session.world.life_a, sizeof state.LifeA) == 0);
    assert(memcmp(state.MapB, session.world.tiles.nest_b, sizeof state.MapB) == 0);
    assert(memcmp(state.PherMapRT, session.world.pheromone_r_trail, sizeof state.PherMapRT) == 0);
    assert(memcmp(state.AlistX, session.world.ants_a.x, sizeof state.AlistX) == 0);
    assert(memcmp(state.BlistS, session.world.ants_b.state, sizeof state.BlistS) == 0);
    assert(state.ListIndexA == 0x123 && state.ListIndexB == 0x234 && state.ListIndexR == 0x345);
    assert(state.fd_50F6_0A0A[63] == 0x3456);
    assert(state.fd_50F6_04F4 == 42 && state.fd_3D57_0828 == 3);
    assert(state.BAntsEaten == 0x1234567 && state.RAntsEaten == 0x7654321);
    assert(state.SCorpseBase == 4 && state.fd_50F6_0476 == 73);
    assert(state.fd_50F6_037C[99] == session.spider.corpse_x[99]);
    assert(state.fd_50F6_0404[99] == session.spider.corpse_y[99]);
    assert(state.fd_50F6_0F12 == 0x1234 && state.fd_50F6_0F34 == 0x5678);
    assert(state.g_5AAC == session.sine_q15 && state.g_5AAC[3] == 0x4321);
    assert(memcmp(state.fd_3E1D_C89F, session.world.pheromone_aux,
                  sizeof state.fd_3E1D_C89F) == 0);
    assert(state.fd_50F6_0228 == session.nest_runtime.theme_index);
    assert(state.fd_50F6_1068 == session.nest_runtime.dug_b_x_sum);
    assert(state.fd_50F6_104E == session.world.source_state_104e);
    assert(state.fd_3D57_07BE == session.world.source_state_07be);
    assert(state.fd_50F6_0C26 == 0x12345678u);
    assert(state.fd_50F6_105E == 17);
    assert(state.fd_3D57_07CC[0] == 2);
    assert(state.fd_3D57_07CC[1] == 21 && state.fd_3D57_07CC[2] == 7);
    assert(state.fd_3D57_07CC[3] == 0 && state.fd_3D57_07CC[4] == -1);
    assert(state.fd_3E1D_0000[0][0] == 0x7788);
    assert(state.CurGndTileID == 1000);
    assert(state.fd_3D57_0164[11][8] == 2);
    assert(state.fd_3D57_006C[0] == defaults.fd_3D57_006C[0]);
    assert(session.world.random_seed_grid[0] == 0x7788);

    /* The source alias is a single view, not a second field. */
    recovered_bind_begin(&frame, &state);
    fd_3D57_07A8[5] = 0x1357;
    assert(fd_3D57_07B2 == 0x1357);
    fd_3D57_07B2 = 0x2468;
    recovered_bind_end(&frame, &state);
    assert(state.fd_3D57_07A8[5] == 0x2468);

    /* Recovered code changes are projected back; unowned session storage is
     * retained and private recovered fields are not normalized by export. */
    state.MapA[11][12] = 0x9a;
    state.CurGndTileID = 1008;
    state.fd_3D57_0164[11][8] = 3;
    state.fd_3E1D_0000[0][0] = 0x1888;
    state.fd_3E1D_C89F[0][0] = 0x3c;
    state.fd_50F6_0C26 = 0x23456789u;
    state.fd_50F6_105E = -1;
    state.fd_3D57_07CC[0] = 1;
    state.fd_3D57_07CC[1] = 7;
    state.LifeR[13][14] = 0x8b;
    state.fd_50F6_0A0A[63] = 0x7654;
    state.BAntsEaten = 0x1020304;
    state.fd_50F6_037C[22] = 0xe1;
    state.fd_50F6_0404[22] = 0x1e;
    state.fd_3D57_006C[0] = 0x5d;
    assert(sim_session_from_recovered_state(&session, &state) == SIM_RECOVERED_BRIDGE_OK);
    assert(session.world.tiles.surface[11][12] == 0x9a);
    assert(session.world.life_r[13][14] == 0x8b);
    assert(session.setup_state.history_series[9][63] == 0x7654);
    assert(session.setup_state.black_ants_eaten == 0x1020304);
    assert(session.spider.corpse_x[22] == 0xe1 && session.spider.corpse_y[22] == 0x1e);
    assert(session.world.random_seed_grid[0] == 0x1888);
    assert(session.world.pheromone_aux[0][0] == 0x3c);
    assert(session.world.current_ground_tile_id == 1008);
    assert(session.world.build_red[11][8] == 3);
    assert(session.world.lifetime_graph[9][8] == 3);
    assert(session.world.simulation_speed_index == 1);
    assert(session.world.tick_count_delays[0] == 7);
    assert(session.world.world_ticks == 0x23456789u);
    assert(session.modal_mode_105e == -1);
    assert(session.world.build_black[0][0] == 0x7a);
    assert(session.nest_runtime.entrance_b_surface_x == 0x345);
    assert(state.fd_3D57_006C[0] == 0x5d);
    assert(session.spider.sine_q15 == session.sine_q15);
    assert(sim_recovered_session_rng(&session) == &session.rng);

    manifest = sim_recovered_projection_manifest(&manifest_count);
    unmapped = sim_recovered_unmapped_new_game_writes(&unmapped_count);
    assert(manifest != NULL && manifest_count > 100);
    assert(unmapped != NULL && unmapped_count >= 1);
    assert(strstr(manifest[manifest_count - 1].recovered_view, "one alias") != NULL);
    {
        size_t i;
        for (i = 0; i < unmapped_count; ++i)
            assert(strstr(unmapped[i], "fd_50F6_0516") == NULL);
    }
    assert(sim_recovered_state_from_session(NULL, &session) == SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT);
    assert(sim_session_from_recovered_state(&session, NULL) == SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT);
    state.MapA[0][0] = 0xee;
    session.world.source_state_104e = 1;
    assert(sim_recovered_state_from_session(&state, &session) ==
           SIM_RECOVERED_BRIDGE_INCONSISTENT_MIRROR);
    assert(state.MapA[0][0] == 0xee);
    {
        SimSession missing_view = SIM_SESSION_INITIALIZER;
        missing_view.new_game_ready = 1;
        state.MapA[0][0] = 0x52;
        assert(sim_recovered_state_from_session(&state, &missing_view) ==
               SIM_RECOVERED_BRIDGE_VIEW_UNAVAILABLE);
        assert(state.MapA[0][0] == 0x52);
    }
    test_resource_backed_new_game();
    return 0;
}
