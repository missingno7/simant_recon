#include "portable/whole_program/state/map_render_selectors.h"
#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_slots.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#include "balloon_queue_state_v1.h"
#include "portable/whole_program/algorithms/line16b5.h"
#pragma pack(push, 2)
/* Module at root frame 0250 (large-model code segment). */

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

typedef char  *  *Handle;

extern int16_t  TileIsVisible(int16_t plane, int16_t x, int16_t y);
extern int16_t  fd_50F6_10E0;
extern int16_t  fd_50F6_10DE;
#include "portable/whole_program/state/eu_map_cache.h"

int16_t g_19BE = 16;
int16_t g_19C0 = 16;
int16_t g_19C2 = 13;
int16_t g_19C4 = 7;
char  *g_19C6 = 0;
int32_t g_19CA = 0;
int16_t g_19CE = 1;
int16_t g_19D0 = 0;
int16_t g_19D2[8] = { 0, 0, 1, 1, 2, 2, 3, 3 };
int16_t g_19E2[8] = { 4, 0, 5, 1, 6, 2, 7, 3 };

void  ZapEuMapAt(int16_t plane, int16_t x, int16_t y)
{
    int16_t h;
    int16_t v;

    if (TileIsVisible(plane, x, y) == 1) {
        h = x;
        if (h >= 0 && h < fd_50F6_10E0) {
            v = y;
            if (v >= 0 && v < fd_50F6_10DE)
                portable_eu_map_cache.rows[v][h] = -1;
        }
    }
}

void  InvalEuMap(int16_t left, int16_t top, int16_t right, int16_t bottom)
{
    int16_t x;
    int16_t i;
    int16_t y;

    if (left < 0)
        left = 0;
    else if (right > 127)
        right = 127;
    if (top < 0)
        top = 0;
    else if (bottom > 63)
        bottom = 63;
    for (y = top; y <= bottom; y++) {
        i = y * 40 + left;
        for (x = left; x <= right; x++, i++)
            if (x >= 0 && x < fd_50F6_10E0 && y >= 0 && y < fd_50F6_10DE)
                portable_eu_map_cache.linear[i] = -1;
    }
}

extern void  f_195A_007D(int16_t handle);

void  f_0250_0114(void)
{
    if (g_19D0)
        f_195A_007D(g_19D0);
}

extern int16_t  f_195A_0260(void);
extern char  fd_55B3_360C;
extern int16_t  WinPrintf(char  *format, ...);
extern void  f_195A_0035(void);
extern int16_t  fd_55B3_3614;
extern int16_t  fd_55B3_3612;
extern void  f_195A_001D(void);
extern int16_t  f_195A_004B(int16_t pages);
extern void  f_195A_01CB(int16_t handle, char  *name);
extern int16_t  atexit(void ( *func)(void));

/*C*/
int16_t  f_0250_012D(void)
{
    int16_t ok;

    if (g_19D0 != 0)
        return 1;
    if (f_195A_0260() && fd_55B3_360C >= 0x40) {
        WinPrintf("\nEMS version: %x", fd_55B3_360C);
        f_195A_0035();
        WinPrintf("\ntotal pages: %d", fd_55B3_3614);
        WinPrintf("\nfree  pages: %d", fd_55B3_3612);
        if (fd_55B3_3612 >= 8) {
            f_195A_001D();
            g_19D0 = f_195A_004B(8);
            f_195A_01CB(g_19D0, "TILESXXX");
            atexit(f_0250_0114);
            return 1;
        }
    }
    return 0;
}

extern void  db_ReleaseHandle(Handle handle);

void  f_0250_01E7(void)
{
    if (native_game_fd_50F6_10EA) {
        db_ReleaseHandle(native_game_fd_50F6_10EA);
        native_game_fd_50F6_10EA = 0;
    }
    if (native_game_fd_50F6_10E6) {
        db_ReleaseHandle(native_game_fd_50F6_10E6);
        native_game_fd_50F6_10E6 = 0;
    }
}

static int16_t g_1A2E = -1;

extern int16_t  TERRAINset;

extern Handle  f_1A53_00BA(int16_t object, int16_t kind);
extern void  o00_31AD_18BA(char  *p, uint16_t seg, int16_t n);
extern void  o00_31AD_186A(char  *p, uint16_t seg, int16_t page, uint16_t n);
extern void  db_PurgeObject(int16_t object, int16_t kind);
extern void  f_171C_1C0A(Handle h);
extern void  db_UnhookObject(int16_t object, int16_t kind);

void  f_0250_0256(int16_t set)
{
    int16_t i;

    if (g_1A2E == set)
        return;
    g_1A2E = set;
    TERRAINset = set;
    if ((g_5A97 & 1) || g_5A97 == 2) {
        if (native_game_fd_50F6_10EE)
            f_171C_1C0A(native_game_fd_50F6_10EE);
        native_game_fd_50F6_10EE = f_1A53_00BA(10 - set, 9);
        db_UnhookObject(10 - set, 9);
    } else {
        if (g_19D0 == 0)
            f_0250_01E7();
        fd_50F6_37DE = f_1A53_00BA(10 - set, 9);
        o00_31AD_18BA(*fd_50F6_37DE, 0xa000, 0x100);
        for (i = 0; i < 4; i++)
            o00_31AD_186A(*fd_50F6_37DE + (i << 13), 0xc000, i, 0x2000);
        db_PurgeObject(10 - set, 9);
    }
}


void  OverlayTileSet(int16_t type, int16_t id)
{
    if (type == 0) {
        if (id == 0x3e9) {
            f_0250_0256(1);
            native_state_Barrier.signed_value = 0x90;
        } else if (id == 0x3e8) {
            f_0250_0256(0);
            native_state_Barrier.signed_value = 0x50;
        }
    }
}

extern int16_t  fd_50F6_1102;
extern Handle  f_1A53_00F0(int16_t object, int16_t kind, int16_t type);
extern int32_t  f_171C_1C1C(Handle h);
extern int16_t  f_171C_1E9A(Handle h);
extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);

extern void  f_195A_00F8(int16_t handle);
extern void  f_195A_0122(int16_t handle, int16_t n, int16_t  *map);
extern char  *  fd_55B3_360E;
extern void  f_195A_010D(int16_t handle);
extern Handle  f_171C_1BBA(Handle h);

void  LoadTiles(void)
{
    int16_t i;
    uint16_t n;
    Handle h;
    char  *p;

    native_game_fd_50F6_10EA = 0;
    native_game_fd_50F6_10E6 = 0;
    native_game_fd_50F6_10EE = 0;
    f_0250_0256(0);
    switch (g_5A97) {
    case 0:
    case 8:
        f_0250_012D();
    case 4:
        fd_50F6_1102 = 1;
        if (g_19D0) {
            for (i = 0; i < 6; i++) {
                native_game_fd_50F6_10E6 = f_1A53_00F0(i + 15, 9, 1);
                n = f_171C_1C1C(native_game_fd_50F6_10E6);
                if (f_171C_1E9A(native_game_fd_50F6_10E6)) {
                    h = f_171C_13CA((int32_t)n, 9, "emstiles");
                    p = f_171C_1B84(h);
                    _fmemcpy(p, f_171C_1B84(native_game_fd_50F6_10E6), n);
                } else {
                    h = 0;
                    p = f_171C_1B84(native_game_fd_50F6_10E6);
                }
                f_195A_00F8(g_19D0);
                f_195A_0122(g_19D0, 4, i < 3 ? g_19D2 : g_19E2);
                _fmemcpy(fd_55B3_360E + i % 3 * 0x5000, p, n);
                f_195A_010D(g_19D0);
                f_171C_1BBA(native_game_fd_50F6_10E6);
                if (h) {
                    f_171C_1BBA(h);
                    f_171C_1C0A(h);
                }
                db_PurgeObject(i + 15, 9);
            }
            native_game_fd_50F6_10E6 = 0;
        }
        break;
    case 2:
        g_19BE = g_19C0 = 12;
        fd_50F6_1102 = 2;
        break;
    case 3:
    case 5:
    case 7:
        fd_50F6_1102 = 3;
        break;
    }
}


void  f_0250_05CB(void)
{
    _fmemset(portable_eu_map_cache.rows, -1, 0x960);
}


void  f_0250_05EB(void)
{
    if (g_19D0) {
        f_195A_00F8(g_19D0);
        if (native_state_MapPlane.signed_value < 2)
            f_195A_0122(g_19D0, 4, g_19D2);
        else
            f_195A_0122(g_19D0, 4, g_19E2);
    }
}

void  f_0250_062A(void)
{
    if (g_19D0)
        f_195A_010D(g_19D0);
}

void  f_0250_0643(int16_t which)
{
    if (g_19D0 == 0) {
        if (which == 1) {
            if (native_game_fd_50F6_10EA) {
                db_ReleaseHandle(native_game_fd_50F6_10EA);
                native_game_fd_50F6_10EA = 0;
            }
            if (native_game_fd_50F6_10E6 == 0)
                native_game_fd_50F6_10E6 = f_1A53_00BA(13, 9);
        } else {
            if (native_game_fd_50F6_10E6) {
                db_ReleaseHandle(native_game_fd_50F6_10E6);
                native_game_fd_50F6_10E6 = 0;
            }
            if (native_game_fd_50F6_10EA == 0)
                native_game_fd_50F6_10EA = f_1A53_00BA(14, 9);
        }
    } else
        f_0250_05EB();
}


extern void  Punt(char  *format, ...);

extern void  o00_31AD_2FDA(int16_t x, int16_t y, int16_t col, int16_t row, char  *p);
extern void  o00_31AD_1B49(int16_t x, int16_t y, int16_t col, int16_t row, char  *p, int16_t mask);
extern void  o00_31AD_300B(int16_t x, int16_t y, int16_t col, int16_t row, char  *p, int16_t mask);
extern void  o03_3258_0690(int16_t x, int16_t y, char  *tile, char  *life, int16_t mask);
extern void  o01_3126_1343(int16_t x, int16_t y, char  *tile, char  *life, int16_t n);

