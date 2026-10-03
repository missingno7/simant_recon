#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S22, code frame 3BBD: experiment-mode map editor tools (Win16
 * ANTEDIT run processExp..SetSM, same 23 members in the same order).
 * Built /AL /Os /Oe /Og /Zi (like S22:39C7: one code record per function, which
 * the program-wide __aFchkstk relocation order requires).  processExp takes the
 * third argument processEdit passes (unused).  Declaration placement is part of
 * the fingerprint (identifier-count sensitivity): the ExpAddAnt prototype ahead of
 * processExp fixes its compare order, the IsItWall prototype ahead of IncFoodHere
 * fixes its compares.  DropWall/ExpDig walk local copies of their start point
 * (the copies decide the SI/DI assignment).  IncFoodHere keeps the original
 * dangling else.  The one-line "} else v++;" puts the 52-line-entry record break
 * inside ConnectAll where the original has it. */

struct Pt {
    int16_t x;
    int16_t y;
};

extern int16_t  fd_50F6_09FC[2];
extern int16_t  IsValidLocation(int16_t plane, int16_t x, int16_t y);
void  DoTool(int16_t x, int16_t y);
void  ExpAddAnt(int16_t x, int16_t y);
void  ReDrawMapEdit(int16_t flags);
extern int16_t  myButton(void);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern int16_t  fd_50F6_0A9C;
extern int16_t  win_IsWinInFront(int16_t win);
extern int16_t  fd_50F6_3856;
extern int16_t  fd_50F6_3858;
extern int16_t  g_19BE;
extern int16_t  g_19C0;

void  processExp(int16_t x, int16_t y, int16_t shift)
{
    int16_t nx;
    int16_t ny;
    int16_t count;
    struct Pt pt;

    if (native_state_MapPlane.signed_value) {
        count = 0;
        fd_50F6_09FC[0] = x;
        fd_50F6_09FC[1] = y;
        if (IsValidLocation(native_state_MapPlane.signed_value, x, y))
            DoTool(x, y);
        ReDrawMapEdit(count);
        while (myButton() == 1) {
            f_1FD2_04D0(&pt);
            fd_50F6_0A9C++;
            if (win_IsWinInFront(0x100)) {
                nx = (pt.x - native_game_fd_50F6_10D2.words[0]) / fd_50F6_3856;
                ny = (pt.y - native_game_fd_50F6_10D2.words[1]) / fd_50F6_3858;
                if (native_state_MapPlane.signed_value > 1)
                    nx -= 32;
            } else {
                nx = (pt.x - native_game_fd_50F6_110C.words[0]) / g_19BE + native_sim_state_fd_50F6_0508.words[0];
                ny = (pt.y - native_game_fd_50F6_110C.words[1]) / g_19C0 + native_sim_state_fd_50F6_0508.words[1];
            }
            if (nx != x || ny != y) {
                fd_50F6_09FC[0] = x;
                fd_50F6_09FC[1] = y;
                x = nx;
                y = ny;
                if (IsValidLocation(native_state_MapPlane.signed_value, x, y))
                    DoTool(x, y);
            }
            if (native_state_CurExpTool.signed_value >= 5 && IsValidLocation(native_state_MapPlane.signed_value, nx, ny)) {
                DoTool(nx, ny);
                fd_50F6_106C ^= 1;
            }
            count = (count + 1) & 0x3f;
            ReDrawMapEdit(count);
        }
    }
}

extern int16_t  GetLife(int16_t plane, int16_t x, int16_t y);
extern void  MagnifyMenu(int16_t x, int16_t y, int16_t plane);
void  DropWall(int16_t x, int16_t y, int16_t tx, int16_t ty);
void  ExpDig(int16_t x, int16_t y, int16_t tx, int16_t ty);
void  ExpAddFood(int16_t x, int16_t y);
void  ExpIncSmell(int16_t x, int16_t y);
void  ExpKillAnts(int16_t x, int16_t y);

void  DoTool(int16_t x, int16_t y)
{
    switch (native_state_CurExpTool.signed_value) {
    case 0:
        if (GetLife(native_state_MapPlane.signed_value, x, y))
            MagnifyMenu(x, y, native_state_MapPlane.signed_value);
        break;
    case 1:
        if (native_state_MapPlane.signed_value == 1)
            DropWall(fd_50F6_09FC[0], fd_50F6_09FC[1], x, y);
        break;
    case 2:
        ExpDig(fd_50F6_09FC[0], fd_50F6_09FC[1], x, y);
        break;
    case 3:
        ExpAddAnt(x, y);
        break;
    case 4:
        ExpAddFood(x, y);
        break;
    case 5:
        ExpIncSmell(x, y);
        break;
    case 6:
        ExpKillAnts(x, y);
        break;
    }
}

