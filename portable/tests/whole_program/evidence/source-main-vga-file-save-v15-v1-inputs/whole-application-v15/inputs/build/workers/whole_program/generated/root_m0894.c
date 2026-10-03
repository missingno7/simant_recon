#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
extern int16_t  fd_3D57_0C1A[];
/* Root module, code frame 0894: ant colony simulation (DoAntSim, A-list ants).
 * MSC 6.00A /AL /Os /Oe /Og.  The set/order of declarations (externs and locals, also of
 * earlier functions) decides commutative operand order under /Og (e.g. tile ^ attribute),
 * so declarations are kept exactly as verified. */

extern int16_t  SRand1(int16_t range);
extern int16_t  SRand2(void);
extern int16_t  SRand4(void);
extern int16_t  SRand8(void);
extern int16_t  SRand16(void);
extern int16_t  SRand32(void);
extern int16_t  SRand256(void);

extern int16_t  fd_3D57_07B2;
extern int16_t  fd_50F6_0F06;
extern int16_t  fd_50F6_0F2E;
extern int16_t  fd_50F6_0F10;
extern int16_t  fd_50F6_0EF6;
typedef struct {
    int16_t v;
    int16_t h;
} Point;

extern int16_t  fd_3D57_02C2;
extern int16_t  fd_3D57_0C18;
extern int16_t  fd_50F6_0EAC;
extern int16_t  ListIndexA;
extern int16_t  Tindex;
extern uint8_t  AlistT[];
extern uint8_t  AlistY[];
extern uint8_t  AlistX[];
extern uint8_t  AlistM[];
extern uint8_t  LifeA[128][64];
extern char  Dy8[8];
extern char  Dx8[8];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapBN[64][32];
extern uint8_t  MapA[128][64];
extern uint8_t  AlistS[];
extern int8_t  TurnTab[8][8];
extern uint8_t  PherMapA[64][32];
extern uint8_t  HoleMapB[];
extern uint8_t  HoleMapR[];
extern int16_t  fd_3D57_0C14;
extern int16_t  TERRAINset;
extern int16_t  fd_3D57_0074[16];
extern int8_t  fd_3D57_0094[];

