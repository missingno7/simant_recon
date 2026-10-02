#include "recovered_state.h"
#include <string.h>
#include <stdlib.h>

static _Thread_local uint8_t recovered_keyboard_flags;
static _Thread_local int recovered_keyboard_flags_bound;
void recovered_keyboard_set_modifiers(uint8_t dos_flags)
{
    recovered_keyboard_flags = dos_flags;
    recovered_keyboard_flags_bound = 1;
}
uint8_t recovered_keyboard_modifiers(void)
{
    if (!recovered_keyboard_flags_bound) abort();
    return recovered_keyboard_flags;
}

_Thread_local void * * AdviceStrs;
_Thread_local uint8_t AlistM[1001];
_Thread_local uint8_t AlistS[1001];
_Thread_local uint8_t AlistT[1001];
_Thread_local uint8_t AlistX[1001];
_Thread_local uint8_t AlistY[1001];
_Thread_local int16_t AntsEatenByLions;
_Thread_local int32_t BAntsEaten;
_Thread_local int16_t Barrier;
_Thread_local uint8_t BlistM[501];
_Thread_local uint8_t BlistS[501];
_Thread_local uint8_t BlistT[501];
_Thread_local uint8_t BlistX[501];
_Thread_local uint8_t BlistY[501];
_Thread_local int16_t BpopT;
_Thread_local int8_t CasteModeTabB[16];
_Thread_local int16_t CasteTabB[4];
_Thread_local int16_t ChaseSpid;
_Thread_local int16_t CurExpTool;
_Thread_local int16_t CurGndTileID;
_Thread_local int16_t Cycle;
_Thread_local int16_t DROPdir;
_Thread_local int16_t DeathCnt;
_Thread_local int8_t Dx8[8];
_Thread_local int8_t Dx9[10];
_Thread_local int8_t Dy8[8];
_Thread_local int8_t Dy9[10];
_Thread_local int16_t EatCnt;
_Thread_local uint8_t ExitMapB[64][64];
_Thread_local uint8_t ExitMapR[64][64];
_Thread_local int8_t ExpSubStates[8];
_Thread_local int16_t FoodB;
_Thread_local int16_t FoodR;
_Thread_local int16_t FuzLocX;
_Thread_local int16_t FuzLocY;
_Thread_local int16_t HealthB;
_Thread_local int16_t HealthR;
_Thread_local uint8_t HoleMapB[64];
_Thread_local uint8_t HoleMapR[64];
_Thread_local int16_t IdealCaste[7];
_Thread_local int16_t InitialLions;
_Thread_local uint8_t LifeA[128][64];
_Thread_local uint8_t LifeB[64][64];
_Thread_local uint8_t LifeR[64][64];
_Thread_local int16_t LionIndex;
_Thread_local uint8_t LionListM[10];
_Thread_local uint8_t LionListS[10];
_Thread_local uint8_t LionListT[10];
_Thread_local uint8_t LionListX[10];
_Thread_local uint8_t LionListY[10];
_Thread_local int16_t ListIndexA;
_Thread_local int16_t ListIndexB;
_Thread_local int16_t ListIndexR;
_Thread_local uint8_t MapA[128][64];
_Thread_local uint8_t MapB[64][64];
_Thread_local int16_t MapPlane;
_Thread_local uint8_t MapR[64][64];
_Thread_local int16_t MeHealth;
_Thread_local int16_t MeLocX;
_Thread_local int16_t MeLocY;
_Thread_local int16_t MePlane;
_Thread_local int16_t ModeAuto;
_Thread_local int16_t ModeMe;
_Thread_local int16_t ModeTabB[24];
_Thread_local int8_t ModeTabSB[6][8];
_Thread_local int8_t ModeTabWB[6][8];
_Thread_local uint8_t PherMapA[64][32];
_Thread_local uint8_t PherMapBN[64][32];
_Thread_local uint8_t PherMapBT[64][32];
_Thread_local uint8_t PherMapRN[64][32];
_Thread_local uint8_t PherMapRT[64][32];
_Thread_local int16_t PillDir;
_Thread_local int16_t PillarMap[6];
_Thread_local int16_t PillarSeg;
_Thread_local int16_t PillarState;
_Thread_local int16_t PillarX;
_Thread_local int16_t PillarY;
_Thread_local int32_t RAntsEaten;
_Thread_local uint8_t RT3[18][3];
_Thread_local uint8_t RT5[30][5];
_Thread_local int16_t RedLocX;
_Thread_local int16_t RedLocY;
_Thread_local int16_t RedPlane;
_Thread_local uint8_t RlistM[501];
_Thread_local uint8_t RlistS[501];
_Thread_local uint8_t RlistT[501];
_Thread_local uint8_t RlistX[501];
_Thread_local uint8_t RlistY[501];
_Thread_local int16_t RpopT;
_Thread_local int16_t SCorpseBase;
_Thread_local int16_t SMode;
_Thread_local int16_t Scycle;
_Thread_local int16_t Scycle2;
_Thread_local int16_t SowDir[3];
_Thread_local int16_t SowSave[3];
_Thread_local uint8_t SowTab[8];
_Thread_local int16_t SowX[3];
_Thread_local int16_t SowY[3];
_Thread_local int16_t SpidBurpCnt;
_Thread_local int16_t SpidRevenge;
_Thread_local int16_t Starg;
_Thread_local int16_t StargLife;
_Thread_local int16_t StrategicModeB;
_Thread_local int16_t SuserX;
_Thread_local int16_t SuserY;
_Thread_local int16_t TERRAINset;
_Thread_local int16_t TilesDugR;
_Thread_local int16_t Tindex;
_Thread_local int8_t TurnTab[9][8];
_Thread_local int16_t YardMode;
_Thread_local int8_t fd_3D57_006C[8];
_Thread_local int16_t fd_3D57_0074[16];
_Thread_local int8_t fd_3D57_0094[16];
_Thread_local uint8_t fd_3D57_00A4[12][16];
_Thread_local uint8_t fd_3D57_0164[12][16];
_Thread_local int16_t fd_3D57_02A4[2];
_Thread_local int16_t fd_3D57_02A8[2];
_Thread_local int16_t fd_3D57_02AC[2];
_Thread_local int16_t fd_3D57_02B0[2];
_Thread_local int16_t fd_3D57_02B4[2];
_Thread_local int16_t fd_3D57_02B8[2];
_Thread_local int16_t fd_3D57_02BC[2];
_Thread_local int16_t fd_3D57_02C0;
_Thread_local int16_t fd_3D57_02C2[38];
_Thread_local int16_t fd_3D57_0798[4];
_Thread_local int16_t fd_3D57_07A2;
_Thread_local int16_t fd_3D57_07A4;
_Thread_local int16_t fd_3D57_07A6;
_Thread_local int16_t fd_3D57_07A8[7];
_Thread_local int16_t fd_3D57_07BE;
_Thread_local int16_t fd_3D57_07C0[4];
_Thread_local int16_t fd_3D57_07C8[2];
_Thread_local int16_t fd_3D57_07CC[7];
_Thread_local int16_t fd_3D57_0828;
_Thread_local int16_t * fd_3D57_0852[40];
_Thread_local int8_t fd_3D57_0994[8];
_Thread_local int8_t fd_3D57_099C[8];
_Thread_local int8_t fd_3D57_09A4[8];
_Thread_local int8_t fd_3D57_09AC[8];
_Thread_local struct Pt fd_3D57_0B14[4];
_Thread_local RecoveredPointBytes18 fd_3D57_0B24[1];
_Thread_local int8_t fd_3D57_0B36[48];
_Thread_local int16_t fd_3D57_0C0E;
_Thread_local int16_t fd_3D57_0C12;
_Thread_local int16_t fd_3D57_0C14;
_Thread_local int16_t fd_3D57_0C16;
_Thread_local int16_t fd_3D57_0C18;
_Thread_local int16_t fd_3D57_0C1A[2];
_Thread_local int16_t fd_3D57_0C1C;
_Thread_local int16_t fd_3D57_0C1E;
_Thread_local int16_t fd_3D57_0C20;
_Thread_local int16_t fd_3D57_0C22;
_Thread_local int16_t fd_3D57_0C24;
_Thread_local int16_t fd_3D57_0C26;
_Thread_local int16_t fd_3D57_0C28;
_Thread_local int16_t fd_3D57_0C2A;
_Thread_local int16_t fd_3D57_0C2C;
_Thread_local int16_t fd_3D57_0C2E;
_Thread_local int16_t fd_3D57_0C30;
_Thread_local int16_t fd_3D57_0C32;
_Thread_local int16_t fd_3D57_0C34;
_Thread_local int8_t fd_3D57_0C36[4];
_Thread_local int8_t fd_3D57_0C3A[4];
_Thread_local int16_t fd_3D57_0C3E;
_Thread_local int16_t fd_3D57_0C40;
_Thread_local int16_t fd_3D57_0C42;
_Thread_local int16_t fd_3D57_0C44;
_Thread_local int16_t fd_3D57_0C46;
_Thread_local int16_t fd_3D57_0C48;
_Thread_local int16_t fd_3E1D_0000[16][12];
_Thread_local uint8_t fd_3E1D_C89F[64][32];
_Thread_local uint8_t fd_3E1D_D89F[64][32];
_Thread_local int16_t fd_50F6_0200;
_Thread_local int16_t fd_50F6_0202;
_Thread_local int32_t fd_50F6_0204;
_Thread_local int16_t fd_50F6_0208;
_Thread_local int16_t fd_50F6_020E;
_Thread_local int16_t fd_50F6_0210;
_Thread_local int16_t fd_50F6_0212;
_Thread_local int32_t fd_50F6_0214;
_Thread_local int32_t fd_50F6_0220;
_Thread_local int16_t fd_50F6_0224;
_Thread_local int16_t fd_50F6_0226;
_Thread_local int16_t fd_50F6_0228;
_Thread_local int16_t fd_50F6_022C;
_Thread_local int16_t fd_50F6_023E;
_Thread_local int16_t fd_50F6_0240;
_Thread_local int16_t fd_50F6_0242;
_Thread_local int16_t fd_50F6_0244;
_Thread_local int16_t fd_50F6_0246;
_Thread_local int16_t fd_50F6_0254;
_Thread_local uint8_t fd_50F6_0256[100];
_Thread_local int8_t * * fd_50F6_02BA;
_Thread_local int16_t fd_50F6_02BE;
_Thread_local uint8_t fd_50F6_02C0[100];
_Thread_local int16_t fd_50F6_032C;
_Thread_local int16_t fd_50F6_0332;
_Thread_local int16_t fd_50F6_0334[12];
_Thread_local void * * fd_50F6_034C;
_Thread_local int16_t fd_50F6_0352;
_Thread_local int16_t fd_50F6_0354;
_Thread_local int16_t fd_50F6_0356;
_Thread_local int16_t fd_50F6_035E;
_Thread_local int16_t fd_50F6_0364;
_Thread_local int16_t fd_50F6_0366;
_Thread_local int16_t fd_50F6_036C;
_Thread_local int16_t fd_50F6_036E;
_Thread_local int16_t fd_50F6_0376;
_Thread_local int16_t fd_50F6_037A;
_Thread_local uint8_t fd_50F6_037C[100];
_Thread_local int16_t fd_50F6_03E0;
_Thread_local int16_t fd_50F6_03E2;
_Thread_local int16_t fd_50F6_0400;
_Thread_local int16_t fd_50F6_0402;
_Thread_local uint8_t fd_50F6_0404[100];
_Thread_local int16_t fd_50F6_046A;
_Thread_local int16_t fd_50F6_0470;
_Thread_local int32_t fd_50F6_0472;
_Thread_local int16_t fd_50F6_0476;
_Thread_local int16_t fd_50F6_0478;
_Thread_local int16_t fd_50F6_047A;
_Thread_local int16_t fd_50F6_047E;
_Thread_local int16_t fd_50F6_0488;
_Thread_local int16_t fd_50F6_048E;
_Thread_local int16_t fd_50F6_0492;
_Thread_local int16_t fd_50F6_0496;
_Thread_local int16_t fd_50F6_049A;
_Thread_local int16_t fd_50F6_04A4;
_Thread_local int16_t fd_50F6_04BE;
_Thread_local int16_t fd_50F6_04C2;
_Thread_local int16_t fd_50F6_04C4;
_Thread_local int16_t fd_50F6_04C6;
_Thread_local int16_t fd_50F6_04E0;
_Thread_local int16_t fd_50F6_04E2;
_Thread_local int16_t fd_50F6_04E4;
_Thread_local int16_t fd_50F6_04F2;
_Thread_local int16_t fd_50F6_04F4;
_Thread_local int16_t fd_50F6_0502;
_Thread_local int16_t fd_50F6_0504;
_Thread_local int16_t fd_50F6_0506;
_Thread_local int16_t fd_50F6_0508[2];
_Thread_local int16_t fd_50F6_0510;
_Thread_local int16_t fd_50F6_0516[64];
_Thread_local int16_t fd_50F6_0596[2];
_Thread_local int16_t fd_50F6_059E;
_Thread_local int16_t fd_50F6_05A0[64];
_Thread_local int16_t fd_50F6_0624;
_Thread_local int16_t fd_50F6_0626[64];
_Thread_local int16_t fd_50F6_06A6[2];
_Thread_local int16_t fd_50F6_06AA;
_Thread_local int16_t fd_50F6_06AC;
_Thread_local int16_t fd_50F6_06AE[64];
_Thread_local int16_t fd_50F6_072E[2];
_Thread_local int32_t fd_50F6_0736;
_Thread_local int16_t fd_50F6_073A;
_Thread_local int16_t fd_50F6_073C[64];
_Thread_local int16_t fd_50F6_07BC[2];
_Thread_local int16_t fd_50F6_07C0;
_Thread_local int16_t fd_50F6_07C2;
_Thread_local int16_t fd_50F6_07C8;
_Thread_local int16_t fd_50F6_07CA[2];
_Thread_local int16_t fd_50F6_07CE[64];
_Thread_local int16_t fd_50F6_084E;
_Thread_local int16_t fd_50F6_0850;
_Thread_local RecoveredPoint fd_50F6_0852;
_Thread_local int16_t fd_50F6_0856[64];
_Thread_local int16_t fd_50F6_08DA;
_Thread_local int16_t fd_50F6_08DC;
_Thread_local RecoveredXY fd_50F6_08DE;
_Thread_local int16_t fd_50F6_08E2;
_Thread_local int16_t fd_50F6_08E8;
_Thread_local RecoveredPoint fd_50F6_08EC;
_Thread_local int16_t fd_50F6_08F0[64];
_Thread_local int16_t fd_50F6_0970[64];
_Thread_local int16_t fd_50F6_09F0;
_Thread_local RecoveredXY fd_50F6_09F2;
_Thread_local int16_t fd_50F6_09FA;
_Thread_local int16_t fd_50F6_09FC[2];
_Thread_local int16_t fd_50F6_0A00;
_Thread_local RecoveredPoint fd_50F6_0A02;
_Thread_local int16_t fd_50F6_0A06;
_Thread_local int16_t fd_50F6_0A0A[64];
_Thread_local RecoveredXY fd_50F6_0A8A;
_Thread_local int16_t fd_50F6_0A8E;
_Thread_local int16_t fd_50F6_0A90;
_Thread_local int16_t fd_50F6_0A9C;
_Thread_local int16_t fd_50F6_0A9E;
_Thread_local int16_t fd_50F6_0AA0;
_Thread_local RecoveredPoint fd_50F6_0AA2;
_Thread_local int16_t fd_50F6_0AA6;
_Thread_local RecoveredXY fd_50F6_0AB2;
_Thread_local int16_t fd_50F6_0AB6;
_Thread_local int16_t fd_50F6_0AC4;
_Thread_local int16_t fd_50F6_0AC6;
_Thread_local int16_t fd_50F6_0AC8;
_Thread_local int16_t fd_50F6_0ACA;
_Thread_local int16_t fd_50F6_0AD6;
_Thread_local int16_t fd_50F6_0AD8;
_Thread_local int32_t fd_50F6_0ADA;
_Thread_local int16_t fd_50F6_0AE8;
_Thread_local int16_t fd_50F6_0AEA;
_Thread_local int16_t fd_50F6_0AEC[6];
_Thread_local int16_t fd_50F6_0AF8;
_Thread_local int16_t fd_50F6_0AFA[6];
_Thread_local int16_t fd_50F6_0B06;
_Thread_local int16_t fd_50F6_0B08;
_Thread_local int16_t fd_50F6_0B12[6];
_Thread_local int16_t fd_50F6_0B1E;
_Thread_local int16_t fd_50F6_0B20;
_Thread_local int16_t * fd_50F6_0B22;
_Thread_local uint32_t fd_50F6_0C26;
_Thread_local int16_t fd_50F6_0C2A[6];
_Thread_local int16_t fd_50F6_0C38;
_Thread_local int16_t fd_50F6_0C3A;
_Thread_local int16_t fd_50F6_0C3E;
_Thread_local int16_t fd_50F6_0D40[20];
_Thread_local int16_t fd_50F6_0D68;
_Thread_local int16_t fd_50F6_0D6C;
_Thread_local int16_t fd_50F6_0D70;
_Thread_local int16_t fd_50F6_0D72[20];
_Thread_local int16_t fd_50F6_0D9A;
_Thread_local int16_t fd_50F6_0EAC;
_Thread_local int16_t fd_50F6_0EB6[32];
_Thread_local int16_t fd_50F6_0EF6;
_Thread_local int16_t fd_50F6_0EF8;
_Thread_local int16_t fd_50F6_0EFA;
_Thread_local int32_t fd_50F6_0EFC;
_Thread_local int16_t fd_50F6_0F06;
_Thread_local int16_t fd_50F6_0F0C;
_Thread_local int16_t fd_50F6_0F0E;
_Thread_local int16_t fd_50F6_0F10;
_Thread_local int16_t fd_50F6_0F12;
_Thread_local int16_t fd_50F6_0F26;
_Thread_local int16_t fd_50F6_0F2E;
_Thread_local int32_t fd_50F6_0F30;
_Thread_local int16_t fd_50F6_0F34;
_Thread_local int16_t fd_50F6_0F36;
_Thread_local int32_t fd_50F6_0F3E;
_Thread_local int16_t fd_50F6_0F44;
_Thread_local int16_t fd_50F6_0FB6;
_Thread_local int16_t fd_50F6_0FBA;
_Thread_local int32_t fd_50F6_0FBC;
_Thread_local int32_t fd_50F6_0FC2;
_Thread_local int16_t fd_50F6_0FFA;
_Thread_local int16_t fd_50F6_0FFE;
_Thread_local int32_t fd_50F6_1000;
_Thread_local int16_t fd_50F6_1004;
_Thread_local int16_t fd_50F6_1006;
_Thread_local int16_t fd_50F6_1040;
_Thread_local int16_t fd_50F6_1044;
_Thread_local int16_t fd_50F6_104E;
_Thread_local int16_t fd_50F6_1058;
_Thread_local int16_t fd_50F6_105C;
_Thread_local int16_t fd_50F6_105E;
_Thread_local int16_t fd_50F6_1066;
_Thread_local int32_t fd_50F6_1068;
_Thread_local uint8_t fd_50F6_106C;
_Thread_local int16_t fd_50F6_1074;
_Thread_local int32_t fd_50F6_107E;
_Thread_local int32_t fd_50F6_1082;
_Thread_local int16_t fd_50F6_108C;
_Thread_local int32_t fd_50F6_108E;
_Thread_local int32_t fd_50F6_109C;
_Thread_local int16_t fd_50F6_10A0;
_Thread_local int32_t fd_50F6_10A2;
_Thread_local int16_t fd_50F6_10A6;
_Thread_local int16_t fd_50F6_10AC;
_Thread_local int16_t fd_50F6_10B0;
_Thread_local int16_t fd_50F6_10B2;
_Thread_local int16_t fd_50F6_10B8;
_Thread_local int16_t fd_50F6_10BA;
_Thread_local int16_t fd_50F6_10BC;
_Thread_local int16_t fd_50F6_10C0;
_Thread_local struct Rect fd_50F6_10D2;
_Thread_local int16_t fd_50F6_10DE;
_Thread_local int16_t fd_50F6_10E0;
_Thread_local struct Rect fd_50F6_110C;
_Thread_local int32_t fd_50F6_383A;
_Thread_local int16_t fd_50F6_3856;
_Thread_local int16_t fd_50F6_3858;
_Thread_local int16_t fd_55B3_19BE;
_Thread_local int16_t fd_55B3_19C0;
_Thread_local int16_t fd_55B3_29A2;
_Thread_local int16_t fd_55B3_2A42[2];
_Thread_local int16_t fd_55B3_2CBC;
_Thread_local int16_t g_3DB2;
_Thread_local int8_t g_5A97;
_Thread_local int16_t * g_5AAC;
_Thread_local uint16_t modeLevels[3];
_Thread_local int16_t * fd_3D57_082A[20];

