#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 0BE8: ant counts, water, eggs, directions. */

extern int16_t  SRand1(int16_t range);
extern int16_t  SRand2(void);
extern int16_t  RRand(int16_t range);
extern void  Feedback(void);
extern void  DrownBList(int16_t y);
extern void  DrownRList(int16_t y);
extern void  ZapEuMapAt(int16_t plane, int16_t x, int16_t y);

extern void  myBeginSound(int16_t a, int16_t b, int16_t c);

extern void  myBeginSong(int16_t id, int16_t arg);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);

extern char  Dx8[8];
extern char  Dy8[8];
extern uint8_t  fd_3D57_0184[][16];
extern int16_t  fd_3D57_0C1E;
extern uint8_t  MapA[128][64];
extern uint8_t  MapB[64][64];
extern uint8_t  MapR[64][64];
extern uint8_t  ExitMapB[64][64];
extern uint8_t  ExitMapR[64][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern uint8_t  AlistT[];
extern uint8_t  BlistT[];
extern uint8_t  RlistT[];
extern uint8_t  PherMapA[64][32];
extern uint8_t  fd_3E1D_D89F[64][32];
extern uint8_t  PherMapBN[64][32];
extern uint8_t  PherMapBT[64][32];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapRT[64][32];
extern int32_t  fd_50F6_0214;
extern int16_t  fd_50F6_0354;
extern int16_t  fd_50F6_04C2;
extern int16_t  fd_50F6_0A06;
extern int16_t  ListIndexA;
extern int16_t  fd_50F6_0EAC;
extern int16_t  fd_50F6_0EB6[32];
extern int16_t  TERRAINset;
extern int16_t  DROPdir;
uint8_t g_1B9A[4] = { 0, 1, 0, 0xFF };
uint8_t g_1B9E[4] = { 0xFF, 0, 1, 0 };
extern int16_t  SRand16(void);
extern int16_t  SRand8(void);
extern int32_t  TickCount(void);
extern void  DigTileB(int16_t x, int16_t y);
extern void  DigTileR(int16_t x, int16_t y);
extern void  AddAntToBList(int16_t x, int16_t y, int16_t life, int16_t state, int16_t dir);
extern void  AddAntToRList(int16_t x, int16_t y, int16_t life, int16_t state, int16_t dir);

void  CountAnts(void);
void  PlaceDrop(int16_t i);
void  CountUpdate(void);
void  AddWater(int16_t y);
void  DropWater(int16_t y);
void  FoodFall(int16_t x, int16_t y);
int16_t  InNestBounds(int16_t x, int16_t y);

/* CountAnts: counts ants per caste (Win16 CountAnts, LOW confidence).  The far data
   externs above are declared in address order; with that declaration order the
   commutative sums below come out in the original operand order (SYM-1). */
void  CountAnts(void)
{
    int16_t i;
    int16_t n;
    int16_t v;

    native_sim_state_fd_50F6_0AFA.signed_values[0] = 0;
    native_sim_state_fd_50F6_0AEC.signed_values[0] = 0;
    for (i = 0; i < 32; i++)
        fd_50F6_0EB6[i] = 0;
    for (n = ListIndexA; n > 0; ) {
        v = AlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = native_state_ListIndexB.signed_value; n > 0; ) {
        v = BlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = native_state_ListIndexR.signed_value; n > 0; ) {
        v = RlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    if (fd_50F6_0A06 == 0) {
        if (native_state_fd_50F6_04E2.signed_value == 0)
            fd_50F6_0EB6[fd_50F6_04C2 >> 3]++;
        else
            fd_50F6_0EB6[(fd_50F6_04C2 | 0x80) >> 3]++;
    }
    native_sim_state_fd_50F6_0AEC.signed_values[0] = fd_50F6_0EB6[0];
    native_sim_state_fd_50F6_0AEC.signed_values[1] = fd_50F6_0EB6[1] + fd_50F6_0EB6[2] + fd_50F6_0EB6[3] + fd_50F6_0EB6[5];
    native_sim_state_fd_50F6_0AEC.signed_values[2] = fd_50F6_0EB6[6] + fd_50F6_0EB6[7] + fd_50F6_0EB6[9];
    native_sim_state_fd_50F6_0AEC.signed_values[3] = fd_50F6_0EB6[4];
    native_sim_state_fd_50F6_0AEC.signed_values[4] = fd_50F6_0EB6[8];
    if (native_sim_state_fd_50F6_0AEC.signed_values[5] && fd_50F6_0EB6[12] == 0 && fd_50F6_0354 == 0) {
        myBeginSong(0x2b0c, 0x7e);
        PictStrnDialog(0, 0x271a, 1);
        if (fd_50F6_0EAC <= 1) {
            PictStrnDialog(0, 0x271b, 1);
            native_state_fd_50F6_0376.signed_value = 1;
            native_state_fd_50F6_0366.signed_value = 0;
        }
    }
    native_sim_state_fd_50F6_0AEC.signed_values[5] = fd_50F6_0EB6[12];
    native_sim_state_fd_50F6_0AFA.signed_values[0] = fd_50F6_0EB6[16];
    native_sim_state_fd_50F6_0AFA.signed_values[1] = fd_50F6_0EB6[18] + fd_50F6_0EB6[19] + fd_50F6_0EB6[21] + fd_50F6_0EB6[17];
    native_sim_state_fd_50F6_0AFA.signed_values[2] = fd_50F6_0EB6[23] + fd_50F6_0EB6[22] + fd_50F6_0EB6[25];
    native_sim_state_fd_50F6_0AFA.signed_values[3] = fd_50F6_0EB6[20];
    native_sim_state_fd_50F6_0AFA.signed_values[4] = fd_50F6_0EB6[24];
    if (native_sim_state_fd_50F6_0AFA.signed_values[5] && fd_50F6_0EB6[28] == 0 && fd_50F6_0354 == 0) {
        myBeginSong(0x2b0d, 0x7e);
        PictStrnDialog(0, 0x271c, 1);
        if (fd_50F6_0EAC <= 1) {
            PictStrnDialog(0, 0x271d, 1);
            native_state_fd_50F6_0376.signed_value = 1;
            native_state_fd_50F6_0366.signed_value = 1;
        }
        if (fd_50F6_0EAC == 2 && native_state_fd_50F6_0400.signed_value == 1 && native_sim_state_fd_50F6_07CA.words[0] == 0xb && native_sim_state_fd_50F6_07CA.words[1] == 8)
            fd_3D57_0184[SRand1(6)][0] = 0x14;
    }
    native_state_BpopT.signed_value = native_sim_state_fd_50F6_0AEC.signed_values[3] + native_sim_state_fd_50F6_0AEC.signed_values[1] + native_sim_state_fd_50F6_0AEC.signed_values[2] + native_sim_state_fd_50F6_0AEC.signed_values[4] + native_sim_state_fd_50F6_0AEC.signed_values[5];
    native_sim_state_fd_50F6_0AFA.signed_values[5] = fd_50F6_0EB6[28];
    native_state_RpopT.signed_value = native_sim_state_fd_50F6_0AFA.signed_values[5] + native_sim_state_fd_50F6_0AFA.signed_values[4] + native_sim_state_fd_50F6_0AFA.signed_values[1] + native_sim_state_fd_50F6_0AFA.signed_values[3] + native_sim_state_fd_50F6_0AFA.signed_values[2];
    fd_50F6_0354 = 0;
}


void  FullCount(void)
{
    CountAnts();
    CountUpdate();
}

void  CountUpdate(void)
{
    Feedback();
}

void  DoWater(void)
{
    int16_t i;
    int16_t x;
    int16_t y;
    int16_t v;

    if (native_state_fd_50F6_0352.signed_value && !TERRAINset) {
        if (SRand1(50) == 0)
            myBeginSound(0x29, 0, 0x40);
        fd_3D57_0C1E = 1;
        if (SRand1(10) == 0 && native_state_fd_50F6_0242.signed_value > 4) {
            --native_state_fd_50F6_0242.signed_value;
            AddWater(native_state_fd_50F6_0242.signed_value);
        }
        for (i = 0; i < 100; i++) {
            x = native_sim_state_fd_50F6_0256.unsigned_values[i];
            y = native_sim_state_fd_50F6_02C0.unsigned_values[i];
            v = MapA[x][y];
            if (v >= 0x74 && v < 0x77)
                MapA[x][y]++;
            else {
                if (v == 0x77)
                    MapA[x][y] = SRand1(14);
                PlaceDrop(i);
            }
        }
    } else if (!TERRAINset) {
        if (fd_3D57_0C1E == 1) {
            fd_3D57_0C1E = 0;
            for (i = 0; i < 100; i++) {
                x = native_sim_state_fd_50F6_0256.unsigned_values[i];
                y = native_sim_state_fd_50F6_02C0.unsigned_values[i];
                v = MapA[x][y];
                if (v >= 0x74 && v <= 0x77)
                    MapA[x][y] = SRand1(14);
            }
        }
        if (native_state_fd_50F6_0242.signed_value < 0x40 && SRand1(10) == 0) {
            DropWater(native_state_fd_50F6_0242.signed_value);
            native_state_fd_50F6_0242.signed_value++;
        }
    }
}

void  PlaceDrop(int16_t i)
{
    int16_t x;
    int16_t y;

    x = RRand(128);
    y = RRand(64);
    native_sim_state_fd_50F6_0256.unsigned_values[i] = x;
    native_sim_state_fd_50F6_02C0.unsigned_values[i] = y;
    if (MapA[x][y] < 0xe) {
        MapA[x][y] = 0x74;
        x >>= 1;
        y >>= 1;
        fd_3E1D_D89F[x][y] = PherMapA[x][y] = 0;
        if (PherMapBN[x][y] >= 0x14)
            PherMapBN[x][y] -= 0x14;
        else
            PherMapBN[x][y] = 0;
        PherMapBT[x][y] = 0;
        if (PherMapRN[x][y] >= 0x14)
            PherMapRN[x][y] -= 0x14;
        else
            PherMapRN[x][y] = 0;
        PherMapRT[x][y] = 0;
    }
}

void  InitWater(void)
{
    int16_t i;

    for (i = 0; i < 100; ++i)
        PlaceDrop(i);
}

void  AddWater(int16_t y)
{
    int16_t x;
    int16_t v;
    int16_t t;

    DrownBList(y);
    DrownRList(y);
    for (x = 0; x < 64; x++) {
        v = MapB[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        MapB[x][y] = t;
        v = MapR[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        MapR[x][y] = t;
        ZapEuMapAt(2, x, y);
        ZapEuMapAt(3, x, y);
    }
}

void  DropWater(int16_t y)
{
    int16_t x;
    int16_t v;
    int16_t t;

    for (x = 0; x < 64; x++) {
        v = MapB[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        MapB[x][y] = t;
        v = MapR[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        MapR[x][y] = t;
        ZapEuMapAt(2, x, y);
        ZapEuMapAt(3, x, y);
    }
}

void  PickupFoodA(int16_t x, int16_t y)
{
    int16_t v;

    v = MapA[x][y];
    if (!TERRAINset) {
        if (v == 0x48)
            MapA[x][y] = SRand16();
        else
            MapA[x][y]--;
    } else {
        if (v % 4 == 0)
            MapA[x][y] = (v - 0x18) >> 2;
        else
            MapA[x][y]--;
    }
    if (native_state_fd_50F6_1040.signed_value > 0)
        native_state_fd_50F6_1040.signed_value--;
}

int16_t  DropFoodA(int16_t x, int16_t y)
{
    int16_t v;

    v = MapA[x][y];
    if (TERRAINset == 1) {
        if (v < 4) {
            MapA[x][y] = (v + 6) << 2;
            native_state_fd_50F6_1040.signed_value++;
            return 1;
        }
        if (v >= 8 && v < 0x18) {
            v = (v - 8) >> 2;
            MapA[x][y] = (v + 6) << 2;
            native_state_fd_50F6_1040.signed_value++;
            return 1;
        }
        if (v >= 0x18 && v < 0x27) {
            MapA[x][y]++;
            native_state_fd_50F6_1040.signed_value++;
            return 1;
        }
        if (v < 0x40) {
            FoodFall(x, y);
            return 1;
        }
    } else {
        if (v < 0x4b) {
            if (v >= 0x48) {
                MapA[x][y]++;
                native_state_fd_50F6_1040.signed_value++;
                return 1;
            }
            MapA[x][y] = 0x48;
            native_state_fd_50F6_1040.signed_value++;
            return 1;
        }
    }
    return 0;
}

void  FoodFall(int16_t a, int16_t b)
{
    int16_t v;
    int16_t go;
    int16_t x;
    int16_t y;

    go = 1;
    x = a;
    y = b;
    while (go) {
        v = MapA[x][y];
        if (v < 4) {
            MapA[x][y] = (v + 6) << 2;
            native_state_fd_50F6_1040.signed_value++;
            go = 0;
        }
        x += g_1B9A[DROPdir];
        y += g_1B9E[DROPdir];
        if (x < 0 || x > 0x7f)
            go = 0;
        if (y < 0 || y > 0x3f)
            go = 0;
    }
}

void  PickupFoodB(int16_t x, int16_t y)
{
    int16_t v;
    int16_t flag;

    flag = 0;
    v = MapB[x][y];
    if (v == 0x10) {
        MapB[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        MapB[x][y]--;
        flag = 1;
    }
    if (flag == 1 && native_state_FoodB.signed_value > 0)
        native_state_FoodB.signed_value--;
}

void  PickupFoodR(int16_t x, int16_t y)
{
    int16_t v;
    int16_t flag;

    flag = 0;
    v = MapR[x][y];
    if (v == 0x10) {
        MapR[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        MapR[x][y]--;
        flag = 1;
    }
    if (flag == 1 && native_state_FoodR.signed_value > 0)
        native_state_FoodR.signed_value--;
}


void  PlaceEggB(int16_t x, int16_t y, int16_t life)
{
    if (native_state_ListIndexB.signed_value < 500 && InNestBounds(x, y)) {
        DigTileB(x, y);
        AddAntToBList(x, y, life, 8, 0);
        LifeB[x][y] = life;
    }
}

void  PlaceEggR(int16_t x, int16_t y, int16_t life)
{
    if (native_state_ListIndexR.signed_value < 500 && InNestBounds(x, y)) {
        DigTileR(x, y);
        AddAntToRList(x, y, life, 8, 0);
        LifeR[x][y] = life;
    }
}

int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    int16_t dx;
    int16_t dy;

    dy = y2 - y1;
    dx = x2 - x1;
    if (dx == 0) {
        if (dy == 0)
            return 0;
        if (dy < 0)
            return 1;
        return 5;
    }
    if (dx > 0) {
        if (dy < 0)
            return 2;
        if (dy == 0)
            return 3;
        return 4;
    }
    if (dy > 0)
        return 6;
    if (dy == 0)
        return 7;
    return 8;
}

int32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    return (int32_t)(y2 - y1) * (y2 - y1) + (int32_t)(x2 - x1) * (x2 - x1);
}

int16_t  InNestBounds(int16_t x, int16_t y)
{
    if (x >= 0 && x <= 0x3f && y >= 1 && y <= 0x3f)
        return 1;
    return 0;
}

int16_t  IsItDirt(int16_t value)
{
    if (value >= 0x20 && value <= 0x2e)
        return 1;
    return 0;
}

int16_t  GetExitDirB(int16_t x, int16_t y, int16_t dir)
{
    int16_t back;
    int16_t best;
    int16_t bestValue;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t value;

    if (y == 1) {
        if (MapB[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapB[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

int16_t  GetExitDirR(int16_t x, int16_t y, int16_t dir)
{
    int16_t back;
    int16_t best;
    int16_t bestValue;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t value;

    if (y == 1) {
        if (MapR[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapR[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

int16_t  GetEnterDirB(int16_t x, int16_t y, int16_t dir)
{
    int16_t back;
    int16_t best;
    int16_t bestValue;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t value;

    back = dir ^ 4;
    best = -1;
    bestValue = ExitMapB[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapB[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue > value) {
            bestValue = value;
            best = i;
        } else if (SRand2()) {
            bestValue = value;
            best = i;
        }
    }
    return best;
}

int16_t  GetEnterDirR(int16_t x, int16_t y, int16_t dir)
{
    int16_t back;
    int16_t best;
    int16_t bestValue;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t value;

    back = dir ^ 4;
    best = -1;
    bestValue = ExitMapR[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapR[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue > value) {
            bestValue = value;
            best = i;
        } else if (SRand2()) {
            bestValue = value;
            best = i;
        }
    }
    return best;
}


void  TryAntTheme(void)
{
    if (TickCount() >= fd_50F6_0214 + 0x1c20) {
        fd_50F6_0214 = TickCount();
        if (++native_state_fd_50F6_0228.signed_value > 2)
            native_state_fd_50F6_0228.signed_value = 0;
        myBeginSong(native_state_fd_50F6_0228.signed_value + 0x2713, 0x7e);
    }
}



#pragma pack(pop)