void  f_0250_0721(int16_t x, int16_t y)
{
    static int16_t masks[3] = { 0, 3, 1 };
    int16_t row;
    int16_t col;
    int16_t flip;
    int16_t mask;
    char  *base;

    row = g_94E4 >> 6;
    col = ((g_94E4 & 0x3f) - 0x80) << 7;
    if (g_94E4 >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (g_9126 >= 0x380) {
        g_9126 -= 0x280;
        flip = 0;
    } else if (g_9126 >= 0x300) {
        g_9126 -= 0x200;
        flip = 1;
    } else if (g_9126 >= 0x200) {
        g_9126 -= 0x200;
        flip = 1;
    } else {
        g_9126 -= 0x100;
        flip = 0;
    }
    if (g_19D0 && fd_50F6_1102 == 1) {
        o00_31AD_2FDA(x & ~0xf, y, col, row, fd_55B3_360E + g_9126 * 0xa0);
        return;
    }
    base = *(flip == 1 ? native_game_fd_50F6_10E6 : native_game_fd_50F6_10EA);
    if (g_9126 >= 0xf0 && g_9126 <= 0xff)
        mask = masks[0];
    else
        mask = masks[g_9126 >> 7];
    if (fd_50F6_1102 == 1) {
        if (g_5A97 == 4)
            o00_31AD_1B49(x & ~0xf, y, col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
        else
            o00_31AD_300B(x & ~0xf, y, col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
    } else if (fd_50F6_1102 == 2)
        o03_3258_0690(x & ~1, y, *native_game_fd_50F6_10EE + g_94E4 * 0x48, base + (g_9126 & 0x7f) * 0x48, mask);
    else if (fd_50F6_1102 == 3)
        o01_3126_1343(x & ~7, y, *native_game_fd_50F6_10EE + (g_94E4 << 5), base + (g_9126 << 5), 0x3000 - ((g_9126 >> 7) << 12));
}

extern void  o00_31AD_2B1A(int16_t col, int16_t row, char  *p);
extern void  o00_31AD_1B7D(int16_t col, int16_t row, char  *p, int16_t mask);
extern void  o00_31AD_303F(int16_t col, int16_t row, char  *p, int16_t mask);
extern void  o03_3258_0F04(char  *tile, char  *life, int16_t mask);
extern void  o01_3126_14B6(char  *tile, char  *life, int16_t n);

void  f_0250_0915(void)
{
    static int16_t masks[3] = { 0, 3, 1 };
    int16_t row;
    int16_t col;
    int16_t flip;
    int16_t mask;
    char  *base;

    row = g_94E4 >> 6;
    col = ((g_94E4 & 0x3f) - 0x80) << 7;
    if (g_94E4 >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (g_9126 >= 0x380) {
        g_9126 -= 0x280;
        flip = 0;
    } else if (g_9126 >= 0x300) {
        g_9126 -= 0x200;
        flip = 1;
    } else if (g_9126 >= 0x200) {
        g_9126 -= 0x200;
        flip = 1;
    } else {
        g_9126 -= 0x100;
        flip = 0;
    }
    if (g_19D0 && fd_50F6_1102 == 1) {
        o00_31AD_2B1A(col, row, fd_55B3_360E + g_9126 * 0xa0);
        return;
    }
    base = *(flip == 1 ? native_game_fd_50F6_10E6 : native_game_fd_50F6_10EA);
    if (g_9126 >= 0xf0 && g_9126 <= 0xff)
        mask = masks[0];
    else
        mask = masks[g_9126 >> 7];
    if (fd_50F6_1102 == 1) {
        if (g_5A97 == 4)
            o00_31AD_1B7D(col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
        else
            o00_31AD_303F(col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
    } else if (fd_50F6_1102 == 2)
        o03_3258_0F04(*native_game_fd_50F6_10EE + g_94E4 * 0x48, base + (g_9126 & 0x7f) * 0x48, mask);
    else if (fd_50F6_1102 == 3)
        o01_3126_14B6(*native_game_fd_50F6_10EE + (g_94E4 << 5), base + (g_9126 << 5), 0x3000 - ((g_9126 >> 7) << 12));
}

extern void ( *  g_917C)(int16_t x, int16_t y, int16_t offset);
extern void ( *  g_914C)(int16_t x, int16_t y, char  *p, int16_t w, int16_t h);

void  f_0250_0ADB(int16_t x, int16_t y)
{
    if (g_94E4 >= 0x100)
        Punt("PutTile grndTile > 0x100");
    switch (fd_50F6_1102) {
    case 1:
        (*g_917C)(x, y, (g_94E4 - 0x300) << 5);
        break;
    case 2:
        (*g_914C)(x & ~1, y, *native_game_fd_50F6_10EE + g_94E4 * 0x48, 12, 12);
        break;
    case 3:
        (*g_914C)(x & ~0xf, y, *native_game_fd_50F6_10EE + (g_94E4 << 5), 16, 16);
        break;
    }
}

extern void  o00_31AD_1A8F(int16_t row, int16_t col);
extern char  g_3D20[];

void  f_0250_0B86(void)
{
    switch (fd_50F6_1102) {
    case 1:
        o00_31AD_1A8F(g_94E4 >> 6, ((g_94E4 & 0x3f) - 0x80) << 7);
        break;
    case 2:
        _fmemcpy(g_3D20, *native_game_fd_50F6_10EE + g_94E4 * 0x48, 0x48);
        break;
    case 3:
        _fmemcpy(g_3D20, *native_game_fd_50F6_10EE + (g_94E4 << 5), 0x20);
        break;
    }
}

extern void  clip_SetWin(int16_t win);
extern void  processEdit(struct Event  *event);
extern void  OpenMiniMapWin(void);
extern void  DoWinHelp(int16_t mode);
extern void  EditToolsMenu(void);
extern void  SetMapPlane(int16_t plane);
extern void  GotoMyAnt(void);
extern void  GotoSpider(void);
extern void  GotoBQueen(void);
extern void  GotoRQueen(void);
extern void  SetPause(int16_t pause);
extern void  EditScentMenu(void);
extern void  DoHealthSetY(struct Event  *event);
extern void  DoWarnSetB(struct Event  *event);
extern void  clip_Off(void);

void  ProcEditEvent(struct Event  *event)
{
    clip_SetWin(0);
    switch (event->code) {
    case 4:
    case 21:
        processEdit(event);
        break;
    case 5:
        OpenMiniMapWin();
        break;
    case 6:
        DoWinHelp(2);
        break;
    case 7:
        EditToolsMenu();
        break;
    case 8:
        SetMapPlane(1);
        break;
    case 9:
        SetMapPlane(2);
        break;
    case 10:
        SetMapPlane(3);
        break;
    case 11:
        GotoMyAnt();
        break;
    case 12:
        GotoSpider();
        break;
    case 13:
        GotoBQueen();
        break;
    case 14:
        GotoRQueen();
        break;
    case 15:
        SetPause(native_state_fd_50F6_047E.signed_value == 0);
        break;
    case 16:
        EditScentMenu();
        break;
    case 17:
        DoHealthSetY(event);
        break;
    case 18:
        DoWarnSetB(event);
        break;
    }
    clip_Off();
}

int16_t  f_0250_0D10(int16_t a, int16_t b);

void  f_0250_0CF6(int16_t a, int16_t b)
{
    f_0250_0D10(a, b);
}


void  f_0250_0F2C(void);
void  UpdateEdit(void);

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);

int16_t  f_0250_0D10(int16_t dx, int16_t dy)
{
    uint32_t error;
    int16_t i;
    uint32_t fraction;
    int16_t unused;
    int16_t yStep;
    int16_t xStep;
    int16_t xDistance;
    int16_t yDistance;

    if (dx == 0) {
        if (dy == 0)
            return 0;
    }
    xDistance = dx;
    xStep = 1;
    yStep = 1;
    yDistance = dy;
    error = 0;
    if (xDistance < 0) {
        xDistance = -xDistance;
        xStep = -1;
    }
    if (yDistance < 0) {
        yDistance = -yDistance;
        yStep = -1;
    }
    if (yDistance >= xDistance) {
        fraction = ((uint32_t)xDistance << 16) / yDistance;
        for (i = 0; i < yDistance; i++) {
            (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y += yStep;
            error += fraction;
            if ((error >> 16) & 1) {
                (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x += xStep;
                error ^= 0x10000L;
            }
        }
        f_0250_0F2C();
        UpdateEdit();
        return 1;
    } else {
        fraction = ((uint32_t)yDistance << 16) / xDistance;
        for (i = 0; i < xDistance; i++) {
            (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x += xStep;
            error += fraction;
            if ((error >> 16) & 1) {
                (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y += yStep;
                error ^= 0x10000L;
            }
        }
        f_0250_0F2C();
        UpdateEdit();
        return 1;
    }
}

void  f_0250_0E15(void)
{
    win_GetObjRect(4, &(*((struct Rect *)native_game_fd_50F6_110C.raw)));
    fd_50F6_10E0 = ((*((struct Rect *)native_game_fd_50F6_110C.raw)).right - (*((struct Rect *)native_game_fd_50F6_110C.raw)).left) / g_19BE;
    fd_50F6_10DE = ((*((struct Rect *)native_game_fd_50F6_110C.raw)).bottom - (*((struct Rect *)native_game_fd_50F6_110C.raw)).top) / g_19C0 + 1;
    f_0250_05CB();
    g_19CE = 1;
    f_0250_0F2C();
}

extern void  win_Open(int16_t win, ...);

void  OpenEditWindow(void)
{
    win_Open(0);
}

void  ForceUpdateEdit(void)
{
    f_0250_05CB();
    UpdateEdit();
}

void  DoEditUpdateDraw(void)
{
    ForceUpdateEdit();
}

extern int16_t  win_IsWinOpen(int16_t win);
void  f_0250_13A6(void);
void  DrawEditGraphs(void);
void  f_0250_13A6(void);
void  DrawEditGraphs(void);

void  UpdateEdit(void)
{
    if (win_IsWinOpen(0)) {
        clip_SetWin(0);
        f_0250_13A6();
        DrawEditGraphs();
        clip_Off();
    }
}

void  f_0250_0EC6(void)
{
    UpdateEdit();
}

void  f_0250_0ED2(void)
{
}

extern int16_t  fd_50F6_0EAC;
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  win_DrawBitMapAtObjNum(int16_t obj, int16_t id);

void  f_0250_0EDA(int16_t flags)
{
    int16_t id;

    if (flags & 2) {
        f_0250_0E15();
        f_0250_13A6();
        f_0250_0E15();
        if (fd_50F6_0EAC == 3)
            id = native_state_CurExpTool.signed_value + 0x13ec;
        else
            id = 0x13f3;
        win_SetColorFromObjNum(7);
        win_DrawBitMapAtObjNum(7, id);
    }
}

void  f_0250_0F2C(void)
{
    int16_t limit;
    int16_t ylimit;

    ylimit = 0x40;
    switch (native_state_MapPlane.signed_value) {
    case 0:
    case 1:
        limit = 0x80;
        break;
    default:
        limit = 0x40;
    }
    if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x < 0)
        (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x = 0;
    else if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x + fd_50F6_10E0 > limit)
        (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x = limit - fd_50F6_10E0;
    if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y < 0)
        (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y = 0;
    else if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + fd_50F6_10DE > ylimit)
        (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y = ylimit - fd_50F6_10DE;
}

void  CenterEdit(int16_t x, int16_t y)
{
    int16_t width;

    switch (native_state_MapPlane.signed_value) {
    case 0:
    case 1:
        width = 0x80;
        break;
    default:
        width = 0x40;
    }
    f_0250_0CF6(x - fd_50F6_10E0 / 2 - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x, y - fd_50F6_10DE / 2 - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y);
    f_0250_0F2C();
}

extern int16_t  fd_3D57_07BE;
extern uint8_t  PherMapA[64][32];
extern uint8_t  PherMapBN[64][32];
extern uint8_t  PherMapBT[64][32];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapRT[64][32];
extern uint8_t  MapA[128][64];
extern uint8_t  LifeA[128][64];
extern int16_t  fd_50F6_04C2;
extern int16_t  fd_50F6_0496;
extern uint8_t  MapB[64][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  MapR[64][64];
extern uint8_t  LifeR[64][64];

/* OPEN (unclaimed draft, kept in place for CONST/_DATA order and identifier counts):
 * residue: the original keeps the tile value v in [bp-2] (memory) and mx/my in SI/DI with a
 * 4-byte frame; here v wins SI.  Taking &v reproduces the allocation (not adopted).  The
 * sums fd_049A+fd_04C2(+fd_0496) load in the original order only with one declaration
 * between fd_049A and fd_04C2 (mod-17 symbol order). */

/* SCAFFOLD BEGIN: unclaimed f_0250_1018; retained whole-module context */

void  f_0250_1018(int16_t x, int16_t y)
{
    int16_t v;
    int16_t mx;
    int16_t my;

    mx = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x + x;
    my = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + y;
    if (my > 0x3f) {
        mx += 0x40;
        my &= 0x3f;
    }
    g_94E4 = 0;
    g_9126 = 0;
    switch (native_state_MapPlane.signed_value) {
    case 0:
    case 1:
        mx &= 0x7f;
        switch (fd_3D57_07BE) {
        case 0:
            v = PherMapA[mx >> 1][my >> 1];
            break;
        case 1:
            v = PherMapBN[mx >> 1][my >> 1];
            break;
        case 2:
            v = PherMapBT[mx >> 1][my >> 1];
            break;
        case 3:
            v = PherMapRN[mx >> 1][my >> 1];
            break;
        case 4:
            v = PherMapRT[mx >> 1][my >> 1];
            break;
        default:
            goto noscent;
        }
        if (v > 0x10)
            g_94E4 = ((v >> 4) & 0x1f) - 0x10;
        else
            g_94E4 = 0;
noscent:
        if (g_94E4 == 0)
            g_94E4 = MapA[mx][my];
        v = LifeA[mx][my];
        if (v == 0)
            return;
        if (v == 0xff) {
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_04C2 + 0x380;
            if (fd_50F6_04C2 < 8)
                g_9126 += native_state_fd_50F6_0502.signed_value;
            else
                g_9126 += fd_50F6_0496;
        } else if (v == 0xfe)
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_0496 + fd_50F6_04C2 + 0x388;
        else
            g_9126 = v + 0x100;
        break;
    case 2:
        mx &= 0x3f;
        g_94E4 = MapB[mx][my] - 0x70;
        v = LifeB[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_0496 + fd_50F6_04C2 + 0x308;
            break;
        case 0xff:
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_04C2 + 0x300;
            if (fd_50F6_04C2 < 8)
                g_9126 += native_state_fd_50F6_0502.signed_value;
            else
                g_9126 += fd_50F6_0496;
            break;
        default:
            g_9126 = v + 0x200;
        }
        break;
    case 3:
        mx &= 0x3f;
        g_94E4 = MapR[mx][my] - 0x70;
        v = LifeR[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_0496 + fd_50F6_04C2 + 0x308;
            break;
        case 0xff:
            g_9126 = native_state_fd_50F6_049A.signed_value + fd_50F6_04C2 + 0x300;
            if (fd_50F6_04C2 < 8)
                g_9126 += native_state_fd_50F6_0502.signed_value;
            else
                g_9126 += fd_50F6_0496;
            break;
        default:
            g_9126 = v + 0x200;
        }
        break;
    }
}
/* SCAFFOLD END */

extern uint8_t  fd_50F6_1114[30 * 40];

/* OPEN: residue 2 extra frame words ([bp-2],[bp-4]) and SI/DI swapped (y param in DI,
 * index in SI in the original). */
/* SCAFFOLD BEGIN: unclaimed f_0250_129E; retained whole-module context */
void  f_0250_129E(int16_t x, int16_t y)
{
    int16_t ay;
    int16_t i;
    int16_t  *p;

    ay = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + y;
    if (x < 0 || y < 0 || x >= 40 || y >= 30)
        return;
    if (ay > 0x3f)
        Punt("Y>MAXAY");
    f_0250_1018(x, y);
    i = y * 40 + x;
    if (portable_eu_map_cache.linear[i] == -2) {
        portable_eu_map_cache.linear[i]++;
        return;
    }
    p = &portable_eu_map_cache.linear[i];
    if (*p != g_9126 || fd_50F6_1114[i] != g_94E4 || (y == 0 && g_19CE != 0)) {
        if (g_9126)
            f_0250_0721(g_19BE * x + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left, g_19C0 * y + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top);
        else
            f_0250_0ADB(g_19BE * x + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left, y * g_19C0 + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top);
        *p = g_9126;
        fd_50F6_1114[i] = g_94E4;
    }
}
/* SCAFFOLD END */

extern void  clip_Push(void);
void  f_0250_5058(void);
extern int32_t  TickCount(void);
extern void  win_SetColorNum(int16_t color);
extern void  f_15D9_0006(char  *msg, struct Rect  *rect, int16_t y);
void  PreDrawSpider(void);
void  PreDrawBalloons(void);
extern int16_t  fd_50F6_37D2;
void  DrawSpider(void);
void  DrawBalloons(void);
extern int16_t  fd_50F6_37D4;
extern void  f_1B4E_003B(int16_t x, int16_t y, char  *image);


static struct Rect balTileRect;
static struct Rect balloonRect;
static Handle balBufHandle;
static Pnt edPenPos;
static char  *balBufPtr;

extern void  clip_Pop(void);

/* px and py are never read: their stepping keeps the dead loads of editRect.left/top (and of
 * g_19C0) alive.  The px step constant is not decided by the bytes (px += 16 is a hypothesis;
 * px++ compiles identically).  balloon = spider = 0 stores spider first (worker resG). */
void  f_0250_13A6(void)
{
    int16_t spider;
    int16_t balloon;
    int16_t x;
    int16_t y;
    int16_t px;
    int16_t py;

    balloon = spider = 0;
    clip_Push();
    f_0250_5058();
    if (g_19C6) {
        if (TickCount() > g_19CA) {
            if (g_19C6)
                g_19CE = 1;
            g_19C6 = 0;
        } else {
            win_SetColorNum(3);
            f_15D9_0006(g_19C6, &(*((struct Rect *)native_game_fd_50F6_110C.raw)), (*((struct Rect *)native_game_fd_50F6_110C.raw)).top + 4);
        }
    }
    PreDrawSpider();
    PreDrawBalloons();
    if (fd_50F6_37D2 != 500)
        DrawSpider();
    DrawBalloons();
    f_0250_0643(native_state_MapPlane.signed_value / 2);
    py = (*((struct Rect *)native_game_fd_50F6_110C.raw)).top;
    for (y = 0; y < fd_50F6_10DE; y++, py += g_19C0) {
        px = (*((struct Rect *)native_game_fd_50F6_110C.raw)).left;
        for (x = 0; x < fd_50F6_10E0; x++, px += 16) {
            if (x >= balTileRect.left && x < balTileRect.right && y >= balTileRect.top && y < balTileRect.bottom)
                goto drawballoon;
            if ((y >= fd_50F6_37D4 && y < fd_50F6_37D4 + 7 && x >= fd_50F6_37D2 && x < fd_50F6_37D2 + 7)
                || (y == fd_50F6_10DE - 1 && x == fd_50F6_10E0 - 1)) {
                if (spider)
                    continue;
                f_1B4E_003B(fd_50F6_37D6.left, fd_50F6_37D6.top, (char  *)&portable_line16b5_source_buffer);
                spider = 1;
                if (balTileRect.left == 500)
                    continue;
            drawballoon:
                if (balloon)
                    continue;
                f_1B4E_003B(balloonRect.left, balloonRect.top, balBufPtr);
                balloon = 1;
                continue;
            }
            f_0250_129E(x, y);
        }
    }
    f_0250_062A();
    if (balTileRect.left != 500) {
        f_171C_1BBA(balBufHandle);
        f_171C_1C0A(balBufHandle);
    }
    clip_Pop();
    g_19CE = 0;
}

extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);
extern void  f_1CE2_044D(struct Rect  *rect, int16_t width);
extern void  f_1CE2_0430(struct Rect  *rect);

/* h is computed from r before top is copied: /Og then sinks h = r.bottom - r.top into the
 * __aFlmul argument list (after the 0x10000L and frac pushes) as in the original.  The three
 * vals[] stores share one source line: the /Zi line-entry flush must fall after 16BA
 * (records.py FORBID (1680,16BA]); line layout is a hypothesis (worker resG). */
void  DrawEditGraphs(void)
{
    static int16_t objs[3] = { 0x11, 0x12, 0x13 };
    int16_t obj;
    int16_t h;
    int32_t frac;
    struct Rect r;
    int16_t  *vals[3];
    int16_t i;
    int16_t top;

    vals[0] = &native_state_MeHealth.signed_value; vals[1] = &native_state_HealthB.signed_value; vals[2] = &native_state_HealthR.signed_value;
    for (i = 0; i < 3; i++) {
        obj = objs[i];
        frac = ((int32_t)*vals[i] << 16) / 100;
        win_SetColorFromObjNum(obj);
        win_GetObjRect(obj, &r);
        h = r.bottom - r.top;
        top = r.top;
        r.top = r.bottom - (int16_t)(h * frac / 0x10000L);
        if (r.top < r.bottom) {
            f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE0);
            if ((g_5A97 & 1) && i == 0) {
                (*g_9128)(0, 0, 0);
                f_1CE2_044D(&r, 1);
                win_SetColorFromObjNum(obj);
            }
        }
        if (r.top > top) {
            r.bottom = r.top;
            r.top = top;
            f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE2);
        }
        if (i == 0) {
            r.top = (100 - native_state_fd_50F6_0FBA.signed_value) * h / 100 + top;
            r.bottom = r.top + 1;
            f_1CE2_046D(&r, f_1B4E_000D(15));
        }
        if (i == 1) {
            r.top = (100 - native_state_fd_50F6_0FFE.signed_value) * h / 100 + top;
            r.bottom = r.top + 1;
            f_1CE2_0430(&r);
        }
    }
}

extern char  *  *  fd_50F6_0368;

extern char  *  *  fd_50F6_0324;
extern void  win_SetObjFormatStr(int16_t obj, char  *text);
extern void  win_DrawTitle(int16_t obj);

void  SetEditWinTitle(void)
{
    char buf[80];

    _fstrcpy(buf, "SimAnt");
    _fstrcat(buf, fd_50F6_0368[15]);
    _fstrcat(buf, fd_50F6_0324[fd_50F6_0EAC]);
    win_SetObjFormatStr(1, buf);
    if (win_IsWinOpen(0)) {
        clip_Push();
        clip_SetWin(0);
        win_DrawTitle(1);
        clip_Pop();
    }
}


void  PreDrawSpider(void)
{
    int16_t x, y, px, py;
    int16_t sx, sy;

    fd_50F6_37D6.top = 0x8000;
    fd_50F6_37D2 = 500;
    fd_50F6_37D4 = 500;
    if (!native_state_fd_50F6_0F0C.signed_value)
        return;
    y = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
    x = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
    px = x * g_19BE;
    py = y * g_19C0;
    sx = native_state_fd_50F6_0F12.signed_value;
    sy = native_state_fd_50F6_0F34.signed_value;
    if (g_5A97 == 2) {
        sx = sx * 3 / 4;
        sy = sy * 3 / 4;
    }
    if (native_state_MapPlane.signed_value != 1)
        return;
    if (px > sx)
        return;
    if (fd_50F6_10E0 * g_19BE + px < sx)
        return;
    if (py > sy)
        return;
    if (fd_50F6_10DE * g_19C0 + py < sy)
        return;
    portable_line16b5_source_buffer.x = 7 * g_19BE;
    portable_line16b5_source_buffer.y = 7 * g_19C0;
    fd_50F6_37D2 = native_state_fd_50F6_0F12.signed_value / 16 - x - 3;
    fd_50F6_37D4 = native_state_fd_50F6_0F34.signed_value / 16 - y - 3;
}

void  DrawEditGraphs(void);
extern void  f_2662_1120(int16_t x, int16_t y, char  *buf, int16_t id);
void  DrawLegs(int16_t x, int16_t y, int16_t dir, int16_t frame);
void  DrawPalps(int16_t x, int16_t y, int16_t dir);
extern void  f_16B5_0033(void  *buf, int16_t mode);
extern char  fd_3D57_09CC[];
extern char  fd_3D57_09D0[];
extern char  fd_3D57_09BC[];
extern char  fd_3D57_09C4[];
extern int16_t  fd_3D57_07B2;
extern int32_t  fd_3D57_098E;
extern int16_t  SRand64(void);
extern int16_t  SRand2(void);
extern int16_t  fd_50F6_0D6E;
extern int16_t  fd_3D57_0992;
extern int16_t  fd_50F6_0EB4;
extern char  *  *  fd_50F6_10B4;
extern char  Dy8[8];
extern char  Dx8[8];
extern int16_t  SRand32(void);
void  AddMsgBalloon(int16_t x, int16_t y, int16_t plane, int16_t style, char  *msg);

/*sx,sy,mx,my,l,t*/
/* OPEN: residue register/slot allocation (px in SI, lx/ly in [bp-2]/[bp-4]), statement
 * scheduling of the SpidX/SpidY block and TickCount()/fd_098E compare operand order.
 * NOTE: its local identifier count is load-bearing for later claims (keep 18). */
void  DrawSpider(void)
{
    int16_t py;
    int16_t top;
    int16_t left;
    int16_t ty;
    int16_t j;
    int16_t skip;
    int16_t modx;
    int16_t mody;
    int16_t i;
    int16_t w;
    char  *p;
    int16_t sx;
    int16_t lx;
    int16_t ly;
    int16_t px;

    px = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x * g_19BE;
    py = (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y * g_19C0;
    if (g_5A97 == 2) {
        sx = native_state_fd_50F6_0F12.signed_value * 3 / 4;
        modx = sx % 12;
        mody = (native_state_fd_50F6_0F34.signed_value * 3 / 4) % 12;
        left = sx - modx + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left - px - 0x24;
        top = native_state_fd_50F6_0F34.signed_value * 3 / 4 - mody + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top - py - 0x24;
    } else {
        modx = native_state_fd_50F6_0F12.signed_value & 0xf;
        mody = native_state_fd_50F6_0F34.signed_value & 0xf;
        left = native_state_fd_50F6_0F12.signed_value - modx + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left - px - 0x30;
        top = native_state_fd_50F6_0F34.signed_value - mody + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top - py - 0x30;
    }
    fd_50F6_37D6.left = left;
    fd_50F6_37D6.top = top;
    fd_50F6_37D6.bottom = top + portable_line16b5_source_buffer.y;
    fd_50F6_37D6.right = left + portable_line16b5_source_buffer.x;
    f_0250_0643(native_state_MapPlane.signed_value / 2);
    w = 2;
    switch (fd_50F6_1102) {
    case 2:
        w = 6;
    case 1:
        skip = 2;
        break;
    case 3:
        skip = 8;
        break;
    }
    skip = g_19C0 / skip * portable_line16b5_source_buffer.x - w * 7;
    p = (char  *)&portable_line16b5_source_buffer + 4;
    for (j = 0, ty = fd_50F6_37D4; j < 7; j++, ty++, p += skip) {
        int16_t tx;
        int16_t n;
        int16_t idx;

        for (idx = ty * 40 + (tx = fd_50F6_37D2), n = 0; n < 7; n++, tx++, p += w, idx++) {
            f_0250_1018(tx, ty);
            if (idx >= 0 && idx < 1200)
                portable_eu_map_cache.linear[idx] = -1;
            if (g_9126)
                f_0250_0915();
            else
                f_0250_0B86();
            (*fd_50F6_37E6)(p, portable_line16b5_source_buffer.x);
        }
    }
    f_0250_062A();
    (g_5A97 & 1) ? f_16B5_0033((char  *)&portable_line16b5_source_buffer, 0) : (g_5A97 == 2 ? f_16B5_0033((char  *)&portable_line16b5_source_buffer, 1) : f_16B5_0033((char  *)&portable_line16b5_source_buffer, 2));
    if (native_state_SMode.signed_value == 5) {
        lx = fd_3D57_09CC[native_state_Scycle.signed_value] + 0x30;
        ly = fd_3D57_09D0[native_state_Scycle.signed_value] + 0x30;
        if (g_5A97 == 2) {
            lx = lx * 3 / 4 + modx;
            ly = ly * 3 / 4 + mody;
        } else {
            lx += modx;
            ly += mody;
        }
        f_2662_1120(lx, ly, (char  *)&portable_line16b5_source_buffer, native_state_Scycle.signed_value + 0x41a);
    } else {
        lx = fd_3D57_09BC[native_state_fd_50F6_1004.signed_value] + 0x30;
        ly = fd_3D57_09C4[native_state_fd_50F6_1004.signed_value] + 0x30;
        if (g_5A97 == 2) {
            f_2662_1120(lx = lx * 3 / 4 + modx, ly = ly * 3 / 4 + mody, (char  *)&portable_line16b5_source_buffer, native_state_fd_50F6_1004.signed_value + 1000);
            DrawLegs((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, native_state_fd_50F6_1004.signed_value, native_state_Scycle.signed_value & 7);
            DrawPalps((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, native_state_fd_50F6_1004.signed_value);
        } else {
            f_2662_1120(modx + lx, mody + ly, (char  *)&portable_line16b5_source_buffer, native_state_fd_50F6_1004.signed_value + 1000);
            DrawLegs(modx + 0x30, mody + 0x30, native_state_fd_50F6_1004.signed_value, native_state_Scycle.signed_value & 7);
            DrawPalps(modx + 0x30, mody + 0x30, native_state_fd_50F6_1004.signed_value);
        }
    }
    if (fd_3D57_07B2) {
        if (native_state_fd_50F6_047E.signed_value == 0 && fd_3D57_098E < TickCount()) {
            fd_3D57_098E = TickCount() + SRand64() + 180;
            if (SRand2() == 0) {
                fd_50F6_0D6E = 1;
                if (++fd_3D57_0992 >= 5)
                    fd_3D57_0992 = 0;
            } else
                fd_50F6_0D6E = 0;
        }
        if (native_state_SMode.signed_value == fd_50F6_0EB4 && native_state_SMode.signed_value <= 4) {
            if (fd_50F6_0D6E)
                AddMsgBalloon((Dx8[native_state_fd_50F6_1004.signed_value] << 3) + native_state_fd_50F6_0F12.signed_value, (Dy8[native_state_fd_50F6_1004.signed_value] << 3) + native_state_fd_50F6_0F34.signed_value, 1, 10,
                              fd_50F6_10B4[native_state_SMode.signed_value * 5 + fd_3D57_0992]);
        } else {
            fd_3D57_098E = TickCount() + SRand32() + 30;
            fd_50F6_0D6E = 0;
            fd_50F6_0EB4 = native_state_SMode.signed_value;
        }
    }
}

extern int16_t  fd_3D57_0C30;
extern int16_t  fd_3D57_0C28;

/* OPEN: residue commutative operand order MapPnt.x + EditColumns (original loads the
 * MapPnt member first) - structural, not changed by names or preceding declaration counts. */
void  f_0250_1E80(void)
{
    int16_t x;
    int16_t y;
    int16_t t;

    if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x + fd_50F6_10E0 >= native_state_fd_50F6_03E0.signed_value && native_state_fd_50F6_03E0.signed_value + 15 >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x
        && (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + fd_50F6_10DE >= native_state_fd_50F6_046A.signed_value && native_state_fd_50F6_046A.signed_value + 15 >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y) {
        x = (native_state_fd_50F6_03E0.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x) * g_19BE + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left;
        y = (native_state_fd_50F6_046A.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y) * g_19C0 + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top;
        (*g_9134)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x10);
        x = native_state_fd_50F6_03E0.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        y = native_state_fd_50F6_046A.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        if (fd_3D57_0C30 & 1)
            InvalEuMap(x, y, x + 16, y + 6);
        else
            InvalEuMap(x, y, x + 6, y + 16);
        if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
            if ((*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x + fd_50F6_10E0 >= native_state_fd_50F6_0470.signed_value && native_state_fd_50F6_0470.signed_value + 0x1b >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x
                && (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + fd_50F6_10DE >= native_state_fd_50F6_047A.signed_value && native_state_fd_50F6_047A.signed_value + 0x1b >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x) {
                x = (native_state_fd_50F6_0470.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x) * g_19BE + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left;
                y = (native_state_fd_50F6_047A.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y) * g_19C0 + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top;
                (*g_9134)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x20);
                x = native_state_fd_50F6_0470.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
                y = native_state_fd_50F6_047A.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
                InvalEuMap(x, y, x + 0x1b, y + 0x1b);
            }
        }
    }
}

void  ed_MoveTo(int16_t x, int16_t y)
{
    if (g_5A97 == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    edPenPos.x = x;
    edPenPos.y = y;
}

extern void  f_16B5_0008(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t color);

void  ed_LineTo(int16_t x, int16_t y)
{
    if (g_5A97 == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    f_16B5_0008(edPenPos.x, edPenPos.y, x, y, SIM_GRAPHICS_SOURCE_g_3DE0);
    edPenPos.x = x;
    edPenPos.y = y;
}

extern int16_t  SRand1(int16_t range);
extern int16_t  fd_50F6_0A06;
extern char  fd_3D57_09E8[4];
extern char  fd_3D57_09E4[4];
extern char  fd_3D57_09F0[4];
extern char  fd_3D57_09EC[4];
extern char  fd_3D57_09F8[4];
extern char  fd_3D57_09F4[4];
extern char  fd_3D57_0A00[4];
extern char  fd_3D57_09FC[4];
void  DrawPalps(int16_t x, int16_t y, int16_t dir)
{
    int16_t r;

    if (native_state_SMode.signed_value <= 1 && native_state_fd_50F6_06AC.signed_value < 6)
        r = 0;
    else
        r = SRand1(4);
    if (fd_50F6_0A06 == 1)
        (*g_9128)(f_1B4E_000D(1), 0, 0);
    else
        (*g_9128)(f_1B4E_000D(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + 4, y - 10);
        ed_LineTo(x + fd_3D57_09E4[r], y + fd_3D57_09E8[r]);
        ed_LineTo(x + fd_3D57_09EC[r], y + fd_3D57_09F0[r]);
        ed_MoveTo(x - 4, y - 10);
        ed_LineTo(x - fd_3D57_09E4[r], y + fd_3D57_09E8[r]);
        ed_LineTo(x - fd_3D57_09EC[r], y + fd_3D57_09F0[r]);
        break;
    case 1:
        ed_MoveTo(x + 10, y - 3);
        ed_LineTo(x + fd_3D57_09F4[r], y + fd_3D57_09F8[r]);
        ed_LineTo(x + fd_3D57_09FC[r], y + fd_3D57_0A00[r]);
        ed_MoveTo(x + 3, y - 10);
        ed_LineTo(x - fd_3D57_09F8[r], y - fd_3D57_09F4[r]);
        ed_LineTo(x - fd_3D57_0A00[r], y - fd_3D57_09FC[r]);
        break;
    case 2:
        ed_MoveTo(x + 10, y - 4);
        ed_LineTo(x - fd_3D57_09E8[r], y - fd_3D57_09E4[r]);
        ed_LineTo(x - fd_3D57_09F0[r], y - fd_3D57_09EC[r]);
        ed_MoveTo(x + 10, y + 4);
        ed_LineTo(x - fd_3D57_09E8[r], y + fd_3D57_09E4[r]);
        ed_LineTo(x - fd_3D57_09F0[r], y + fd_3D57_09EC[r]);
        break;
    case 3:
        ed_MoveTo(x + 10, y + 3);
        ed_LineTo(x + fd_3D57_09F4[r], y - fd_3D57_09F8[r]);
        ed_LineTo(x + fd_3D57_09FC[r], y - fd_3D57_0A00[r]);
        ed_MoveTo(x + 3, y + 10);
        ed_LineTo(x - fd_3D57_09F8[r], y + fd_3D57_09F4[r]);
        ed_LineTo(x - fd_3D57_0A00[r], y + fd_3D57_09FC[r]);
        break;
    case 4:
        ed_MoveTo(x + 4, y + 10);
        ed_LineTo(x + fd_3D57_09E4[r], y - fd_3D57_09E8[r]);
        ed_LineTo(x + fd_3D57_09EC[r], y - fd_3D57_09F0[r]);
        ed_MoveTo(x - 4, y + 10);
        ed_LineTo(x - fd_3D57_09E4[r], y - fd_3D57_09E8[r]);
        ed_LineTo(x - fd_3D57_09EC[r], y - fd_3D57_09F0[r]);
        break;
    case 5:
        ed_MoveTo(x - 10, y + 3);
        ed_LineTo(x - fd_3D57_09F4[r], y - fd_3D57_09F8[r]);
        ed_LineTo(x - fd_3D57_09FC[r], y - fd_3D57_0A00[r]);
        ed_MoveTo(x - 3, y + 10);
        ed_LineTo(x + fd_3D57_09F8[r], y + fd_3D57_09F4[r]);
        ed_LineTo(x + fd_3D57_0A00[r], y + fd_3D57_09FC[r]);
        break;
    case 6:
        ed_MoveTo(x - 10, y - 4);
        ed_LineTo(x + fd_3D57_09E8[r], y - fd_3D57_09E4[r]);
        ed_LineTo(x + fd_3D57_09F0[r], y - fd_3D57_09EC[r]);
        ed_MoveTo(x - 10, y + 4);
        ed_LineTo(x + fd_3D57_09E8[r], y + fd_3D57_09E4[r]);
        ed_LineTo(x + fd_3D57_09F0[r], y + fd_3D57_09EC[r]);
        break;
    case 7:
        ed_MoveTo(x - 10, y - 3);
        ed_LineTo(x - fd_3D57_09F4[r], y + fd_3D57_09F8[r]);
        ed_LineTo(x - fd_3D57_09FC[r], y + fd_3D57_0A00[r]);
        ed_MoveTo(x - 3, y - 10);
        ed_LineTo(x + fd_3D57_09F8[r], y - fd_3D57_09F4[r]);
        ed_LineTo(x + fd_3D57_0A00[r], y - fd_3D57_09FC[r]);
        break;
    }
}

extern char  fd_3D57_0A08[4];
extern char  fd_3D57_0A04[4];
extern char  fd_3D57_0A4C[8];
extern char  fd_3D57_0A0C[8];
extern char  fd_3D57_0A54[8];
extern char  fd_3D57_0A14[8];
extern char  fd_3D57_0A5C[8];
extern char  fd_3D57_0A1C[8];
extern char  fd_3D57_0A64[8];
extern char  fd_3D57_0A24[8];
extern char  fd_3D57_0A6C[8];
extern char  fd_3D57_0A2C[8];
extern char  fd_3D57_0A74[8];
extern char  fd_3D57_0A34[8];
extern char  fd_3D57_0A7C[8];
extern char  fd_3D57_0A3C[8];
extern char  fd_3D57_0A84[8];
extern char  fd_3D57_0A44[8];
extern char  fd_3D57_0A90[4];
extern char  fd_3D57_0A8C[4];
extern char  fd_3D57_0A9C[8];
extern char  fd_3D57_0A94[8];
extern char  fd_3D57_0ADC[8];
extern char  fd_3D57_0AD4[8];
extern char  fd_3D57_0AAC[8];
extern char  fd_3D57_0AA4[8];
extern char  fd_3D57_0AEC[8];
extern char  fd_3D57_0AE4[8];
extern char  fd_3D57_0ABC[8];
extern char  fd_3D57_0AB4[8];
extern char  fd_3D57_0AFC[8];
extern char  fd_3D57_0AF4[8];
extern char  fd_3D57_0ACC[8];
extern char  fd_3D57_0AC4[8];
extern char  fd_3D57_0B0C[8];
extern char  fd_3D57_0B04[8];
void  DrawLegs(int16_t x, int16_t y, int16_t dir, int16_t frame)
{
    int16_t other;

    other = (frame + 4) & 7;
    (*g_9128)(f_1B4E_000D(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + fd_3D57_0A04[0], y + fd_3D57_0A08[0]);
        ed_LineTo(x + fd_3D57_0A0C[frame], y + fd_3D57_0A4C[frame]);
        ed_LineTo(x + fd_3D57_0A14[frame], y + fd_3D57_0A54[frame]);
        ed_MoveTo(x + fd_3D57_0A04[1], y + fd_3D57_0A08[1]);
        ed_LineTo(x + fd_3D57_0A1C[frame], y + fd_3D57_0A5C[frame]);
        ed_LineTo(x + fd_3D57_0A24[frame], y + fd_3D57_0A64[frame]);
        ed_MoveTo(x + fd_3D57_0A04[2], y + fd_3D57_0A08[2]);
        ed_LineTo(x + fd_3D57_0A2C[frame], y + fd_3D57_0A6C[frame]);
        ed_LineTo(x + fd_3D57_0A34[frame], y + fd_3D57_0A74[frame]);
        ed_MoveTo(x + fd_3D57_0A04[3], y + fd_3D57_0A08[3]);
        ed_LineTo(x + fd_3D57_0A3C[frame], y + fd_3D57_0A7C[frame]);
        ed_LineTo(x + fd_3D57_0A44[frame], y + fd_3D57_0A84[frame]);
        ed_MoveTo(x - fd_3D57_0A04[0], y + fd_3D57_0A08[0]);
        ed_LineTo(x - fd_3D57_0A0C[other], y + fd_3D57_0A4C[other]);
        ed_LineTo(x - fd_3D57_0A14[other], y + fd_3D57_0A54[other]);
        ed_MoveTo(x - fd_3D57_0A04[1], y + fd_3D57_0A08[1]);
        ed_LineTo(x - fd_3D57_0A1C[other], y + fd_3D57_0A5C[other]);
        ed_LineTo(x - fd_3D57_0A24[other], y + fd_3D57_0A64[other]);
        ed_MoveTo(x - fd_3D57_0A04[2], y + fd_3D57_0A08[2]);
        ed_LineTo(x - fd_3D57_0A2C[other], y + fd_3D57_0A6C[other]);
        ed_LineTo(x - fd_3D57_0A34[other], y + fd_3D57_0A74[other]);
        ed_MoveTo(x - fd_3D57_0A04[3], y + fd_3D57_0A08[3]);
        ed_LineTo(x - fd_3D57_0A3C[other], y + fd_3D57_0A7C[other]);
        ed_LineTo(x - fd_3D57_0A44[other], y + fd_3D57_0A84[other]);
        break;
    case 1:
        ed_MoveTo(x + fd_3D57_0A8C[0], y + fd_3D57_0A90[0]);
        ed_LineTo(x + fd_3D57_0A94[frame], y + fd_3D57_0A9C[frame]);
        ed_LineTo(x + fd_3D57_0AD4[frame], y + fd_3D57_0ADC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y + fd_3D57_0A90[1]);
        ed_LineTo(x + fd_3D57_0AA4[frame], y + fd_3D57_0AAC[frame]);
        ed_LineTo(x + fd_3D57_0AE4[frame], y + fd_3D57_0AEC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y + fd_3D57_0A90[2]);
        ed_LineTo(x + fd_3D57_0AB4[frame], y + fd_3D57_0ABC[frame]);
        ed_LineTo(x + fd_3D57_0AF4[frame], y + fd_3D57_0AFC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y + fd_3D57_0A90[3]);
        ed_LineTo(x + fd_3D57_0AC4[frame], y + fd_3D57_0ACC[frame]);
        ed_LineTo(x + fd_3D57_0B04[frame], y + fd_3D57_0B0C[frame]);
        ed_MoveTo(x - fd_3D57_0A90[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x - fd_3D57_0A9C[other], y - fd_3D57_0A94[other]);
        ed_LineTo(x - fd_3D57_0ADC[other], y - fd_3D57_0AD4[other]);
        ed_MoveTo(x - fd_3D57_0A90[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x - fd_3D57_0AAC[other], y - fd_3D57_0AA4[other]);
        ed_LineTo(x - fd_3D57_0AEC[other], y - fd_3D57_0AE4[other]);
        ed_MoveTo(x - fd_3D57_0A90[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x - fd_3D57_0ABC[other], y - fd_3D57_0AB4[other]);
        ed_LineTo(x - fd_3D57_0AFC[other], y - fd_3D57_0AF4[other]);
        ed_MoveTo(x - fd_3D57_0A90[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x - fd_3D57_0ACC[other], y - fd_3D57_0AC4[other]);
        ed_LineTo(x - fd_3D57_0B0C[other], y - fd_3D57_0B04[other]);
        break;
    case 2:
        ed_MoveTo(x - fd_3D57_0A08[0], y + fd_3D57_0A04[0]);
        ed_LineTo(x - fd_3D57_0A4C[frame], y + fd_3D57_0A0C[frame]);
        ed_LineTo(x - fd_3D57_0A54[frame], y + fd_3D57_0A14[frame]);
        ed_MoveTo(x - fd_3D57_0A08[1], y + fd_3D57_0A04[1]);
        ed_LineTo(x - fd_3D57_0A5C[frame], y + fd_3D57_0A1C[frame]);
        ed_LineTo(x - fd_3D57_0A64[frame], y + fd_3D57_0A24[frame]);
        ed_MoveTo(x - fd_3D57_0A08[2], y + fd_3D57_0A04[2]);
        ed_LineTo(x - fd_3D57_0A6C[frame], y + fd_3D57_0A2C[frame]);
        ed_LineTo(x - fd_3D57_0A74[frame], y + fd_3D57_0A34[frame]);
        ed_MoveTo(x - fd_3D57_0A08[3], y + fd_3D57_0A04[3]);
        ed_LineTo(x - fd_3D57_0A7C[frame], y + fd_3D57_0A3C[frame]);
        ed_LineTo(x - fd_3D57_0A84[frame], y + fd_3D57_0A44[frame]);
        ed_MoveTo(x - fd_3D57_0A08[0], y - fd_3D57_0A04[0]);
        ed_LineTo(x - fd_3D57_0A4C[other], y - fd_3D57_0A0C[other]);
        ed_LineTo(x - fd_3D57_0A54[other], y - fd_3D57_0A14[other]);
        ed_MoveTo(x - fd_3D57_0A08[1], y - fd_3D57_0A04[1]);
        ed_LineTo(x - fd_3D57_0A5C[other], y - fd_3D57_0A1C[other]);
        ed_LineTo(x - fd_3D57_0A64[other], y - fd_3D57_0A24[other]);
        ed_MoveTo(x - fd_3D57_0A08[2], y - fd_3D57_0A04[2]);
        ed_LineTo(x - fd_3D57_0A6C[other], y - fd_3D57_0A2C[other]);
        ed_LineTo(x - fd_3D57_0A74[other], y - fd_3D57_0A34[other]);
        ed_MoveTo(x - fd_3D57_0A08[3], y - fd_3D57_0A04[3]);
        ed_LineTo(x - fd_3D57_0A7C[other], y - fd_3D57_0A3C[other]);
        ed_LineTo(x - fd_3D57_0A84[other], y - fd_3D57_0A44[other]);
        break;
    case 3:
        ed_MoveTo(x + fd_3D57_0A8C[0], y - fd_3D57_0A90[0]);
        ed_LineTo(x + fd_3D57_0A94[frame], y - fd_3D57_0A9C[frame]);
        ed_LineTo(x + fd_3D57_0AD4[frame], y - fd_3D57_0ADC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y - fd_3D57_0A90[1]);
        ed_LineTo(x + fd_3D57_0AA4[frame], y - fd_3D57_0AAC[frame]);
        ed_LineTo(x + fd_3D57_0AE4[frame], y - fd_3D57_0AEC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y - fd_3D57_0A90[2]);
        ed_LineTo(x + fd_3D57_0AB4[frame], y - fd_3D57_0ABC[frame]);
        ed_LineTo(x + fd_3D57_0AF4[frame], y - fd_3D57_0AFC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y - fd_3D57_0A90[3]);
        ed_LineTo(x + fd_3D57_0AC4[frame], y - fd_3D57_0ACC[frame]);
        ed_LineTo(x + fd_3D57_0B04[frame], y - fd_3D57_0B0C[frame]);
        ed_MoveTo(x - fd_3D57_0A90[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x - fd_3D57_0A9C[other], y + fd_3D57_0A94[other]);
        ed_LineTo(x - fd_3D57_0ADC[other], y + fd_3D57_0AD4[other]);
        ed_MoveTo(x - fd_3D57_0A90[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x - fd_3D57_0AAC[other], y + fd_3D57_0AA4[other]);
        ed_LineTo(x - fd_3D57_0AEC[other], y + fd_3D57_0AE4[other]);
        ed_MoveTo(x - fd_3D57_0A90[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x - fd_3D57_0ABC[other], y + fd_3D57_0AB4[other]);
        ed_LineTo(x - fd_3D57_0AFC[other], y + fd_3D57_0AF4[other]);
        ed_MoveTo(x - fd_3D57_0A90[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x - fd_3D57_0ACC[other], y + fd_3D57_0AC4[other]);
        ed_LineTo(x - fd_3D57_0B0C[other], y + fd_3D57_0B04[other]);
        break;
    case 4:
        ed_MoveTo(x - fd_3D57_0A04[0], y - fd_3D57_0A08[0]);
        ed_LineTo(x - fd_3D57_0A0C[frame], y - fd_3D57_0A4C[frame]);
        ed_LineTo(x - fd_3D57_0A14[frame], y - fd_3D57_0A54[frame]);
        ed_MoveTo(x - fd_3D57_0A04[1], y - fd_3D57_0A08[1]);
        ed_LineTo(x - fd_3D57_0A1C[frame], y - fd_3D57_0A5C[frame]);
        ed_LineTo(x - fd_3D57_0A24[frame], y - fd_3D57_0A64[frame]);
        ed_MoveTo(x - fd_3D57_0A04[2], y - fd_3D57_0A08[2]);
        ed_LineTo(x - fd_3D57_0A2C[frame], y - fd_3D57_0A6C[frame]);
        ed_LineTo(x - fd_3D57_0A34[frame], y - fd_3D57_0A74[frame]);
        ed_MoveTo(x - fd_3D57_0A04[3], y - fd_3D57_0A08[3]);
        ed_LineTo(x - fd_3D57_0A3C[frame], y - fd_3D57_0A7C[frame]);
        ed_LineTo(x - fd_3D57_0A44[frame], y - fd_3D57_0A84[frame]);
        ed_MoveTo(x + fd_3D57_0A04[0], y - fd_3D57_0A08[0]);
        ed_LineTo(x + fd_3D57_0A0C[other], y - fd_3D57_0A4C[other]);
        ed_LineTo(x + fd_3D57_0A14[other], y - fd_3D57_0A54[other]);
        ed_MoveTo(x + fd_3D57_0A04[1], y - fd_3D57_0A08[1]);
        ed_LineTo(x + fd_3D57_0A1C[other], y - fd_3D57_0A5C[other]);
        ed_LineTo(x + fd_3D57_0A24[other], y - fd_3D57_0A64[other]);
        ed_MoveTo(x + fd_3D57_0A04[2], y - fd_3D57_0A08[2]);
        ed_LineTo(x + fd_3D57_0A2C[other], y - fd_3D57_0A6C[other]);
        ed_LineTo(x + fd_3D57_0A34[other], y - fd_3D57_0A74[other]);
        ed_MoveTo(x + fd_3D57_0A04[3], y - fd_3D57_0A08[3]);
        ed_LineTo(x + fd_3D57_0A3C[other], y - fd_3D57_0A7C[other]);
        ed_LineTo(x + fd_3D57_0A44[other], y - fd_3D57_0A84[other]);
        break;
    case 5:
        ed_MoveTo(x - fd_3D57_0A8C[0], y - fd_3D57_0A90[0]);
        ed_LineTo(x - fd_3D57_0A94[frame], y - fd_3D57_0A9C[frame]);
        ed_LineTo(x - fd_3D57_0AD4[frame], y - fd_3D57_0ADC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y - fd_3D57_0A90[1]);
        ed_LineTo(x - fd_3D57_0AA4[frame], y - fd_3D57_0AAC[frame]);
        ed_LineTo(x - fd_3D57_0AE4[frame], y - fd_3D57_0AEC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y - fd_3D57_0A90[2]);
        ed_LineTo(x - fd_3D57_0AB4[frame], y - fd_3D57_0ABC[frame]);
        ed_LineTo(x - fd_3D57_0AF4[frame], y - fd_3D57_0AFC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y - fd_3D57_0A90[3]);
        ed_LineTo(x - fd_3D57_0AC4[frame], y - fd_3D57_0ACC[frame]);
        ed_LineTo(x - fd_3D57_0B04[frame], y - fd_3D57_0B0C[frame]);
        ed_MoveTo(x + fd_3D57_0A90[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x + fd_3D57_0A9C[other], y + fd_3D57_0A94[other]);
        ed_LineTo(x + fd_3D57_0ADC[other], y + fd_3D57_0AD4[other]);
        ed_MoveTo(x + fd_3D57_0A90[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x + fd_3D57_0AAC[other], y + fd_3D57_0AA4[other]);
        ed_LineTo(x + fd_3D57_0AEC[other], y + fd_3D57_0AE4[other]);
        ed_MoveTo(x + fd_3D57_0A90[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x + fd_3D57_0ABC[other], y + fd_3D57_0AB4[other]);
        ed_LineTo(x + fd_3D57_0AFC[other], y + fd_3D57_0AF4[other]);
        ed_MoveTo(x + fd_3D57_0A90[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x + fd_3D57_0ACC[other], y + fd_3D57_0AC4[other]);
        ed_LineTo(x + fd_3D57_0B0C[other], y + fd_3D57_0B04[other]);
        break;
    case 6:
        ed_MoveTo(x + fd_3D57_0A08[0], y - fd_3D57_0A04[0]);
        ed_LineTo(x + fd_3D57_0A4C[frame], y - fd_3D57_0A0C[frame]);
        ed_LineTo(x + fd_3D57_0A54[frame], y - fd_3D57_0A14[frame]);
        ed_MoveTo(x + fd_3D57_0A08[1], y - fd_3D57_0A04[1]);
        ed_LineTo(x + fd_3D57_0A5C[frame], y - fd_3D57_0A1C[frame]);
        ed_LineTo(x + fd_3D57_0A64[frame], y - fd_3D57_0A24[frame]);
        ed_MoveTo(x + fd_3D57_0A08[2], y - fd_3D57_0A04[2]);
        ed_LineTo(x + fd_3D57_0A6C[frame], y - fd_3D57_0A2C[frame]);
        ed_LineTo(x + fd_3D57_0A74[frame], y - fd_3D57_0A34[frame]);
        ed_MoveTo(x + fd_3D57_0A08[3], y - fd_3D57_0A04[3]);
        ed_LineTo(x + fd_3D57_0A7C[frame], y - fd_3D57_0A3C[frame]);
        ed_LineTo(x + fd_3D57_0A84[frame], y - fd_3D57_0A44[frame]);
        ed_MoveTo(x + fd_3D57_0A08[0], y + fd_3D57_0A04[0]);
        ed_LineTo(x + fd_3D57_0A4C[other], y + fd_3D57_0A0C[other]);
        ed_LineTo(x + fd_3D57_0A54[other], y + fd_3D57_0A14[other]);
        ed_MoveTo(x + fd_3D57_0A08[1], y + fd_3D57_0A04[1]);
        ed_LineTo(x + fd_3D57_0A5C[other], y + fd_3D57_0A1C[other]);
        ed_LineTo(x + fd_3D57_0A64[other], y + fd_3D57_0A24[other]);
        ed_MoveTo(x + fd_3D57_0A08[2], y + fd_3D57_0A04[2]);
        ed_LineTo(x + fd_3D57_0A6C[other], y + fd_3D57_0A2C[other]);
        ed_LineTo(x + fd_3D57_0A74[other], y + fd_3D57_0A34[other]);
        ed_MoveTo(x + fd_3D57_0A08[3], y + fd_3D57_0A04[3]);
        ed_LineTo(x + fd_3D57_0A7C[other], y + fd_3D57_0A3C[other]);
        ed_LineTo(x + fd_3D57_0A84[other], y + fd_3D57_0A44[other]);
        break;
    case 7:
        ed_MoveTo(x - fd_3D57_0A8C[0], y + fd_3D57_0A90[0]);
        ed_LineTo(x - fd_3D57_0A94[frame], y + fd_3D57_0A9C[frame]);
        ed_LineTo(x - fd_3D57_0AD4[frame], y + fd_3D57_0ADC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y + fd_3D57_0A90[1]);
        ed_LineTo(x - fd_3D57_0AA4[frame], y + fd_3D57_0AAC[frame]);
        ed_LineTo(x - fd_3D57_0AE4[frame], y + fd_3D57_0AEC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y + fd_3D57_0A90[2]);
        ed_LineTo(x - fd_3D57_0AB4[frame], y + fd_3D57_0ABC[frame]);
        ed_LineTo(x - fd_3D57_0AF4[frame], y + fd_3D57_0AFC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y + fd_3D57_0A90[3]);
        ed_LineTo(x - fd_3D57_0AC4[frame], y + fd_3D57_0ACC[frame]);
        ed_LineTo(x - fd_3D57_0B04[frame], y + fd_3D57_0B0C[frame]);
        ed_MoveTo(x + fd_3D57_0A90[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x + fd_3D57_0A9C[other], y - fd_3D57_0A94[other]);
        ed_LineTo(x + fd_3D57_0ADC[other], y - fd_3D57_0AD4[other]);
        ed_MoveTo(x + fd_3D57_0A90[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x + fd_3D57_0AAC[other], y - fd_3D57_0AA4[other]);
        ed_LineTo(x + fd_3D57_0AEC[other], y - fd_3D57_0AE4[other]);
        ed_MoveTo(x + fd_3D57_0A90[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x + fd_3D57_0ABC[other], y - fd_3D57_0AB4[other]);
        ed_LineTo(x + fd_3D57_0AFC[other], y - fd_3D57_0AF4[other]);
        ed_MoveTo(x + fd_3D57_0A90[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x + fd_3D57_0ACC[other], y - fd_3D57_0AC4[other]);
        ed_LineTo(x + fd_3D57_0B0C[other], y - fd_3D57_0B04[other]);
        break;
    }
}

void  f_0250_41CA(void)
{
    InvalEuMap((native_state_fd_50F6_0F12.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x * g_19BE) / g_19BE - 3,
                (native_state_fd_50F6_0F34.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y * g_19C0) / g_19C0 - 3,
                (native_state_fd_50F6_0F12.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x * g_19BE) / g_19BE + 3,
                (native_state_fd_50F6_0F34.signed_value - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y * g_19C0) / g_19C0 + 3);
}

/* OPEN: residue as f_0250_1E80: original keeps MapPnt.x in AX after the compare and adds
 * EditColumns; this compiles to load EditColumns then add the [bp-2] CSE temp. */
int16_t  BalloonIsVisible(int16_t plane, int16_t x, int16_t y)
{
    if (plane != native_state_MapPlane.signed_value)
        return 0;
    if (x < (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x || x >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x + fd_50F6_10E0)
        return 0;
    if (y - 3 < (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y || y >= (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y + fd_50F6_10DE)
        return 0;
    return 1;
}

extern int16_t  fd_50F6_0EF6;
extern int16_t  fd_50F6_0AD8;
extern int16_t  fd_50F6_0ACA;

void  EggBalloons(int16_t x, int16_t y, int16_t plane)
{
    if (fd_50F6_0EF6 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if ((*((Pnt *)native_sim_state_fd_50F6_08DE.raw_bytes)).x == x && (*((Pnt *)native_sim_state_fd_50F6_08DE.raw_bytes)).y == y && fd_50F6_0AD8 == plane) {
        fd_50F6_0EF6++;
        return;
    }
    (*((Pnt *)native_sim_state_fd_50F6_0852.raw_bytes)).x = x;
    (*((Pnt *)native_sim_state_fd_50F6_0852.raw_bytes)).y = y;
    fd_50F6_0ACA = plane;
}

extern int16_t  fd_50F6_0F06;
extern int16_t  fd_50F6_0B06;
extern int16_t  fd_50F6_0AEA;

void  FightBalloons(int16_t x, int16_t y, int16_t plane)
{
    if (fd_50F6_0F06 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if ((*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).x == x && (*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).y == y && fd_50F6_0B06 == plane) {
        fd_50F6_0F06++;
        return;
    }
    (*((Pnt *)native_sim_state_fd_50F6_08EC.raw_bytes)).x = x;
    (*((Pnt *)native_sim_state_fd_50F6_08EC.raw_bytes)).y = y;
    fd_50F6_0AEA = plane;
}

extern int16_t  fd_50F6_0F10;
extern int16_t  fd_50F6_0C3A;
extern int16_t  fd_50F6_0B08;

void  QueenBalloons(int16_t x, int16_t y, int16_t plane)
{
    if (fd_50F6_0F10 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if ((*((Pnt *)native_sim_state_fd_50F6_0A8A.raw_bytes)).x == x && (*((Pnt *)native_sim_state_fd_50F6_0A8A.raw_bytes)).y == y && fd_50F6_0C3A == plane) {
        fd_50F6_0F10++;
        return;
    }
    (*((Pnt *)native_sim_state_fd_50F6_0A02.raw_bytes)).x = x;
    (*((Pnt *)native_sim_state_fd_50F6_0A02.raw_bytes)).y = y;
    fd_50F6_0B08 = plane;
}

extern int16_t  fd_50F6_0F2E;
extern int16_t  fd_50F6_0D9A;
extern int16_t  fd_50F6_0D68;

void  RestBalloons(int16_t x, int16_t y, int16_t plane)
{
    if (fd_50F6_0F2E != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if ((*((Pnt *)native_sim_state_fd_50F6_0AB2.raw_bytes)).x == x && (*((Pnt *)native_sim_state_fd_50F6_0AB2.raw_bytes)).y == y && fd_50F6_0D9A == plane) {
        fd_50F6_0F2E++;
        return;
    }
    (*((Pnt *)native_sim_state_fd_50F6_0AA2.raw_bytes)).x = x;
    (*((Pnt *)native_sim_state_fd_50F6_0AA2.raw_bytes)).y = y;
    fd_50F6_0D68 = plane;
}

extern int16_t  fd_50F6_1092;

void  AddMsgBalloon(int16_t x, int16_t y, int16_t plane, int16_t style, char  *msg)
{
    int16_t tx;
    int16_t ty;

    if (style == 10) {
        tx = x / g_19BE;
        ty = y / g_19C0;
    } else {
        tx = x;
        ty = y;
    }
    if (fd_50F6_1092 >= 6)
        return;
    if (!BalloonIsVisible(plane, tx, ty))
        return;
    native_balloon_position_slots_v1[fd_50F6_1092].x = style == 10 ? x : g_19BE * x + 8;
    native_balloon_position_slots_v1[fd_50F6_1092].y = style == 10 ? y : g_19C0 * y + 8;
    native_balloon_plane_slots_v1[fd_50F6_1092] = plane;
    native_balloon_style_slots_v1[fd_50F6_1092] = style;
    native_balloon_message_slots_v1[fd_50F6_1092] = msg;
    fd_50F6_1092++;
}

extern int16_t  fd_50F6_1046;
extern int16_t  fd_50F6_0F3C;
extern char  *  *  fd_50F6_020A;
extern int16_t  fd_50F6_1064;
extern int16_t  fd_50F6_0FF8;
extern char  *  *  fd_50F6_0218;
extern int16_t  fd_50F6_104A;
extern int32_t  fd_50F6_050C;
extern int32_t  fd_50F6_0732;
extern int32_t  fd_50F6_059A;
extern int32_t  fd_50F6_0620;
extern int16_t  SRand4(void);

extern char  *  *  fd_50F6_021C;
extern int16_t  fd_50F6_1062;
extern int16_t  fd_50F6_0FC0;
extern char  *  *  fd_50F6_0234;
extern int16_t  fd_50F6_107C;
extern int16_t  fd_50F6_103A;
extern char  *  *  fd_50F6_023A;
extern void  f_24AB_02AD(int16_t font);
extern Handle  MakeBalloon(char  *msg, int16_t flags);
extern int32_t  fd_50F6_07C4;
extern Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name);

/* OPEN: residue only the operand order of the five TickCount() vs long-timer compares
 * (original: cmp mem,dx / cmp mem,ax).  A declaration order of the timer externs was found
 * that fixes all five in a different DrawSpider state; it is count-coupled with DrawSpider. */
void  DrawCurBalloons(void)
{
    if (!fd_3D57_07B2 || fd_3D57_07BE != -1)
        return;
    if (fd_50F6_0F06 == 0 && (*((Pnt *)native_sim_state_fd_50F6_08EC.raw_bytes)).x >= 0 && (*((Pnt *)native_sim_state_fd_50F6_08EC.raw_bytes)).y >= 0) {
        (*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)) = (*((Pnt *)native_sim_state_fd_50F6_08EC.raw_bytes));
        fd_50F6_0B06 = fd_50F6_0AEA;
        fd_50F6_0F06++;
        fd_50F6_0732 = 0;
        fd_50F6_050C = 0;
    }
    if (fd_50F6_0F06 > 0) {
        if (native_state_fd_50F6_047E.signed_value == 0) {
            if (fd_50F6_050C < TickCount()) {
                fd_50F6_050C = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    fd_50F6_1046 = 1;
                    if (fd_50F6_020A[++fd_50F6_0F3C] == 0)
                        fd_50F6_0F3C = 0;
                } else
                    fd_50F6_1046 = 0;
            }
            if (fd_50F6_0732 < TickCount()) {
                fd_50F6_0732 = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    fd_50F6_1064 = 1;
                    if (fd_50F6_0218[++fd_50F6_0FF8] == 0)
                        fd_50F6_0FF8 = 0;
                } else
                    fd_50F6_1064 = 0;
            }
        }
        if (fd_50F6_1046)
            AddMsgBalloon((*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).x, (*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).y, fd_50F6_0B06, 0, fd_50F6_020A[fd_50F6_0F3C]);
        if (fd_50F6_1064)
            AddMsgBalloon((*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).x, (*((Pnt *)native_sim_state_fd_50F6_09F2.raw_bytes)).y, fd_50F6_0B06, 1, fd_50F6_0218[fd_50F6_0FF8]);
    }
    if (fd_50F6_0EF6 == 0 && (*((Pnt *)native_sim_state_fd_50F6_0852.raw_bytes)).x >= 0 && (*((Pnt *)native_sim_state_fd_50F6_0852.raw_bytes)).y >= 0) {
        (*((Pnt *)native_sim_state_fd_50F6_08DE.raw_bytes)) = (*((Pnt *)native_sim_state_fd_50F6_0852.raw_bytes));
        fd_50F6_0AD8 = fd_50F6_0ACA;
        fd_50F6_0EF6++;
        fd_50F6_059A = 0;
        fd_50F6_104A = 0;
    }
    if (fd_50F6_0EF6 > 0) {
        if (native_state_fd_50F6_047E.signed_value == 0 && fd_50F6_059A < TickCount()) {
            fd_50F6_059A = TickCount() + SRand32() + 170;
            if (SRand4() == 0) {
                fd_50F6_104A = 1;
                if (fd_50F6_021C[++fd_50F6_0F7A] == 0)
                    fd_50F6_0F7A = 0;
            } else
                fd_50F6_104A = 0;
        }
        if (fd_50F6_104A)
            AddMsgBalloon((*((Pnt *)native_sim_state_fd_50F6_08DE.raw_bytes)).x, (*((Pnt *)native_sim_state_fd_50F6_08DE.raw_bytes)).y, fd_50F6_0AD8, 2, fd_50F6_021C[fd_50F6_0F7A]);
    }
    if (fd_50F6_0F10 == 0 && (*((Pnt *)native_sim_state_fd_50F6_0A02.raw_bytes)).x >= 0 && (*((Pnt *)native_sim_state_fd_50F6_0A02.raw_bytes)).y >= 0) {
        (*((Pnt *)native_sim_state_fd_50F6_0A8A.raw_bytes)) = (*((Pnt *)native_sim_state_fd_50F6_0A02.raw_bytes));
        fd_50F6_0C3A = fd_50F6_0B08;
        fd_50F6_0F10++;
        fd_50F6_0620 = 0;
        fd_50F6_1062 = 0;
    }
    if (fd_50F6_0F10 > 0) {
        if (native_state_fd_50F6_047E.signed_value == 0 && fd_50F6_0620 < TickCount()) {
            fd_50F6_0620 = TickCount() + SRand32() + 180;
            if (SRand4() == 0) {
                fd_50F6_1062 = 1;
                if (fd_50F6_0234[++fd_50F6_0FC0] == 0)
                    fd_50F6_0FC0 = 0;
            } else
                fd_50F6_1062 = 0;
        }
        if (fd_50F6_1062)
            AddMsgBalloon((*((Pnt *)native_sim_state_fd_50F6_0A8A.raw_bytes)).x, (*((Pnt *)native_sim_state_fd_50F6_0A8A.raw_bytes)).y, fd_50F6_0C3A, 2, fd_50F6_0234[fd_50F6_0FC0]);
    }
    if (fd_50F6_0F2E == 0 && (*((Pnt *)native_sim_state_fd_50F6_0AA2.raw_bytes)).x >= 0 && (*((Pnt *)native_sim_state_fd_50F6_0AA2.raw_bytes)).y >= 0) {
        (*((Pnt *)native_sim_state_fd_50F6_0AB2.raw_bytes)) = (*((Pnt *)native_sim_state_fd_50F6_0AA2.raw_bytes));
        fd_50F6_0D9A = fd_50F6_0D68;
        fd_50F6_0F2E++;
        fd_50F6_07C4 = 0;
        fd_50F6_107C = 0;
    }
    if (fd_50F6_0F2E > 0) {
        if (native_state_fd_50F6_047E.signed_value == 0 && fd_50F6_07C4 < TickCount()) {
            fd_50F6_07C4 = TickCount() + SRand64() + 120;
            if (SRand2() == 0) {
                fd_50F6_107C = 1;
                if (fd_50F6_023A[++fd_50F6_103A] == 0)
                    fd_50F6_103A = 0;
            } else
                fd_50F6_107C = 0;
        }
        if (fd_50F6_107C)
            AddMsgBalloon((*((Pnt *)native_sim_state_fd_50F6_0AB2.raw_bytes)).x, (*((Pnt *)native_sim_state_fd_50F6_0AB2.raw_bytes)).y, fd_50F6_0D9A, 2, fd_50F6_023A[fd_50F6_103A]);
    }
}

void  EditMsgBalloon(int16_t x, int16_t y, int16_t plane, int16_t style, char  *msg)
{
    char line1[256];
    char line2[256];

    if (BalloonIsVisible(plane, (x >> 4) + (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x, (y >> 4) + (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y) && msg != 0) {
        line2[0] = 0;
        line1[0] = 0;
    }
}

void  PreDrawBalloons(void)
{
    DrawCurBalloons();
}


/* OPEN: residue frame layout (0x58), i in DI, pic pointer in memory; logic complete. */
/* SCAFFOLD BEGIN: unclaimed DrawBalloons; retained whole-module context */
void  DrawBalloons(void)
{
    int16_t idx;
    int16_t tx;
    int16_t col;
    int16_t ty;
    int16_t wt;
    int16_t wpix;
    int16_t skip;
    int16_t ht;
    int16_t bpp;
    int16_t rowbytes;
    int16_t div;
    int16_t by;
    int16_t bx;
    int16_t saved;
    int16_t shown;
    Pnt pos;
    Handle hs[1];
    char  *dst;
    char  *bufp;
    int16_t  *pic;
    Handle h;
    int16_t i;
    int16_t row;
    uint16_t n;

    f_24AB_02AD(2);
    bpp = 2;
    rowbytes = 0x80;
    switch (fd_50F6_1102) {
    case 2:
        bpp = 6;
        rowbytes = 0x48;
    case 1:
        div = 2;
        break;
    case 3:
        div = 8;
        rowbytes = 0x20;
        break;
    }
    if (fd_50F6_37D2 == 500)
        f_0250_5058();
    balTileRect.left = 500;
    for (i = 0, shown = 0; i < fd_50F6_1092; i++) {
        if (shown >= 1 || native_balloon_message_slots_v1[i] == 0)
            break;
        pos = native_balloon_position_slots_v1[i];
        if (!BalloonIsVisible(native_balloon_plane_slots_v1[i], pos.x / g_19BE, pos.y / g_19C0))
            continue;
        WinPrintf("Vis message %s at %d,%d", native_balloon_message_slots_v1[i], pos.x, pos.y);
        shown++;
        hs[i] = h = MakeBalloon(native_balloon_message_slots_v1[i], 0);
        pic = (int16_t  *)f_171C_1B84(h);
        by = pos.y - pic[5] - 4;
        bx = pos.x + 4;
        wt = (bx % g_19BE + pic[4] + g_19BE - 1) / g_19BE;
        ht = (by % g_19C0 + pic[5] + g_19C0 - 1) / g_19C0;
        balTileRect.top = by / g_19C0 - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        balTileRect.left = bx / g_19BE - (*((Pnt *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        balTileRect.bottom = ht + balTileRect.top;
        balTileRect.right = balTileRect.left + wt;
        wpix = g_19BE * wt;
        n = ht * wt * rowbytes;
        balBufHandle = f_171C_1A9E((int32_t)(n + 4), 9, "balbuf");
        balBufPtr = f_171C_1B84(balBufHandle);
        bufp = balBufPtr;
        ((int16_t  *)bufp)[0] = g_19BE * wt;
        ((int16_t  *)bufp)[1] = g_19C0 * ht;
        skip = g_19C0 / div * ((int16_t  *)bufp)[0] - wt * bpp;
        dst = bufp + 4;
        _fmemset(dst, 0, n);
        balloonRect.left = g_19BE * balTileRect.left + (*((struct Rect *)native_game_fd_50F6_110C.raw)).left;
        balloonRect.top = g_19C0 * balTileRect.top + (*((struct Rect *)native_game_fd_50F6_110C.raw)).top;
        balloonRect.bottom = balloonRect.top + ((int16_t  *)bufp)[1];
        balloonRect.right = balloonRect.left + ((int16_t  *)bufp)[0];
        f_0250_0643(native_state_MapPlane.signed_value / 2);
        saved = i;
        for (row = 0, ty = balTileRect.top; row < ht; row++, ty++, dst += skip) {
            idx = ty * 40 + balTileRect.left;
            for (tx = balTileRect.left, col = 0; col < wt; col++, tx++, dst += bpp, idx++) {
                f_0250_1018(tx, ty);
                if (g_9126)
                    f_0250_0915();
                else
                    f_0250_0B86();
                (*fd_50F6_37E6)(dst, wpix);
                if (idx >= 0 && idx < 1200)
                    portable_eu_map_cache.linear[idx] = -1;
            }
        }
        f_0250_062A();
        if (fd_50F6_37D2 != 500)
            (*fd_50F6_37EE)(&fd_50F6_37D6, &portable_line16b5_source_buffer, &balloonRect, bufp);
        (*fd_50F6_37EA)((char  *)pic + 8, bufp, bx % g_19BE, by % g_19C0);
        if (fd_50F6_37D2 != 500)
            (*fd_50F6_37EE)(&balloonRect, bufp, &fd_50F6_37D6, &portable_line16b5_source_buffer);
        f_171C_1BBA(h);
        f_171C_1C0A(h);
        i = saved;
    }
    f_24AB_02AD(0);
    fd_50F6_1092 = 0;
}
/* SCAFFOLD END */

extern void  f_1E57_08F5(struct Rect  *rects);

void  f_0250_5058(void)
{
    struct Rect rects[3];

    win_GetObjRect(0x15, &(*((struct Rect *)native_game_fd_50F6_1104.raw)));
    rects[0] = (*((struct Rect *)native_game_fd_50F6_110C.raw));
    rects[1] = (*((struct Rect *)native_game_fd_50F6_1104.raw));
    rects[2].top = 0x8000;
    f_1E57_08F5(rects);
}

#pragma pack(pop)