static void recovered_export(RecoveredState *state)
{
    memcpy(&state->AdviceStrs, &AdviceStrs, sizeof(state->AdviceStrs));
    memcpy(&state->AlistM, &AlistM, sizeof(state->AlistM));
    memcpy(&state->AlistS, &AlistS, sizeof(state->AlistS));
    memcpy(&state->AlistT, &AlistT, sizeof(state->AlistT));
    memcpy(&state->AlistX, &AlistX, sizeof(state->AlistX));
    memcpy(&state->AlistY, &AlistY, sizeof(state->AlistY));
    memcpy(&state->AntsEatenByLions, &AntsEatenByLions, sizeof(state->AntsEatenByLions));
    memcpy(&state->BAntsEaten, &BAntsEaten, sizeof(state->BAntsEaten));
    memcpy(&state->Barrier, &Barrier, sizeof(state->Barrier));
    memcpy(&state->BlistM, &BlistM, sizeof(state->BlistM));
    memcpy(&state->BlistS, &BlistS, sizeof(state->BlistS));
    memcpy(&state->BlistT, &BlistT, sizeof(state->BlistT));
    memcpy(&state->BlistX, &BlistX, sizeof(state->BlistX));
    memcpy(&state->BlistY, &BlistY, sizeof(state->BlistY));
    memcpy(&state->BpopT, &BpopT, sizeof(state->BpopT));
    memcpy(&state->CasteModeTabB, &CasteModeTabB, sizeof(state->CasteModeTabB));
    memcpy(&state->CasteTabB, &CasteTabB, sizeof(state->CasteTabB));
    memcpy(&state->ChaseSpid, &ChaseSpid, sizeof(state->ChaseSpid));
    memcpy(&state->CurExpTool, &CurExpTool, sizeof(state->CurExpTool));
    memcpy(&state->CurGndTileID, &CurGndTileID, sizeof(state->CurGndTileID));
    memcpy(&state->Cycle, &Cycle, sizeof(state->Cycle));
    memcpy(&state->DROPdir, &DROPdir, sizeof(state->DROPdir));
    memcpy(&state->DeathCnt, &DeathCnt, sizeof(state->DeathCnt));
    memcpy(&state->Dx8, &Dx8, sizeof(state->Dx8));
    memcpy(&state->Dx9, &Dx9, sizeof(state->Dx9));
    memcpy(&state->Dy8, &Dy8, sizeof(state->Dy8));
    memcpy(&state->Dy9, &Dy9, sizeof(state->Dy9));
    memcpy(&state->EatCnt, &EatCnt, sizeof(state->EatCnt));
    memcpy(&state->ExitMapB, &ExitMapB, sizeof(state->ExitMapB));
    memcpy(&state->ExitMapR, &ExitMapR, sizeof(state->ExitMapR));
    memcpy(&state->ExpSubStates, &ExpSubStates, sizeof(state->ExpSubStates));
    memcpy(&state->FoodB, &FoodB, sizeof(state->FoodB));
    memcpy(&state->FoodR, &FoodR, sizeof(state->FoodR));
    memcpy(&state->FuzLocX, &FuzLocX, sizeof(state->FuzLocX));
    memcpy(&state->FuzLocY, &FuzLocY, sizeof(state->FuzLocY));
    memcpy(&state->HealthB, &HealthB, sizeof(state->HealthB));
    memcpy(&state->HealthR, &HealthR, sizeof(state->HealthR));
    memcpy(&state->HoleMapB, &HoleMapB, sizeof(state->HoleMapB));
    memcpy(&state->HoleMapR, &HoleMapR, sizeof(state->HoleMapR));
    memcpy(&state->IdealCaste, &IdealCaste, sizeof(state->IdealCaste));
    memcpy(&state->InitialLions, &InitialLions, sizeof(state->InitialLions));
    memcpy(&state->LifeA, &LifeA, sizeof(state->LifeA));
    memcpy(&state->LifeB, &LifeB, sizeof(state->LifeB));
    memcpy(&state->LifeR, &LifeR, sizeof(state->LifeR));
    memcpy(&state->LionIndex, &LionIndex, sizeof(state->LionIndex));
    memcpy(&state->LionListM, &LionListM, sizeof(state->LionListM));
    memcpy(&state->LionListS, &LionListS, sizeof(state->LionListS));
    memcpy(&state->LionListT, &LionListT, sizeof(state->LionListT));
    memcpy(&state->LionListX, &LionListX, sizeof(state->LionListX));
    memcpy(&state->LionListY, &LionListY, sizeof(state->LionListY));
    memcpy(&state->ListIndexA, &ListIndexA, sizeof(state->ListIndexA));
    memcpy(&state->ListIndexB, &ListIndexB, sizeof(state->ListIndexB));
    memcpy(&state->ListIndexR, &ListIndexR, sizeof(state->ListIndexR));
    memcpy(&state->MapA, &MapA, sizeof(state->MapA));
    memcpy(&state->MapB, &MapB, sizeof(state->MapB));
    memcpy(&state->MapPlane, &MapPlane, sizeof(state->MapPlane));
    memcpy(&state->MapR, &MapR, sizeof(state->MapR));
    memcpy(&state->MeHealth, &MeHealth, sizeof(state->MeHealth));
    memcpy(&state->MeLocX, &MeLocX, sizeof(state->MeLocX));
    memcpy(&state->MeLocY, &MeLocY, sizeof(state->MeLocY));
    memcpy(&state->MePlane, &MePlane, sizeof(state->MePlane));
    memcpy(&state->ModeAuto, &ModeAuto, sizeof(state->ModeAuto));
    memcpy(&state->ModeMe, &ModeMe, sizeof(state->ModeMe));
    memcpy(&state->ModeTabB, &ModeTabB, sizeof(state->ModeTabB));
    memcpy(&state->ModeTabSB, &ModeTabSB, sizeof(state->ModeTabSB));
    memcpy(&state->ModeTabWB, &ModeTabWB, sizeof(state->ModeTabWB));
    memcpy(&state->PherMapA, &PherMapA, sizeof(state->PherMapA));
    memcpy(&state->PherMapBN, &PherMapBN, sizeof(state->PherMapBN));
    memcpy(&state->PherMapBT, &PherMapBT, sizeof(state->PherMapBT));
    memcpy(&state->PherMapRN, &PherMapRN, sizeof(state->PherMapRN));
    memcpy(&state->PherMapRT, &PherMapRT, sizeof(state->PherMapRT));
    memcpy(&state->PillDir, &PillDir, sizeof(state->PillDir));
    memcpy(&state->PillarMap, &PillarMap, sizeof(state->PillarMap));
    memcpy(&state->PillarSeg, &PillarSeg, sizeof(state->PillarSeg));
    memcpy(&state->PillarState, &PillarState, sizeof(state->PillarState));
    memcpy(&state->PillarX, &PillarX, sizeof(state->PillarX));
    memcpy(&state->PillarY, &PillarY, sizeof(state->PillarY));
    memcpy(&state->RAntsEaten, &RAntsEaten, sizeof(state->RAntsEaten));
    memcpy(&state->RT3, &RT3, sizeof(state->RT3));
    memcpy(&state->RT5, &RT5, sizeof(state->RT5));
    memcpy(&state->RedLocX, &RedLocX, sizeof(state->RedLocX));
    memcpy(&state->RedLocY, &RedLocY, sizeof(state->RedLocY));
    memcpy(&state->RedPlane, &RedPlane, sizeof(state->RedPlane));
    memcpy(&state->RlistM, &RlistM, sizeof(state->RlistM));
    memcpy(&state->RlistS, &RlistS, sizeof(state->RlistS));
    memcpy(&state->RlistT, &RlistT, sizeof(state->RlistT));
    memcpy(&state->RlistX, &RlistX, sizeof(state->RlistX));
    memcpy(&state->RlistY, &RlistY, sizeof(state->RlistY));
    memcpy(&state->RpopT, &RpopT, sizeof(state->RpopT));
    memcpy(&state->SCorpseBase, &SCorpseBase, sizeof(state->SCorpseBase));
    memcpy(&state->SMode, &SMode, sizeof(state->SMode));
    memcpy(&state->Scycle, &Scycle, sizeof(state->Scycle));
    memcpy(&state->Scycle2, &Scycle2, sizeof(state->Scycle2));
    memcpy(&state->SowDir, &SowDir, sizeof(state->SowDir));
    memcpy(&state->SowSave, &SowSave, sizeof(state->SowSave));
    memcpy(&state->SowTab, &SowTab, sizeof(state->SowTab));
    memcpy(&state->SowX, &SowX, sizeof(state->SowX));
    memcpy(&state->SowY, &SowY, sizeof(state->SowY));
    memcpy(&state->SpidBurpCnt, &SpidBurpCnt, sizeof(state->SpidBurpCnt));
    memcpy(&state->SpidRevenge, &SpidRevenge, sizeof(state->SpidRevenge));
    memcpy(&state->Starg, &Starg, sizeof(state->Starg));
    memcpy(&state->StargLife, &StargLife, sizeof(state->StargLife));
    memcpy(&state->StrategicModeB, &StrategicModeB, sizeof(state->StrategicModeB));
    memcpy(&state->SuserX, &SuserX, sizeof(state->SuserX));
    memcpy(&state->SuserY, &SuserY, sizeof(state->SuserY));
    memcpy(&state->TERRAINset, &TERRAINset, sizeof(state->TERRAINset));
    memcpy(&state->TilesDugR, &TilesDugR, sizeof(state->TilesDugR));
    memcpy(&state->Tindex, &Tindex, sizeof(state->Tindex));
    memcpy(&state->TurnTab, &TurnTab, sizeof(state->TurnTab));
    memcpy(&state->YardMode, &YardMode, sizeof(state->YardMode));
    memcpy(&state->fd_3D57_006C, &fd_3D57_006C, sizeof(state->fd_3D57_006C));
    memcpy(&state->fd_3D57_0074, &fd_3D57_0074, sizeof(state->fd_3D57_0074));
    memcpy(&state->fd_3D57_0094, &fd_3D57_0094, sizeof(state->fd_3D57_0094));
    memcpy(&state->fd_3D57_00A4, &fd_3D57_00A4, sizeof(state->fd_3D57_00A4));
    memcpy(&state->fd_3D57_0164, &fd_3D57_0164, sizeof(state->fd_3D57_0164));
    memcpy(&state->fd_3D57_02A4, &fd_3D57_02A4, sizeof(state->fd_3D57_02A4));
    memcpy(&state->fd_3D57_02A8, &fd_3D57_02A8, sizeof(state->fd_3D57_02A8));
    memcpy(&state->fd_3D57_02AC, &fd_3D57_02AC, sizeof(state->fd_3D57_02AC));
    memcpy(&state->fd_3D57_02B0, &fd_3D57_02B0, sizeof(state->fd_3D57_02B0));
    memcpy(&state->fd_3D57_02B4, &fd_3D57_02B4, sizeof(state->fd_3D57_02B4));
    memcpy(&state->fd_3D57_02B8, &fd_3D57_02B8, sizeof(state->fd_3D57_02B8));
    memcpy(&state->fd_3D57_02BC, &fd_3D57_02BC, sizeof(state->fd_3D57_02BC));
    memcpy(&state->fd_3D57_02C0, &fd_3D57_02C0, sizeof(state->fd_3D57_02C0));
    memcpy(&state->fd_3D57_02C2, &fd_3D57_02C2, sizeof(state->fd_3D57_02C2));
    memcpy(&state->fd_3D57_0798, &fd_3D57_0798, sizeof(state->fd_3D57_0798));
    memcpy(&state->fd_3D57_07A2, &fd_3D57_07A2, sizeof(state->fd_3D57_07A2));
    memcpy(&state->fd_3D57_07A4, &fd_3D57_07A4, sizeof(state->fd_3D57_07A4));
    memcpy(&state->fd_3D57_07A6, &fd_3D57_07A6, sizeof(state->fd_3D57_07A6));
    memcpy(&state->fd_3D57_07A8, &fd_3D57_07A8, sizeof(state->fd_3D57_07A8));
    memcpy(&state->fd_3D57_07BE, &fd_3D57_07BE, sizeof(state->fd_3D57_07BE));
    memcpy(&state->fd_3D57_07C0, &fd_3D57_07C0, sizeof(state->fd_3D57_07C0));
    memcpy(&state->fd_3D57_07C8, &fd_3D57_07C8, sizeof(state->fd_3D57_07C8));
    memcpy(&state->fd_3D57_07CC, &fd_3D57_07CC, sizeof(state->fd_3D57_07CC));
    memcpy(&state->fd_3D57_0828, &fd_3D57_0828, sizeof(state->fd_3D57_0828));
    memcpy(&state->fd_3D57_0852, &fd_3D57_0852, sizeof(state->fd_3D57_0852));
    memcpy(&state->fd_3D57_0994, &fd_3D57_0994, sizeof(state->fd_3D57_0994));
    memcpy(&state->fd_3D57_099C, &fd_3D57_099C, sizeof(state->fd_3D57_099C));
    memcpy(&state->fd_3D57_09A4, &fd_3D57_09A4, sizeof(state->fd_3D57_09A4));
    memcpy(&state->fd_3D57_09AC, &fd_3D57_09AC, sizeof(state->fd_3D57_09AC));
    memcpy(&state->fd_3D57_0B14, &fd_3D57_0B14, sizeof(state->fd_3D57_0B14));
    memcpy(&state->fd_3D57_0B24, &fd_3D57_0B24, sizeof(state->fd_3D57_0B24));
    memcpy(&state->fd_3D57_0B36, &fd_3D57_0B36, sizeof(state->fd_3D57_0B36));
    memcpy(&state->fd_3D57_0C0E, &fd_3D57_0C0E, sizeof(state->fd_3D57_0C0E));
    memcpy(&state->fd_3D57_0C12, &fd_3D57_0C12, sizeof(state->fd_3D57_0C12));
    memcpy(&state->fd_3D57_0C14, &fd_3D57_0C14, sizeof(state->fd_3D57_0C14));
    memcpy(&state->fd_3D57_0C16, &fd_3D57_0C16, sizeof(state->fd_3D57_0C16));
    memcpy(&state->fd_3D57_0C18, &fd_3D57_0C18, sizeof(state->fd_3D57_0C18));
    memcpy(&state->fd_3D57_0C1A, &fd_3D57_0C1A, sizeof(state->fd_3D57_0C1A));
    memcpy(&state->fd_3D57_0C1C, &fd_3D57_0C1C, sizeof(state->fd_3D57_0C1C));
    memcpy(&state->fd_3D57_0C1E, &fd_3D57_0C1E, sizeof(state->fd_3D57_0C1E));
    memcpy(&state->fd_3D57_0C20, &fd_3D57_0C20, sizeof(state->fd_3D57_0C20));
    memcpy(&state->fd_3D57_0C22, &fd_3D57_0C22, sizeof(state->fd_3D57_0C22));
    memcpy(&state->fd_3D57_0C24, &fd_3D57_0C24, sizeof(state->fd_3D57_0C24));
    memcpy(&state->fd_3D57_0C26, &fd_3D57_0C26, sizeof(state->fd_3D57_0C26));
    memcpy(&state->fd_3D57_0C28, &fd_3D57_0C28, sizeof(state->fd_3D57_0C28));
    memcpy(&state->fd_3D57_0C2A, &fd_3D57_0C2A, sizeof(state->fd_3D57_0C2A));
    memcpy(&state->fd_3D57_0C2C, &fd_3D57_0C2C, sizeof(state->fd_3D57_0C2C));
    memcpy(&state->fd_3D57_0C2E, &fd_3D57_0C2E, sizeof(state->fd_3D57_0C2E));
    memcpy(&state->fd_3D57_0C30, &fd_3D57_0C30, sizeof(state->fd_3D57_0C30));
    memcpy(&state->fd_3D57_0C32, &fd_3D57_0C32, sizeof(state->fd_3D57_0C32));
    memcpy(&state->fd_3D57_0C34, &fd_3D57_0C34, sizeof(state->fd_3D57_0C34));
    memcpy(&state->fd_3D57_0C36, &fd_3D57_0C36, sizeof(state->fd_3D57_0C36));
    memcpy(&state->fd_3D57_0C3A, &fd_3D57_0C3A, sizeof(state->fd_3D57_0C3A));
    memcpy(&state->fd_3D57_0C3E, &fd_3D57_0C3E, sizeof(state->fd_3D57_0C3E));
    memcpy(&state->fd_3D57_0C40, &fd_3D57_0C40, sizeof(state->fd_3D57_0C40));
    memcpy(&state->fd_3D57_0C42, &fd_3D57_0C42, sizeof(state->fd_3D57_0C42));
    memcpy(&state->fd_3D57_0C44, &fd_3D57_0C44, sizeof(state->fd_3D57_0C44));
    memcpy(&state->fd_3D57_0C46, &fd_3D57_0C46, sizeof(state->fd_3D57_0C46));
    memcpy(&state->fd_3D57_0C48, &fd_3D57_0C48, sizeof(state->fd_3D57_0C48));
    memcpy(&state->fd_3E1D_0000, &fd_3E1D_0000, sizeof(state->fd_3E1D_0000));
    memcpy(&state->fd_3E1D_C89F, &fd_3E1D_C89F, sizeof(state->fd_3E1D_C89F));
    memcpy(&state->fd_3E1D_D89F, &fd_3E1D_D89F, sizeof(state->fd_3E1D_D89F));
    memcpy(&state->fd_50F6_0200, &fd_50F6_0200, sizeof(state->fd_50F6_0200));
    memcpy(&state->fd_50F6_0202, &fd_50F6_0202, sizeof(state->fd_50F6_0202));
    memcpy(&state->fd_50F6_0204, &fd_50F6_0204, sizeof(state->fd_50F6_0204));
    memcpy(&state->fd_50F6_0208, &fd_50F6_0208, sizeof(state->fd_50F6_0208));
    memcpy(&state->fd_50F6_020E, &fd_50F6_020E, sizeof(state->fd_50F6_020E));
    memcpy(&state->fd_50F6_0210, &fd_50F6_0210, sizeof(state->fd_50F6_0210));
    memcpy(&state->fd_50F6_0212, &fd_50F6_0212, sizeof(state->fd_50F6_0212));
    memcpy(&state->fd_50F6_0214, &fd_50F6_0214, sizeof(state->fd_50F6_0214));
    memcpy(&state->fd_50F6_0220, &fd_50F6_0220, sizeof(state->fd_50F6_0220));
    memcpy(&state->fd_50F6_0224, &fd_50F6_0224, sizeof(state->fd_50F6_0224));
    memcpy(&state->fd_50F6_0226, &fd_50F6_0226, sizeof(state->fd_50F6_0226));
    memcpy(&state->fd_50F6_0228, &fd_50F6_0228, sizeof(state->fd_50F6_0228));
    memcpy(&state->fd_50F6_022C, &fd_50F6_022C, sizeof(state->fd_50F6_022C));
    memcpy(&state->fd_50F6_023E, &fd_50F6_023E, sizeof(state->fd_50F6_023E));
    memcpy(&state->fd_50F6_0240, &fd_50F6_0240, sizeof(state->fd_50F6_0240));
    memcpy(&state->fd_50F6_0242, &fd_50F6_0242, sizeof(state->fd_50F6_0242));
    memcpy(&state->fd_50F6_0244, &fd_50F6_0244, sizeof(state->fd_50F6_0244));
    memcpy(&state->fd_50F6_0246, &fd_50F6_0246, sizeof(state->fd_50F6_0246));
    memcpy(&state->fd_50F6_0254, &fd_50F6_0254, sizeof(state->fd_50F6_0254));
    memcpy(&state->fd_50F6_0256, &fd_50F6_0256, sizeof(state->fd_50F6_0256));
    memcpy(&state->fd_50F6_02BA, &fd_50F6_02BA, sizeof(state->fd_50F6_02BA));
    memcpy(&state->fd_50F6_02BE, &fd_50F6_02BE, sizeof(state->fd_50F6_02BE));
    memcpy(&state->fd_50F6_02C0, &fd_50F6_02C0, sizeof(state->fd_50F6_02C0));
    memcpy(&state->fd_50F6_032C, &fd_50F6_032C, sizeof(state->fd_50F6_032C));
    memcpy(&state->fd_50F6_0332, &fd_50F6_0332, sizeof(state->fd_50F6_0332));
    memcpy(&state->fd_50F6_0334, &fd_50F6_0334, sizeof(state->fd_50F6_0334));
    memcpy(&state->fd_50F6_034C, &fd_50F6_034C, sizeof(state->fd_50F6_034C));
    memcpy(&state->fd_50F6_0352, &fd_50F6_0352, sizeof(state->fd_50F6_0352));
    memcpy(&state->fd_50F6_0354, &fd_50F6_0354, sizeof(state->fd_50F6_0354));
    memcpy(&state->fd_50F6_0356, &fd_50F6_0356, sizeof(state->fd_50F6_0356));
    memcpy(&state->fd_50F6_035E, &fd_50F6_035E, sizeof(state->fd_50F6_035E));
    memcpy(&state->fd_50F6_0364, &fd_50F6_0364, sizeof(state->fd_50F6_0364));
    memcpy(&state->fd_50F6_0366, &fd_50F6_0366, sizeof(state->fd_50F6_0366));
    memcpy(&state->fd_50F6_036C, &fd_50F6_036C, sizeof(state->fd_50F6_036C));
    memcpy(&state->fd_50F6_036E, &fd_50F6_036E, sizeof(state->fd_50F6_036E));
    memcpy(&state->fd_50F6_0376, &fd_50F6_0376, sizeof(state->fd_50F6_0376));
    memcpy(&state->fd_50F6_037A, &fd_50F6_037A, sizeof(state->fd_50F6_037A));
    memcpy(&state->fd_50F6_037C, &fd_50F6_037C, sizeof(state->fd_50F6_037C));
    memcpy(&state->fd_50F6_03E0, &fd_50F6_03E0, sizeof(state->fd_50F6_03E0));
    memcpy(&state->fd_50F6_03E2, &fd_50F6_03E2, sizeof(state->fd_50F6_03E2));
    memcpy(&state->fd_50F6_0400, &fd_50F6_0400, sizeof(state->fd_50F6_0400));
    memcpy(&state->fd_50F6_0402, &fd_50F6_0402, sizeof(state->fd_50F6_0402));
    memcpy(&state->fd_50F6_0404, &fd_50F6_0404, sizeof(state->fd_50F6_0404));
    memcpy(&state->fd_50F6_046A, &fd_50F6_046A, sizeof(state->fd_50F6_046A));
    memcpy(&state->fd_50F6_0470, &fd_50F6_0470, sizeof(state->fd_50F6_0470));
    memcpy(&state->fd_50F6_0472, &fd_50F6_0472, sizeof(state->fd_50F6_0472));
    memcpy(&state->fd_50F6_0476, &fd_50F6_0476, sizeof(state->fd_50F6_0476));
    memcpy(&state->fd_50F6_0478, &fd_50F6_0478, sizeof(state->fd_50F6_0478));
    memcpy(&state->fd_50F6_047A, &fd_50F6_047A, sizeof(state->fd_50F6_047A));
    memcpy(&state->fd_50F6_047E, &fd_50F6_047E, sizeof(state->fd_50F6_047E));
    memcpy(&state->fd_50F6_0488, &fd_50F6_0488, sizeof(state->fd_50F6_0488));
    memcpy(&state->fd_50F6_048E, &fd_50F6_048E, sizeof(state->fd_50F6_048E));
    memcpy(&state->fd_50F6_0492, &fd_50F6_0492, sizeof(state->fd_50F6_0492));
    memcpy(&state->fd_50F6_0496, &fd_50F6_0496, sizeof(state->fd_50F6_0496));
    memcpy(&state->fd_50F6_049A, &fd_50F6_049A, sizeof(state->fd_50F6_049A));
    memcpy(&state->fd_50F6_04A4, &fd_50F6_04A4, sizeof(state->fd_50F6_04A4));
    memcpy(&state->fd_50F6_04BE, &fd_50F6_04BE, sizeof(state->fd_50F6_04BE));
    memcpy(&state->fd_50F6_04C2, &fd_50F6_04C2, sizeof(state->fd_50F6_04C2));
    memcpy(&state->fd_50F6_04C4, &fd_50F6_04C4, sizeof(state->fd_50F6_04C4));
    memcpy(&state->fd_50F6_04C6, &fd_50F6_04C6, sizeof(state->fd_50F6_04C6));
    memcpy(&state->fd_50F6_04E0, &fd_50F6_04E0, sizeof(state->fd_50F6_04E0));
    memcpy(&state->fd_50F6_04E2, &fd_50F6_04E2, sizeof(state->fd_50F6_04E2));
    memcpy(&state->fd_50F6_04E4, &fd_50F6_04E4, sizeof(state->fd_50F6_04E4));
    memcpy(&state->fd_50F6_04F2, &fd_50F6_04F2, sizeof(state->fd_50F6_04F2));
    memcpy(&state->fd_50F6_04F4, &fd_50F6_04F4, sizeof(state->fd_50F6_04F4));
    memcpy(&state->fd_50F6_0502, &fd_50F6_0502, sizeof(state->fd_50F6_0502));
    memcpy(&state->fd_50F6_0504, &fd_50F6_0504, sizeof(state->fd_50F6_0504));
    memcpy(&state->fd_50F6_0506, &fd_50F6_0506, sizeof(state->fd_50F6_0506));
    memcpy(&state->fd_50F6_0508, &fd_50F6_0508, sizeof(state->fd_50F6_0508));
    memcpy(&state->fd_50F6_0510, &fd_50F6_0510, sizeof(state->fd_50F6_0510));
    memcpy(&state->fd_50F6_0516, &fd_50F6_0516, sizeof(state->fd_50F6_0516));
    memcpy(&state->fd_50F6_0596, &fd_50F6_0596, sizeof(state->fd_50F6_0596));
    memcpy(&state->fd_50F6_059E, &fd_50F6_059E, sizeof(state->fd_50F6_059E));
    memcpy(&state->fd_50F6_05A0, &fd_50F6_05A0, sizeof(state->fd_50F6_05A0));
    memcpy(&state->fd_50F6_0624, &fd_50F6_0624, sizeof(state->fd_50F6_0624));
    memcpy(&state->fd_50F6_0626, &fd_50F6_0626, sizeof(state->fd_50F6_0626));
    memcpy(&state->fd_50F6_06A6, &fd_50F6_06A6, sizeof(state->fd_50F6_06A6));
    memcpy(&state->fd_50F6_06AA, &fd_50F6_06AA, sizeof(state->fd_50F6_06AA));
    memcpy(&state->fd_50F6_06AC, &fd_50F6_06AC, sizeof(state->fd_50F6_06AC));
    memcpy(&state->fd_50F6_06AE, &fd_50F6_06AE, sizeof(state->fd_50F6_06AE));
    memcpy(&state->fd_50F6_072E, &fd_50F6_072E, sizeof(state->fd_50F6_072E));
    memcpy(&state->fd_50F6_0736, &fd_50F6_0736, sizeof(state->fd_50F6_0736));
    memcpy(&state->fd_50F6_073A, &fd_50F6_073A, sizeof(state->fd_50F6_073A));
    memcpy(&state->fd_50F6_073C, &fd_50F6_073C, sizeof(state->fd_50F6_073C));
    memcpy(&state->fd_50F6_07BC, &fd_50F6_07BC, sizeof(state->fd_50F6_07BC));
    memcpy(&state->fd_50F6_07C0, &fd_50F6_07C0, sizeof(state->fd_50F6_07C0));
    memcpy(&state->fd_50F6_07C2, &fd_50F6_07C2, sizeof(state->fd_50F6_07C2));
    memcpy(&state->fd_50F6_07C8, &fd_50F6_07C8, sizeof(state->fd_50F6_07C8));
    memcpy(&state->fd_50F6_07CA, &fd_50F6_07CA, sizeof(state->fd_50F6_07CA));
    memcpy(&state->fd_50F6_07CE, &fd_50F6_07CE, sizeof(state->fd_50F6_07CE));
    memcpy(&state->fd_50F6_084E, &fd_50F6_084E, sizeof(state->fd_50F6_084E));
    memcpy(&state->fd_50F6_0850, &fd_50F6_0850, sizeof(state->fd_50F6_0850));
    memcpy(&state->fd_50F6_0852, &fd_50F6_0852, sizeof(state->fd_50F6_0852));
    memcpy(&state->fd_50F6_0856, &fd_50F6_0856, sizeof(state->fd_50F6_0856));
    memcpy(&state->fd_50F6_08DA, &fd_50F6_08DA, sizeof(state->fd_50F6_08DA));
    memcpy(&state->fd_50F6_08DC, &fd_50F6_08DC, sizeof(state->fd_50F6_08DC));
    memcpy(&state->fd_50F6_08DE, &fd_50F6_08DE, sizeof(state->fd_50F6_08DE));
    memcpy(&state->fd_50F6_08E2, &fd_50F6_08E2, sizeof(state->fd_50F6_08E2));
    memcpy(&state->fd_50F6_08E8, &fd_50F6_08E8, sizeof(state->fd_50F6_08E8));
    memcpy(&state->fd_50F6_08EC, &fd_50F6_08EC, sizeof(state->fd_50F6_08EC));
    memcpy(&state->fd_50F6_08F0, &fd_50F6_08F0, sizeof(state->fd_50F6_08F0));
    memcpy(&state->fd_50F6_0970, &fd_50F6_0970, sizeof(state->fd_50F6_0970));
    memcpy(&state->fd_50F6_09F0, &fd_50F6_09F0, sizeof(state->fd_50F6_09F0));
    memcpy(&state->fd_50F6_09F2, &fd_50F6_09F2, sizeof(state->fd_50F6_09F2));
    memcpy(&state->fd_50F6_09FA, &fd_50F6_09FA, sizeof(state->fd_50F6_09FA));
    memcpy(&state->fd_50F6_09FC, &fd_50F6_09FC, sizeof(state->fd_50F6_09FC));
    memcpy(&state->fd_50F6_0A00, &fd_50F6_0A00, sizeof(state->fd_50F6_0A00));
    memcpy(&state->fd_50F6_0A02, &fd_50F6_0A02, sizeof(state->fd_50F6_0A02));
    memcpy(&state->fd_50F6_0A06, &fd_50F6_0A06, sizeof(state->fd_50F6_0A06));
    memcpy(&state->fd_50F6_0A0A, &fd_50F6_0A0A, sizeof(state->fd_50F6_0A0A));
    memcpy(&state->fd_50F6_0A8A, &fd_50F6_0A8A, sizeof(state->fd_50F6_0A8A));
    memcpy(&state->fd_50F6_0A8E, &fd_50F6_0A8E, sizeof(state->fd_50F6_0A8E));
    memcpy(&state->fd_50F6_0A90, &fd_50F6_0A90, sizeof(state->fd_50F6_0A90));
    memcpy(&state->fd_50F6_0A9C, &fd_50F6_0A9C, sizeof(state->fd_50F6_0A9C));
    memcpy(&state->fd_50F6_0A9E, &fd_50F6_0A9E, sizeof(state->fd_50F6_0A9E));
    memcpy(&state->fd_50F6_0AA0, &fd_50F6_0AA0, sizeof(state->fd_50F6_0AA0));
    memcpy(&state->fd_50F6_0AA2, &fd_50F6_0AA2, sizeof(state->fd_50F6_0AA2));
    memcpy(&state->fd_50F6_0AA6, &fd_50F6_0AA6, sizeof(state->fd_50F6_0AA6));
    memcpy(&state->fd_50F6_0AB2, &fd_50F6_0AB2, sizeof(state->fd_50F6_0AB2));
    memcpy(&state->fd_50F6_0AB6, &fd_50F6_0AB6, sizeof(state->fd_50F6_0AB6));
    memcpy(&state->fd_50F6_0AC4, &fd_50F6_0AC4, sizeof(state->fd_50F6_0AC4));
    memcpy(&state->fd_50F6_0AC6, &fd_50F6_0AC6, sizeof(state->fd_50F6_0AC6));
    memcpy(&state->fd_50F6_0AC8, &fd_50F6_0AC8, sizeof(state->fd_50F6_0AC8));
    memcpy(&state->fd_50F6_0ACA, &fd_50F6_0ACA, sizeof(state->fd_50F6_0ACA));
    memcpy(&state->fd_50F6_0AD6, &fd_50F6_0AD6, sizeof(state->fd_50F6_0AD6));
    memcpy(&state->fd_50F6_0AD8, &fd_50F6_0AD8, sizeof(state->fd_50F6_0AD8));
    memcpy(&state->fd_50F6_0ADA, &fd_50F6_0ADA, sizeof(state->fd_50F6_0ADA));
    memcpy(&state->fd_50F6_0AE8, &fd_50F6_0AE8, sizeof(state->fd_50F6_0AE8));
    memcpy(&state->fd_50F6_0AEA, &fd_50F6_0AEA, sizeof(state->fd_50F6_0AEA));
    memcpy(&state->fd_50F6_0AEC, &fd_50F6_0AEC, sizeof(state->fd_50F6_0AEC));
    memcpy(&state->fd_50F6_0AF8, &fd_50F6_0AF8, sizeof(state->fd_50F6_0AF8));
    memcpy(&state->fd_50F6_0AFA, &fd_50F6_0AFA, sizeof(state->fd_50F6_0AFA));
    memcpy(&state->fd_50F6_0B06, &fd_50F6_0B06, sizeof(state->fd_50F6_0B06));
    memcpy(&state->fd_50F6_0B08, &fd_50F6_0B08, sizeof(state->fd_50F6_0B08));
    memcpy(&state->fd_50F6_0B12, &fd_50F6_0B12, sizeof(state->fd_50F6_0B12));
    memcpy(&state->fd_50F6_0B1E, &fd_50F6_0B1E, sizeof(state->fd_50F6_0B1E));
    memcpy(&state->fd_50F6_0B20, &fd_50F6_0B20, sizeof(state->fd_50F6_0B20));
    memcpy(&state->fd_50F6_0B22, &fd_50F6_0B22, sizeof(state->fd_50F6_0B22));
    memcpy(&state->fd_50F6_0C26, &fd_50F6_0C26, sizeof(state->fd_50F6_0C26));
    memcpy(&state->fd_50F6_0C2A, &fd_50F6_0C2A, sizeof(state->fd_50F6_0C2A));
    memcpy(&state->fd_50F6_0C38, &fd_50F6_0C38, sizeof(state->fd_50F6_0C38));
    memcpy(&state->fd_50F6_0C3A, &fd_50F6_0C3A, sizeof(state->fd_50F6_0C3A));
    memcpy(&state->fd_50F6_0C3E, &fd_50F6_0C3E, sizeof(state->fd_50F6_0C3E));
    memcpy(&state->fd_50F6_0D40, &fd_50F6_0D40, sizeof(state->fd_50F6_0D40));
    memcpy(&state->fd_50F6_0D68, &fd_50F6_0D68, sizeof(state->fd_50F6_0D68));
    memcpy(&state->fd_50F6_0D6C, &fd_50F6_0D6C, sizeof(state->fd_50F6_0D6C));
    memcpy(&state->fd_50F6_0D70, &fd_50F6_0D70, sizeof(state->fd_50F6_0D70));
    memcpy(&state->fd_50F6_0D72, &fd_50F6_0D72, sizeof(state->fd_50F6_0D72));
    memcpy(&state->fd_50F6_0D9A, &fd_50F6_0D9A, sizeof(state->fd_50F6_0D9A));
    memcpy(&state->fd_50F6_0EAC, &fd_50F6_0EAC, sizeof(state->fd_50F6_0EAC));
    memcpy(&state->fd_50F6_0EB6, &fd_50F6_0EB6, sizeof(state->fd_50F6_0EB6));
    memcpy(&state->fd_50F6_0EF6, &fd_50F6_0EF6, sizeof(state->fd_50F6_0EF6));
    memcpy(&state->fd_50F6_0EF8, &fd_50F6_0EF8, sizeof(state->fd_50F6_0EF8));
    memcpy(&state->fd_50F6_0EFA, &fd_50F6_0EFA, sizeof(state->fd_50F6_0EFA));
    memcpy(&state->fd_50F6_0EFC, &fd_50F6_0EFC, sizeof(state->fd_50F6_0EFC));
    memcpy(&state->fd_50F6_0F06, &fd_50F6_0F06, sizeof(state->fd_50F6_0F06));
    memcpy(&state->fd_50F6_0F0C, &fd_50F6_0F0C, sizeof(state->fd_50F6_0F0C));
    memcpy(&state->fd_50F6_0F0E, &fd_50F6_0F0E, sizeof(state->fd_50F6_0F0E));
    memcpy(&state->fd_50F6_0F10, &fd_50F6_0F10, sizeof(state->fd_50F6_0F10));
    memcpy(&state->fd_50F6_0F12, &fd_50F6_0F12, sizeof(state->fd_50F6_0F12));
    memcpy(&state->fd_50F6_0F26, &fd_50F6_0F26, sizeof(state->fd_50F6_0F26));
    memcpy(&state->fd_50F6_0F2E, &fd_50F6_0F2E, sizeof(state->fd_50F6_0F2E));
    memcpy(&state->fd_50F6_0F30, &fd_50F6_0F30, sizeof(state->fd_50F6_0F30));
    memcpy(&state->fd_50F6_0F34, &fd_50F6_0F34, sizeof(state->fd_50F6_0F34));
    memcpy(&state->fd_50F6_0F36, &fd_50F6_0F36, sizeof(state->fd_50F6_0F36));
    memcpy(&state->fd_50F6_0F3E, &fd_50F6_0F3E, sizeof(state->fd_50F6_0F3E));
    memcpy(&state->fd_50F6_0F44, &fd_50F6_0F44, sizeof(state->fd_50F6_0F44));
    memcpy(&state->fd_50F6_0FB6, &fd_50F6_0FB6, sizeof(state->fd_50F6_0FB6));
    memcpy(&state->fd_50F6_0FBA, &fd_50F6_0FBA, sizeof(state->fd_50F6_0FBA));
    memcpy(&state->fd_50F6_0FBC, &fd_50F6_0FBC, sizeof(state->fd_50F6_0FBC));
    memcpy(&state->fd_50F6_0FC2, &fd_50F6_0FC2, sizeof(state->fd_50F6_0FC2));
    memcpy(&state->fd_50F6_0FFA, &fd_50F6_0FFA, sizeof(state->fd_50F6_0FFA));
    memcpy(&state->fd_50F6_0FFE, &fd_50F6_0FFE, sizeof(state->fd_50F6_0FFE));
    memcpy(&state->fd_50F6_1000, &fd_50F6_1000, sizeof(state->fd_50F6_1000));
    memcpy(&state->fd_50F6_1004, &fd_50F6_1004, sizeof(state->fd_50F6_1004));
    memcpy(&state->fd_50F6_1006, &fd_50F6_1006, sizeof(state->fd_50F6_1006));
    memcpy(&state->fd_50F6_1040, &fd_50F6_1040, sizeof(state->fd_50F6_1040));
    memcpy(&state->fd_50F6_1044, &fd_50F6_1044, sizeof(state->fd_50F6_1044));
    memcpy(&state->fd_50F6_104E, &fd_50F6_104E, sizeof(state->fd_50F6_104E));
    memcpy(&state->fd_50F6_1058, &fd_50F6_1058, sizeof(state->fd_50F6_1058));
    memcpy(&state->fd_50F6_105C, &fd_50F6_105C, sizeof(state->fd_50F6_105C));
    memcpy(&state->fd_50F6_105E, &fd_50F6_105E, sizeof(state->fd_50F6_105E));
    memcpy(&state->fd_50F6_1066, &fd_50F6_1066, sizeof(state->fd_50F6_1066));
    memcpy(&state->fd_50F6_1068, &fd_50F6_1068, sizeof(state->fd_50F6_1068));
    memcpy(&state->fd_50F6_106C, &fd_50F6_106C, sizeof(state->fd_50F6_106C));
    memcpy(&state->fd_50F6_1074, &fd_50F6_1074, sizeof(state->fd_50F6_1074));
    memcpy(&state->fd_50F6_107E, &fd_50F6_107E, sizeof(state->fd_50F6_107E));
    memcpy(&state->fd_50F6_1082, &fd_50F6_1082, sizeof(state->fd_50F6_1082));
    memcpy(&state->fd_50F6_108C, &fd_50F6_108C, sizeof(state->fd_50F6_108C));
    memcpy(&state->fd_50F6_108E, &fd_50F6_108E, sizeof(state->fd_50F6_108E));
    memcpy(&state->fd_50F6_109C, &fd_50F6_109C, sizeof(state->fd_50F6_109C));
    memcpy(&state->fd_50F6_10A0, &fd_50F6_10A0, sizeof(state->fd_50F6_10A0));
    memcpy(&state->fd_50F6_10A2, &fd_50F6_10A2, sizeof(state->fd_50F6_10A2));
    memcpy(&state->fd_50F6_10A6, &fd_50F6_10A6, sizeof(state->fd_50F6_10A6));
    memcpy(&state->fd_50F6_10AC, &fd_50F6_10AC, sizeof(state->fd_50F6_10AC));
    memcpy(&state->fd_50F6_10B0, &fd_50F6_10B0, sizeof(state->fd_50F6_10B0));
    memcpy(&state->fd_50F6_10B2, &fd_50F6_10B2, sizeof(state->fd_50F6_10B2));
    memcpy(&state->fd_50F6_10B8, &fd_50F6_10B8, sizeof(state->fd_50F6_10B8));
    memcpy(&state->fd_50F6_10BA, &fd_50F6_10BA, sizeof(state->fd_50F6_10BA));
    memcpy(&state->fd_50F6_10BC, &fd_50F6_10BC, sizeof(state->fd_50F6_10BC));
    memcpy(&state->fd_50F6_10C0, &fd_50F6_10C0, sizeof(state->fd_50F6_10C0));
    memcpy(&state->fd_50F6_10D2, &fd_50F6_10D2, sizeof(state->fd_50F6_10D2));
    memcpy(&state->fd_50F6_10DE, &fd_50F6_10DE, sizeof(state->fd_50F6_10DE));
    memcpy(&state->fd_50F6_10E0, &fd_50F6_10E0, sizeof(state->fd_50F6_10E0));
    memcpy(&state->fd_50F6_110C, &fd_50F6_110C, sizeof(state->fd_50F6_110C));
    memcpy(&state->fd_50F6_383A, &fd_50F6_383A, sizeof(state->fd_50F6_383A));
    memcpy(&state->fd_50F6_3856, &fd_50F6_3856, sizeof(state->fd_50F6_3856));
    memcpy(&state->fd_50F6_3858, &fd_50F6_3858, sizeof(state->fd_50F6_3858));
    memcpy(&state->fd_55B3_19BE, &fd_55B3_19BE, sizeof(state->fd_55B3_19BE));
    memcpy(&state->fd_55B3_19C0, &fd_55B3_19C0, sizeof(state->fd_55B3_19C0));
    memcpy(&state->fd_55B3_29A2, &fd_55B3_29A2, sizeof(state->fd_55B3_29A2));
    memcpy(&state->fd_55B3_2A42, &fd_55B3_2A42, sizeof(state->fd_55B3_2A42));
    memcpy(&state->fd_55B3_2CBC, &fd_55B3_2CBC, sizeof(state->fd_55B3_2CBC));
    memcpy(&state->g_3DB2, &g_3DB2, sizeof(state->g_3DB2));
    memcpy(&state->g_5A97, &g_5A97, sizeof(state->g_5A97));
    memcpy(&state->g_5AAC, &g_5AAC, sizeof(state->g_5AAC));
    memcpy(&state->modeLevels, &modeLevels, sizeof(state->modeLevels));
}