extern void  UpdateEdit(void);
extern void  f_0250_0ED2(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  MakeDMap(int16_t mode);
extern void  o12_384C_100A(void);

void  ReDrawMapEdit(int16_t flags)
{
    if (win_IsWinInFront(0)) {
        UpdateEdit();
        f_0250_0ED2();
        if (!win_IsWinOpen(0x100))
            return;
        if (flags & 3)
            return;
        MakeDMap(1);
        o12_384C_100A();
        return;
    }

    MakeDMap(1);
    o12_384C_100A();
    if (!win_IsWinOpen(0))
        return;
    if (flags & 3)
        return;
    UpdateEdit();
    f_0250_0ED2();
}

extern int16_t  IsValidA(int16_t x, int16_t y);
extern uint8_t  MapA[128][64];
extern int16_t  SRand1(int16_t range);
void  ConnectAll(int16_t x, int16_t y);
extern char  ExpSubStates[];
extern uint8_t  LifeA[128][64];
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int8_t  Dx9[];
extern int8_t  Dy9[];

void  DropWall(int16_t fromX, int16_t fromY, int16_t tx, int16_t ty)
{
    int16_t x;
    int16_t y;
    int16_t dir;

    x = fromX;
    y = fromY;

    while (IsValidA(x, y)) {
        if (dos_keyboard_modifiers() & 8) {
            if (MapA[x][y] > 0x50 && MapA[x][y] < 0x68)
                MapA[x][y] = SRand1(16);
            ConnectAll(x, y);
        } else if (ExpSubStates[1] == 0) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0)
                MapA[x][y] = 0x60;
            ConnectAll(x, y);
            myBeginSound(0x28, 0, 0x7e);
        } else {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0)
                MapA[x][y] = SRand1(3) + 0x51;
            myBeginSound(10, SRand1(10000) + 2000, 0x7e);
        }
        dir = GetDir(x, y, tx, ty);
        if (Dx9[dir])
            x += Dx9[dir];
        else
            y += Dy9[dir];
        if (dir == 0)
            break;
    }
}

extern int16_t  DigMyNewHole(int16_t x, int16_t y);
extern void  *  *  fd_50F6_034C;
extern void  EditMessage(void  *msg, int32_t ticks, int16_t mode);
extern int16_t  IsItDigable(int16_t plane, int16_t x, int16_t y);
extern void  DigTileB(int16_t x, int16_t y);
extern void  MakeNewHoleB(int16_t x);
extern void  DigTileR(int16_t x, int16_t y);
extern void  MakeNewHoleR(int16_t x);
extern uint8_t  LifeB[64][64];
void  ClearLifeB(int16_t x, int16_t y);
void  FillDirtB(int16_t x, int16_t y);
extern uint8_t  LifeR[64][64];
void  ClearLifeR(int16_t x, int16_t y);
void  FillDirtR(int16_t x, int16_t y);

void  ExpDig(int16_t fromX, int16_t fromY, int16_t tx, int16_t ty)
{
    int16_t x;
    int16_t y;
    int16_t fill;
    int16_t dir;


    fill = ExpSubStates[2];
    if (dos_keyboard_modifiers() & 8)
        fill ^= 1;
    x = fromX;
    y = fromY;
    do {
        if (fill == 0) {
            switch (native_state_MapPlane.signed_value) {
            case 1:
                if (DigMyNewHole(x, y)) {
                    myBeginSound(0x13, 0, 0x7e);
                } else {
                    myBeginSound(1, 0, 0x7e);
                    EditMessage(fd_50F6_034C[22], 120L, 1);
                }
                break;
            case 2:
                if (!IsItDigable(2, x, y) || y == 0)
                    break;
                DigTileB(x, y);
                if (y == 1)
                    MakeNewHoleB(x);
                myBeginSound(0x13, 0, 0x7e);
                break;
            case 3:
                if (!IsItDigable(3, x, y) || y == 0)
                    break;
                DigTileR(x, y);
                if (y == 1)
                    MakeNewHoleR(x);
                myBeginSound(0x13, 0, 0x7e);
                break;
            }
        } else {
            switch (native_state_MapPlane.signed_value) {
            case 1:
                myBeginSound(1, 0, 0x7e);
                EditMessage(fd_50F6_034C[21], 180L, 1);
                break;
            case 2:
                if (IsItDigable(2, x, y) || y == 0)
                    break;
                if (LifeB[x][y])
                    ClearLifeB(x, y);
                FillDirtB(x, y);
                myBeginSound(0x12, 0, 0x7e);
                break;
            case 3:
                if (IsItDigable(3, x, y) || y == 0)
                    break;
                if (LifeR[x][y])
                    ClearLifeR(x, y);
                FillDirtR(x, y);
                myBeginSound(0x12, 0, 0x7e);
                break;
            }
        }
        dir = GetDir(x, y, tx, ty);
        x += Dx9[dir];
        y += Dy9[dir];
    } while (dir != 0);
}

