#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S25, code frame 3BA4: yellow ant movement (DoAntMoveY unit).
 * Built /AL /Os /Oe /Og /Zi.  The order of the extern declarations is part of the
 * fingerprint: MSC 6.00A breaks some operand-order ties by symbol-table state
 * (ExitNest's MePlane/MeGoalPlane compare, GetMyDis' GetDis call order), and this
 * order (0D6C/0EF8 first, MeLastX/Y before MeGoalY, entrance arrays A4,B0,A8,AC)
 * reproduces them. */

extern int16_t  GetAntIndex(int16_t list, int16_t index, int16_t  *x, int16_t  *y,
                           int16_t  *attr, int16_t  *state, int16_t  *dir);
extern int16_t  MePlane;
extern int16_t  MeLocX;
extern int16_t  ABS(int16_t value);
extern int16_t  MeLocY;
extern int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  fd_50F6_0496;
extern void  DoEditUpdateDraw(void);
extern int8_t  Dx9[];
extern int8_t  Dy9[];
extern int16_t  TryMyDropOrLift(int16_t plane, int16_t x, int16_t y);
int16_t  o25_3BA4_1A9F(int16_t plane, int16_t x, int16_t y, int16_t gplane, int16_t gx, int16_t gy);
extern int8_t  Dy8[];
extern int16_t  fd_50F6_04C2;
extern int8_t  Dx8[];
extern void  MoveMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern void  JamScentBT(int16_t, int16_t, int16_t);
extern void  JamScentRT(int16_t, int16_t, int16_t);
extern void  AlarmHere(int16_t, int16_t, int16_t);
extern void  f_14EE_0C9C(int16_t x, int16_t y);
extern void  f_14EE_0D71(int16_t x, int16_t y);
extern int16_t  fd_3D57_0C24;
extern int16_t  fd_3D57_0C18;
extern void  SetMyHealth(int16_t health);
extern int16_t  IsItHole(int16_t, int16_t);
extern void  DoEditAndMapUpdateDraw(void);
void  o25_3BA4_1035(void);
extern int16_t  fd_3D57_07A8[];
extern void  GotoMyAnt(void);
void  ExitNest(void);
extern int16_t  GetMap(int16_t plane, int16_t x, int16_t y);
extern void  ClearMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t code);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  *  *  fd_50F6_034C;
extern void  EditMessage(void  *, int32_t, int16_t);
void  o25_3BA4_0DFB(int16_t list, int16_t index);
extern void  SetAntIndex(int16_t list, int16_t index, int16_t x, int16_t y,
                            int16_t attr, int16_t state, int16_t dir);
extern void  SetLife(int16_t plane, int16_t x, int16_t y, int16_t value);
extern void  EatMyFood(int16_t kind);
extern void  ResetYellowVars(int16_t plane, int16_t x, int16_t y);
extern int16_t  TERRAINset;
extern uint8_t  MapA[128][64];
extern void  YellowDeath(int16_t code);

/* DoAntMoveY: exact body and relocation evidence. The folded unsigned
 * attribute range check is STEERED: it reproduces the stack-slot use ranking,
 * but the eliminated expression in the original source is unknown. */
