#include "session_bridge.h"
#include "../../ui_model/windows/game_view.h"

#include <string.h>

#define MAP(src, dst, view) { src, dst, view }
static const SimRecoveredProjectionEntry projection[] = {
    MAP("fd_3E1D_0180 / MapA", "world.tiles.surface", "MapA"),
    MAP("fd_3D57_0164[12][16] / fd_3D57_0184[10][16]", "world.build_red / world.lifetime_graph", "one 192-byte backing; 0184 aliases rows 2..11"),
    MAP("CurGndTileID", "world.current_ground_tile_id", "CurGndTileID"),
    MAP("fd_3E1D_0000[16][12]", "world.random_seed_grid", "fd_3E1D_0000"),
    MAP("fd_3E1D_2180 / MapB", "world.tiles.nest_b", "MapB"),
    MAP("fd_3E1D_3180 / MapR", "world.tiles.nest_r", "MapR"),
    MAP("fd_3E1D_4180 / ExitMapB", "world.exit_b", "ExitMapB"),
    MAP("fd_3E1D_5180 / ExitMapR", "world.exit_r", "ExitMapR"),
    MAP("fd_3E1D_6180 / LifeA", "world.life_a", "LifeA"),
    MAP("fd_3E1D_8180 / LifeB", "world.life_b", "LifeB"),
    MAP("fd_3E1D_9180 / LifeR", "world.life_r", "LifeR"),
    MAP("fd_3E1D_D09F / PherMapA", "world.pheromone_a", "PherMapA"),
    MAP("fd_3E1D_C89F", "world.pheromone_aux", "fd_3E1D_C89F"),
    MAP("fd_3E1D_E09F / PherMapBN", "world.pheromone_b_nest", "PherMapBN"),
    MAP("fd_3E1D_E89F / PherMapBT", "world.pheromone_b_trail", "PherMapBT"),
    MAP("fd_3E1D_F09F / PherMapRN", "world.pheromone_r_nest", "PherMapRN"),
    MAP("fd_4DA7_0000 / PherMapRT", "world.pheromone_r_trail", "PherMapRT"),
    MAP("fd_3D57_0224 / HoleMapB", "world.hole_b", "HoleMapB"),
    MAP("fd_3D57_0264 / HoleMapR", "world.hole_r", "HoleMapR"),
    MAP("fd_3E1D_A180 / AlistX", "world.ants_a.x", "AlistX"),
    MAP("fd_3E1D_A569 / AlistY", "world.ants_a.y", "AlistY"),
    MAP("fd_3E1D_A952 / AlistM", "world.ants_a.mode", "AlistM"),
    MAP("fd_3E1D_AD3B / AlistT", "world.ants_a.type", "AlistT"),
    MAP("fd_3E1D_B124 / AlistS", "world.ants_a.state", "AlistS"),
    MAP("fd_3E1D_B50D / BlistX", "world.ants_b.x", "BlistX"),
    MAP("fd_3E1D_B702 / BlistY", "world.ants_b.y", "BlistY"),
    MAP("fd_3E1D_B8F7 / BlistM", "world.ants_b.mode", "BlistM"),
    MAP("fd_3E1D_BAEC / BlistT", "world.ants_b.type", "BlistT"),
    MAP("fd_3E1D_BCE1 / BlistS", "world.ants_b.state", "BlistS"),
    MAP("fd_3E1D_BED6 / RlistX", "world.ants_r.x", "RlistX"),
    MAP("fd_3E1D_C0CB / RlistY", "world.ants_r.y", "RlistY"),
    MAP("fd_3E1D_C2C0 / RlistM", "world.ants_r.mode", "RlistM"),
    MAP("fd_3E1D_C4B5 / RlistT", "world.ants_r.type", "RlistT"),
    MAP("fd_3E1D_C6AA / RlistS", "world.ants_r.state", "RlistS"),
    MAP("LionListX", "world.ant_lions[].x", "LionListX"),
    MAP("LionListY", "world.ant_lions[].y", "LionListY"),
    MAP("LionListM", "world.ant_lions[].mode", "LionListM"),
    MAP("LionListS", "world.ant_lions[].seconds", "LionListS"),
    MAP("LionListT", "world.ant_lions[].timer", "LionListT"),
    MAP("SowX", "world.sow_x", "SowX"),
    MAP("SowY", "world.sow_y", "SowY"),
    MAP("SowDir", "world.sow_direction", "SowDir"),
    MAP("SowSave", "world.sow_saved_tile", "SowSave"),
    MAP("PillarMap", "world.pillar_map", "PillarMap"),
    MAP("PillarState", "world.pillar_state", "PillarState"),
    MAP("PillarX", "world.pillar_x", "PillarX"),
    MAP("PillarY", "world.pillar_y", "PillarY"),
    MAP("PillarSeg", "world.pillar_segment", "PillarSeg"),
    MAP("PillDir", "world.pillar_direction", "PillDir"),
    MAP("fd_3D57_02B4[2]", "world.queen_black_x/y", "fd_3D57_02B4"),
    MAP("fd_3D57_02B8[2]", "world.queen_red_x/y", "fd_3D57_02B8"),
    MAP("fd_50F6_032E / MapPlane", "world.map_plane", "MapPlane"),
    MAP("fd_50F6_0EAC", "world.scenario", "fd_50F6_0EAC"),
    MAP("fd_3D57_07C8", "world.selected_map_plane", "fd_3D57_07C8"),
    MAP("YardMode", "world.yard_mode", "YardMode"),
    MAP("fd_3D57_07CC[0] + fd_3D57_07CE[4]", "world.simulation_speed_index + world.tick_count_delays[4]", "canonical packed 07CC[0..6]; speed[0], deadlines[1..4], source DATA tail[5..6]"),
    MAP("fd_50F6_048C / MePlane", "world.current_ant_plane", "MePlane"),
    MAP("fd_50F6_047C / MeLocX", "world.me_x", "MeLocX"),
    MAP("fd_50F6_048A / MeLocY", "world.me_y", "MeLocY"),
    MAP("fd_50F6_04C2", "world.me_type", "fd_50F6_04C2"),
    MAP("fd_50F6_0496", "world.me_direction", "fd_50F6_0496"),
    MAP("fd_50F6_0F78 / MeHealth", "world.me_health", "MeHealth"),
    MAP("fd_50F6_0FBA", "world.health_warning_threshold", "fd_50F6_0FBA"),
    MAP("fd_50F6_0FFE", "world.colony_health_warning_threshold", "fd_50F6_0FFE"),
    MAP("fd_50F6_0204", "world.source_state_0204", "fd_50F6_0204"),
    MAP("fd_50F6_0228", "nest_runtime.theme_index", "fd_50F6_0228"),
    MAP("fd_50F6_0214", "nest_runtime.theme_last_tick", "fd_50F6_0214"),
    MAP("fd_50F6_0224", "nest_runtime.dug_b_count", "fd_50F6_0224"),
    MAP("fd_50F6_1068", "nest_runtime.dug_b_x_sum", "fd_50F6_1068"),
    MAP("fd_50F6_1082", "nest_runtime.dug_b_y_sum", "fd_50F6_1082"),
    MAP("fd_50F6_10B2", "nest_runtime.dug_b_x_average", "fd_50F6_10B2"),
    MAP("fd_50F6_10C0", "nest_runtime.dug_b_y_average", "fd_50F6_10C0"),
    MAP("TilesDugR", "nest_runtime.dug_r_count", "TilesDugR"),
    MAP("fd_50F6_108E", "nest_runtime.dug_r_x_sum", "fd_50F6_108E"),
    MAP("fd_50F6_10A2", "nest_runtime.dug_r_y_sum", "fd_50F6_10A2"),
    MAP("fd_50F6_0200", "nest_runtime.dug_r_x_average", "fd_50F6_0200"),
    MAP("fd_50F6_020E", "nest_runtime.dug_r_y_average", "fd_50F6_020E"),
    MAP("fd_50F6_104E", "world.source_state_104e / nest_runtime.alarm_drop_state", "fd_50F6_104E"),
    MAP("fd_3D57_07BE", "world.source_state_07be / nest_runtime.alarm_indicator", "fd_3D57_07BE"),
    MAP("fd_50F6_0FB6", "nest_runtime.invalidate_right", "active window-0/object-4 logical column bound from resolved resource geometry"),
    MAP("fd_50F6_0FFA", "nest_runtime.invalidate_bottom", "active window-0/object-4 logical row bound from resolved resource geometry"),
    MAP("fd_50F6_0478", "world.source_state_0478", "fd_50F6_0478"),
    MAP("fd_50F6_0504", "world.source_state_0504", "fd_50F6_0504"),
    MAP("fd_3D57_0C44", "world.source_state_0c44", "fd_3D57_0C44"),
    MAP("fd_3D57_0C18", "world.source_state_0c18", "fd_3D57_0C18"),
    MAP("fd_3D57_0C16", "world.health_force_full", "fd_3D57_0C16"),
    MAP("fd_3D57_0C14", "world.source_state_0c14", "fd_3D57_0C14"),
    MAP("fd_50F6_049A", "world.source_state_049a", "fd_50F6_049A"),
    MAP("fd_3D57_0C22", "world.source_state_0c22", "fd_3D57_0C22"),
    MAP("fd_50F6_04C4", "world.source_state_04c4", "fd_50F6_04C4"),
    MAP("fd_50F6_0242", "world.source_counter_0242", "fd_50F6_0242"),
    MAP("fd_50F6_0472", "world.source_counter_0472", "fd_50F6_0472"),
    MAP("fd_50F6_09FA", "world.source_counter_09fa", "fd_50F6_09FA"),
    MAP("fd_50F6_0A00", "world.source_counter_0a00", "fd_50F6_0A00"),
    MAP("fd_50F6_0A06", "world.player_mode", "fd_50F6_0A06"),
    MAP("fd_50F6_035E", "world.queens_black", "fd_50F6_035E"),
    MAP("fd_50F6_036C", "world.queens_red", "fd_50F6_036C"),
    MAP("fd_50F6_04E2", "world.player_death_plane", "fd_50F6_04E2"),
    MAP("fd_50F6_0354", "world.population_new_game", "fd_50F6_0354"),
    MAP("fd_50F6_0400", "world.population_lifetime_graph_enabled", "fd_50F6_0400"),
    MAP("fd_50F6_0376", "world.population_selection_pending", "fd_50F6_0376"),
    MAP("fd_50F6_0366", "world.population_selection_colony", "fd_50F6_0366"),
    MAP("fd_50F6_07CA[2]", "world.lifetime_graph_preset", "fd_50F6_07CA"),
    MAP("fd_50F6_07BC[2]", "world.requested_preset_x/y", "fd_50F6_07BC"),
    MAP("fd_50F6_0596[2]", "world.map_focus[0]", "fd_50F6_0596"),
    MAP("fd_50F6_06A6[2]", "world.map_focus[1]", "fd_50F6_06A6"),
    MAP("fd_50F6_072E[2]", "world.map_focus[2]", "fd_50F6_072E"),
    MAP("fd_50F6_0AEC[6]", "world.population_black", "fd_50F6_0AEC"),
    MAP("fd_50F6_0AFA[6]", "world.population_red", "fd_50F6_0AFA"),
    MAP("fd_50F6_0EB6[32]", "world.ants_by_type", "fd_50F6_0EB6"),
    MAP("BpopT", "world.total_population_black", "BpopT"),
    MAP("RpopT", "world.total_population_red", "RpopT"),
    MAP("FoodB", "world.food_black", "FoodB"),
    MAP("FoodR", "world.food_red", "FoodR"),
    MAP("HealthB", "world.health_black", "HealthB"),
    MAP("HealthR", "world.health_red", "HealthR"),
    MAP("Cycle", "world.cycle", "Cycle"),
    MAP("fd_50F6_0C26", "world.world_ticks", "fd_50F6_0C26 (zeroed by RandYard, incremented once per DoAntSim)"),
    MAP("fd_50F6_105E", "session.modal_mode_105e", "RandYard sets -1; main-loop gate and TargetAnt/StartLifeTransfer transitions"),
    MAP("CurExpTool", "world.current_experiment_tool", "CurExpTool"),
    MAP("DROPdir", "world.drop_direction", "DROPdir"),
    MAP("fd_50F6_0508[2]", "world.map_view_x/y", "fd_50F6_0508"),
    MAP("fd_50F6_1040", "world.food_added_terrain", "fd_50F6_1040"),
    MAP("fd_50F6_0378 / ModeAuto", "setup_controls.mode_auto", "ModeAuto"),
#ifndef SIMANT_ENABLE_CONTROL_INIT_NEXT4
    MAP("modeLevels", "setup_controls.mode_level", "three-word current mode triangle"),
    MAP("ModeMe", "setup_controls.mode_current", "ModeMe"),
#else
    MAP("modeLevels", "setup_controls.mode_level", "modeLevels[3]"),
    MAP("casteLevels", "setup_controls.caste_level", "casteLevels[3]"),
    MAP("fd_3D57_080A[3]", "setup_controls.mode_defaults", "fd_3D57_080A"),
    MAP("fd_3D57_07EC[3]", "setup_controls.caste_defaults", "fd_3D57_07EC"),
    MAP("fd_3D57_0810[12]", "setup_controls.mode_levels[4]", "fd_3D57_0810"),
    MAP("fd_3D57_07F2[12]", "setup_controls.caste_levels[4]", "fd_3D57_07F2"),
    MAP("CasteAuto", "setup_controls.caste_auto", "CasteAuto"),
    MAP("fd_50F6_0468", "setup_controls.mode_enabled", "fd_50F6_0468"),
    MAP("fd_3D57_07EA", "setup_controls.caste_enabled", "fd_3D57_07EA"),
    MAP("fd_50F6_0370", "setup_controls.state_0370", "fd_50F6_0370"),
    MAP("fd_50F6_024E", "setup_controls.state_024e", "fd_50F6_024E"),
    MAP("IdealCaste[0..3]", "setup_controls.ideal_caste[4]", "IdealCaste[0..3]; [4..6] retain source DATA"),
    MAP("knobSize", "setup_controls.knob_width/height", "knobSize.x/y"),
    MAP("fd_50F6_3816", "setup_controls.mode_rect", "mode rect -> InitTriVars TriPoints"),
    MAP("fd_50F6_3822", "setup_controls.caste_rect", "caste rect -> InitTriVars TriPoints"),
    MAP("fd_50F6_0358", "setup_controls.mode_point", "SetTriLatPoint mode output"),
    MAP("fd_50F6_022E", "setup_controls.caste_point", "SetTriLatPoint caste output"),
    MAP("triWidth/triWidthL/triWidthR/triHeight", "setup_controls.caste_width/height", "last InitTriVars call is caste"),
    MAP("fd_50F6_382E", "setup_controls.caste_slope", "last InitTriVars call is caste"),
    MAP("fd_50F6_37F6", "session.controls[mode].animation_resource", "borrowed actual animation resource or NULL"),
    MAP("fd_50F6_37F2", "session.controls[caste].animation_resource", "borrowed actual animation resource or NULL"),
#endif
#ifndef SIMANT_ENABLE_CONTROL_INIT_NEXT4
    MAP("IdealCaste[4]", "setup_controls.ideal_caste", "IdealCaste"),
#endif
    MAP("BAntsEaten", "setup_state.black_ants_eaten", "BAntsEaten"),
    MAP("RAntsEaten", "setup_state.red_ants_eaten", "RAntsEaten"),
    MAP("fd_50F6_0F30", "setup_state.counter_0f30", "fd_50F6_0F30"),
    MAP("fd_50F6_0EFC", "setup_state.counter_0efc", "fd_50F6_0EFC"),
    MAP("fd_50F6_0516[64]", "setup_state.history_series[0]", "fd_50F6_0516"),
    MAP("fd_50F6_05A0[64]", "setup_state.history_series[1]", "fd_50F6_05A0"),
    MAP("fd_50F6_0626[64]", "setup_state.history_series[2]", "fd_50F6_0626"),
    MAP("fd_50F6_06AE[64]", "setup_state.history_series[3]", "fd_50F6_06AE"),
    MAP("fd_50F6_073C[64]", "setup_state.history_series[4]", "fd_50F6_073C"),
    MAP("fd_50F6_07CE[64]", "setup_state.history_series[5]", "fd_50F6_07CE"),
    MAP("fd_50F6_0856[64]", "setup_state.history_series[6]", "fd_50F6_0856"),
    MAP("fd_50F6_08F0[64]", "setup_state.history_series[7]", "fd_50F6_08F0"),
    MAP("fd_50F6_0970[64]", "setup_state.history_series[8]", "fd_50F6_0970"),
    MAP("fd_50F6_0A0A[64]", "setup_state.history_series[9]", "fd_50F6_0A0A"),
    MAP("fd_50F6_04F4", "setup_state.history_start", "fd_50F6_04F4"),
    MAP("fd_3D57_0828", "setup_state.graph_selection", "fd_3D57_0828"),
    MAP("fd_50F6_0FBC", "setup_state.history_counter_0fbc", "fd_50F6_0FBC"),
    MAP("fd_50F6_0F3E", "setup_state.history_counter_0f3e", "fd_50F6_0F3E"),
    MAP("fd_50F6_0FC2", "setup_state.history_counter_0fc2", "fd_50F6_0FC2"),
    MAP("fd_50F6_1000", "setup_state.history_counter_1000", "fd_50F6_1000"),
    MAP("fd_50F6_0ADA", "setup_state.value_0ada", "fd_50F6_0ADA"),
    MAP("fd_50F6_0A90", "setup_state.value_0a90", "fd_50F6_0A90"),
    MAP("fd_50F6_0AC4", "setup_state.value_0ac4", "fd_50F6_0AC4"),
    MAP("fd_50F6_0A9E", "setup_state.value_0a9e", "fd_50F6_0A9E"),
    MAP("fd_50F6_0AC8", "setup_state.value_0ac8", "fd_50F6_0AC8"),
    MAP("fd_50F6_109C", "yard_scene.boy_message_count", "fd_50F6_109C"),
    MAP("fd_3D57_0C2C", "yard_scene.boy_x", "fd_3D57_0C2C"),
    MAP("fd_3D57_0C2E", "yard_scene.boy_y", "fd_3D57_0C2E"),
    MAP("fd_3D57_0C34", "yard_scene.boy_turn_count", "fd_3D57_0C34"),
    MAP("fd_3D57_0C2A", "yard_scene.boy_wait", "fd_3D57_0C2A"),
    MAP("fd_50F6_107E", "yard_scene.bird_delay", "fd_50F6_107E"),
    MAP("fd_50F6_0220", "yard_scene.cat_delay", "fd_50F6_0220"),
    MAP("fd_50F6_04BE", "yard_scene.dog_x", "fd_50F6_04BE"),
    MAP("fd_50F6_04C6", "yard_scene.dog_y", "fd_50F6_04C6"),
    MAP("fd_3D57_0C30", "yard_scene.boy_direction", "fd_3D57_0C30"),
    MAP("fd_50F6_0624", "yard_scene.dog_turn_count", "fd_50F6_0624"),
    MAP("fd_50F6_10B0", "yard_scene.boy_message_on", "fd_50F6_10B0"),
    MAP("fd_50F6_0246", "yard_scene.boy_pixel_x", "fd_50F6_0246"),
    MAP("fd_50F6_023E", "yard_scene.boy_pixel_y", "fd_50F6_023E"),
    MAP("fd_3D57_0C32", "yard_scene.boy_frame", "fd_3D57_0C32"),
    MAP("fd_3D57_0C28", "yard_scene.boy_here", "fd_3D57_0C28"),
    MAP("fd_3D57_0C40", "yard_scene.boy_stand_count", "fd_3D57_0C40"),
    MAP("fd_3D57_0C46", "yard_scene.node_count", "fd_3D57_0C46"),
    MAP("fd_3D57_0C48", "yard_scene.node_number", "fd_3D57_0C48"),
    MAP("fd_50F6_10A0", "yard_scene.bird_on", "fd_50F6_10A0"),
    MAP("fd_50F6_022C", "yard_scene.cat_cycle", "fd_50F6_022C"),
    MAP("fd_50F6_0244", "yard_scene.cat_frame", "fd_50F6_0244"),
    MAP("fd_50F6_0254", "yard_scene.cat_on", "fd_50F6_0254"),
    MAP("fd_50F6_04E4", "yard_scene.dog_frame", "fd_50F6_04E4"),
    MAP("fd_50F6_0506", "yard_scene.dog_direction", "fd_50F6_0506"),
    MAP("fd_3D57_0C3E", "yard_scene.foot_here", "fd_3D57_0C3E"),
    MAP("fd_3D57_0C42", "yard_scene.foot_toggle", "fd_3D57_0C42"),
    MAP("fd_50F6_03E0", "yard_scene.foot_x", "fd_50F6_03E0"),
    MAP("fd_50F6_046A", "yard_scene.foot_y", "fd_50F6_046A"),
    MAP("fd_50F6_0470", "yard_scene.mower_x", "fd_50F6_0470"),
    MAP("fd_50F6_047A", "yard_scene.mower_y", "fd_50F6_047A"),
    MAP("fd_50F6_0202", "yard_scene.boy_is_mowing", "fd_50F6_0202"),
    MAP("fd_50F6_0352", "yard_scene.rain_on", "fd_50F6_0352"),
    MAP("fd_50F6_105C", "yard_scene.swarm_delay_black", "fd_50F6_105C"),
    MAP("fd_50F6_1066", "yard_scene.swarm_delay_red", "fd_50F6_1066"),
    MAP("fd_50F6_108C", "yard_scene.bird_frame", "fd_50F6_108C"),
    MAP("fd_50F6_0364", "yard_scene.last_colony_pop_black", "fd_50F6_0364"),
    MAP("fd_50F6_036E", "yard_scene.last_colony_pop_red", "fd_50F6_036E"),
    MAP("fd_50F6_10BC", "yard_scene.boy_message_offset", "fd_50F6_10BC"),
    MAP("fd_50F6_07C2", "yard_scene.yard_cycle", "fd_50F6_07C2"),
    MAP("SCorpseBase", "spider.corpse_base", "SCorpseBase"),
    MAP("SpidBurpCnt", "spider.burp_count", "SpidBurpCnt"),
    MAP("EatCnt", "spider.eat_count", "EatCnt"),
    MAP("Scycle", "spider.cycle", "Scycle"),
    MAP("Scycle2", "spider.cycle2", "Scycle2"),
    MAP("SpidRevenge", "spider.revenge", "SpidRevenge"),
    MAP("SMode", "spider.mode", "SMode"),
    MAP("Starg", "spider.target", "Starg"),
    MAP("StargLife", "spider.target_life", "StargLife"),
    MAP("SuserX", "spider.user_x", "SuserX"),
    MAP("SuserY", "spider.user_y", "SuserY"),
    MAP("fd_50F6_0476", "spider.corpse_index", "fd_50F6_0476"),
    MAP("fd_50F6_037C[100]", "spider.corpse_x", "fd_50F6_037C"),
    MAP("fd_50F6_0404[100]", "spider.corpse_y", "fd_50F6_0404"),
    MAP("fd_50F6_0F12", "spider.x16", "fd_50F6_0F12"),
    MAP("fd_50F6_0F34", "spider.y16", "fd_50F6_0F34"),
    MAP("fd_50F6_0F0C", "spider.target_mode", "fd_50F6_0F0C"),
    MAP("fd_50F6_1004", "spider.state_flag", "fd_50F6_1004"),
    MAP("fd_3D57_0C12", "spider.direction", "fd_3D57_0C12"),
    MAP("fd_50F6_06AC", "spider.aux_mode", "fd_50F6_06AC"),
    MAP("g_5AAC", "session.sine_q15", "native sine pointer"),
    MAP("fd_50F6_0B22", "session.sine_q15", "initStuff: retained kind-9 resource 1000, used by fracSIN/fracCOS"),
    MAP("AdviceStrs / fd_50F6_034C", "session.advice", "PrepareStrings: retained SHARED kind-4 tables 1020 and 1010; separately typed void* pointer backing"),
    MAP("fd_3D57_07A8[5] / fd_3D57_07B2", "options runtime state (not session-owned)", "one alias; source DATA defaults {0,1,1,1,1,0} survive fresh import; S11 menu and S09 save mutate it outside NewGame/this bridge"),
};
#undef MAP

