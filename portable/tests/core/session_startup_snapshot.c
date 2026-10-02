#include "../../game/session.h"
#include "../../game/recovered/session_bridge.h"
#include "recovered_state.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

static int emit(const char *name, const void *data, unsigned size)
{
    unsigned short name_size = (unsigned short)strlen(name);
    if (fwrite(&name_size, sizeof name_size, 1, stdout) != 1 ||
        fwrite(&size, sizeof size, 1, stdout) != 1 ||
        fwrite(name, 1, name_size, stdout) != name_size ||
        fwrite(data, 1, size, stdout) != size)
        return 0;
    return 1;
}

#define EMIT(name, expr) do { \
    if (!emit((name), &(expr), (unsigned)sizeof(expr))) return 3; \
} while (0)
#define EMIT_N(name, expr, n) do { \
    if (!emit((name), (expr), (unsigned)(n))) return 3; \
} while (0)

int main(int argc, char **argv)
{
    PortableDatabase database = { 0 };
    PortableWindowRegistry registry = { 0 };
    SimSession *session = (SimSession *)calloc(1, sizeof *session);
    RecoveredState *state = (RecoveredState *)calloc(1, sizeof *state);
    SimNewGameConfig config = { 1, 0, 11, 8 };
    SimRecoveredBridgeStatus bridge_status;
#ifdef _WIN32
    (void)_setmode(_fileno(stdout), _O_BINARY);
#endif
    if (argc != 2 || argv == NULL || session == NULL || state == NULL)
        return 2;
    if (portable_db_open(&database, "assets/HCEGANT") != PORTABLE_DB_OK ||
        portable_window_registry_init(&registry, &database, 0) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        portable_window_registry_load(&registry, 0) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        portable_window_registry_recalculate(&registry, 0, NULL) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        sim_session_init(session, "assets", &database, &registry) !=
            SIM_SESSION_OK ||
        sim_session_seed_startup(session, 0x12345678u, 0x87654321u) !=
            SIM_SESSION_OK ||
        sim_session_new_game(session, &config) != SIM_SESSION_OK) {
        fprintf(stderr, "native session initialization failed\n");
        return 4;
    }
    bridge_status = sim_recovered_state_from_session(state, session);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        fprintf(stderr, "native session bridge failed: %d\n", bridge_status);
        return 5;
    }

    /* Emit the source-identified simulation contract in little-endian native
     * representation. Pointer-valued DATA entries and UI-only handles are
     * deliberately excluded. */
    EMIT_N("MapA", state->MapA, sizeof state->MapA);
    EMIT_N("MapB", state->MapB, sizeof state->MapB);
    EMIT_N("MapR", state->MapR, sizeof state->MapR);
    EMIT_N("ExitMapB", state->ExitMapB, sizeof state->ExitMapB);
    EMIT_N("ExitMapR", state->ExitMapR, sizeof state->ExitMapR);
    EMIT_N("LifeA", state->LifeA, sizeof state->LifeA);
    EMIT_N("LifeB", state->LifeB, sizeof state->LifeB);
    EMIT_N("LifeR", state->LifeR, sizeof state->LifeR);
    EMIT_N("PherMapA", state->PherMapA, sizeof state->PherMapA);
    EMIT_N("fd_3E1D_C89F", state->fd_3E1D_C89F, sizeof state->fd_3E1D_C89F);
    EMIT_N("PherMapBN", state->PherMapBN, sizeof state->PherMapBN);
    EMIT_N("PherMapBT", state->PherMapBT, sizeof state->PherMapBT);
    EMIT_N("PherMapRN", state->PherMapRN, sizeof state->PherMapRN);
    EMIT_N("PherMapRT", state->PherMapRT, sizeof state->PherMapRT);
    EMIT_N("HoleMapB", state->HoleMapB, sizeof state->HoleMapB);
    EMIT_N("HoleMapR", state->HoleMapR, sizeof state->HoleMapR);
    EMIT_N("AlistX", state->AlistX, 1000);
    EMIT_N("AlistY", state->AlistY, 1000);
    EMIT_N("AlistM", state->AlistM, 1000);
    EMIT_N("AlistT", state->AlistT, 1000);
    EMIT_N("AlistS", state->AlistS, 1000);
    EMIT_N("BlistX", state->BlistX, 500);
    EMIT_N("BlistY", state->BlistY, 500);
    EMIT_N("BlistM", state->BlistM, 500);
    EMIT_N("BlistT", state->BlistT, 500);
    EMIT_N("BlistS", state->BlistS, 500);
    EMIT_N("RlistX", state->RlistX, 500);
    EMIT_N("RlistY", state->RlistY, 500);
    EMIT_N("RlistM", state->RlistM, 500);
    EMIT_N("RlistT", state->RlistT, 500);
    EMIT_N("RlistS", state->RlistS, 500);
    EMIT("ListIndexA", state->ListIndexA);
    EMIT("ListIndexB", state->ListIndexB);
    EMIT("ListIndexR", state->ListIndexR);
    EMIT("fd_3E1D_0000", state->fd_3E1D_0000);
    EMIT("fd_3D57_00A4", state->fd_3D57_00A4);
    EMIT("fd_3D57_0164", state->fd_3D57_0164);
    EMIT_N("fd_3D57_0184", state->fd_3D57_0164[2], 10 * 16);
    EMIT("fd_50F6_035E", state->fd_50F6_035E);
    EMIT("fd_50F6_036C", state->fd_50F6_036C);
    EMIT("fd_50F6_0AFA", state->fd_50F6_0AFA);
    EMIT("fd_50F6_0AEC", state->fd_50F6_0AEC);
    EMIT("fd_50F6_0EB6", state->fd_50F6_0EB6);
    EMIT("fd_50F6_0508", state->fd_50F6_0508);
    EMIT("fd_50F6_0596", state->fd_50F6_0596);
    EMIT("fd_50F6_06A6", state->fd_50F6_06A6);
    EMIT("fd_50F6_072E", state->fd_50F6_072E);
    EMIT("fd_50F6_0EAC", state->fd_50F6_0EAC);
    EMIT("MapPlane", state->MapPlane);
    EMIT("MePlane", state->MePlane);
    EMIT("MeLocX", state->MeLocX);
    EMIT("MeLocY", state->MeLocY);
    EMIT("fd_50F6_04C2", state->fd_50F6_04C2);
    EMIT("fd_3D57_02B4", state->fd_3D57_02B4);
    EMIT("fd_3D57_02B8", state->fd_3D57_02B8);
    EMIT("fd_50F6_0496", state->fd_50F6_0496);
    EMIT("MeHealth", state->MeHealth);
    EMIT("fd_50F6_0FBA", state->fd_50F6_0FBA);
    EMIT("fd_50F6_0FFE", state->fd_50F6_0FFE);
    EMIT("fd_50F6_0354", state->fd_50F6_0354);
    EMIT("fd_50F6_0400", state->fd_50F6_0400);
    EMIT("fd_50F6_0376", state->fd_50F6_0376);
    EMIT("fd_50F6_0366", state->fd_50F6_0366);
    EMIT("fd_50F6_07CA", state->fd_50F6_07CA);
    EMIT("fd_50F6_07BC", state->fd_50F6_07BC);
    EMIT_N("fd_3D57_07C8", state->fd_3D57_07C8, 2);
    EMIT("fd_3D57_07CC", state->fd_3D57_07CC);
    EMIT("YardMode", state->YardMode);
    EMIT("FoodB", state->FoodB);
    EMIT("FoodR", state->FoodR);
    EMIT("HealthB", state->HealthB);
    EMIT("HealthR", state->HealthR);
    EMIT("Cycle", state->Cycle);
    EMIT("fd_50F6_0C26", state->fd_50F6_0C26);
    EMIT("fd_50F6_105E", state->fd_50F6_105E);
    EMIT("fd_50F6_1040", state->fd_50F6_1040);
    EMIT("fd_50F6_104E", state->fd_50F6_104E);
    EMIT("fd_3D57_07BE", state->fd_3D57_07BE);
    EMIT("fd_50F6_0214", state->fd_50F6_0214);
    EMIT("fd_50F6_0204", state->fd_50F6_0204);
    EMIT("fd_50F6_0228", state->fd_50F6_0228);
    EMIT("fd_50F6_0478", state->fd_50F6_0478);
    EMIT("fd_50F6_0504", state->fd_50F6_0504);
    EMIT("fd_3D57_0C44", state->fd_3D57_0C44);
    EMIT("fd_3D57_0C18", state->fd_3D57_0C18);
    EMIT("fd_3D57_0C16", state->fd_3D57_0C16);
    EMIT("fd_3D57_0C14", state->fd_3D57_0C14);
    EMIT("fd_50F6_049A", state->fd_50F6_049A);
    EMIT("fd_3D57_0C22", state->fd_3D57_0C22);
    EMIT("fd_50F6_0242", state->fd_50F6_0242);
    EMIT("fd_50F6_0472", state->fd_50F6_0472);
    EMIT("fd_50F6_09FA", state->fd_50F6_09FA);
    EMIT("fd_50F6_0A00", state->fd_50F6_0A00);
    EMIT("fd_50F6_0A06", state->fd_50F6_0A06);
    EMIT("fd_50F6_04E2", state->fd_50F6_04E2);
    EMIT("fd_50F6_047C", state->fd_50F6_047C);
    EMIT("fd_50F6_048A", state->fd_50F6_048A);
    EMIT("fd_50F6_0F78", state->MeHealth);
    EMIT("BpopT", state->BpopT);
    EMIT("RpopT", state->RpopT);
    EMIT("CurExpTool", state->CurExpTool);
    EMIT("DROPdir", state->DROPdir);
    EMIT("CurGndTileID", state->CurGndTileID);
    EMIT("world_current_ground_tile_id", session->world.current_ground_tile_id);
    EMIT("TERRAINset", state->TERRAINset);
    EMIT("fd_50F6_0480", state->fd_50F6_0480);
    EMIT("SowX", state->SowX);
    EMIT("SowY", state->SowY);
    EMIT("SowDir", state->SowDir);
    EMIT("SowSave", state->SowSave);
    EMIT("LionIndex", state->LionIndex);
    EMIT("InitialLions", state->InitialLions);
    EMIT("AntsEatenByLions", state->AntsEatenByLions);
    EMIT("LionListX", state->LionListX);
    EMIT("LionListY", state->LionListY);
    EMIT("LionListM", state->LionListM);
    EMIT("LionListS", state->LionListS);
    EMIT("LionListT", state->LionListT);
    EMIT("PillarMap", state->PillarMap);
    EMIT("PillarState", state->PillarState);
    EMIT("PillarX", state->PillarX);
    EMIT("PillarY", state->PillarY);
    EMIT("PillarSeg", state->PillarSeg);
    EMIT("PillDir", state->PillDir);
    EMIT("SCorpseBase", state->SCorpseBase);
    EMIT("SpidBurpCnt", state->SpidBurpCnt);
    EMIT("EatCnt", state->EatCnt);
    EMIT("Scycle", state->Scycle);
    EMIT("Scycle2", state->Scycle2);
    EMIT("SpidRevenge", state->SpidRevenge);
    EMIT("SMode", state->SMode);
    EMIT("Starg", state->Starg);
    EMIT("StargLife", state->StargLife);
    EMIT("SuserX", state->SuserX);
    EMIT("SuserY", state->SuserY);
    EMIT("fd_50F6_0476", state->fd_50F6_0476);
    EMIT("fd_50F6_037C", state->fd_50F6_037C);
    EMIT("fd_50F6_0404", state->fd_50F6_0404);
    EMIT("fd_50F6_0F12", state->fd_50F6_0F12);
    EMIT("fd_50F6_0F34", state->fd_50F6_0F34);
    EMIT("fd_50F6_0F0C", state->fd_50F6_0F0C);
    EMIT("fd_50F6_1004", state->fd_50F6_1004);
    EMIT("fd_3D57_0C12", state->fd_3D57_0C12);
    EMIT("fd_50F6_06AC", state->fd_50F6_06AC);
    EMIT("fd_50F6_10DE", state->fd_50F6_10DE);
    EMIT("fd_50F6_10E0", state->fd_50F6_10E0);
    EMIT("rng_s", session->rng.s_state);
    EMIT("rng_c", session->rng.c_state);
    {
        int16_t native_rand[32];
        uint16_t native_s[32];
        unsigned i;
        for (i = 0; i < 32; ++i) {
            (void)sim_rng_r(&session->rng, 32767, &native_rand[i]);
            (void)sim_rng_s1(&session->rng, 32767, &native_s[i]);
        }
        EMIT("rng_r_next", native_rand);
        EMIT("rng_s_next", native_s);
    }
    (void)argc;
    sim_session_close(session);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
    free(state);
    free(session);
    return 0;
}