void  DoAntMoveY(void)
{
    int16_t dir;
    int16_t x;
    int16_t result;
    int16_t ty;
    int16_t tattr;
    int16_t tx;
    int16_t tdir;
    int16_t tstate;
    int16_t y;
    int16_t d;
    int16_t dx;
    int16_t dy;
    int16_t tile;

    if (native_state_fd_50F6_0AA0.signed_value == 0)
        return;
    result = 0;
    if (native_state_fd_50F6_0A8E.signed_value >= 3) {
        if (GetAntIndex(native_state_fd_50F6_08DA.signed_value, native_state_fd_50F6_07C0.signed_value, &tx, &ty, &tattr, &tstate, &tdir) == 0
            || (((uint16_t)tattr >= 0) && ((native_state_fd_50F6_084E.signed_value ^ tattr) & 0xf0) != 0)) {
            result = -2;
            goto done;
        }
        if (MePlane == native_state_fd_50F6_08DA.signed_value) {
            dx = ABS(MeLocX - tx);
            dy = ABS(MeLocY - ty);
            if (dx <= 1 && dy <= 1) {
                d = GetDir(MeLocX, MeLocY, tx, ty) - 1;
                if (d >= 0)
                    fd_50F6_0496 = d;
                DoEditUpdateDraw();
                goto moved;
            }
        }
        native_state_fd_50F6_0AD6.signed_value = native_state_fd_50F6_08E2.signed_value = tx;
        native_state_fd_50F6_0AE8.signed_value = native_state_fd_50F6_09F0.signed_value = ty;
    }
    if (native_state_fd_50F6_0A8E.signed_value == 1 && native_state_fd_50F6_0AF8.signed_value == MePlane) {
        dir = GetDir(MeLocX, MeLocY, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value);
        x = Dx9[dir] + MeLocX;
        y = Dy9[dir] + MeLocY;
        if (x < 0 || x > 0x7f)
            x = MeLocX;
        if (y < 0 || y > 0x3f)
            y = MeLocY;
        if (native_state_fd_50F6_0AD6.signed_value == x && native_state_fd_50F6_0AE8.signed_value == y) {
            if ((result = TryMyDropOrLift(MePlane, x, y)) != 0) {
                result = (result == 1) ? -1 : -2;
                goto done;
            }
        }
    }
    d = o25_3BA4_1A9F(MePlane, MeLocX, MeLocY,
                      native_state_fd_50F6_0AF8.signed_value, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value);
    if (d < 0) {
        result = d;
        goto done;
    }
    x = Dx8[d] + MeLocX;
    y = Dy8[d] + MeLocY;
    native_state_fd_50F6_0AB6.signed_value = MeLocX;
    native_state_fd_50F6_0AC6.signed_value = MeLocY;
    MoveMyLife(MePlane, x, y, fd_50F6_04C2, d);
    native_state_fd_50F6_0C3E.signed_value++;
    if (MePlane == 1) {
        if (native_state_fd_50F6_04C4.signed_value > 0 && (fd_50F6_04C2 == 0x18 || fd_50F6_04C2 == 0x38)) {
            if (native_state_fd_50F6_04E2.signed_value == 0)
                JamScentBT(MeLocX, MeLocY, native_state_fd_50F6_04C4.signed_value);
            else
                JamScentRT(MeLocX, MeLocY, native_state_fd_50F6_04C4.signed_value);
            if (native_state_fd_50F6_04C4.signed_value > 10)
                native_state_fd_50F6_04C4.signed_value--;
        }
        if (native_state_fd_50F6_104E.signed_value != 0)
            AlarmHere(MeLocX, MeLocY, 50);
    } else if (MePlane == 2)
        f_14EE_0C9C(MeLocX, MeLocY);
    else
        f_14EE_0D71(MeLocX, MeLocY);
    if (native_state_fd_50F6_0C3E.signed_value & 1) {
        if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0 && native_state_HealthB.signed_value > 0 && fd_3D57_0C18 == 0)
            native_state_HealthB.signed_value--;
        SetMyHealth(native_state_MeHealth.signed_value - 1);
    }
    if (MePlane == 1) {
        if (IsItHole(MeLocX, MeLocY) == 0)
            goto done;
        if (native_state_fd_50F6_0AF8.signed_value > 1 || (native_state_fd_50F6_0AF8.signed_value == MePlane && native_state_fd_50F6_0AD6.signed_value == MeLocX
                                 && native_state_fd_50F6_0AE8.signed_value == MeLocY)) {
            DoEditAndMapUpdateDraw();
            d = MePlane;
            o25_3BA4_1035();
            if (native_state_fd_50F6_0AF8.signed_value != d || native_state_fd_50F6_0AD6.signed_value != x || native_state_fd_50F6_0AE8.signed_value != y
                || MePlane == native_state_MapPlane.signed_value)
                goto done;
            if (fd_3D57_07A8[0] == 0)
                GotoMyAnt();
            goto moved;
        }
        goto done;
    }
    if (MeLocY == 0) {
        DoEditAndMapUpdateDraw();
        d = MePlane;
        ExitNest();
        if (native_state_fd_50F6_0AF8.signed_value != d || native_state_fd_50F6_0AD6.signed_value != x || native_state_fd_50F6_0AE8.signed_value != y
            || MePlane == native_state_MapPlane.signed_value)
            goto done;
        if (fd_3D57_07A8[0] == 0)
            GotoMyAnt();
        goto moved;
    }
    if (GetMap(MePlane, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value) != 0x14)
        goto done;
    if (fd_50F6_04C2 == 0x60 || native_state_fd_50F6_0AD6.signed_value != MeLocX || native_state_fd_50F6_0AE8.signed_value != MeLocY)
        goto done;
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    if (MePlane == 2)
        MePlane = 3;
    else
        MePlane = 2;
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
    myBeginSound(1, 0, 0x7e);
    GotoMyAnt();
    if (MePlane == 3)
        EditMessage(fd_50F6_034C[4], 360L, 0);