#ifndef SIMANT_ENABLE_CONTROL_INIT_NEXT4
static const char *const unmapped_new_game_writes[] = {
    "RandYard/initControls writes CasteAuto, casteLevels, fd_3D57_07EA, fd_50F6_0468, fd_50F6_0370, fd_50F6_024E, mode/caste preset arrays, knobSize and triangle dimensions. SimSetupControls has typed views, but the current generated RecoveredState profile omits these globals, so they cannot be overlaid into this core state yet.",
};
#else
static const char *const unmapped_new_game_writes[] = {
    "The next4 RecoveredState profile projects the RandYard/initControls defaults, presets, levels, flags, geometry, ideal caste values and real session animation pointers. The TU-static preset selectors g_1B50/g_1B4E are not fields in this profile and are explicitly outside this bridge projection.",
};
#endif

const SimRecoveredProjectionEntry *sim_recovered_projection_manifest(size_t *count)
{
    if (count != NULL)
        *count = sizeof projection / sizeof projection[0];
    return projection;
}

const char *const *sim_recovered_unmapped_new_game_writes(size_t *count)
{
    if (count != NULL)
        *count = sizeof unmapped_new_game_writes / sizeof unmapped_new_game_writes[0];
    return unmapped_new_game_writes;
}

#define COPY_IN(dst, src) memcpy((dst), (src), sizeof(dst))
#define COPY_OUT(dst, src) memcpy((dst), (src), sizeof(dst))
/* Read/write the source module's first-word view while retaining the complete
 * initialized backing object in profiles with wider DATA table declarations. */
