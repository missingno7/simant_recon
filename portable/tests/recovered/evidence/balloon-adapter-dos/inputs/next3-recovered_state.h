#ifndef SIMANT_RECOVERED_STATE_H
#define SIMANT_RECOVERED_STATE_H

#include <stdint.h>
#include <stddef.h>

typedef struct { int16_t v; int16_t h; } RecoveredPoint;
typedef struct { int16_t x; int16_t y; } RecoveredXY;

struct Pt {
    int16_t x;
    int16_t y;
};
struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};
typedef union { struct Pt point; uint8_t bytes[18]; } RecoveredPointBytes18;

typedef struct RecoveredState {
    void * * AdviceStrs;
    uint8_t AlistM[1001];
    uint8_t AlistS[1001];
    uint8_t AlistT[1001];
    uint8_t AlistX[1001];
    uint8_t AlistY[1001];
    int16_t AntsEatenByLions;
    int32_t BAntsEaten;
    int16_t Barrier;
    uint8_t BlistM[501];
    uint8_t BlistS[501];
    uint8_t BlistT[501];
    uint8_t BlistX[501];
    uint8_t BlistY[501];
    int16_t BpopT;
    int8_t CasteModeTabB[16];
    int16_t CasteTabB[4];
    int16_t ChaseSpid;
    int16_t CurExpTool;
    int16_t CurGndTileID;
    int16_t Cycle;
    int16_t DROPdir;
    int16_t DeathCnt;
    int8_t Dx8[8];
    int8_t Dx9[10];
    int8_t Dy8[8];
    int8_t Dy9[10];
    int16_t EatCnt;
    uint8_t ExitMapB[64][64];
    uint8_t ExitMapR[64][64];
    int8_t ExpSubStates[8];
    int16_t FoodB;
    int16_t FoodR;
    int16_t FuzLocX;
    int16_t FuzLocY;
    int16_t HealthB;
    int16_t HealthR;
    uint8_t HoleMapB[64];
    uint8_t HoleMapR[64];
    int16_t IdealCaste[7];
    int16_t InitialLions;
    uint8_t LifeA[128][64];
    uint8_t LifeB[64][64];
    uint8_t LifeR[64][64];
    int16_t LionIndex;
    uint8_t LionListM[10];
    uint8_t LionListS[10];
    uint8_t LionListT[10];
    uint8_t LionListX[10];
    uint8_t LionListY[10];
    int16_t ListIndexA;
    int16_t ListIndexB;
    int16_t ListIndexR;
    uint8_t MapA[128][64];
    uint8_t MapB[64][64];
    int16_t MapPlane;
    uint8_t MapR[64][64];
    int16_t MeHealth;
    int16_t MeLocX;
    int16_t MeLocY;
    int16_t MePlane;
    int16_t ModeAuto;
    int16_t ModeMe;
    int16_t ModeTabB[24];
    int8_t ModeTabSB[6][8];
    int8_t ModeTabWB[6][8];
    uint8_t PherMapA[64][32];
    uint8_t PherMapBN[64][32];
    uint8_t PherMapBT[64][32];
    uint8_t PherMapRN[64][32];
    uint8_t PherMapRT[64][32];
    int16_t PillDir;
    int16_t PillarMap[6];
    int16_t PillarSeg;
    int16_t PillarState;
    int16_t PillarX;
    int16_t PillarY;
    int32_t RAntsEaten;
    uint8_t RT3[18][3];
    uint8_t RT5[30][5];
    int16_t RedLocX;
    int16_t RedLocY;
    int16_t RedPlane;
    uint8_t RlistM[501];
    uint8_t RlistS[501];
    uint8_t RlistT[501];
    uint8_t RlistX[501];
    uint8_t RlistY[501];
    int16_t RpopT;
    int16_t SCorpseBase;
    int16_t SMode;
    int16_t Scycle;
    int16_t Scycle2;
    int16_t SowDir[3];
    int16_t SowSave[3];
    uint8_t SowTab[8];
    int16_t SowX[3];
    int16_t SowY[3];
    int16_t SpidBurpCnt;
    int16_t SpidRevenge;
    int16_t Starg;
    int16_t StargLife;
    int16_t StrategicModeB;
    int16_t SuserX;
    int16_t SuserY;
    int16_t TERRAINset;
    int16_t TilesDugR;
    int16_t Tindex;
    int8_t TurnTab[9][8];
    int16_t YardMode;
    int8_t fd_3D57_006C[8];
    int16_t fd_3D57_0074[16];
    int8_t fd_3D57_0094[16];
    uint8_t fd_3D57_00A4[12][16];
    uint8_t fd_3D57_0164[12][16];
    int16_t fd_3D57_02A4[2];
    int16_t fd_3D57_02A8[2];
    int16_t fd_3D57_02AC[2];
    int16_t fd_3D57_02B0[2];
    int16_t fd_3D57_02B4[2];
    int16_t fd_3D57_02B8[2];
    int16_t fd_3D57_02BC[2];
    int16_t fd_3D57_02C0;
    int16_t fd_3D57_02C2[38];
    int16_t fd_3D57_0798[4];
    int16_t fd_3D57_07A2;
    int16_t fd_3D57_07A4;
    int16_t fd_3D57_07A6;
    int16_t fd_3D57_07A8[7];
    int16_t fd_3D57_07BE;
    int16_t fd_3D57_07C0[4];
    int16_t fd_3D57_07C8[2];
    int16_t fd_3D57_07CC[7];
    int16_t fd_3D57_0828;
    int16_t * fd_3D57_0852[40];
    int8_t fd_3D57_0994[8];
    int8_t fd_3D57_099C[8];
    int8_t fd_3D57_09A4[8];
    int8_t fd_3D57_09AC[8];
    struct Pt fd_3D57_0B14[4];
    RecoveredPointBytes18 fd_3D57_0B24[1];
    int8_t fd_3D57_0B36[48];
    int16_t fd_3D57_0C0E;
    int16_t fd_3D57_0C12;
    int16_t fd_3D57_0C14;
    int16_t fd_3D57_0C16;
    int16_t fd_3D57_0C18;
    int16_t fd_3D57_0C1A[2];
    int16_t fd_3D57_0C1C;
    int16_t fd_3D57_0C1E;
    int16_t fd_3D57_0C20;
    int16_t fd_3D57_0C22;
    int16_t fd_3D57_0C24;
    int16_t fd_3D57_0C26;
    int16_t fd_3D57_0C28;
    int16_t fd_3D57_0C2A;
    int16_t fd_3D57_0C2C;
    int16_t fd_3D57_0C2E;
    int16_t fd_3D57_0C30;
    int16_t fd_3D57_0C32;
    int16_t fd_3D57_0C34;
    int8_t fd_3D57_0C36[4];
    int8_t fd_3D57_0C3A[4];
    int16_t fd_3D57_0C3E;
    int16_t fd_3D57_0C40;
    int16_t fd_3D57_0C42;
    int16_t fd_3D57_0C44;
    int16_t fd_3D57_0C46;
    int16_t fd_3D57_0C48;
    int16_t fd_3E1D_0000[16][12];
    uint8_t fd_3E1D_C89F[64][32];
    uint8_t fd_3E1D_D89F[64][32];
    int16_t fd_50F6_0200;
    int16_t fd_50F6_0202;
    int32_t fd_50F6_0204;
    int16_t fd_50F6_0208;
    int16_t fd_50F6_020E;
    int16_t fd_50F6_0210;
    int16_t fd_50F6_0212;
    int32_t fd_50F6_0214;
    int32_t fd_50F6_0220;
    int16_t fd_50F6_0224;
    int16_t fd_50F6_0226;
    int16_t fd_50F6_0228;
    int16_t fd_50F6_022C;
    int16_t fd_50F6_023E;
    int16_t fd_50F6_0240;
    int16_t fd_50F6_0242;
    int16_t fd_50F6_0244;
    int16_t fd_50F6_0246;
    int16_t fd_50F6_0254;
    uint8_t fd_50F6_0256[100];
    int8_t * * fd_50F6_02BA;
    int16_t fd_50F6_02BE;
    uint8_t fd_50F6_02C0[100];
    int16_t fd_50F6_032C;
    int16_t fd_50F6_0332;
    int16_t fd_50F6_0334[12];
    void * * fd_50F6_034C;
    int16_t fd_50F6_0352;
    int16_t fd_50F6_0354;
    int16_t fd_50F6_0356;
    int16_t fd_50F6_035E;
    int16_t fd_50F6_0364;
    int16_t fd_50F6_0366;
    int16_t fd_50F6_036C;
    int16_t fd_50F6_036E;
    int16_t fd_50F6_0376;
    int16_t fd_50F6_037A;
    uint8_t fd_50F6_037C[100];
    int16_t fd_50F6_03E0;
    int16_t fd_50F6_03E2;
    int16_t fd_50F6_0400;
    int16_t fd_50F6_0402;
    uint8_t fd_50F6_0404[100];
    int16_t fd_50F6_046A;
    int16_t fd_50F6_0470;
    int32_t fd_50F6_0472;
    int16_t fd_50F6_0476;
    int16_t fd_50F6_0478;
    int16_t fd_50F6_047A;
    int16_t fd_50F6_047E;
    int16_t fd_50F6_0488;
    int16_t fd_50F6_048E;
    int16_t fd_50F6_0492;
    int16_t fd_50F6_0496;
    int16_t fd_50F6_049A;
    int16_t fd_50F6_04A4;
    int16_t fd_50F6_04BE;
    int16_t fd_50F6_04C2;
    int16_t fd_50F6_04C4;
    int16_t fd_50F6_04C6;
    int16_t fd_50F6_04E0;
    int16_t fd_50F6_04E2;
    int16_t fd_50F6_04E4;
    int16_t fd_50F6_04F2;
    int16_t fd_50F6_04F4;
    int16_t fd_50F6_0502;
    int16_t fd_50F6_0504;
    int16_t fd_50F6_0506;
    int16_t fd_50F6_0508[2];
    int16_t fd_50F6_0510;
    int16_t fd_50F6_0516[64];
    int16_t fd_50F6_0596[2];
    int16_t fd_50F6_059E;
    int16_t fd_50F6_05A0[64];
    int16_t fd_50F6_0624;
    int16_t fd_50F6_0626[64];
    int16_t fd_50F6_06A6[2];
    int16_t fd_50F6_06AA;
    int16_t fd_50F6_06AC;
    int16_t fd_50F6_06AE[64];
    int16_t fd_50F6_072E[2];
    int32_t fd_50F6_0736;
    int16_t fd_50F6_073A;
    int16_t fd_50F6_073C[64];
    int16_t fd_50F6_07BC[2];
    int16_t fd_50F6_07C0;
    int16_t fd_50F6_07C2;
    int16_t fd_50F6_07C8;
    int16_t fd_50F6_07CA[2];
    int16_t fd_50F6_07CE[64];
    int16_t fd_50F6_084E;
    int16_t fd_50F6_0850;
    RecoveredPoint fd_50F6_0852;
    int16_t fd_50F6_0856[64];
    int16_t fd_50F6_08DA;
    int16_t fd_50F6_08DC;
    RecoveredXY fd_50F6_08DE;
    int16_t fd_50F6_08E2;
    int16_t fd_50F6_08E8;
    RecoveredPoint fd_50F6_08EC;
    int16_t fd_50F6_08F0[64];
    int16_t fd_50F6_0970[64];
    int16_t fd_50F6_09F0;
    RecoveredXY fd_50F6_09F2;
    int16_t fd_50F6_09FA;
    int16_t fd_50F6_09FC[2];
    int16_t fd_50F6_0A00;
    RecoveredPoint fd_50F6_0A02;
    int16_t fd_50F6_0A06;
    int16_t fd_50F6_0A0A[64];
    RecoveredXY fd_50F6_0A8A;
    int16_t fd_50F6_0A8E;
    int16_t fd_50F6_0A90;
    int16_t fd_50F6_0A9C;
    int16_t fd_50F6_0A9E;
    int16_t fd_50F6_0AA0;
    RecoveredPoint fd_50F6_0AA2;
    int16_t fd_50F6_0AA6;
    RecoveredXY fd_50F6_0AB2;
    int16_t fd_50F6_0AB6;
    int16_t fd_50F6_0AC4;
    int16_t fd_50F6_0AC6;
    int16_t fd_50F6_0AC8;
    int16_t fd_50F6_0ACA;
    int16_t fd_50F6_0AD6;
    int16_t fd_50F6_0AD8;
    int32_t fd_50F6_0ADA;
    int16_t fd_50F6_0AE8;
    int16_t fd_50F6_0AEA;
    int16_t fd_50F6_0AEC[6];
    int16_t fd_50F6_0AF8;
    int16_t fd_50F6_0AFA[6];
    int16_t fd_50F6_0B06;
    int16_t fd_50F6_0B08;
    int16_t fd_50F6_0B12[6];
    int16_t fd_50F6_0B1E;
    int16_t fd_50F6_0B20;
    int16_t * fd_50F6_0B22;
    uint32_t fd_50F6_0C26;
    int16_t fd_50F6_0C2A[6];
    int16_t fd_50F6_0C38;
    int16_t fd_50F6_0C3A;
    int16_t fd_50F6_0C3E;
    int16_t fd_50F6_0D40[20];
    int16_t fd_50F6_0D68;
    int16_t fd_50F6_0D6C;
    int16_t fd_50F6_0D70;
    int16_t fd_50F6_0D72[20];
    int16_t fd_50F6_0D9A;
    int16_t fd_50F6_0EAC;
    int16_t fd_50F6_0EB6[32];
    int16_t fd_50F6_0EF6;
    int16_t fd_50F6_0EF8;
    int16_t fd_50F6_0EFA;
    int32_t fd_50F6_0EFC;
    int16_t fd_50F6_0F06;
    int16_t fd_50F6_0F0C;
    int16_t fd_50F6_0F0E;
    int16_t fd_50F6_0F10;
    int16_t fd_50F6_0F12;
    int16_t fd_50F6_0F26;
    int16_t fd_50F6_0F2E;
    int32_t fd_50F6_0F30;
    int16_t fd_50F6_0F34;
    int16_t fd_50F6_0F36;
    int32_t fd_50F6_0F3E;
    int16_t fd_50F6_0F44;
    int16_t fd_50F6_0FB6;
    int16_t fd_50F6_0FBA;
    int32_t fd_50F6_0FBC;
    int32_t fd_50F6_0FC2;
    int16_t fd_50F6_0FFA;
    int16_t fd_50F6_0FFE;
    int32_t fd_50F6_1000;
    int16_t fd_50F6_1004;
    int16_t fd_50F6_1006;
    int16_t fd_50F6_1040;
    int16_t fd_50F6_1044;
    int16_t fd_50F6_104E;
    int16_t fd_50F6_1058;
    int16_t fd_50F6_105C;
    int16_t fd_50F6_105E;
    int16_t fd_50F6_1066;
    int32_t fd_50F6_1068;
    uint8_t fd_50F6_106C;
    int16_t fd_50F6_1074;
    int32_t fd_50F6_107E;
    int32_t fd_50F6_1082;
    int16_t fd_50F6_108C;
    int32_t fd_50F6_108E;
    int32_t fd_50F6_109C;
    int16_t fd_50F6_10A0;
    int32_t fd_50F6_10A2;
    int16_t fd_50F6_10A6;
    int16_t fd_50F6_10AC;
    int16_t fd_50F6_10B0;
    int16_t fd_50F6_10B2;
    int16_t fd_50F6_10B8;
    int16_t fd_50F6_10BA;
    int16_t fd_50F6_10BC;
    int16_t fd_50F6_10C0;
    struct Rect fd_50F6_10D2;
    int16_t fd_50F6_10DE;
    int16_t fd_50F6_10E0;
    struct Rect fd_50F6_110C;
    int32_t fd_50F6_383A;
    int16_t fd_50F6_3856;
    int16_t fd_50F6_3858;
    int16_t fd_55B3_19BE;
    int16_t fd_55B3_19C0;
    int16_t fd_55B3_29A2;
    int16_t fd_55B3_2A42[2];
    int16_t fd_55B3_2CBC;
    int16_t g_3DB2;
    int8_t g_5A97;
    int16_t * g_5AAC;
    uint16_t modeLevels[3];
} RecoveredState;