moved:
    result = -1;
done:
    if (fd_3D57_07A8[0] != 0)
        GotoMyAnt();
    if (result == 0 && native_state_fd_50F6_0AF8.signed_value == MePlane && native_state_fd_50F6_0AD6.signed_value == MeLocX
        && native_state_fd_50F6_0AE8.signed_value == MeLocY && native_state_fd_50F6_0A8E.signed_value == 0)
        result = -1;
    if (result == 0)
        return;
    if (result == -2) {
        myBeginSound(1, 0, 0x7e);
        GotoMyAnt();
    } else if (native_state_fd_50F6_0A8E.signed_value == 3) {
        native_state_fd_50F6_1058.signed_value = 1;
        o25_3BA4_0DFB(native_state_fd_50F6_08DA.signed_value, native_state_fd_50F6_07C0.signed_value);
        native_state_fd_50F6_1058.signed_value = 0;
    } else if (native_state_fd_50F6_0A8E.signed_value == 4) {
        d = GetDir(tx, ty, MeLocX, MeLocY) - 1;
        if (d >= 0 && (tattr & 0x70) != 0x60) {
            tattr = (tattr & 0xf8) | d;
            SetAntIndex(MePlane, native_state_fd_50F6_07C0.signed_value, tx, ty, tattr, tstate, tdir);
            SetLife(MePlane, tx, ty, tattr);
            DoEditUpdateDraw();
        }
        EatMyFood(1);
    }
    ResetYellowVars(MePlane, MeLocX, MeLocY);
    if (TERRAINset != 0 && MePlane == 1) {
        tile = MapA[MeLocX][MeLocY];
        if (tile == 0x76 || tile == 0x78)
            YellowDeath(10);
    }
}

extern int16_t  fd_50F6_0A06;
extern int16_t  InNestBounds(int16_t x, int16_t y);
extern int16_t  SRand128(void);
extern void  PlaceEggB(int16_t x, int16_t y, int16_t type);
extern void  o25_39C7_15B4(void);
extern void  PlaceEggR(int16_t x, int16_t y, int16_t type);
extern void  DecEatR(void);

void  DoAntSimY(void)
{
    int16_t newy, newx;
    int16_t mapval;
    int16_t bx;

    if (fd_50F6_0A06 != 0)
        return;

    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);

    if (!(native_state_Cycle.raw_bytes[0] & 0x3f))
        SetMyHealth(native_state_MeHealth.signed_value - 1);

    if (MePlane >= 2) {
        mapval = GetMap(MePlane, MeLocX, MeLocY);
        if (mapval >= 0x4e)
            SetMyHealth(native_state_MeHealth.signed_value - 1);
    }

    if (fd_50F6_04C2 == 0x60 && MePlane > 1 && !(native_state_Cycle.raw_bytes[0] & 0xf)) {
        bx = fd_50F6_0496 ^ 4;
        newx = MeLocX + 2 * Dx8[bx];
        newy = MeLocY + 2 * Dy8[bx];
        if (InNestBounds(newx, newy)) {
            if (SRand128() <= native_state_MeHealth.signed_value) {
                if (native_state_fd_50F6_04E2.signed_value == 0) {
                    PlaceEggB(newx, newy, 1);
                    o25_39C7_15B4();
                } else {
                    PlaceEggR(newx, newy, 1);
                    DecEatR();
                }
                SetMyHealth(native_state_MeHealth.signed_value - 5);
            }
        }
    }

    if (native_state_MeHealth.signed_value <= 0) {
        if (++native_state_fd_50F6_1006.signed_value >= 100) {
            if (MePlane >= 2 && mapval >= 0x4e)
                YellowDeath(7);
            else
                YellowDeath(8);
        }
    }
}

