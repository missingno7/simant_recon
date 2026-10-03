#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/state/menu_bar_rect.h"
#pragma pack(push, 2)
/* Overlay section S26, code frame 39C7: window zoom, drag and grow with screen constraints (_fastcall window API). */

#include <string.h>



struct Obj;

struct Win {
    struct Rect rect;
    char pad08[0x0c - 0x08];
    int16_t count;
    char pad0E[0x18 - 0x0e];
    int16_t minWidth;
    int16_t minHeight;
    uint16_t flags;
    char pad1E[0x20 - 0x1e];
    int16_t gridX;
    int16_t gridY;
    struct Rect zoomRect;
    struct Obj  *objs[2];
};

struct Obj {
    struct Rect rect;
    int16_t x;
    int16_t y;
    int16_t width;
    int16_t height;
    char pad10[0x21 - 0x10];
    char type;
};

struct Pt {
    int16_t x;
    int16_t y;
};

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

void  o26_39C7_022F(int16_t win, int16_t mode, struct Rect  *r);

extern void  win_LockWin(int16_t win);
extern struct Win  *  win_WinAddr(int16_t win);
extern void  win_UnlockWin(int16_t win);
extern struct Obj  *  win_ObjAddr(int16_t obj);
extern struct Rect  *  win_WinRectAddr(int16_t win);
extern void  win_Recalc(int16_t win);
extern void  f_1E57_038E(void);
extern void ( *  g_62EC)(int16_t win);
extern void  clip_SetWin(int16_t win);
extern void  f_1E57_0D97(struct Rect  *r);
extern void  f_1E57_0FDC(struct Rect  *r);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  clip_Push(void);
extern void  f_1E57_0296(void);
extern void  f_1FD2_05FD(void);
extern void  clip_Pop(void);
extern void  clip_SubExclude(struct Rect  *r);
extern int16_t  g_5702[];
extern void  f_1E57_0A9C(struct Rect  *r);
extern void  win_DrawWindow(int16_t win);
extern void  f_2505_08EA(int16_t win);
extern void  f_2505_0831(int16_t win);

void  o26_39C7_0000(int16_t win)
{
    struct Win  *w;
    struct Obj  *o;
    struct Rect r;
    struct Rect saved;
    int16_t i;

    if (win == (int16_t)0x8000)
        return;
    win_LockWin(win);
    w = win_WinAddr(win);
    if (!(w->flags & 0x100)) {
        win_UnlockWin(win);
        return;
    }
    o = win_ObjAddr(win);
    if (w->flags & 0x80) {
        *(struct Rect  *)&o->x = w->zoomRect;
        w->flags &= ~0x80;
        saved = w->rect;
    } else {
        w->zoomRect = *(struct Rect  *)&o->x;
        r.left = 0;
        r.top = fd_50F6_393C.bottom;
        o26_39C7_022F(win, 0, &r);
        w->rect = r;
        r.bottom = SIM_GRAPHICS_SOURCE_g_3DB4;
        r.right = SIM_GRAPHICS_SOURCE_g_3DB2;
        o26_39C7_022F(win, 1, &r);
        w->flags |= 0x80;
        o->x = r.left;
        o->width = r.right - r.left;
        o->y = r.top;
        o->height = r.bottom - r.top;
        *win_WinRectAddr(win) = r;
    }
    win_Recalc(win);
    f_1E57_038E();
    (*g_62EC)(win);
    if (w->flags & 0x80) {
        clip_SetWin(win);
        f_1E57_0D97(&saved);
    } else {
        f_1E57_0FDC(&saved);
        win_GetObjRect(win, &r);
    }
    win_UnlockWin(win);
    clip_Push();
    f_1E57_0296();
    f_1FD2_05FD();
    clip_Pop();
    clip_SubExclude(&r);
    for (i = 1; g_5702[i] != (int16_t)0x8000; i++)
        ;
    while (--i >= 1) {
        clip_Push();
        win_GetObjRect(g_5702[i], &r);
        f_1E57_0A9C(&r);
        win_DrawWindow(g_5702[i]);
        clip_Pop();
    }
    clip_SetWin(win);
    win_DrawWindow(g_5702[0]);
    f_2505_08EA(win);
    f_2505_0831(win);
}

extern void  f_22BF_0B5B(struct Rect  *dst, struct Rect  *src, int16_t l, int16_t t, int16_t r, int16_t b);

void  o26_39C7_022F(int16_t win, int16_t mode, struct Rect  *r)
{
    struct Rect  *wr;
    struct Win  *w;
    int16_t dy;
    int16_t dx;
    struct Rect old;
    int16_t done;
    int16_t g;
    int16_t gx;
    int16_t gy;
    int16_t h;

    wr = win_WinRectAddr(win);
    w = win_WinAddr(win);
    if (mode) {
        dy = r->bottom - wr->bottom;
        dx = r->right - wr->right;
    } else {
        dy = r->top - wr->top;
        dx = r->left - wr->left;
    }
    old = *r;
    do {
        done = 0;
        if (r->left < SIM_GRAPHICS_SOURCE_g_3DB2 && !((w->flags & 0x1000) && r->right > SIM_GRAPHICS_SOURCE_g_3DB2) &&
            r->right - r->left < SIM_GRAPHICS_SOURCE_g_3DB2) {
            if (r->right >= 0 && r->right - r->left >= w->minWidth && !((w->flags & 0x1000) && r->left < 0)) {
                if (r->top <= SIM_GRAPHICS_SOURCE_g_3DB4 && !((w->flags & 0x1000) && r->bottom > SIM_GRAPHICS_SOURCE_g_3DB4)) {
                    if (r->top > fd_50F6_393C.bottom && r->bottom - r->top >= w->minHeight)
                        done = 1;
                    else
                        dy++;
                } else
                    dy--;
            } else
                dx++;
        } else
            dx--;
        gx = dx;
        if ((g = w->gridX) != 0)
            gx -= gx % g;
        gy = dy;
        if ((h = w->gridY) != 0)
            gy -= gy % h;
        if (mode)
            f_22BF_0B5B(r, wr, 0, 0, gx, gy);
        else
            f_22BF_0B5B(r, wr, gx, gy, gx, gy);
        if (_fmemcmp(&old, r, 8))
            done = 0;
        old = *r;
    } while (!done);
}

