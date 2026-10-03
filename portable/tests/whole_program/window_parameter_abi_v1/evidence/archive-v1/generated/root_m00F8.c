#include "portable/whole_program/state/yard_cache_globals_v1.h"
#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect g_5A9C;
/* Root module 00F8: map/yard window helpers, timing and small hooks. */
typedef struct {
    int16_t x;
    int16_t y;
} Point;

typedef char  *  *Handle;

extern void  clip_Push(void);
extern void  clip_SetWin(int16_t win);
extern void  hanim_RemoveAllAnimObjects(Handle);
extern void  hanim_RenderAnimSet(Handle);
extern void  hanim_RemoveAnimSet(Handle);
extern void  clip_Pop(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  EraseYardCursor(void);

void  win_YardClosed(void)
{
    if (native_game_fd_50F6_10DA) {
        clip_Push();
        clip_SetWin(0x1900);
        hanim_RemoveAllAnimObjects(native_game_fd_50F6_10DA);
        hanim_RenderAnimSet(native_game_fd_50F6_10DA);
        hanim_RemoveAnimSet(native_game_fd_50F6_10DA);
        clip_Pop();
        native_game_fd_50F6_10DA = 0;
    }
    if (win_IsWinOpen(0x1902)) {
        win_GetObjRect(0x1902, &(*((struct Rect *)native_game_fd_50F6_10D2.raw)));
        (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left++;
        EraseYardCursor();
    }
}

extern void  EraseMapCursor(void);
extern int16_t  fd_55B3_29A2;

void  win_MapChanged(void)
{
    if (win_IsWinOpen(0x100)) {
        EraseMapCursor();
        win_GetObjRect(0x102, &(*((struct Rect *)native_game_fd_50F6_10D2.raw)));
        fd_55B3_29A2 = 1;
    }
}

extern int16_t  fd_3D57_07C8;
extern char  *  *  fd_50F6_046C;
extern void  win_SetObjFormatStr(int32_t _dos_obj_wide, ...);
extern void  win_DrawTitle(int16_t win);

void  SetMapTitle(void)
{
    win_SetObjFormatStr(0x101, fd_50F6_046C[fd_3D57_07C8]);
    win_SetObjFormatStr(0x1901, fd_50F6_046C[native_state_YardMode.signed_value + 9]);
    if (win_IsWinOpen(0x100)) {
        clip_Push();
        clip_SetWin(0x100);
        win_DrawTitle(0x101);
        clip_Pop();
    } else if (win_IsWinOpen(0x1900)) {
        clip_Push();
        clip_SetWin(0x1900);
        win_DrawTitle(0x1901);
        clip_Pop();
    }
}

static int32_t g_8BA4;
extern int16_t  WaitedEnough(int32_t  *, int16_t);
extern int16_t  fd_55B3_2CBC;
extern char  fd_55B3_2CBA;
void  f_00F8_01BE(void);

void  f_00F8_017D(void)
{
    if (WaitedEnough(&g_8BA4, 2) && fd_55B3_2CBC == 0) {
        fd_55B3_2CBA = 1;
        f_00F8_01BE();
        fd_55B3_2CBA = 0;
    }
}

extern int16_t  win_Events(void);
extern int16_t  f_1F58_0038(void);
extern int16_t  f_1B73_0A30(int16_t);
extern void  o19_384C_0000(void);
extern int16_t  f_1B73_0EEE(void);
extern int16_t  g_9122;
extern int16_t  g_9124;
extern int16_t  f_0250_0D10(int16_t dx, int16_t dy);

void  f_00F8_01BE(void)
{
    int16_t dx, dy;

    if (win_Events() || f_1F58_0038() || f_1B73_0A30(0x1d) || fd_55B3_2CBC)
        o19_384C_0000();
    do {
        dx = dy = 0;
        if (f_1B73_0EEE())
            break;
        if (g_9122 <= 1)
            dx = -1;
        else if (SIM_GRAPHICS_SOURCE_g_3DB2 - 4 <= g_9122)
            dx = 1;
        if (g_9124 < 1)
            dy = -1;
        else if (SIM_GRAPHICS_SOURCE_g_3DB4 - 4 <= g_9124)
            dy = 1;
        if (!dx && !dy)
            break;
    } while (f_0250_0D10(dx, dy));
}

extern void  win_MakeGroupUnselected(int16_t win, int16_t group);

void  ClearMapScentButtons(void)
{
    win_MakeGroupUnselected(0x100, 2);
}

extern uint32_t  TickCount(void);
int16_t  DialogAbortOrCont(void);

void  myDelay(uint16_t ticks)
{
    int32_t t;

    t = TickCount();
    while (!WaitedEnough(&t, ticks / 3) && !win_Events() && !DialogAbortOrCont())
        ;
}

extern void  f_0000_046F(void);
extern int16_t  StillDown(void);

void  myButton(void)
{
    f_0000_046F();
    StillDown();
}

int32_t  MacTickCount(void)
{
    return TickCount() * 3;
}

void  f_00F8_02D7(void)
{
}

void  SetSimCursor(void)
{
}

void  f_00F8_02E7(void)
{
}

int16_t  f_00F8_02EF(void)
{
    return 0;
}

static int32_t g_8BA8;
static int16_t g_8BAC;
extern void  win_FlushEvents(void);

void  DialogWaitInit(int16_t secs)
{
    while (StillDown())
        win_FlushEvents();
    g_8BA8 = TickCount();
    g_8BAC = secs * 18;
}

void  DialogClearWait(void)
{
    g_8BA8 = TickCount();
    g_8BAC = 5400;
}

int16_t  DialogWait(void)
{
    return WaitedEnough(&g_8BA8, g_8BAC);
}

void  f_00F8_035D(void)
{
}

void  f_00F8_0365(void)
{
}

void  f_00F8_036D(void)
{
}

void  f_00F8_0375(void)
{
}

void  f_00F8_037D(void)
{
}

void  f_00F8_0385(void)
{
}

void  f_00F8_038D(void)
{
}

void  InvalQueenStorageDisp(void)
{
}

void  f_00F8_039D(void)
{
}

void  MakeDMap(void)
{
}

extern int16_t  fd_50F6_10E0;
extern int16_t  fd_50F6_10DE;

int16_t  TileIsVisible(int16_t plane, int16_t x, int16_t y)
{
    int16_t r;

    r = native_state_MapPlane.signed_value == plane && (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x <= x && (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x + fd_50F6_10E0 > x
        && (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y <= y && (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y + fd_50F6_10DE > y;
    return r;
}

extern int16_t  f_1F58_0090(void);

int16_t  f_00F8_040F(void)
{
    int16_t k;

    if (f_1F58_0038() && (k = f_1F58_0090() == 0x1b) || k == 12)
        return 1;
    return 0;
}

void  f_00F8_044C(void)
{
    win_FlushEvents();
}

int16_t  ABS(int16_t value)
{
    if (value < 0)
        return -value;
    return value;
}

void  f_00F8_0477(void)
{
}

extern void  SetMapPlane(int16_t plane);
extern void  win_Swap(int16_t from, int16_t to);
extern void  win_Open(int16_t win);

void  YardToMap(void)
{
    ClearMapScentButtons();
    if (!win_IsWinOpen(0x100)) {
        if (win_IsWinOpen(0x1900)) {
            SetMapPlane(1);
            win_Swap(0x1900, 0x100);
        } else {
            win_Open(0x100);
        }
    }
}

void  MapToYard(void)
{
    if (!win_IsWinOpen(0x1900)) {
        if (win_IsWinOpen(0x100)) {
            SetMapPlane(0);
            win_Swap(0x100, 0x1900);
        } else {
            win_Open(0x1900);
        }
    }
}

extern void  f_20E8_0725(int16_t win);

void  OpenMapYard(int16_t unused)
{
    if (win_IsWinOpen(0x100))
        f_20E8_0725(0x100);
    else if (win_IsWinOpen(0x1900))
        f_20E8_0725(0x1900);
    else
        YardToMap();
}



SimYardCacheHandle f_00F8_0543(int16_t object, int16_t type)
{
    if (type == 2) {
        switch (object) {
        case 30000:
            return fd_55B3_2A36;
        case 30001:
            return fd_55B3_2A3A;
        }
    }
    return 0;
}

extern void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type));
void  f_00F8_0585(void)
{
    ch_SetCacheHooks(f_00F8_0543);
}

extern int16_t  WinPrintf(char  *format, ...);
void  f_00F8_05B4(void);

void  UpdateEverything(void)
{
    WinPrintf("\nUPDATEEVERYTHING!");
    f_00F8_05B4();
}

extern void  f_21FA_0AD2(struct Rect  *rect);
void  f_00F8_05B4(void)
{
    f_21FA_0AD2(&g_5A9C);
}

int16_t  DialogAbort(void)
{
    if (DialogWait())
        return 1;
    if (f_1F58_0038() && f_1F58_0090() == 0x1b)
        return 1;
    return 0;
}

int16_t  DialogAbortOrCont(void)
{
    int16_t r;

    if (DialogWait()) {
        WinPrintf("WAIT YES");
        r = 1;
    } else if (f_1F58_0038()) {
        r = f_1F58_0090();
    } else {
        r = 0;
    }
    if (r == 0)
        WinPrintf("result=%d", r);
    return r;
}

#pragma pack(pop)
