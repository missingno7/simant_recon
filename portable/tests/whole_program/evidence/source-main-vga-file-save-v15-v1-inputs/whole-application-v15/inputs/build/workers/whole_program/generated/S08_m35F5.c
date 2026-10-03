#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
extern int16_t  fd_3D57_07CC[];
/* Overlay section S08, code frame 35F5: world generation (RandWorld unit). */


extern uint8_t  MapA[128][64];
extern uint8_t  MapB[64][64];
extern uint8_t  MapR[64][64];
extern uint8_t  ExitMapB[64][64];
extern uint8_t  ExitMapR[64][64];
extern uint8_t  LifeA[128][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern uint8_t  PherMapA[64][32];
extern uint8_t  fd_3E1D_D89F[64][32];
extern uint8_t  PherMapBN[64][32];
extern uint8_t  PherMapBT[64][32];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapRT[64][32];
extern uint8_t  HoleMapB[64];
extern uint8_t  HoleMapR[64];
extern int16_t  TERRAINset;
extern int16_t  fd_50F6_0EAC;
extern int16_t  fd_3D57_02B4[2];
extern int16_t  fd_3D57_02B8[2];
extern uint32_t  fd_50F6_0472;
extern int16_t  fd_50F6_0FFA;
extern int16_t  fd_50F6_0FB6;

extern void  SetSRandSeed(uint32_t seed);
extern void  InitSpider(void);
extern void  MakeMap(int16_t width, int16_t kind);
extern int16_t  SRand1(int16_t range);
extern int16_t  SRand2(void);
extern int16_t  SRand4(void);
extern int16_t  SRand8(void);
extern int16_t  SRand16(void);
extern int16_t  SRand64(void);
extern int16_t  SGRand(int16_t range);
extern void  MakeNewHoleB(int16_t x);
extern void  MakeNewHoleR(int16_t x);
extern void  BuildAntListA(void);
extern void  ClearListB(void);
extern void  ClearListR(void);
extern void  ClearHistory(int16_t a);
extern void  CountAnts(void);
extern void  InvalEuMap(int16_t a, int16_t b, int16_t columns, int16_t rows);

extern uint32_t  fd_50F6_0214;
extern uint32_t  fd_50F6_0204;
extern int16_t  fd_3D57_0C44;
extern int16_t  fd_3D57_0C18;
extern int16_t  fd_3D57_0C16;
extern int16_t  fd_3D57_0C14;
extern int16_t  fd_3D57_07C8;
extern int16_t  fd_3E1D_0000[16][12];
extern int16_t  fd_3D57_0C24;
extern int16_t  MePlane;
extern int16_t  MeLocX;
extern int16_t  MeLocY;

extern void  o06_35F5_0000(void);
extern void  initControls(void);
extern int16_t  RRand(int16_t range);
extern uint8_t  fd_3D57_00A4[12][16];
extern uint8_t  fd_3D57_0164[12][16];
void  AddBlackAnts(int16_t count);
void  AddRedAnts(int16_t count);
extern void  FullCount(void);
extern void  SetMapPlane(int16_t plane);

static char tutorialX[30] = {
    0, 1, 2, 5, 7, 2, 2, 7, 8, 6, 3, 7, 7, 10, 11,
    6, 8, 10, 11, 9, 10, 11, 9, 10, 11, 9, 10, 10, 10, 11
};
static char tutorialY[30] = {
    0, 0, 0, 0, 0, 1, 2, 2, 2, 3, 4, 4, 5, 5, 5,
    6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 10, 11, 11
};
static char tutorialBlack[30] = {
    2, 4, 6, 5, 7, 4, 2, 2, 3, 6, 1, 7, 4, 5, 3,
    1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0
};
static char tutorialRed[30] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 4, 6, 3, 4, 6, 5, 6, 3, 0, 4, 3, 2, 5
};
extern char  Dx8[];
extern char  Dy8[];
extern int16_t  DigTileThemB(int16_t x, int16_t y);
extern void  DigTileB(int16_t x, int16_t y);
extern int16_t  DigTileThemR(int16_t x, int16_t y);
extern int16_t  fd_3D57_0C22;
extern int16_t  fd_3D57_07BE;
extern int16_t  fd_50F6_0A06;
extern int16_t  fd_50F6_04C2;
extern void  SetMyHealth(int16_t health);
extern int16_t  *  fd_50F6_0B22;
extern int16_t  fd_3D57_02BC[2];
extern int16_t  ListIndexA;
extern uint8_t  AlistT[1000];
extern uint8_t  AlistM[1000];
extern uint8_t  AlistS[1000];
extern uint8_t  BlistT[500];
extern uint8_t  BlistM[500];
extern uint8_t  BlistS[500];
extern uint8_t  RlistT[500];
extern uint8_t  RlistM[500];
extern uint8_t  RlistS[500];
extern void  AddAntToAList(int16_t x, int16_t y, int16_t type, int16_t kind, int16_t a);
extern int16_t  SRand128(void);
extern int16_t  SRand256(void);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t a, int16_t b);
extern void  AddAntToRList(int16_t x, int16_t y, int16_t type, int16_t a, int16_t b);
extern void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t code);
extern void  ResetYellowVars(int16_t plane, int16_t x, int16_t y);
extern void  DigTileR(int16_t x, int16_t y);

