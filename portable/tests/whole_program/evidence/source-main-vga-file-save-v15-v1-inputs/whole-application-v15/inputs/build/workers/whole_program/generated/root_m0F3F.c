#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 0F3F: red colony nest ants (DoAntSimR, R-list ants).
 * MSC 6.00AX /AL /Os /Oe /Og /Zi. */

extern int16_t  Tindex;
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];
extern uint8_t  RlistT[];
extern uint8_t  RlistM[];
extern int16_t  SRand256(void);
extern int16_t  SRand32(void);
extern uint8_t  LifeR[64][64];
extern int16_t  FindInRList(int16_t x, int16_t y, int16_t ant);
extern int16_t  GetWinner(int16_t a, int16_t b);
extern uint8_t  RlistS[];
extern int16_t  MePlane;
extern uint8_t  MapR[64][64];
extern int16_t  SRand1(int16_t range);
extern int16_t  GetEnterDirR(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetExitDirR(int16_t x, int16_t y, int16_t dir);
extern int16_t  SRand8(void);
extern int16_t  GetNewMode(int16_t caste, int16_t type);
extern int16_t  fd_3D57_07B2;
extern void  RestBalloons(int16_t x, int16_t y, int16_t plane);
extern int16_t  GetNewModeR(int16_t mode);
extern int16_t  SRand16(void);
extern void  FightBalloons(int16_t x, int16_t y, int16_t plane);
extern int16_t  IsYellowAnt(int16_t value);
extern void  o25_3BA4_0DFB(int16_t a, int16_t index);
extern int8_t  fd_3D57_0B36[];
extern void  EggBalloons(int16_t x, int16_t y, int16_t plane);
extern int16_t  SRand64(void);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
extern void  QueenBalloons(int16_t x, int16_t y, int16_t plane);
extern int8_t  Dx8[8];
extern int8_t  Dy8[8];
extern int16_t  InNestBounds(int16_t x, int16_t y);
extern int16_t  fd_3D57_02B8[2];
extern int16_t  SRand128(void);
extern void  PlaceEggR(int16_t x, int16_t y, int16_t life);
extern int16_t  o25_39C7_0CBD(int16_t kind, int16_t x, int16_t y, int16_t tx, int16_t ty);
extern void  AddAntToRList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t state);
extern int16_t  SRand4(void);
extern int16_t  IsItDirt(int16_t value);
extern int16_t  DigTileThemR(int16_t x, int16_t y);
extern void  myBeginSound(int16_t a, int16_t b, int16_t c);
extern void  f_14EE_0D71(int16_t x, int16_t y);
extern void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t state);
extern uint8_t  LifeB[64][64];
extern int16_t  RandTurn(int16_t dir);
extern uint8_t  ExitMapR[64][64];
extern uint8_t  HoleMapR[];
extern void  MakeNewHoleR(int16_t x);
extern int16_t  ExitHole(int16_t hole, int16_t x, int16_t type, int16_t mode, int16_t state);
extern int16_t  SRand2(void);



void  DoNestAntR(int16_t x, int16_t y, int16_t attr);
void  RaidInR(int16_t x, int16_t y, int16_t dirHint);
void  StayInR(int16_t x, int16_t y, int16_t dirHint);
void  RaidOutR(int16_t x, int16_t y, int16_t attr);
void  DoRestR(int16_t x, int16_t y, int16_t attacker);
void  DoDrownR(int16_t x, int16_t y, int16_t attr);
void  DoRandR(int16_t x, int16_t y, int16_t attr, int16_t modeArg);
void  DoNestFightR(int16_t x, int16_t y);
int16_t  CheckNestFightR(int16_t x, int16_t y, int16_t attacker);
void  SimEggR(int16_t x, int16_t y);
void  SimQueenR(int16_t x, int16_t y, int16_t caste, int16_t attr);
void  MakeNewTailR(int16_t index);
void  KillTailR(int16_t index);
int16_t  TryMoveDirR(int16_t x, int16_t y, int16_t dir);
void  DoNestingR(int16_t x, int16_t y, int16_t attr, int16_t caste);
void  StealFoodR(int16_t x, int16_t y);
int16_t  QueenMoveR(int16_t x, int16_t y, int16_t dirHint);
int16_t  LostHeadR(int16_t x, int16_t y, int16_t attr);
int16_t  LostTailR(int16_t x, int16_t y, int16_t attr);
void  TryEatFoodR(int16_t y, int16_t x);
void  EatFoodR(int16_t x, int16_t y);
void  DecEatR(void);
int16_t  DropFoodR(int16_t x, int16_t y);
int16_t  GetOutR(int16_t x);
void  DoFoodInR(int16_t x, int16_t y, int16_t attr);
void  DoDigInR(int16_t x, int16_t y, int16_t attr, int16_t caste);
void  DoDigOutR(int16_t x, int16_t y, int16_t attr);

