#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S25, code frame 39C7: black colony nest simulation (DoAntSimB unit).
 * Built /AL /Os /Oe /Og /Zi (like the sibling S25:3BA4): under /Zd 27 cross-function
 * relocation-order constraints are violated, under /Zi none.  Line layout: the seven
 * "map = list = value" stores are written as two statements (the file's own style, e.g.
 * "BlistT[..] = ..; fd_3E1D_8180[x][y] = BlistT[..];"); byte-identical either way, but the
 * extra /Zi line entries put the fourth 52-entry flush before GetBestDir's first GetDis
 * call, as its within-group relocation order requires (FORBID (0CDC,0D54]).
 * Worker resI: QueenMoveB (0DAF) writes its y<3 test as one condition (the nested form adds
 * references to dir, REG-3, and puts dir in SI); its final store is two statements like the
 * others, and TryMoveDirB (105B) tests its three trophallaxis conditions as nested ifs.  Both
 * are byte-identical to the one-line forms; their three extra /Zi line entries put the sixth
 * flush at 12FB (DoNestingB NEED (12E3,131E], FORBID (12FE,132D]) and the ninth outside
 * GetOutB's FORBID (1CFC,1DC0].  DoDigInB writes the DigTileThemB test as
 * "if (DigTileThemB(..)) {..} else {..; return;}" like its red twin DoDigInR (root:0F3F); the
 * negated early-return form compiles to the same instructions except that dir then loses DI
 * in the first region (allocation: the if/else form puts the GetEnterDirB result in DI and
 * spills it to [bp-4] after the y == 0x3f test, as the original does). */

extern int16_t  Tindex;
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];
extern uint8_t  BlistT[];
void  o25_39C7_006D(int16_t x, int16_t y, int16_t attr);

void  o25_39C7_0000(void)
{
    int16_t x;
    int16_t y;
    int16_t attr;

    Tindex = native_state_ListIndexB.signed_value;
    while (Tindex > 0) {
        --Tindex;
        x = BlistX[Tindex];
        y = BlistY[Tindex] & 0xff;
        attr = BlistT[Tindex];
        if (attr != 0)
            o25_39C7_006D(x, y, attr);
    }
}

extern uint8_t  BlistM[];
extern int16_t  SRand256(void);
extern int16_t  SRand32(void);
extern uint8_t  LifeB[64][64];
void  o25_39C7_0677(int16_t x, int16_t y, int16_t attr, int16_t caste);
void  DoNestingB(int16_t x, int16_t y, int16_t attr, int16_t caste);
void  DoFoodInB(int16_t x, int16_t y, int16_t attr);
void  DoDigInB(int16_t x, int16_t y, int16_t attr, int16_t caste);
void  o25_39C7_06E2(int16_t x, int16_t y, int16_t attr);
void  o25_39C7_0980(int16_t x, int16_t y);
void  o25_39C7_0AB0(int16_t x, int16_t y, int16_t caste, int16_t attr);
void  o25_39C7_0746(int16_t x, int16_t y);
void  o25_39C7_04E5(int16_t x, int16_t y, int16_t attr);
void  DoDigOutB(int16_t x, int16_t y, int16_t attr);
void  o25_39C7_0590(int16_t x, int16_t y, int16_t attr);
extern int16_t  IsYellowAnt(int16_t value);
extern void  o25_3BA4_0DFB(int16_t list, int16_t index);
extern int16_t  FindInBList(int16_t x, int16_t y, int16_t life);
void  o25_39C7_0F30(int16_t index);
extern int16_t  GetWinner(int16_t a, int16_t b);
extern uint8_t  BlistS[];
void  o25_39C7_038F(int16_t x, int16_t y, int16_t attr);
void  o25_39C7_0460(int16_t x, int16_t y, int16_t attr);