extern void  o06_35F5_0173(void);
extern void  DoWater(void);
extern void  DoAntLions(void);
extern void  MoveSpider(void);
extern void  DoPillar(void);
extern void  GetStrategy(void);
extern void  o25_39C7_0000(void);
extern void  DoAntSimR(void);
extern void  DoAntSimY(void);
extern void  DoAntMoveY(void);
extern void  Feedback(void);
extern void  EndGameDialog(int16_t a);
extern void  CompactListA(void);
extern void  FullCount(void);
extern void  HistUpdate(void);
extern void  SmoothAlarm(void);
extern void  CompactListB(void);
extern void  FillHolesBN(void);
extern void  ColonySmellBN(void);
extern void  ColonySmellBT(void);
extern void  CompactListR(void);
extern void  FillHolesRN(void);
extern void  ColonySmellRN(void);
extern void  ColonySmellRT(void);
extern void  f_0DEF_0000(void);
extern void  AddFood(int16_t count, int16_t sound);
extern void  f_0DEF_006B(int16_t index);
extern int16_t  FindInAList(int16_t x, int16_t y);
extern void  RestBalloons(int16_t x, int16_t y, int16_t a);
extern void  InvalQueenStorageDisp(void);
extern int16_t  GetRandDir(int16_t x, int16_t y, int16_t dir);
extern void  PickupFoodA(int16_t x, int16_t y);
extern void  JamScentRN(int16_t x, int16_t y, int16_t level);
extern void  JamScentBN(int16_t x, int16_t y, int16_t level);
extern void  DecTSmell(int16_t x, int16_t y, int16_t colour);
extern int16_t  IsYellowAnt(int16_t value);
extern void  o25_3BA4_0DFB(int16_t a, int16_t index);
extern void  DoTroph(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetNewMode(int16_t caste, int16_t type);
extern int16_t  Bounce(int16_t x, int16_t y);
extern int16_t  GetNestDir(int16_t x, int16_t y, int16_t dir, int16_t attribute);
extern int16_t  GetAlarmDir(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetForageDir(int16_t x, int16_t y, int16_t dir, int16_t attribute);
extern int16_t  GetRedDefendDir(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetDefendDir(int16_t x, int16_t y, int16_t dir);
extern void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t state);
extern void  AddAntToRList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t state);
extern void  DigTileB(int16_t x, int16_t y);
extern void  DigTileR(int16_t x, int16_t y);
extern void  AlarmHere2(int16_t x, int16_t y, int16_t level);
extern int16_t  RRand(int16_t range);
extern void  FightBalloons(int16_t x, int16_t y, int16_t plane);
extern int16_t  IsValidA(int16_t x, int16_t y);

void  DoSmells(void);
void  ClrModePop(void);
void  TallyModePop(void);
void  FeedAnts(void);
void  DoAntSimA(void);
void  SimEggA(int16_t index);
void  SimQueenA(int16_t index);
int16_t  LostHeadA(int16_t x, int16_t y, int16_t life);
void  DoRestAnt(int16_t index);
void  DoRepoLoit(int16_t index);
void  DoRepoExit(int16_t index);
void  DoRepoFly(int16_t index);
void  DoDefendNest(int16_t index);
void  DoRandAntA(int16_t index);
void  DoRandAntAA(int16_t index);
void  DoDigOutAntA(int16_t index);
void  DoToNestAnt(int16_t index);
void  DoToAlarm(int16_t index);
void  DoReturnFoodAnt(int16_t index);
void  DoForageAnt(int16_t index);
void  DoRecruitAnt(int16_t index);
void  GoInNest(int16_t x, int16_t y, int16_t index);
void  DoFightA(int16_t index);
void  DeadAntHere(int16_t x, int16_t y, int16_t type);
void  DoAttackAnt(int16_t index);
int16_t  IsItHole(int16_t x, int16_t y);
int16_t  IsItFood(int16_t tile);
int16_t  RandTurn(int16_t dir);
void  StartFightA(int16_t index, int16_t x, int16_t y, int16_t nx, int16_t ny);
int16_t  GetWinner(int16_t a, int16_t b);

void  DoAntSim(void)
{
    if (++native_state_Cycle.signed_value > 0x1000)
        native_state_Cycle.signed_value = 0;
    native_state_fd_50F6_0C26.unsigned_value++;
    if (fd_3D57_07B2 == 1) {
        fd_50F6_0F06 = 0;
        fd_50F6_0F2E = 0;
        fd_50F6_0F10 = 0;
        fd_50F6_0EF6 = 0;
        (*((Point *)native_sim_state_fd_50F6_08EC.raw_bytes)).h = -1;
        (*((Point *)native_sim_state_fd_50F6_08EC.raw_bytes)).v = -1;
        (*((Point *)native_sim_state_fd_50F6_0AA2.raw_bytes)) = (*((Point *)native_sim_state_fd_50F6_08EC.raw_bytes));
        (*((Point *)native_sim_state_fd_50F6_0A02.raw_bytes)) = (*((Point *)native_sim_state_fd_50F6_08EC.raw_bytes));
        (*((Point *)native_sim_state_fd_50F6_0852.raw_bytes)) = (*((Point *)native_sim_state_fd_50F6_08EC.raw_bytes));
    }
    if ((native_state_Cycle.signed_value & 0x3f) == 0)
        FeedAnts();
    if ((native_state_Cycle.signed_value & 0x1f) == 0)
        DoSmells();
    o06_35F5_0173();
    DoWater();
    DoAntLions();
    MoveSpider();
    if (native_state_Cycle.signed_value & 1)
        DoPillar();
    GetStrategy();
    ClrModePop();
    DoAntSimA();
    o25_39C7_0000();
    DoAntSimR();
    DoAntSimY();
    TallyModePop();
    DoAntMoveY();
    Feedback();
    if (native_state_fd_50F6_0376.signed_value)
        EndGameDialog(0);
    fd_3D57_02C2 = 1;
}

void  DoSmells(void)
{
    switch ((native_state_Cycle.signed_value & 0x60) >> 5) {
    case 0:
        CompactListA();
        FullCount();
        HistUpdate();
        SmoothAlarm();
        break;
    case 1:
        CompactListB();
        FillHolesBN();
        ColonySmellBN();
        ColonySmellBT();
        break;
    case 2:
        FullCount();
        HistUpdate();
        SmoothAlarm();
        break;
    case 3:
        CompactListR();
        FillHolesRN();
        ColonySmellRN();
        ColonySmellRT();
        break;
    }
}

void  ClrModePop(void)
{
    int16_t i;

    for (i = 0; i < 20; i++) {
        fd_50F6_0D40[i] = 0;
        fd_50F6_0D72[i] = 0;
    }
    if (native_state_fd_50F6_08DC.signed_value)
        --native_state_fd_50F6_08DC.signed_value;
    if (native_state_fd_50F6_08E8.signed_value)
        --native_state_fd_50F6_08E8.signed_value;
}

void  TallyModePop(void)
{
    native_sim_state_fd_50F6_0B12.signed_values[0] = fd_50F6_0D40[2] + fd_50F6_0D40[3];
    native_sim_state_fd_50F6_0B12.signed_values[1] = fd_50F6_0D40[4] + fd_50F6_0D40[5];
    native_sim_state_fd_50F6_0B12.signed_values[2] = fd_50F6_0D40[1];
    native_sim_state_fd_50F6_0B12.signed_values[3] = fd_50F6_0D40[7];
    native_sim_state_fd_50F6_0B12.signed_values[4] = fd_50F6_0D40[12];
    native_sim_state_fd_50F6_0B12.signed_values[5] = fd_50F6_0D40[6];
    native_sim_state_fd_50F6_0C2A.signed_values[0] = fd_50F6_0D72[2] + fd_50F6_0D72[3];
    native_sim_state_fd_50F6_0C2A.signed_values[1] = fd_50F6_0D72[4] + fd_50F6_0D72[5];
    native_sim_state_fd_50F6_0C2A.signed_values[2] = fd_50F6_0D72[1];
    native_sim_state_fd_50F6_0C2A.signed_values[3] = fd_50F6_0D72[7];
    native_sim_state_fd_50F6_0C2A.signed_values[4] = fd_50F6_0D72[12];
    native_sim_state_fd_50F6_0C2A.signed_values[5] = fd_50F6_0D72[6];
    if (fd_50F6_0D72[19] < 1)
        f_0DEF_0000();
}

void  FeedAnts(void)
{
    if (fd_3D57_0C18 == 0) {
        if (--native_state_HealthB.signed_value < 0)
            native_state_HealthB.signed_value = 0;
    }
    if (--native_state_HealthR.signed_value < 0)
        native_state_HealthR.signed_value = 0;
    if (fd_50F6_0EAC == 3)
        return;
    if (native_state_fd_50F6_1040.signed_value >= (fd_3D57_0C1A[0]))
        return;
    AddFood(0x96, 1);
    (fd_3D57_0C1A[0]) = SRand1(0x32) + 1;
}

void  DoAntSimA(void)
{
    int16_t t;
    int16_t mode;

    Tindex = ListIndexA;
    while (Tindex > 0) {
        Tindex--;
        if (SRand256() == 0) {
            t = AlistT[Tindex];
            if (t) {
                if (t & 0x80)
                    t = native_state_HealthR.signed_value;
                else
                    t = native_state_HealthB.signed_value;
                if (SRand32() > t) {
                    DeadAntHere(AlistX[Tindex], AlistY[Tindex],
                                AlistT[Tindex] & 0x80);
                    AlistT[Tindex] = 0;
                    native_state_fd_50F6_0F30.signed_value++;
                }
            }
        }
        t = AlistT[Tindex];
        if (t == 0)
            continue;
        mode = AlistM[Tindex];
        if (t & 0x80)
            fd_50F6_0D72[mode]++;
        else
            fd_50F6_0D40[mode]++;
        switch (mode) {
        case 0:
            DoRandAntA(Tindex);
            break;
        case 1:
        case 4:
            DoToNestAnt(Tindex);
            break;
        case 2:
            DoForageAnt(Tindex);
            break;
        case 3:
            DoReturnFoodAnt(Tindex);
            break;
        case 5:
            DoDigOutAntA(Tindex);
            break;
        case 6:
            DoRecruitAnt(Tindex);
            break;
        case 7:
            DoAttackAnt(Tindex);
            break;
        case 8:
            SimEggA(Tindex);
            break;
        case 9:
            SimQueenA(Tindex);
            break;
        case 10:
            DoFightA(Tindex);
            break;
        case 11:
            DoToAlarm(Tindex);
            break;
        case 12:
            DoDefendNest(Tindex);
            break;
        case 13:
            DoRestAnt(Tindex);
            break;
        case 14:
            DoRepoLoit(Tindex);
            break;
        case 15:
            DoRepoExit(Tindex);
            break;
        case 16:
            DoRepoFly(Tindex);
            break;
        case 19:
            f_0DEF_006B(Tindex);
            break;
        }
    }
}

void  SimEggA(int16_t index)
{
    int16_t x;
    int16_t y;
    uint8_t type;

    x = AlistX[index];
    y = AlistY[index];
    type = AlistT[index];
    LifeA[x][y] = type;
    if (SRand1(200) == 0) {
        AlistT[index] = 0;
        LifeA[x][y] = 0;
    }
}

void  SimQueenA(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t type;

    x = AlistX[index];
    y = AlistY[index];
    type = AlistT[index];
    LifeA[x][y] = type;
    if ((type & 0x7f) > 0x67) {
        if (LostHeadA(x, y, type)) {
            LifeA[x][y] = 0;
            AlistT[index] = 0;
        }
    }
}

int16_t  LostHeadA(int16_t x, int16_t y, int16_t life)
{
    int16_t row;
    int16_t column;

    row = x + Dx8[life & 7];
    column = y + Dy8[life & 7];
    if (LifeA[row][column] - life == -8)
        return 0;
    if (FindInAList(row, column) >= 0)
        return 0;
    return 1;
}

void  DoRestAnt(int16_t index)
{
    int16_t x;
    int16_t y;

    x = AlistX[index];
    y = AlistY[index];
    if (IsItHole(x, y) == 1)
        GoInNest(x, y, index);
    else if (SRand4() == 0)
        AlistM[index] = 2;
    else if (fd_3D57_07B2 == 1)
        RestBalloons(x, y, 1);
}

void  DoRepoLoit(int16_t index)
{
    if (SRand2())
        DoRandAntAA(index);
    else
        DoToNestAnt(index);
    if (AlistT[index] & 0x80) {
        if (native_state_fd_50F6_08E8.signed_value > 100)
            AlistM[Tindex] = 0xf;
    } else {
        if (native_state_fd_50F6_08DC.signed_value > 100)
            AlistM[Tindex] = 0xf;
    }
}

void  DoRepoExit(int16_t index)
{
    int16_t scent;

    if (AlistT[index] & 0x80)
        scent = PherMapRN[AlistX[index] >> 1][AlistY[index] >> 1];
    else
        scent = PherMapBN[AlistX[index] >> 1][AlistY[index] >> 1];
    if (scent < 100)
        DoToNestAnt(index);
    else
        DoRandAntAA(index);
    if (AlistT[index] & 0x80) {
        if (native_state_fd_50F6_08E8.signed_value != 0 && (native_state_fd_50F6_08E8.signed_value == 1 || SRand1(native_state_fd_50F6_08E8.signed_value) == 0))
            AlistM[Tindex] = 0x10;
    } else {
        if (native_state_fd_50F6_08DC.signed_value != 0 && (native_state_fd_50F6_08DC.signed_value == 1 || SRand1(native_state_fd_50F6_08DC.signed_value) == 0))
            AlistM[Tindex] = 0x10;
    }
}

void  DoRepoFly(int16_t index)
{
    int16_t red;

    red = AlistT[index] & 0x80;
    if (SRand32() == 0) {
        if ((red == 0 && native_state_fd_50F6_06AA.signed_value < 50) || (red != 0 && native_state_fd_50F6_073A.signed_value < 50)) {
            AlistT[index] = 0;
            LifeA[AlistX[index]][AlistY[index]] = 0;
            if (fd_50F6_0EAC == 2) {
                if (red == 0)
                    native_state_fd_50F6_06AA.signed_value++;
                else
                    native_state_fd_50F6_073A.signed_value++;
                if (SRand16() == 0) {
                    if (red == 0) {
                        native_state_fd_50F6_07C8.signed_value++;
                        InvalQueenStorageDisp();
                    } else
                        native_state_fd_50F6_0850.signed_value++;
                }
            }
        }
    }
}

void  DoDefendNest(int16_t index)
{
    int16_t scent;

    if (AlistT[index] & 0x80)
        scent = PherMapRN[AlistX[index] >> 1][AlistY[index] >> 1];
    else
        scent = PherMapBN[AlistX[index] >> 1][AlistY[index] >> 1];
    if (scent < 0x6e)
        DoToNestAnt(index);
    else
        DoRandAntAA(index);
}


void  DoRandAntA(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t attribute;
    int16_t tile;
    int16_t flags;
    int16_t caste;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = GetRandDir(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        if (caste == 6 || caste == 2) {
            AlistT[index] = dir | flags | 8;
            LifeA[x][y] = AlistT[index];
            AlistM[index] = 3;
            PickupFoodA(nx, ny);
            AlistS[index] = 200;
            return;
        }
    } else if (tile > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                JamScentRN(nx, ny, AlistS[index]);
            else
                JamScentBN(nx, ny, AlistS[index]);
        }
        DecTSmell(nx, ny, attribute & 0x80);
        if (SRand8() == 0 && (caste == 6 || caste == 2))
            AlistM[index] = 2;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (native_state_fd_50F6_1044.signed_value == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            DoTroph(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        AlistM[index] = GetNewMode(caste, attribute);
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void  DoRandAntAA(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t tile;
    int16_t attribute;
    int16_t flags;
    int16_t dir;
    int16_t nx;
    int16_t ny;


    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    dir = GetRandDir(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((attribute ^ tile) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void  DoDigOutAntA(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t attribute;
    int16_t flags;
    int16_t digmode;
    int16_t dirindex;
    int16_t bdir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    flags = attribute & 0xf8;
    digmode = (attribute & 0x78) >> 3;
    dirindex = TurnTab[attribute & 7][SRand8()];
    bdir = Bounce(x, y);
    if (bdir != 0)
        dirindex = (bdir - 1) & 7;
    nx = x + Dx8[dirindex];
    ny = y + Dy8[dirindex];
    if (digmode != 5 && digmode != 9) {
        AlistM[index] = GetNewMode(digmode, attribute);
        AlistS[index] = 0;
        return;
    }
    if (SRand8() == 0) {
        AlistT[index] -= 0x18;
        AlistM[index] = GetNewMode(digmode, attribute);
        AlistS[index] = 0;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (LifeA[nx][ny] == 0) {
        AlistT[index] = LifeA[nx][ny] = dirindex | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
    } else {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (AlistS[index] != 0) {
        AlistS[index]--;
        if (attribute & 0x80)
            JamScentRN(nx, ny, AlistS[index]);
        else
            JamScentBN(nx, ny, AlistS[index]);
    }
}


void  DoToNestAnt(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t attribute;
    int16_t tile;
    int16_t flags;
    int16_t caste;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = GetNestDir(x, y, attribute & 7, attribute);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        if (caste == 6 || caste == 2) {
            AlistT[index] = dir | flags | 8;
            LifeA[x][y] = AlistT[index];
            AlistM[index] = 3;
            PickupFoodA(nx, ny);
            AlistS[index] = 200;
            return;
        }
    } else if (tile > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                JamScentRN(nx, ny, AlistS[index]);
            else
                JamScentBN(nx, ny, AlistS[index]);
        }
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (native_state_fd_50F6_1044.signed_value == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            DoTroph(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void  DoToAlarm(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t tile;
    int16_t attribute;
    int16_t flags;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (PherMapA[x >> 1][y >> 1] == 0 && SRand4() == 0) {
        LifeA[x][y] = AlistT[index];
        AlistM[index] = GetNewMode((attribute & 0x78) >> 3, attribute);
        return;
    }
    dir = GetAlarmDir(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


extern void  JamScentRT(int16_t x, int16_t y, int16_t level);
extern void  JamScentBT(int16_t x, int16_t y, int16_t level);

void  DoReturnFoodAnt(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t attribute;
    int16_t flags;
    int16_t ndir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    ndir = GetNestDir(x, y, attribute & 7, attribute);
    nx = x + Dx8[ndir];
    ny = y + Dy8[ndir];
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    AlistT[index] = LifeA[nx][ny] = ndir | flags;
    LifeA[x][y] = 0;
    AlistX[index] = nx;
    AlistY[index] = ny;
    if (AlistS[index] != 0) {
        AlistS[index]--;
        if (attribute & 0x80)
            JamScentRT(nx, ny, AlistS[index]);
        else
            JamScentBT(nx, ny, AlistS[index]);
    }
}

void  DoForageAnt(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t attribute;
    int16_t tile;
    int16_t flags;
    int16_t caste;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    if (SRand32() == 0) {
        AlistM[index] = 0xd;
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    if (PherMapA[x >> 1][y >> 1] != 0) {
        AlistM[index] = 0xb;
        return;
    }
    if (caste != 6 && caste != 2) {
        AlistM[index] = GetNewMode(caste, attribute);
        AlistS[index] = 0;
        return;
    }
    dir = GetForageDir(x, y, attribute & 7, attribute);
    if (dir < 0) {
        if (SRand8())
            AlistM[index] = 0;
        else
            AlistM[index] = GetNewMode(caste, attribute);
        AlistS[index] = 0;
        DecTSmell(x >> 1, y >> 1, attribute & 0x80);
        return;
    }
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        AlistT[index] = dir | flags | 8;
        LifeA[x][y] = AlistT[index];
        AlistM[index] = 3;
        PickupFoodA(nx, ny);
        AlistS[index] = 200;
        return;
    }
    if (tile > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        if (SRand16() == 0) {
            AlistM[index] = GetNewMode(caste, attribute);
            AlistS[index] = 0;
        }
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                JamScentRN(nx, ny, AlistS[index]);
            else
                JamScentBN(nx, ny, AlistS[index]);
        }
        DecTSmell(nx, ny, attribute & 0x80);
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (native_state_fd_50F6_1044.signed_value == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            DoTroph(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

void  DoRecruitAnt(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t tile;
    int16_t attribute;
    int16_t flags;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (PherMapA[x >> 1][y >> 1] != 0)
        dir = GetAlarmDir(x, y, attribute & 7);
    else if (attribute > 0x7f)
        dir = GetRedDefendDir(x, y, attribute & 7);
    else
        dir = GetDefendDir(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = SRand8() | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile)) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (native_state_fd_50F6_1044.signed_value) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            DoTroph(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

void  GoInNest(int16_t x, int16_t y, int16_t index)
{
    if (x < 0x40) {
        if (native_state_ListIndexB.signed_value >= 500)
            CompactListB();
        if (native_state_ListIndexB.signed_value >= 500)
            return;
        AddAntToBList(y, 1, (AlistT[index] & 0xf8) + 4, AlistM[index], AlistS[index]);
        if (HoleMapB[y] != 0)
            DigTileB(y, 1);
    } else {
        if (native_state_ListIndexR.signed_value >= 500)
            CompactListR();
        if (native_state_ListIndexR.signed_value >= 500)
            return;
        AddAntToRList(y, 1, (AlistT[index] & 0xf8) + 4, AlistM[index], AlistS[index]);
        if (HoleMapR[y] != 0)
            DigTileR(y, 1);
    }
    AlistT[index] = 0;
    LifeA[x][y] = 0;
}

void  StartFightA(int16_t ant, int16_t x, int16_t y, int16_t nx, int16_t ny)
{
    int16_t loser;
    int16_t type;
    int16_t winner;

    type = AlistT[ant];
    AlistT[ant] = 0;
    LifeA[x][y] = 0;
    loser = FindInAList(nx, ny);
    if (loser >= 0) {
        winner = GetWinner(AlistT[loser], type);
        AlistT[loser] = (winner & 0x80) + 0x70;
        LifeA[nx][ny] = (winner & 0x80) + 0x70;
        AlistM[loser] = 0xa;
        AlistS[loser] = winner;
        AlarmHere2(nx, ny, 0x28);
    }
}

static uint8_t  combatLevel[16] = {
    0, 0, 0, 0, 2, 0, 1, 1, 2, 1, 0, 0, 3, 3, 0, 0
};
static uint8_t  combatOdds[16] = {
    5, 2, 7, 3, 8, 5, 9, 4, 3, 1, 5, 2, 7, 6, 8, 5
};

int16_t  GetWinner(int16_t a, int16_t b)
{
    int16_t levelA;
    int16_t levelB;
    int16_t threshold;

    if (fd_3D57_0C14 == 1) {
        native_state_fd_50F6_0F3E.signed_value++;
        if (a & 0x80)
            return b;
        return a;
    }
    levelA = combatLevel[(a & 0x78) >> 3];
    levelB = combatLevel[(b & 0x78) >> 3];
    threshold = combatOdds[(levelA << 2) + levelB];
    if (RRand(10) < threshold) {
        if (a & 0x80) {
            native_state_fd_50F6_09FA.signed_value++;
            native_state_fd_50F6_0EFC.signed_value++;
        } else {
            native_state_fd_50F6_0A00.signed_value++;
            native_state_fd_50F6_0F3E.signed_value++;
        }
        return a;
    }
    if (b & 0x80) {
        native_state_fd_50F6_09FA.signed_value++;
        native_state_fd_50F6_0EFC.signed_value++;
    } else {
        native_state_fd_50F6_0A00.signed_value++;
        native_state_fd_50F6_0F3E.signed_value++;
    }
    return b;
}

void  DoFightA(int16_t index)
{
    int16_t x;
    int16_t y;

    x = AlistX[index];
    y = AlistY[index];
    AlistT[index] = (AlistT[index] & 0xf8) + SRand1(7);
    LifeA[x][y] = AlistT[index];
    if (SRand16() == 0) {
        LifeA[x][y] = AlistS[index];
        AlistT[index] = LifeA[x][y];
        AlistM[Tindex] = GetNewMode((AlistT[index] & 0x78) >> 3, AlistT[index]);
        AlistS[index] = 0;
        DeadAntHere(x, y, AlistT[index] & 0x80);
    } else if (fd_3D57_07B2 == 1)
        FightBalloons(x, y, 1);
}

void  DeadAntHere(int16_t x, int16_t y, int16_t type)
{
    int16_t oldX;
    int16_t oldY;
    int16_t otile;

    if (++native_state_fd_50F6_0476.signed_value >= 100)
        native_state_fd_50F6_0476.signed_value = 0;
    oldX = fd_50F6_037C[native_state_fd_50F6_0476.signed_value];
    oldY = fd_50F6_0404[native_state_fd_50F6_0476.signed_value];
    otile = MapA[oldX][oldY];
    if (TERRAINset == 0) {
        if (otile >= 0x10 && otile < 0x18)
            MapA[oldX][oldY] = SRand16();
        fd_50F6_037C[native_state_fd_50F6_0476.signed_value] = x;
        fd_50F6_0404[native_state_fd_50F6_0476.signed_value] = y;
        if (MapA[x][y] < 0x18) {
            if (type != 0)
                MapA[x][y] = SRand4() + 0x14;
            else
                MapA[x][y] = SRand4() + 0x10;
        }
    } else {
        if (otile >= 8 && otile < 0x18)
            MapA[oldX][oldY] = (otile - 8) >> 2;
        fd_50F6_037C[native_state_fd_50F6_0476.signed_value] = x;
        fd_50F6_0404[native_state_fd_50F6_0476.signed_value] = y;
        otile = MapA[x][y];
        if (otile < 4) {
            if (type != 0)
                MapA[x][y] = SRand1(2) + otile * 4 + 0xa;
            else
                MapA[x][y] = SRand1(2) + (otile + 2) * 4;
        }
    }
    LifeA[x][y] = 0;
}

int16_t  RandTurn(int16_t dir)
{
    return TurnTab[dir][SRand8()];
}

void  DoAttackAnt(int16_t index)
{
    int16_t x;
    int16_t y;
    int16_t tile;
    int16_t attribute;
    int16_t caste;
    int16_t flags;
    int16_t dir;
    int16_t nx;
    int16_t ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    caste = (attribute & 0x78) >> 3;
    if (fd_3D57_0074[caste] == 1)
        attribute = (fd_3D57_0094[caste] << 3) | (attribute & 0x87);
    flags = attribute & 0xf8;
    dir = GetNestDir(x, y, attribute & 7, attribute ^ 0x80);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > native_state_Barrier.signed_value) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((native_state_fd_50F6_04E2.signed_value ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

int16_t  IsItHole(int16_t x, int16_t y)
{
    int16_t tile;

    if (IsValidA(x, y) == 0)
        return 0;
    if (TERRAINset == 0) {
        if (MapA[x][y] == 0x50)
            return 1;
        return 0;
    }
    tile = MapA[x][y];
    if (tile < 0x80)
        return 0;
    if (tile > 0x8f)
        return 0;
    return 1;
}

int16_t  IsItFood(int16_t tile)
{
    if (TERRAINset == 0) {
        if (tile < 0x48 || tile > 0x4b)
            return 0;
        return 1;
    }
    if (tile < 0x18 || tile > 0x27)
        return 0;
    return 1;
}

#pragma pack(pop)
