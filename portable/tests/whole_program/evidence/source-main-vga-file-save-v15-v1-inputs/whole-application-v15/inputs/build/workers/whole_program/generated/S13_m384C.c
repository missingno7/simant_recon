#include "portable/whole_program/state/yard_cache_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/types/fonts.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S13, code frame 384C: yard window (yard events, animated yard objects, colonies). */

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

struct Pt {
    int16_t h;
    int16_t v;
};

static int16_t g_2A2A = -1;
static int16_t g_2A2C = -1;
static int16_t g_2A2E = -1;
static int16_t g_2A30 = -1;
static int16_t g_2A32 = -1;
static int16_t g_2A34 = -1;
extern SimYardCacheHandle fd_55B3_2A36;
extern SimYardCacheHandle fd_55B3_2A3A;
static int16_t g_2A3E = -1;
static int16_t g_2A40 = -1;
extern int16_t fd_55B3_2A42[8];
static int16_t g_2A52 = 0;
static int16_t g_2A54 = -1;
static int8_t kidX[12] = { 3, 3, 1, 0, 3, 0, 1, 4, 4, 3, 7, 2 };
static int8_t kidY[44] = {
    2, 0, 2, 3, 2, 3, 2, 0, 2, 3, 2, 3, 4, 5, 4, 6, 0, 2, 0, 2, 0, 3,
    2, 1, 5, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1
};
static int8_t dogWalkX[12] = { 1, 0, 1, 2, 0, 1, 2, 2, 2, 1, 0, 1 };
static int8_t dogWalkY[8] = { 0, 1, 0, 1, 2, 1, 2, 0 };
static int8_t catOfs[40] = {
    0, 1, 2, 1, 2, 0, 2, 0, 1, 1, 3, 3, -10, -9, -10, -10, -21, -19, -18, 0,
    0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 0, -16, -23, -24, -22, -18, -10, -10, -4, -2
};
static int16_t g_2ACA[4] = { 15, 31, 35, 72 };
static int16_t g_2AD2[4] = { 15, 19, 35, 72 };

void  YardArea(struct Event  *ev);
extern void  YardToMap(void);
extern void  SetYardMode(int16_t mode);
extern int16_t  fd_50F6_0EAC;
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern char  *  *  fd_50F6_034C;
extern void  EditMessage(void  *text, int32_t pos, int16_t mode);
extern int16_t  fd_50F6_04C2;
extern int16_t  fd_3D57_02C0;
extern void  win_MakeObjSelected(int16_t obj);
extern void  PlaceQueenInYard(void);
void  UpdateYard(void);
extern void  win_MakeObjUnselected(int16_t obj);
extern void  DoWinHelp(int16_t win);

void  ProcYardEvent(struct Event  *ev)
{
    int16_t n;

    switch (ev->code) {
    case 0x1902:
        YardArea(ev);
        break;
    case 0x1907:
        YardToMap();
        break;
    case 0x1908:
        if (native_state_YardMode.signed_value < 2)
            SetYardMode(native_state_YardMode.signed_value ^ 1);
        else
            SetYardMode(0);
        break;
    case 0x1909:
        SetYardMode(2);
        break;
    case 0x190a:
        SetYardMode(3);
        break;
    case 0x190b:
        if (fd_50F6_0EAC != 2) {
            myBeginSound(1, 0, 0x7e);
            EditMessage(fd_50F6_034C[15], 180L, 1);
        } else {
            n = native_sim_state_fd_50F6_0AEC.signed_values[3] + native_sim_state_fd_50F6_0AEC.signed_values[4];
            if (fd_50F6_04C2 == 0x40 || fd_50F6_04C2 == 0x20)
                n--;
            if (n <= 0) {
                myBeginSound(1, 0, 0x7e);
                EditMessage(fd_50F6_034C[5], 180L, 1);
            } else {
                native_state_fd_50F6_08DC.signed_value = 200;
                EditMessage(fd_50F6_034C[6], 180L, 1);
            }
        }
        break;
    case 0x190d:
        fd_3D57_02C0 = 1;
        break;
    case 0x190e:
        fd_3D57_02C0 = 0;
        break;
    case 0x1910:
        win_MakeObjSelected(0x190e);
        win_MakeObjSelected(0x1910);
        PlaceQueenInYard();
        UpdateYard();
        win_MakeObjUnselected(0x1910);
        break;
    case 0x1911:
        DoWinHelp(0x1906);
        break;
    }
}

