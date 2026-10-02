#include "session_bridge.h"

#include <string.h>

#define MAP(src, dst, view) { src, dst, view }
static const SimRecoveredProjectionEntry projection[] = {
    MAP("fd_3E1D_0180 / MapA", "world.tiles.surface", "MapA"),
    MAP("fd_3E1D_2180 / MapB", "world.tiles.nest_b", "MapB"),
    MAP("fd_3E1D_3180 / MapR", "world.tiles.nest_r", "MapR"),
    MAP("fd_3E1D_4180 / ExitMapB", "world.exit_b", "ExitMapB"),
    MAP("fd_3E1D_5180 / ExitMapR", "world.exit_r", "ExitMapR"),
    MAP("fd_3E1D_6180 / LifeA", "world.life_a", "LifeA"),
    MAP("fd_3E1D_8180 / LifeB", "world.life_b", "LifeB"),
    MAP("fd_3E1D_9180 / LifeR", "world.life_r", "LifeR"),
    MAP("fd_3E1D_D09F / PherMapA", "world.pheromone_a", "PherMapA"),
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
    MAP("SowTab", "recovered DATA initializer", "SowTab"),
    MAP("PillarMap", "world.pillar_map", "PillarMap"),
    MAP("PillarState", "world.pillar_state", "PillarState"),
    MAP("PillarX", "world.pillar_x", "PillarX"),
    MAP("PillarY", "world.pillar_y", "PillarY"),
    MAP("PillarSeg", "world.pillar_segment", "PillarSeg"),
    MAP("PillDir", "world.pillar_direction", "PillDir"),
    MAP("fd_50F6_032E / MapPlane", "world.map_plane", "MapPlane"),
    MAP("fd_50F6_0EAC", "world.scenario", "fd_50F6_0EAC"),
    MAP("fd_50F6_048C / MePlane", "world.current_ant_plane", "MePlane"),
    MAP("fd_50F6_047C / MeLocX", "world.me_x", "MeLocX"),
    MAP("fd_50F6_048A / MeLocY", "world.me_y", "MeLocY"),
    MAP("fd_50F6_04C2", "world.me_type", "fd_50F6_04C2"),
    MAP("fd_50F6_0496", "world.me_direction", "fd_50F6_0496"),
    MAP("fd_50F6_0F78 / MeHealth", "world.me_health", "MeHealth"),
    MAP("fd_50F6_0FBA", "world.health_warning_threshold", "fd_50F6_0FBA"),
    MAP("fd_50F6_0FFE", "world.colony_health_warning_threshold", "fd_50F6_0FFE"),
    MAP("fd_50F6_0378 / ModeAuto", "setup_controls.mode_auto", "ModeAuto"),
    MAP("ModeMe", "setup_controls.mode_current", "ModeMe"),
    MAP("IdealCaste[4]", "setup_controls.ideal_caste", "IdealCaste"),
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
    MAP("fd_3D57_07A8[5] / fd_3D57_07B2", "unmapped setup state", "fd_3D57_07A8[5] (07B2 alias)"),
};
#undef MAP

static const char *const unmapped_new_game_writes[] = {
    "fd_3D57_07A8[0..6], with fd_3D57_07B2 exactly aliasing element 5 (NewGame source control state; no session owner assigned)",
    "CasteAuto (fd_3D57_07E8), casteLevels (fd_50F6_0482), modeLevels (fd_50F6_049E), knob/triangle dimensions (fd_50F6_380E..3832), and fd_50F6_0370/fd_50F6_024E (setup controls only partly represented; no exact aggregate projection)",
    "fd_50F6_0200/0204/020E/0210/0212/0224/0226/0228/0232/0240/032C/0334/0354/0356/035E/0366/036C/0376/037A/03E2/0400/0402/04A4/04F2/0502/0504/0508/0510/0596/059E/06A6/06AA/072E/0736/073A/07BC/07C0/07C8/07CA/084E/0850/0852/08DA/08DC/08E2/08E8/08EC/09F0/09FA/0A00/0A02/0A06/0A8E/0AA0/0AA2/0AB6/0AC6/0AD6/0AE8/0AEC/0AF8/0AFA/0B12/0B1E/0B20/0B22/0C26/0C2A/0C38/0C3E/0D40/0D6C/0D72/0EF6/0EF8/0EFA/0F06/0F0C/0F0E/0F10/0F12/0F26/0F2E/0F34/0F44/0FB6/0FFA/1004/1006/1040/1044/104E/1058/105E/1068/1074/1082/108E/10A2/10A6/10AC/10B2/10BA/10C0/383A/3856/3858 (known source globals without exact typed session projection)",
};

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

