/*
 * Tracks window zooming, dragging and resizing. It constrains the resulting rectangles to the
 * screen and uses the resize icon.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 26 (S26); segment 39C7; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Og /Oe /Gs /Zi.
 */

#include <string.h>

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Obj;

struct Win {
    struct Rect rect;
    char pad08[0x0c - 0x08];
    int count;
    char pad0E[0x18 - 0x0e];
    int minWidth;
    int minHeight;
    unsigned flags;
    char pad1E[0x20 - 0x1e];
    int gridX;
    int gridY;
    struct Rect zoomRect;
    struct Obj far *objs[2];
};

struct Obj {
    struct Rect rect;
    int x;
    int y;
    int width;
    int height;
    char pad10[0x21 - 0x10];
    char type;
};

struct Pt {
    int x;
    int y;
};

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

void _fastcall win_constrain_drag_rect(int win, int mode, struct Rect far *r);

extern void _fastcall win_LockWin(int win);
extern struct Win far * _fastcall win_WinAddr(int win);
extern void _fastcall win_UnlockWin(int win);
extern struct Obj far * _fastcall win_ObjAddr(int obj);
extern struct Rect far fd_50F6_393C;
extern int near g_3DB4;
extern int near g_3DB2;
extern struct Rect far * _fastcall win_WinRectAddr(int win);
extern void _fastcall win_Recalc(int win);
extern void far win_rebuild_visible_clips(void);
extern void (far * far g_62EC)(int win);
extern void far clip_SetWin(int win);
extern void far clip_expand_by_rect(struct Rect far *r);
extern void far clip_set_screen_intersection(struct Rect far *r);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far clip_set_desktop_region(void);
extern void far win_redraw_desktop_menu(void);
extern void far clip_Pop(void);
extern void far clip_SubExclude(struct Rect far *r);
extern int far g_5702[];
extern void far clip_restrict_rect(struct Rect far *r);
extern void _fastcall win_DrawWindow(int win);
extern void _fastcall win_deactivate_pointer_regions(int win);
extern void _fastcall win_activate_pointer_regions(int win);

void _fastcall win_toggle_zoom(int win)
{
    struct Win far *w;
    struct Obj far *o;
    struct Rect r;
    struct Rect saved;
    int i;

    if (win == (int)0x8000)
        return;
    win_LockWin(win);
    w = win_WinAddr(win);
    if (!(w->flags & 0x100)) {
        win_UnlockWin(win);
        return;
    }
    o = win_ObjAddr(win);
    if (w->flags & 0x80) {
        *(struct Rect far *)&o->x = w->zoomRect;
        w->flags &= ~0x80;
        saved = w->rect;
    } else {
        w->zoomRect = *(struct Rect far *)&o->x;
        r.left = 0;
        r.top = fd_50F6_393C.bottom;
        win_constrain_drag_rect(win, 0, &r);
        w->rect = r;
        r.bottom = g_3DB4;
        r.right = g_3DB2;
        win_constrain_drag_rect(win, 1, &r);
        w->flags |= 0x80;
        o->x = r.left;
        o->width = r.right - r.left;
        o->y = r.top;
        o->height = r.bottom - r.top;
        *win_WinRectAddr(win) = r;
    }
    win_Recalc(win);
    win_rebuild_visible_clips();
    (*g_62EC)(win);
    if (w->flags & 0x80) {
        clip_SetWin(win);
        clip_expand_by_rect(&saved);
    } else {
        clip_set_screen_intersection(&saved);
        win_GetObjRect(win, &r);
    }
    win_UnlockWin(win);
    clip_Push();
    clip_set_desktop_region();
    win_redraw_desktop_menu();
    clip_Pop();
    clip_SubExclude(&r);
    for (i = 1; g_5702[i] != (int)0x8000; i++)
        ;
    while (--i >= 1) {
        clip_Push();
        win_GetObjRect(g_5702[i], &r);
        clip_restrict_rect(&r);
        win_DrawWindow(g_5702[i]);
        clip_Pop();
    }
    clip_SetWin(win);
    win_DrawWindow(g_5702[0]);
    win_deactivate_pointer_regions(win);
    win_activate_pointer_regions(win);
}

extern void _fastcall win_offset_rect_edges(struct Rect far *dst, struct Rect far *src, int l, int t, int r, int b);

