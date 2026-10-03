#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#include "portable/whole_program/state/elevator_thumb_size.h"
#include "portable/whole_program/state/menu_bar_rect.h"
#pragma pack(push, 2)
extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 20E8: window loading and window-stack operations. */



void  f_20E8_0000(void);

void ( *g_62E0)(int16_t win) = f_20E8_0000;
void ( *g_62E4)(void) = f_20E8_0000;
void ( *g_62E8)(void) = f_20E8_0000;
void ( *g_62EC)(void) = f_20E8_0000;
void ( *g_62F0)(void) = f_20E8_0000;
void ( *g_62F4)(int16_t win) = f_20E8_0000;
int16_t g_62F8 = 0;
int16_t g_62FA = -1;
int16_t g_62FC = 0;
int16_t g_62FE = 0;
int16_t g_6300 = 0;

void  f_20E8_0000(void)
{
}

extern char  *  *  f_1A53_00F0(int16_t object, int16_t kind, int16_t type);
extern void  Punt(char  *format, ...);

extern void  win_LockWin(int16_t win);
extern void  RepointObjects(int16_t win);
extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];
extern void  win_UnlockWin(int16_t win);

void  win_LoadWindow(int16_t win)
{
    char  *  *h;
    char  *obj;
    int16_t i;
    char  *w;

    h = f_1A53_00F0((char)(win >> 8), 0, 1);
    if (h == 0)
        Punt("CANNOT LOAD WINDOW %03x", win);
    win_handles[(char)(win >> 8)] = h;
    w = *h;
    win_LockWin(win);
    RepointObjects(win);
    obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]);
    if (win_offsets[(char)(win >> 8)].left != (int16_t)0x8000)
        *(struct Rect  *)(obj + 8) = win_offsets[(char)(win >> 8)];
    else
        win_offsets[(char)(win >> 8)] = *(struct Rect  *)(obj + 8);
    for (i = 0; i < sim_window_wire_read_i16(w, 0x0c); i++) {
        obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (i == 0)
            *(struct Rect  *)w = *(struct Rect  *)obj;
        switch (obj[0x21]) {
        case 4:
            if (sim_window_ref_registry_clear_runtime_for_object(&sim_window_ref_registry, (char *)obj, 0x2a, 14) != SIM_WINDOW_REFS_OK)
            { Punt("window type-4 runtime clear failed"); return; };
            break;
        case 16:
        case 17:
        case 18:
            if (sim_window_ref_registry_clear_runtime_for_object(&sim_window_ref_registry, (char *)obj, 0x2a, 4) != SIM_WINDOW_REFS_OK)
                { Punt("window text Handle clear failed"); return; }
            break;
        }
    }
    win_UnlockWin(win);
}


struct Rect g_635C = { (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000 };

extern void  font_InitFonts(void);
extern void  win_LockInit(void);
extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];

extern char  *  *  db_LoadObject(int16_t object, int16_t kind);
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);
extern void  db_PurgeObject(int16_t object, int16_t kind);
struct Pt {
    int16_t x;
    int16_t y;
};
extern void  f_208F_0419(struct Pt  *size, int16_t id);



extern int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];
extern void  db_UnhookObject(int16_t object, int16_t kind);

int16_t  win_LoadAllWindows(void)
{
    char purge[0x28];
    int16_t i;
    char  *  *h;
    int16_t  *p;
    char  *q;

    font_InitFonts();
    win_LockInit();
    sim_window_source_clear_draw_hooks(win_drawHooks, 45);
    for (i = 0; i < 45; i++) win_offsets[i] = g_635C;
    h = db_LoadObject(g_5A97, 9);
    if (h) {
        _fmemcpy(win_offsets, f_171C_1B84(h), 0x140);
        f_171C_1BBA(h);
        db_PurgeObject(g_5A97, 9);
    }
    f_208F_0419(&fd_50F6_47DA, 0x6f);
    h = db_LoadObject(0x80, 0);
    if (h == 0) {
        Punt("Cannot load resource\nplease try another");
    } else {
        p = (int16_t  *)*h;
        win_numOfWindows = p[0];
        win_numOfColors = p[1];
        win_numOfGroups = p[2];
        db_PurgeObject(0x80, 0);
    }
    if (!sim_window_source_reserve_colors(win_numOfColors)) {
        Punt("window color table allocation failed");
        return 0;
    }
    h = db_LoadObject(0x81, 0);
    _fmemcpy(win_colors, *h, (uint16_t)(win_numOfColors * 6));
    db_PurgeObject(0x81, 0);
    h = db_LoadObject(0x83, 0);
    q = *h;
    if (h == 0)
        Punt("Could not load purge list");
    _fmemcpy(purge, q, 0x28);
    db_PurgeObject(0x83, 0);
    for (i = 0; i < win_numOfWindows; i++) {
        if (purge[i] == 0) {
            win_LoadWindow(i << 8);
            db_UnhookObject(i, 0);
        }
    }
    return 1;
}

