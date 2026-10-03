#include "portable/whole_program/platform/map_transform_callbacks.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#include "portable/whole_program/state/map_cursor_rect.h"
#pragma pack(push, 2)
/* Overlay section S12, code frame 384C: map window (map functions, map image generation). */

#include <string.h>

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

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

static int16_t g_298E = 0;
int16_t fd_55B3_2990 = 0;
static int16_t g_2992 = -1;
static int16_t g_2994 = 0;
int16_t g_2996 = 0;
static int16_t g_2998 = -1;
int32_t fd_55B3_299A = 0;
int32_t fd_55B3_299E = 0;
int16_t fd_55B3_29A2 = 0;
static int16_t g_29A4 = 0;

void  DeinitMapFunctions(void)
{
}

extern int32_t  f_171C_1750(void);
extern int32_t  f_171C_1772(void);
extern void  WinPrintf(char  *format, ...);
extern char  *  *  f_171C_1A9E(int32_t size, int16_t kind, char  *name);

extern int16_t  fd_50F6_3856;
extern int16_t  fd_50F6_3858;




extern void  o03_3253_0008();
extern void  o01_328E_000A();
extern void  o01_328E_009D();


void  InitMapFunctions(void)
{
    WinPrintf("\nFREE+SOFT AT INITMAP=%ld", f_171C_1750() + f_171C_1772());
    native_game_fd_50F6_10E2 = f_171C_1A9E(0x2000L, 1, "Generated buffer window");
    switch (g_5A97) {
    case 0:
    case 8:
        fd_50F6_3856 = 4;
        fd_50F6_3858 = 4;
        fd_50F6_38B8 = o00_3126_0000;
        fd_50F6_38BC = o00_3126_0137;
        break;
    case 2:
        fd_50F6_3856 = 2;
        fd_50F6_3858 = 2;
        fd_50F6_38B8 = o03_3253_0008;
        fd_50F6_38BC = o03_3253_0008;
        break;
    case 3:
    case 5:
    case 7:
        fd_50F6_3856 = 4;
        fd_50F6_3858 = 4;
        fd_50F6_38B8 = o01_328E_000A;
        fd_50F6_38BC = o01_328E_009D;
        break;
    case 4:
        fd_50F6_3856 = 2;
        fd_50F6_3858 = 2;
        fd_50F6_38B8 = o00_3126_026A;
        fd_50F6_38BC = o00_3126_03A9;
        break;
    }
}

extern void  MapAreaEvent(struct Event  *ev);
extern void  MapToYard(void);
extern void  ClearMapScentButtons(void);
extern void  SetMapPlane(int16_t plane);
extern void  f_20E8_0725(int16_t win);
extern void  SetMapModeAnt(int16_t mode);
extern void  OpenModeWindow(void);
void  o12_384C_12D3(struct Event  *ev);
extern void  OpenCasteWindow(void);
extern void  MysteryButton(void);
extern void  OpenHistoryWindow(void);
extern void  ScoreDialog(void);
extern void  OpenInfoWindow(void);
extern void  DoWinHelp(int16_t win);
extern void  MapToolsMenu(void);
extern void  DrawCastePopUp(void);

void  ProcMapEvent(struct Event  *ev)
{
    switch (ev->code) {
    case 0x102: MapAreaEvent(ev); break;
    case 0x105: MapToYard(); break;
    case 0x106: ClearMapScentButtons(); SetMapPlane(1); break;
    case 0x107: ClearMapScentButtons(); SetMapPlane(2); break;
    case 0x108: ClearMapScentButtons(); SetMapPlane(3); f_20E8_0725(0x100); break;
    case 0x109: SetMapModeAnt(4); f_20E8_0725(0x100); break;
    case 0x10a: SetMapModeAnt(5); break;
    case 0x10b: SetMapModeAnt(8); break;
    case 0x10c: SetMapModeAnt(6); break;
    case 0x10d: SetMapModeAnt(7); break;
    case 0x10e: g_2994 = !g_2994; break;
    case 0x10f: OpenModeWindow(); break;
    case 0x110: o12_384C_12D3(ev); break;
    case 0x111: OpenCasteWindow(); break;
    case 0x112: MysteryButton(); break;
    case 0x113: OpenHistoryWindow(); break;
    case 0x114: ScoreDialog(); break;
    case 0x115: OpenInfoWindow(); break;
    case 0x116: native_state_fd_50F6_1074.signed_value = 1; DoWinHelp(0x103); break;
    case 0x117: MapToolsMenu(); break;
    case 0x118: DrawCastePopUp(); break;
    }
}

extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;

void  OpenMapWindow(void)
{
    win_Open(0x100, 0, 0, 0, 0, 0);
}

extern int16_t  win_IsWinOpen(int16_t win);
extern void  clip_Push(void);
extern void  clip_SetWin(int16_t win);
extern int16_t  fd_50F6_10DE;
extern int16_t  fd_50F6_38C0;
extern int16_t  fd_50F6_10E0;
extern void  GRectInvOutline(struct Rect  *rect, int16_t width);
extern void  clip_Pop(void);

/* SCAFFOLD BEGIN: DrawMapCursor draft (worker resA): with +2..+13 identifiers declared before the first extern the length is exact and the original value-CSE of fd_50F6_3858 appears (symbol-table state, probe SYM-1); left over (37 bytes): the original saves the rect segment (mov dx,es) after the left store and adds fd_50F6_10D2.left before fd_50F6_38C0; a 1024-point search over dummy positions found no exact state. Same residue as S04 DrawMiniMapCursor */
void  DrawMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 0)
        return;
    clip_Push();
    clip_SetWin(0x100);
    fd_50F6_38C2.top = fd_50F6_3858 * native_sim_state_fd_50F6_0508.words[1] + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    fd_50F6_38C2.bottom = fd_50F6_38C2.top + fd_50F6_3858 * fd_50F6_10DE;
    fd_50F6_38C2.left = fd_50F6_3856 * native_sim_state_fd_50F6_0508.words[0] + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + fd_50F6_38C0;
    fd_50F6_38C2.right = fd_50F6_38C2.left + fd_50F6_3856 * fd_50F6_10E0;
    GRectInvOutline(&fd_50F6_38C2, 2);
    g_298E = 1;
    clip_Pop();
}

/* SCAFFOLD END */

void  EraseMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 1)
        return;
    clip_Push();
    clip_SetWin(0x100);
    GRectInvOutline(&fd_50F6_38C2, 2);
    g_298E = 0;
    clip_Pop();
}

void  ToggleMapCursor(void)
{
    if (g_298E)
        EraseMapCursor();
    else
        DrawMapCursor();
}

extern int16_t  fd_50F6_3854;

void  o12_384C_03D0(char  *src, char  *dst, int16_t n)
{
    if (fd_50F6_3854 == 64)
        (*fd_50F6_38BC)(src, dst, fd_50F6_3854, n);
    else
        (*fd_50F6_38B8)(src, dst, fd_50F6_3854, n);
}

extern void  win_MapChanged(void);

void  o12_384C_0425(void)
{
    win_MapChanged();
}

extern int16_t  fd_3D57_07C8;
extern char  *  *  fd_50F6_385A;
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);
extern uint8_t  LifeA[128][64];
extern uint8_t  MapA[128][64];
extern int16_t  TERRAINset;
extern uint8_t  fd_3D57_046E[];
extern uint8_t  fd_3D57_039E[];
extern uint8_t  fd_3D57_030E[];
extern uint8_t  fd_3D57_061E[];
extern uint8_t  fd_3D57_054E[];
extern uint8_t  fd_3D57_04CE[];

void  o12_384C_0432(void)
{
    int16_t fresh;
    uint8_t  *buf;
    uint8_t  *p;
    uint8_t  *q;
    int16_t x, y, c;

    fresh = g_2994;
    if (fd_3D57_07C8 != g_2992) {
        o12_384C_0425();
        g_2992 = fd_3D57_07C8;
        fresh = 0;
    }
    buf = (uint8_t  *)f_171C_1B84(fd_50F6_385A);
    if (fresh) {
        _fmemcpy(buf, f_171C_1B84(native_game_fd_50F6_10E2), 0x2000);
        f_171C_1BBA(native_game_fd_50F6_10E2);
    }
    p = &LifeA[0][0];
    q = &MapA[0][0];
    if (!(g_5A97 & 1)) {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_046E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_039E[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_046E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_030E[*q]; else buf++;
                }
        }
    } else {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_061E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_054E[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_061E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_04CE[*q]; else buf++;
                }
        }
    }
    f_171C_1BBA(fd_50F6_385A);
}