void  InvertPatch(int16_t x, int16_t y);

void  DrawYardCursor(void)
{
    if (!g_2A52) {
        InvertPatch(native_sim_state_fd_50F6_07CA.words[0], native_sim_state_fd_50F6_07CA.words[1]);
        g_2A52 = 1;
    }
}

void  EraseYardCursor(void)
{
    if (g_2A52) {
        InvertPatch(native_sim_state_fd_50F6_07CA.words[0], native_sim_state_fd_50F6_07CA.words[1]);
        g_2A52 = 0;
    }
}

extern int32_t  fd_55B3_299A;
extern int32_t  TickCount(void);
extern int32_t  fd_55B3_299E;
extern int16_t  fd_55B3_29A2;
extern void  win_SetColorNum(int16_t color);
extern void  f_15D9_0006(int32_t msg, struct Rect  *rect, int16_t y);

void  o13_384C_01E5(void)
{
    if (fd_55B3_299A) {
        if (TickCount() > fd_55B3_299E) {
            if (fd_55B3_299A)
                fd_55B3_29A2 = 1;
            fd_55B3_299A = 0;
        } else {
            win_SetColorNum(3);
            if (native_state_YardMode.signed_value > 1)
                f_15D9_0006(fd_55B3_299A, &(*((struct Rect *)native_game_fd_50F6_10D2.raw)), (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 4);
        }
    }
}

void  Draw_SimYard(int16_t mode, int16_t force);
extern void  win_ObjFormatPrint(int16_t obj, ...);

void  o13_384C_027C(void)
{
    o13_384C_01E5();
    Draw_SimYard(native_state_YardMode.signed_value, 1);
    win_ObjFormatPrint(0x190c, native_state_fd_50F6_07C8.signed_value);
    win_ObjFormatPrint(0x1912, native_state_fd_50F6_03E2.signed_value);
    win_ObjFormatPrint(0x1913, native_state_fd_50F6_0400.signed_value);
}


extern void  win_DrawObjectNum(int16_t objNum);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern void  f_208F_0419(struct Pt  *size, int16_t id);
extern int16_t  fd_55B3_2990;

void  win_DrawYardWindow(int16_t flags)
{
    struct Rect r;
    struct Pt sz;
    int16_t id, y;

    if (flags & 1) {
        EraseYardCursor();
        if (native_state_YardMode.signed_value > 1) {
            if (native_state_YardMode.signed_value > 2 || fd_55B3_29A2 || !(flags & 4) || native_state_YardMode.signed_value != g_2A54) {
                if (SIM_GRAPHICS_SOURCE_g_3DB2 != 320 && !(g_5A97 & 1)) {
                    o13_384C_01E5();
                    win_DrawObjectNum(0x1914);
                    win_GetObjRect(0x1914, &r);
                    y = r.bottom;
                    win_GetObjRect(0x1902, &r);
                    for (id = 0x1b6c; id <= 0x1b6e; id++) {
                        win_DrawBitMap(r.left, y, id);
                        f_208F_0419(&sz, id);
                        y += sz.v;
                    }
                    win_DrawObjectNum(0x1915);
                } else
                    win_DrawBitMap((*((struct Rect *)native_game_fd_50F6_10D2.raw)).left - ((g_5A97 & 1) != 0), (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top, 0x1b5a);
            }
        }
        g_2A54 = native_state_YardMode.signed_value;
    }
    if (flags & 2) {
        fd_55B3_2990 = 0;
        o13_384C_027C();
        fd_55B3_29A2 = fd_55B3_2990;
        DrawYardCursor();
    }
}

extern int16_t  win_IsWinOpen(int16_t win);
extern void  clip_SetWin(int16_t win);
extern void  clip_Off(void);

void  o13_384C_03F8(void)
{
    if (win_IsWinOpen(0x1900) && fd_55B3_29A2) {
        clip_SetWin(0x1900);
        EraseYardCursor();
        o13_384C_01E5();
        win_DrawObjectNum(0x1914);
        DrawYardCursor();
        clip_Off();
        fd_55B3_29A2 = 0;
    }
}

void  DrawYard(void)
{
    if (win_IsWinOpen(0x1900)) {
        clip_SetWin(0x1900);
        win_DrawYardWindow(7);
        clip_Off();
    }
}

void  UpdateYard(void)
{
    DrawYard();
}

typedef SimYardCacheHandle Handle;
extern int16_t  fd_3D57_0C2C;
extern int16_t  fd_3D57_0C2E;
extern int16_t  fd_3D57_0C32;
extern void  hanim_SetObjectPos(int16_t x, int16_t y, int16_t pic, Handle h, int16_t id, int16_t pri);
extern int16_t  hanim_AddAnimObject(Handle h, int16_t x, int16_t y, int16_t pic, int16_t pri);
extern int32_t  MacTickCount(void);
extern void  hanim_RemoveAnimObject(Handle h, int16_t id);
extern void f_171C_1C0A(SimYardCacheHandle h);
extern void  f_24AB_02AD(int16_t font);
extern SimYardCacheHandle MakeBalloon(char *msg, int16_t flags);
extern char  *  *  fd_50F6_10A8;

void  DrawSimKid(void)
{
    struct Pt sz;
    int16_t x, y;

    x = fd_3D57_0C2C;
    y = fd_3D57_0C2E;
    if (fd_3D57_0C32 < 12) {
        x += kidX[fd_3D57_0C32];
        y += kidY[fd_3D57_0C32];
    } else if (fd_3D57_0C32 < 24) {
        x += kidX[fd_3D57_0C32 + 4];
        y += kidY[fd_3D57_0C32 - 4];
    } else if (fd_3D57_0C32 < 200) {
        x += kidX[fd_3D57_0C32 - 68];
        y += kidY[fd_3D57_0C32 - 68];
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    if (g_2A2A != -1)
        hanim_SetObjectPos(x, y, fd_3D57_0C32 + 0x1f40, native_game_fd_50F6_10DA, g_2A2A, -1);
    else
        g_2A2A = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, fd_3D57_0C32 + 0x1f40, -1);
    if (native_state_fd_50F6_047E.signed_value == 0 && MacTickCount() > native_state_fd_50F6_109C.signed_value)
        native_state_fd_50F6_10B0.signed_value = 0;
    if (g_2A3E != -1) {
        hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A3E);
        g_2A3E = -1;
    }
    if (fd_55B3_2A36) {
        f_171C_1C0A(fd_55B3_2A36);
        fd_55B3_2A36 = 0;
    }
    if (native_state_fd_50F6_10B0.signed_value) {
        f_24AB_02AD(2);
        fd_55B3_2A36 = MakeBalloon(fd_50F6_10A8[native_state_fd_50F6_10BC.signed_value], 0);
        f_24AB_02AD(0);
        f_208F_0419(&sz, 30000);
        y = fd_3D57_0C2E;
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
            y = (y >> 1) + 6;
        else
            x += 4;
        y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top - sz.v;
        if (g_2A3E != -1)
            hanim_SetObjectPos(x, y, 30000, native_game_fd_50F6_10DA, g_2A3E, 999);
        else
            g_2A3E = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, 30000, 999);
    }
}