extern int16_t  win_IsWinInFront(int16_t v);
extern int32_t  MacTickCount(void);
extern void  myDelay(int32_t);
extern void  f_00DF_015C(void);
extern int16_t  SRand2(void);
extern int16_t  mySongIsDone(void);
extern void  SetMap(int16_t plane, int16_t x, int16_t y, int16_t value);
extern int16_t  SRand8(void);

void  o25_3BA4_0999(int16_t plane, int16_t x, int16_t y, int16_t dir, int16_t type, int16_t kind)
{
    int32_t t;
    int16_t count;
    int16_t tile;
    int16_t i;
    int16_t n;
    int16_t svY;
    int16_t svType;
    int16_t svDir;
    int16_t svPlane;
    int16_t svX;

    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = fd_50F6_04C2;
    svDir = dir;
    if (kind == 0)
        count = 6;
    else if (win_IsWinInFront(0))
        count = fd_3D57_07A8[1] ? 0x40 : 0x20;
    else
        count = 8;
    if (kind == 10) {
        tile = MapA[x][y];
        count = 0x20;
    }
    if (kind == 2)
        n = 3;
    t = MacTickCount();
    for (i = 0; i < count; i++) {
        while (MacTickCount() <= t)
            myDelay(1L);
        t = MacTickCount() + 6;
        f_00DF_015C();
        if (kind == 0 && SRand2())
            myBeginSound(0x25, 0x32c8, 0x7e);
        if (kind == 10) {
            myBeginSound(0x31, 0x55f0, 0x7f);
            MapA[x][y] = SRand2() ? tile - 3 : tile;
        }
        if (kind != 0 && kind < 10 && fd_3D57_07A8[1] != 0 && mySongIsDone())
            break;
        if (kind == 2) {
            SetMap(plane, x, y, n + 0x38);
            if (n < 5)
                n++;
            else if (n > 3)
                n--;
        }
        MoveMyLife(plane, x, y, type, SRand8());
        DoEditUpdateDraw();
    }
    if (kind == 10)
        MapA[x][y] = tile;
    ClearMyLife(plane, x, y, type, fd_50F6_0496);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
    fd_50F6_04C2 = svType;
    fd_50F6_0496 = svDir;
}

extern int16_t  WinPrintf(char  *format, ...);
extern int32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  RRand(int16_t range);
extern int16_t  o25_39C7_0CBD(int16_t plane, int16_t x, int16_t y, int16_t gx, int16_t gy);

void  o25_3BA4_0C01(int16_t plane, int16_t x, int16_t y, int16_t dir, int16_t type)
{
    int32_t t;
    int16_t d;
    int16_t i;
    int16_t count;
    int16_t svY;
    int16_t svX;
    int16_t svType;
    int16_t svDir;
    int16_t svPlane;

    WinPrintf("AnimYellowInsane");
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = fd_50F6_04C2;
    svDir = dir;
    count = win_IsWinInFront(0) ? 0x20 : 8;
    t = MacTickCount();
    for (i = 0; i < count; i++) {
        while (MacTickCount() <= t)
            myDelay(1L);
        t = MacTickCount() + 3;
        f_00DF_015C();
        if ((int16_t)GetDis(x, y, svX, svY) == 0 && count - i - 1 != 0)
            d = o25_39C7_0CBD(plane, x, y, RRand(7) + x - 3, RRand(7) + y - 3);
        else
            d = o25_39C7_0CBD(plane, x, y, svX, svY);
        if (d >= 0) {
            x += Dx8[d];
            y += Dy8[d];
        } else
            d = SRand8();
        MoveMyLife(plane, x, y, type, d);
        WinPrintf("2");
        DoEditUpdateDraw();
    }
    ClearMyLife(plane, x, y, type, fd_50F6_0496);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
    fd_50F6_04C2 = svType;
    fd_50F6_0496 = svDir;
    WinPrintf("3");
}

extern uint8_t  AlistX[];
extern uint8_t  AlistY[];
extern uint8_t  AlistT[];
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];
extern uint8_t  BlistT[];
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];
extern uint8_t  RlistT[];
extern void  ClearLife(int16_t plane, int16_t x, int16_t y, int16_t value);
extern int16_t  GetWinner(int16_t a, int16_t b);
extern void  DeadAntHere(int16_t x, int16_t y, int16_t type);