void  o25_39C7_006D(int16_t x, int16_t y, int16_t attr)
{
    int16_t caste;
    int16_t task;
    int16_t i;
    int16_t t;

    caste = (attr & 0x78) >> 3;
    if (!(attr & 0x80)) {
        t = BlistM[Tindex];
        fd_50F6_0D40[t]++;
        if (SRand256() == 0 && t != 9 && SRand32() > native_state_HealthB.signed_value) {
            BlistT[Tindex] = 0;
            LifeB[x][y] = 0;
            native_state_fd_50F6_0F30.signed_value++;
            return;
        }
        switch (t) {
        case 0:
            o25_39C7_0677(x, y, attr, caste);
            break;
        case 1:
            DoNestingB(x, y, attr, caste);
            break;
        case 2:
            DoDigOutB(x, y, attr);
            break;
        case 3:
            DoFoodInB(x, y, attr);
            break;
        case 4:
            DoDigInB(x, y, attr, caste);
            break;
        case 5:
            DoDigOutB(x, y, attr);
            break;
        case 6:
            o25_39C7_06E2(x, y, attr);
            break;
        case 7:
            DoDigOutB(x, y, attr);
            break;
        case 8:
            o25_39C7_0980(x, y);
            break;
        case 9:
            o25_39C7_0AB0(x, y, caste, attr);
            break;
        case 10:
            o25_39C7_0746(x, y);
            break;
        case 11:
        case 12:
            DoDigOutB(x, y, attr);
            break;
        case 13:
            o25_39C7_04E5(x, y, attr);
            break;
        case 14:
            o25_39C7_0677(x, y, attr, caste);
            if (native_state_fd_50F6_08DC.signed_value > 100)
                BlistM[Tindex] = 0xf;
            break;
        case 15:
        case 16:
            DoDigOutB(x, y, attr);
            break;
        case 17:
            o25_39C7_0590(x, y, attr);
            break;
        default:
            o25_39C7_0677(x, y, attr, caste);
            break;
        }
    } else {
        task = BlistM[Tindex];
        fd_50F6_0D72[task]++;
        if (attr > 0xef) {
            o25_39C7_0746(x, y);
            return;
        }
        caste = LifeB[x][y];
        if (IsYellowAnt(caste) == 1 && native_state_fd_50F6_04E2.signed_value == 0) {
            o25_3BA4_0DFB(2, Tindex);
            return;
        }
        if (caste > 0 && caste < 0x68 && (i = FindInBList(x, y, caste)) >= 0) {
            if (caste > 0x5f)
                o25_39C7_0F30(i);
            if (caste < 8) {
                BlistM[Tindex] = 3;
                BlistT[Tindex] |= 8;
                LifeB[x][y] = BlistT[Tindex];
                BlistT[i] = 0;
                native_state_fd_50F6_1000.signed_value++;
            } else {
                t = GetWinner(BlistT[i], attr);
                BlistT[Tindex] = 0;
                BlistS[i] = t;
                BlistT[i] = (t & 0x80) + 0x70;
                LifeB[x][y] = BlistT[i];
                BlistM[i] = 0xa;
            }
            return;
        }
        switch (task) {
        case 7:
            o25_39C7_038F(x, y, attr);
            break;
        default:
            o25_39C7_0460(x, y, attr);
            break;
        }
    }
}