extern int16_t  fd_3D57_0C44;

void  DrawDog(void)
{
    int16_t x, y;

    x = native_state_fd_50F6_04BE.signed_value;
    y = native_state_fd_50F6_04C6.signed_value;
    if (fd_3D57_0C44 == 0) {
        if (native_state_fd_50F6_04E4.signed_value < 12) {
            x += dogWalkX[native_state_fd_50F6_04E4.signed_value];
            y += dogWalkY[native_state_fd_50F6_04E4.signed_value];
        } else {
            x += kidX[native_state_fd_50F6_04E4.signed_value - 20];
            y += kidX[native_state_fd_50F6_04E4.signed_value - 16];
        }
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
        y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
        if (g_2A30 != -1)
            hanim_SetObjectPos(x, y, native_state_fd_50F6_04E4.signed_value + 0x2134, native_game_fd_50F6_10DA, g_2A30, -1);
        else
            g_2A30 = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, native_state_fd_50F6_04E4.signed_value + 0x2134, -1);
    }
}


void  DrawSimBird(void)
{
    int16_t x, y;

    x = native_state_fd_50F6_10AC.signed_value - 10;
    y = native_state_fd_50F6_10BA.signed_value - 3;
    if (native_state_fd_50F6_108C.signed_value) {
        x++;
        y += 2;
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    if (g_2A2E != -1)
        hanim_SetObjectPos(x, y, native_state_fd_50F6_108C.signed_value + 0x4e2, native_game_fd_50F6_10DA, g_2A2E, -1);
    else
        g_2A2E = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, native_state_fd_50F6_108C.signed_value + 0x4e2, -1);
}