void _fastcall win_constrain_drag_rect(int win, int mode, struct Rect far *r)
{
    struct Rect far *wr;
    struct Win far *w;
    int dy;
    int dx;
    struct Rect old;
    int done;
    int g;
    int gx;
    int gy;
    int h;

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
        if (r->left < g_3DB2 && !((w->flags & 0x1000) && r->right > g_3DB2) &&
            r->right - r->left < g_3DB2) {
            if (r->right >= 0 && r->right - r->left >= w->minWidth && !((w->flags & 0x1000) && r->left < 0)) {
                if (r->top <= g_3DB4 && !((w->flags & 0x1000) && r->bottom > g_3DB4)) {
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
            win_offset_rect_edges(r, wr, 0, 0, gx, gy);
        else
            win_offset_rect_edges(r, wr, gx, gy, gx, gy);
        if (_fmemcmp(&old, r, 8))
            done = 0;
        old = *r;
    } while (!done);
}

extern void far clip_set_screen_region(void);
extern void _fastcall win_rect_center(struct Pt far *center, struct Rect far *rect);
extern void far mouse_set_position(int x, int y);
extern void far GRectInvOutline(struct Rect far *r, int width);
extern void far ButtonHeldInit(void);
extern int far ButtonHeld(void);
extern int near g_9122;
extern int near g_9124;
extern void far GetMousePos(struct Pt far *pt);
extern struct Rect far win_offsets[];
extern void _fastcall win_redraw_exposed_windows(struct Rect far *rect);
extern int far StillDown(void);
extern void far win_FlushEvents(void);

void _fastcall win_track_move(struct Event far *ev)
{
    int win;
    struct Rect far *wr;
    struct Rect orig;
    struct Win far *w;
    struct Obj far *o;
    struct Rect orect;
    struct Pt start;
    struct Pt pt;
    struct Rect r;

    if ((win = g_5702[0]) == (int)0x8000)
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
    clip_set_screen_region();
    orect = o->rect;
    if (ev == 0) {
        win_rect_center(&start, &orect);
        mouse_set_position(start.x, start.y);
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
            GetMousePos(&pt);
            win_offset_rect_edges(&r, wr, pt.x - start.x, pt.y - start.y, pt.x - start.x, pt.y - start.y);
            GRectInvOutline(&r, 2);
        }
    }
    GRectInvOutline(&r, 2);
    win_constrain_drag_rect(win, 0, &r);
    o = w->objs[0];
    o->x += r.left - orig.left;
    o->y += r.top - orig.top;
    *win_WinRectAddr(win) = r;
    w = win_WinAddr(win);
    win_offsets[win >> 8] = *(struct Rect far *)&w->objs[0]->x;
    win_Recalc(win);
    win_UnlockWin(win);
    win_rebuild_visible_clips();
    (*g_62EC)(win);
    win_redraw_exposed_windows(&orig);
    win_deactivate_pointer_regions(win);
    win_activate_pointer_regions(win);
    while (StillDown())
        ;
    win_FlushEvents();
}

extern int far input_get_object_hit_rect(int id, struct Rect far *r);
extern void far Punt(char far *fmt, ...);

void _fastcall win_track_resize(struct Event far *ev)
{
    int win;
    struct Win far *w;
    struct Rect orig;
    struct Pt min;
    struct Rect icon;
    struct Pt start;
    struct Pt pt;
    struct Rect r;
    struct Obj far *o;

    if ((win = g_5702[0]) == (int)0x8000)
        return;
    win_LockWin(win);
    w = win_WinAddr(win);
    if (!(w->flags & 8)) {
        win_UnlockWin(win);
        return;
    }
    w->flags &= ~0x80;
    orig = w->rect;
    min = *(struct Pt far *)&w->minWidth;
    if (min.x == 0)
        min.x = 0x30;
    if (min.y == 0)
        min.y = 0x30;
    if (!input_get_object_hit_rect(0xf084, &icon))
        Punt("Couldn't find resize icoN!!");
    clip_set_screen_region();
    if (ev == 0) {
        win_rect_center(&start, &icon);
        mouse_set_position(start.x, start.y);
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
            GetMousePos(&pt);
            win_offset_rect_edges(&r, &orig, 0, 0, pt.x - start.x, pt.y - start.y);
            if (r.right - r.left < min.x)
                r.right = min.x + r.left;
            if (r.bottom - r.top < min.y)
                r.bottom = min.y + r.top;
            GRectInvOutline(&r, 2);
        }
    }
    GRectInvOutline(&r, 2);
    win_constrain_drag_rect(win, 1, &r);
    o = w->objs[0];
    o->width += r.right - orig.right;
    o->height += r.bottom - orig.bottom;
    *win_WinRectAddr(win) = r;
    win_Recalc(win);
    win_UnlockWin(win);
    win_rebuild_visible_clips();
    (*g_62EC)(win);
    win_redraw_exposed_windows(&orig);
    win_deactivate_pointer_regions(win);
    win_activate_pointer_regions(win);
    win_FlushEvents();
}