extern _Thread_local void * * AdviceStrs;
extern _Thread_local uint8_t AlistM[1001];
extern _Thread_local uint8_t AlistS[1001];
extern _Thread_local uint8_t AlistT[1001];
extern _Thread_local uint8_t AlistX[1001];
extern _Thread_local uint8_t AlistY[1001];
extern _Thread_local int16_t AntsEatenByLions;
extern _Thread_local int32_t BAntsEaten;
extern _Thread_local int16_t Barrier;
extern _Thread_local uint8_t BlistM[501];
extern _Thread_local uint8_t BlistS[501];
extern _Thread_local uint8_t BlistT[501];
extern _Thread_local uint8_t BlistX[501];
extern _Thread_local uint8_t BlistY[501];
extern _Thread_local int16_t BpopT;
extern _Thread_local int8_t CasteModeTabB[16];
extern _Thread_local int16_t CasteTabB[4];
extern _Thread_local int16_t ChaseSpid;
extern _Thread_local int16_t CurExpTool;
extern _Thread_local int16_t CurGndTileID;
extern _Thread_local int16_t Cycle;
extern _Thread_local int16_t DROPdir;
extern _Thread_local int16_t DeathCnt;
extern _Thread_local int8_t Dx8[8];
extern _Thread_local int8_t Dx9[10];
extern _Thread_local int8_t Dy8[8];
extern _Thread_local int8_t Dy9[10];
extern _Thread_local int16_t EatCnt;
extern _Thread_local uint8_t ExitMapB[64][64];
extern _Thread_local uint8_t ExitMapR[64][64];
extern _Thread_local int8_t ExpSubStates[8];
extern _Thread_local int16_t FoodB;
extern _Thread_local int16_t FoodR;
extern _Thread_local int16_t FuzLocX;
extern _Thread_local int16_t FuzLocY;
extern _Thread_local int16_t HealthB;
extern _Thread_local int16_t HealthR;
extern _Thread_local uint8_t HoleMapB[64];
extern _Thread_local uint8_t HoleMapR[64];
extern _Thread_local int16_t IdealCaste[7];
extern _Thread_local int16_t InitialLions;
extern _Thread_local uint8_t LifeA[128][64];
extern _Thread_local uint8_t LifeB[64][64];
extern _Thread_local uint8_t LifeR[64][64];
extern _Thread_local int16_t LionIndex;
extern _Thread_local uint8_t LionListM[10];
extern _Thread_local uint8_t LionListS[10];
extern _Thread_local uint8_t LionListT[10];
extern _Thread_local uint8_t LionListX[10];
extern _Thread_local uint8_t LionListY[10];
extern _Thread_local int16_t ListIndexA;
extern _Thread_local int16_t ListIndexB;
extern _Thread_local int16_t ListIndexR;
extern _Thread_local uint8_t MapA[128][64];
extern _Thread_local uint8_t MapB[64][64];
extern _Thread_local int16_t MapPlane;
extern _Thread_local uint8_t MapR[64][64];
extern _Thread_local int16_t MeHealth;
extern _Thread_local int16_t MeLocX;
extern _Thread_local int16_t MeLocY;
extern _Thread_local int16_t MePlane;
extern _Thread_local int16_t ModeAuto;
extern _Thread_local int16_t ModeMe;
extern _Thread_local int16_t ModeTabB[24];
extern _Thread_local int8_t ModeTabSB[6][8];
extern _Thread_local int8_t ModeTabWB[6][8];
extern _Thread_local uint8_t PherMapA[64][32];
extern _Thread_local uint8_t PherMapBN[64][32];
extern _Thread_local uint8_t PherMapBT[64][32];
extern _Thread_local uint8_t PherMapRN[64][32];
extern _Thread_local uint8_t PherMapRT[64][32];
extern _Thread_local int16_t PillDir;
extern _Thread_local int16_t PillarMap[6];
extern _Thread_local int16_t PillarSeg;
extern _Thread_local int16_t PillarState;
extern _Thread_local int16_t PillarX;
extern _Thread_local int16_t PillarY;
extern _Thread_local int32_t RAntsEaten;
extern _Thread_local uint8_t RT3[18][3];
extern _Thread_local uint8_t RT5[30][5];
extern _Thread_local int16_t RedLocX;
extern _Thread_local int16_t RedLocY;
extern _Thread_local int16_t RedPlane;
extern _Thread_local uint8_t RlistM[501];
extern _Thread_local uint8_t RlistS[501];
extern _Thread_local uint8_t RlistT[501];
extern _Thread_local uint8_t RlistX[501];
extern _Thread_local uint8_t RlistY[501];
extern _Thread_local int16_t RpopT;
extern _Thread_local int16_t SCorpseBase;
extern _Thread_local int16_t SMode;
extern _Thread_local int16_t Scycle;
extern _Thread_local int16_t Scycle2;
extern _Thread_local int16_t SowDir[3];
extern _Thread_local int16_t SowSave[3];
extern _Thread_local uint8_t SowTab[8];
extern _Thread_local int16_t SowX[3];
extern _Thread_local int16_t SowY[3];
extern _Thread_local int16_t SpidBurpCnt;
extern _Thread_local int16_t SpidRevenge;
extern _Thread_local int16_t Starg;
extern _Thread_local int16_t StargLife;
extern _Thread_local int16_t StrategicModeB;
extern _Thread_local int16_t SuserX;
extern _Thread_local int16_t SuserY;
extern _Thread_local int16_t TERRAINset;
extern _Thread_local int16_t TilesDugR;
extern _Thread_local int16_t Tindex;
extern _Thread_local int8_t TurnTab[9][8];
extern _Thread_local int16_t YardMode;
extern _Thread_local int8_t fd_3D57_006C[8];
extern _Thread_local int16_t fd_3D57_0074[16];
extern _Thread_local int8_t fd_3D57_0094[16];
extern _Thread_local uint8_t fd_3D57_00A4[12][16];
extern _Thread_local uint8_t fd_3D57_0164[12][16];
extern _Thread_local int16_t fd_3D57_02A4[2];
extern _Thread_local int16_t fd_3D57_02A8[2];
extern _Thread_local int16_t fd_3D57_02AC[2];
extern _Thread_local int16_t fd_3D57_02B0[2];
extern _Thread_local int16_t fd_3D57_02B4[2];
extern _Thread_local int16_t fd_3D57_02B8[2];
extern _Thread_local int16_t fd_3D57_02BC[2];
extern _Thread_local int16_t fd_3D57_02C0;
extern _Thread_local int16_t fd_3D57_02C2[38];
extern _Thread_local int16_t fd_3D57_0798[4];
extern _Thread_local int16_t fd_3D57_07A2;
extern _Thread_local int16_t fd_3D57_07A4;
extern _Thread_local int16_t fd_3D57_07A6;
extern _Thread_local int16_t fd_3D57_07A8[7];
extern _Thread_local int16_t fd_3D57_07BE;
extern _Thread_local int16_t fd_3D57_07C0[4];
extern _Thread_local int16_t fd_3D57_07C8[2];
extern _Thread_local int16_t fd_3D57_07CC[7];
extern _Thread_local int16_t fd_3D57_0828;
extern _Thread_local int16_t * fd_3D57_0852[40];
extern _Thread_local int8_t fd_3D57_0994[8];
extern _Thread_local int8_t fd_3D57_099C[8];
extern _Thread_local int8_t fd_3D57_09A4[8];
extern _Thread_local int8_t fd_3D57_09AC[8];
extern _Thread_local struct Pt fd_3D57_0B14[4];
extern _Thread_local RecoveredPointBytes18 fd_3D57_0B24[1];
extern _Thread_local int8_t fd_3D57_0B36[48];
extern _Thread_local int16_t fd_3D57_0C0E;
extern _Thread_local int16_t fd_3D57_0C12;
extern _Thread_local int16_t fd_3D57_0C14;
extern _Thread_local int16_t fd_3D57_0C16;
extern _Thread_local int16_t fd_3D57_0C18;
extern _Thread_local int16_t fd_3D57_0C1A[2];
extern _Thread_local int16_t fd_3D57_0C1C;
extern _Thread_local int16_t fd_3D57_0C1E;
extern _Thread_local int16_t fd_3D57_0C20;
extern _Thread_local int16_t fd_3D57_0C22;
extern _Thread_local int16_t fd_3D57_0C24;
extern _Thread_local int16_t fd_3D57_0C26;
extern _Thread_local int16_t fd_3D57_0C28;
extern _Thread_local int16_t fd_3D57_0C2A;
extern _Thread_local int16_t fd_3D57_0C2C;
extern _Thread_local int16_t fd_3D57_0C2E;
extern _Thread_local int16_t fd_3D57_0C30;
extern _Thread_local int16_t fd_3D57_0C32;
extern _Thread_local int16_t fd_3D57_0C34;
extern _Thread_local int8_t fd_3D57_0C36[4];
extern _Thread_local int8_t fd_3D57_0C3A[4];
extern _Thread_local int16_t fd_3D57_0C3E;
extern _Thread_local int16_t fd_3D57_0C40;
extern _Thread_local int16_t fd_3D57_0C42;
extern _Thread_local int16_t fd_3D57_0C44;
extern _Thread_local int16_t fd_3D57_0C46;
extern _Thread_local int16_t fd_3D57_0C48;
extern _Thread_local int16_t fd_3E1D_0000[16][12];
extern _Thread_local uint8_t fd_3E1D_C89F[64][32];
extern _Thread_local uint8_t fd_3E1D_D89F[64][32];
extern _Thread_local int16_t fd_50F6_0200;
extern _Thread_local int16_t fd_50F6_0202;
extern _Thread_local int32_t fd_50F6_0204;
extern _Thread_local int16_t fd_50F6_0208;
extern _Thread_local int16_t fd_50F6_020E;
extern _Thread_local int16_t fd_50F6_0210;
extern _Thread_local int16_t fd_50F6_0212;
extern _Thread_local int32_t fd_50F6_0214;
extern _Thread_local int32_t fd_50F6_0220;
extern _Thread_local int16_t fd_50F6_0224;
extern _Thread_local int16_t fd_50F6_0226;
extern _Thread_local int16_t fd_50F6_0228;
extern _Thread_local int16_t fd_50F6_022C;
extern _Thread_local int16_t fd_50F6_023E;
extern _Thread_local int16_t fd_50F6_0240;
extern _Thread_local int16_t fd_50F6_0242;
extern _Thread_local int16_t fd_50F6_0244;
extern _Thread_local int16_t fd_50F6_0246;
extern _Thread_local int16_t fd_50F6_0254;
extern _Thread_local uint8_t fd_50F6_0256[100];
extern _Thread_local int8_t * * fd_50F6_02BA;
extern _Thread_local int16_t fd_50F6_02BE;
extern _Thread_local uint8_t fd_50F6_02C0[100];
extern _Thread_local int16_t fd_50F6_032C;
extern _Thread_local int16_t fd_50F6_0332;
extern _Thread_local int16_t fd_50F6_0334[12];
extern _Thread_local void * * fd_50F6_034C;
extern _Thread_local int16_t fd_50F6_0352;
extern _Thread_local int16_t fd_50F6_0354;
extern _Thread_local int16_t fd_50F6_0356;
extern _Thread_local int16_t fd_50F6_035E;
extern _Thread_local int16_t fd_50F6_0364;
extern _Thread_local int16_t fd_50F6_0366;
extern _Thread_local int16_t fd_50F6_036C;
extern _Thread_local int16_t fd_50F6_036E;
extern _Thread_local int16_t fd_50F6_0376;
extern _Thread_local int16_t fd_50F6_037A;
extern _Thread_local uint8_t fd_50F6_037C[100];
extern _Thread_local int16_t fd_50F6_03E0;
extern _Thread_local int16_t fd_50F6_03E2;
extern _Thread_local int16_t fd_50F6_0400;
extern _Thread_local int16_t fd_50F6_0402;
extern _Thread_local uint8_t fd_50F6_0404[100];
extern _Thread_local int16_t fd_50F6_046A;
extern _Thread_local int16_t fd_50F6_0470;
extern _Thread_local int32_t fd_50F6_0472;
extern _Thread_local int16_t fd_50F6_0476;
extern _Thread_local int16_t fd_50F6_0478;
extern _Thread_local int16_t fd_50F6_047A;
extern _Thread_local int16_t fd_50F6_047E;
extern _Thread_local int16_t fd_50F6_0488;
extern _Thread_local int16_t fd_50F6_048E;
extern _Thread_local int16_t fd_50F6_0492;
extern _Thread_local int16_t fd_50F6_0496;
extern _Thread_local int16_t fd_50F6_049A;
extern _Thread_local int16_t fd_50F6_04A4;
extern _Thread_local int16_t fd_50F6_04BE;
extern _Thread_local int16_t fd_50F6_04C2;
extern _Thread_local int16_t fd_50F6_04C4;
extern _Thread_local int16_t fd_50F6_04C6;
extern _Thread_local int16_t fd_50F6_04E0;
extern _Thread_local int16_t fd_50F6_04E2;
extern _Thread_local int16_t fd_50F6_04E4;
extern _Thread_local int16_t fd_50F6_04F2;
extern _Thread_local int16_t fd_50F6_04F4;
extern _Thread_local int16_t fd_50F6_0502;
extern _Thread_local int16_t fd_50F6_0504;
extern _Thread_local int16_t fd_50F6_0506;
extern _Thread_local int16_t fd_50F6_0508[2];
extern _Thread_local int16_t fd_50F6_0510;
extern _Thread_local int16_t fd_50F6_0516[64];
extern _Thread_local int16_t fd_50F6_0596[2];
extern _Thread_local int16_t fd_50F6_059E;
extern _Thread_local int16_t fd_50F6_05A0[64];
extern _Thread_local int16_t fd_50F6_0624;
extern _Thread_local int16_t fd_50F6_0626[64];
extern _Thread_local int16_t fd_50F6_06A6[2];
extern _Thread_local int16_t fd_50F6_06AA;
extern _Thread_local int16_t fd_50F6_06AC;
extern _Thread_local int16_t fd_50F6_06AE[64];
extern _Thread_local int16_t fd_50F6_072E[2];
extern _Thread_local int32_t fd_50F6_0736;
extern _Thread_local int16_t fd_50F6_073A;
extern _Thread_local int16_t fd_50F6_073C[64];
extern _Thread_local int16_t fd_50F6_07BC[2];
extern _Thread_local int16_t fd_50F6_07C0;
extern _Thread_local int16_t fd_50F6_07C2;
extern _Thread_local int16_t fd_50F6_07C8;
extern _Thread_local int16_t fd_50F6_07CA[2];
extern _Thread_local int16_t fd_50F6_07CE[64];
extern _Thread_local int16_t fd_50F6_084E;
extern _Thread_local int16_t fd_50F6_0850;
extern _Thread_local RecoveredPoint fd_50F6_0852;
extern _Thread_local int16_t fd_50F6_0856[64];
extern _Thread_local int16_t fd_50F6_08DA;
extern _Thread_local int16_t fd_50F6_08DC;
extern _Thread_local RecoveredXY fd_50F6_08DE;
extern _Thread_local int16_t fd_50F6_08E2;
extern _Thread_local int16_t fd_50F6_08E8;
extern _Thread_local RecoveredPoint fd_50F6_08EC;
extern _Thread_local int16_t fd_50F6_08F0[64];
extern _Thread_local int16_t fd_50F6_0970[64];
extern _Thread_local int16_t fd_50F6_09F0;
extern _Thread_local RecoveredXY fd_50F6_09F2;
extern _Thread_local int16_t fd_50F6_09FA;
extern _Thread_local int16_t fd_50F6_09FC[2];
extern _Thread_local int16_t fd_50F6_0A00;
extern _Thread_local RecoveredPoint fd_50F6_0A02;
extern _Thread_local int16_t fd_50F6_0A06;
extern _Thread_local int16_t fd_50F6_0A0A[64];
extern _Thread_local RecoveredXY fd_50F6_0A8A;
extern _Thread_local int16_t fd_50F6_0A8E;
extern _Thread_local int16_t fd_50F6_0A90;
extern _Thread_local int16_t fd_50F6_0A9C;
extern _Thread_local int16_t fd_50F6_0A9E;
extern _Thread_local int16_t fd_50F6_0AA0;
extern _Thread_local RecoveredPoint fd_50F6_0AA2;
extern _Thread_local int16_t fd_50F6_0AA6;
extern _Thread_local RecoveredXY fd_50F6_0AB2;
extern _Thread_local int16_t fd_50F6_0AB6;
extern _Thread_local int16_t fd_50F6_0AC4;
extern _Thread_local int16_t fd_50F6_0AC6;
extern _Thread_local int16_t fd_50F6_0AC8;
extern _Thread_local int16_t fd_50F6_0ACA;
extern _Thread_local int16_t fd_50F6_0AD6;
extern _Thread_local int16_t fd_50F6_0AD8;
extern _Thread_local int32_t fd_50F6_0ADA;
extern _Thread_local int16_t fd_50F6_0AE8;
extern _Thread_local int16_t fd_50F6_0AEA;
extern _Thread_local int16_t fd_50F6_0AEC[6];
extern _Thread_local int16_t fd_50F6_0AF8;
extern _Thread_local int16_t fd_50F6_0AFA[6];
extern _Thread_local int16_t fd_50F6_0B06;
extern _Thread_local int16_t fd_50F6_0B08;
extern _Thread_local int16_t fd_50F6_0B12[6];
extern _Thread_local int16_t fd_50F6_0B1E;
extern _Thread_local int16_t fd_50F6_0B20;
extern _Thread_local int16_t * fd_50F6_0B22;
extern _Thread_local uint32_t fd_50F6_0C26;
extern _Thread_local int16_t fd_50F6_0C2A[6];
extern _Thread_local int16_t fd_50F6_0C38;
extern _Thread_local int16_t fd_50F6_0C3A;
extern _Thread_local int16_t fd_50F6_0C3E;
extern _Thread_local int16_t fd_50F6_0D40[20];
extern _Thread_local int16_t fd_50F6_0D68;
extern _Thread_local int16_t fd_50F6_0D6C;
extern _Thread_local int16_t fd_50F6_0D70;
extern _Thread_local int16_t fd_50F6_0D72[20];
extern _Thread_local int16_t fd_50F6_0D9A;
extern _Thread_local int16_t fd_50F6_0EAC;
extern _Thread_local int16_t fd_50F6_0EB6[32];
extern _Thread_local int16_t fd_50F6_0EF6;
extern _Thread_local int16_t fd_50F6_0EF8;
extern _Thread_local int16_t fd_50F6_0EFA;
extern _Thread_local int32_t fd_50F6_0EFC;
extern _Thread_local int16_t fd_50F6_0F06;
extern _Thread_local int16_t fd_50F6_0F0C;
extern _Thread_local int16_t fd_50F6_0F0E;
extern _Thread_local int16_t fd_50F6_0F10;
extern _Thread_local int16_t fd_50F6_0F12;
extern _Thread_local int16_t fd_50F6_0F26;
extern _Thread_local int16_t fd_50F6_0F2E;
extern _Thread_local int32_t fd_50F6_0F30;
extern _Thread_local int16_t fd_50F6_0F34;
extern _Thread_local int16_t fd_50F6_0F36;
extern _Thread_local int32_t fd_50F6_0F3E;
extern _Thread_local int16_t fd_50F6_0F44;
extern _Thread_local int16_t fd_50F6_0FB6;
extern _Thread_local int16_t fd_50F6_0FBA;
extern _Thread_local int32_t fd_50F6_0FBC;
extern _Thread_local int32_t fd_50F6_0FC2;
extern _Thread_local int16_t fd_50F6_0FFA;
extern _Thread_local int16_t fd_50F6_0FFE;
extern _Thread_local int32_t fd_50F6_1000;
extern _Thread_local int16_t fd_50F6_1004;
extern _Thread_local int16_t fd_50F6_1006;
extern _Thread_local int16_t fd_50F6_1040;
extern _Thread_local int16_t fd_50F6_1044;
extern _Thread_local int16_t fd_50F6_104E;
extern _Thread_local int16_t fd_50F6_1058;
extern _Thread_local int16_t fd_50F6_105C;
extern _Thread_local int16_t fd_50F6_105E;
extern _Thread_local int16_t fd_50F6_1066;
extern _Thread_local int32_t fd_50F6_1068;
extern _Thread_local uint8_t fd_50F6_106C;
extern _Thread_local int16_t fd_50F6_1074;
extern _Thread_local int32_t fd_50F6_107E;
extern _Thread_local int32_t fd_50F6_1082;
extern _Thread_local int16_t fd_50F6_108C;
extern _Thread_local int32_t fd_50F6_108E;
extern _Thread_local int32_t fd_50F6_109C;
extern _Thread_local int16_t fd_50F6_10A0;
extern _Thread_local int32_t fd_50F6_10A2;
extern _Thread_local int16_t fd_50F6_10A6;
extern _Thread_local int16_t fd_50F6_10AC;
extern _Thread_local int16_t fd_50F6_10B0;
extern _Thread_local int16_t fd_50F6_10B2;
extern _Thread_local int16_t fd_50F6_10B8;
extern _Thread_local int16_t fd_50F6_10BA;
extern _Thread_local int16_t fd_50F6_10BC;
extern _Thread_local int16_t fd_50F6_10C0;
extern _Thread_local struct Rect fd_50F6_10D2;
extern _Thread_local int16_t fd_50F6_10DE;
extern _Thread_local int16_t fd_50F6_10E0;
extern _Thread_local struct Rect fd_50F6_110C;
extern _Thread_local int32_t fd_50F6_383A;
extern _Thread_local int16_t fd_50F6_3856;
extern _Thread_local int16_t fd_50F6_3858;
extern _Thread_local int16_t fd_55B3_19BE;
extern _Thread_local int16_t fd_55B3_19C0;
extern _Thread_local int16_t fd_55B3_29A2;
extern _Thread_local int16_t fd_55B3_2A42[2];
extern _Thread_local int16_t fd_55B3_2CBC;
extern _Thread_local int16_t g_3DB2;
extern _Thread_local int8_t g_5A97;
extern _Thread_local int16_t * g_5AAC;
extern _Thread_local uint16_t modeLevels[3];
extern _Thread_local int16_t * fd_3D57_082A[20];