extern uint8_t  BlistT[];
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];

void  ClearLifeB(int16_t x, int16_t y)
{
    int16_t i;

    i = native_state_ListIndexB.signed_value;
    while (i) {
        --i;
        if (BlistT[i] != 0 && BlistX[i] == x && BlistY[i] == y)
            BlistT[i] = 0;
    }
    LifeB[x][y] = 0;
}

extern uint8_t  RlistT[];
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];

void  ClearLifeR(int16_t x, int16_t y)
{
    int16_t i;

    i = native_state_ListIndexR.signed_value;
    while (i) {
        --i;
        if (RlistT[i] != 0 && RlistX[i] == x && RlistY[i] == y)
            RlistT[i] = 0;
    }
    LifeR[x][y] = 0;
}

extern int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y);
extern void  AddAntToAList(int16_t x, int16_t y, int16_t type, int16_t a, int16_t b);
extern uint8_t  MapB[64][64];
extern void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t a, int16_t b);
extern uint8_t  MapR[64][64];
extern void  AddAntToRList(int16_t x, int16_t y, int16_t type, int16_t a, int16_t b);

void  ExpAddAnt(int16_t x, int16_t y)
{
    int16_t amt;

    amt = SRand1(8) + 16;
    if (ExpSubStates[3] == 1)
        amt += 0x80;

    switch (native_state_MapPlane.signed_value) {
    case 1:
        if (IsClearTile(1, x, y))
            AddAntToAList(x, y, amt, 2, 0);
        else
            return;
        break;
    case 2:
        if (y == 0)
            return;
        if (MapB[x][y] >= 0x1c)
            DigTileB(x, y);
        if (amt > 0x80)
            AddAntToBList(x, y, amt, 7, 0);
        else
            AddAntToBList(x, y, amt, 2, 0);
        break;
    case 3:
        if (y == 0)
            return;
        if (MapR[x][y] >= 0x1c)
            DigTileR(x, y);
        if (amt > 0x80)
            AddAntToRList(x, y, amt, 2, 0);
        else
            AddAntToRList(x, y, amt, 7, 0);
        break;
    }

    myBeginSound(0x1c, 0, 0x7e);
}

int16_t  IncFoodHere(int16_t x, int16_t y);

void  ExpAddFood(int16_t x, int16_t y)
{
    int16_t i;
    int16_t fx;
    int16_t fy;

    if (ExpSubStates[4] == 0) {
        if (IncFoodHere(x, y))
            myBeginSound(0x1d, 0, 0x7e);
    } else {
        myBeginSound(0x20, 0, 0x7e);
        for (i = 0; i < 20; i++) {
            fx = SRand1(9) + x - 4;
            fy = SRand1(9) + y - 4;
            if (IsValidLocation(native_state_MapPlane.signed_value, fx, fy))
                IncFoodHere(fx, fy);
        }
    }
}

int16_t  GetSM(int16_t x, int16_t y);
void  SetSM(int16_t x, int16_t y, int16_t val);
void  SmoothMany(int16_t x, int16_t y);

void  ExpIncSmell(int16_t x, int16_t y)
{
    int16_t sx;
    int16_t sy;
    int16_t v;

    if (native_state_MapPlane.signed_value == 1) {
        sx = x >> 1;
        sy = y >> 1;
        v = GetSM(sx, sy);
        if (dos_keyboard_modifiers() & 8)
            v -= 40;
        else
            v += 70;
        if (v < 0)
            v = 0;
        if (v > 255)
            v = 255;
        SetSM(sx, sy, v);
        SmoothMany(sx, sy);
        myBeginSound(0x1b, 0, 0x7e);
    }
}

extern int16_t  FindInAList(int16_t x, int16_t y);
extern int16_t  Tindex;
extern uint8_t  AlistT[];
extern void  DeadAntHere(int16_t x, int16_t y, int16_t type);
extern void  KillSpider(void);
extern int16_t  FindInLionList(int16_t x, int16_t y);
extern void  KillAntLion(int16_t index);
extern int16_t  FindInBList(int16_t x, int16_t y, int16_t life);
extern int16_t  FindInRList(int16_t x, int16_t y, int16_t life);

