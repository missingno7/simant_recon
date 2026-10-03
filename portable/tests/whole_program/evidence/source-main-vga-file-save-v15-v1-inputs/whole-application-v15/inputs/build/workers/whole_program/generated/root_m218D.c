#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_refs.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 218D: window event dispatch. */

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

int32_t g_6364 = -1;
int16_t g_6368 = -1;
static char g_8CEC;

extern void  win_LockWin(int16_t win);
extern char  *  win_ObjAddr(int16_t obj);
extern void  f_23E6_0A53(struct Event  *ev);
extern void  win_ProcSliderEvent(struct Event  *ev);
extern char  *  win_WinAddr(int16_t win);
extern void  o26_39C7_040F(struct Event  *ev);
extern void  clip_Push(void);
extern void  f_1E57_0351(void);
extern void  win_SetObjSelectedState(int16_t obj, int16_t state);
extern void  f_208F_0530(int16_t ticks);
extern void  clip_Pop(void);
extern struct Event  fd_50F6_49FA;
extern struct Event  fd_50F6_4A0A;
extern int32_t  TickCount(void);
extern void  win_UnlockWin(int16_t win);

void  f_218D_000C(struct Event  *ev)
{
    char  *obj;

    win_LockWin(ev->code);
    obj = win_ObjAddr(ev->code);
    switch (obj[0x21]) {
    case 4:
        f_23E6_0A53(ev);
        goto check;
    case 7:
    case 8:
        win_ProcSliderEvent(ev);
        goto check;
    case 12:
    case 18:
        if (*(int16_t  *)(win_WinAddr(ev->code) + 0x1c) & 2)
            o26_39C7_040F(ev);
        break;
    }
    if (*(int16_t  *)(obj + 0x24) & 0x800) {
        clip_Push();
        f_1E57_0351();
        if (*(int16_t  *)(obj + 0x24) & 8) {
            if (!(*(int16_t  *)(obj + 0x24) & 0x20) || !(*(int16_t  *)(obj + 0x24) & 0x400) || !(*(int16_t  *)(obj + 0x24) & 4))
                win_SetObjSelectedState(ev->code, !(*(int16_t  *)(obj + 0x24) & 4));
        } else if (*(int16_t  *)(obj + 0x24) & 1) {
            win_SetObjSelectedState(ev->code, !(*(int16_t  *)(obj + 0x24) & 4));
            f_208F_0530(5);
            win_SetObjSelectedState(ev->code, !(*(int16_t  *)(obj + 0x24) & 4));
        }
        clip_Pop();
    }
check:
    if (fd_50F6_4A0A.code == fd_50F6_49FA.code && TickCount() - 10 < g_6364) {
        if (((fd_50F6_4A0A.modifiers ^ fd_50F6_49FA.modifiers) & 0x0a00) == 0) {
            fd_50F6_49FA.modifiers &= ~0x0a00;
            if (fd_50F6_4A0A.modifiers & 0x0800)
                fd_50F6_49FA.modifiers |= 0x4000;
            if (fd_50F6_4A0A.modifiers & 0x0200)
                fd_50F6_49FA.modifiers |= 0x2000;
            g_6364 = -1;
            goto done;
        }
    }
    g_6364 = TickCount();
    fd_50F6_4A0A = fd_50F6_49FA;
done:
    win_UnlockWin(ev->code);
}

void  f_218D_01EB(void)
{
    g_6368 = -1;
}

int16_t  win_GetProxEvent(void)
{
    return g_6368;
}

extern void  f_1E57_0A9C(char  *p);
extern void  win_ObjInv(int16_t obj);

void  _win_SetProxItem(int16_t obj)
{
    clip_Push();
    f_1E57_0A9C((char *)&g_5A9C);
    if (g_6368 != -1)
        win_ObjInv(g_6368);
    if (obj != -1)
        win_ObjInv(obj);
    g_6368 = obj;
    clip_Pop();
}

extern int16_t g_5702[];
extern int16_t  f_1B73_0BFF(void);

void  f_218D_023A(struct Event  *ev)
{
    int16_t obj;

    if ((char)(g_5702[0] >> 8) == (uint8_t)ev->code) {
        win_LockWin(g_5702[0]);
        obj = f_1B73_0BFF();
        if (obj != 0 && (obj & 0xff00) == g_5702[0] && g_6368 != obj &&
            (*(int16_t  *)(win_ObjAddr(obj) + 0x24) & 0x10))
            _win_SetProxItem(obj);
        else if (g_6368 != -1 && !(*(int16_t  *)(win_ObjAddr(g_6368) + 0x24) & 0x400) && obj != g_6368)
            _win_SetProxItem(-1);
        win_UnlockWin(g_5702[0]);
    }
}

extern void  f_1B28_0069(void);
extern void  f_0000_046F(void);
extern int16_t  f_1B73_032A(void);
extern void  f_1B73_032E(struct Event  *ev);
void  f_218D_0451(struct Event  *ev);
extern void  f_20E8_0776(int16_t win);
void  win_FlushEvents(void);
extern void  win_Close(int16_t win);
extern void  o26_39C7_0671(struct Event  *ev);
extern void  o26_39C7_0000(int16_t win);
void  f_218D_0656(int16_t dir);