void  DrawSimCat(void)
{
    int16_t x, y;

    x = native_state_fd_50F6_02BE.signed_value;
    y = native_state_fd_50F6_032C.signed_value;
    if (native_state_fd_50F6_0244.signed_value >= 10) {
        if (native_state_fd_50F6_0244.signed_value < 20) {
            x += catOfs[native_state_fd_50F6_0244.signed_value + 2];
            y += catOfs[native_state_fd_50F6_0244.signed_value + 6];
        } else {
            x += catOfs[native_state_fd_50F6_0244.signed_value];
            y += catOfs[native_state_fd_50F6_0244.signed_value + 10];
        }
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    if (g_2A2C != -1)
        hanim_SetObjectPos(x, y, native_state_fd_50F6_0244.signed_value + 0x514, native_game_fd_50F6_10DA, g_2A2C, -1);
    else
        g_2A2C = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, native_state_fd_50F6_0244.signed_value + 0x514, -1);
}

void  DrawForSale(void)
{
    int16_t x, y;

    x = 0xaa;
    y = 0xba;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = 0x5a;
        y = 0x63;
    }
    x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    if (g_2A34 != -1)
        hanim_SetObjectPos(x, y, 0x4ec, native_game_fd_50F6_10DA, g_2A34, -1);
    else
        g_2A34 = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, 0x4ec, -1);
}

extern int16_t  fd_3D57_0C28;

/* DrawMower: the final position goes to separate h, v; x and y then die before the call and
 * x is allocated to BX (frame 8 keeps the h/v homes), as in the original (worker resF). */
void  DrawMower(void)
{
    int16_t frame, x, y, h, v;

    frame = 0;
    if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
        if (native_state_fd_50F6_047E.signed_value == 0)
            myBeginSound(0x24, 0, 0x40);
        switch (fd_3D57_0C32) {
        case 0x67:
        case 0x68:
        case 0x69:
            frame = 1;
            break;
        case 0x6d:
        case 0x6e:
        case 0x6f:
            frame = 2;
            break;
        default:
            if (g_2A32 != -1) {
                hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A32);
                g_2A32 = -1;
            }
            return;
        }
    }
    if (frame == 0) {
        x = 0x62;
        y = 0xb5;
    } else {
        if (frame == 1)
            x = fd_3D57_0C2C + 0x13;
        else
            x = fd_3D57_0C2C - 0xf;
        y = fd_3D57_0C2E + 0xf;
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    h = x + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    v = y + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    if (g_2A32 != -1)
        hanim_SetObjectPos(h, v, frame + 0x2260, native_game_fd_50F6_10DA, g_2A32, -1);
    else
        g_2A32 = hanim_AddAnimObject(native_game_fd_50F6_10DA, h, v, frame + 0x2260, -1);
}

extern Handle  hanim_MakeAnimSet(void);
extern int16_t  fd_50F6_38CA[15];
extern int16_t  fd_50F6_38E8[17];
extern int16_t  fd_50F6_390A[17];

extern void  hanim_RenderAnimSet(Handle h);
extern int16_t  fd_3D57_0C20;
void  DrawAnimYardMessage(void);
void  DrawRain(void);
void  DrawSwarm(void);
void  DrawSimColonies(int16_t mode);
void  DrawColonyBars(int16_t mode);