void  ExpKillAnts(int16_t x, int16_t y)
{
    int16_t n;
    int16_t i;
    int16_t kx;
    int16_t ky;
    int16_t v;

    n = ExpSubStates[6] == 0 ? 8 : 1;
    for (i = 0; i < 8; i++) {
        if (n == 1) {
            kx = x;
            ky = y;
            myBeginSound(9, 0, 0x7e);
        } else {
            kx = SRand1(9) + x - 4;
            ky = SRand1(9) + y - 4;
            myBeginSound(9, SRand1(1000) + 0x278f, 0x7e);
        }
        if (IsValidLocation(native_state_MapPlane.signed_value, kx, ky)) {
            switch (native_state_MapPlane.signed_value) {
            case 1:
                if (LifeA[kx][ky]) {
                    Tindex = FindInAList(kx, ky);
                    if (Tindex >= 0) {
                        DeadAntHere(kx, ky, AlistT[Tindex] & 0x80);
                        AlistT[Tindex] = 0;
                        LifeA[kx][ky] = 0;
                    }
                }
                if ((native_state_fd_50F6_0F12.signed_value >> 4) == kx && (native_state_fd_50F6_0F34.signed_value >> 4) == ky)
                    KillSpider();
                v = MapA[kx][ky];
                if (v >= 0x38 && v <= 0x3e)
                    KillAntLion(FindInLionList(kx, ky));
                break;
            case 2:
                v = LifeB[kx][ky];
                if (v) {
                    Tindex = FindInBList(kx, ky, v);
                    if (Tindex >= 0) {
                        BlistT[Tindex] = 0;
                        LifeB[kx][ky] = 0;
                    }
                }
                break;
            case 3:
                v = LifeR[kx][ky];
                if (v) {
                    Tindex = FindInRList(kx, ky, v);
                    if (Tindex >= 0) {
                        RlistT[Tindex] = 0;
                        LifeR[kx][ky] = 0;
                    }
                }
                break;
            }
        }
    }
}

extern int16_t  GetMap(int16_t plane, int16_t x, int16_t y);
extern void  SetMap(int16_t plane, int16_t x, int16_t y, int16_t value);

void  ConnectWall(int16_t x, int16_t y);
int16_t  IsItWall(int16_t value);

int16_t  IncFoodHere(int16_t x, int16_t y)
{
    int16_t base;
    int16_t v;

    if (native_state_MapPlane.signed_value == 1)
        base = 0x48;
    else
        base = 0x10;
    v = GetMap(native_state_MapPlane.signed_value, x, y);
    if (dos_keyboard_modifiers() & 8) {
        if (base > v)
            return 0;
        if (base + 3 < v)
            return 0;
        v = SRand1(8);
        if (native_state_MapPlane.signed_value == 1)
            if (native_state_fd_50F6_1040.signed_value > 0)
                native_state_fd_50F6_1040.signed_value--;
        else if (native_state_MapPlane.signed_value == 2)
            if (native_state_FoodB.signed_value > 0)
                native_state_FoodB.signed_value--;
        else
            if (native_state_FoodR.signed_value > 0)
                native_state_FoodR.signed_value--;
    } else {
        if (base + 2 < v)
            return 0;
        if (base > v) {
            if (v < 0x18)
                v = base;
        } else v++;
        if (native_state_MapPlane.signed_value == 1)
            native_state_fd_50F6_1040.signed_value++;
        else if (native_state_MapPlane.signed_value == 2)
            native_state_FoodB.signed_value++;
        else
            native_state_FoodR.signed_value++;
    }
    SetMap(native_state_MapPlane.signed_value, x, y, v);
    return 1;
}


void  ConnectAll(int16_t x, int16_t y)
{
    ConnectWall(x, y);
    if (IsValidA(x, y - 1) == 1)
        ConnectWall(x, y - 1);
    if (IsValidA(x + 1, y) == 1)
        ConnectWall(x + 1, y);
    if (IsValidA(x, y + 1) == 1)
        ConnectWall(x, y + 1);
    if (IsValidA(x - 1, y) == 1)
        ConnectWall(x - 1, y);
}

int16_t  WallNeighbors(int16_t x, int16_t y, int16_t plane);

static uint8_t wallShape[16] = {
    0x60, 0x64, 0x65, 0x66, 0x62, 0x61, 0x62, 0x61,
    0x63, 0x63, 0x60, 0x60, 0x67, 0x67, 0x67, 0x67
};

void  ConnectWall(int16_t x, int16_t y)
{
    if (IsItWall(MapA[x][y]))
        MapA[x][y] = wallShape[WallNeighbors(x, y, 1)];
}