#define SOURCE_WORD(field) (*(int16_t *)(void *)&(field))

#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
static void controls_into_next4(RecoveredState *s, const SimSession *session)
{
    const SimSetupControls *c = &session->setup_controls;
    const SimSessionControlVisual *mode =
        &session->controls[SIM_SETUP_MODE_CONTROL];
    const SimSessionControlVisual *caste =
        &session->controls[SIM_SETUP_CASTE_CONTROL];
    int16_t half;

    s->ModeAuto = c->mode_auto;
    s->CasteAuto = c->caste_auto;
    s->fd_50F6_0468 = c->mode_enabled;
    s->fd_3D57_07EA = c->caste_enabled;
    s->fd_50F6_0370 = c->state_0370;
    s->fd_50F6_024E = c->state_024e;
    memcpy(s->modeLevels, &c->mode_level, sizeof s->modeLevels);
    memcpy(s->casteLevels, &c->caste_level, sizeof s->casteLevels);
    memcpy(s->fd_3D57_080A, &c->mode_defaults, sizeof s->fd_3D57_080A);
    memcpy(s->fd_3D57_07EC, &c->caste_defaults, sizeof s->fd_3D57_07EC);
    memcpy(s->fd_3D57_0810, c->mode_levels, sizeof s->fd_3D57_0810);
    memcpy(s->fd_3D57_07F2, c->caste_levels, sizeof s->fd_3D57_07F2);
    memcpy(s->IdealCaste, c->ideal_caste, sizeof c->ideal_caste);

    s->knobSize.x = c->knob_width;
    s->knobSize.y = c->knob_height;
    half = (int16_t)(c->mode_width >> 1);
    s->fd_50F6_3816.apexX = (int16_t)(half + c->mode_rect.left);
    s->fd_50F6_3816.apexY = c->mode_rect.top;
    s->fd_50F6_3816.leftX = c->mode_rect.left;
    s->fd_50F6_3816.leftY = c->mode_rect.bottom;
    s->fd_50F6_3816.rightX = c->mode_rect.right;
    s->fd_50F6_3816.rightY = c->mode_rect.bottom;
    half = (int16_t)(c->caste_width >> 1);
    s->fd_50F6_3822.apexX = (int16_t)(half + c->caste_rect.left);
    s->fd_50F6_3822.apexY = c->caste_rect.top;
    s->fd_50F6_3822.leftX = c->caste_rect.left;
    s->fd_50F6_3822.leftY = c->caste_rect.bottom;
    s->fd_50F6_3822.rightX = c->caste_rect.right;
    s->fd_50F6_3822.rightY = c->caste_rect.bottom;
    s->fd_50F6_0358.x = c->mode_point.x;
    s->fd_50F6_0358.y = c->mode_point.y;
    s->fd_50F6_022E.x = c->caste_point.x;
    s->fd_50F6_022E.y = c->caste_point.y;
    /* initControls calls mode Changed then caste Changed; the latter owns
     * the shared triangle width/height/slope globals at return. */
    s->triWidth = (uint16_t)c->caste_width;
    s->triWidthL = (uint16_t)(c->caste_width >> 1);
    s->triWidthR = (uint16_t)(c->caste_width >> 1);
    s->triHeight = (uint16_t)c->caste_height;
    s->fd_50F6_382E = c->caste_slope;
    s->fd_50F6_37F6 = mode->animation_resource;
    s->fd_50F6_37F2 = caste->animation_resource;
}