extern uint8_t  MapB[64][64];
void  o25_39C7_154F(int16_t x, int16_t y);
extern int16_t  SRand1(int16_t range);
int16_t  o25_39C7_105B(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetEnterDirB(int16_t x, int16_t y, int16_t dir);
extern int16_t  GetExitDirB(int16_t x, int16_t y, int16_t limit);
extern int16_t  SRand8(void);
int16_t  o25_39C7_0853(int16_t x, int16_t y, int16_t attacker);
extern int16_t  GetNewMode(int16_t caste, int16_t type);
extern int16_t  fd_3D57_07A8[];
extern void  RestBalloons(int16_t x, int16_t y, int16_t plane);

void  o25_39C7_038F(int16_t x, int16_t y, int16_t dirHint)
{
    int16_t dir;

    if (MapB[x][y] >= 0x10 && MapB[x][y] <= 0x13) {
        o25_39C7_154F(x, y);
        BlistM[Tindex] = 3;
        BlistT[Tindex] |= 8;
        LifeB[x][y] = BlistT[Tindex];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    dir = GetEnterDirB(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    BlistM[Tindex] = 1;
    LifeB[x][y] = BlistT[Tindex];
}

void  o25_39C7_0460(int16_t x, int16_t y, int16_t attr)
{
    int16_t dir;

    dir = GetExitDirB(x, y, 8);
    if (dir == 0)
        dir = SRand8();
    else
        dir--;
    if (o25_39C7_105B(x, y, dir) == 0) {
        if (o25_39C7_105B(x, y, SRand8()) == 0)
            LifeB[x][y] = BlistT[Tindex];
    }
}

void  o25_39C7_04E5(int16_t x, int16_t y, int16_t attacker)
{
    int16_t type;

    if (o25_39C7_0853(x, y, attacker) == 1)
        return;
    LifeB[x][y] = BlistT[Tindex];
    if (SRand1(20) == 0) {
        type = BlistT[Tindex];
        BlistM[Tindex] = GetNewMode((type & 0x78) >> 3, type);
        return;
    }
    if (fd_3D57_07A8[5] == 1)
        RestBalloons(x, y, 2);
}

extern int16_t  GetNewModeB(int16_t caste);
extern int16_t  MePlane;

void  o25_39C7_0590(int16_t x, int16_t y, int16_t attr)
{
    if (MapB[x][y] < 0x14) {
        BlistM[Tindex] = GetNewModeB((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    BlistT[Tindex] = attr;
    LifeB[x][y] = BlistT[Tindex];
    if (SRand1(100) == 0) {
        LifeB[x][y] = 0;
        BlistT[Tindex] = LifeB[x][y];
        if (attr & 0x80)
            native_state_fd_50F6_0FBC.signed_value++;
        else
            native_state_fd_50F6_0F30.signed_value++;
    }
}

void  o25_39C7_0677(int16_t x, int16_t y, int16_t attr, int16_t caste)
{
    if (SRand32() == 0)
        BlistM[Tindex] = GetNewModeB(caste);
    if (o25_39C7_0853(x, y, attr) == 1)
        return;
    if (o25_39C7_105B(x, y, attr & 7) != 0)
        return;
    o25_39C7_105B(x, y, SRand8());
}

void  o25_39C7_06E2(int16_t x, int16_t y, int16_t attr)
{
    if (MePlane != 2) {
        DoDigOutB(x, y, attr);
        return;
    }
    if (o25_39C7_0853(x, y, attr) == 1)
        return;
    if (o25_39C7_105B(x, y, attr & 7) != 0)
        return;
    o25_39C7_105B(x, y, SRand8());
}

extern int16_t  SRand16(void);
void  o25_39C7_0EC2(int16_t index);
extern void  FightBalloons(int16_t x, int16_t y, int16_t plane);

void  o25_39C7_0746(int16_t x, int16_t y)
{
    BlistT[Tindex] = (BlistT[Tindex] & 0xf8) + SRand1(7);
    LifeB[x][y] = BlistT[Tindex];
    if (SRand16() == 0) {
        LifeB[x][y] = BlistS[Tindex];
        BlistT[Tindex] = LifeB[x][y];
        if ((BlistT[Tindex] & 0x78) == 0x60)
            o25_39C7_0EC2(Tindex);
        if (BlistT[Tindex] & 0x80)
            BlistM[Tindex] = 7;
        else
            BlistM[Tindex] = GetNewMode((BlistT[Tindex] & 0x78) >> 3, BlistT[Tindex]);
    } else if (fd_3D57_07A8[5] == 1)
        FightBalloons(x, y, 2);
}

int16_t  o25_39C7_0853(int16_t x, int16_t y, int16_t attacker)
{
    int16_t ant;
    int16_t index;
    int16_t winner;

    ant = LifeB[x][y];
    if (IsYellowAnt(ant) == 1 && native_state_fd_50F6_04E2.signed_value != 0) {
        o25_3BA4_0DFB(2, Tindex);
        return 1;
    }
    if (ant > 0x87 && ant < 0xe8 && (index = FindInBList(x, y, ant)) >= 0) {
        winner = GetWinner(ant, attacker);
        BlistS[index] = winner;
        BlistT[index] = (winner & 0x80) + 0x70;
        LifeB[x][y] = BlistT[index];
        BlistM[index] = 0xa;
        return 1;
    }
    return 0;
}

int16_t  o25_39C7_090A(int16_t x, int16_t y)
{
    int16_t result;
    int16_t food;

    result = 0;
    food = MapB[x][y];
    if (food < 0x10) {
        MapB[x][y] = 0x10;
        result = 1;
    } else if (food < 0x13) {
        MapB[x][y]++;
        result = 1;
    }
    native_state_FoodB.signed_value++;
    if (BlistT[Tindex] & 8)
        BlistT[Tindex] -= 8;
    return result;
}

extern int16_t  SGRand(int16_t range);
extern int16_t  fd_3D57_0C0E;
extern void  EggBalloons(int16_t x, int16_t y, int16_t plane);

void  o25_39C7_0980(int16_t x, int16_t y)
{
    int16_t attr;
    int16_t mode;
    int16_t mask;

    attr = BlistT[Tindex];
    mode = -1;
    if (native_state_BpopT.signed_value <= 2)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(native_state_Cycle.signed_value & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            if (native_state_ModeAuto.signed_value != 0 || (int16_t)(native_sim_state_modeLevels.unsigned_values[2] >> 7) >= SGRand(255)) {
                mode = fd_3D57_0C0E;
                attr = (mode << 3) + 2;
                if (mode == 2)
                    BlistM[Tindex] = 1;
                else
                    BlistM[Tindex] = GetNewModeB(mode);
            } else {
                attr = 0;
                native_state_fd_50F6_1000.signed_value++;
            }
        }
    }
    if (fd_3D57_07A8[5] != 0 && mode < 0)
        EggBalloons(x, y, 2);
    LifeB[x][y] = attr;
    BlistT[Tindex] = attr;
    BlistS[Tindex] = 0;
}

extern int16_t  SRand64(void);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
int16_t  o25_39C7_0DAF(int16_t x, int16_t y, int16_t dirHint);
int16_t  o25_39C7_0FE7(int16_t x, int16_t y, int16_t attr);
extern void  QueenBalloons(int16_t x, int16_t y, int16_t plane);
int16_t  o25_39C7_0F76(int16_t x, int16_t y, int16_t attr);
extern int8_t  Dy8[];
extern int8_t  Dx8[];
extern int16_t  InNestBounds(int16_t x, int16_t y);
extern int16_t  fd_3D57_02B4[2];
extern int16_t  SRand128(void);
extern void  PlaceEggB(int16_t x, int16_t y, int16_t type);
void  o25_39C7_15B4(void);

void  o25_39C7_0AB0(int16_t x, int16_t y, int16_t caste, int16_t attr)
{
    int16_t t;
    int16_t nx;
    int16_t ny;

    if (caste == 12) {
        if (SRand64() == 0) {
            if (native_state_HealthB.signed_value == 0) {
                BlistT[Tindex] = 0;
                LifeB[x][y] = BlistT[Tindex];
                PictStrnDialog(0, 0x271f, 1);
                return;
            }
            if (o25_39C7_0DAF(x, y, attr) != 0)
                return;
        }
        t = BlistT[Tindex];
        if (o25_39C7_0FE7(x, y, t) != 0) {
            t = 0;
            BlistT[Tindex] = 0;
            native_state_fd_50F6_035E.signed_value--;
        }
        LifeB[x][y] = t;
        if (fd_3D57_07A8[5] != 0)
            QueenBalloons(x, y, 2);
    } else if (caste == 13) {
        t = BlistT[Tindex];
        LifeB[x][y] = t;
        if (native_state_fd_50F6_035E.signed_value > 0 && o25_39C7_0F76(x, y, t) != 0) {
            native_state_fd_50F6_035E.signed_value--;
            BlistT[Tindex] = 0;
            LifeB[x][y] = BlistT[Tindex];
            return;
        }
        nx = Dx8[(attr ^ 4) & 7] + x;
        ny = Dy8[(attr ^ 4) & 7] + y;
        if (InNestBounds(nx, ny)) {
            fd_3D57_02B4[0] = nx;
            fd_3D57_02B4[1] = ny;
            if (!(native_state_Cycle.signed_value & 0xf) && SRand128() <= native_state_HealthB.signed_value) {
                PlaceEggB(nx, ny, 1);
                o25_39C7_15B4();
                native_state_fd_50F6_0FC2.signed_value++;
            }
        }
    }
}

extern int32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  GetMap(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsNotObstacle(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsThisPebble(int16_t plane, int16_t tile);
extern int16_t  GetLife(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y);

int16_t  o25_39C7_0CBD(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t fallback;
    int16_t best;
    int16_t threshold;
    int16_t dir;
    int16_t nx;
    int16_t ny;
    int16_t tile;
    int16_t dis;

    best = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold <= 0)
        goto done;
    fallback = -2;
    for (dir = 0; dir < 8; dir++) {
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        tile = GetMap(plane, nx, ny);
        if (IsNotObstacle(plane, nx, ny) != 1)
            continue;
        if (IsThisPebble(plane, tile) != 0)
            continue;
        dis = GetDis(nx, ny, a, b);
        if (dis >= threshold)
            continue;
        if (GetLife(plane, nx, ny) <= 0 && IsClearTile(plane, nx, ny) == 1)
            best = dir;
        else
            fallback = dir;
        threshold = dis;
    }
    if (best < 0)
        best = fallback;
done:
    return best;
}

int16_t  o25_39C7_0DAF(int16_t x, int16_t y, int16_t dirHint)
{
    int16_t newRow;
    int16_t newCol;
    int16_t opp;
    int16_t index;
    int16_t dir;

    dir = o25_39C7_0CBD(2, x, y, native_state_fd_50F6_10B2.signed_value, native_state_fd_50F6_10C0.signed_value);
    if (dir < 0) {
        if (dir == -1)
            return 0;
        dir = SRand8();
    }
    if (y < 3 && (dir > 5 || dir < 3))
        return 0;
    if (o25_39C7_105B(x, y, dir) != 0) {
        opp = (dirHint ^ 0xfc) & 7;
        newCol = x + Dx8[opp];
        newRow = y + Dy8[opp];
        LifeB[newCol][newRow] = 0;
        index = FindInBList(newCol, newRow, (dirHint & 7) + 0x68);
        if (index >= 0 && BlistT[index] != 0) {
            BlistX[index] = x;
            BlistY[index] = y;
            BlistT[index] = dir + 0x68;
            LifeB[x][y] = BlistT[index];
        }
        return 1;
    }
    return 0;
}

extern void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t flag);

void  o25_39C7_0EC2(int16_t index)
{
    uint8_t type;
    int16_t direction;
    int16_t life;
    int16_t column;

    type = BlistT[index];
    direction = type & 7;
    direction ^= 4;
    life = BlistX[index] + Dx8[direction];
    column = BlistY[index] + Dy8[direction];
    AddAntToBList(life, column, type + 8, 9, 0);
}

void  o25_39C7_0F30(int16_t index)
{
    LifeB[BlistX[index]][BlistY[index]] = BlistT[index] = 0;
}

int16_t  o25_39C7_0F76(int16_t x, int16_t y, int16_t attr)
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
    cell = LifeB[newX][newY];
    if (cell == headMarker)
        return 0;
    if (FindInBList(newX, newY, headMarker) >= 0)
        return 0;
    return 1;
}

int16_t  o25_39C7_0FE7(int16_t x, int16_t y, int16_t attr)
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
    cell = LifeB[newX][newY];
    if (cell == tailMarker)
        return 0;
    if (FindInBList(newX, newY, tailMarker) >= 0)
        return 0;
    return 1;
}

int16_t  o25_39C7_1C81(int16_t x);
extern void  DoTroph(int16_t x, int16_t y, int16_t dir);

int16_t  o25_39C7_105B(int16_t x, int16_t y, int16_t dir)
{
    int16_t dy;
    int16_t dx;

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
        return o25_39C7_1C81(x);
    if (MapB[dx][dy] >= 0x1c)
        return 0;
    if (LifeB[dx][dy] == 0xff)
        if (native_state_fd_50F6_1044.signed_value)
            if (BlistX[Tindex] < 0x80) {
                LifeB[x][y] = BlistT[Tindex] & 0xf8 | (uint8_t)dir;
                DoTroph(x, y, dir);
            }
    LifeB[dx][dy] = BlistT[Tindex] & 0xf8 | (uint8_t)dir;
    LifeB[x][y] = 0;
    BlistX[Tindex] = (uint8_t)dx;
    BlistY[Tindex] = (uint8_t)dy;
    BlistT[Tindex] = LifeB[dx][dy];
    return 1;
}

void  o25_39C7_13EF(int16_t x, int16_t y);

/* autosearch: exact after rules IF-NEG */
void  DoNestingB(int16_t x, int16_t y, int16_t attr, int16_t caste)
{
    int16_t dir;
    uint8_t food;
    int16_t load;
    uint8_t cell;
    int16_t index;

    dir = attr & 7;
    load = BlistS[Tindex] & 7;
    cell = LifeB[x][y];
    food = BlistS[Tindex] >> 3;
    switch (caste) {
    case 1:
        if (food == 0) {
            if ((dir = GetEnterDirB(x, y, attr & 7)) < 0)
                BlistS[Tindex] = load | 8;
            break;
        }
        if (cell == 0 || cell > 8) {
            BlistT[Tindex] += 8;
            PlaceEggB(x, y, load);
            LifeB[x][y] = BlistT[Tindex];
            BlistS[Tindex] = 8;
            BlistM[Tindex] = GetNewModeB(caste);
        }
        if ((dir = GetExitDirB(x, y, attr & 7)) == 0)
            dir = SRand8();
        else
            dir--;
        break;
    case 2:
        if (food != 0) {
            if (SRand8() == 0)
                BlistS[Tindex] = 0;
            if ((dir = GetExitDirB(x, y, attr & 7)) == 0)
                dir = SRand8();
            else
                dir--;
            break;
        }
        if (cell != 0 && cell < 8) {
            if ((index = FindInBList(x, y, cell)) >= 0) {
                BlistT[index] = 0;
                BlistT[Tindex] -= 8;
                BlistS[Tindex] = cell;
                return;
            }
        } else if (SRand1(100) > native_state_HealthB.signed_value)
            o25_39C7_13EF(x, y);
        else if (SRand16() == 0)
            BlistM[Tindex] = GetNewModeB(caste);
        dir = attr & 7;
        break;
    default:
        if (SRand1(100) > native_state_HealthB.signed_value)
            o25_39C7_13EF(x, y);
        if (SRand8() == 0)
            BlistM[Tindex] = GetNewModeB(caste);
        break;
    }
    if (o25_39C7_105B(x, y, dir) == 0)
        o25_39C7_105B(x, y, SRand8());
}

extern int16_t  fd_3D57_0C18;

void  o25_39C7_13EF(int16_t x, int16_t y)
{
    int16_t threshold;
    int16_t level;

    level = MapB[x][y];
    if (level < 0x10 || level > 0x13)
        return;
    if (level == 0x10)
        MapB[x][y] = SRand8();
    else
        MapB[x][y]--;
    if (native_state_FoodB.signed_value > 0)
        native_state_FoodB.signed_value--;
    threshold = (native_state_BpopT.signed_value + native_sim_state_fd_50F6_0AEC.signed_values[2]) >> 4;
    native_state_fd_50F6_0212.signed_value += 5;
    if (threshold < native_state_fd_50F6_0212.signed_value) {
        native_state_fd_50F6_0212.signed_value = 0;
        if (native_state_HealthB.signed_value < 100)
            native_state_HealthB.signed_value++;
    }
}

void  o25_39C7_14A8(int16_t x, int16_t y)
{
    if (MapB[x][y] == 0x10)
        MapB[x][y] = SRand8();
    else
        MapB[x][y]--;
    if (native_state_FoodB.signed_value > 0)
        native_state_FoodB.signed_value--;
    native_state_fd_50F6_0212.signed_value += 5;
    if ((native_state_BpopT.signed_value + native_sim_state_fd_50F6_0AEC.signed_values[2]) >> 4 < native_state_fd_50F6_0212.signed_value) {
        native_state_fd_50F6_0212.signed_value = 0;
        if (native_state_HealthB.signed_value < 100)
            native_state_HealthB.signed_value++;
    }
}

void  o25_39C7_154F(int16_t x, int16_t y)
{
    if (MapB[x][y] == 0x10)
        MapB[x][y] = SRand8();
    else
        MapB[x][y]--;
    if (native_state_FoodB.signed_value > 0)
        native_state_FoodB.signed_value--;
}

void  o25_39C7_15B4(void)
{
    --native_state_fd_50F6_0212.signed_value;
    if (native_state_fd_50F6_0212.signed_value < 0) {
        native_state_fd_50F6_0212.signed_value = native_state_BpopT.signed_value >> 5;
        if (native_state_HealthB.signed_value > 0 && !fd_3D57_0C18)
            --native_state_HealthB.signed_value;
    }
}


void  DoFoodInB(int16_t x, int16_t y, int16_t attr)
{
    int16_t nx;
    int16_t dir;
    int16_t newattr;
    int16_t ny;

    if ((dir = GetEnterDirB(x, y, attr & 7)) >= 0 && SRand16() != 0) {
        newattr = (attr & 0xf8) | dir;
        BlistT[Tindex] = LifeB[x][y] = newattr;
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        if (nx > 0x3f || nx < 0 || ny > 0x3f)
            return;
        if (ny < 1) {
            o25_39C7_1C81(x);
            return;
        }
        if (MapB[nx][ny] >= 0x30)
            return;
        LifeB[x][y] = 0;
        if ((LifeB[nx][ny] & 0x80)
            && (!IsYellowAnt(LifeB[nx][ny]) || native_state_fd_50F6_04E2.signed_value != 0)
            && o25_39C7_0853(nx, ny, newattr))
            return;
        newattr = (BlistT[Tindex] & 0xf8) | dir;
        BlistT[Tindex] = newattr;
        LifeB[nx][ny] = newattr;
        BlistX[Tindex] = nx;
        BlistY[Tindex] = ny;
        return;
    }
    o25_39C7_090A(x, y);
    if (SRand1(100) > native_state_HealthB.signed_value)
        o25_39C7_14A8(x, y);
    BlistM[Tindex] = GetNewModeB((attr & 0x78) >> 3);
}

extern int16_t  IsItDirt(int16_t value);
extern int16_t  DigTileThemB(int16_t x, int16_t y);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  f_14EE_0C9C(int16_t x, int16_t y);
extern int16_t  SRand4(void);

void  DoDigInB(int16_t x, int16_t y, int16_t attr, int16_t caste)
{
    int16_t dir;
    int16_t newattr;
    int16_t nx;
    int16_t ny;
    int16_t tile;

    if (caste != 2 && caste != 6) {
        BlistM[Tindex] = GetNewModeB(caste);
        return;
    }
    if ((dir = GetEnterDirB(x, y, attr & 7)) < 0)
        dir = SRand8();
    newattr = (attr & 0xf8) | dir;
    BlistT[Tindex] = LifeB[x][y] = newattr;
    if (y == 0x3f) {
        BlistM[Tindex] = GetNewModeB(caste);
        return;
    }
    nx = Dx8[dir] + x;
    ny = Dy8[dir] + y;
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        o25_39C7_1C81(x);
        return;
    }
    tile = MapB[nx][ny];
    if (tile >= 0x30)
        return;
    if (IsItDirt(tile)) {
        if (DigTileThemB(nx, ny)) {
            BlistT[Tindex] += 0x18;
            BlistM[Tindex] = 5;
            myBeginSound(0x11, 0, 0);
        } else {
            BlistM[Tindex] = GetNewModeB(caste);
            return;
        }
    }
    LifeB[x][y] = 0;
    if ((LifeB[nx][ny] & 0x80)
        && (!IsYellowAnt(LifeB[nx][ny]) || native_state_fd_50F6_04E2.signed_value != 0)
        && o25_39C7_0853(nx, ny, newattr))
        return;
    newattr = (BlistT[Tindex] & 0xf8) | dir;
    BlistT[Tindex] = newattr;
    LifeB[nx][ny] = newattr;
    BlistX[Tindex] = nx;
    BlistY[Tindex] = ny;
    if (SRand64() > native_state_HealthB.signed_value)
        o25_39C7_13EF(nx, ny);
    if (SRand4() == 0)
        f_14EE_0C9C(nx, ny);
}

extern int16_t  RandTurn(int16_t dir);
extern uint8_t  ExitMapB[64][64];

void  DoDigOutB(int16_t x, int16_t y, int16_t attr)
{
    int16_t ny;
    int16_t nx;
    int16_t newattr;
    int16_t dir;
    int16_t caste;

    if ((dir = GetExitDirB(x, y, attr & 7)) > 0)
        dir--;
    else
        dir = RandTurn(attr & 7);
    newattr = (attr & 0xf8) | dir;
    BlistT[Tindex] = LifeB[x][y] = newattr;
    nx = Dx8[dir] + x;
    ny = Dy8[dir] + y;
    if (nx < 0 || nx > 0x3f || ny > 0x3f)
        return;
    if (ny < 1) {
        o25_39C7_1C81(x);
        return;
    }
    if (MapB[nx][ny] >= 0x30) {
        ExitMapB[x][y]--;
        caste = (attr & 0x78) >> 3;
        if (caste == 5 || caste == 9) {
            BlistT[Tindex] -= 0x18;
            BlistM[Tindex] = 4;
        }
        if (caste == 2 || caste == 6)
            BlistM[Tindex] = 4;
        return;
    }
    if (IsItDirt(MapB[nx][ny]))
        return;
    LifeB[x][y] = 0;
    if ((LifeB[nx][ny] & 0x80)
        && (!IsYellowAnt(LifeB[nx][ny]) || native_state_fd_50F6_04E2.signed_value != 0)
        && o25_39C7_0853(nx, ny, newattr))
        return;
    BlistT[Tindex] = LifeB[nx][ny] = (BlistT[Tindex] & 0xf8) | dir;
    BlistX[Tindex] = nx;
    BlistY[Tindex] = ny;
    if (SRand64() > native_state_HealthB.signed_value)
        o25_39C7_13EF(nx, ny);
}

extern uint8_t  HoleMapB[];
extern void  MakeNewHoleB(int16_t x);
extern int16_t  ExitHole(int16_t hole, int16_t x, int16_t dir, int16_t mode, int16_t state);
extern int16_t  SRand2(void);

int16_t  o25_39C7_1BBB(int16_t x, int16_t y)
{
    int16_t dir;

    dir = BlistT[Tindex];
    BlistT[Tindex] = 0;
    if (HoleMapB[x] == 0)
        MakeNewHoleB(x);
    if (ExitHole(HoleMapB[x], x, SRand8() + (dir & 0xf8),
                    BlistM[Tindex], BlistS[Tindex])) {
        LifeB[x][y] = 0;
        return 1;
    }
    BlistT[Tindex] = dir;
    BlistM[Tindex] = 0;
    return 0;
}


int16_t  o25_39C7_1C81(int16_t x)
{
    int16_t raw;

    if (MapB[x][0] == 0x18) {
        raw = BlistT[Tindex];
        BlistT[Tindex] = 0;
        if (HoleMapB[x] == 0)
            MakeNewHoleB(x);
        if (ExitHole(HoleMapB[x], x, SRand8() + (raw & 0xf8),
                        BlistM[Tindex], BlistS[Tindex]) != 0) {
            LifeB[x][1] = 0;
            return 1;
        }
        BlistT[Tindex] = raw;
        BlistM[Tindex] = 0;
        return 0;
    }
    if (ExitMapB[x][0] != 0)
        ExitMapB[x][0]--;
    if (SRand2() != 0) {
        if (x > 0 && IsItDirt(MapB[x - 1][1]) != 0)
            DigTileThemB(x - 1, 1);
    } else {
        if (x < 0x3f && IsItDirt(MapB[x + 1][1]) != 0)
            DigTileThemB(x + 1, 1);
    }
    o25_39C7_105B(x, 1, SRand8());
    return 0;
}



#pragma pack(pop)