extern char  *  f_2505_0006(int16_t win);
extern int16_t g_5702[];
extern void  f_2505_08EA(int16_t win);
extern void  clip_KillWin(int16_t win);
extern void  win_Recalc(int16_t win);
extern void  f_1E57_00B1(int16_t win);
extern void  f_2505_0831(int16_t win);
extern void  clip_SetWin(int16_t win);
extern void  win_DrawWindow(int16_t win);
extern void  clip_Off(void);

void  win_Swap(int16_t from, int16_t to, int16_t unused, int16_t p0, int16_t p1, int16_t p2, int16_t p3)
{
    char  *w;
    struct Rect origin;
    struct Rect rect;
    char  *obj;

    win_LockWin(from);
    w = f_2505_0006(from);
    origin = *(struct Rect  *)(((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]) + 8);
    rect = *(struct Rect  *)w;
    if (g_5702[0] != 0)
        f_2505_08EA(g_5702[0]);
    if (*(int16_t  *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(from);
        clip_KillWin(from);
        *(int16_t  *)(w + 0x1c) &= ~0x200;
        (*g_62E0)(from);
    }
    win_UnlockWin(from);
    win_LockWin(to);
    w = f_2505_0006(to);
    obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]);
    *(int16_t  *)(obj + 8) = origin.left;
    *(int16_t  *)(obj + 0xa) = origin.top;
    *(struct Rect  *)w = rect;
    *(struct Rect  *)obj = *(struct Rect  *)w;
    ((int16_t  *)(w + 0x10))[0] = p0;
    ((int16_t  *)(w + 0x10))[1] = p1;
    ((int16_t  *)(w + 0x10))[2] = p2;
    ((int16_t  *)(w + 0x10))[3] = p3;
    win_Recalc(to);
    (*g_62E0)(to);
    *(int16_t  *)(f_2505_0006(to) + 0x1c) |= 0x200;
    if (g_5702[0] != (int16_t)0x8000)
        f_2505_08EA(g_5702[0]);
    f_1E57_00B1(to);
    f_2505_0831(to);
    clip_SetWin(to);
    win_DrawWindow(to);
    (*g_62E8)();
    win_UnlockWin(to);
    clip_Off();
}

extern void  win_LockWinHigh(int16_t win);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  win_FlushEvents(void);

void  win_Open(int16_t win, ...)
{
    char  *w;
    int16_t dx;
    int16_t dy;
    struct Rect r;
    int16_t  *origin;

    if (g_5702[0] != win) {
        win_LockWinHigh(win);
        (*g_62E4)();
        w = f_2505_0006(win);
        ((int16_t  *)(w + 0x10))[0] = (&win)[1];
        ((int16_t  *)(w + 0x10))[1] = (&win)[2];
        ((int16_t  *)(w + 0x10))[2] = (&win)[3];
        ((int16_t  *)(w + 0x10))[3] = (&win)[4];
        win_Recalc(win);
        w = f_2505_0006(win);
        if (*(int16_t  *)(w + 0x1c) & 0x1000) {
            dx = dy = 0;
            win_GetObjRect(win, &r);
            if (r.bottom > SIM_GRAPHICS_SOURCE_g_3DB4)
                dy = SIM_GRAPHICS_SOURCE_g_3DB4 - r.bottom;
            else if (r.top <= fd_50F6_393C.bottom)
                dy = fd_50F6_393C.bottom - r.top;
            if (r.left < 0)
                dx = -r.left;
            else if (r.right >= SIM_GRAPHICS_SOURCE_g_3DB2)
                dx = SIM_GRAPHICS_SOURCE_g_3DB2 - r.right;
            origin = (int16_t  *)(((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]) + 8);
            win_offsets[win >> 8] = *(struct Rect  *)origin;
            origin[0] += dx;
            origin[1] += dy;
            win_Recalc(win);
        }
        (*g_62E0)(win);
        *(int16_t  *)(f_2505_0006(win) + 0x1c) |= 0x200;
        if (g_5702[0] != (int16_t)0x8000)
            f_2505_08EA(g_5702[0]);
        f_1E57_00B1(win);
        f_2505_0831(win);
        clip_SetWin(win);
        win_DrawWindow(win);
        (*g_62E8)();
        clip_Off();
        win_UnlockWin(win);
    }
    win_FlushEvents();
}

extern void  f_21FA_0B4B(struct Rect  *rect);