void  DoAntSimR(void)
{
    int16_t x;
    int16_t y;
    int16_t attr;

    Tindex = native_state_ListIndexR.signed_value;
    while (Tindex > 0) {
        --Tindex;
        x = RlistX[Tindex];
        y = RlistY[Tindex];
        attr = RlistT[Tindex];
        if (attr != 0)
            DoNestAntR(x, y, attr);
    }
}

/* Locals follow the accepted black twin S25 o25_39C7_006D (caste reused for the cell value, t for
   the mode and the fight winner).  The grouping of the DoDigOutR case labels is only partly
   decided by the bytes: 5/6/7 and 11/12 merged with 15 and 16 separate is one of several forms
   that give `mov bx,si` for the mode index; the fully merged 15/16 form gives `mov bx,ax`
   (worker resG, work/resG/v8.py: 108 of 406 groupings are exact). */
void  DoNestAntR(int16_t x, int16_t y, int16_t attr)
{
    int16_t caste;
    int16_t task;
    int16_t i;
    int16_t t;

    caste = (attr & 0x78) >> 3;
    if (attr & 0x80) {
        t = RlistM[Tindex];
        fd_50F6_0D72[t]++;
        if (SRand256() == 0 && t != 9 && SRand32() > native_state_HealthR.signed_value) {
            RlistT[Tindex] = 0;
            LifeR[x][y] = 0;
            native_state_fd_50F6_0FBC.signed_value++;
            return;
        }
        switch (t) {
        case 0:
            DoRandR(x, y, attr, caste);
            break;
        case 1:
            DoNestingR(x, y, attr, caste);
            break;
        case 2:
            DoDigOutR(x, y, attr);
            break;
        case 3:
            DoFoodInR(x, y, attr);
            break;
        case 4:
            DoDigInR(x, y, attr, caste);
            break;
        case 5:
        case 6:
        case 7:
            DoDigOutR(x, y, attr);
            break;
        case 8:
            SimEggR(x, y);
            break;
        case 9:
            SimQueenR(x, y, caste, attr);
            break;
        case 10:
            DoNestFightR(x, y);
            break;
        case 11:
        case 12:
            DoDigOutR(x, y, attr);
            break;
        case 13:
            DoRestR(x, y, attr);
            break;
        case 14:
            DoRandR(x, y, attr, caste);
            if (native_state_fd_50F6_08E8.signed_value > 100)
                RlistM[Tindex] = 0xf;
            break;
        case 15:
            DoDigOutR(x, y, attr);
            break;
        case 16:
            DoDigOutR(x, y, attr);
            break;
        case 17:
            DoDrownR(x, y, attr);
            break;
        default:
            DoRandR(x, y, attr, caste);
            break;
        }
    } else {
        task = RlistM[Tindex];
        fd_50F6_0D40[task]++;
        if (attr < 8) {
            RlistT[Tindex] = 0;
            LifeR[RlistX[Tindex]][RlistY[Tindex]] = 0;
            return;
        }
        if (attr > 0x6f) {
            DoNestFightR(x, y);
            return;
        }
        caste = LifeR[x][y];
        if (caste > 0x80 && caste < 0xe8 && (i = FindInRList(x, y, caste)) >= 0) {
            if (caste > 0xdf)
                KillTailR(i);
            if (caste < 0x88) {
                RlistM[Tindex] = 3;
                RlistT[Tindex] |= 8;
                LifeR[x][y] = RlistT[Tindex];
                RlistT[i] = 0;
            } else {
                t = GetWinner(RlistT[i], attr);
                RlistT[Tindex] = 0;
                RlistS[i] = t;
                LifeR[x][y] = RlistT[i] = (t & 0x80) + 0x70;
                RlistM[i] = 0xa;
            }
            return;
        }
        switch (task) {
        case 6:
            if (MePlane == 3)
                StayInR(x, y, attr);
            else
                RaidOutR(x, y, attr);
            break;
        case 7:
            RaidInR(x, y, attr);
            break;
        default:
            RaidOutR(x, y, attr);
            break;
        }
    }
}