static void controls_from_next4(SimSession *session, const RecoveredState *s)
{
    SimSetupControls *c = &session->setup_controls;
    SimSetupRect *rect;

    c->mode_auto = s->ModeAuto;
    c->caste_auto = s->CasteAuto;
    c->mode_enabled = s->fd_50F6_0468;
    c->caste_enabled = s->fd_3D57_07EA;
    c->state_0370 = s->fd_50F6_0370;
    c->state_024e = s->fd_50F6_024E;
    memcpy(&c->mode_level, s->modeLevels, sizeof c->mode_level);
    memcpy(&c->caste_level, s->casteLevels, sizeof c->caste_level);
    memcpy(&c->mode_defaults, s->fd_3D57_080A, sizeof c->mode_defaults);
    memcpy(&c->caste_defaults, s->fd_3D57_07EC, sizeof c->caste_defaults);
    memcpy(c->mode_levels, s->fd_3D57_0810, sizeof c->mode_levels);
    memcpy(c->caste_levels, s->fd_3D57_07F2, sizeof c->caste_levels);
    memcpy(c->ideal_caste, s->IdealCaste, sizeof c->ideal_caste);
    c->knob_width = s->knobSize.x;
    c->knob_height = s->knobSize.y;

    rect = &c->mode_rect;
    rect->left = s->fd_50F6_3816.leftX;
    rect->top = s->fd_50F6_3816.apexY;
    rect->right = s->fd_50F6_3816.rightX;
    rect->bottom = s->fd_50F6_3816.leftY;
    c->mode_width = (int16_t)(rect->right - rect->left);
    c->mode_height = (int16_t)(rect->bottom - rect->top);
    c->mode_slope = c->mode_height != 0 ?
        (((int32_t)(c->mode_width >> 1) << 8) / c->mode_height) : 0;
    c->mode_point.x = s->fd_50F6_0358.x;
    c->mode_point.y = s->fd_50F6_0358.y;

    rect = &c->caste_rect;
    rect->left = s->fd_50F6_3822.leftX;
    rect->top = s->fd_50F6_3822.apexY;
    rect->right = s->fd_50F6_3822.rightX;
    rect->bottom = s->fd_50F6_3822.leftY;
    c->caste_width = (int16_t)(rect->right - rect->left);
    c->caste_height = (int16_t)(rect->bottom - rect->top);
    c->caste_slope = s->fd_50F6_382E;
    c->caste_point.x = s->fd_50F6_022E.x;
    c->caste_point.y = s->fd_50F6_022E.y;
    session->controls[SIM_SETUP_MODE_CONTROL].animation_resource =
        s->fd_50F6_37F6;
    session->controls[SIM_SETUP_CASTE_CONTROL].animation_resource =
        s->fd_50F6_37F2;
    session->controls[SIM_SETUP_MODE_CONTROL].rectangle = c->mode_rect;
    session->controls[SIM_SETUP_MODE_CONTROL].point = c->mode_point;
    session->controls[SIM_SETUP_CASTE_CONTROL].rectangle = c->caste_rect;
    session->controls[SIM_SETUP_CASTE_CONTROL].point = c->caste_point;
}
#endif

