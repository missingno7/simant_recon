#include "portable/whole_program/state/yard_cache_globals_v1.h"
#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect *g_5AAC;
/* Overlay section S22, code frame 39C7: editor mouse dispatch and the yellow ant
 * (processEdit..YellowHelp; Win16 SIMANT unit processEdit..YellowHelp).
 * Built /AL /Os /Oe /Og /Zi under MSC 6.00AX: 6.00A allocates CONST segment words for
 * far variables whose loads were all hoisted to immediate segments (YellowDeath), 6.00AX
 * does not.  /Zi (a code record per function) reproduces the original relocation order
 * across all 15 functions, /Zd cannot (SetGoalsY and YellowCommandKey start records).
 * The one-line ifs and the while loops in YellowDeath place the line-number record
 * breaks (every 52 entries) where the original has them.  The MapPnt/editTileRect
 * struct types decide the imul operand order in DoLaserFire; the fd_50F6_048A
 * declaration after 0AE8 decides the compare order in YellowCommandKey. */

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

extern int16_t  WinPrintf(char  *format, ...);
extern int16_t  win_IsWinInFront(int16_t win);
extern int32_t  TickCount(void);
extern int16_t  win_GetEvent(struct Event  *ev);
struct Pt {
    int16_t x;
    int16_t y;
};