#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
#define RECOVERED_LOW_BYTE(p) (((uint8_t *)(p)) + sizeof(*(p)) - 1)
#elif defined(_WIN32) || !defined(__BYTE_ORDER__) || __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#define RECOVERED_LOW_BYTE(p) ((uint8_t *)(p))
#else
#error Unsupported host byte order for DOS low-byte overlays
#endif

typedef struct RecoveredBindingFrame {
    RecoveredState previous;
} RecoveredBindingFrame;

#define fd_3D57_0000 Dx8
#define fd_3D57_0008 Dy8
#define fd_3D57_0010 Dx9
#define fd_3D57_001A Dy9
#define fd_3D57_0024 TurnTab
#define fd_3D57_0224 HoleMapB
#define fd_3D57_0264 HoleMapR
#define fd_3D57_07B6 ExpSubStates
#define fd_3E1D_0180 MapA
#define fd_3E1D_2180 MapB
#define fd_3E1D_3180 MapR
#define fd_3E1D_4180 ExitMapB
#define fd_3E1D_5180 ExitMapR
#define fd_3E1D_6180 LifeA
#define fd_3E1D_8180 LifeB
#define fd_3E1D_9180 LifeR
#define fd_3E1D_A180 AlistX
#define fd_3E1D_A569 AlistY
#define fd_3E1D_A952 AlistM
#define fd_3E1D_AD3B AlistT
#define fd_3E1D_B124 AlistS
#define fd_3E1D_B50D BlistX
#define fd_3E1D_B702 BlistY
#define fd_3E1D_B8F7 BlistM
#define fd_3E1D_BAEC BlistT
#define fd_3E1D_BCE1 BlistS
#define fd_3E1D_BED6 RlistX
#define fd_3E1D_C0CB RlistY
#define fd_3E1D_C2C0 RlistM
#define fd_3E1D_C4B5 RlistT
#define fd_3E1D_C6AA RlistS
#define fd_3E1D_D09F PherMapA
#define fd_3E1D_E09F PherMapBN
#define fd_3E1D_E89F PherMapBT
#define fd_3E1D_F09F PherMapRN
#define fd_4DA7_0000 PherMapRT
#define fd_50F6_01FE HealthR
#define fd_50F6_0232 TilesDugR
#define fd_50F6_032E MapPlane
#define fd_50F6_0330 BpopT
#define fd_50F6_0350 RpopT
#define fd_50F6_035C YardMode
#define fd_50F6_0378 ModeAuto
#define fd_50F6_047C MeLocX
#define fd_50F6_0480 Barrier
#define fd_50F6_048A MeLocY
#define fd_50F6_048C MePlane
#define fd_50F6_049E modeLevels
#define fd_50F6_0D6A ListIndexA
#define fd_50F6_0DA8 ListIndexB
#define fd_50F6_0EAA ListIndexR
#define fd_50F6_0F08 (*RECOVERED_LOW_BYTE(&Cycle))
#define fd_50F6_0F18 Tindex
#define fd_50F6_0F24 TERRAINset
#define fd_50F6_0F3A DROPdir
#define fd_50F6_0F42 SuserX
#define fd_50F6_0F78 MeHealth
#define fd_50F6_0F7E SuserY
#define fd_50F6_0FB8 SMode
#define fd_50F6_0FFC Starg
#define fd_50F6_1042 Scycle
#define fd_50F6_104C CurExpTool
#define fd_50F6_1050 FoodB
#define fd_50F6_1054 EatCnt
#define fd_50F6_105A SCorpseBase
#define fd_50F6_1060 FoodR
#define fd_50F6_1072 Scycle2
#define fd_50F6_1076 SpidBurpCnt
#define fd_50F6_108A SpidRevenge
#define fd_50F6_109A DeathCnt
#define fd_50F6_10AE StargLife
#define fd_50F6_10BE HealthB
#define fd_3D57_07AA (fd_3D57_07A8[1])
#define fd_3D57_07AE (fd_3D57_07A8[3])
#define fd_3D57_07B0 (fd_3D57_07A8[4])
#define fd_3D57_07B2 (fd_3D57_07A8[5])
#define fd_3D57_07CE (fd_3D57_07CC + 1)

void recovered_bind_begin(RecoveredBindingFrame *frame, const RecoveredState *state);
void recovered_state_init(RecoveredState *state);
void recovered_bind_end(RecoveredBindingFrame *frame, RecoveredState *state);

void recovered_keyboard_set_modifiers(uint8_t dos_flags);
uint8_t recovered_keyboard_modifiers(void);

#endif