void  o25_3BA4_0DFB(int16_t list, int16_t index)
{
    int16_t type;
    uint8_t  *pl;
    uint8_t  *px;
    uint8_t  *py;

    if (list <= 1) {
        px = AlistX;
        py = AlistY;
        pl = AlistT;
    } else if (list == 2) {
        px = BlistX;
        py = BlistY;
        pl = BlistT;
    } else {
        px = RlistX;
        py = RlistY;
        pl = RlistT;
    }
    ClearLife(list, px[index], py[index], pl[index]);
    type = GetWinner(fd_50F6_04C2, pl[index]);
    if (fd_50F6_04C2 != type)
        GotoMyAnt();
    o25_3BA4_0999(MePlane, MeLocX, MeLocY, fd_50F6_0496, 0x70, 0);
    if (fd_50F6_04C2 == type) {
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
        if (list <= 1)
            DeadAntHere(px[index], py[index], pl[index] & 0x80);
        pl[index] = 0;
        if (native_state_fd_50F6_0A8E.signed_value == 3 && MePlane == native_state_fd_50F6_08DA.signed_value && native_state_fd_50F6_07C0.signed_value == index)
            ResetYellowVars(MePlane, MeLocX, MeLocY);
    } else {
        SetLife(list, px[index], py[index], pl[index]);
        if (list <= 1)
            DeadAntHere(MeLocX, MeLocY, native_state_fd_50F6_04E2.signed_value);
        YellowDeath(0);
    }
}

extern void  TryAntTheme(void);
extern void  SetAlarmDropState(int16_t state, int16_t quiet);
extern void  DigMyTile(int16_t plane, int16_t x, int16_t y);
extern uint8_t  HoleMapB[];
extern void  MakeNewHoleB(int16_t x);
extern uint8_t  HoleMapR[];
extern void  MakeNewHoleR(int16_t x);
extern int8_t  fd_3D57_006C[];
extern int16_t  IsNotObstacle(int16_t plane, int16_t x, int16_t y);

/* SCAFFOLD BEGIN: o25_3BA4_1035 (EnterNest) best draft: 3 bytes differ, the merged DigMyTile call loads &MeLocX via bx instead of si (register tie-break); the if/else with identical arms reproduces the dead "les bx,[bp-14h]" of the original */
void  o25_3BA4_1035(void)
{
    TryAntTheme();
    if (native_state_fd_50F6_104E.signed_value != 0)
        SetAlarmDropState(0, 1);
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    if (MeLocX > 0x40)
        MePlane = 3;
    else
        MePlane = 2;
    MeLocX = MeLocY;
    if (fd_50F6_04C2 == 0x60)
        MeLocY = 2;
    else
        MeLocY = 1;
    fd_50F6_0496 = 4;
    if (MePlane == 2)
        DigMyTile(MePlane, MeLocX, MeLocY);
    else
        DigMyTile(MePlane, MeLocX, MeLocY);
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
}
/* SCAFFOLD END */

void  ExitNest(void)
{
    int16_t step;
    int16_t nx;
    int16_t ny;
    int16_t dir;
    int16_t i;
    int16_t d;

    TryAntTheme();
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0);
    MeLocY = MeLocX & 0x3f;
    if (MePlane == 2) {
        if (HoleMapB[MeLocY] == 0)
            MakeNewHoleB(MeLocX);
        MeLocX = HoleMapB[MeLocY];
    } else {
        if (HoleMapR[MeLocY] == 0)
            MakeNewHoleR(MeLocX);
        MeLocX = HoleMapR[MeLocY];
    }
    step = (fd_50F6_04C2 == 0x60) ? 2 : 1;
    if (native_state_fd_50F6_0AF8.signed_value == 1) {
        d = GetDir(MeLocX, MeLocY, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value);
        if (d > 0)
            d--;
    } else if (MePlane == native_state_fd_50F6_0AF8.signed_value) {
        if (MeLocX < 0x40)
            d = 2;
        else
            d = 6;
    } else {
        d = o25_3BA4_1A9F(1, MeLocX, MeLocY, native_state_fd_50F6_0AF8.signed_value, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value);
        if (d < 0)
            d = SRand8();
    }
    i = 0;
    dir = d;
    for (; i < 8; i++) {
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = Dx8[d] * step + MeLocX;
        ny = Dy8[d] * step + MeLocY;
        if (IsNotObstacle(1, nx, ny)) {
            MeLocX = nx;
            MeLocY = ny;
            fd_50F6_0496 = d;
            break;
        }
    }
    if (i == 8) {
        fd_50F6_0496 = dir;
        MeLocX = (MeLocX + step) & 0x7f;
    }
    SetMyLife(MePlane = 1, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
}