SimRecoveredBridgeStatus sim_recovered_state_from_session(
    RecoveredState *s, SimSession *session)
{
    int i;
    int16_t resolved_right, resolved_bottom;
    if (s == NULL || session == NULL)
        return SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT;
    resolved_right = session->nest_runtime.invalidate_right;
    resolved_bottom = session->nest_runtime.invalidate_bottom;
    if (session->new_game_ready) {
        PortableGameViewState view_state = {
            0, session->world.source_state_07be, 0, 0, 0, 0
        };
        PortableGameView view;
        if (portable_game_view_resolve(session->window_registry,
                                       &session->world,
                                       &view_state, &view) !=
            PORTABLE_GAME_VIEW_OK)
            return SIM_RECOVERED_BRIDGE_VIEW_UNAVAILABLE;
        /* InitEuMapOrigins uses the active Edit viewport, not guessed logical
         * dimensions. The resolver applies the resource rectangle's original
         * cell-size/partial-bottom-row formula and this is the same pair the
         * native window owner uses for map invalidation. */
        resolved_right = view.map.columns;
        resolved_bottom = view.map.rows;
    }
    if (session->world.source_state_104e != session->nest_runtime.alarm_drop_state ||
        session->world.source_state_07be != session->nest_runtime.alarm_indicator)
        return SIM_RECOVERED_BRIDGE_INCONSISTENT_MIRROR;
    if (session->new_game_ready) {
        session->nest_runtime.invalidate_right = resolved_right;
        session->nest_runtime.invalidate_bottom = resolved_bottom;
    }
    recovered_state_init(s);
    s->AdviceStrs = portable_advice_source_pointers(&session->advice,
        PORTABLE_ADVICE_TUTORIAL, NULL);
    s->fd_50F6_034C = portable_advice_source_pointers(&session->advice,
        PORTABLE_ADVICE_SHARED_MESSAGES, NULL);
    COPY_IN(s->fd_3E1D_0000, session->world.random_seed_grid);
    COPY_IN(s->fd_3D57_0164, session->world.build_red);
    s->CurGndTileID = session->world.current_ground_tile_id;
    COPY_IN(s->MapA, session->world.tiles.surface);
    COPY_IN(s->MapB, session->world.tiles.nest_b);
    COPY_IN(s->MapR, session->world.tiles.nest_r);
    COPY_IN(s->ExitMapB, session->world.exit_b);
    COPY_IN(s->ExitMapR, session->world.exit_r);
    COPY_IN(s->LifeA, session->world.life_a);
    COPY_IN(s->LifeB, session->world.life_b);
    COPY_IN(s->LifeR, session->world.life_r);
    COPY_IN(s->PherMapA, session->world.pheromone_a);
    COPY_IN(s->fd_3E1D_C89F, session->world.pheromone_aux);
    COPY_IN(s->PherMapBN, session->world.pheromone_b_nest);
    COPY_IN(s->PherMapBT, session->world.pheromone_b_trail);
    COPY_IN(s->PherMapRN, session->world.pheromone_r_nest);
    COPY_IN(s->PherMapRT, session->world.pheromone_r_trail);
    COPY_IN(s->HoleMapB, session->world.hole_b);
    COPY_IN(s->HoleMapR, session->world.hole_r);
    COPY_IN(s->AlistX, session->world.ants_a.x);
    COPY_IN(s->AlistY, session->world.ants_a.y);
    COPY_IN(s->AlistM, session->world.ants_a.mode);
    COPY_IN(s->AlistT, session->world.ants_a.type);
    COPY_IN(s->AlistS, session->world.ants_a.state);
    COPY_IN(s->BlistX, session->world.ants_b.x);
    COPY_IN(s->BlistY, session->world.ants_b.y);
    COPY_IN(s->BlistM, session->world.ants_b.mode);
    COPY_IN(s->BlistT, session->world.ants_b.type);
    COPY_IN(s->BlistS, session->world.ants_b.state);
    COPY_IN(s->RlistX, session->world.ants_r.x);
    COPY_IN(s->RlistY, session->world.ants_r.y);
    COPY_IN(s->RlistM, session->world.ants_r.mode);
    COPY_IN(s->RlistT, session->world.ants_r.type);
    COPY_IN(s->RlistS, session->world.ants_r.state);
    s->ListIndexA = session->world.ants_a.count;
    s->ListIndexB = session->world.ants_b.count;
    s->ListIndexR = session->world.ants_r.count;
    for (i = 0; i < 10; ++i) {
        s->LionListX[i] = session->world.ant_lions[i].x;
        s->LionListY[i] = session->world.ant_lions[i].y;
        s->LionListM[i] = session->world.ant_lions[i].mode;
        s->LionListS[i] = session->world.ant_lions[i].seconds;
        s->LionListT[i] = session->world.ant_lions[i].timer;
    }
    s->LionIndex = session->world.ant_lion_count;
    s->InitialLions = session->world.initial_ant_lions;
    s->AntsEatenByLions = session->world.ants_eaten_by_lions;
    COPY_IN(s->SowX, session->world.sow_x);
    COPY_IN(s->SowY, session->world.sow_y);
    COPY_IN(s->SowDir, session->world.sow_direction);
    COPY_IN(s->SowSave, session->world.sow_saved_tile);
    s->PillarState = session->world.pillar_state;
    s->PillarX = session->world.pillar_x;
    s->PillarY = session->world.pillar_y;
    s->PillarSeg = session->world.pillar_segment;
    s->PillDir = session->world.pillar_direction;
    COPY_IN(s->PillarMap, session->world.pillar_map);
    s->fd_50F6_035E = session->world.queens_black;
    s->fd_50F6_036C = session->world.queens_red;
    s->fd_3D57_02B4[0] = session->world.queen_black_x;
    s->fd_3D57_02B4[1] = session->world.queen_black_y;
    s->fd_3D57_02B8[0] = session->world.queen_red_x;
    s->fd_3D57_02B8[1] = session->world.queen_red_y;
    s->TERRAINset = session->world.tiles.terrain_set;
    s->MapPlane = session->world.map_plane;
    s->fd_50F6_0EAC = session->world.scenario;
    SOURCE_WORD(s->fd_3D57_07C8) = session->world.selected_map_plane;
    s->YardMode = session->world.yard_mode;
    s->fd_3D57_07CC[0] = session->world.simulation_speed_index;
    memcpy(&s->fd_3D57_07CC[1], session->world.tick_count_delays,
           sizeof session->world.tick_count_delays);
    s->MePlane = session->world.current_ant_plane;
    s->MeLocX = session->world.me_x;
    s->MeLocY = session->world.me_y;
    s->fd_50F6_04C2 = session->world.me_type;
    s->fd_50F6_0496 = session->world.me_direction;
    s->MeHealth = session->world.me_health;
    s->fd_50F6_0FBA = session->world.health_warning_threshold;
    s->fd_50F6_0FFE = session->world.colony_health_warning_threshold;
    s->fd_50F6_0204 = session->world.source_state_0204;
    s->fd_50F6_0478 = session->world.source_state_0478;
    s->fd_50F6_0504 = session->world.source_state_0504;
    s->fd_3D57_0C44 = session->world.source_state_0c44;
    s->fd_3D57_0C18 = session->world.source_state_0c18;
    s->fd_3D57_0C16 = session->world.health_force_full;
    s->fd_3D57_0C14 = session->world.source_state_0c14;
    s->fd_50F6_049A = session->world.source_state_049a;
    s->fd_3D57_0C22 = session->world.source_state_0c22;
    s->fd_50F6_0242 = session->world.source_counter_0242;
    s->fd_50F6_0472 = session->world.source_counter_0472;
    s->fd_50F6_09FA = session->world.source_counter_09fa;
    s->fd_50F6_0A00 = session->world.source_counter_0a00;
    s->fd_50F6_0A06 = session->world.player_mode;
    s->fd_50F6_04E2 = session->world.player_death_plane;
    s->fd_50F6_0354 = session->world.population_new_game;
    s->fd_50F6_0400 = session->world.population_lifetime_graph_enabled;
    s->fd_50F6_0376 = session->world.population_selection_pending;
    s->fd_50F6_0366 = session->world.population_selection_colony;
    s->fd_50F6_07CA[0] = session->world.lifetime_graph_preset[0];
    s->fd_50F6_07CA[1] = session->world.lifetime_graph_preset[1];
    s->fd_50F6_07BC[0] = session->world.requested_preset_x;
    s->fd_50F6_07BC[1] = session->world.requested_preset_y;
    COPY_IN(s->fd_50F6_0596, session->world.map_focus[0]);
    COPY_IN(s->fd_50F6_06A6, session->world.map_focus[1]);
    COPY_IN(s->fd_50F6_072E, session->world.map_focus[2]);
    COPY_IN(s->fd_50F6_0AEC, session->world.population_black);
    COPY_IN(s->fd_50F6_0AFA, session->world.population_red);
    COPY_IN(s->fd_50F6_0EB6, session->world.ants_by_type);
    s->BpopT = session->world.total_population_black;
    s->RpopT = session->world.total_population_red;
    s->FoodB = session->world.food_black;
    s->FoodR = session->world.food_red;
    s->HealthB = session->world.health_black;
    s->HealthR = session->world.health_red;
    s->Cycle = session->world.cycle;
    s->fd_50F6_0C26 = session->world.world_ticks;
    s->fd_50F6_105E = session->modal_mode_105e;
    s->CurExpTool = session->world.current_experiment_tool;
    s->DROPdir = session->world.drop_direction;
    s->fd_50F6_1040 = session->world.food_added_terrain;
    s->fd_50F6_0214 = session->nest_runtime.theme_last_tick;
    s->fd_50F6_0228 = session->nest_runtime.theme_index;
    s->fd_50F6_0224 = session->nest_runtime.dug_b_count;
    s->fd_50F6_1068 = session->nest_runtime.dug_b_x_sum;
    s->fd_50F6_1082 = session->nest_runtime.dug_b_y_sum;
    s->fd_50F6_10B2 = session->nest_runtime.dug_b_x_average;
    s->fd_50F6_10C0 = session->nest_runtime.dug_b_y_average;
    s->TilesDugR = session->nest_runtime.dug_r_count;
    s->fd_50F6_108E = session->nest_runtime.dug_r_x_sum;
    s->fd_50F6_10A2 = session->nest_runtime.dug_r_y_sum;
    s->fd_50F6_0200 = session->nest_runtime.dug_r_x_average;
    s->fd_50F6_020E = session->nest_runtime.dug_r_y_average;
    s->fd_50F6_104E = session->world.source_state_104e;
    s->fd_3D57_07BE = session->world.source_state_07be;
    s->fd_50F6_0FB6 = session->nest_runtime.invalidate_right;
    s->fd_50F6_0FFA = session->nest_runtime.invalidate_bottom;
    s->fd_50F6_0508[0] = session->world.map_view_x;
    s->fd_50F6_0508[1] = session->world.map_view_y;
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
    controls_into_next4(s, session);
#else
    s->ModeAuto = session->setup_controls.mode_auto;
    s->ModeMe = session->setup_controls.mode_current;
    COPY_IN(s->modeLevels, &session->setup_controls.mode_level);
    /* initControls owns four words; keep the remaining source DATA words. */
    memcpy(s->IdealCaste, session->setup_controls.ideal_caste,
           sizeof(session->setup_controls.ideal_caste));
#endif
    s->BAntsEaten = session->setup_state.black_ants_eaten;
    s->RAntsEaten = session->setup_state.red_ants_eaten;
    s->fd_50F6_0F30 = session->setup_state.counter_0f30;
    s->fd_50F6_0EFC = session->setup_state.counter_0efc;
    COPY_IN(s->fd_50F6_0516, session->setup_state.history_series[0]);
    COPY_IN(s->fd_50F6_05A0, session->setup_state.history_series[1]);
    COPY_IN(s->fd_50F6_0626, session->setup_state.history_series[2]);
    COPY_IN(s->fd_50F6_06AE, session->setup_state.history_series[3]);
    COPY_IN(s->fd_50F6_073C, session->setup_state.history_series[4]);
    COPY_IN(s->fd_50F6_07CE, session->setup_state.history_series[5]);
    COPY_IN(s->fd_50F6_0856, session->setup_state.history_series[6]);
    COPY_IN(s->fd_50F6_08F0, session->setup_state.history_series[7]);
    COPY_IN(s->fd_50F6_0970, session->setup_state.history_series[8]);
    COPY_IN(s->fd_50F6_0A0A, session->setup_state.history_series[9]);
    s->fd_50F6_04F4 = session->setup_state.history_start;
    s->fd_3D57_0828 = session->setup_state.graph_selection;
    s->fd_50F6_0FBC = session->setup_state.history_counter_0fbc;
    s->fd_50F6_0F3E = session->setup_state.history_counter_0f3e;
    s->fd_50F6_0FC2 = session->setup_state.history_counter_0fc2;
    s->fd_50F6_1000 = session->setup_state.history_counter_1000;
    s->fd_50F6_0ADA = session->setup_state.value_0ada;
    s->fd_50F6_0A90 = session->setup_state.value_0a90;
    s->fd_50F6_0AC4 = session->setup_state.value_0ac4;
    s->fd_50F6_0A9E = session->setup_state.value_0a9e;
    s->fd_50F6_0AC8 = session->setup_state.value_0ac8;
    /* Yard, spider and several setup controls are shared with original source
     * globals. Exact scalar copies are below; unrepresented controls remain
     * at recovered_state_init's source DATA values. */
    s->fd_50F6_109C = session->yard_scene.boy_message_count;
    s->fd_3D57_0C2C = session->yard_scene.boy_x;
    s->fd_3D57_0C2E = session->yard_scene.boy_y;
    s->fd_3D57_0C34 = session->yard_scene.boy_turn_count;
    s->fd_3D57_0C2A = session->yard_scene.boy_wait;
    s->fd_50F6_107E = session->yard_scene.bird_delay;
    s->fd_50F6_0220 = session->yard_scene.cat_delay;
    s->fd_50F6_04BE = session->yard_scene.dog_x;
    s->fd_50F6_04C6 = session->yard_scene.dog_y;
    s->fd_3D57_0C30 = session->yard_scene.boy_direction;
    s->fd_50F6_0624 = session->yard_scene.dog_turn_count;
    s->fd_50F6_10B0 = session->yard_scene.boy_message_on;
    s->fd_50F6_0246 = session->yard_scene.boy_pixel_x;
    s->fd_50F6_023E = session->yard_scene.boy_pixel_y;
    s->fd_3D57_0C32 = session->yard_scene.boy_frame;
    s->fd_3D57_0C28 = session->yard_scene.boy_here;
    s->fd_3D57_0C40 = session->yard_scene.boy_stand_count;
    s->fd_3D57_0C46 = session->yard_scene.node_count;
    s->fd_3D57_0C48 = session->yard_scene.node_number;
    s->fd_50F6_10A0 = session->yard_scene.bird_on;
    s->fd_50F6_022C = session->yard_scene.cat_cycle;
    s->fd_50F6_0244 = session->yard_scene.cat_frame;
    s->fd_50F6_0254 = session->yard_scene.cat_on;
    s->fd_50F6_04E4 = session->yard_scene.dog_frame;
    s->fd_50F6_0506 = session->yard_scene.dog_direction;
    s->fd_3D57_0C3E = session->yard_scene.foot_here;
    s->fd_3D57_0C42 = session->yard_scene.foot_toggle;
    s->fd_50F6_03E0 = session->yard_scene.foot_x;
    s->fd_50F6_046A = session->yard_scene.foot_y;
    s->fd_50F6_0470 = session->yard_scene.mower_x;
    s->fd_50F6_047A = session->yard_scene.mower_y;
    s->fd_50F6_0202 = session->yard_scene.boy_is_mowing;
    s->fd_50F6_0352 = session->yard_scene.rain_on;
    s->fd_50F6_105C = session->yard_scene.swarm_delay_black;
    s->fd_50F6_1066 = session->yard_scene.swarm_delay_red;
    s->fd_50F6_108C = session->yard_scene.bird_frame;
    s->fd_50F6_0364 = session->yard_scene.last_colony_pop_black;
    s->fd_50F6_036E = session->yard_scene.last_colony_pop_red;
    s->fd_50F6_10BC = session->yard_scene.boy_message_offset;
    s->fd_50F6_07C2 = session->yard_scene.yard_cycle;
    s->SCorpseBase = session->spider.corpse_base;
    s->SpidBurpCnt = session->spider.burp_count;
    s->EatCnt = session->spider.eat_count;
    s->Scycle = session->spider.cycle;
    s->Scycle2 = session->spider.cycle2;
    s->SpidRevenge = session->spider.revenge;
    s->SMode = session->spider.mode;
    s->Starg = session->spider.target;
    s->StargLife = session->spider.target_life;
    s->SuserX = session->spider.user_x;
    s->SuserY = session->spider.user_y;
    s->fd_50F6_0476 = session->spider.corpse_index;
    COPY_IN(s->fd_50F6_037C, session->spider.corpse_x);
    COPY_IN(s->fd_50F6_0404, session->spider.corpse_y);
    s->fd_50F6_0F12 = session->spider.x16;
    s->fd_50F6_0F34 = session->spider.y16;
    s->fd_50F6_0F0C = session->spider.target_mode;
    s->fd_50F6_1004 = session->spider.state_flag;
    s->fd_3D57_0C12 = session->spider.direction;
    s->fd_50F6_06AC = session->spider.aux_mode;
    s->g_5AAC = session->sine_q15;
    /* initStuff (root:075B) locks kind-9 object 1000 and retains its
     * table pointer. fracSIN/fracCOS use this separate source global. */
    s->fd_50F6_0B22 = session->sine_q15;
    return SIM_RECOVERED_BRIDGE_OK;
}