extern int16_t  g_19BE;
extern int16_t  g_19C0;
extern int16_t  fd_50F6_0EAC;
extern void  processExp(int16_t x, int16_t y, int16_t shift);
extern int16_t  MePlane;
extern int16_t  IsItYellow(int16_t plane, int16_t x, int16_t y);
extern int16_t  myButton(void);
extern void  AntMenu(struct Event  *ev);
extern int16_t  GetLife(int16_t plane, int16_t x, int16_t y);
extern void  CenterAnt(void);
extern int16_t  MagnifyMenu(int16_t x, int16_t y, int16_t plane);
extern int16_t  fd_50F6_0A06;
extern int16_t  IsYellowAnt(int16_t life);
extern int16_t  FindAntIndex(int16_t plane, int16_t x, int16_t y, int16_t life);
void  SetGoalsY(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsItDigable(int16_t plane, int16_t x, int16_t y);
extern int16_t  GetMap(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsThisGrass(int16_t plane, int16_t tile);
extern int16_t  fd_50F6_04C2;
extern int16_t  IsLiftable(int16_t plane, int16_t x, int16_t y);
extern void  ExchangeLives(int16_t plane, int16_t x, int16_t y);
void  processSpider(int16_t x, int16_t y, int16_t mode);

void  processEdit(struct Event  *ePtr)
{
    struct Event ev;
    int32_t t;
    int16_t shift;
    int16_t x;
    int16_t y;
    int16_t life;

    if ((dos_keyboard_modifiers() & 8) == 1)
        shift = 1;
    else
        shift = (ePtr->modifiers & 0x6000) != 0;
    WinPrintf("ePtr->mouse_flags=%x", ePtr->modifiers);
    if (!shift && win_IsWinInFront(0)) {
        t = TickCount() + 6;
        while (TickCount() < t) {
            if (win_GetEvent(&ev) == 1 && (ev.modifiers & 0x6000) && ev.code == ePtr->code) {
                ePtr = &ev;
                break;
            }
        }
        shift = (ePtr->modifiers & 0x6000) != 0;
    }
    x = (ePtr->h - (*((struct Rect *)native_game_fd_50F6_110C.raw)).left) / g_19BE + (*((struct Pt *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
    y = (ePtr->v - (*((struct Rect *)native_game_fd_50F6_110C.raw)).top) / g_19C0 + (*((struct Pt *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
    if (fd_50F6_0EAC == 3) {
        processExp(x, y, shift);
        return;
    }
    if (native_state_fd_50F6_0F44.signed_value) native_state_fd_50F6_0F44.signed_value = 0;
    switch (native_state_fd_50F6_105E.signed_value) {
    case -1:
        if (!shift) {
            if (IsItYellow(MePlane, x, y) == 1) {
                if (myButton() == 1) {
                    AntMenu(ePtr);
                    return;
                }
                if (GetLife(MePlane, x, y) != 0xfe) CenterAnt();
                return;
            }
            if (myButton() == 1 && MagnifyMenu(x, y, native_state_MapPlane.signed_value) >= 0)
                return;
        } else if (fd_50F6_0A06 == 0 && (life = GetLife(native_state_MapPlane.signed_value, x, y)) >= 0
                   && (life & 0x7f) >= 8 && !IsYellowAnt(life)) {
            if ((native_state_fd_50F6_07C0.signed_value = FindAntIndex(native_state_MapPlane.signed_value, x, y, life)) < 0)
                return;
            native_state_fd_50F6_0A8E.signed_value = ((native_state_fd_50F6_04E2.signed_value ^ life) & 0x80) ? 3 : 4;
            native_state_fd_50F6_084E.signed_value = life;
            if (native_state_MapPlane.signed_value == 0)
                native_state_fd_50F6_08DA.signed_value = 1;
            else
                native_state_fd_50F6_08DA.signed_value = native_state_MapPlane.signed_value;
            native_state_fd_50F6_08E2.signed_value = x;
            native_state_fd_50F6_09F0.signed_value = y;
            SetGoalsY(native_state_MapPlane.signed_value, x, y);
            native_state_fd_50F6_0AA0.signed_value = 1;
            return;
        }
        WinPrintf("\nMapPlane=%d", native_state_MapPlane.signed_value);
        if (native_state_MapPlane.signed_value <= 1) {
            if (fd_50F6_0A06 == 1) {
                processSpider(x, y, shift);
                return;
            }
            native_state_fd_50F6_0A8E.signed_value = shift;
        } else {
            if (fd_50F6_0A06 != 0)
                return;
            if (shift == 1) {
                if (IsItDigable(native_state_MapPlane.signed_value, x, y) == 1
                    || (MePlane >= 2 && y <= 0
                        && IsThisGrass(native_state_MapPlane.signed_value, GetMap(native_state_MapPlane.signed_value, x, y)) == 1))
                    native_state_fd_50F6_0A8E.signed_value = 2;
                else if ((fd_50F6_04C2 & 8) || IsLiftable(native_state_MapPlane.signed_value, x, y))
                    native_state_fd_50F6_0A8E.signed_value = 1;
                else
                    native_state_fd_50F6_0A8E.signed_value = 2;
            } else
                native_state_fd_50F6_0A8E.signed_value = 0;
        }
        SetGoalsY(native_state_MapPlane.signed_value, x, y);
        native_state_fd_50F6_0AA0.signed_value = 1;
        return;
    case 10:
        ExchangeLives(native_state_MapPlane.signed_value == 0 ? 1 : native_state_MapPlane.signed_value, x, y);
        return;
    case 11:
        if (native_state_MapPlane.signed_value <= 1 && fd_50F6_0A06 == 1)
            processSpider(x, y, shift);
        return;
    }
}

extern void  myBeginSound(int16_t a, int16_t b, int16_t c);

extern void  clip_Push(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  clip_SetWin(int16_t win);
extern void  f_0250_5058(void);
extern void ( *  g_916C)(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t color);
extern void  f_0250_0E15(void);
extern void  clip_SubInclude(struct Rect  *rect);
extern int16_t  fd_50F6_3856;
extern int16_t  fd_50F6_3858;
extern int16_t  fd_55B3_29A2;
extern void  clip_Pop(void);

void  DoLaserFire(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    int16_t sx;
    int16_t sy;
    int16_t ex;
    int16_t ey;
    int16_t originX;
    int16_t originY;

    myBeginSound(0x37, 0x8265, 0x3f);
    if (native_state_MapPlane.signed_value == 1) {
        if (g_5A97 == 2) {
            x2 = (3 * x2) / 4;
            y2 = (3 * y2) / 4;
            x1 = (3 * x1) / 4;
            y1 = (3 * y1) / 4;
        }
        clip_Push();
        if (win_IsWinOpen(0)) {
            clip_SetWin(0);
            if (g_5AAC->top != (int16_t)0x8000) {
                f_0250_5058();
                originX = (*((struct Pt *)native_sim_state_fd_50F6_0508.raw_bytes)).x * g_19BE - (*((struct Rect *)native_game_fd_50F6_110C.raw)).left;
                originX = -originX;
                originY = g_19C0 * (*((struct Pt *)native_sim_state_fd_50F6_0508.raw_bytes)).y - (*((struct Rect *)native_game_fd_50F6_110C.raw)).top;
                originY = -originY;
                ex = originX + x1;
                ey = originY + y1;
                sx = originX + x2;
                sy = originY + y2;
                g_916C(ex, ey, sx, sy, f_1B4E_000D(3));
                g_916C(ex + 1, ey + 1, sx + 1, sy + 1, f_1B4E_000D(3));
                g_9134(sx, sy, sx + 2, sy + 2, f_1B4E_000D(2));
                f_0250_0E15();
            }
        }
        if (win_IsWinOpen(0x100)) {
            clip_SetWin(0x100);
            clip_SubInclude(&(*((struct Rect *)native_game_fd_50F6_10D2.raw)));
            sx = (x2 / g_19BE) * fd_50F6_3856 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
            sy = (y2 / g_19C0) * fd_50F6_3858 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
            ex = (x1 / g_19BE) * fd_50F6_3856 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
            ey = (y1 / g_19C0) * fd_50F6_3858 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
            g_916C(ex, ey, sx, sy, f_1B4E_000D(3));
            g_916C(ex + 1, ey + 1, sx + 1, sy + 1, f_1B4E_000D(3));
            g_9134(sx, sy, sx + 2, sy + 2, f_1B4E_000D(1) | 0x20);
            fd_55B3_29A2 = 1;
        }
        clip_Pop();
    }
}

extern uint8_t  LifeA[64][64];
extern void  EndTargetMode(void);

void  processSpider(int16_t x, int16_t y, int16_t mode)
{
    int16_t life;
    int16_t idx;

    if (mode < 1 && native_state_fd_50F6_105E.signed_value != 11) {
        native_state_Starg.signed_value = -2;
        native_state_StargLife.signed_value = -1;
        native_state_SMode.signed_value = 0;
        native_state_SuserX.signed_value = x;
        native_state_SuserY.signed_value = y;
        native_state_fd_50F6_0A8E.signed_value = mode;
        return;
    }
    life = LifeA[x][y];
    if (life != 0) {
        idx = FindAntIndex(1, x, y, life);
        if (idx >= 0) {
            native_state_StargLife.signed_value = life;
            native_state_Starg.signed_value = idx;
            native_state_SMode.signed_value = 2;
            if (native_state_fd_50F6_105E.signed_value == 11) {
                myBeginSound(0xf, 0, 0x7e);
                native_state_fd_50F6_06AC.signed_value = 6;
                EndTargetMode();
            }
            return;
        }
    }
    if (native_state_fd_50F6_105E.signed_value == 11) {
        myBeginSound(1, 0, 0x7e);
        return;
    }
    native_state_Starg.signed_value = -2;
    native_state_StargLife.signed_value = -1;
    native_state_SMode.signed_value = 0;
    native_state_SuserX.signed_value = x;
    native_state_SuserY.signed_value = y;
    native_state_fd_50F6_0A8E.signed_value = mode;
}

extern int16_t  MeLocX;
extern int16_t  MeLocY;

void  ResetYellowVars(int16_t plane, int16_t x, int16_t y)
{
    MePlane = plane;
    native_state_fd_50F6_0AF8.signed_value = plane;
    MeLocX = x;
    native_state_fd_50F6_0AB6.signed_value = x;
    native_state_fd_50F6_0AD6.signed_value = x;
    MeLocY = y;
    native_state_fd_50F6_0AC6.signed_value = y;
    native_state_fd_50F6_0AE8.signed_value = y;
    native_state_fd_50F6_0A8E.signed_value = 0;
    native_state_fd_50F6_0AA0.signed_value = 0;
    native_state_fd_50F6_0B1E.signed_value = 0;
    native_state_fd_50F6_0C38.signed_value = 0;
    native_state_fd_50F6_0C3E.signed_value = 0;
    native_state_fd_50F6_0D6C.signed_value = -2;
}

void  SetGoalsY(int16_t plane, int16_t x, int16_t y)
{
    if (plane == 0)
        native_state_fd_50F6_0AF8.signed_value = 1;
    else
        native_state_fd_50F6_0AF8.signed_value = plane;
    native_state_fd_50F6_0AD6.signed_value = x;
    native_state_fd_50F6_0AE8.signed_value = y;
    native_state_fd_50F6_0D6C.signed_value = -2;
    if (plane >= 2 && y < 2) {
        if (x <= 0)
            x = 1;
        else if (x >= 63)
            x = 62;
        native_state_fd_50F6_0AD6.signed_value = x;
    }
}

extern int16_t  fd_3D57_07A8[];
extern int16_t  fd_50F6_0496;
extern void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t code);
extern void  ClearMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern void  GotoMyAnt(void);
extern void  DoEditAndMapUpdateDraw(void);
extern void  myBeginSong(uint16_t id, uint16_t arg);
extern int16_t  mySongIsDone(void);
extern int16_t  win_Events(void);
extern void  myDelay(int32_t ticks);
extern void  SetLife(int16_t plane, int16_t x, int16_t y, int16_t value);
extern void  win_FlushEvents(void);
extern int16_t  fd_3D57_0C24;
extern void  SetMyHealth(int16_t health);
extern int32_t  MacTickCount(void);
extern void  DoEditUpdateDraw(void);
extern void  MakeBlkQueen(int16_t x, int16_t y, int16_t dir);
extern void  MakeRedQueen(int16_t x, int16_t y, int16_t dir);
extern int16_t  mySoundIsDone(void);
extern void  SetSimCursor(int16_t a);
void  YellowDialog(int16_t bitmap, int16_t promptIndex);

void  YellowBirth(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t mode)
{
    int32_t t;
    int16_t save;
    int16_t oldType;
    int16_t i;

    save = fd_3D57_07A8[2];
    oldType = fd_50F6_04C2;
    fd_3D57_07A8[2] = 0;
    fd_50F6_0A06 = 0;
    if (mode == 0) {
        native_state_fd_50F6_0502.signed_value = 1;
        SetMyLife(plane, x, y, 0, fd_50F6_0496, 0xff);
    } else {
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
        SetMyLife(MePlane, MeLocX, MeLocY, 0x60, fd_50F6_0496, 0xff);
    }
    if (mode == 0)
        GotoMyAnt();
    DoEditAndMapUpdateDraw();
    if (mode != 0) {
        myBeginSong(0x4e20, 0x7e);
        t = TickCount() + 300;
        while (!mySongIsDone()) {
            if (TickCount() >= t || win_Events())
                break;
            myDelay(1L);
        }
        SetLife(plane, x, y, 1);
        DoEditAndMapUpdateDraw();
    }
    win_FlushEvents();
    fd_3D57_07A8[2] = save;
    myBeginSound(0x1c, 0, 0x7e);
    myDelay(45L);
    ResetYellowVars(MePlane, MeLocX, MeLocY);
    fd_3D57_0C24 = 1;
    SetMyHealth(100);
    if (mode == 0)
        fd_50F6_0496 = oldType == 0x60 ? 2 : 6;
    for (i = 2; i <= 7; i++) {
        t = MacTickCount() + 10;
        if (mode == 0) {
            native_state_fd_50F6_0502.signed_value = i;
            SetMyLife(MePlane, MeLocX, MeLocY, 0, fd_50F6_0496, 0xff);
        } else
            SetLife(MePlane, x, y, i);
        DoEditUpdateDraw();
        while (MacTickCount() < t && !win_Events())
            myDelay(1L);
    }
    win_FlushEvents();
    if (mode != 0)
        while (!mySongIsDone())
            myDelay(5L);
    myBeginSound(0x31, 0, 0x7e);
    if (mode == 0) {
        SetMyLife(MePlane, MeLocX, MeLocY, type, fd_50F6_0496, 0xff);
    } else {
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
        if (MePlane == 2) {
            MakeBlkQueen(MeLocX, MeLocY, fd_50F6_0496);
            native_sim_state_fd_50F6_0AEC.signed_values[5]++;
        } else {
            MakeRedQueen(MeLocX, MeLocY, fd_50F6_0496);
            native_sim_state_fd_50F6_0AFA.signed_values[5]++;
        }
        SetMyLife(MePlane, x, y, type, fd_50F6_0496 ^ 4, 0xff);
        if (native_state_fd_50F6_04E2.signed_value == 0) {
            native_sim_state_fd_50F6_0AEC.signed_values[1]++;
            native_sim_state_fd_50F6_0AEC.signed_values[4]--;
            native_state_BpopT.signed_value++;
        } else {
            native_sim_state_fd_50F6_0AFA.signed_values[1]++;
            native_sim_state_fd_50F6_0AFA.signed_values[4]--;
            native_state_RpopT.signed_value++;
        }
    }
    DoEditUpdateDraw();
    while (!mySoundIsDone())
        myDelay(5L);
    if (mode != 0)
        myBeginSong(0x4e21, 0x7e);
    else
        myBeginSong(0x2afd, 0x7e);
    SetSimCursor(0);
    YellowDialog(0x238d, mode + 1);
}

extern void  SetDefaultWindPrompt(int16_t mode);
extern int16_t  DropMyObject(int16_t plane, int16_t x, int16_t y, int16_t tx, int16_t ty);
extern int8_t  fd_3D57_0094[];
extern void  o25_3BA4_0C01(int16_t plane, int16_t x, int16_t y, int16_t dir, int16_t type, int16_t cause);
extern int16_t  SRand1(int16_t range);
extern void  PictStrnDialog(int16_t pict, int16_t strn, int16_t flag);
extern void  SpiderDialog(void);
extern void  o25_3BA4_0999(int16_t plane, int16_t x, int16_t y, int16_t dir, int16_t type, int16_t cause);
void  LionDialog(void);
extern void  UpdateEverything(void);
extern void  UnRecruit(int16_t all);
void  SetAlarmDropState(int16_t state, int16_t quiet);
extern uint8_t  BlistT[];
extern uint8_t  BlistY[];
extern uint8_t  BlistX[];
extern uint8_t  LifeB[64][64];
extern int16_t  ListIndexA;
extern uint8_t  AlistT[];
extern uint8_t  AlistY[];
extern uint8_t  AlistX[];
extern uint8_t  RlistT[];
extern uint8_t  RlistY[];
extern uint8_t  RlistX[];
extern uint8_t  LifeR[64][64];
void  SpecialXfer(void);

void  YellowDeath(int16_t cause)
{
    int16_t save;
    int16_t strn;
    int16_t found;
    int16_t i;
    int16_t t;
    int16_t life;

    SetSimCursor(6);
    SetDefaultWindPrompt(1);
    if (fd_50F6_0A06 == 0 && (fd_50F6_04C2 & 8)) {
        save = fd_3D57_07A8[2];
        fd_3D57_07A8[2] = 0;
        if (!DropMyObject(MePlane, MeLocX, MeLocY, MeLocX, MeLocY))
            fd_50F6_04C2 = (fd_50F6_04C2 & 0x80) | (fd_3D57_0094[(fd_50F6_04C2 & 0x78) >> 3] << 3);
        fd_3D57_07A8[2] = save;
    }
    GotoMyAnt();
    DoEditAndMapUpdateDraw();
    if (cause >= 7 && cause < 10)
        o25_3BA4_0C01(MePlane, MeLocX, MeLocY, fd_50F6_0496, fd_50F6_04C2, cause);
    SetSimCursor(0);
    switch (cause) {
    case 0:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        strn = native_state_fd_50F6_1058.signed_value ? 0x272e : 0x2730;
        if (fd_3D57_07A8[3]) PictStrnDialog(0x23c4, strn, 1);
        break;
    case 1:
        if (fd_3D57_07A8[3]) SpiderDialog();
        native_state_BAntsEaten.signed_value++;
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        o25_3BA4_0999(MePlane, MeLocX, MeLocY, fd_50F6_0496, fd_50F6_04C2, cause);
        break;
    case 2:
        if (fd_3D57_07A8[3]) LionDialog();
        native_state_BAntsEaten.signed_value++;
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        o25_3BA4_0999(MePlane, MeLocX, MeLocY, fd_50F6_0496, fd_50F6_04C2, cause);
        break;
    case 3:
        myBeginSound(1, 0, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0, 0x272a, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 4:
        myBeginSound(1, 0, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0, 0x272c, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 5:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c3, 0x2732, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 6:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c0, 0x2734, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 7:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23be, 0x2736, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 8:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c2, 0x2738, 1);
        native_state_fd_50F6_0F30.signed_value++;
        break;
    case 9:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23bf, 0x273a, 1);
        native_state_fd_50F6_0EFC.signed_value++;
        break;
    case 10:
        native_state_fd_50F6_0EFC.signed_value++;
        o25_3BA4_0999(MePlane, MeLocX, MeLocY, fd_50F6_0496, fd_50F6_04C2, 10);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c4, 0x273d, 1);
        break;
    }
    if (cause >= 1 && cause <= 2)
        YellowDialog(0x238c, 0);
    UpdateEverything();
    if (fd_50F6_0A06 == 0)
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    SetSimCursor(6);
    UnRecruit(1);
    if (native_state_fd_50F6_104E.signed_value)
        SetAlarmDropState(0, 1);
    found = 0;
    i = native_state_ListIndexB.signed_value;
    while (i >= 0) {
        t = BlistT[i];
        if (t != 0 && t < 8) {
            LifeB[native_state_fd_50F6_0F0E.signed_value = BlistX[i]][native_state_fd_50F6_0F26.signed_value = BlistY[i]] = BlistT[i] = 0;
            found = 1;
            MePlane = 2;
            break;
        }
        i--;
    }
    if (!found) {
        i = native_state_ListIndexB.signed_value;
        while (i >= 0) {
            t = BlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeB[native_state_fd_50F6_0F0E.signed_value = BlistX[i]][native_state_fd_50F6_0F26.signed_value = BlistY[i]] =
                    (life = BlistT[i], BlistT[i] = 0);
                found = 2;
                MePlane = found;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = ListIndexA;
        while (i >= 0) {
            t = AlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeA[native_state_fd_50F6_0F0E.signed_value = AlistX[i]][native_state_fd_50F6_0F26.signed_value = AlistY[i]] =
                    (life = AlistT[i], AlistT[i] = 0);
                found = 2;
                MePlane = 1;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = native_state_ListIndexR.signed_value;
        while (i >= 0) {
            t = RlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeR[native_state_fd_50F6_0F0E.signed_value = RlistX[i]][native_state_fd_50F6_0F26.signed_value = RlistY[i]] =
                    (life = RlistT[i], RlistT[i] = 0);
                found = 2;
                MePlane = 3;
                break;
            }
            i--;
        }
    }
    if (!found) {
        if (fd_50F6_0EAC <= 1) {
            native_state_fd_50F6_0376.signed_value = 1;
            native_state_fd_50F6_0366.signed_value = 0;
            return;
        } else if (fd_50F6_0EAC == 2) {
            if (native_state_fd_50F6_03E2.signed_value < 2) {
                native_state_fd_50F6_0376.signed_value = 1;
                native_state_fd_50F6_0366.signed_value = 0;
                PictStrnDialog(0, 0x2748, 1);
            } else {
                PictStrnDialog(0, 0x274a, 1);
                SpecialXfer();
            }
            return;
        }
    }
    if (found == 1) {
        if (fd_50F6_04C2 == 0x60)
            fd_50F6_04C2 = 0x10;
        YellowBirth(MePlane, native_state_fd_50F6_0F0E.signed_value, native_state_fd_50F6_0F26.signed_value, fd_50F6_04C2, 0);
    } else {
        fd_50F6_0A06 = 0;
        SetMyLife(MePlane, native_state_fd_50F6_0F0E.signed_value, native_state_fd_50F6_0F26.signed_value, life & 0xf8, fd_50F6_0496,
                  (life & 0xf8) + fd_50F6_0496);
        ResetYellowVars(MePlane, native_state_fd_50F6_0F0E.signed_value, native_state_fd_50F6_0F26.signed_value);
        SetMyHealth(100);
        GotoMyAnt();
        DoEditAndMapUpdateDraw();
        PictStrnDialog(0, 0x274b, 1);
    }
}

extern uint8_t  fd_3D57_00A4[12][16];
extern void  MapToYard(void);
extern void  f_20E8_0725(int16_t win);
extern void  SetYardMode(int16_t mode);
extern int16_t  fd_3D57_0C20;
extern void  SetMapPlane(int16_t plane);
extern void  *  *  fd_50F6_034C;
extern void  EditMessage(void  *msg, int32_t ticks, int16_t mode);

extern void  XferPatch(void);

void  SpecialXfer(void)
{
    struct Event ev;
    int16_t done;
    int16_t x;
    int16_t y;

    fd_3D57_00A4[native_sim_state_fd_50F6_07CA.words[0]][native_sim_state_fd_50F6_07CA.words[1]] = 0;
    if (!win_IsWinInFront(0x1900)) {
        if (!win_IsWinOpen(0x1900))
            MapToYard();
        else
            f_20E8_0725(0x1900);
    }
    SetYardMode(2);
    fd_3D57_0C20 = 1;
    SetMapPlane(0);
    EditMessage(fd_50F6_034C[20], -2L, 1);
    done = 0;
    while (!done) {
        if (!win_GetEvent(&ev))
            continue;
        if (!win_IsWinInFront(0x1900)) {
            if (!win_IsWinOpen(0x1900))
                MapToYard();
            else
                f_20E8_0725(0x1900);
        }
        y = ev.v - (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
        x = ev.h - (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
            x = (x + 2) * 2;
            y = (y - 8) * 2;
        }
        y = (y - fd_55B3_2A42[1]) / 10;
        x = (x - fd_55B3_2A42[0] + y * 10) / 28;
        if (x >= 0 && y >= 0 && x <= 11 && y <= 15) {
            if (fd_3D57_00A4[x][y]) {
                myBeginSong(0x2afb, 0x7e);
                native_sim_state_fd_50F6_07BC.words[0] = x;
                native_sim_state_fd_50F6_07BC.words[1] = y;
                XferPatch();
                done = 1;
            } else {
                myBeginSound(1, 0, 0x7e);
                EditMessage(fd_50F6_034C[19], 120L, 1);
            }
        } else {
            myBeginSound(1, 0, 0x7e);
            EditMessage(fd_50F6_034C[10], 120L, 1);
        }
    }
    EditMessage(0L, -2L, 1);
}

extern void  win_LockWin(int16_t win);
extern void  win_SetObjBitmap(int16_t obj, int16_t bitmap);
extern void  win_Open(int16_t win);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern struct Pt  fd_3D57_0B14[];
extern void  win_UnlockWin(int16_t win);
extern void  win_Close(int16_t win);

void  LionDialog(void)
{
    struct Rect rect;
    int32_t t1;
    int32_t t2;
    int16_t x0;
    int16_t y0;
    int16_t frame;

    if (fd_3D57_07A8[3] == 0)
        return;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, 0x23f0);
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    y0 = rect.top;
    x0 = rect.left;
    myBeginSound(0x26, 0, 0x7e);
    while (!mySoundIsDone())
        ;
    frame = 1;
    t1 = MacTickCount() + 300;
    t2 = MacTickCount() + 30;
    win_FlushEvents();
    while (!win_Events()) {
        if (MacTickCount() >= t1)
            break;
        if (!win_IsWinOpen(0x1a00))
            break;
        if (MacTickCount() >= t2) {
            t2 = MacTickCount() + 30;
            if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140)
                win_DrawBitMap(x0, y0, 0x23f0 + frame);
            else
                win_DrawBitMap(fd_3D57_0B14[frame].x + x0, fd_3D57_0B14[frame].y + y0, 0x23f0 + frame);
            if (frame & 1)
                myBeginSound(0x25, 0, 0x7e);
            frame++;
            if (frame > 3)
                frame = 2;
        }
    }
    win_FlushEvents();
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}

extern void  win_PrintfAtObj(int16_t obj, char  *fmt, ...);
extern struct Pt  fd_3D57_0B24;
extern int16_t  f_1F58_0038(void);
extern void  DialogWaitInit(int16_t mode);
extern int16_t  DialogAbortOrCont(void);

void  YellowDialog(int16_t bitmap, int16_t promptIndex)
{
    struct Rect rect;
    int16_t x0;
    int16_t y0;

    if (fd_3D57_07A8[3] == 0)
        return;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, bitmap);
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    y0 = rect.top;
    x0 = rect.left;
    switch (bitmap) {
    case 0x238c:
    case 0x238d:
        win_PrintfAtObj(0x1a02, fd_50F6_034C[promptIndex + 23]);
        myDelay(300L);
        break;
    case 0x2396:
        myBeginSound(0x2a, 0, 0x7e);
        myDelay(45L);
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
            fd_3D57_0B24.x = 0x28;
            fd_3D57_0B24.y = 0x23;
        }
        if (win_IsWinOpen(0x1a00))
            win_DrawBitMap(fd_3D57_0B24.x + x0, y0 + fd_3D57_0B24.y, 0x2397);
        myBeginSound(0x2d, 0, 0x7e);
        myDelay(45L);
        break;
    }
    if (!win_Events() && f_1F58_0038()) {
        DialogWaitInit(3);
        while (!DialogAbortOrCont() && !win_Events())
            ;
    }
    win_FlushEvents();
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}

extern int8_t  Dx8[8];
extern int8_t  Dy8[8];
extern int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern void  MoveMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern void  EatMyFood(int16_t kind);

void  DoTroph(int16_t x, int16_t y, int16_t index)
{
    int16_t newX;
    int16_t newY;

    newX = Dx8[index] + x;
    newY = Dy8[index] + y;
    MoveMyLife(MePlane, newX, newY, fd_50F6_04C2, GetDir(newX, newY, x, y) - 1);
    DoEditUpdateDraw();
    EatMyFood(1);
}

extern int16_t  fd_3D57_07BE;
extern void  win_SetObjSelectedState(int16_t obj, int16_t state);
extern int16_t  fd_50F6_0FFA;
extern int16_t  fd_50F6_0FB6;
extern void  InvalEuMap(int16_t left, int16_t top, int16_t right, int16_t bottom);

void  SetAlarmDropState(int16_t state, int16_t quiet)
{
    if (state) {
        if (MePlane == 1 && fd_50F6_0A06 == 0) {
            fd_3D57_07BE = 0;
            win_SetObjSelectedState(0x10, state);
            native_state_fd_50F6_104E.signed_value = 1;
            if (quiet == 0)
                myBeginSound(0xf, 0, 0x7e);
        } else if (quiet == 0)
            myBeginSound(1, 0, 0x7e);
    } else {
        native_state_fd_50F6_104E.signed_value = 0;
        win_SetObjSelectedState(0x10, state);
        fd_3D57_07BE = -1;
        if (quiet == 0)
            myBeginSound(0xf, 0, 0x7e);
    }
    InvalEuMap(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
}

void  YellowCommand(int16_t cmd);

int16_t  YellowCommandKey(int16_t key)
{
    int16_t handled;

    handled = 1;
    switch (key) {
    case 0x30:
        YellowCommand(7);
        break;
    case 0x31:
        if (fd_50F6_0A06 == 0) {
            if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
                YellowCommand(8);
            else
                YellowCommand(1);
        } else
            YellowCommand(10);
        break;
    case 0x32:
        if (fd_50F6_0A06 == 0) {
            if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
                YellowCommand(9);
            else
                YellowCommand(2);
        } else
            YellowCommand(11);
        break;
    case 0x33:
        YellowCommand(4);
        break;
    case 0x34:
        YellowCommand(5);
        break;
    case 0x58:
    case 0x78:
        YellowCommand(6);
        break;
    case 0x88:
        if (dos_keyboard_modifiers() & 3) {
            GotoMyAnt();
            break;
        }
        if (fd_50F6_0A06 == 0) {
            if (native_state_fd_50F6_0AA0.signed_value)
                ResetYellowVars(MePlane, MeLocX, MeLocY);
            else
                CenterAnt();
        } else if (fd_50F6_0A06 == 1) {
            if (native_state_SuserX.signed_value != MeLocX || native_state_SuserY.signed_value != MeLocY) {
                native_state_SuserX.signed_value = MeLocX;
                native_state_SuserY.signed_value = MeLocY;
                native_state_SMode.signed_value = 0;
            } else
                CenterAnt();
        }
        break;
    case 0x824:
        if (fd_50F6_0A06 == 1)
            YellowCommand(12);
        break;
    case 0x847:
        myBeginSound(0xf, 0, 0x7e);
        GotoMyAnt();
        break;
    default:
        handled = 0;
        break;
    }
    return handled;
}

void  YellowHelp(void);
extern void  Recruit(int16_t count);
extern void  StartLifeTransfer(void);
extern int16_t  TryMyDropOrLift(int16_t plane, int16_t x, int16_t y);
extern void  TargetAnt(void);

void  YellowCommand(int16_t cmd)
{
    if (fd_50F6_0A06 > 1)
        return;
    switch (cmd) {
    case 0:
        YellowHelp();
        break;
    case 1:
        myBeginSong(0x2b05, 0x7e);
        Recruit(5);
        break;
    case 2:
        myBeginSong(0x2b06, 0x7e);
        Recruit(10);
        break;
    case 3:
        myBeginSong(0x2b07, 0x7e);
        Recruit(1000);
        break;
    case 4:
        myBeginSong(0x2b08, 0x7e);
        UnRecruit(0);
        break;
    case 5:
        myBeginSong(0x2b09, 0x7e);
        UnRecruit(1);
        break;
    case 6:
        StartLifeTransfer();
        break;
    case 7:
        SetAlarmDropState(!native_state_fd_50F6_104E.signed_value, 0);
        break;
    case 8:
        if (MePlane != 1 || TryMyDropOrLift(MePlane, MeLocX, MeLocY) == -1)
            myBeginSound(1, 0, 0x7e);
        break;
    case 9:
        if (MePlane == 2 && MeLocY >= 3) {
            SetSimCursor(6);
            YellowBirth(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4] * 2,
                        MeLocY + Dy8[fd_50F6_0496 ^ 4] * 2, 0x10, 1);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    case 10:
        TargetAnt();
        break;
    case 11:
        if (native_state_fd_50F6_06AC.signed_value == 7) {
            native_state_fd_50F6_06AC.signed_value = 0;
            myBeginSound(2, 0x56ee, 0x7e);
        } else {
            native_state_fd_50F6_06AC.signed_value = 7;
            myBeginSound(2, 0x2b77, 0x7e);
        }
        break;
    case 12:
        if (native_state_fd_50F6_06AC.signed_value == 8) {
            native_state_fd_50F6_06AC.signed_value = 0;
            myBeginSound(2, 0x56ee, 0x7e);
        } else {
            native_state_fd_50F6_06AC.signed_value = 8;
            myBeginSound(0x29, 0, 0x7e);
        }
        break;
    }
}

void  YellowHelp(void)
{
    struct Event ev;
    int16_t bitmap;

    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04C2 == 0x40)
            bitmap = 0x1197;
        else
            bitmap = 0x1195;
    } else
        bitmap = 0x1199;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, bitmap);
    win_Open(0x1a00);
    DialogWaitInit(0x1e);
    while (win_IsWinOpen(0x1a01) && !DialogAbortOrCont()) {
        if (win_GetEvent(&ev) && (ev.code >> 8) == 0x1a)
            break;
    }
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}


#pragma pack(pop)