extern int16_t  fd_3D57_02A4[2];
extern int16_t  fd_3D57_02B0[2];
extern int16_t  fd_3D57_02A8[2];
extern int16_t  fd_3D57_02AC[2];

int16_t  o25_3BA4_13AB(int16_t p1, int16_t x1, int16_t y1, int16_t p2, int16_t x2, int16_t y2)
{
    if (p2 == p1)
        return GetDis(x1, y1, x2, y2);
    if (p1 == 1 && p2 > p1) {
        if (p2 == 2)
            return GetDis(x1, y1, fd_3D57_02AC[0], fd_3D57_02AC[1])
                 + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
        return GetDis(x1, y1, fd_3D57_02B0[0], fd_3D57_02B0[1])
             + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
    }
    if (p2 == 1) {
        if (p1 == 2)
            return GetDis(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
                 + GetDis(fd_3D57_02AC[0], fd_3D57_02AC[1], x2, y2);
        return GetDis(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
             + GetDis(fd_3D57_02B0[0], fd_3D57_02B0[1], x2, y2);
    }
    if (p1 == 2)
        return GetDis(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
             + GetDis(fd_3D57_02AC[0], fd_3D57_02AC[1], fd_3D57_02B0[0], fd_3D57_02B0[1])
             + GetDis(fd_3D57_02A8[0], fd_3D57_02A8[1], x2, y2);
    return GetDis(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
         + GetDis(fd_3D57_02B0[0], fd_3D57_02B0[1], fd_3D57_02AC[0], fd_3D57_02AC[1])
         + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
}

extern int16_t  TileCanBeMovedOn(int16_t plane, int16_t x, int16_t y, int16_t fromPlane, int16_t fromX, int16_t fromY, int16_t digging);
extern int16_t  GetLife(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y);

int16_t  o25_3BA4_1581(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t best;
    int16_t fallback;
    int16_t flag;
    int16_t threshold;
    int16_t dir;
    int16_t nx;
    int16_t ny;
    int16_t dis;

    best = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold > 0) {
        fallback = -2;
        flag = (native_state_fd_50F6_0A8E.signed_value == 2) ? 1 : 0;
        for (dir = 0; dir < 8; dir++) {
            nx = Dx8[dir] + x;
            ny = Dy8[dir] + y;
            if (TileCanBeMovedOn(plane, nx, ny, native_state_fd_50F6_0AF8.signed_value, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value, flag) != 0) {
                dis = GetDis(nx, ny, a, b);
                if (dis < threshold) {
                    if (GetLife(plane, nx, ny) > 0 || IsClearTile(plane, nx, ny) == 0)
                        fallback = dir;
                    else
                        best = dir;
                    threshold = dis;
                }
            }
        }
        if (best < 0)
            best = fallback;
    }
    return best;
}

/* SCAFFOLD BEGIN: o25_3BA4_1686 (GetMyRandDirs) best draft, 0.93 similar: SI/DI roles of right/left and the web of best (DI at entry/exit, [bp-8] inside) differ */
int16_t  o25_3BA4_1686(int16_t  *rot, int16_t  *dir, int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t flag;
    int16_t d;
    int16_t left;
    int16_t best;
    int16_t threshold;
    char ok[8];
    int16_t i;
    int16_t right;
    int16_t nx;
    int16_t ny;
    int16_t dis;

    best = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold > 0) {
        best = -2;
        flag = (native_state_fd_50F6_0A8E.signed_value == 2) ? 1 : 0;
        for (i = 0; i < 8; i++) {
            nx = Dx8[i] + x;
            ny = Dy8[i] + y;
            if ((nx != native_state_fd_50F6_0AB6.signed_value || ny != native_state_fd_50F6_0AC6.signed_value)
                && TileCanBeMovedOn(plane, nx, ny, native_state_fd_50F6_0AF8.signed_value, native_state_fd_50F6_0AD6.signed_value, native_state_fd_50F6_0AE8.signed_value, flag)) {
                best = i;
                ok[i] = 1;
            } else
                ok[i] = 0;
        }
        if (best < 0)
            return best;
        best = -1;
        right = left = *dir;
        if (*rot == 0) {
            for (i = 0; i < 8; i++) {
                if (ok[right]) {
                    best = right;
                    *dir = GetDir(x, y, a, b) - 1;
                    *rot = 1;
                    break;
                }
                if (ok[left]) {
                    best = left;
                    *dir = GetDir(x, y, a, b) - 1;
                    *rot = -1;
                    break;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        } else {
            for (i = 0; i < 8; i++) {
                if (*rot > 0) {
                    if (ok[right]) {
                        d = right;
                        goto found;
                    }
                } else if (ok[left]) {
                    right = left;
                    goto found;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        }
    }
    return best;
found:
    dis = GetDis(Dx8[right] + x, Dy8[right] + y, a, b);
    if (dis <= threshold) {
        *dir = GetDir(x, y, a, b) - 1;
        *rot = 0;
    }
    return right;
}
/* SCAFFOLD END */

int16_t  o25_3BA4_188A(int16_t  *steps, int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t nx;
    int16_t ny;
    int16_t count;
    int16_t dir;

    count = 0;
    dir = o25_3BA4_1581(plane, x, y, a, b);
    if (dir >= 0) {
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        while (dir >= 0 && count < 0x40) {
            dir = o25_3BA4_1581(plane, nx, ny, a, b);
            if (dir >= 0) {
                nx += Dx8[dir];
                ny += Dy8[dir];
            }
            count++;
        }
    }
    *steps = count;
    if (dir >= 0)
        dir = -1;
    return dir;
}


int16_t  o25_3BA4_1935(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t dir;
    int16_t steps;

    if (o25_3BA4_188A(&steps, plane, x, y, a, b) == -2)
        dir = o25_3BA4_1686(&native_state_fd_50F6_0EFA.signed_value, &native_state_fd_50F6_0EF8.signed_value, plane, x, y, a, b);
    else {
        native_state_fd_50F6_0D6C.signed_value = -1;
        dir = o25_3BA4_1581(plane, x, y, a, b);
    }
    return dir;
}

int16_t  o25_3BA4_19AD(int16_t  *rot, int16_t  *dir, int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    native_state_fd_50F6_0EF8.signed_value = GetDir(x, y, a, b) - 1;
    native_state_fd_50F6_0D6C.signed_value = 0x10;
    native_state_fd_50F6_0EFA.signed_value = 0;
    return o25_3BA4_1686(&native_state_fd_50F6_0EFA.signed_value, &native_state_fd_50F6_0EF8.signed_value, plane, x, y, a, b);
}

int16_t  o25_3BA4_1A0D(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t dir;

    if (native_state_fd_50F6_0D6C.signed_value < 0) {
        dir = o25_3BA4_1581(plane, x, y, a, b);
        if (dir == -2 && native_state_fd_50F6_0D6C.signed_value == -2)
            dir = o25_3BA4_19AD(&native_state_fd_50F6_0EFA.signed_value, &native_state_fd_50F6_0EF8.signed_value, plane, x, y, a, b);
    } else {
        dir = o25_3BA4_1935(plane, x, y, a, b);
        native_state_fd_50F6_0D6C.signed_value--;
    }
    return dir;
}

/* The result goes through a local that MSC eliminates (value only returned); as a
 * register candidate it still takes SI first, so p1 lands in DI as in the original. */
int16_t  o25_3BA4_1A9F(int16_t p1, int16_t x1, int16_t y1, int16_t p2, int16_t x2, int16_t y2)
{
    int16_t r;

    if (p1 <= 1) {
        if (p2 <= 1)
            r = o25_3BA4_1A0D(p1, x1, y1, x2, y2);
        else if (p2 == 2)
            r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02AC[0], fd_3D57_02AC[1]);
        else
            r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02B0[0], fd_3D57_02B0[1]);
    } else if (p2 == p1)
        r = o25_3BA4_1A0D(p1, x1, y1, x2, y2);
    else if (p1 == 2)
        r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1]);
    else
        r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1]);
    return r;
}

#pragma pack(pop)