int16_t  WallNeighbors(int16_t x, int16_t y, int16_t plane)
{
    int16_t n;

    n = 0;
    if (IsItWall(GetMap(plane, x - 1, y)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x, y + 1)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x + 1, y)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x, y - 1)) == 1)
        n++;
    return n;
}

int16_t  IsItWall(int16_t value)
{
    return value >= 0x60 && value <= 0x67;
}

extern void  SmoothEdgesB(int16_t x, int16_t y);
extern uint8_t  ExitMapB[64][64];

void  FillDirtB(int16_t x, int16_t y)
{
    MapB[x][y] = '.';
    LifeB[x][y] = 0;

    if (native_state_fd_50F6_0224.signed_value > 1) {
        native_state_fd_50F6_1068.signed_value -= x;
        if (native_state_fd_50F6_1068.signed_value < 0)
            native_state_fd_50F6_1068.signed_value = 0;
        native_state_fd_50F6_1082.signed_value -= y;
        if (native_state_fd_50F6_1082.signed_value < 0)
            native_state_fd_50F6_1082.signed_value = 0;
        --native_state_fd_50F6_0224.signed_value;
    }

    SmoothEdgesB(x, y - 1);
    SmoothEdgesB(x + 1, y);
    SmoothEdgesB(x, y + 1);
    SmoothEdgesB(x - 1, y);

    ExitMapB[x][y] = 0;
}

extern void  SmoothEdgesR(int16_t x, int16_t y);
extern uint8_t  ExitMapR[64][64];

void  FillDirtR(int16_t x, int16_t y)
{
    MapR[x][y] = '.';
    LifeR[x][y] = 0;

    if (native_state_TilesDugR.signed_value > 1) {
        native_state_fd_50F6_108E.signed_value -= x;
        if (native_state_fd_50F6_108E.signed_value < 0)
            native_state_fd_50F6_108E.signed_value = 0;
        native_state_fd_50F6_10A2.signed_value -= y;
        if (native_state_fd_50F6_10A2.signed_value < 0)
            native_state_fd_50F6_10A2.signed_value = 0;
        --native_state_TilesDugR.signed_value;
    }

    SmoothEdgesR(x, y - 1);
    SmoothEdgesR(x + 1, y);
    SmoothEdgesR(x, y + 1);
    SmoothEdgesR(x - 1, y);

    ExitMapR[x][y] = 0;
}

void  SmoothACell(int16_t x, int16_t y);

void  SmoothMany(int16_t x, int16_t y)
{
    SmoothACell(x, y);
    SmoothACell(x, y - 1);
    SmoothACell(x + 1, y);
    SmoothACell(x, y + 1);
    SmoothACell(x - 1, y);
    SmoothACell(x, y);
}

void  SmoothACell(int16_t x, int16_t y)
{
    int16_t v;

    v = GetSM(x, y - 1);
    v += GetSM(x + 1, y);
    v += GetSM(x, y + 1);
    v += GetSM(x - 1, y);
    v = (v / 4 + GetSM(x, y)) / 2;
    SetSM(x, y, v);
}

int16_t  IsValidSLoc(int16_t x, int16_t y)
{
    if (x >= 0 && x <= 63 && y >= 0 && y <= 31)
        return 1;
    return 0;
}

extern uint8_t  PherMapBN[64][32];
extern uint8_t  PherMapBT[64][32];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapRT[64][32];
extern uint8_t  PherMapA[64][32];

int16_t  GetSM(int16_t x, int16_t y)
{
    int16_t v;

    if (!IsValidSLoc(x, y))
        return -1;
    switch (ExpSubStates[5]) {
    case 0:
        v = PherMapBN[x][y];
        break;
    case 1:
        v = PherMapBT[x][y];
        break;
    case 2:
        v = PherMapRN[x][y];
        break;
    case 3:
        v = PherMapRT[x][y];
        break;
    case 4:
        v = PherMapA[x][y];
        break;
    }
    return v;
}

void  SetSM(int16_t x, int16_t y, int16_t val)
{
    if (IsValidSLoc(x, y)) {
        if (val > 255)
            val = 255;
        switch (ExpSubStates[5]) {
        case 0:
            PherMapBN[x][y] = val;
            break;
        case 1:
            PherMapBT[x][y] = val;
            break;
        case 2:
            PherMapRN[x][y] = val;
            break;
        case 3:
            PherMapRT[x][y] = val;
            break;
        case 4:
            PherMapA[x][y] = val;
            break;
        }
    }
}

#pragma pack(pop)