void  win_Close(int16_t win)
{
    char  *w;
    struct Rect r;

    win_LockWin(win);
    w = f_2505_0006(win);
    if (*(int16_t  *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(win);
        if (g_5702[0] == win) {
            f_2505_08EA(win);
            clip_KillWin(win);
            if (g_5702[0] != (int16_t)0x8000)
                f_2505_0831(g_5702[0]);
        } else {
            clip_KillWin(win);
        }
        *(int16_t  *)(w + 0x1c) &= ~0x200;
        if (*(int16_t  *)(w + 0x1c) & 0x1000)
            *(struct Rect  *)(((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]) + 8) = win_offsets[(char)(win >> 8)];
        (*g_62E0)(win);
        r = *(struct Rect  *)w;
        win_UnlockWin(win);
        f_21FA_0B4B(&r);
        (*g_62E8)();
        clip_Off();
    } else {
        win_UnlockWin(win);
    }
}

extern char  *  win_WinAddr(int16_t win);

void  f_20E8_0725(int16_t win)
{
    int16_t top;
    int16_t flag;

    top = g_5702[0];
    if (top != win) {
        if (top != (int16_t)0x8000) {
            win_LockWin(top);
            flag = *(int16_t  *)(win_WinAddr(top) + 0x1c) & 1;
            win_UnlockWin(top);
            if (flag)
                win_Close(top);
        }
        win_Open(win);
    }
}

extern void  f_1E57_0052(int16_t win);
extern void  f_21FA_0AD2(struct Rect  *rect);

void  f_20E8_0776(int16_t win)
{
    int16_t flag;
    char  *w;
    struct Rect r;

    win_LockWin(win);
    f_2505_0006(win);
    flag = *(int16_t  *)(win_WinAddr(g_5702[0]) + 0x1c) & 1;
    win_UnlockWin(win);
    (*g_62E4)();
    if (g_5702[0] == win) {
        if (g_5702[1] != (int16_t)0x8000) {
            if (flag) {
                win_Close(g_5702[0]);
                return;
            }
            f_1E57_0052(win);
            if (g_5702[0] != win) {
                f_2505_08EA(win);
                f_2505_0831(g_5702[0]);
            }
        }
    } else {
        f_1E57_0052(win);
    }
    win_LockWin(win);
    w = f_2505_0006(win);
    *(int16_t  *)(w + 0x1c) |= 0x200;
    r = *(struct Rect  *)w;
    win_UnlockWin(win);
    (*g_62E0)(win);
    f_21FA_0AD2(&r);
    (*g_62E8)();
    clip_Off();
}

void  win_SetWinDrawHook(int16_t win, void ( *hook)(int16_t phase))
{
    win_drawHooks[win >> 8] = hook;
}

void  f_20E8_088B(void ( *hook)(int16_t win))
{
    g_62E0 = hook;
}

void  f_20E8_089F(void ( *hook)(int16_t win))
{
    g_62F4 = hook;
}

void  f_20E8_08B3(void ( *hook)(void))
{
    g_62E4 = hook;
}

void  f_20E8_08C7(void ( *hook)(void))
{
    g_62E8 = hook;
}

void  f_20E8_08DB(void ( *hook)(void))
{
    g_62EC = hook;
}

void  f_20E8_08EF(void ( *hook)(void))
{
    g_62F0 = hook;
}

/* SCAFFOLD BEGIN: f_20E8_0903 best draft.
   Residue: loops 2/3 index with DI=i*2 and base in BX (les bx,[ptr];
   mov ax,es:[bx+di]); the original moves the index to BX and loads the far
   base into DI (mov bx,di; les di,[ptr]; ...) with a dead les bx,[bp-20h]
   before rect[i]-o[i]: 258 vs 286 bytes. */
extern int16_t  *  win_ObjAddr(int16_t obj);

void  f_20E8_0903(int16_t obj, int16_t  *rect)
{
    int16_t j;
    int16_t win;
    int16_t  *o;
    int16_t  *origin;
    int16_t  *mode;
    int16_t  *ref;
    int16_t i;

    win = obj & 0xff00;
    win_LockWin(win);
    o = win_ObjAddr(obj);
    origin = o + 4;
    mode = o + 12;
    ref = o + 8;
    for (j = 0; j < 4; j++)
        origin[j] = 0;
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = 0;
        else
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    win_UnlockWin(win);
}

/* SCAFFOLD END */

extern int16_t  f_2505_036E(void);

void  f_20E8_0A21(void)
{
    int16_t top;

    top = g_5702[0];
    if (f_2505_036E()) {
        win_LockWin(top);
        if (*(int16_t  *)(win_WinAddr(top) + 0x1c) & 1)
            win_Close(top);
        win_UnlockWin(top);
    }
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");

#pragma pack(pop)