SimRecoveredBridgeStatus sim_recovered_state_from_session(
    RecoveredState *s, SimSession *session)
{
    int i;
    if (s == NULL || session == NULL)
        return SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT;
    recovered_state_init(s);
    COPY_IN(s->MapA, session->world.tiles.surface);
    COPY_IN(s->MapB, session->world.tiles.nest_b);
    COPY_IN(s->MapR, session->world.tiles.nest_r);
    COPY_IN(s->ExitMapB, session->world.exit_b);
    COPY_IN(s->ExitMapR, session->world.exit_r);
    COPY_IN(s->LifeA, session->world.life_a);
    COPY_IN(s->LifeB, session->world.life_b);
    COPY_IN(s->LifeR, session->world.life_r);
    COPY_IN(s->PherMapA, session->world.pheromone_a);
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
    s->TERRAINset = session->world.tiles.terrain_set;
    s->MapPlane = session->world.map_plane;
    s->fd_50F6_0EAC = session->world.scenario;
    s->MePlane = session->world.current_ant_plane;
    s->MeLocX = session->world.me_x;
    s->MeLocY = session->world.me_y;
    s->fd_50F6_04C2 = session->world.me_type;
    s->fd_50F6_0496 = session->world.me_direction;
    s->MeHealth = session->world.me_health;
    s->fd_50F6_0FBA = session->world.health_warning_threshold;
    s->fd_50F6_0FFE = session->world.colony_health_warning_threshold;
    s->ModeAuto = session->setup_controls.mode_auto;
    s->ModeMe = session->setup_controls.mode_current;
    COPY_IN(s->IdealCaste, session->setup_controls.ideal_caste);
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
    return SIM_RECOVERED_BRIDGE_OK;
}

SimRecoveredBridgeStatus sim_session_from_recovered_state(
    SimSession *session, const RecoveredState *s)
{
    int i;
    if (session == NULL || s == NULL)
        return SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT;
    COPY_OUT(session->world.tiles.surface, s->MapA);
    COPY_OUT(session->world.tiles.nest_b, s->MapB);
    COPY_OUT(session->world.tiles.nest_r, s->MapR);
    COPY_OUT(session->world.exit_b, s->ExitMapB);
    COPY_OUT(session->world.exit_r, s->ExitMapR);
    COPY_OUT(session->world.life_a, s->LifeA);
    COPY_OUT(session->world.life_b, s->LifeB);
    COPY_OUT(session->world.life_r, s->LifeR);
    COPY_OUT(session->world.pheromone_a, s->PherMapA);
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
    session->world.tiles.terrain_set = s->TERRAINset;
    session->world.map_plane = s->MapPlane;
    session->world.scenario = s->fd_50F6_0EAC;
    session->world.current_ant_plane = s->MePlane;
    session->world.me_x = s->MeLocX;
    session->world.me_y = s->MeLocY;
    session->world.me_type = s->fd_50F6_04C2;
    session->world.me_direction = s->fd_50F6_0496;
    session->world.me_health = s->MeHealth;
    session->world.health_warning_threshold = s->fd_50F6_0FBA;
    session->world.colony_health_warning_threshold = s->fd_50F6_0FFE;
    session->setup_controls.mode_auto = s->ModeAuto;
    session->setup_controls.mode_current = s->ModeMe;
    COPY_OUT(session->setup_controls.ideal_caste, s->IdealCaste);
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