void  RaidInR(int16_t x, int16_t y, int16_t dirHint)
{
    int16_t dir;

    if (MapR[x][y] >= 0x10 && MapR[x][y] <= 0x13) {
        StealFoodR(x, y);
        RlistM[Tindex] = 3;
        RlistT[Tindex] |= 8;
        LifeR[x][y] = RlistT[Tindex];
        return;
    }
    if (TryMoveDirR(x, y, (SRand1(3) + dirHint - 2) & 7))
        return;
    dir = GetEnterDirR(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (TryMoveDirR(x, y, dir))
        return;
    RlistM[Tindex] = 1;
    LifeR[x][y] = RlistT[Tindex];
}

void  StayInR(int16_t x, int16_t y, int16_t dirHint)
{
    int16_t dir;

    if (MapR[x][y] >= 0x10 && MapR[x][y] <= 0x13) {
        StealFoodR(x, y);
        RlistM[Tindex] = 3;
        RlistT[Tindex] |= 8;
        LifeR[x][y] = RlistT[Tindex];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    RlistT[Tindex] = (RlistT[Tindex] & 0xf8) | dir;
    if (TryMoveDirR(x, y, dir))
        return;
    dir = GetEnterDirR(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (TryMoveDirR(x, y, dir))
        return;
    LifeR[x][y] = RlistT[Tindex];
}

void  RaidOutR(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;

    dir = GetExitDirR(x, y, 8);
    if (dir == 0)
        dir = SRand8();
    else
        dir--;
    if (TryMoveDirR(x, y, dir) == 0) {
        if (TryMoveDirR(x, y, SRand8()) == 0)
            LifeR[x][y] = RlistT[Tindex];
    }
}

void  DoRestR(int16_t x, int16_t y, int16_t attacker)
{
    int16_t type;

    if (CheckNestFightR(x, y, attacker))
        return;
    LifeR[x][y] = RlistT[Tindex];
    if (SRand1(20) == 0) {
        type = RlistT[Tindex];
        RlistM[Tindex] = GetNewMode((type & 0x78) >> 3, type);
        return;
    }
    if (fd_3D57_07B2 != 0)
        RestBalloons(x, y, 3);
}

void  DoDrownR(int16_t x, int16_t y, int16_t attr)
{
    if (MapR[x][y] < 0x14) {
        RlistM[Tindex] = GetNewModeR((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    RlistT[Tindex] = attr;
    LifeR[x][y] = attr;
    if (SRand1(100) == 0) {
        RlistT[Tindex] = LifeR[x][y] = 0;
        if (attr & 0x80)
            native_state_fd_50F6_0FBC.signed_value++;
        else
            native_state_fd_50F6_0F30.signed_value++;
    }
}

void  DoRandR(int16_t x, int16_t y, int16_t attr, int16_t modeArg)
{
    if (SRand32() == 0)
        RlistM[Tindex] = GetNewModeR(modeArg);
    if (CheckNestFightR(x, y, attr))
        return;
    if (TryMoveDirR(x, y, attr & 7))
        return;
    TryMoveDirR(x, y, SRand8());
}

static uint8_t  nestFightMode[16] = {
    1, 1, 1, 3, 0, 5, 2, 3, 0, 5, 0, 0, 9, 9, 10, 0
};

void  DoNestFightR(int16_t x, int16_t y)
{
    RlistT[Tindex] = (RlistT[Tindex] & 0xf8) + SRand1(7);
    LifeR[x][y] = RlistT[Tindex];
    if (SRand16() == 0) {
        RlistT[Tindex] = LifeR[x][y] = RlistS[Tindex];
        if ((RlistT[Tindex] & 0x78) == 0x60)
            MakeNewTailR(Tindex);
        if (!(RlistT[Tindex] & 0x80))
            RlistM[Tindex] = 7;
        else
            RlistM[Tindex] = nestFightMode[(RlistT[Tindex] & 0x78) >> 3];
    } else if (fd_3D57_07B2 != 0)
        FightBalloons(x, y, 3);
}

int16_t  CheckNestFightR(int16_t x, int16_t y, int16_t attacker)
{
    int16_t ant;
    int16_t index;
    int16_t winner;

    ant = LifeR[x][y];
    if (ant > 7 && ant < 0x68) {
        index = FindInRList(x, y, ant);
        if (index >= 0) {
            winner = GetWinner(ant, attacker);
            RlistS[index] = winner;
            RlistT[index] = (winner & 0x80) + 0x70;
            LifeR[x][y] = (winner & 0x80) + 0x70;
            RlistM[index] = 0xa;
            return 1;
        }
    } else if (IsYellowAnt(ant) && native_state_fd_50F6_04E2.signed_value == 0) {
        o25_3BA4_0DFB(3, Tindex);
        return 1;
    }
    return 0;
}

int16_t  DropFoodR(int16_t x, int16_t y)
{
    int16_t level;
    int16_t result;

    result = 0;
    level = MapR[x][y];
    if (level < 16) {
        MapR[x][y] = 16;
        result = 1;
    } else if (level < 19) {
        MapR[x][y]++;
        result = 1;
    }
    ++native_state_FoodR.signed_value;
    if (RlistT[Tindex] & 8)
        RlistT[Tindex] -= 8;
    return result;
}

void  SimEggR(int16_t x, int16_t y)
{
    int16_t attr;
    int16_t mode;
    int16_t mask;

    attr = RlistT[Tindex];
    mode = -1;
    if (native_state_RpopT.signed_value == 1)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(native_state_Cycle.signed_value & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            mode = fd_3D57_0B36[((native_state_fd_50F6_10A6.signed_value % 7) << 3) + SRand8()];
            attr = (mode << 3) + 0x82;
            RlistM[Tindex] = GetNewModeR(mode);
        }
    }
    if (fd_3D57_07B2 != 0 && mode < 0)
        EggBalloons(x, y, 3);
    LifeR[x][y] = attr;
    RlistT[Tindex] = attr;
    RlistS[Tindex] = 0;
}

void  SimQueenR(int16_t x, int16_t y, int16_t caste, int16_t attr)
{
    int16_t type;
    int16_t nx;
    int16_t ny;

    if (caste == 12) {
        if (SRand64() == 0) {
            if (native_state_HealthR.signed_value == 0) {
                LifeR[x][y] = RlistT[Tindex] = 0;
                PictStrnDialog(0, 0x2720, 1);
                return;
            }
            if (QueenMoveR(x, y, attr))
                return;
        }
        type = RlistT[Tindex];
        if (LostTailR(x, y, type)) {
            type = 0;
            RlistT[Tindex] = 0;
            native_state_fd_50F6_036C.signed_value--;
        }
        LifeR[x][y] = type;
        if (fd_3D57_07B2 != 0)
            QueenBalloons(x, y, 3);
    } else if (caste == 13) {
        type = RlistT[Tindex];
        LifeR[x][y] = type;
        if (native_state_fd_50F6_036C.signed_value > 0 && LostHeadR(x, y, type)) {
            native_state_fd_50F6_036C.signed_value--;
            LifeR[x][y] = RlistT[Tindex] = 0;
            return;
        }
        nx = x + Dx8[(attr ^ 0xfc) & 7];
        ny = y + Dy8[(attr ^ 0xfc) & 7];
        if (InNestBounds(nx, ny)) {
            fd_3D57_02B8[0] = nx;
            fd_3D57_02B8[1] = ny;
            if ((native_state_Cycle.signed_value & 0xf) == 0 && SRand128() <= native_state_HealthR.signed_value) {
                PlaceEggR(nx, ny, 0x81);
                DecEatR();
            }
        }
    }
}

int16_t  QueenMoveR(int16_t x, int16_t y, int16_t dirHint)
{
    int16_t dir;
    int16_t newRow;
    int16_t newCol;
    int16_t opp;
    int16_t index;

    dir = o25_39C7_0CBD(3, x, y, native_state_fd_50F6_0200.signed_value, native_state_fd_50F6_020E.signed_value);
    if (dir < 0) {
        if (dir == -1)
            return 0;
        dir = SRand8();
    }
    if (y < 3 && (dir > 5 || dir < 3))
        return 0;
    if (TryMoveDirR(x, y, dir) != 0) {
        opp = (dirHint ^ 0xfc) & 7;
        newCol = x + Dx8[opp];
        newRow = y + Dy8[opp];
        LifeR[newCol][newRow] = 0;
        index = FindInRList(newCol, newRow, (dirHint & 7) + 0xe8);
        if (index >= 0 && RlistT[index] != 0) {
            RlistX[index] = x;
            RlistY[index] = y;
            RlistT[index] = dir - 0x18;
            LifeR[x][y] = dir - 0x18;
        }
        return 1;
    }
    return 0;
}

void  MakeNewTailR(int16_t index)
{
    uint8_t type;
    int16_t direction;
    int16_t life;
    int16_t column;

    type = RlistT[index];
    direction = type & 7;
    direction ^= 4;
    life = RlistX[index] + Dx8[direction];
    column = RlistY[index] + Dy8[direction];
    AddAntToRList(life, column, type + 8, 9, 0);
}

void  KillTailR(int16_t index)
{
    RlistT[index] = 0;
    LifeR[RlistX[index]][RlistY[index]] = 0;
}

int16_t  LostHeadR(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;
    int16_t newY;
    int16_t headMarker;
    int16_t newX;
    uint8_t cell;

    dir = attr & 7;
    newY = Dy8[dir];
    newX = x + Dx8[dir];
    newY += y;
    headMarker = attr - 8;
    cell = LifeR[newX][newY];
    if (cell == headMarker)
        return 0;
    if (FindInRList(newX, newY, headMarker) >= 0)
        return 0;
    return 1;
}

int16_t  LostTailR(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;
    int16_t newY;
    int16_t tailMarker;
    int16_t newX;
    uint8_t cell;

    dir = (attr ^ 0xfc) & 7;
    newY = Dy8[dir];
    newX = x + Dx8[dir];
    newY += y;
    tailMarker = attr + 8;
    cell = LifeR[newX][newY];
    if (cell == tailMarker)
        return 0;
    if (FindInRList(newX, newY, tailMarker) >= 0)
        return 0;
    return 1;
}

int16_t  TryMoveDirR(int16_t x, int16_t y, int16_t dir)
{
    int16_t dx;
    int16_t dy;

    if (dir < 0)
        return 0;
    dx = Dx8[dir] + x;
    dy = Dy8[dir] + y;
    if (dx > 0x3f)
        return 0;
    if (dx < 0)
        return 0;
    if (dy > 0x3f)
        return 0;
    if (dy < 1)
        return GetOutR(x);
    if (MapR[dx][dy] >= 0x1c)
        return 0;
    LifeR[dx][dy] = RlistT[Tindex] & 0xf8 | dir;
    LifeR[x][y] = 0;
    RlistX[Tindex] = dx;
    RlistY[Tindex] = dy;
    RlistT[Tindex] = LifeR[dx][dy];
    return 1;
}

void  DoNestingR(int16_t x, int16_t y, int16_t attr, int16_t caste)
{
    int16_t dir;
    int16_t ant;
    int16_t index;

    dir = attr & 7;
    if (caste == 1) {
        if (SRand4() == 0 && MapR[x][y] < 0x10) {
            RlistT[Tindex] += 8;
            LifeR[x][y] = RlistT[Tindex];
            PlaceEggR(x, y, 0x82);
            RlistS[Tindex] = 0;
            RlistM[Tindex] = GetNewModeR(caste);
            return;
        }
        if (SRand4() == 0 || (dir = GetEnterDirR(x, y, attr & 7)) < 0)
            dir = SRand8();
    } else if (caste == 2) {
        if (SRand4() == 0) {
            ant = LifeR[x][y];
            if (ant != 0 && (ant & 0x7f) < 8) {
                if ((index = FindInRList(x, y, ant)) >= 0) {
                    RlistT[index] = 0;
                    RlistT[Tindex] -= 8;
                    return;
                }
            } else if (SRand1(100) > native_state_HealthR.signed_value)
                TryEatFoodR(x, y);
            else
                RlistM[Tindex] = GetNewModeR(caste);
        }
        if (SRand4() != 0)
            dir = attr & 7;
        else
            dir = SRand8();
    } else
        RlistM[Tindex] = GetNewModeR(caste);
    if (TryMoveDirR(x, y, dir) == 0)
        TryMoveDirR(x, y, SRand8());
}

void  TryEatFoodR(int16_t y, int16_t x)
{
    int16_t threshold;
    int16_t level;

    level = MapR[y][x];
    if (level < 0x10 || level > 0x13)
        return;
    if (level == 0x10)
        MapR[y][x] = SRand8();
    else
        MapR[y][x]--;
    if (native_state_FoodR.signed_value > 0)
        native_state_FoodR.signed_value--;
    threshold = (native_state_RpopT.signed_value + native_sim_state_fd_50F6_0AFA.signed_values[2]) >> 4;
    native_state_fd_50F6_0226.signed_value += 5;
    if (threshold < native_state_fd_50F6_0226.signed_value) {
        native_state_fd_50F6_0226.signed_value = 0;
        if (native_state_HealthR.signed_value < 100)
            native_state_HealthR.signed_value++;
    }
}

void  EatFoodR(int16_t x, int16_t y)
{
    if (MapR[x][y] == 0x10)
        MapR[x][y] = SRand8();
    else
        MapR[x][y]--;
    if (native_state_FoodR.signed_value > 0)
        native_state_FoodR.signed_value--;
    native_state_fd_50F6_0226.signed_value += 5;
    if ((native_state_RpopT.signed_value + native_sim_state_fd_50F6_0AFA.signed_values[2]) >> 4 < native_state_fd_50F6_0226.signed_value) {
        native_state_fd_50F6_0226.signed_value = 0;
        if (native_state_HealthR.signed_value < 100)
            native_state_HealthR.signed_value++;
    }
}

void  StealFoodR(int16_t x, int16_t y)
{
    if (MapR[x][y] == 0x10)
        MapR[x][y] = SRand8();
    else
        MapR[x][y]--;
    if (native_state_FoodR.signed_value > 0)
        native_state_FoodR.signed_value--;
}

void  DecEatR(void)
{
    --native_state_fd_50F6_0226.signed_value;
    if (native_state_fd_50F6_0226.signed_value < 0) {
        native_state_fd_50F6_0226.signed_value = native_state_RpopT.signed_value >> 5;
        if (native_state_HealthR.signed_value > 0)
            --native_state_HealthR.signed_value;
    }
}

void  DoFoodInR(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;
    int16_t newattr;
    int16_t nx;
    int16_t ny;

    dir = GetEnterDirR(x, y, attr & 7);
    if (dir < 0 || SRand16() == 0) {
        DropFoodR(x, y);
        if (SRand1(100) > native_state_HealthR.signed_value)
            EatFoodR(x, y);
        RlistM[Tindex] = GetNewModeR((attr & 0x78) >> 3);
        return;
    }
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30)
        return;
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    newattr = (RlistT[Tindex] & 0xf8) | dir;
    RlistT[Tindex] = newattr;
    LifeR[nx][ny] = newattr;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
}

void  DoDigInR(int16_t x, int16_t y, int16_t attr, int16_t caste)
{
    int16_t dir;
    int16_t newattr;
    int16_t nx;
    int16_t ny;

    if (caste != 2 && caste != 6) {
        RlistM[Tindex] = GetNewModeR(caste);
        return;
    }
    dir = GetEnterDirR(x, y, attr & 7);
    if (dir < 0)
        dir = SRand8();
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    if (y == 0x3f) {
        RlistM[Tindex] = GetNewModeR(caste);
        return;
    }
    ny = y + Dy8[dir];
    nx = x + Dx8[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30)
        return;
    if (IsItDirt(MapR[nx][ny])) {
        if (DigTileThemR(nx, ny)) {
            RlistT[Tindex] += 0x18;
            RlistM[Tindex] = 5;
            myBeginSound(0x12, 0, 0);
        } else {
            RlistM[Tindex] = 0;
            return;
        }
    }
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    newattr = (RlistT[Tindex] & 0xf8) | dir;
    RlistT[Tindex] = newattr;
    LifeR[nx][ny] = newattr;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
    if (SRand64() > native_state_HealthR.signed_value)
        TryEatFoodR(x, y);
    if (SRand4() == 0)
        f_14EE_0D71(nx, ny);
    if (MapR[nx][ny] == 0x14) {
        LifeR[nx][ny] = RlistT[Tindex] = 0;
        /* constant-left comparison: `(newattr & 0x7f) < 0x30 ? ...` lays the 0xb0 arm out first
           (jl), `0x30 > (newattr & 0x7f)` gives the original jge / 0x90-arm-first layout */
        AddAntToBList(nx, ny, newattr = 0x30 > (newattr & 0x7f) ? SRand8() + 0x90 : SRand8() + 0xb0, 3, 0);
        LifeB[nx][ny] = newattr;
    }
}

void  DoDigOutR(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;
    int16_t newattr;
    int16_t nx;
    int16_t ny;
    int16_t caste;

    dir = GetExitDirR(x, y, attr & 7);
    if (dir > 0)
        dir--;
    else
        dir = RandTurn(attr & 7);
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (nx < 0 || nx > 0x3f || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30) {
        if (ExitMapR[x][y] != 0)
            ExitMapR[x][y]--;
        caste = (attr & 0x78) >> 3;
        if (caste == 5 || caste == 9) {
            RlistT[Tindex] -= 0x18;
            RlistM[Tindex] = 4;
        }
        if (caste == 2 || caste == 6)
            RlistM[Tindex] = 4;
        return;
    }
    if (IsItDirt(MapR[nx][ny]))
        return;
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    RlistT[Tindex] = LifeR[nx][ny] = (RlistT[Tindex] & 0xf8) | dir;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
    if (SRand64() > native_state_HealthR.signed_value)
        TryEatFoodR(x, y);
}

int16_t  GetOutR(int16_t x)
{
    int16_t raw;

    if (MapR[x][0] == 0x18) {
        raw = RlistT[Tindex];
        RlistT[Tindex] = 0;
        if (HoleMapR[x] == 0)
            MakeNewHoleR(x);
        if (ExitHole(HoleMapR[x], x, SRand8() + (raw & 0xf8),
                        RlistM[Tindex], RlistS[Tindex]) != 0) {
            LifeR[x][1] = 0;
            return 1;
        }
        RlistT[Tindex] = raw;
        RlistM[Tindex] = 0;
        return 0;
    }
    if (ExitMapR[x][0] != 0)
        ExitMapR[x][0]--;
    if (SRand2() != 0) {
        if (x > 0 && IsItDirt(MapR[x - 1][1]) != 0)
            DigTileThemR(x - 1, 1);
    } else {
        if (x < 0x3f && IsItDirt(MapR[x + 1][1]) != 0)
            DigTileThemR(x + 1, 1);
    }
    TryMoveDirR(x, 1, SRand8());
    return 0;
}

#pragma pack(pop)
