#include "session_bridge.h"

#include "../../game/session.h"
#include "../../ui_model/windows/game_view.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

static void test_resource_new_game_projection(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimSession session = SIM_SESSION_INITIALIZER;
    const SimNewGameConfig config = {1, 0, 11, 8};
    PortableGameViewState view_state = {0, -1, 0, 0, 0, 0};
    PortableGameView view;
    RecoveredState state, initialized;
    int16_t ideal_tail[3];
    int16_t mode_me_data;
    static const uint16_t source_mode_defaults[3] = {39321, 13107, 13107};
    static const uint16_t source_caste_defaults[3] = {0, 39321, 26214};
    static const uint16_t source_mode_presets[12] = {
        39321, 13107, 13107, 65535, 0, 0, 0, 65535, 0, 0, 0, 65535
    };
    static const uint16_t source_caste_presets[12] = {
        0, 39321, 26214, 32767, 16383, 16383, 0, 65535, 0, 0, 0, 65535
    };

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(sim_session_init(&session, "assets", &database, &registry) ==
           SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x12345678u, 0x87654321u) ==
           SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(portable_window_registry_load(&registry,
           PORTABLE_GAME_VIEW_WINDOW_ID) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_recalculate(&registry,
           PORTABLE_GAME_VIEW_WINDOW_ID, NULL) == PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_game_view_resolve(&registry, &session.world, &view_state,
                                      &view) == PORTABLE_GAME_VIEW_OK);
    /* These are the original DOS initControls values from
     * setup_differential_report.json for the same HCEGANT windows/resources. */
    assert(memcmp(&session.setup_controls.mode_defaults, source_mode_defaults,
                  sizeof source_mode_defaults) == 0);
    assert(memcmp(&session.setup_controls.caste_defaults, source_caste_defaults,
                  sizeof source_caste_defaults) == 0);
    assert(memcmp(session.setup_controls.mode_levels, source_mode_presets,
                  sizeof source_mode_presets) == 0);
    assert(memcmp(session.setup_controls.caste_levels, source_caste_presets,
                  sizeof source_caste_presets) == 0);
    assert(session.setup_controls.mode_auto == 1 &&
           session.setup_controls.caste_auto == 1 &&
           session.setup_controls.mode_enabled == 1 &&
           session.setup_controls.caste_enabled == 1);
    assert(session.setup_controls.state_0370 == -1 &&
           session.setup_controls.state_024e == -1);
    assert(session.setup_controls.mode_rect.left == 136 &&
           session.setup_controls.mode_rect.top == 344 &&
           session.setup_controls.mode_rect.right == 247 &&
           session.setup_controls.mode_rect.bottom == 440);
    assert(session.setup_controls.caste_rect.left == 392 &&
           session.setup_controls.caste_rect.top == 344 &&
           session.setup_controls.caste_rect.right == 501 &&
           session.setup_controls.caste_rect.bottom == 440);
    assert(session.setup_controls.mode_point.x == 192 &&
           session.setup_controls.mode_point.y == 381);
    assert(session.setup_controls.caste_point.x == 436 &&
           session.setup_controls.caste_point.y == 438);
    assert(session.setup_controls.mode_width == 111 &&
           session.setup_controls.mode_height == 96 &&
           session.setup_controls.caste_width == 109 &&
           session.setup_controls.caste_height == 96);
    assert(session.setup_controls.knob_width == 14 &&
           session.setup_controls.knob_height == 14);

    recovered_state_init(&initialized);
    state = initialized;
    memcpy(ideal_tail, state.IdealCaste + 4, sizeof ideal_tail);
    mode_me_data = state.ModeMe;
    assert(sim_recovered_state_from_session(&state, &session) ==
           SIM_RECOVERED_BRIDGE_OK);

    assert(state.ModeAuto == session.setup_controls.mode_auto);
    assert(state.CasteAuto == session.setup_controls.caste_auto);
    assert(state.fd_50F6_0468 == session.setup_controls.mode_enabled);
    assert(state.fd_3D57_07EA == session.setup_controls.caste_enabled);
    assert(state.fd_50F6_0370 == session.setup_controls.state_0370);
    assert(state.fd_50F6_024E == session.setup_controls.state_024e);
    assert(state.modeLevels[0] == session.setup_controls.mode_level.frac);
    assert(state.modeLevels[1] == session.setup_controls.mode_level.mid);
    assert(state.modeLevels[2] == session.setup_controls.mode_level.weight);
    assert(state.casteLevels[0] == session.setup_controls.caste_level.frac);
    assert(state.casteLevels[1] == session.setup_controls.caste_level.mid);
    assert(state.casteLevels[2] == session.setup_controls.caste_level.weight);
    assert(memcmp(state.fd_3D57_080A, &session.setup_controls.mode_defaults,
                  sizeof state.fd_3D57_080A) == 0);
    assert(memcmp(state.fd_3D57_07EC, &session.setup_controls.caste_defaults,
                  sizeof state.fd_3D57_07EC) == 0);
    assert(memcmp(state.fd_3D57_0810, session.setup_controls.mode_levels,
                  sizeof state.fd_3D57_0810) == 0);
    assert(memcmp(state.fd_3D57_07F2, session.setup_controls.caste_levels,
                  sizeof state.fd_3D57_07F2) == 0);
    assert(memcmp(state.IdealCaste, session.setup_controls.ideal_caste,
                  sizeof session.setup_controls.ideal_caste) == 0);
    assert(memcmp(state.IdealCaste + 4, ideal_tail, sizeof ideal_tail) == 0);
    assert(state.knobSize.x == session.setup_controls.knob_width);
    assert(state.knobSize.y == session.setup_controls.knob_height);
    assert(state.fd_50F6_3816.leftX == session.setup_controls.mode_rect.left);
    assert(state.fd_50F6_3816.apexY == session.setup_controls.mode_rect.top);
    assert(state.fd_50F6_3816.rightX == session.setup_controls.mode_rect.right);
    assert(state.fd_50F6_3816.leftY == session.setup_controls.mode_rect.bottom);
    assert(state.fd_50F6_3822.leftX == session.setup_controls.caste_rect.left);
    assert(state.fd_50F6_3822.apexY == session.setup_controls.caste_rect.top);
    assert(state.fd_50F6_3822.rightX == session.setup_controls.caste_rect.right);
    assert(state.fd_50F6_3822.leftY == session.setup_controls.caste_rect.bottom);
    assert(state.fd_50F6_0358.x == session.setup_controls.mode_point.x);
    assert(state.fd_50F6_0358.y == session.setup_controls.mode_point.y);
    assert(state.fd_50F6_022E.x == session.setup_controls.caste_point.x);
    assert(state.fd_50F6_022E.y == session.setup_controls.caste_point.y);
    assert(state.fd_50F6_37F6 == session.controls[SIM_SETUP_MODE_CONTROL].animation_resource);
    assert(state.fd_50F6_37F2 == session.controls[SIM_SETUP_CASTE_CONTROL].animation_resource);
    assert(state.ModeMe == mode_me_data);

    /* Simulate a source-owned control mutation and verify every projected
     * field returns to the corresponding typed session view. */
    state.ModeAuto = 7;
    state.CasteAuto = 8;
    state.fd_50F6_0468 = 9;
    state.fd_3D57_07EA = 10;
    state.fd_50F6_0370 = 11;
    state.fd_50F6_024E = 12;
    state.modeLevels[0] = (uint16_t)0x1111;
    state.modeLevels[1] = (uint16_t)0x2222;
    state.modeLevels[2] = (uint16_t)0x3333;
    state.casteLevels[0] = (uint16_t)0x4444;
    state.casteLevels[1] = (uint16_t)0x5555;
    state.casteLevels[2] = (uint16_t)0x6666;
    state.fd_3D57_080A[0] = (uint16_t)0x1212;
    state.fd_3D57_080A[1] = (uint16_t)0x2323;
    state.fd_3D57_080A[2] = (uint16_t)0x3434;
    state.fd_3D57_07EC[0] = (uint16_t)0x4545;
    state.fd_3D57_07EC[1] = (uint16_t)0x5656;
    state.fd_3D57_07EC[2] = (uint16_t)0x6767;
    state.fd_3D57_0810[3] = (uint16_t)0x7878;
    state.fd_3D57_07F2[3] = (uint16_t)0x8989;
    state.IdealCaste[0] = 21;
    state.IdealCaste[1] = 22;
    state.IdealCaste[2] = 23;
    state.IdealCaste[3] = 24;
    state.knobSize.x = 15;
    state.knobSize.y = 16;
    state.fd_50F6_3816.apexX = 60;
    state.fd_50F6_3816.apexY = 20;
    state.fd_50F6_3816.leftX = 10;
    state.fd_50F6_3816.leftY = 100;
    state.fd_50F6_3816.rightX = 110;
    state.fd_50F6_3816.rightY = 100;
    state.fd_50F6_3822.apexX = 245;
    state.fd_50F6_3822.apexY = 30;
    state.fd_50F6_3822.leftX = 200;
    state.fd_50F6_3822.leftY = 100;
    state.fd_50F6_3822.rightX = 290;
    state.fd_50F6_3822.rightY = 100;
    state.fd_50F6_0358.x = 70;
    state.fd_50F6_0358.y = 90;
    state.fd_50F6_022E.x = 260;
    state.fd_50F6_022E.y = 80;
    state.triWidth = 90;
    state.triWidthL = 45;
    state.triWidthR = 45;
    state.triHeight = 70;
    state.fd_50F6_382E = 0x12345678;
    state.fd_50F6_37F6 = NULL;
    state.fd_50F6_37F2 = NULL;
    assert(sim_session_from_recovered_state(&session, &state) ==
           SIM_RECOVERED_BRIDGE_OK);

    assert(session.setup_controls.mode_auto == 7);
    assert(session.setup_controls.caste_auto == 8);
    assert(session.setup_controls.mode_enabled == 9);
    assert(session.setup_controls.caste_enabled == 10);
    assert(session.setup_controls.state_0370 == 11);
    assert(session.setup_controls.state_024e == 12);
    assert(session.setup_controls.mode_level.frac == 0x1111);
    assert(session.setup_controls.mode_level.mid == 0x2222);
    assert(session.setup_controls.mode_level.weight == 0x3333);
    assert(session.setup_controls.caste_level.frac == 0x4444);
    assert(session.setup_controls.caste_level.mid == 0x5555);
    assert(session.setup_controls.caste_level.weight == 0x6666);
    assert(session.setup_controls.mode_defaults.frac == 0x1212);
    assert(session.setup_controls.caste_defaults.weight == 0x6767);
    assert(session.setup_controls.mode_levels[1].frac == 0x7878);
    assert(session.setup_controls.caste_levels[1].frac == 0x8989);
    assert(session.setup_controls.ideal_caste[0] == 21 &&
           session.setup_controls.ideal_caste[3] == 24);
    assert(session.setup_controls.knob_width == 15 &&
           session.setup_controls.knob_height == 16);
    assert(session.setup_controls.mode_rect.left == 10 &&
           session.setup_controls.mode_rect.top == 20 &&
           session.setup_controls.mode_rect.right == 110 &&
           session.setup_controls.mode_rect.bottom == 100);
    assert(session.setup_controls.caste_rect.left == 200 &&
           session.setup_controls.caste_rect.top == 30 &&
           session.setup_controls.caste_rect.right == 290 &&
           session.setup_controls.caste_rect.bottom == 100);
    assert(session.setup_controls.mode_point.x == 70 &&
           session.setup_controls.mode_point.y == 90);
    assert(session.setup_controls.caste_point.x == 260 &&
           session.setup_controls.caste_point.y == 80);
    assert(session.setup_controls.caste_slope == 0x12345678);
    assert(session.controls[SIM_SETUP_MODE_CONTROL].rectangle.left == 10);
    assert(session.controls[SIM_SETUP_CASTE_CONTROL].rectangle.right == 290);
    assert(memcmp(state.IdealCaste + 4, ideal_tail, sizeof ideal_tail) == 0);

    sim_session_close(&session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    test_resource_new_game_projection();
    return 0;
}