static void recovered_import(const RecoveredState *state)
{
    memcpy(&AdviceStrs, &state->AdviceStrs, sizeof(AdviceStrs));
    memcpy(&AlistM, &state->AlistM, sizeof(AlistM));
    memcpy(&AlistS, &state->AlistS, sizeof(AlistS));
    memcpy(&AlistT, &state->AlistT, sizeof(AlistT));
    memcpy(&AlistX, &state->AlistX, sizeof(AlistX));
    memcpy(&AlistY, &state->AlistY, sizeof(AlistY));
    memcpy(&AntsEatenByLions, &state->AntsEatenByLions, sizeof(AntsEatenByLions));
    memcpy(&BAntsEaten, &state->BAntsEaten, sizeof(BAntsEaten));
    memcpy(&Barrier, &state->Barrier, sizeof(Barrier));
    memcpy(&BlistM, &state->BlistM, sizeof(BlistM));
    memcpy(&BlistS, &state->BlistS, sizeof(BlistS));
    memcpy(&BlistT, &state->BlistT, sizeof(BlistT));
    memcpy(&BlistX, &state->BlistX, sizeof(BlistX));
    memcpy(&BlistY, &state->BlistY, sizeof(BlistY));
    memcpy(&BpopT, &state->BpopT, sizeof(BpopT));
    memcpy(&CasteModeTabB, &state->CasteModeTabB, sizeof(CasteModeTabB));
    memcpy(&CasteTabB, &state->CasteTabB, sizeof(CasteTabB));
    memcpy(&ChaseSpid, &state->ChaseSpid, sizeof(ChaseSpid));
    memcpy(&CurExpTool, &state->CurExpTool, sizeof(CurExpTool));
    memcpy(&CurGndTileID, &state->CurGndTileID, sizeof(CurGndTileID));
    memcpy(&Cycle, &state->Cycle, sizeof(Cycle));
    memcpy(&DROPdir, &state->DROPdir, sizeof(DROPdir));
    memcpy(&DeathCnt, &state->DeathCnt, sizeof(DeathCnt));
    memcpy(&Dx8, &state->Dx8, sizeof(Dx8));
    memcpy(&Dx9, &state->Dx9, sizeof(Dx9));
    memcpy(&Dy8, &state->Dy8, sizeof(Dy8));
    memcpy(&Dy9, &state->Dy9, sizeof(Dy9));
    memcpy(&EatCnt, &state->EatCnt, sizeof(EatCnt));
    memcpy(&ExitMapB, &state->ExitMapB, sizeof(ExitMapB));
    memcpy(&ExitMapR, &state->ExitMapR, sizeof(ExitMapR));
    memcpy(&ExpSubStates, &state->ExpSubStates, sizeof(ExpSubStates));
    memcpy(&FoodB, &state->FoodB, sizeof(FoodB));
    memcpy(&FoodR, &state->FoodR, sizeof(FoodR));
    memcpy(&FuzLocX, &state->FuzLocX, sizeof(FuzLocX));
    memcpy(&FuzLocY, &state->FuzLocY, sizeof(FuzLocY));
    memcpy(&HealthB, &state->HealthB, sizeof(HealthB));
    memcpy(&HealthR, &state->HealthR, sizeof(HealthR));
    memcpy(&HoleMapB, &state->HoleMapB, sizeof(HoleMapB));
    memcpy(&HoleMapR, &state->HoleMapR, sizeof(HoleMapR));
    memcpy(&IdealCaste, &state->IdealCaste, sizeof(IdealCaste));
    memcpy(&InitialLions, &state->InitialLions, sizeof(InitialLions));
    memcpy(&LifeA, &state->LifeA, sizeof(LifeA));
    memcpy(&LifeB, &state->LifeB, sizeof(LifeB));
    memcpy(&LifeR, &state->LifeR, sizeof(LifeR));
    memcpy(&LionIndex, &state->LionIndex, sizeof(LionIndex));
    memcpy(&LionListM, &state->LionListM, sizeof(LionListM));
    memcpy(&LionListS, &state->LionListS, sizeof(LionListS));
    memcpy(&LionListT, &state->LionListT, sizeof(LionListT));
    memcpy(&LionListX, &state->LionListX, sizeof(LionListX));
    memcpy(&LionListY, &state->LionListY, sizeof(LionListY));
    memcpy(&ListIndexA, &state->ListIndexA, sizeof(ListIndexA));
    memcpy(&ListIndexB, &state->ListIndexB, sizeof(ListIndexB));
    memcpy(&ListIndexR, &state->ListIndexR, sizeof(ListIndexR));
    memcpy(&MapA, &state->MapA, sizeof(MapA));
    memcpy(&MapB, &state->MapB, sizeof(MapB));
    memcpy(&MapPlane, &state->MapPlane, sizeof(MapPlane));
    memcpy(&MapR, &state->MapR, sizeof(MapR));
    memcpy(&MeHealth, &state->MeHealth, sizeof(MeHealth));
    memcpy(&MeLocX, &state->MeLocX, sizeof(MeLocX));
    memcpy(&MeLocY, &state->MeLocY, sizeof(MeLocY));
    memcpy(&MePlane, &state->MePlane, sizeof(MePlane));
    memcpy(&ModeAuto, &state->ModeAuto, sizeof(ModeAuto));
    memcpy(&ModeMe, &state->ModeMe, sizeof(ModeMe));
    memcpy(&ModeTabB, &state->ModeTabB, sizeof(ModeTabB));
    memcpy(&ModeTabSB, &state->ModeTabSB, sizeof(ModeTabSB));
    memcpy(&ModeTabWB, &state->ModeTabWB, sizeof(ModeTabWB));
    memcpy(&PherMapA, &state->PherMapA, sizeof(PherMapA));
    memcpy(&PherMapBN, &state->PherMapBN, sizeof(PherMapBN));
    memcpy(&PherMapBT, &state->PherMapBT, sizeof(PherMapBT));
    memcpy(&PherMapRN, &state->PherMapRN, sizeof(PherMapRN));
    memcpy(&PherMapRT, &state->PherMapRT, sizeof(PherMapRT));
    memcpy(&PillDir, &state->PillDir, sizeof(PillDir));
    memcpy(&PillarMap, &state->PillarMap, sizeof(PillarMap));
    memcpy(&PillarSeg, &state->PillarSeg, sizeof(PillarSeg));
    memcpy(&PillarState, &state->PillarState, sizeof(PillarState));
    memcpy(&PillarX, &state->PillarX, sizeof(PillarX));
    memcpy(&PillarY, &state->PillarY, sizeof(PillarY));
    memcpy(&RAntsEaten, &state->RAntsEaten, sizeof(RAntsEaten));
    memcpy(&RT3, &state->RT3, sizeof(RT3));
    memcpy(&RT5, &state->RT5, sizeof(RT5));
    memcpy(&RedLocX, &state->RedLocX, sizeof(RedLocX));
    memcpy(&RedLocY, &state->RedLocY, sizeof(RedLocY));
    memcpy(&RedPlane, &state->RedPlane, sizeof(RedPlane));
    memcpy(&RlistM, &state->RlistM, sizeof(RlistM));
    memcpy(&RlistS, &state->RlistS, sizeof(RlistS));
    memcpy(&RlistT, &state->RlistT, sizeof(RlistT));
    memcpy(&RlistX, &state->RlistX, sizeof(RlistX));
    memcpy(&RlistY, &state->RlistY, sizeof(RlistY));
    memcpy(&RpopT, &state->RpopT, sizeof(RpopT));
    memcpy(&SCorpseBase, &state->SCorpseBase, sizeof(SCorpseBase));
    memcpy(&SMode, &state->SMode, sizeof(SMode));
    memcpy(&Scycle, &state->Scycle, sizeof(Scycle));
    memcpy(&Scycle2, &state->Scycle2, sizeof(Scycle2));
    memcpy(&SowDir, &state->SowDir, sizeof(SowDir));
    memcpy(&SowSave, &state->SowSave, sizeof(SowSave));
    memcpy(&SowTab, &state->SowTab, sizeof(SowTab));
    memcpy(&SowX, &state->SowX, sizeof(SowX));
    memcpy(&SowY, &state->SowY, sizeof(SowY));
    memcpy(&SpidBurpCnt, &state->SpidBurpCnt, sizeof(SpidBurpCnt));
    memcpy(&SpidRevenge, &state->SpidRevenge, sizeof(SpidRevenge));
    memcpy(&Starg, &state->Starg, sizeof(Starg));
    memcpy(&StargLife, &state->StargLife, sizeof(StargLife));
    memcpy(&StrategicModeB, &state->StrategicModeB, sizeof(StrategicModeB));
    memcpy(&SuserX, &state->SuserX, sizeof(SuserX));
    memcpy(&SuserY, &state->SuserY, sizeof(SuserY));
    memcpy(&TERRAINset, &state->TERRAINset, sizeof(TERRAINset));
    memcpy(&TilesDugR, &state->TilesDugR, sizeof(TilesDugR));
    memcpy(&Tindex, &state->Tindex, sizeof(Tindex));
    memcpy(&TurnTab, &state->TurnTab, sizeof(TurnTab));
    memcpy(&YardMode, &state->YardMode, sizeof(YardMode));
    memcpy(&fd_3D57_006C, &state->fd_3D57_006C, sizeof(fd_3D57_006C));
    memcpy(&fd_3D57_0074, &state->fd_3D57_0074, sizeof(fd_3D57_0074));
    memcpy(&fd_3D57_0094, &state->fd_3D57_0094, sizeof(fd_3D57_0094));
    memcpy(&fd_3D57_00A4, &state->fd_3D57_00A4, sizeof(fd_3D57_00A4));
    memcpy(&fd_3D57_0164, &state->fd_3D57_0164, sizeof(fd_3D57_0164));
    memcpy(&fd_3D57_02A4, &state->fd_3D57_02A4, sizeof(fd_3D57_02A4));
    memcpy(&fd_3D57_02A8, &state->fd_3D57_02A8, sizeof(fd_3D57_02A8));
    memcpy(&fd_3D57_02AC, &state->fd_3D57_02AC, sizeof(fd_3D57_02AC));
    memcpy(&fd_3D57_02B0, &state->fd_3D57_02B0, sizeof(fd_3D57_02B0));
    memcpy(&fd_3D57_02B4, &state->fd_3D57_02B4, sizeof(fd_3D57_02B4));
    memcpy(&fd_3D57_02B8, &state->fd_3D57_02B8, sizeof(fd_3D57_02B8));
    memcpy(&fd_3D57_02BC, &state->fd_3D57_02BC, sizeof(fd_3D57_02BC));
    memcpy(&fd_3D57_02C0, &state->fd_3D57_02C0, sizeof(fd_3D57_02C0));
    memcpy(&fd_3D57_02C2, &state->fd_3D57_02C2, sizeof(fd_3D57_02C2));
    memcpy(&fd_3D57_0798, &state->fd_3D57_0798, sizeof(fd_3D57_0798));
    memcpy(&fd_3D57_07A2, &state->fd_3D57_07A2, sizeof(fd_3D57_07A2));
    memcpy(&fd_3D57_07A4, &state->fd_3D57_07A4, sizeof(fd_3D57_07A4));
    memcpy(&fd_3D57_07A6, &state->fd_3D57_07A6, sizeof(fd_3D57_07A6));
    memcpy(&fd_3D57_07A8, &state->fd_3D57_07A8, sizeof(fd_3D57_07A8));
    memcpy(&fd_3D57_07BE, &state->fd_3D57_07BE, sizeof(fd_3D57_07BE));
    memcpy(&fd_3D57_07C0, &state->fd_3D57_07C0, sizeof(fd_3D57_07C0));
    memcpy(&fd_3D57_07C8, &state->fd_3D57_07C8, sizeof(fd_3D57_07C8));
    memcpy(&fd_3D57_07CC, &state->fd_3D57_07CC, sizeof(fd_3D57_07CC));
    memcpy(&fd_3D57_0828, &state->fd_3D57_0828, sizeof(fd_3D57_0828));
    memcpy(&fd_3D57_0852, &state->fd_3D57_0852, sizeof(fd_3D57_0852));
    memcpy(&fd_3D57_0994, &state->fd_3D57_0994, sizeof(fd_3D57_0994));
    memcpy(&fd_3D57_099C, &state->fd_3D57_099C, sizeof(fd_3D57_099C));
    memcpy(&fd_3D57_09A4, &state->fd_3D57_09A4, sizeof(fd_3D57_09A4));
    memcpy(&fd_3D57_09AC, &state->fd_3D57_09AC, sizeof(fd_3D57_09AC));
    memcpy(&fd_3D57_0B14, &state->fd_3D57_0B14, sizeof(fd_3D57_0B14));
    memcpy(&fd_3D57_0B24, &state->fd_3D57_0B24, sizeof(fd_3D57_0B24));
    memcpy(&fd_3D57_0B36, &state->fd_3D57_0B36, sizeof(fd_3D57_0B36));
    memcpy(&fd_3D57_0C0E, &state->fd_3D57_0C0E, sizeof(fd_3D57_0C0E));
    memcpy(&fd_3D57_0C12, &state->fd_3D57_0C12, sizeof(fd_3D57_0C12));
    memcpy(&fd_3D57_0C14, &state->fd_3D57_0C14, sizeof(fd_3D57_0C14));
    memcpy(&fd_3D57_0C16, &state->fd_3D57_0C16, sizeof(fd_3D57_0C16));
    memcpy(&fd_3D57_0C18, &state->fd_3D57_0C18, sizeof(fd_3D57_0C18));
    memcpy(&fd_3D57_0C1A, &state->fd_3D57_0C1A, sizeof(fd_3D57_0C1A));
    memcpy(&fd_3D57_0C1C, &state->fd_3D57_0C1C, sizeof(fd_3D57_0C1C));
    memcpy(&fd_3D57_0C1E, &state->fd_3D57_0C1E, sizeof(fd_3D57_0C1E));
    memcpy(&fd_3D57_0C20, &state->fd_3D57_0C20, sizeof(fd_3D57_0C20));
    memcpy(&fd_3D57_0C22, &state->fd_3D57_0C22, sizeof(fd_3D57_0C22));
    memcpy(&fd_3D57_0C24, &state->fd_3D57_0C24, sizeof(fd_3D57_0C24));
    memcpy(&fd_3D57_0C26, &state->fd_3D57_0C26, sizeof(fd_3D57_0C26));
    memcpy(&fd_3D57_0C28, &state->fd_3D57_0C28, sizeof(fd_3D57_0C28));
    memcpy(&fd_3D57_0C2A, &state->fd_3D57_0C2A, sizeof(fd_3D57_0C2A));
    memcpy(&fd_3D57_0C2C, &state->fd_3D57_0C2C, sizeof(fd_3D57_0C2C));
    memcpy(&fd_3D57_0C2E, &state->fd_3D57_0C2E, sizeof(fd_3D57_0C2E));
    memcpy(&fd_3D57_0C30, &state->fd_3D57_0C30, sizeof(fd_3D57_0C30));
    memcpy(&fd_3D57_0C32, &state->fd_3D57_0C32, sizeof(fd_3D57_0C32));
    memcpy(&fd_3D57_0C34, &state->fd_3D57_0C34, sizeof(fd_3D57_0C34));
    memcpy(&fd_3D57_0C36, &state->fd_3D57_0C36, sizeof(fd_3D57_0C36));
    memcpy(&fd_3D57_0C3A, &state->fd_3D57_0C3A, sizeof(fd_3D57_0C3A));
    memcpy(&fd_3D57_0C3E, &state->fd_3D57_0C3E, sizeof(fd_3D57_0C3E));
    memcpy(&fd_3D57_0C40, &state->fd_3D57_0C40, sizeof(fd_3D57_0C40));
    memcpy(&fd_3D57_0C42, &state->fd_3D57_0C42, sizeof(fd_3D57_0C42));
    memcpy(&fd_3D57_0C44, &state->fd_3D57_0C44, sizeof(fd_3D57_0C44));
    memcpy(&fd_3D57_0C46, &state->fd_3D57_0C46, sizeof(fd_3D57_0C46));
    memcpy(&fd_3D57_0C48, &state->fd_3D57_0C48, sizeof(fd_3D57_0C48));
    memcpy(&fd_3E1D_0000, &state->fd_3E1D_0000, sizeof(fd_3E1D_0000));
    memcpy(&fd_3E1D_C89F, &state->fd_3E1D_C89F, sizeof(fd_3E1D_C89F));
    memcpy(&fd_3E1D_D89F, &state->fd_3E1D_D89F, sizeof(fd_3E1D_D89F));
    memcpy(&fd_50F6_0200, &state->fd_50F6_0200, sizeof(fd_50F6_0200));
    memcpy(&fd_50F6_0202, &state->fd_50F6_0202, sizeof(fd_50F6_0202));
    memcpy(&fd_50F6_0204, &state->fd_50F6_0204, sizeof(fd_50F6_0204));
    memcpy(&fd_50F6_0208, &state->fd_50F6_0208, sizeof(fd_50F6_0208));
    memcpy(&fd_50F6_020E, &state->fd_50F6_020E, sizeof(fd_50F6_020E));
    memcpy(&fd_50F6_0210, &state->fd_50F6_0210, sizeof(fd_50F6_0210));
    memcpy(&fd_50F6_0212, &state->fd_50F6_0212, sizeof(fd_50F6_0212));
    memcpy(&fd_50F6_0214, &state->fd_50F6_0214, sizeof(fd_50F6_0214));
    memcpy(&fd_50F6_0220, &state->fd_50F6_0220, sizeof(fd_50F6_0220));
    memcpy(&fd_50F6_0224, &state->fd_50F6_0224, sizeof(fd_50F6_0224));
    memcpy(&fd_50F6_0226, &state->fd_50F6_0226, sizeof(fd_50F6_0226));
    memcpy(&fd_50F6_0228, &state->fd_50F6_0228, sizeof(fd_50F6_0228));
    memcpy(&fd_50F6_022C, &state->fd_50F6_022C, sizeof(fd_50F6_022C));
    memcpy(&fd_50F6_023E, &state->fd_50F6_023E, sizeof(fd_50F6_023E));
    memcpy(&fd_50F6_0240, &state->fd_50F6_0240, sizeof(fd_50F6_0240));
    memcpy(&fd_50F6_0242, &state->fd_50F6_0242, sizeof(fd_50F6_0242));
    memcpy(&fd_50F6_0244, &state->fd_50F6_0244, sizeof(fd_50F6_0244));
    memcpy(&fd_50F6_0246, &state->fd_50F6_0246, sizeof(fd_50F6_0246));
    memcpy(&fd_50F6_0254, &state->fd_50F6_0254, sizeof(fd_50F6_0254));
    memcpy(&fd_50F6_0256, &state->fd_50F6_0256, sizeof(fd_50F6_0256));
    memcpy(&fd_50F6_02BA, &state->fd_50F6_02BA, sizeof(fd_50F6_02BA));
    memcpy(&fd_50F6_02BE, &state->fd_50F6_02BE, sizeof(fd_50F6_02BE));
    memcpy(&fd_50F6_02C0, &state->fd_50F6_02C0, sizeof(fd_50F6_02C0));
    memcpy(&fd_50F6_032C, &state->fd_50F6_032C, sizeof(fd_50F6_032C));
    memcpy(&fd_50F6_0332, &state->fd_50F6_0332, sizeof(fd_50F6_0332));
    memcpy(&fd_50F6_0334, &state->fd_50F6_0334, sizeof(fd_50F6_0334));
    memcpy(&fd_50F6_034C, &state->fd_50F6_034C, sizeof(fd_50F6_034C));
    memcpy(&fd_50F6_0352, &state->fd_50F6_0352, sizeof(fd_50F6_0352));
    memcpy(&fd_50F6_0354, &state->fd_50F6_0354, sizeof(fd_50F6_0354));
    memcpy(&fd_50F6_0356, &state->fd_50F6_0356, sizeof(fd_50F6_0356));
    memcpy(&fd_50F6_035E, &state->fd_50F6_035E, sizeof(fd_50F6_035E));
    memcpy(&fd_50F6_0364, &state->fd_50F6_0364, sizeof(fd_50F6_0364));
    memcpy(&fd_50F6_0366, &state->fd_50F6_0366, sizeof(fd_50F6_0366));
    memcpy(&fd_50F6_036C, &state->fd_50F6_036C, sizeof(fd_50F6_036C));
    memcpy(&fd_50F6_036E, &state->fd_50F6_036E, sizeof(fd_50F6_036E));
    memcpy(&fd_50F6_0376, &state->fd_50F6_0376, sizeof(fd_50F6_0376));
    memcpy(&fd_50F6_037A, &state->fd_50F6_037A, sizeof(fd_50F6_037A));
    memcpy(&fd_50F6_037C, &state->fd_50F6_037C, sizeof(fd_50F6_037C));
    memcpy(&fd_50F6_03E0, &state->fd_50F6_03E0, sizeof(fd_50F6_03E0));
    memcpy(&fd_50F6_03E2, &state->fd_50F6_03E2, sizeof(fd_50F6_03E2));
    memcpy(&fd_50F6_0400, &state->fd_50F6_0400, sizeof(fd_50F6_0400));
    memcpy(&fd_50F6_0402, &state->fd_50F6_0402, sizeof(fd_50F6_0402));
    memcpy(&fd_50F6_0404, &state->fd_50F6_0404, sizeof(fd_50F6_0404));
    memcpy(&fd_50F6_046A, &state->fd_50F6_046A, sizeof(fd_50F6_046A));
    memcpy(&fd_50F6_0470, &state->fd_50F6_0470, sizeof(fd_50F6_0470));
    memcpy(&fd_50F6_0472, &state->fd_50F6_0472, sizeof(fd_50F6_0472));
    memcpy(&fd_50F6_0476, &state->fd_50F6_0476, sizeof(fd_50F6_0476));
    memcpy(&fd_50F6_0478, &state->fd_50F6_0478, sizeof(fd_50F6_0478));
    memcpy(&fd_50F6_047A, &state->fd_50F6_047A, sizeof(fd_50F6_047A));
    memcpy(&fd_50F6_047E, &state->fd_50F6_047E, sizeof(fd_50F6_047E));
    memcpy(&fd_50F6_0488, &state->fd_50F6_0488, sizeof(fd_50F6_0488));
    memcpy(&fd_50F6_048E, &state->fd_50F6_048E, sizeof(fd_50F6_048E));
    memcpy(&fd_50F6_0492, &state->fd_50F6_0492, sizeof(fd_50F6_0492));
    memcpy(&fd_50F6_0496, &state->fd_50F6_0496, sizeof(fd_50F6_0496));
    memcpy(&fd_50F6_049A, &state->fd_50F6_049A, sizeof(fd_50F6_049A));
    memcpy(&fd_50F6_04A4, &state->fd_50F6_04A4, sizeof(fd_50F6_04A4));
    memcpy(&fd_50F6_04BE, &state->fd_50F6_04BE, sizeof(fd_50F6_04BE));
    memcpy(&fd_50F6_04C2, &state->fd_50F6_04C2, sizeof(fd_50F6_04C2));
    memcpy(&fd_50F6_04C4, &state->fd_50F6_04C4, sizeof(fd_50F6_04C4));
    memcpy(&fd_50F6_04C6, &state->fd_50F6_04C6, sizeof(fd_50F6_04C6));
    memcpy(&fd_50F6_04E0, &state->fd_50F6_04E0, sizeof(fd_50F6_04E0));
    memcpy(&fd_50F6_04E2, &state->fd_50F6_04E2, sizeof(fd_50F6_04E2));
    memcpy(&fd_50F6_04E4, &state->fd_50F6_04E4, sizeof(fd_50F6_04E4));
    memcpy(&fd_50F6_04F2, &state->fd_50F6_04F2, sizeof(fd_50F6_04F2));
    memcpy(&fd_50F6_04F4, &state->fd_50F6_04F4, sizeof(fd_50F6_04F4));
    memcpy(&fd_50F6_0502, &state->fd_50F6_0502, sizeof(fd_50F6_0502));
    memcpy(&fd_50F6_0504, &state->fd_50F6_0504, sizeof(fd_50F6_0504));
    memcpy(&fd_50F6_0506, &state->fd_50F6_0506, sizeof(fd_50F6_0506));
    memcpy(&fd_50F6_0508, &state->fd_50F6_0508, sizeof(fd_50F6_0508));
    memcpy(&fd_50F6_0510, &state->fd_50F6_0510, sizeof(fd_50F6_0510));
    memcpy(&fd_50F6_0516, &state->fd_50F6_0516, sizeof(fd_50F6_0516));
    memcpy(&fd_50F6_0596, &state->fd_50F6_0596, sizeof(fd_50F6_0596));
    memcpy(&fd_50F6_059E, &state->fd_50F6_059E, sizeof(fd_50F6_059E));
    memcpy(&fd_50F6_05A0, &state->fd_50F6_05A0, sizeof(fd_50F6_05A0));
    memcpy(&fd_50F6_0624, &state->fd_50F6_0624, sizeof(fd_50F6_0624));
    memcpy(&fd_50F6_0626, &state->fd_50F6_0626, sizeof(fd_50F6_0626));
    memcpy(&fd_50F6_06A6, &state->fd_50F6_06A6, sizeof(fd_50F6_06A6));
    memcpy(&fd_50F6_06AA, &state->fd_50F6_06AA, sizeof(fd_50F6_06AA));
    memcpy(&fd_50F6_06AC, &state->fd_50F6_06AC, sizeof(fd_50F6_06AC));
    memcpy(&fd_50F6_06AE, &state->fd_50F6_06AE, sizeof(fd_50F6_06AE));
    memcpy(&fd_50F6_072E, &state->fd_50F6_072E, sizeof(fd_50F6_072E));
    memcpy(&fd_50F6_0736, &state->fd_50F6_0736, sizeof(fd_50F6_0736));
    memcpy(&fd_50F6_073A, &state->fd_50F6_073A, sizeof(fd_50F6_073A));
    memcpy(&fd_50F6_073C, &state->fd_50F6_073C, sizeof(fd_50F6_073C));
    memcpy(&fd_50F6_07BC, &state->fd_50F6_07BC, sizeof(fd_50F6_07BC));
    memcpy(&fd_50F6_07C0, &state->fd_50F6_07C0, sizeof(fd_50F6_07C0));
    memcpy(&fd_50F6_07C2, &state->fd_50F6_07C2, sizeof(fd_50F6_07C2));
    memcpy(&fd_50F6_07C8, &state->fd_50F6_07C8, sizeof(fd_50F6_07C8));
    memcpy(&fd_50F6_07CA, &state->fd_50F6_07CA, sizeof(fd_50F6_07CA));
    memcpy(&fd_50F6_07CE, &state->fd_50F6_07CE, sizeof(fd_50F6_07CE));
    memcpy(&fd_50F6_084E, &state->fd_50F6_084E, sizeof(fd_50F6_084E));
    memcpy(&fd_50F6_0850, &state->fd_50F6_0850, sizeof(fd_50F6_0850));
    memcpy(&fd_50F6_0852, &state->fd_50F6_0852, sizeof(fd_50F6_0852));
    memcpy(&fd_50F6_0856, &state->fd_50F6_0856, sizeof(fd_50F6_0856));
    memcpy(&fd_50F6_08DA, &state->fd_50F6_08DA, sizeof(fd_50F6_08DA));
    memcpy(&fd_50F6_08DC, &state->fd_50F6_08DC, sizeof(fd_50F6_08DC));
    memcpy(&fd_50F6_08DE, &state->fd_50F6_08DE, sizeof(fd_50F6_08DE));
    memcpy(&fd_50F6_08E2, &state->fd_50F6_08E2, sizeof(fd_50F6_08E2));
    memcpy(&fd_50F6_08E8, &state->fd_50F6_08E8, sizeof(fd_50F6_08E8));
    memcpy(&fd_50F6_08EC, &state->fd_50F6_08EC, sizeof(fd_50F6_08EC));
    memcpy(&fd_50F6_08F0, &state->fd_50F6_08F0, sizeof(fd_50F6_08F0));
    memcpy(&fd_50F6_0970, &state->fd_50F6_0970, sizeof(fd_50F6_0970));
    memcpy(&fd_50F6_09F0, &state->fd_50F6_09F0, sizeof(fd_50F6_09F0));
    memcpy(&fd_50F6_09F2, &state->fd_50F6_09F2, sizeof(fd_50F6_09F2));
    memcpy(&fd_50F6_09FA, &state->fd_50F6_09FA, sizeof(fd_50F6_09FA));
    memcpy(&fd_50F6_09FC, &state->fd_50F6_09FC, sizeof(fd_50F6_09FC));
    memcpy(&fd_50F6_0A00, &state->fd_50F6_0A00, sizeof(fd_50F6_0A00));
    memcpy(&fd_50F6_0A02, &state->fd_50F6_0A02, sizeof(fd_50F6_0A02));
    memcpy(&fd_50F6_0A06, &state->fd_50F6_0A06, sizeof(fd_50F6_0A06));
    memcpy(&fd_50F6_0A0A, &state->fd_50F6_0A0A, sizeof(fd_50F6_0A0A));
    memcpy(&fd_50F6_0A8A, &state->fd_50F6_0A8A, sizeof(fd_50F6_0A8A));
    memcpy(&fd_50F6_0A8E, &state->fd_50F6_0A8E, sizeof(fd_50F6_0A8E));
    memcpy(&fd_50F6_0A90, &state->fd_50F6_0A90, sizeof(fd_50F6_0A90));
    memcpy(&fd_50F6_0A9C, &state->fd_50F6_0A9C, sizeof(fd_50F6_0A9C));
    memcpy(&fd_50F6_0A9E, &state->fd_50F6_0A9E, sizeof(fd_50F6_0A9E));
    memcpy(&fd_50F6_0AA0, &state->fd_50F6_0AA0, sizeof(fd_50F6_0AA0));
    memcpy(&fd_50F6_0AA2, &state->fd_50F6_0AA2, sizeof(fd_50F6_0AA2));
    memcpy(&fd_50F6_0AA6, &state->fd_50F6_0AA6, sizeof(fd_50F6_0AA6));
    memcpy(&fd_50F6_0AB2, &state->fd_50F6_0AB2, sizeof(fd_50F6_0AB2));
    memcpy(&fd_50F6_0AB6, &state->fd_50F6_0AB6, sizeof(fd_50F6_0AB6));
    memcpy(&fd_50F6_0AC4, &state->fd_50F6_0AC4, sizeof(fd_50F6_0AC4));
    memcpy(&fd_50F6_0AC6, &state->fd_50F6_0AC6, sizeof(fd_50F6_0AC6));
    memcpy(&fd_50F6_0AC8, &state->fd_50F6_0AC8, sizeof(fd_50F6_0AC8));
    memcpy(&fd_50F6_0ACA, &state->fd_50F6_0ACA, sizeof(fd_50F6_0ACA));
    memcpy(&fd_50F6_0AD6, &state->fd_50F6_0AD6, sizeof(fd_50F6_0AD6));
    memcpy(&fd_50F6_0AD8, &state->fd_50F6_0AD8, sizeof(fd_50F6_0AD8));
    memcpy(&fd_50F6_0ADA, &state->fd_50F6_0ADA, sizeof(fd_50F6_0ADA));
    memcpy(&fd_50F6_0AE8, &state->fd_50F6_0AE8, sizeof(fd_50F6_0AE8));
    memcpy(&fd_50F6_0AEA, &state->fd_50F6_0AEA, sizeof(fd_50F6_0AEA));
    memcpy(&fd_50F6_0AEC, &state->fd_50F6_0AEC, sizeof(fd_50F6_0AEC));
    memcpy(&fd_50F6_0AF8, &state->fd_50F6_0AF8, sizeof(fd_50F6_0AF8));
    memcpy(&fd_50F6_0AFA, &state->fd_50F6_0AFA, sizeof(fd_50F6_0AFA));
    memcpy(&fd_50F6_0B06, &state->fd_50F6_0B06, sizeof(fd_50F6_0B06));
    memcpy(&fd_50F6_0B08, &state->fd_50F6_0B08, sizeof(fd_50F6_0B08));
    memcpy(&fd_50F6_0B12, &state->fd_50F6_0B12, sizeof(fd_50F6_0B12));
    memcpy(&fd_50F6_0B1E, &state->fd_50F6_0B1E, sizeof(fd_50F6_0B1E));
    memcpy(&fd_50F6_0B20, &state->fd_50F6_0B20, sizeof(fd_50F6_0B20));
    memcpy(&fd_50F6_0B22, &state->fd_50F6_0B22, sizeof(fd_50F6_0B22));
    memcpy(&fd_50F6_0C26, &state->fd_50F6_0C26, sizeof(fd_50F6_0C26));
    memcpy(&fd_50F6_0C2A, &state->fd_50F6_0C2A, sizeof(fd_50F6_0C2A));
    memcpy(&fd_50F6_0C38, &state->fd_50F6_0C38, sizeof(fd_50F6_0C38));
    memcpy(&fd_50F6_0C3A, &state->fd_50F6_0C3A, sizeof(fd_50F6_0C3A));
    memcpy(&fd_50F6_0C3E, &state->fd_50F6_0C3E, sizeof(fd_50F6_0C3E));
    memcpy(&fd_50F6_0D40, &state->fd_50F6_0D40, sizeof(fd_50F6_0D40));
    memcpy(&fd_50F6_0D68, &state->fd_50F6_0D68, sizeof(fd_50F6_0D68));
    memcpy(&fd_50F6_0D6C, &state->fd_50F6_0D6C, sizeof(fd_50F6_0D6C));
    memcpy(&fd_50F6_0D70, &state->fd_50F6_0D70, sizeof(fd_50F6_0D70));
    memcpy(&fd_50F6_0D72, &state->fd_50F6_0D72, sizeof(fd_50F6_0D72));
    memcpy(&fd_50F6_0D9A, &state->fd_50F6_0D9A, sizeof(fd_50F6_0D9A));
    memcpy(&fd_50F6_0EAC, &state->fd_50F6_0EAC, sizeof(fd_50F6_0EAC));
    memcpy(&fd_50F6_0EB6, &state->fd_50F6_0EB6, sizeof(fd_50F6_0EB6));
    memcpy(&fd_50F6_0EF6, &state->fd_50F6_0EF6, sizeof(fd_50F6_0EF6));
    memcpy(&fd_50F6_0EF8, &state->fd_50F6_0EF8, sizeof(fd_50F6_0EF8));
    memcpy(&fd_50F6_0EFA, &state->fd_50F6_0EFA, sizeof(fd_50F6_0EFA));
    memcpy(&fd_50F6_0EFC, &state->fd_50F6_0EFC, sizeof(fd_50F6_0EFC));
    memcpy(&fd_50F6_0F06, &state->fd_50F6_0F06, sizeof(fd_50F6_0F06));
    memcpy(&fd_50F6_0F0C, &state->fd_50F6_0F0C, sizeof(fd_50F6_0F0C));
    memcpy(&fd_50F6_0F0E, &state->fd_50F6_0F0E, sizeof(fd_50F6_0F0E));
    memcpy(&fd_50F6_0F10, &state->fd_50F6_0F10, sizeof(fd_50F6_0F10));
    memcpy(&fd_50F6_0F12, &state->fd_50F6_0F12, sizeof(fd_50F6_0F12));
    memcpy(&fd_50F6_0F26, &state->fd_50F6_0F26, sizeof(fd_50F6_0F26));
    memcpy(&fd_50F6_0F2E, &state->fd_50F6_0F2E, sizeof(fd_50F6_0F2E));
    memcpy(&fd_50F6_0F30, &state->fd_50F6_0F30, sizeof(fd_50F6_0F30));
    memcpy(&fd_50F6_0F34, &state->fd_50F6_0F34, sizeof(fd_50F6_0F34));
    memcpy(&fd_50F6_0F36, &state->fd_50F6_0F36, sizeof(fd_50F6_0F36));
    memcpy(&fd_50F6_0F3E, &state->fd_50F6_0F3E, sizeof(fd_50F6_0F3E));
    memcpy(&fd_50F6_0F44, &state->fd_50F6_0F44, sizeof(fd_50F6_0F44));
    memcpy(&fd_50F6_0FB6, &state->fd_50F6_0FB6, sizeof(fd_50F6_0FB6));
    memcpy(&fd_50F6_0FBA, &state->fd_50F6_0FBA, sizeof(fd_50F6_0FBA));
    memcpy(&fd_50F6_0FBC, &state->fd_50F6_0FBC, sizeof(fd_50F6_0FBC));
    memcpy(&fd_50F6_0FC2, &state->fd_50F6_0FC2, sizeof(fd_50F6_0FC2));
    memcpy(&fd_50F6_0FFA, &state->fd_50F6_0FFA, sizeof(fd_50F6_0FFA));
    memcpy(&fd_50F6_0FFE, &state->fd_50F6_0FFE, sizeof(fd_50F6_0FFE));
    memcpy(&fd_50F6_1000, &state->fd_50F6_1000, sizeof(fd_50F6_1000));
    memcpy(&fd_50F6_1004, &state->fd_50F6_1004, sizeof(fd_50F6_1004));
    memcpy(&fd_50F6_1006, &state->fd_50F6_1006, sizeof(fd_50F6_1006));
    memcpy(&fd_50F6_1040, &state->fd_50F6_1040, sizeof(fd_50F6_1040));
    memcpy(&fd_50F6_1044, &state->fd_50F6_1044, sizeof(fd_50F6_1044));
    memcpy(&fd_50F6_104E, &state->fd_50F6_104E, sizeof(fd_50F6_104E));
    memcpy(&fd_50F6_1058, &state->fd_50F6_1058, sizeof(fd_50F6_1058));
    memcpy(&fd_50F6_105C, &state->fd_50F6_105C, sizeof(fd_50F6_105C));
    memcpy(&fd_50F6_105E, &state->fd_50F6_105E, sizeof(fd_50F6_105E));
    memcpy(&fd_50F6_1066, &state->fd_50F6_1066, sizeof(fd_50F6_1066));
    memcpy(&fd_50F6_1068, &state->fd_50F6_1068, sizeof(fd_50F6_1068));
    memcpy(&fd_50F6_106C, &state->fd_50F6_106C, sizeof(fd_50F6_106C));
    memcpy(&fd_50F6_1074, &state->fd_50F6_1074, sizeof(fd_50F6_1074));
    memcpy(&fd_50F6_107E, &state->fd_50F6_107E, sizeof(fd_50F6_107E));
    memcpy(&fd_50F6_1082, &state->fd_50F6_1082, sizeof(fd_50F6_1082));
    memcpy(&fd_50F6_108C, &state->fd_50F6_108C, sizeof(fd_50F6_108C));
    memcpy(&fd_50F6_108E, &state->fd_50F6_108E, sizeof(fd_50F6_108E));
    memcpy(&fd_50F6_109C, &state->fd_50F6_109C, sizeof(fd_50F6_109C));
    memcpy(&fd_50F6_10A0, &state->fd_50F6_10A0, sizeof(fd_50F6_10A0));
    memcpy(&fd_50F6_10A2, &state->fd_50F6_10A2, sizeof(fd_50F6_10A2));
    memcpy(&fd_50F6_10A6, &state->fd_50F6_10A6, sizeof(fd_50F6_10A6));
    memcpy(&fd_50F6_10AC, &state->fd_50F6_10AC, sizeof(fd_50F6_10AC));
    memcpy(&fd_50F6_10B0, &state->fd_50F6_10B0, sizeof(fd_50F6_10B0));
    memcpy(&fd_50F6_10B2, &state->fd_50F6_10B2, sizeof(fd_50F6_10B2));
    memcpy(&fd_50F6_10B8, &state->fd_50F6_10B8, sizeof(fd_50F6_10B8));
    memcpy(&fd_50F6_10BA, &state->fd_50F6_10BA, sizeof(fd_50F6_10BA));
    memcpy(&fd_50F6_10BC, &state->fd_50F6_10BC, sizeof(fd_50F6_10BC));
    memcpy(&fd_50F6_10C0, &state->fd_50F6_10C0, sizeof(fd_50F6_10C0));
    memcpy(&fd_50F6_10D2, &state->fd_50F6_10D2, sizeof(fd_50F6_10D2));
    memcpy(&fd_50F6_10DE, &state->fd_50F6_10DE, sizeof(fd_50F6_10DE));
    memcpy(&fd_50F6_10E0, &state->fd_50F6_10E0, sizeof(fd_50F6_10E0));
    memcpy(&fd_50F6_110C, &state->fd_50F6_110C, sizeof(fd_50F6_110C));
    memcpy(&fd_50F6_383A, &state->fd_50F6_383A, sizeof(fd_50F6_383A));
    memcpy(&fd_50F6_3856, &state->fd_50F6_3856, sizeof(fd_50F6_3856));
    memcpy(&fd_50F6_3858, &state->fd_50F6_3858, sizeof(fd_50F6_3858));
    memcpy(&fd_55B3_19BE, &state->fd_55B3_19BE, sizeof(fd_55B3_19BE));
    memcpy(&fd_55B3_19C0, &state->fd_55B3_19C0, sizeof(fd_55B3_19C0));
    memcpy(&fd_55B3_29A2, &state->fd_55B3_29A2, sizeof(fd_55B3_29A2));
    memcpy(&fd_55B3_2A42, &state->fd_55B3_2A42, sizeof(fd_55B3_2A42));
    memcpy(&fd_55B3_2CBC, &state->fd_55B3_2CBC, sizeof(fd_55B3_2CBC));
    memcpy(&g_3DB2, &state->g_3DB2, sizeof(g_3DB2));
    memcpy(&g_5A97, &state->g_5A97, sizeof(g_5A97));
    memcpy(&g_5AAC, &state->g_5AAC, sizeof(g_5AAC));
    memcpy(&modeLevels, &state->modeLevels, sizeof(modeLevels));
    fd_3D57_082A[0] = fd_50F6_0516;
    fd_3D57_082A[1] = fd_50F6_0626;
    fd_3D57_082A[2] = fd_50F6_073C;
    fd_3D57_082A[3] = fd_50F6_0856;
    fd_3D57_082A[4] = fd_50F6_08F0;
    fd_3D57_082A[5] = fd_50F6_05A0;
    fd_3D57_082A[6] = fd_50F6_06AE;
    fd_3D57_082A[7] = fd_50F6_07CE;
    fd_3D57_082A[8] = fd_50F6_0970;
    fd_3D57_082A[9] = fd_50F6_0A0A;
    fd_3D57_082A[10] = fd_50F6_05A0;
    fd_3D57_082A[11] = fd_50F6_06AE;
    fd_3D57_082A[12] = fd_50F6_07CE;
    fd_3D57_082A[13] = fd_50F6_0856;
    fd_3D57_082A[14] = fd_50F6_0A0A;
    fd_3D57_082A[15] = fd_50F6_0516;
    fd_3D57_082A[16] = fd_50F6_0626;
    fd_3D57_082A[17] = fd_50F6_073C;
    fd_3D57_082A[18] = fd_50F6_0A0A;
    fd_3D57_082A[19] = fd_50F6_0970;
}

