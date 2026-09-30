/* Overlay section S26, code frame 39C7: window zoom, drag and grow with screen constraints (_fastcall window API). */

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

void _fastcall o26_39C7_022F(int win, int mode, struct Rect far *r);

extern void _fastcall win_LockWin(int win);
extern struct Win far * _fastcall win_WinAddr(int win);
extern void _fastcall win_UnlockWin(int win);
extern struct Obj far * _fastcall win_ObjAddr(int obj);
extern int far fd_50F6_3942;
extern int near g_3DB4;
extern int near g_3DB2;
extern struct Rect far * _fastcall win_WinRectAddr(int win);
extern void _fastcall win_Recalc(int win);
extern void far f_1E57_038E(void);
extern void (far * far g_62EC)(int win);
extern void far clip_SetWin(int win);
extern void far f_1E57_0D97(struct Rect far *r);
extern void far f_1E57_0FDC(struct Rect far *r);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far f_1E57_0296(void);
extern void far f_1FD2_05FD(void);
extern void far clip_Pop(void);
extern void far clip_SubExclude(struct Rect far *r);
extern int far g_5702[];
extern void far f_1E57_0A9C(struct Rect far *r);
extern void _fastcall win_DrawWindow(int win);
extern void _fastcall f_2505_08EA(int win);
extern void _fastcall f_2505_0831(int win);

void _fastcall o26_39C7_0000(int win)
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
        r.top = fd_50F6_3942;
        o26_39C7_022F(win, 0, &r);
        w->rect = r;
        r.bottom = g_3DB4;
        r.right = g_3DB2;
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
    for (i = 1; g_5702[i] != (int)0x8000; i++)
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

extern void _fastcall f_22BF_0B5B(struct Rect far *dst, struct Rect far *src, int l, int t, int r, int b);
extern int far _fmemcmp(void far *a, void far *b, unsigned n);

void _fastcall o26_39C7_022F(int win, int mode, struct Rect far *r)
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
                    if (r->top > fd_50F6_3942 && r->bottom - r->top >= w->minHeight)
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

extern void far f_1E57_0351(void);
extern void _fastcall f_2505_0382(struct Pt far *center, struct Rect far *rect);
extern void far f_1B73_09E9(int x, int y);
extern void far f_1CE2_0410(struct Rect far *r, int width);
extern void far f_1FD2_057F(void);
extern int far f_1FD2_0598(void);
extern int near g_9122;
extern int near g_9124;
extern void far f_1FD2_04D0(struct Pt far *pt);
extern struct Rect far win_offsets[];
extern void _fastcall f_21FA_0B4B(struct Rect far *rect);
extern int far f_1FD2_0542(void);
extern void far win_FlushEvents(void);

/* SCAFFOLD BEGIN: o26_39C7_040F (drag front window) best draft, 615 vs 610 bytes: logic complete; the original keeps the early "win_UnlockWin; return" block inline after the count test (the type test jumps back to it) and stores the object pointer at [bp-12h]; MSC 6.00AX here moves that block to the end and lays out the frame differently */
void _fastcall o26_39C7_040F(struct Event far *ev)
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
unlock:
        win_UnlockWin(win);
        return;
    }
    o = w->objs[1];
    if (o->type != 0x0c && o->type != 0x12)
        goto unlock;
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
    f_1CE2_0410(&r, 2);
    pt = start;
    f_1FD2_057F();
    while (f_1FD2_0598()) {
        if (pt.x != g_9122 || pt.y != g_9124) {
            f_1CE2_0410(&r, 2);
            f_1FD2_04D0(&pt);
            f_22BF_0B5B(&r, wr, pt.x - start.x, pt.y - start.y, pt.x - start.x, pt.y - start.y);
            f_1CE2_0410(&r, 2);
        }
    }
    f_1CE2_0410(&r, 2);
    o26_39C7_022F(win, 0, &r);
    o = w->objs[0];
    o->x += r.left - orig.left;
    o->y += r.top - orig.top;
    *win_WinRectAddr(win) = r;
    w = win_WinAddr(win);
    win_offsets[win >> 8] = *(struct Rect far *)&w->objs[0]->x;
    win_Recalc(win);
    win_UnlockWin(win);
    f_1E57_038E();
    (*g_62EC)(win);
    f_21FA_0B4B(&orig);
    f_2505_08EA(win);
    f_2505_0831(win);
    while (f_1FD2_0542())
        ;
    win_FlushEvents();
}
/* SCAFFOLD END */

extern int far f_1FD2_04B3(int id, struct Rect far *r);
extern void far Punt(char far *fmt, ...);

/* SCAFFOLD BEGIN: o26_39C7_0671 (grow front window) best draft, 589 vs 587 bytes: same frame/block-order residue as o26_39C7_040F */
void _fastcall o26_39C7_0671(struct Event far *ev)
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
    f_1CE2_0410(&r, 2);
    pt = start;
    f_1FD2_057F();
    while (f_1FD2_0598()) {
        if (pt.x != g_9122 || pt.y != g_9124) {
            f_1CE2_0410(&r, 2);
            f_1FD2_04D0(&pt);
            f_22BF_0B5B(&r, &orig, 0, 0, pt.x - start.x, pt.y - start.y);
            if (r.right - r.left < min.x)
                r.right = min.x + r.left;
            if (r.bottom - r.top < min.y)
                r.bottom = min.y + r.top;
            f_1CE2_0410(&r, 2);
        }
    }
    f_1CE2_0410(&r, 2);
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
/* SCAFFOLD END */