extern void  f_1E57_0351(void);
extern void  f_2505_0382(struct Pt  *center, struct Rect  *rect);
extern void  f_1B73_09E9(int16_t x, int16_t y);
extern void  GRectInvOutline(struct Rect  *r, int16_t width);
extern void  ButtonHeldInit(void);
extern int16_t  ButtonHeld(void);
extern int16_t  g_9122;
extern int16_t  g_9124;
extern void  f_1FD2_04D0(struct Pt  *pt);
extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];
extern void  f_21FA_0B4B(struct Rect  *rect);
extern int16_t  StillDown(void);
extern void  win_FlushEvents(void);

void  o26_39C7_040F(struct Event  *ev)
{
    int16_t win;
    struct Rect  *wr;
    struct Rect orig;
    struct Win  *w;
    struct Obj  *o;
    struct Rect orect;
    struct Pt start;
    struct Pt pt;
    struct Rect r;

    if ((win = g_5702[0]) == (int16_t)0x8000)
        return;
    win_LockWin(win);
    wr = win_WinRectAddr(win);
    orig = *wr;
    w = win_WinAddr(win);
    if (w->count < 2) {
        win_UnlockWin(win);
        return;
    }
    o = w->objs[1];
    if (o->type != 0x0c && o->type != 0x12) {
        win_UnlockWin(win);
        return;
    }
    f_1E57_0351();
    orect = o->rect;
    if (ev == 0) {
        f_2505_0382(&start, &orect);
        f_1B73_09E9(start.x, start.y);
    } else {
        start.x = ev->h;
        start.y = ev->v;
    }
    r = *wr;
    GRectInvOutline(&r, 2);
    pt = start;
    ButtonHeldInit();
    while (ButtonHeld()) {
        if (pt.x != g_9122 || pt.y != g_9124) {
            GRectInvOutline(&r, 2);
            f_1FD2_04D0(&pt);
            f_22BF_0B5B(&r, wr, pt.x - start.x, pt.y - start.y, pt.x - start.x, pt.y - start.y);
            GRectInvOutline(&r, 2);
        }
    }
    GRectInvOutline(&r, 2);
    o26_39C7_022F(win, 0, &r);
    o = w->objs[0];
    o->x += r.left - orig.left;
    o->y += r.top - orig.top;
    *win_WinRectAddr(win) = r;
    w = win_WinAddr(win);
    win_offsets[win >> 8] = *(struct Rect  *)&w->objs[0]->x;
    win_Recalc(win);
    win_UnlockWin(win);
    f_1E57_038E();
    (*g_62EC)(win);
    f_21FA_0B4B(&orig);
    f_2505_08EA(win);
    f_2505_0831(win);
    while (StillDown())
        ;
    win_FlushEvents();
}

extern int16_t  f_1FD2_04B3(int16_t id, struct Rect  *r);
extern void  Punt(char  *fmt, ...);

void  o26_39C7_0671(struct Event  *ev)
{
    int16_t win;
    struct Win  *w;
    struct Rect orig;
    struct Pt min;
    struct Rect icon;
    struct Pt start;
    struct Pt pt;
    struct Rect r;
    struct Obj  *o;

    if ((win = g_5702[0]) == (int16_t)0x8000)
        return;
    win_LockWin(win);
    w = win_WinAddr(win);
    if (!(w->flags & 8)) {
        win_UnlockWin(win);
        return;
    }
    w->flags &= ~0x80;
    orig = w->rect;
    min = *(struct Pt  *)&w->minWidth;
    if (min.x == 0)
        min.x = 0x30;
    if (min.y == 0)
        min.y = 0x30;
    if (!f_1FD2_04B3(0xf084, &icon))
        Punt("Couldn't find resize icoN!!");
    f_1E57_0351();
    if (ev == 0) {
        f_2505_0382(&start, &icon);
        f_1B73_09E9(start.x, start.y);
    } else {
        start.x = ev->h;
        start.y = ev->v;
    }
    r = orig;
    GRectInvOutline(&r, 2);
    pt = start;
    ButtonHeldInit();
    while (ButtonHeld()) {
        if (pt.x != g_9122 || pt.y != g_9124) {
            GRectInvOutline(&r, 2);
            f_1FD2_04D0(&pt);
            f_22BF_0B5B(&r, &orig, 0, 0, pt.x - start.x, pt.y - start.y);
            if (r.right - r.left < min.x)
                r.right = min.x + r.left;
            if (r.bottom - r.top < min.y)
                r.bottom = min.y + r.top;
            GRectInvOutline(&r, 2);
        }
    }
    GRectInvOutline(&r, 2);
    o26_39C7_022F(win, 1, &r);
    o = w->objs[0];
    o->width += r.right - orig.right;
    o->height += r.bottom - orig.bottom;
    *win_WinRectAddr(win) = r;
    win_Recalc(win);
    win_UnlockWin(win);
    f_1E57_038E();
    (*g_62EC)(win);
    f_21FA_0B4B(&orig);
    f_2505_08EA(win);
    f_2505_0831(win);
    win_FlushEvents();
}

#pragma pack(pop)