SimRecoveredBridgeStatus sim_session_from_recovered_state(
    SimSession *session, const RecoveredState *s)
{
    int i;
    if (session == NULL || s == NULL)
        return SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT;
    COPY_OUT(session->world.tiles.surface, s->MapA);
    COPY_OUT(session->world.random_seed_grid, s->fd_3E1D_0000);
    COPY_OUT(session->world.tiles.nest_b, s->MapB);
    COPY_OUT(session->world.tiles.nest_r, s->MapR);
    COPY_OUT(session->world.exit_b, s->ExitMapB);
    COPY_OUT(session->world.exit_r, s->ExitMapR);
    COPY_OUT(session->world.life_a, s->LifeA);
    COPY_OUT(session->world.life_b, s->LifeB);
    COPY_OUT(session->world.life_r, s->LifeR);
    COPY_OUT(session->world.pheromone_a, s->PherMapA);
    COPY_OUT(session->world.pheromone_aux, s->fd_3E1D_C89F);
    COPY_OUT(session->world.pheromone_b_nest, s->PherMapBN);
    COPY_OUT(session->world.pheromone_b_trail, s->PherMapBT);
    COPY_OUT(session->world.pheromone_r_nest, s->PherMapRN);
    COPY_OUT(session->world.pheromone_r_trail, s->PherMapRT);
    COPY_OUT(session->world.hole_b, s->HoleMapB);
    COPY_OUT(session->world.hole_r, s->HoleMapR);
    COPY_OUT(session->world.ants_a.x, s->AlistX);
    COPY_OUT(session->world.ants_a.y, s->AlistY);
    COPY_OUT(session->world.ants_a.mode, s->AlistM);
    COPY_OUT(session->world.ants_a.type, s->AlistT);
    COPY_OUT(session->world.ants_a.state, s->AlistS);
    COPY_OUT(session->world.ants_b.x, s->BlistX);
    COPY_OUT(session->world.ants_b.y, s->BlistY);
    COPY_OUT(session->world.ants_b.mode, s->BlistM);
    COPY_OUT(session->world.ants_b.type, s->BlistT);
    COPY_OUT(session->world.ants_b.state, s->BlistS);
    COPY_OUT(session->world.ants_r.x, s->RlistX);
    COPY_OUT(session->world.ants_r.y, s->RlistY);
    COPY_OUT(session->world.ants_r.mode, s->RlistM);
    COPY_OUT(session->world.ants_r.type, s->RlistT);
    COPY_OUT(session->world.ants_r.state, s->RlistS);
    session->world.ants_a.count = s->ListIndexA;
    session->world.ants_b.count = s->ListIndexB;
    session->world.ants_r.count = s->ListIndexR;
    for (i = 0; i < 10; ++i) {
        session->world.ant_lions[i].x = s->LionListX[i];
        session->world.ant_lions[i].y = s->LionListY[i];
        session->world.ant_lions[i].mode = s->LionListM[i];
        session->world.ant_lions[i].seconds = s->LionListS[i];
        session->world.ant_lions[i].timer = s->LionListT[i];
    }
    session->world.ant_lion_count = s->LionIndex;
    session->world.initial_ant_lions = s->InitialLions;
    session->world.ants_eaten_by_lions = s->AntsEatenByLions;
    COPY_OUT(session->world.sow_x, s->SowX);
    COPY_OUT(session->world.sow_y, s->SowY);
    COPY_OUT(session->world.sow_direction, s->SowDir);
    COPY_OUT(session->world.sow_saved_tile, s->SowSave);
    session->world.pillar_state = s->PillarState;
    session->world.pillar_x = s->PillarX;
    session->world.pillar_y = s->PillarY;
    session->world.pillar_segment = s->PillarSeg;
    session->world.pillar_direction = s->PillDir;
    COPY_OUT(session->world.pillar_map, s->PillarMap);
    session->world.queen_black_x = s->fd_3D57_02B4[0];
    session->world.queen_black_y = s->fd_3D57_02B4[1];
    session->world.queen_red_x = s->fd_3D57_02B8[0];
    session->world.queen_red_y = s->fd_3D57_02B8[1];
    session->world.queens_black = s->fd_50F6_035E;
    session->world.queens_red = s->fd_50F6_036C;
    session->world.tiles.terrain_set = s->TERRAINset;
    session->world.map_plane = s->MapPlane;
    session->world.scenario = s->fd_50F6_0EAC;
    session->world.selected_map_plane = SOURCE_WORD(s->fd_3D57_07C8);
    session->world.current_ground_tile_id = s->CurGndTileID;
    session->world.yard_mode = s->YardMode;
    session->world.simulation_speed_index = s->fd_3D57_07CC[0];
    memcpy(session->world.tick_count_delays, &s->fd_3D57_07CC[1],
           sizeof session->world.tick_count_delays);
    session->world.current_ant_plane = s->MePlane;
    session->world.me_x = s->MeLocX;
    session->world.me_y = s->MeLocY;
    session->world.me_type = s->fd_50F6_04C2;
    session->world.me_direction = s->fd_50F6_0496;
    session->world.me_health = s->MeHealth;
    session->world.health_warning_threshold = s->fd_50F6_0FBA;
    session->world.colony_health_warning_threshold = s->fd_50F6_0FFE;
    session->world.source_state_0204 = s->fd_50F6_0204;
    session->world.source_state_0478 = s->fd_50F6_0478;
    session->world.source_state_0504 = s->fd_50F6_0504;
    session->world.source_state_0c44 = s->fd_3D57_0C44;
    session->world.source_state_0c18 = s->fd_3D57_0C18;
    session->world.health_force_full = s->fd_3D57_0C16;
    session->world.source_state_0c14 = s->fd_3D57_0C14;
    session->world.source_state_049a = s->fd_50F6_049A;
    session->world.source_state_0c22 = s->fd_3D57_0C22;
    session->world.source_counter_0242 = s->fd_50F6_0242;
    session->world.source_counter_0472 = s->fd_50F6_0472;
    session->world.source_counter_09fa = s->fd_50F6_09FA;
    session->world.source_counter_0a00 = s->fd_50F6_0A00;
    session->world.player_mode = s->fd_50F6_0A06;
    session->world.player_death_plane = s->fd_50F6_04E2;
    session->world.population_new_game = s->fd_50F6_0354;
    session->world.population_lifetime_graph_enabled = s->fd_50F6_0400;
    session->world.population_selection_pending = s->fd_50F6_0376;
    session->world.population_selection_colony = s->fd_50F6_0366;
    session->world.lifetime_graph_preset[0] = s->fd_50F6_07CA[0];
    session->world.lifetime_graph_preset[1] = s->fd_50F6_07CA[1];
    session->world.requested_preset_x = s->fd_50F6_07BC[0];
    session->world.requested_preset_y = s->fd_50F6_07BC[1];
    COPY_OUT(session->world.map_focus[0], s->fd_50F6_0596);
    COPY_OUT(session->world.map_focus[1], s->fd_50F6_06A6);
    COPY_OUT(session->world.map_focus[2], s->fd_50F6_072E);
    COPY_OUT(session->world.population_black, s->fd_50F6_0AEC);
    COPY_OUT(session->world.population_red, s->fd_50F6_0AFA);
    COPY_OUT(session->world.ants_by_type, s->fd_50F6_0EB6);
    COPY_OUT(session->world.build_red, s->fd_3D57_0164);
    session->world.total_population_black = s->BpopT;
    session->world.total_population_red = s->RpopT;
    session->world.food_black = s->FoodB;
    session->world.food_red = s->FoodR;
    session->world.health_black = s->HealthB;
    session->world.health_red = s->HealthR;
    session->world.cycle = s->Cycle;
    session->world.world_ticks = s->fd_50F6_0C26;
    session->modal_mode_105e = s->fd_50F6_105E;
    session->world.current_experiment_tool = s->CurExpTool;
    session->world.drop_direction = s->DROPdir;
    session->world.food_added_terrain = s->fd_50F6_1040;
    session->nest_runtime.theme_last_tick = s->fd_50F6_0214;
    session->nest_runtime.theme_index = s->fd_50F6_0228;
    session->nest_runtime.dug_b_count = s->fd_50F6_0224;
    session->nest_runtime.dug_b_x_sum = s->fd_50F6_1068;
    session->nest_runtime.dug_b_y_sum = s->fd_50F6_1082;
    session->nest_runtime.dug_b_x_average = s->fd_50F6_10B2;
    session->nest_runtime.dug_b_y_average = s->fd_50F6_10C0;
    session->nest_runtime.dug_r_count = s->TilesDugR;
    session->nest_runtime.dug_r_x_sum = s->fd_50F6_108E;
    session->nest_runtime.dug_r_y_sum = s->fd_50F6_10A2;
    session->nest_runtime.dug_r_x_average = s->fd_50F6_0200;
    session->nest_runtime.dug_r_y_average = s->fd_50F6_020E;
    session->nest_runtime.alarm_drop_state = s->fd_50F6_104E;
    session->nest_runtime.alarm_indicator = s->fd_3D57_07BE;
    session->world.source_state_104e = s->fd_50F6_104E;
    session->world.source_state_07be = s->fd_3D57_07BE;
    session->nest_runtime.invalidate_right = s->fd_50F6_0FB6;
    session->nest_runtime.invalidate_bottom = s->fd_50F6_0FFA;
    session->world.map_view_x = s->fd_50F6_0508[0];
    session->world.map_view_y = s->fd_50F6_0508[1];
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
    controls_from_next4(session, s);
#else
    session->setup_controls.mode_auto = s->ModeAuto;
    session->setup_controls.mode_current = s->ModeMe;
    memcpy(&session->setup_controls.mode_level, s->modeLevels,
           sizeof session->setup_controls.mode_level);
    COPY_OUT(session->setup_controls.ideal_caste, s->IdealCaste);
#endif
    session->setup_state.black_ants_eaten = s->BAntsEaten;
    session->setup_state.red_ants_eaten = s->RAntsEaten;
    session->setup_state.counter_0f30 = s->fd_50F6_0F30;
    session->setup_state.counter_0efc = s->fd_50F6_0EFC;
    COPY_OUT(session->setup_state.history_series[0], s->fd_50F6_0516);
    COPY_OUT(session->setup_state.history_series[1], s->fd_50F6_05A0);
    COPY_OUT(session->setup_state.history_series[2], s->fd_50F6_0626);
    COPY_OUT(session->setup_state.history_series[3], s->fd_50F6_06AE);
    COPY_OUT(session->setup_state.history_series[4], s->fd_50F6_073C);
    COPY_OUT(session->setup_state.history_series[5], s->fd_50F6_07CE);
    COPY_OUT(session->setup_state.history_series[6], s->fd_50F6_0856);
    COPY_OUT(session->setup_state.history_series[7], s->fd_50F6_08F0);
    COPY_OUT(session->setup_state.history_series[8], s->fd_50F6_0970);
    COPY_OUT(session->setup_state.history_series[9], s->fd_50F6_0A0A);
    session->setup_state.history_start = s->fd_50F6_04F4;
    session->setup_state.graph_selection = s->fd_3D57_0828;
    session->setup_state.history_counter_0fbc = s->fd_50F6_0FBC;
    session->setup_state.history_counter_0f3e = s->fd_50F6_0F3E;
    session->setup_state.history_counter_0fc2 = s->fd_50F6_0FC2;
    session->setup_state.history_counter_1000 = s->fd_50F6_1000;
    session->setup_state.value_0ada = s->fd_50F6_0ADA;
    session->setup_state.value_0a90 = s->fd_50F6_0A90;
    session->setup_state.value_0ac4 = s->fd_50F6_0AC4;
    session->setup_state.value_0a9e = s->fd_50F6_0A9E;
    session->setup_state.value_0ac8 = s->fd_50F6_0AC8;
    session->yard_scene.boy_message_count = s->fd_50F6_109C;
    session->yard_scene.boy_x = s->fd_3D57_0C2C;
    session->yard_scene.boy_y = s->fd_3D57_0C2E;
    session->yard_scene.boy_turn_count = s->fd_3D57_0C34;
    session->yard_scene.boy_wait = s->fd_3D57_0C2A;
    session->yard_scene.bird_delay = s->fd_50F6_107E;
    session->yard_scene.cat_delay = s->fd_50F6_0220;
    session->yard_scene.dog_x = s->fd_50F6_04BE;
    session->yard_scene.dog_y = s->fd_50F6_04C6;
    session->yard_scene.boy_direction = s->fd_3D57_0C30;
    session->yard_scene.dog_turn_count = s->fd_50F6_0624;
    session->yard_scene.boy_message_on = s->fd_50F6_10B0;
    session->yard_scene.boy_pixel_x = s->fd_50F6_0246;
    session->yard_scene.boy_pixel_y = s->fd_50F6_023E;
    session->yard_scene.boy_frame = s->fd_3D57_0C32;
    session->yard_scene.boy_here = s->fd_3D57_0C28;
    session->yard_scene.boy_stand_count = s->fd_3D57_0C40;
    session->yard_scene.node_count = s->fd_3D57_0C46;
    session->yard_scene.node_number = s->fd_3D57_0C48;
    session->yard_scene.bird_on = s->fd_50F6_10A0;
    session->yard_scene.cat_cycle = s->fd_50F6_022C;
    session->yard_scene.cat_frame = s->fd_50F6_0244;
    session->yard_scene.cat_on = s->fd_50F6_0254;
    session->yard_scene.dog_frame = s->fd_50F6_04E4;
    session->yard_scene.dog_direction = s->fd_50F6_0506;
    session->yard_scene.foot_here = s->fd_3D57_0C3E;
    session->yard_scene.foot_toggle = s->fd_3D57_0C42;
    session->yard_scene.foot_x = s->fd_50F6_03E0;
    session->yard_scene.foot_y = s->fd_50F6_046A;
    session->yard_scene.mower_x = s->fd_50F6_0470;
    session->yard_scene.mower_y = s->fd_50F6_047A;
    session->yard_scene.boy_is_mowing = s->fd_50F6_0202;
    session->yard_scene.rain_on = s->fd_50F6_0352;
    session->yard_scene.swarm_delay_black = s->fd_50F6_105C;
    session->yard_scene.swarm_delay_red = s->fd_50F6_1066;
    session->yard_scene.bird_frame = s->fd_50F6_108C;
    session->yard_scene.last_colony_pop_black = s->fd_50F6_0364;
    session->yard_scene.last_colony_pop_red = s->fd_50F6_036E;
    session->yard_scene.boy_message_offset = s->fd_50F6_10BC;
    session->yard_scene.yard_cycle = s->fd_50F6_07C2;
    session->spider.corpse_base = s->SCorpseBase;
    session->spider.burp_count = s->SpidBurpCnt;
    session->spider.eat_count = s->EatCnt;
    session->spider.cycle = s->Scycle;
    session->spider.cycle2 = s->Scycle2;
    session->spider.revenge = s->SpidRevenge;
    session->spider.mode = s->SMode;
    session->spider.target = s->Starg;
    session->spider.target_life = s->StargLife;
    session->spider.user_x = s->SuserX;
    session->spider.user_y = s->SuserY;
    session->spider.corpse_index = s->fd_50F6_0476;
    COPY_OUT(session->spider.corpse_x, s->fd_50F6_037C);
    COPY_OUT(session->spider.corpse_y, s->fd_50F6_0404);
    session->spider.x16 = s->fd_50F6_0F12;
    session->spider.y16 = s->fd_50F6_0F34;
    session->spider.target_mode = s->fd_50F6_0F0C;
    session->spider.state_flag = s->fd_50F6_1004;
    session->spider.direction = s->fd_3D57_0C12;
    session->spider.aux_mode = s->fd_50F6_06AC;
    session->spider.sine_q15 = session->sine_q15;
    return SIM_RECOVERED_BRIDGE_OK;
}

SimRng *sim_recovered_session_rng(SimSession *session)
{
    return session != NULL ? &session->rng : NULL;
}