void  Draw_SimYard(int16_t mode, int16_t force)
{
    int16_t i;

    EraseYardCursor();
    if (mode <= 1) {
        if (!native_game_fd_50F6_10DA) {
            native_game_fd_50F6_10DA = hanim_MakeAnimSet();
            _fmemset(fd_50F6_38CA, -1, 0x1e);
            _fmemset(fd_50F6_38E8, -1, 0x22);
            _fmemset(fd_50F6_390A, -1, 0x22);
            g_2A2A = -1;
            g_2A30 = -1;
            g_2A2E = -1;
            g_2A2C = -1;
            g_2A32 = -1;
            g_2A34 = -1;
            g_2A3E = -1;
            g_2A40 = -1;
        }
        if (native_state_fd_50F6_0254.signed_value)
            DrawSimCat();
        else if (g_2A2C != -1) {
            hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A2C);
            g_2A2C = -1;
        }
        DrawDog();
        if ((mode || fd_3D57_0C28) && fd_3D57_0C32 >= 0)
            DrawSimKid();
        else {
            if (g_2A2A != -1) {
                hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A2A);
                g_2A2A = -1;
            }
            if (g_2A3E != -1) {
                hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A3E);
                g_2A3E = -1;
                f_171C_1C0A(fd_55B3_2A36);
                fd_55B3_2A36 = 0;
            }
        }
        DrawMower();
        if (native_state_fd_50F6_10A0.signed_value)
            DrawSimBird();
        else if (g_2A2E != -1) {
            hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A2E);
            g_2A2E = -1;
        }
        if (fd_3D57_0C44)
            DrawForSale();
        if (native_state_fd_50F6_0352.signed_value)
            DrawRain();
        else
            for (i = 0; i <= 14; i++)
                if (fd_50F6_38CA[i] != -1) {
                    hanim_RemoveAnimObject(native_game_fd_50F6_10DA, fd_50F6_38CA[i]);
                    fd_50F6_38CA[i] = -1;
                }
        DrawSwarm();
        DrawAnimYardMessage();
        hanim_RenderAnimSet(native_game_fd_50F6_10DA);
    } else {
        fd_3D57_0C20 = 0;
        if (mode == 2)
            DrawSimColonies(mode);
        else
            DrawColonyBars(mode);
    }
    DrawYardCursor();
}

extern SimYardCacheHandle f_24AB_0002(char *text);
void  DrawAnimYardMessage(void)
{
    if (g_2A40 != -1) {
        hanim_RemoveAnimObject(native_game_fd_50F6_10DA, g_2A40);
        g_2A40 = -1;
    }
    if (fd_55B3_2A3A) {
        f_171C_1C0A(fd_55B3_2A3A);
        fd_55B3_2A3A = 0;
    }
    if (fd_55B3_299A) {
        f_24AB_02AD(2);
        fd_55B3_2A3A = f_24AB_0002(fd_55B3_299A);
        f_24AB_02AD(0);
        g_2A40 = hanim_AddAnimObject(native_game_fd_50F6_10DA,
                             ((*((struct Rect *)native_game_fd_50F6_10D2.raw)).right - fd_50F6_392C.width + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left) / 2,
                             (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 4, 0x7531, 999);
    }
}

extern int16_t  SRand1(int16_t range);

void  DrawRain(void)
{
    int16_t x, y, i;

    i = 14;
    while (i--) {
        x = SRand1(400) + 50;
        y = SRand1(150);
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
        y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
        if (fd_50F6_38CA[i] != -1)
            hanim_SetObjectPos(x, y, 0x1b5d, native_game_fd_50F6_10DA, fd_50F6_38CA[i], 0x8000);
        else
            fd_50F6_38CA[i] = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, 0x1b5d, 1000);
    }
}

extern int16_t  fd_3D57_07C8;
int16_t  TooFar(int16_t x, int16_t y);
extern int16_t  SRand16(void);