void  DigOutBNest(int16_t count);
void  ClrArrays(void);
void  DigOutRNest(int16_t count);
void  InitYelloAnt(void);
void  PlaceBlackQueen(void);
void  MakeBlkQueen(int16_t x, int16_t y, int16_t dir);
void  MakeRedQueen(int16_t x, int16_t y, int16_t dir);
void  PlaceRedQueen(void);
void  AddFood(int16_t count, int16_t sound);

void  InitSimVars(void)
{
    (fd_3D57_07CC[0]) = 1;
    native_state_fd_50F6_0FBA.signed_value = 30;
    native_state_fd_50F6_0FFE.signed_value = 30;
    native_state_CurExpTool.signed_value = 0;
    native_state_fd_50F6_073A.signed_value = 0;
    native_state_fd_50F6_06AA.signed_value = 0;
    native_state_fd_50F6_0850.signed_value = 0;
    native_state_fd_50F6_07C8.signed_value = 0;
}

/* STEERED (ZERO-1): seed is unsigned, so seed < 0 is always false.
 * This folded initializer reproduces the original AX-to-DI zeroing; the
 * eliminated original expression is unknown. All array boundary indexes
 * are literal zero. The unused y declaration is retained from the draft. */
void  RandWorld(uint16_t seed, int16_t blackSize, int16_t redSize, int16_t mapWidth, int16_t mapKind)
{
    int16_t count, roll, tries, lim1, lim2, x, n;
    int16_t y;

    SetSRandSeed(seed);
    InitSpider();
    MakeMap(mapWidth, mapKind);

    blackSize += blackSize >> 2;
    redSize += redSize >> 2;

    for (count = (seed < 0); count < 64; count++) {
        for (x = 0; x < 64; x++) {
            MapB[count][x] = 0x2e;
            MapR[count][x] = 0x2e;
            ExitMapB[count][x] = 0;
            ExitMapR[count][x] = 0;
            LifeB[count][x] = 0;
            LifeR[count][x] = 0;
            LifeA[count][x] = 0;
            LifeA[count + 64][x] = 0;
        }
    }

    for (count = 0; count < 64; count++) {
        if (TERRAINset == 0) {
            MapB[count][0] = SRand4() + 0x1c;
            MapR[count][0] = SRand4() + 0x1c;
        } else {
            if (mapKind > 3)
                MapB[count][0] = SRand1(2) + 0x1c;
            else
                MapB[count][0] = 0x1e;
            if (mapKind > 3)
                MapR[count][0] = SRand1(2) + 0x1c;
            else
                MapR[count][0] = 0x1e;
        }
        ExitMapB[count][0] = 0xff;
        ExitMapR[count][0] = 0xff;
    }

    for (count = 0; count < 64; count++) {
        for (x = 0; x < 32; x++) {
            fd_3E1D_D89F[count][x] = 0;
            PherMapA[count][x] = 0;
            PherMapBN[count][x] = 0;
            PherMapBT[count][x] = 0;
            PherMapRN[count][x] = 0;
            PherMapRT[count][x] = 0;
        }
    }

    tries = 0;
    lim1 = SRand1(6) + 7;
    lim2 = 15 - SRand2();
    n = blackSize;
    while (n > 0) {
        n--;
        count = SGRand(0x80);
        x = SRand64();
        if (MapA[count][x] < 0x50) {
            if (LifeA[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    LifeA[count][x] = SRand8() + 0x10;
                else if (roll < lim2)
                    LifeA[count][x] = SRand8() + 0x30;
                else if (SRand2())
                    LifeA[count][x] = SRand8() + 0x20;
                else
                    LifeA[count][x] = SRand8() + 0x40;
            }
        }
    }

    tries = 0;
    lim1 = SRand1(6) + 7;
    lim2 = 15 - SRand2();
    n = redSize;
    while (n > 0) {
        n--;
        count = 0x7f - SGRand(0x80);
        x = SRand64();
        if (MapA[count][x] < 0x50) {
            if (LifeA[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    LifeA[count][x] = SRand8() - 0x70;
                else if (roll < lim2)
                    LifeA[count][x] = SRand8() - 0x50;
                else if (SRand2())
                    LifeA[count][x] = SRand8() - 0x60;
                else
                    LifeA[count][x] = SRand8() - 0x40;
            }
        }
    }

    for (x = 0; x < 64; x++) {
        HoleMapB[x] = 0;
        HoleMapR[x] = 0;
    }

    if (fd_50F6_0EAC != 2 || blackSize >= 1)
        MakeNewHoleB(0x20);
    if (redSize >= 1)
        MakeNewHoleR(0x20);

    native_state_fd_50F6_10A2.signed_value = 0;
    native_state_fd_50F6_108E.signed_value = 0;
    native_state_fd_50F6_1082.signed_value = 0;
    native_state_fd_50F6_1068.signed_value = 0;
    native_state_fd_50F6_0224.signed_value = 0;
    native_state_TilesDugR.signed_value = 0;
    native_state_fd_50F6_020E.signed_value = 0;
    native_state_fd_50F6_0200.signed_value = 0;
    native_state_fd_50F6_10C0.signed_value = 0;
    native_state_fd_50F6_10B2.signed_value = 0;
    native_state_fd_50F6_0242.signed_value = 0x40;

    if (blackSize > 1)
        DigOutBNest(blackSize << 4);
    if (redSize > 1)
        DigOutRNest(redSize << 4);

    BuildAntListA();
    ClearListB();
    ClearListR();

    native_state_fd_50F6_035E.signed_value = 0;
    native_state_fd_50F6_036C.signed_value = 0;
    fd_3D57_02B4[0] = -1;
    fd_3D57_02B4[1] = -1;
    fd_3D57_02B8[0] = -1;
    fd_3D57_02B8[1] = -1;

    if (redSize > 0)
        PlaceRedQueen();
    if (blackSize > 0)
        PlaceBlackQueen();
    InitYelloAnt();

    native_state_FoodB.signed_value = 0;
    native_state_FoodR.signed_value = 0;
    native_state_fd_50F6_1040.signed_value = 0;
    if (fd_50F6_0EAC != 3)
        AddFood(-1, 0);

    native_state_HealthB.signed_value = 100;
    native_state_HealthR.signed_value = 100;

    fd_50F6_0472 = 0;
    native_state_fd_50F6_09FA.signed_value = 0;
    native_state_fd_50F6_0A00.signed_value = 0;
    native_state_Cycle.signed_value = 0;

    ClearHistory(0);
    CountAnts();
    InvalEuMap(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);

    native_sim_state_fd_50F6_0508.words[0] = 0x40;
    native_sim_state_fd_50F6_0596.words[0] = 0x40;
    native_sim_state_fd_50F6_0508.words[1] = 0x20;
    native_sim_state_fd_50F6_0596.words[1] = 0x20;
    native_sim_state_fd_50F6_06A6.words[0] = 0x20;
    native_sim_state_fd_50F6_072E.words[0] = 0x20;
    native_sim_state_fd_50F6_06A6.words[1] = 1;
    native_sim_state_fd_50F6_072E.words[1] = 1;
}

void  RandYard(void)
{
    int16_t i;

    ClrArrays();
    ClearHistory(1);
    initControls();

    *native_sim_state_fd_50F6_07CA.words = 11;
    *native_sim_state_fd_50F6_07BC.words = 11;
    *(native_sim_state_fd_50F6_07CA.words + 1) = 8;
    *(native_sim_state_fd_50F6_07BC.words + 1) = 8;

    o06_35F5_0000();

    native_state_fd_50F6_105E.signed_value = -1;
    fd_50F6_0214 = 0;
    fd_50F6_0204 = 0;
    native_state_fd_50F6_0228.signed_value = 0;
    native_state_fd_50F6_0478.signed_value = 0;
    native_state_fd_50F6_0504.signed_value = 0;
    native_state_fd_50F6_0366.signed_value = 0;
    native_state_fd_50F6_0376.signed_value = 0;
    fd_3D57_0C44 = 0;
    fd_3D57_0C18 = 0;
    fd_3D57_0C16 = 0;
    fd_3D57_0C14 = 0;
    native_state_fd_50F6_0C26.unsigned_value = 0L;

    if (fd_50F6_0EAC <= 1)
        native_state_MapPlane.signed_value = 2;
    else
        native_state_MapPlane.signed_value = 1;
    fd_3D57_07C8 = native_state_MapPlane.signed_value;
    native_state_YardMode.signed_value = 0;

    for (i = 0; i < 192; i++)
        fd_3E1D_0000[0][i] = (RRand(0x7fff) - 0xc000) & 0x7fff;

    if (fd_50F6_0EAC == 2)
        RandWorld(fd_3E1D_0000[*(native_sim_state_fd_50F6_07CA.words + 1)][*native_sim_state_fd_50F6_07CA.words], fd_3D57_0C24 = 0, 1, *native_sim_state_fd_50F6_07BC.words, *(native_sim_state_fd_50F6_07BC.words + 1));
    else
        RandWorld(fd_3E1D_0000[*(native_sim_state_fd_50F6_07CA.words + 1)][*native_sim_state_fd_50F6_07CA.words], fd_3D57_0C24 = 1, 1, *native_sim_state_fd_50F6_07BC.words, *(native_sim_state_fd_50F6_07BC.words + 1));

    if (MePlane <= 1) {
        native_sim_state_fd_50F6_0596.words[0] = MeLocX;
        native_sim_state_fd_50F6_0596.words[1] = MeLocY;
    } else if (MePlane == 2) {
        native_sim_state_fd_50F6_06A6.words[0] = MeLocX;
        native_sim_state_fd_50F6_06A6.words[1] = MeLocY;
    } else {
        native_sim_state_fd_50F6_072E.words[0] = MeLocX;
        native_sim_state_fd_50F6_072E.words[1] = MeLocY;
    }
}

void  GenerateTutorial(void)
{
    int16_t i;

    fd_50F6_0EAC = 1;
    RandYard();
    AddBlackAnts(32);
    AddRedAnts(32);
    FullCount();
    fd_50F6_0EAC = 2;
    SetMapPlane(MePlane);
    for (i = 0; i < 30; i++) {
        fd_3D57_00A4[tutorialX[i]][tutorialY[i]] = tutorialBlack[i] << 5;
        fd_3D57_0164[tutorialX[i]][tutorialY[i]] = tutorialRed[i] << 5;
    }
}

void  DigOutBNest(int16_t count)
{
    int16_t dir, y, x, newX, newY;

    dir = 4;
    y = 1;
    x = 0x20;
    DigTileB(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + Dx8[dir];
        newY = y + Dy8[dir];
        if (newX < 1) {
            newX = 1;
            dir = 2;
        } else if (newX > 0x3e) {
            newX = 0x3e;
            dir = 6;
        }
        if (newY < 2) {
            newY = 1;
            dir = 4;
        } else if (newY > 0x3e) {
            newY = 0x3e;
            dir = 0;
        }
        if (DigTileThemB(newX, newY) == 1) {
            x = newX;
            y = newY;
            if (y == 1 && HoleMapB[x] == 0)
                MakeNewHoleB(newX);
        }
    }
}

void  DigOutRNest(int16_t count)
{
    int16_t dir, y, x, newX, newY;

    dir = 4;
    y = 1;
    x = 0x20;
    DigTileR(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + Dx8[dir];
        newY = y + Dy8[dir];
        if (newX < 1) {
            newX = 1;
            dir = 2;
        } else if (newX > 0x3e) {
            newX = 0x3e;
            dir = 6;
        }
        if (newY < 2) {
            newY = 1;
            dir = 4;
        } else if (newY > 0x3e) {
            newY = 0x3e;
            dir = 0;
        }
        if (DigTileThemR(newX, newY) == 1) {
            x = newX;
            y = newY;
            if (y == 1 && HoleMapR[x] == 0)
                MakeNewHoleR(newX);
        }
    }
}

void  InitYelloAnt(void)
{
    native_state_fd_50F6_049A.signed_value = 0;
    fd_3D57_0C22 = 0xfd;
    if (native_state_fd_50F6_104E.signed_value != 0) {
        native_state_fd_50F6_104E.signed_value = 0;
        fd_3D57_07BE = -1;
    }
    SetMyHealth(100);

    if (fd_50F6_0EAC != 3) {
        native_state_fd_50F6_04E2.signed_value = 0;
        fd_50F6_0A06 = 0;
        if (fd_50F6_0EAC != 2 || fd_3D57_0C24 != 0) {
            SetMyLife(2, native_state_fd_50F6_0F0E.signed_value, native_state_fd_50F6_0F26.signed_value, 0x10, 2, 0xff);
        } else {
            int16_t x, y;

            x = 0x40;
            y = 0x20;
            {
                int16_t col, count, tries;

                for (tries = 0; tries < 100; tries++) {
                    count = SRand16() - SRand16() + 0x20;
                    col = SRand8() - SRand8() + 0x20;
                    if (MapA[count][col] < 0x10) {
                        x = count;
                        y = col;
                        break;
                    }
                }
            }
            SetMyLife(1, x, y, 0x40, 2, 0xff);
        }
        goto done;
    }
    MePlane = 1;
    native_state_fd_50F6_04E2.signed_value = 0;
    fd_50F6_0A06 = 2;
    MeLocX = 0x40;
    MeLocY = 0x20;
    fd_50F6_04C2 = 0x10;

done:
    ResetYellowVars(MePlane, MeLocX, MeLocY);
}

void  PlaceBlackQueen(void)
{
    int16_t x, y, count, wobble;

    count = SRand4() + 7;
    wobble = 0;
    x = 0x20;
    for (y = 1; y < count; y++) {
        DigTileB(x, y);
        if (SRand2() == 0)
            wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        DigTileB(x, y);
        x++;
        y++;
    }
    DigTileB(x, y);
    fd_3D57_02B4[0] = x;
    fd_3D57_02B4[1] = y;
    native_state_fd_50F6_0F0E.signed_value = x;
    native_state_fd_50F6_0F26.signed_value = y;
    MakeBlkQueen(x + 2, y, 2);
}

void  MakeBlkQueen(int16_t x, int16_t y, int16_t dir)
{
    int16_t d;

    d = dir ^ 4;
    DigTileB(x, y);
    DigTileB(x + Dx8[d], y + Dy8[d]);
    DigTileB(x + 2 * Dx8[d], y + 2 * Dy8[d]);
    AddAntToBList(x, y, dir + 0x60, 9, 0);
    AddAntToBList(x + Dx8[d], y + Dy8[d], dir + 0x68, 9, 0);
    native_state_fd_50F6_035E.signed_value++;
}

void  PlaceRedQueen(void)
{
    int16_t x, y, count, wobble;

    count = SRand4() + 7;
    x = 0x20;
    for (y = 1; y < count; y++) {
        DigTileR(x, y);
        wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        DigTileR(x, y);
        x++;
        y++;
    }
    DigTileR(x, y);
    fd_3D57_02B8[0] = x;
    fd_3D57_02B8[1] = y;
    MakeRedQueen(x + 2, y, 2);
}

void  MakeRedQueen(int16_t x, int16_t y, int16_t dir)
{
    int16_t d;

    d = dir ^ 4;
    DigTileR(x, y);
    DigTileR(x + Dx8[d], y + Dy8[d]);
    DigTileR(x + 2 * Dx8[d], y + 2 * Dy8[d]);
    AddAntToRList(x, y, dir + 0xE0, 9, 0);
    AddAntToRList(x + Dx8[d], y + Dy8[d], dir + 0xE8, 9, 0);
    native_state_fd_50F6_036C.signed_value++;
}

int16_t  fracSIN(int16_t angle)
{
    int16_t index;
    int16_t value;

    index = angle & 0x7f;
    if (index > 0x3f)
        index = 0x80 - index;

    if (index == 0x40)
        value = 0x7fff;
    else {
        index &= 0x3f;
        value = fd_50F6_0B22[index];
    }
    if ((angle & 0xff) > 0x7f)
        value = -value;

    return value;
}

int16_t  fracCOS(int16_t angle)
{
    return fracSIN(angle + 0x40);
}

void  AddFood(int16_t count, int16_t sound)
{
    int16_t x, y, angle, r, i, radius, cx, cy;

    if (sound == 1)
        myBeginSound(0x20, 0, 0x7e);
    if (count < 0) {
        cx = 0x40;
        cy = SRand1(0x30) + 8;
        count = 200;
    } else {
        cx = SRand128();
        cy = SRand64();
    }
    fd_3D57_02BC[0] = cx;
    fd_3D57_02BC[1] = cy;
    radius = SRand8() + 5;
    for (i = 0; i < count; i++) {
        angle = SRand256();
        r = SRand1(radius);
        x = (int32_t)r * fracCOS(angle) / 0x7fffL + cx;
        y = (int32_t)r * fracSIN(angle) / 0x7fffL + cy;
        if (x >= 0 && x <= 0x7f && y >= 0 && y <= 0x3f && LifeA[x][y] == 0) {
            angle = MapA[x][y];
            if (TERRAINset != 0) {
                if (angle < 0x18) {
                    if (angle < 4)
                        MapA[x][y] = (angle + 6) << 2;
                    else
                        MapA[x][y] = ((angle - 8) & 0xfc) + 0x18;
                    native_state_fd_50F6_1040.signed_value++;
                } else if (angle < 0x28 && angle % 4 < 3) {
                    MapA[x][y]++;
                    native_state_fd_50F6_1040.signed_value++;
                }
            } else {
                if (angle < 0x18) {
                    MapA[x][y] = 0x48;
                    native_state_fd_50F6_1040.signed_value++;
                } else if (angle >= 0x48 && angle < 0x4b) {
                    MapA[x][y]++;
                    native_state_fd_50F6_1040.signed_value++;
                }
            }
        }
    }
}

void  AddBlackAnts(int16_t count)
{
    int16_t x;
    int16_t y;
    int16_t base;
    int16_t kind;
    int16_t type;

    for (x = 0; x < 64; x++) {
        for (y = 16; y < 48; y++) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0) {
                switch (SRand1(10)) {
                case 0:
                case 1:
                case 2:
                case 3:
                    base = 0x30;
                    kind = 2;
                    break;
                default:
                    base = 0x10;
                    kind = 4;
                    break;
                }
                type = SRand8() + base;
                LifeA[x][y] = type;
                AddAntToAList(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (ListIndexA >= 1000)
                    return;
            }
        }
    }
}

void  AddRedAnts(int16_t count)
{
    int16_t x;
    int16_t y;
    int16_t base;
    int16_t kind;
    int16_t type;

    for (x = 127; x >= 64; x--) {
        for (y = 16; y < 48; y++) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0) {
                switch (SRand1(10)) {
                case 0:
                case 1:
                case 2:
                case 3:
                    base = 0x30;
                    kind = 2;
                    break;
                default:
                    base = 0x10;
                    kind = 4;
                    break;
                }
                type = SRand8() + base + 0x80;
                LifeA[x][y] = type;
                AddAntToAList(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (ListIndexA >= 1000)
                    return;
            }
        }
    }
}