static const uint8_t recovered_init_AlistM[1001] = { 0 };
static const uint8_t recovered_init_AlistS[1001] = { 0 };
static const uint8_t recovered_init_AlistT[1001] = { 0 };
static const uint8_t recovered_init_AlistX[1001] = { 0 };
static const uint8_t recovered_init_AlistY[1001] = { 0 };
static const uint8_t recovered_init_BlistM[501] = { 0 };
static const uint8_t recovered_init_BlistS[501] = { 0 };
static const uint8_t recovered_init_BlistT[501] = { 0 };
static const uint8_t recovered_init_BlistX[501] = { 0 };
static const uint8_t recovered_init_BlistY[501] = { 0 };
static const uint8_t recovered_init_CasteModeTabB[16] = {
    0x08, 0x01, 0x00, 0x03, 0x0E, 0x05, 0x00, 0x03, 0x0E, 0x05, 0x00, 0x00, 0x09, 0x09, 0x0A, 0x00
};
static const uint8_t recovered_init_CasteTabB[8] = {
    0x02, 0x00, 0x06, 0x00, 0x04, 0x00, 0x08, 0x00
};
static const uint8_t recovered_init_CurGndTileID[2] = {
    0xE8, 0x03
};
static const uint8_t recovered_init_Dx8[8] = {
    0x00, 0x01, 0x01, 0x01, 0x00, 0xFF, 0xFF, 0xFF
};
static const uint8_t recovered_init_Dx9[10] = {
    0x00, 0x00, 0x01, 0x01, 0x01, 0x00, 0xFF, 0xFF, 0xFF, 0x00
};
static const uint8_t recovered_init_Dy8[8] = {
    0xFF, 0xFF, 0x00, 0x01, 0x01, 0x01, 0x00, 0xFF
};
static const uint8_t recovered_init_Dy9[10] = {
    0x00, 0xFF, 0xFF, 0x00, 0x01, 0x01, 0x01, 0x00, 0xFF, 0x00
};
static const uint8_t recovered_init_ExitMapB[4096] = { 0 };
static const uint8_t recovered_init_ExitMapR[4096] = { 0 };
static const uint8_t recovered_init_ExpSubStates[8] = {
    0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF
};
static const uint8_t recovered_init_HoleMapB[64] = { 0 };
static const uint8_t recovered_init_HoleMapR[64] = { 0 };
static const uint8_t recovered_init_IdealCaste[14] = {
    0x3C, 0x00, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x06, 0x00, 0x02, 0x00
};
static const uint8_t recovered_init_LifeA[8192] = { 0 };
static const uint8_t recovered_init_LifeB[4096] = { 0 };
static const uint8_t recovered_init_LifeR[4096] = { 0 };
static const uint8_t recovered_init_LionIndex[2] = { 0 };
static const uint8_t recovered_init_MapA[8192] = { 0 };
static const uint8_t recovered_init_MapB[4096] = { 0 };
static const uint8_t recovered_init_MapR[4096] = { 0 };
static const uint8_t recovered_init_ModeMe[2] = {
    0x02, 0x00
};
static const uint8_t recovered_init_ModeTabB[48] = {
    0x02, 0x00, 0x04, 0x00, 0x01, 0x00, 0x07, 0x00, 0x0C, 0x00, 0x06, 0x00, 0x00, 0x0A, 0x00, 0x14,
    0x00, 0x46, 0x14, 0x0A, 0x00, 0x1E, 0x00, 0x00, 0x05, 0x14, 0x1E, 0x1E, 0x00, 0x00, 0x00, 0x0A,
    0x3C, 0x14, 0x00, 0x00, 0x0A, 0x14, 0x00, 0x32, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3C, 0x00, 0x00
};
static const uint8_t recovered_init_ModeTabSB[48] = {
    0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x01, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02,
    0x02, 0x02, 0x02, 0x04, 0x04, 0x02, 0x02, 0x02, 0x02, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x02,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02
};
static const uint8_t recovered_init_ModeTabWB[48] = {
    0x01, 0x02, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x04, 0x01, 0x01, 0x01, 0x04, 0x02, 0x02, 0x02,
    0x0D, 0x0D, 0x0D, 0x04, 0x04, 0x04, 0x02, 0x02, 0x0D, 0x0D, 0x04, 0x04, 0x04, 0x04, 0x04, 0x02,
    0x01, 0x01, 0x01, 0x02, 0x02, 0x02, 0x02, 0x02, 0x01, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02
};
static const uint8_t recovered_init_PherMapA[2048] = { 0 };
static const uint8_t recovered_init_PherMapBN[2048] = { 0 };
static const uint8_t recovered_init_PherMapBT[2048] = { 0 };
static const uint8_t recovered_init_PherMapRN[2048] = { 0 };
static const uint8_t recovered_init_PherMapRT[0x800] = { 0 };
static const uint8_t recovered_init_PillarState[2] = { 0 };
static const uint8_t recovered_init_PillarX[2] = { 0 };
static const uint8_t recovered_init_PillarY[2] = { 0 };
static const uint8_t recovered_init_RT3[54] = {
    0x5B, 0x54, 0x55, 0x5A, 0x5C, 0x56, 0x59, 0x58, 0x57, 0x5B, 0x55, 0x00, 0x59, 0x5E, 0x55, 0x00,
    0x59, 0x57, 0x5B, 0x54, 0x55, 0x59, 0x58, 0x57, 0x00, 0x00, 0x00, 0x5B, 0x55, 0x00, 0x59, 0x57,
    0x00, 0x00, 0x00, 0x00, 0x5B, 0x55, 0x00, 0x5A, 0x56, 0x00, 0x59, 0x57, 0x00, 0x5B, 0x55, 0x00,
    0x5A, 0x5E, 0x55, 0x59, 0x58, 0x57
};
static const uint8_t recovered_init_RT5[150] = {
    0x00, 0x5B, 0x54, 0x55, 0x00, 0x5B, 0x5C, 0x5C, 0x56, 0x00, 0x5A, 0x5C, 0x5C, 0x5E, 0x55, 0x59,
    0x5D, 0x5C, 0x5C, 0x56, 0x00, 0x59, 0x58, 0x58, 0x57, 0x00, 0x00, 0x5B, 0x54, 0x55, 0x00, 0x5B,
    0x5C, 0x5C, 0x56, 0x5B, 0x5C, 0x5C, 0x5F, 0x57, 0x5A, 0x5F, 0x58, 0x57, 0x00, 0x59, 0x57, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x5B, 0x54, 0x55, 0x5B, 0x54, 0x5C, 0x5F, 0x57, 0x5A, 0x5F, 0x58, 0x57,
    0x00, 0x59, 0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x5B, 0x54, 0x54, 0x54, 0x55, 0x59, 0x5D, 0x5C, 0x5C, 0x56, 0x00, 0x59, 0x5D, 0x5C, 0x56, 0x00,
    0x00, 0x59, 0x58, 0x57, 0x5B, 0x54, 0x54, 0x54, 0x55, 0x59, 0x5D, 0x5C, 0x5F, 0x57, 0x00, 0x5A,
    0x5C, 0x56, 0x00, 0x5B, 0x5C, 0x5F, 0x57, 0x00, 0x59, 0x58, 0x57, 0x00, 0x00, 0x00, 0x00, 0x5B,
    0x54, 0x55, 0x00, 0x5B, 0x5C, 0x5F, 0x57, 0x5B, 0x5C, 0x5C, 0x56, 0x00, 0x59, 0x5D, 0x5C, 0x5E,
    0x55, 0x00, 0x59, 0x58, 0x58, 0x57
};
static const uint8_t recovered_init_RlistM[501] = { 0 };
static const uint8_t recovered_init_RlistS[501] = { 0 };
static const uint8_t recovered_init_RlistT[501] = { 0 };
static const uint8_t recovered_init_RlistX[501] = { 0 };
static const uint8_t recovered_init_RlistY[501] = { 0 };
static const uint8_t recovered_init_SowTab[8] = {
    0x72, 0x73, 0x71, 0x70, 0x72, 0x73, 0x71, 0x70
};
static const uint8_t recovered_init_TurnTab[72] = {
    0x00, 0x01, 0x01, 0x01, 0x07, 0x07, 0x07, 0x07, 0x00, 0x01, 0x02, 0x02, 0x02, 0x02, 0x00, 0x00,
    0x01, 0x01, 0x02, 0x03, 0x03, 0x03, 0x03, 0x01, 0x02, 0x02, 0x02, 0x03, 0x04, 0x04, 0x04, 0x04,
    0x03, 0x03, 0x03, 0x03, 0x04, 0x05, 0x05, 0x05, 0x06, 0x06, 0x04, 0x04, 0x04, 0x05, 0x06, 0x06,
    0x07, 0x07, 0x07, 0x05, 0x05, 0x05, 0x06, 0x07, 0x00, 0x00, 0x00, 0x00, 0x06, 0x06, 0x06, 0x07,
    0x00, 0x01, 0xFE, 0x03, 0xFC, 0x05, 0xFA, 0x07
};
static const uint8_t recovered_init_fd_3D57_006C[8] = {
    0x00, 0x01, 0xFF, 0x02, 0xFE, 0x03, 0xFD, 0x04
};
static const uint8_t recovered_init_fd_3D57_0074[32] = {
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
static const uint8_t recovered_init_fd_3D57_0094[16] = {
    0x00, 0x02, 0x02, 0x02, 0x04, 0x02, 0x06, 0x06, 0x08, 0x06, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
};
static const uint8_t recovered_init_fd_3D57_00A4[192] = { 0 };
static const uint8_t recovered_init_fd_3D57_02A4[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02A8[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02AC[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02B0[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02B4[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02B8[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02BC[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_02C0[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_02C2[76] = {
    0x00, 0x00, 0x01, 0x00, 0x02, 0x00, 0x07, 0x00, 0x09, 0x00, 0x0A, 0x00, 0x0B, 0x00, 0x0D, 0x00,
    0x0E, 0x00, 0x0F, 0x00, 0x11, 0x00, 0x12, 0x00, 0x13, 0x00, 0x14, 0x00, 0x17, 0x00, 0x15, 0x00,
    0x16, 0x00, 0x17, 0x00, 0x18, 0x00, 0x18, 0x00, 0x1A, 0x00, 0x1B, 0x00, 0x1C, 0x00, 0x1D, 0x00,
    0x1E, 0x00, 0x20, 0x00, 0x23, 0x00, 0x24, 0x00, 0x25, 0x00, 0x26, 0x00, 0x28, 0x00, 0x2A, 0x00,
    0x2D, 0x00, 0x2C, 0x00, 0x2F, 0x00, 0x31, 0x00, 0x29, 0x00, 0xFF, 0xFF
};
static const uint8_t recovered_init_fd_3D57_0798[8] = { 0 };
static const uint8_t recovered_init_fd_3D57_07A2[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_07A4[2] = {
    0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_07A6[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_07BE[2] = {
    0xFF, 0xFF
};
static const uint8_t recovered_init_fd_3D57_07C0[8] = {
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x02, 0x00
};
static const uint8_t recovered_init_fd_3D57_07C8[4] = {
    0x01, 0x00, 0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_0828[2] = {
    0x3F, 0x00
};
static const uint8_t recovered_init_fd_3D57_0994[8] = {
    0x00, 0x03, 0x04, 0x03, 0x00, 0xFD, 0xFC, 0xFD
};
static const uint8_t recovered_init_fd_3D57_099C[8] = {
    0xFC, 0xFD, 0x00, 0x03, 0x04, 0x03, 0x00, 0xFD
};
static const uint8_t recovered_init_fd_3D57_09A4[8] = {
    0x00, 0x01, 0x01, 0x01, 0x00, 0xFF, 0xFF, 0xFF
};
static const uint8_t recovered_init_fd_3D57_09AC[8] = {
    0xFF, 0xFF, 0x00, 0x01, 0x01, 0x01, 0x00, 0xFF
};
static const uint8_t recovered_init_fd_3D57_0B14[16] = {
    0x00, 0x00, 0x00, 0x00, 0x26, 0x00, 0x27, 0x00, 0x26, 0x00, 0x34, 0x00, 0x26, 0x00, 0x34, 0x00
};
static const uint8_t recovered_init_fd_3D57_0B24[18] = {
    0x48, 0x00, 0x3E, 0x00, 0x03, 0x01, 0x03, 0x03, 0x02, 0x02, 0x04, 0x05, 0x06, 0x01, 0x04, 0x04,
    0x06, 0x00
};
static const uint8_t recovered_init_fd_3D57_0B36[48] = {
    0x02, 0x02, 0x02, 0x02, 0x02, 0x06, 0x06, 0x06, 0x04, 0x04, 0x08, 0x08, 0x02, 0x02, 0x02, 0x06,
    0x04, 0x08, 0x02, 0x02, 0x02, 0x02, 0x06, 0x06, 0x02, 0x02, 0x02, 0x02, 0x02, 0x06, 0x06, 0x06,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x06, 0x06, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x06
};
static const uint8_t recovered_init_fd_3D57_0C0E[2] = {
    0x02, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C12[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C14[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C16[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C18[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C1A[4] = {
    0x28, 0x00, 0x00, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C1E[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C20[2] = {
    0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C22[2] = {
    0xFD, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C24[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C26[2] = {
    0xFF, 0xFF
};
static const uint8_t recovered_init_fd_3D57_0C28[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C2A[2] = {
    0x14, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C2C[2] = {
    0xB4, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C2E[2] = {
    0x49, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C30[2] = {
    0x02, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C32[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C34[2] = {
    0x0C, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C36[4] = {
    0x04, 0x06, 0xFC, 0xFA
};
static const uint8_t recovered_init_fd_3D57_0C3A[4] = {
    0xFC, 0x00, 0x04, 0x00
};
static const uint8_t recovered_init_fd_3D57_0C3E[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C40[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C42[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C44[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C46[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_0C48[2] = { 0 };
static const uint8_t recovered_init_fd_3E1D_0000[384] = { 0 };
static const uint8_t recovered_init_fd_3E1D_C89F[2048] = { 0 };
static const uint8_t recovered_init_fd_3E1D_D89F[2048] = { 0 };
static const uint8_t recovered_init_fd_3D57_07A8[2] = { 0 };
static const uint8_t recovered_init_fd_3D57_07AA[4] = {
    0x01, 0x00, 0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_07AE[2] = {
    0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_07B0[2] = {
    0x01, 0x00
};
static const uint8_t recovered_init_fd_3D57_07B2[4] = { 0 };
static const uint8_t recovered_init_fd_3D57_07CC[14] = {
    0x01, 0x00, 0x15, 0x00, 0x07, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x01, 0x02, 0x03
};
static const uint8_t recovered_init_fd_3D57_0164[32] = { 0 };
static const uint8_t recovered_init_fd_3D57_0184[160] = { 0 };

void recovered_state_init(RecoveredState *state)
{
    memset(state, 0, sizeof(*state));
    memcpy(&state->AlistM, recovered_init_AlistM, 1001);
    memcpy(&state->AlistS, recovered_init_AlistS, 1001);
    memcpy(&state->AlistT, recovered_init_AlistT, 1001);
    memcpy(&state->AlistX, recovered_init_AlistX, 1001);
    memcpy(&state->AlistY, recovered_init_AlistY, 1001);
    memcpy(&state->BlistM, recovered_init_BlistM, 501);
    memcpy(&state->BlistS, recovered_init_BlistS, 501);
    memcpy(&state->BlistT, recovered_init_BlistT, 501);
    memcpy(&state->BlistX, recovered_init_BlistX, 501);
    memcpy(&state->BlistY, recovered_init_BlistY, 501);
    memcpy(&state->CasteModeTabB, recovered_init_CasteModeTabB, 16);
    memcpy(&state->CasteTabB, recovered_init_CasteTabB, 8);
    memcpy(&state->CurGndTileID, recovered_init_CurGndTileID, 2);
    memcpy(&state->Dx8, recovered_init_Dx8, 8);
    memcpy(&state->Dx9, recovered_init_Dx9, 10);
    memcpy(&state->Dy8, recovered_init_Dy8, 8);
    memcpy(&state->Dy9, recovered_init_Dy9, 10);
    memcpy(&state->ExitMapB, recovered_init_ExitMapB, 4096);
    memcpy(&state->ExitMapR, recovered_init_ExitMapR, 4096);
    memcpy(&state->ExpSubStates, recovered_init_ExpSubStates, 8);
    memcpy(&state->HoleMapB, recovered_init_HoleMapB, 64);
    memcpy(&state->HoleMapR, recovered_init_HoleMapR, 64);
    memcpy(&state->IdealCaste, recovered_init_IdealCaste, 14);
    memcpy(&state->LifeA, recovered_init_LifeA, 8192);
    memcpy(&state->LifeB, recovered_init_LifeB, 4096);
    memcpy(&state->LifeR, recovered_init_LifeR, 4096);
    memcpy(&state->LionIndex, recovered_init_LionIndex, 2);
    memcpy(&state->MapA, recovered_init_MapA, 8192);
    memcpy(&state->MapB, recovered_init_MapB, 4096);
    memcpy(&state->MapR, recovered_init_MapR, 4096);
    memcpy(&state->ModeMe, recovered_init_ModeMe, 2);
    memcpy(&state->ModeTabB, recovered_init_ModeTabB, 48);
    memcpy(&state->ModeTabSB, recovered_init_ModeTabSB, 48);
    memcpy(&state->ModeTabWB, recovered_init_ModeTabWB, 48);
    memcpy(&state->PherMapA, recovered_init_PherMapA, 2048);
    memcpy(&state->PherMapBN, recovered_init_PherMapBN, 2048);
    memcpy(&state->PherMapBT, recovered_init_PherMapBT, 2048);
    memcpy(&state->PherMapRN, recovered_init_PherMapRN, 2048);
    memcpy(&state->PherMapRT, recovered_init_PherMapRT, 2048);
    memcpy(&state->PillarState, recovered_init_PillarState, 2);
    memcpy(&state->PillarX, recovered_init_PillarX, 2);
    memcpy(&state->PillarY, recovered_init_PillarY, 2);
    memcpy(&state->RT3, recovered_init_RT3, 54);
    memcpy(&state->RT5, recovered_init_RT5, 150);
    memcpy(&state->RlistM, recovered_init_RlistM, 501);
    memcpy(&state->RlistS, recovered_init_RlistS, 501);
    memcpy(&state->RlistT, recovered_init_RlistT, 501);
    memcpy(&state->RlistX, recovered_init_RlistX, 501);
    memcpy(&state->RlistY, recovered_init_RlistY, 501);
    memcpy(&state->SowTab, recovered_init_SowTab, 8);
    memcpy(&state->TurnTab, recovered_init_TurnTab, 72);
    memcpy(&state->fd_3D57_006C, recovered_init_fd_3D57_006C, 8);
    memcpy(&state->fd_3D57_0074, recovered_init_fd_3D57_0074, 32);
    memcpy(&state->fd_3D57_0094, recovered_init_fd_3D57_0094, 16);
    memcpy(&state->fd_3D57_00A4, recovered_init_fd_3D57_00A4, 192);
    memcpy(&state->fd_3D57_02A4, recovered_init_fd_3D57_02A4, 4);
    memcpy(&state->fd_3D57_02A8, recovered_init_fd_3D57_02A8, 4);
    memcpy(&state->fd_3D57_02AC, recovered_init_fd_3D57_02AC, 4);
    memcpy(&state->fd_3D57_02B0, recovered_init_fd_3D57_02B0, 4);
    memcpy(&state->fd_3D57_02B4, recovered_init_fd_3D57_02B4, 4);
    memcpy(&state->fd_3D57_02B8, recovered_init_fd_3D57_02B8, 4);
    memcpy(&state->fd_3D57_02BC, recovered_init_fd_3D57_02BC, 4);
    memcpy(&state->fd_3D57_02C0, recovered_init_fd_3D57_02C0, 2);
    memcpy(&state->fd_3D57_02C2, recovered_init_fd_3D57_02C2, 76);
    memcpy(&state->fd_3D57_0798, recovered_init_fd_3D57_0798, 8);
    memcpy(&state->fd_3D57_07A2, recovered_init_fd_3D57_07A2, 2);
    memcpy(&state->fd_3D57_07A4, recovered_init_fd_3D57_07A4, 2);
    memcpy(&state->fd_3D57_07A6, recovered_init_fd_3D57_07A6, 2);
    memcpy(&state->fd_3D57_07BE, recovered_init_fd_3D57_07BE, 2);
    memcpy(&state->fd_3D57_07C0, recovered_init_fd_3D57_07C0, 8);
    memcpy(&state->fd_3D57_07C8, recovered_init_fd_3D57_07C8, 4);
    memcpy(&state->fd_3D57_0828, recovered_init_fd_3D57_0828, 2);
    memcpy(&state->fd_3D57_0994, recovered_init_fd_3D57_0994, 8);
    memcpy(&state->fd_3D57_099C, recovered_init_fd_3D57_099C, 8);
    memcpy(&state->fd_3D57_09A4, recovered_init_fd_3D57_09A4, 8);
    memcpy(&state->fd_3D57_09AC, recovered_init_fd_3D57_09AC, 8);
    memcpy(&state->fd_3D57_0B14, recovered_init_fd_3D57_0B14, 16);
    memcpy(&state->fd_3D57_0B24, recovered_init_fd_3D57_0B24, 18);
    memcpy(&state->fd_3D57_0B36, recovered_init_fd_3D57_0B36, 48);
    memcpy(&state->fd_3D57_0C0E, recovered_init_fd_3D57_0C0E, 2);
    memcpy(&state->fd_3D57_0C12, recovered_init_fd_3D57_0C12, 2);
    memcpy(&state->fd_3D57_0C14, recovered_init_fd_3D57_0C14, 2);
    memcpy(&state->fd_3D57_0C16, recovered_init_fd_3D57_0C16, 2);
    memcpy(&state->fd_3D57_0C18, recovered_init_fd_3D57_0C18, 2);
    memcpy(&state->fd_3D57_0C1A, recovered_init_fd_3D57_0C1A, 4);
    memcpy(&state->fd_3D57_0C1E, recovered_init_fd_3D57_0C1E, 2);
    memcpy(&state->fd_3D57_0C20, recovered_init_fd_3D57_0C20, 2);
    memcpy(&state->fd_3D57_0C22, recovered_init_fd_3D57_0C22, 2);
    memcpy(&state->fd_3D57_0C24, recovered_init_fd_3D57_0C24, 2);
    memcpy(&state->fd_3D57_0C26, recovered_init_fd_3D57_0C26, 2);
    memcpy(&state->fd_3D57_0C28, recovered_init_fd_3D57_0C28, 2);
    memcpy(&state->fd_3D57_0C2A, recovered_init_fd_3D57_0C2A, 2);
    memcpy(&state->fd_3D57_0C2C, recovered_init_fd_3D57_0C2C, 2);
    memcpy(&state->fd_3D57_0C2E, recovered_init_fd_3D57_0C2E, 2);
    memcpy(&state->fd_3D57_0C30, recovered_init_fd_3D57_0C30, 2);
    memcpy(&state->fd_3D57_0C32, recovered_init_fd_3D57_0C32, 2);
    memcpy(&state->fd_3D57_0C34, recovered_init_fd_3D57_0C34, 2);
    memcpy(&state->fd_3D57_0C36, recovered_init_fd_3D57_0C36, 4);
    memcpy(&state->fd_3D57_0C3A, recovered_init_fd_3D57_0C3A, 4);
    memcpy(&state->fd_3D57_0C3E, recovered_init_fd_3D57_0C3E, 2);
    memcpy(&state->fd_3D57_0C40, recovered_init_fd_3D57_0C40, 2);
    memcpy(&state->fd_3D57_0C42, recovered_init_fd_3D57_0C42, 2);
    memcpy(&state->fd_3D57_0C44, recovered_init_fd_3D57_0C44, 2);
    memcpy(&state->fd_3D57_0C46, recovered_init_fd_3D57_0C46, 2);
    memcpy(&state->fd_3D57_0C48, recovered_init_fd_3D57_0C48, 2);
    memcpy(&state->fd_3E1D_0000, recovered_init_fd_3E1D_0000, 384);
    memcpy(&state->fd_3E1D_C89F, recovered_init_fd_3E1D_C89F, 2048);
    memcpy(&state->fd_3E1D_D89F, recovered_init_fd_3E1D_D89F, 2048);
    memcpy((uint8_t *)&state->fd_3D57_07A8 + 0, recovered_init_fd_3D57_07A8, 2);
    memcpy((uint8_t *)&state->fd_3D57_07A8 + 2, recovered_init_fd_3D57_07AA, 4);
    memcpy((uint8_t *)&state->fd_3D57_07A8 + 6, recovered_init_fd_3D57_07AE, 2);
    memcpy((uint8_t *)&state->fd_3D57_07A8 + 8, recovered_init_fd_3D57_07B0, 2);
    memcpy((uint8_t *)&state->fd_3D57_07A8 + 10, recovered_init_fd_3D57_07B2, 4);
    memcpy((uint8_t *)&state->fd_3D57_07CC + 0, recovered_init_fd_3D57_07CC, 14);
    memcpy((uint8_t *)&state->fd_3D57_0164 + 0, recovered_init_fd_3D57_0164, 32);
    memcpy((uint8_t *)&state->fd_3D57_0164 + 32, recovered_init_fd_3D57_0184, 160);
}

void recovered_bind_begin(RecoveredBindingFrame *frame, const RecoveredState *state)
{
    recovered_export(&frame->previous);
    recovered_import(state);
}

void recovered_bind_end(RecoveredBindingFrame *frame, RecoveredState *state)
{
    recovered_export(state);
    recovered_import(&frame->previous);
}