void  o12_384C_0706(uint8_t  *src)
{
    uint8_t  *buf;
    int16_t x, y, i;
    uint8_t c;

    buf = (uint8_t  *)f_171C_1B84(fd_50F6_385A);
    g_2992 = fd_3D57_07C8;
    if (g_5A97 & 1) {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 4) + 0x2e : 0;
                buf[i] = c;
                buf[i + 1] = c;
                buf[i + 0x80] = c;
                buf[i + 0x81] = c;
            }
    } else {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 5) + 0x10 : 0xb;
                buf[i] = c; buf[i + 1] = c;
                buf[i + 0x80] = c; buf[i + 0x81] = c;
            }
    }
    f_171C_1BBA(fd_50F6_385A);
}

extern uint8_t  LifeR[64][64];
extern uint8_t  MapR[64][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  MapB[64][64];
extern uint8_t  fd_3D57_0656[];
extern uint8_t  fd_3D57_04A6[];

void  o12_384C_080E(void)
{
    int16_t fresh;
    uint8_t  *buf;
    uint8_t  *p;
    uint8_t  *q;
    int16_t x, y, c;

    fresh = g_2994;
    if (fd_3D57_07C8 != g_2992) {
        o12_384C_0425();
        g_2992 = fd_3D57_07C8;
        fresh = 0;
    }
    buf = (uint8_t  *)f_171C_1B84(fd_50F6_385A);
    if (fresh) {
        _fmemcpy(buf, f_171C_1B84(native_game_fd_50F6_10E2), 0x2000);
        f_171C_1BBA(native_game_fd_50F6_10E2);
    }
    if (fd_3D57_07C8 == 3) {
        p = &LifeR[0][0];
        q = &MapR[0][0];
    } else {
        p = &LifeB[0][0];
        q = &MapB[0][0];
    }
    if (g_5A97 & 1) {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = fd_3D57_0656[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 0x27;
                    break;
                default:
                    if (c & 0x80) *buf++ = 0x25; else *buf++ = 0x23;
                    break;
                }
            }
    } else {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = fd_3D57_04A6[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 1;
                    break;
                default:
                    if (c & 0x80) *buf++ = 3; else *buf++ = 0xf;
                    break;
                }
            }
    }
    f_171C_1BBA(fd_50F6_385A);
}

extern void  f_24AB_02AD(int16_t font);
extern void  win_PrintfAtObj(int16_t obj, char  *format, ...);
extern void  win_DrawHBar(int16_t obj, int32_t fraction);

void  DrawMapData(void)
{
    int16_t popMax, redHealth;
    int32_t maxPop;

    popMax = 1;
    if (native_state_BpopT.signed_value > popMax)
        popMax = native_state_BpopT.signed_value;
    if (native_state_RpopT.signed_value > popMax)
        popMax = native_state_RpopT.signed_value;
    redHealth = native_state_RpopT.signed_value == 0 ? 0 : native_state_HealthR.signed_value;
    f_24AB_02AD(SIM_GRAPHICS_SOURCE_g_3DB2 == 320 ? 0 : 3);
    win_PrintfAtObj(0x119, "%-d", native_state_BpopT.signed_value);
    win_PrintfAtObj(0x11a, "%-d", native_state_RpopT.signed_value);
    f_24AB_02AD(0);
    win_DrawHBar(0x11b, ((int32_t)native_state_HealthB.signed_value << 16) / 100);
    maxPop = popMax;
    win_DrawHBar(0x11d, ((int32_t)native_state_BpopT.signed_value << 16) / maxPop);
    win_DrawHBar(0x11c, ((int32_t)redHealth << 16) / 100);
    win_DrawHBar(0x11e, ((int32_t)native_state_RpopT.signed_value << 16) / maxPop);
}

extern void  MapToYard(void);
extern char  *  *  fd_50F6_385E;
extern void  Punt(char  *msg);
extern uint8_t  PherMapBN[];
extern uint8_t  PherMapBT[];
extern uint8_t  PherMapRN[];
extern uint8_t  PherMapRT[];
extern uint8_t  PherMapA[];
extern int32_t  TickCount(void);
extern void  win_SetColorNum(int16_t color);
extern void  f_15D9_0006(int32_t msg, struct Rect  *rect, int16_t y);
extern void  clip_SubInclude(struct Rect  *rect);
extern void ( *  g_914C)(int16_t x, int16_t y, char  *image, int16_t width, int16_t height);
void  o12_384C_10A5(int16_t x, int16_t y, int16_t kind);
void  o12_384C_1181(void);
extern void  f_171C_1C0A(char  *  *handle);