int16_t  GrabMap(int16_t x, int16_t y)
{
    int16_t col, row;

    if (x > 0x7f)
        col = 0;
    else if (x < 0)
        col = 0x7f;
    else
        col = x;
    if (y > 0x3f)
        row = 0;
    else if (y < 0)
        row = 0x3f;
    else
        row = y;
    return MapA[col][row];
}

/* The zero is held in a local: its constant-propagated definition before the first
 * loop keeps that loop's entry test (sub di,di / jmp <outer test>), which a literal 0
 * lets MSC rotate away (worker resB). */
void  ClrArrays(void)
{
    int16_t x, y, v;

    v = 0;
    for (x = 0; x < 128; x++) {
        for (y = 0; y < 64; y++) {
            MapA[x][y] = v;
            LifeA[x][y] = v;
        }
    }
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 64; y++) {
            MapB[x][y] = v;
            MapR[x][y] = v;
            ExitMapB[x][y] = v;
            ExitMapR[x][y] = v;
            LifeB[x][y] = v;
            LifeR[x][y] = v;
        }
    }
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            fd_3E1D_D89F[x][y] = v;
            PherMapA[x][y] = v;
            PherMapBN[x][y] = v;
            PherMapBT[x][y] = v;
            PherMapRN[x][y] = v;
            PherMapRT[x][y] = v;
        }
    }
    for (y = 0; y < 1000; y++) {
        AlistT[y] = v;
        AlistM[y] = v;
        AlistS[y] = v;
    }
    for (y = 0; y < 500; y++) {
        BlistT[y] = v;
        BlistM[y] = v;
        BlistS[y] = v;
        RlistT[y] = v;
        RlistM[y] = v;
        RlistS[y] = v;
    }
    for (x = 0; x < 12; x++) {
        for (y = 0; y < 16; y++) {
            fd_3D57_00A4[x][y] = v;
            fd_3D57_0164[x][y] = v;
        }
    }
}

#pragma pack(pop)