void  f_218D_02D5(void)
{
    f_1B28_0069();
    f_0000_046F();
    if (g_8CEC != 0 || !f_1B73_032A())
        return;
    f_1B73_032E(&fd_50F6_49FA);
    if (fd_50F6_49FA.code == (int16_t)0xff00) {
        f_218D_0451(&fd_50F6_49FA);
    } else if ((char)(fd_50F6_49FA.code >> 8) == (char)0xfb) {
        f_218D_023A(&fd_50F6_49FA);
    } else {
        if (g_5702[0] != (int16_t)0x8000) {
            switch ((uint16_t)fd_50F6_49FA.code) {
            case 0xf081:
                o26_39C7_040F(0L);
                break;
            case 0xf082:
                f_20E8_0776(g_5702[0]);
                win_FlushEvents();
                return;
            case 0xf083:
                win_Close(g_5702[0]);
                win_FlushEvents();
                return;
            case 0xf084:
                o26_39C7_0671(0L);
                return;
            case 0xf085:
                o26_39C7_0000(g_5702[0]);
                win_FlushEvents();
                return;
            case 0xf086:
                if (g_5702[0] != (int16_t)0x8000)
                    f_218D_0656(1);
                break;
            case 0xf087:
                if (g_5702[0] != (int16_t)0x8000)
                    f_218D_0656(-1);
                break;
            default:
                if (!(fd_50F6_49FA.code & 0x8000)) {
                    if ((fd_50F6_49FA.code & 0xff00) != g_5702[0])
                        return;
                    f_218D_000C(&fd_50F6_49FA);
                }
                break;
            }
        }
    }
    g_8CEC = 1;
}

int16_t  win_Events(void)
{
    f_218D_02D5();
    return g_8CEC;
}

int16_t  win_GetEvent(struct Event  *ev)
{
    f_218D_02D5();
    if (g_8CEC) {
        g_8CEC = 0;
        *ev = fd_50F6_49FA;
        f_218D_02D5();
        return 1;
    }
    return 0;
}

void  win_FlushEvents(void)
{
    struct Event ev;

    while (f_1B73_032A())
        f_1B73_032E(&ev);
    g_8CEC = 0;
}
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  f_1FD2_04E5(int16_t  *pt, struct Rect  *rect);
extern void  f_20E8_0725(int16_t win);

void  f_218D_0451(struct Event  *ev)
{
    int16_t top;
    int16_t noClose;
    struct Rect r;
    int16_t i;

    top = g_5702[0];
    if (top == (int16_t)0x8000)
        return;
    win_GetObjRect(top, &r);
    win_LockWin(top);
    noClose = (*(uint16_t  *)(win_WinAddr(top) + 0x1c) & 0x40) >> 6;
    if (!f_1FD2_04E5(&ev->h, &r) && (*(int16_t  *)(win_WinAddr(top) + 0x1c) & 1))
        win_Close(top);
    win_UnlockWin(top);
    if (noClose == 0) {
        for (i = 0; g_5702[i] != (int16_t)0x8000; i++) {
            win_GetObjRect(g_5702[i], &r);
            if (f_1FD2_04E5(&ev->h, &r)) {
                f_20E8_0725(g_5702[i]);
                break;
            }
        }
    }
}

struct Pt {
    int16_t x;
    int16_t y;
};

extern char  *  f_2505_0006(int16_t win);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern void  f_1B73_0C80(int16_t obj);

int16_t  f_218D_052F(void)
{
    uint32_t d;
    uint32_t best;
    int16_t top;
    int16_t found;
    char  *obj;
    char  *w;
    struct Pt pt;
    int16_t i;
    int16_t dx;
    int16_t dy;

    found = -1;
    top = g_5702[0];
    best = 0xffffffffL;
    win_LockWin(top);
    w = f_2505_0006(top);
    f_1FD2_04D0(&pt);
    for (i = 1; i < sim_window_wire_read_i16(w, 0x0c); i++) {
        obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (*(int16_t  *)(obj + 0x24) & 2) {
            if (f_1FD2_04E5((int16_t  *)&pt, (struct Rect  *)obj)) {
                win_UnlockWin(top);
                return top + i;
            }
            dy = pt.y - (((struct Rect  *)obj)->top + ((struct Rect  *)obj)->top) / 2;
            dx = pt.x - (((struct Rect  *)obj)->right + ((struct Rect  *)obj)->left) / 2;
            d = (int32_t)dy * dy + (int32_t)dx * dx;
            if (d < best) {
                best = d;
                found = top + i;
            }
        }
    }
    if (found != -1)
        f_1B73_0C80(found);
    win_UnlockWin(top);
    return -1;
}

extern int16_t  f_22BF_0AC5(int16_t win);
extern int16_t  f_22BF_0A97(int16_t obj);

void  f_218D_0656(int16_t dir)
{
    int16_t start;
    int16_t last;
    int16_t cur;

    if (g_5702[0] == (int16_t)0x8000)
        return;
    cur = start = f_218D_052F();
    last = g_5702[0] + f_22BF_0AC5(g_5702[0]);
    if (start == -1)
        return;
    do {
        cur += dir;
        if (g_5702[0] + 1 > cur)
            cur = last - 1;
        else if (last <= cur)
            cur = g_5702[0] + 1;
        if (f_22BF_0A97(cur)) {
            f_1B73_0C80(cur);
            return;
        }
    } while (start != cur);
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");

#pragma pack(pop)