void  DrawSwarm(void)
{
    int16_t i, x, y;

    if (fd_3D57_07C8 == 0) {
        native_state_fd_50F6_1048.signed_value = native_sim_state_fd_50F6_07CA.words[1] * 10 + 0x2e;
        native_state_fd_50F6_103C.signed_value = native_sim_state_fd_50F6_07CA.words[0] * 28 - native_sim_state_fd_50F6_07CA.words[1] * 10 + 0xb2;
        for (i = 0; i < native_state_fd_50F6_06AA.signed_value; i++) {
            if (i >= 16 || native_state_fd_50F6_07C8.signed_value <= i)
                break;
            if (TooFar(native_sim_state_fd_50F6_0F46.signed_values[i], native_sim_state_fd_50F6_0F84.signed_values[i])) {
                native_sim_state_fd_50F6_0F46.signed_values[i] = SRand16() - 10;
                native_sim_state_fd_50F6_0F84.signed_values[i] = SRand16() - 10;
            }
            native_sim_state_fd_50F6_0F46.signed_values[i] += SRand1(3) - 1;
            x = native_sim_state_fd_50F6_0F46.signed_values[i] + native_state_fd_50F6_103C.signed_value;
            native_sim_state_fd_50F6_0F84.signed_values[i] += SRand1(3) - 1;
            y = native_sim_state_fd_50F6_0F84.signed_values[i] + native_state_fd_50F6_1048.signed_value;
            if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
            y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
            if (fd_50F6_38E8[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5e, native_game_fd_50F6_10DA, fd_50F6_38E8[i], -1);
            else
                fd_50F6_38E8[i] = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, 0x1b5e, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_38E8[i] != -1) {
                hanim_RemoveAnimObject(native_game_fd_50F6_10DA, fd_50F6_38E8[i]);
                fd_50F6_38E8[i] = -1;
            }
        for (i = 0; i < native_state_fd_50F6_073A.signed_value; i++) {
            if (i >= 16 || native_state_fd_50F6_0850.signed_value <= i)
                break;
            if (TooFar(native_sim_state_fd_50F6_0FC6.signed_values[i], native_sim_state_fd_50F6_1008.signed_values[i]))
                native_sim_state_fd_50F6_1008.signed_values[i] = native_sim_state_fd_50F6_0FC6.signed_values[i] = 0;
            native_sim_state_fd_50F6_0FC6.signed_values[i] += SRand1(3) - 1;
            x = native_sim_state_fd_50F6_0FC6.signed_values[i] + native_state_fd_50F6_103C.signed_value;
            native_sim_state_fd_50F6_1008.signed_values[i] += SRand1(3) - 1;
            y = native_sim_state_fd_50F6_1008.signed_values[i] + native_state_fd_50F6_1048.signed_value;
            if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
            y += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
            if (fd_50F6_390A[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5f, native_game_fd_50F6_10DA, fd_50F6_390A[i], -1);
            else
                fd_50F6_390A[i] = hanim_AddAnimObject(native_game_fd_50F6_10DA, x, y, 0x1b5f, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_390A[i] != -1) {
                hanim_RemoveAnimObject(native_game_fd_50F6_10DA, fd_50F6_390A[i]);
                fd_50F6_390A[i] = -1;
            }
    }
}

int16_t  TooFar(int16_t x, int16_t y)
{
    if (x > 15 || x < -15 || y > 15 || y < -15)
        return 1;
    return 0;
}

extern void  clip_Push(void);
extern void  f_1FAA_0006(struct Pt  *pts, int16_t a, int16_t b);
extern void  clip_Pop(void);

/* SCAFFOLD BEGIN: InvertPatch draft: one byte short. Original layout (worker resA): i -2, org -6/-4 directly above pts[4] (-0x16), CSE temps x*28 -0x1c, y*10 -0x1a, left -0x18, top -0x1e; h and v live in SI/DI with no BP homes and x, y are not enregistered; the first org.h is computed as x*28 + (left - y*10). The sibling DrawSimColonies became exact once org was dropped (h/v homes) and color = c == 0 ? 3 : 2 */
void  InvertPatch(int16_t x, int16_t y)
{
    struct Pt pts[4];
    struct Pt org;
    int16_t i, h, v;

    clip_Push();
    clip_SetWin(0x1900);
    org.h = x * 28 - y * 10 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    org.v = y * 10 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    h = x * 28 - y * 10;
    v = y * 10;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        h = (h >> 1) + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + 4;
        v = (v >> 1) + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 10;
        org.h = h;
        org.v = v;
        for (i = 0; i < 4; i++) {
            pts[i].h = fd_55B3_2A42[i * 2] / 2 + org.h;
            pts[i].v = fd_55B3_2A42[i * 2 + 1] / 2 + v;
        }
    } else {
        h += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
        v += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
        org.h = h;
        org.v = v;
        for (i = 0; i < 4; i++) {
            pts[i].h = fd_55B3_2A42[i * 2] + org.h;
            pts[i].v = fd_55B3_2A42[i * 2 + 1] + v;
        }
    }
    f_1FAA_0006(pts, -1, -1);
    clip_Pop();
}

/* SCAFFOLD END */

extern uint8_t  fd_3D57_0164[12][16];
extern uint8_t  fd_3D57_00A4[12][16];

void  DrawSimColonies(int16_t mode)
{
    struct Pt pts[4];
    int16_t x, y, i, c, color, h, v;

    if (mode == 2)
        for (x = 0; x < 12; x++)
            for (y = 0; y < 16; y++) {
                c = fd_3D57_0164[x][y];
                if (fd_3D57_00A4[x][y] == 0)
                    color = c == 0 ? 3 : 2;
                else
                    color = c != 0;
                h = x * 28 - y * 10;
                v = y * 10;
                if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
                    h >>= 1;
                    v >>= 1;
                    h += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + 4;
                    v += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 10;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = (i >= 2 ? 0 : -1) + fd_55B3_2A42[i * 2] / 2 + h;
                        pts[i].v = (i >= 2 ? -1 : 1) + fd_55B3_2A42[i * 2 + 1] / 2 + v;
                    }
                } else {
                    h += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
                    v += (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = fd_55B3_2A42[i * 2] + h;
                        pts[i].v = fd_55B3_2A42[i * 2 + 1] + v;
                    }
                }
                f_1FAA_0006(pts, f_1B4E_000D(g_2ACA[color]), f_1B4E_000D(g_2AD2[color]));
            }
}


extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);

void  DrawColonyBars(int16_t mode)
{
    struct Rect r;
    int16_t x, y, h, l, t;
    int16_t baseLeft;

    for (x = 0; x < 12; x++)
        for (y = 0; y < 16; y++) {
            h = (fd_3D57_00A4[x][y] + 3) >> 2;
            if (h > 0) {
                if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
                    t = y * 10 + 12;
                    l = ((x + 6) * 28 - t) / 2 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + 10;
                    r.bottom = (t + 0x47) / 2 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    r.left = (x + 6) * 28 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
                    r.left -= y * 10;
                    r.bottom = y * 10 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 0x47;
                    r.top = r.bottom - h;
                    r.right = r.left + 9;
                }
                f_1CE2_046D(&r, f_1B4E_000D(15));
            }
            h = (fd_3D57_0164[x][y] + 3) >> 2;
            if (h > 0) {
                if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
                    t = y * 10 + 12;
                    l = (x * 28 - t + 0xb4) / 2 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left + 10;
                    r.bottom = (t + 0x47) / 2 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    baseLeft = x * 28 + ((*((struct Rect *)native_game_fd_50F6_10D2.raw)).left - y * 10);
                    l = baseLeft + 0xb4;
                    r.left = l;
                    r.bottom = y * 10 + (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top + 0x47;
                    r.top = r.bottom - h;
                    r.right = l + 9;
                }
                f_1CE2_046D(&r, f_1B4E_000D(0x23));
            }
        }
}


extern void  WinPrintf(char  *format, ...);
extern void  XferPatch(void);

void  YardArea(struct Event  *ev)
{
    int16_t x, y;

    y = ev->v - (*((struct Rect *)native_game_fd_50F6_10D2.raw)).top;
    x = ev->h - (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        x = (x + 2) * 2;
        y = (y - 8) * 2;
    }
    y = (y - fd_55B3_2A42[1]) / 10;
    x = (y * 10 - fd_55B3_2A42[0] + x) / 28;
    WinPrintf("\nYARD AREA @ %d, %d  : %d, %d", x, y, 12, 16);
    if (x >= 0 && x < 12 && y >= 0 && y < 16) {
        EraseYardCursor();
        native_sim_state_fd_50F6_07BC.words[0] = x;
        native_sim_state_fd_50F6_07BC.words[1] = y;
        if (ev->modifiers & 0x6000)
            XferPatch();
        DrawYardCursor();
    }
}


#pragma pack(pop)