void  o12_384C_0B76(void)
{
    int16_t n, row, off, y, sx, sy;
    char  *img;
    char  *gen;
    char  *old;

    if (fd_3D57_07C8 == 0) {
        MapToYard();
        return;
    }
    fd_50F6_3854 = 0x80;
    fd_50F6_38C0 = fd_55B3_2990 = 0;
    fd_50F6_385E = f_171C_1A9E(0x400L, 1, "Map window image");
    fd_50F6_385A = f_171C_1A9E(0x2000L, 1, "Generated map window");
    if (fd_3D57_07C8 != g_2992)
        win_MapChanged();
    switch (fd_3D57_07C8) {
    case 0:
        Punt("Draw map - yard");
        break;
    case 1:
        o12_384C_0432();
        break;
    case 2:
    case 3:
        o12_384C_080E();
        fd_50F6_3854 = 0x40;
        fd_50F6_38C0 = fd_50F6_3856 << 5;
        break;
    case 4:
        o12_384C_0706(PherMapBN);
        break;
    case 5:
        o12_384C_0706(PherMapBT);
        break;
    case 6:
        o12_384C_0706(PherMapRN);
        break;
    case 7:
        o12_384C_0706(PherMapRT);
        break;
    case 8:
        o12_384C_0706(PherMapA);
        break;
    }
    n = ((*((struct Rect *)native_game_fd_50F6_10D2.raw)).bottom - (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top) / fd_50F6_3858;
    if (n > 64)
        WinPrintf("\nYMAXCOUNT =%d!!!!!", n);
    n = 64;
    (*g_9134)((*((struct Rect *)native_game_fd_50F6_10D2.raw)).left, (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + fd_50F6_38C0,
              (*((struct Rect *)native_game_fd_50F6_10D2.raw)).bottom, f_1B4E_000D(15));
    (*g_9134)((*((struct Rect *)native_game_fd_50F6_10D2.raw)).right - fd_50F6_38C0, (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, (*((struct Rect *)native_game_fd_50F6_10D2.raw)).right,
              (*((struct Rect *)native_game_fd_50F6_10D2.raw)).bottom, f_1B4E_000D(15));
    EraseMapCursor();
    if (fd_55B3_299A) {
        if (TickCount() > fd_55B3_299E) {
            if (fd_55B3_299A)
                g_29A4 = 1;
            fd_55B3_299A = 0;
        } else {
            win_SetColorNum(3);
            f_15D9_0006(fd_55B3_299A, &(*((struct Rect *)native_game_fd_50F6_10D2.raw)), (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 4);
        }
    }
    clip_Push();
    clip_SubInclude(&(*((struct Rect *)native_game_fd_50F6_10D2.raw)));
    img = f_171C_1B84(fd_50F6_385A);
    gen = f_171C_1B84(fd_50F6_385E);
    if (native_state_fd_50F6_0F0C.signed_value && !g_2994 && native_state_MapPlane.signed_value == 1) {
        sx = native_state_fd_50F6_0F12.signed_value >> 4;
        sy = native_state_fd_50F6_0F34.signed_value >> 4;
    } else
        sy = 0x7fff;
    old = f_171C_1B84(native_game_fd_50F6_10E2);
    y = (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    for (row = 0, off = 0; row < n; row++, y += fd_50F6_3858) {
        if (_fmemcmp(old + off, img + off, fd_50F6_3854) || fd_55B3_29A2 || (row < 8 && g_29A4)) {
            _fmemcpy(old + off, img + off, fd_50F6_3854);
            o12_384C_03D0(img + off, gen, y);
            (*g_914C)((*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + fd_50F6_38C0, y, gen, fd_50F6_3854 * fd_50F6_3856, fd_50F6_3858);
        }
        off += fd_50F6_3854;
        if (sy != 0x7fff && sy + 4 <= row) {
            o12_384C_10A5(sx, sy, native_state_fd_50F6_1004.signed_value);
            sy = 0x7fff;
        }
    }
    if (sy != 0x7fff)
        o12_384C_10A5(sx, sy, native_state_fd_50F6_1004.signed_value);
    f_171C_1BBA(native_game_fd_50F6_10E2);
    f_171C_1BBA(fd_50F6_385E);
    f_171C_1BBA(fd_50F6_385A);
    f_171C_1C0A(fd_50F6_385E);
    f_171C_1C0A(fd_50F6_385A);
    if (native_state_MapPlane.signed_value == 1 && !g_2994)
        o12_384C_1181();
    DrawMapCursor();
    clip_Pop();
    fd_55B3_29A2 = fd_55B3_2990;
    g_29A4 = 0;
}


extern void  clip_Off(void);

void  o12_384C_100A(void)
{
    if (win_IsWinOpen(0x100)) {
        clip_SetWin(0x100);
        o12_384C_0B76();
        DrawMapData();
        clip_Off();
    }
}

extern int16_t  fd_50F6_0EAC;
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  win_DrawBitMapAtObjNum(int16_t obj, int16_t id);

void  o12_384C_1035(int16_t flags)
{
    int16_t id;

    if (flags & 2) {
        if (fd_3D57_07C8 == 0)
            MapToYard();
        else {
            win_MapChanged();
            clip_SetWin(0x100);
            DrawMapData();
            o12_384C_0B76();
            id = fd_50F6_0EAC == 3 ? native_state_CurExpTool.signed_value + 0x13ec : 0x13f3;
            win_SetColorFromObjNum(0x117);
            win_DrawBitMapAtObjNum(0x117, id);
        }
    }
}

extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);

void  o12_384C_10A5(int16_t x, int16_t y, int16_t kind)
{
    int16_t ys;
    uint8_t  *p;

    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = x * 2 - 3;
        ys = y * 2 - 3;
    } else {
        x = x * 4 - 3;
        ys = y * 4 - 3;
    }
    win_DrawBitMap(x + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left, ys + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, kind + 0x44c);
    y -= 2;
    if (native_game_fd_50F6_10E2) {
        p = (uint8_t  *)f_171C_1B84(native_game_fd_50F6_10E2);
        p += fd_50F6_3854 * y;
        for (x = y + 5; y < x; y++, p += fd_50F6_3854) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        f_171C_1BBA(native_game_fd_50F6_10E2);
    }
}

extern int16_t  fd_3D57_0C3E;
extern int16_t  fd_3D57_0C30;
extern int16_t  fd_3D57_0C28;

void  o12_384C_1181(void)
{
    int16_t x, y, end;
    uint8_t  *p;

    if (fd_3D57_0C3E == 0)
        return;
    x = native_state_fd_50F6_03E0.signed_value << 2;
    y = native_state_fd_50F6_046A.signed_value << 2;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x >>= 1;
        y >>= 1;
    }
    win_DrawBitMap(x + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left, y + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, fd_3D57_0C30 + 0x4b0);
    if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
        x = native_state_fd_50F6_0470.signed_value << 2;
        y = native_state_fd_50F6_047A.signed_value << 2;
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
            x >>= 1;
            y >>= 1;
        }
        win_DrawBitMap(x + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left, y + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, (fd_3D57_0C30 & 1) + 0x4ba);
    }
    y = native_state_fd_50F6_046A.signed_value;
    if (native_game_fd_50F6_10E2) {
        p = (uint8_t  *)f_171C_1B84(native_game_fd_50F6_10E2);
        p += fd_50F6_3854 * y;
        for (end = y + 8; y < end; y++, p += fd_50F6_3854) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        f_171C_1BBA(native_game_fd_50F6_10E2);
    }
    fd_55B3_2990 = 1;
}

extern void  AddFood(int16_t count, int16_t sound);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  KillSomeAnts(int16_t side);
extern void  AddSomeAnts(int16_t side);
extern void  SubtractFood(void);
extern void  GotoMyAnt(void);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);

void  o12_384C_12D3(struct Event  *ev)
{
    struct Rect r;
    int16_t side;

    if (dos_keyboard_modifiers() & 4) {
        if (dos_keyboard_modifiers() & 3) {
            win_GetObjRect(0x110, &r);
            side = (r.left + r.right) / 2;
            side = ev->h >= side ? 0 : 1;
            if (dos_keyboard_modifiers() & 8)
                KillSomeAnts(side);
            else
                AddSomeAnts(side);
        } else if (dos_keyboard_modifiers() & 8) {
            myBeginSound(0x20, 0, 0x7e);
            SubtractFood();
        } else
            AddFood(0x96, 1);
    } else
        GotoMyAnt();
}

#pragma pack(pop)
