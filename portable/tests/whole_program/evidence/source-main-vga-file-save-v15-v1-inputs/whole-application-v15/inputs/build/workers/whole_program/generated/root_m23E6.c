#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_list_refs.h"
#include "portable/whole_program/state/elevator_thumb_size.h"
#pragma pack(push, 2)
/* Root module 23E6: list-box and slider window objects. */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct List {
    int16_t visible;
    int16_t count;
    int16_t top;
    int16_t topOff;
    int16_t endOff;
    char  *  *text;
};

extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);


/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_23E6_0000 (list line address): best draft is 3 bytes short; the original
 * reloads the string segment (mov cx,[bp-0Ah]) after "s += _fstrlen(s) + 1". */
char  *  f_23E6_0000(int16_t line, struct List  *list)
{
    int16_t n;
    int16_t off;
    char  *s;

    n = list->top;
    if (n <= line) {
        if (list->visible + n <= line) {
            off = list->endOff;
            n = list->visible + n;
        } else
            off = list->topOff;
    } else
        off = n = 0;
    s = f_171C_1B84((*sim_window_list_text_slot(list))) + off;
    while (n < line) {
        if (*s == 0)
            break;
        s += _fstrlen(s);
        s++;
        n++;
    }
    f_171C_1BBA((*sim_window_list_text_slot(list)));
    return s;
}
/* SCAFFOLD END */

extern void  win_LockWin(int16_t win);
extern char  *  win_ObjAddr(int16_t obj);
extern void  win_UnlockWin(int16_t win);

int16_t  f_23E6_009F(int16_t obj, int16_t line)
{
    struct List  *list;
    int16_t sel;

    win_LockWin(obj);
    list = (struct List  *)(win_ObjAddr(obj) + 0x2a);
    f_171C_1B84((*sim_window_list_text_slot(list)));
    sel = *f_23E6_0000(line, list) & 1;
    f_171C_1BBA((*sim_window_list_text_slot(list)));
    win_UnlockWin(obj);
    return sel;
}

int16_t  f_23E6_0109(int16_t obj)
{
    int16_t count;

    win_LockWin(obj);
    count = ((struct List  *)(win_ObjAddr(obj) + 0x2a))->count;
    win_UnlockWin(obj);
    return count;
}

char  *  f_23E6_0132(int16_t obj, int16_t line)
{
    char  *s;

    win_LockWin(obj);
    s = f_23E6_0000(line, (struct List  *)(win_ObjAddr(obj) + 0x2a));
    win_UnlockWin(obj);
    return s;
}

void  f_23E6_016B(int16_t obj)
{
    char  *o;
    struct List  *list;
    char  *s;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    list = (struct List  *)(o + 0x2a);
    for (s = f_171C_1B84((*sim_window_list_text_slot(list))); *s; s += _fstrlen(s) + 1)
        *s &= ~1;
    f_171C_1BBA((*sim_window_list_text_slot(list)));
    win_UnlockWin(obj);
}

void  f_23E6_01DC(int16_t obj, int16_t line, int16_t sel)
{
    char  *o;
    struct List  *list;
    char  *s;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    list = (struct List  *)(o + 0x2a);
    if ((*sim_window_list_text_slot(list))) {
        f_171C_1B84((*sim_window_list_text_slot(list)));
        if (list->count > line) {
            s = f_23E6_0000(line, list);
            if (sel)
                *s |= 1;
            else
                *s &= ~1;
            win_UnlockWin(obj);
        }
        f_171C_1BBA((*sim_window_list_text_slot(list)));
    }
}

extern char  *  *  f_171C_18A6(char  *  *handle, int32_t size, int16_t flags);
extern char  *  *  f_171C_13CA(int32_t size, int16_t flags, char  *name);

extern void  f_24AB_02AD(int16_t font);

void  f_23E6_0266(int16_t obj, char  *text)
{
    char  *p;
    int16_t n;
    int16_t len;
    char  *o;
    struct List  *list;
    char  *  *h;
    struct Rect r;

    win_LockWin(obj);
    for (n = len = 0; *(p = text + len); n++)
        len += _fstrlen(p) + 1;
    len++;
    o = win_ObjAddr(obj);
    list = (struct List  *)(o + 0x2a);
    h = (*sim_window_list_text_slot(list));
    if (h)
        h = f_171C_18A6(h, (int32_t)len, 1);
    else
        h = f_171C_13CA((int32_t)len, 1, "list");
    _fmemcpy(f_171C_1B84(h), text, len);
    f_171C_1BBA(h);
    r = *(struct Rect  *)o;
    f_24AB_02AD(o[0x28]);
    list->count = n;
    list->top = 0;
    list->topOff = 0;
    list->endOff = -1;
    (*sim_window_list_text_slot(list)) = h;
    f_24AB_02AD(0);
    win_UnlockWin(obj);
}

extern void  clip_Push(void);
extern void  clip_SubInclude(struct Rect  *rect);
extern int16_t  f_24AB_030B(void);
extern void  win_SetColorNum(int16_t color);
extern void  f_24AB_042B(struct Rect  *rect, int16_t y, char  *text);
extern void  clip_Pop(void);

void  f_23E6_0392(char  *o)
{
    struct List  *list;
    struct Rect  *r;
    char  *base;
    char  *s;
    int16_t color0;
    int16_t color1;
    int16_t cur;
    int16_t y;
    int16_t h;
    int16_t i;
    int16_t sel;

    list = (struct List  *)(o + 0x2a);
    if ((*sim_window_list_text_slot(list)) == 0)
        return;
    f_24AB_02AD(o[0x28]);
    clip_Push();
    r = (struct Rect  *)o;
    clip_SubInclude(r);
    base = f_171C_1B84((*sim_window_list_text_slot(list)));
    s = base + list->topOff;
    color0 = o[0x26];
    color1 = o[0x27];
    cur = -1;
    y = r->top;
    h = f_24AB_030B();
    list->visible = (r->bottom - r->top) / f_24AB_030B();
    for (i = 0; i < list->visible; i++) {
        if (*s) {
            sel = *s & 1;
            if (sel != cur) {
                win_SetColorNum(sel ? color1 : color0);
                cur = sel;
            }
            f_24AB_042B(r, y, s + 1);
            s += _fstrlen(s) + 1;
        } else {
            if (cur)
                win_SetColorNum(color0);
            g_9134(r->left, y, r->right, y + h, SIM_GRAPHICS_SOURCE_g_3DE2);
        }
        y += h;
    }
    list->endOff = s - base;
    f_24AB_02AD(0);
    clip_Pop();
    f_171C_1BBA((*sim_window_list_text_slot(list)));
}

extern void  Punt(char  *format, ...);
struct Pt {
    int16_t x;
    int16_t y;
};

extern int16_t  WinPrintf(char  *format, ...);

void  win_DrawElevator(char  *o)
{
    struct Rect r;
    int16_t link;
    char  *lo;
    struct List  *list;
    int16_t height;
    int16_t eleHeight;
    int16_t eleTop;

    if (o[0x21] != 8)
        Punt("Bad object type in win_DrawElevator");
    r = *(struct Rect  *)o;
    link = *(int16_t  *)(o + 0x28);
    if (link <= 0)
        return;
    lo = win_ObjAddr(link);
    list = (struct List  *)(lo + 0x2a);
    if (list->count <= list->visible)
        return;
    win_SetColorNum(o[0x26]);
    r.left++;
    r.right--;
    r.top += fd_50F6_47DA.y + 1;
    r.bottom -= fd_50F6_47DA.y + 1;
    height = r.bottom - r.top;
    eleHeight = height * list->visible / list->count;
    WinPrintf("SliderHeight=%d, eleHeight=%d", height, eleHeight);
    if (eleHeight < 10)
        eleHeight = 10;
    eleTop = list->top * (height - eleHeight) / (list->count - list->visible);
    if (eleTop > 0)
        g_9134(r.left, r.top, r.right, r.top + eleTop, SIM_GRAPHICS_SOURCE_g_3DE2);
    WinPrintf(" eleTop= %d", eleTop);
    g_9134(r.left, r.top + eleTop, r.right, eleTop + eleHeight + r.top, SIM_GRAPHICS_SOURCE_g_3DE0);
    if (eleTop + eleHeight < height)
        g_9134(r.left, eleTop + eleHeight + r.top, r.right, r.bottom, SIM_GRAPHICS_SOURCE_g_3DE2);
}

extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);

void  f_23E6_066C(char  *o)
{
    struct Rect r;

    r = *(struct Rect  *)o;
    if (o[0x21] == 8) {
        win_DrawBitMap(r.left, r.top, 0x6d);
        win_DrawBitMap(r.left, r.bottom - fd_50F6_47DA.y, 0x6f);
        g_9134(r.left, fd_50F6_47DA.y + r.top, r.right, r.bottom - fd_50F6_47DA.y, SIM_GRAPHICS_SOURCE_g_3DE2);
        win_DrawElevator(o);
    }
}

void  f_23E6_06F1(int16_t line, char  *o)
{
    struct List  *list;
    int16_t n;
    int16_t off;
    char  *base;
    char  *s;

    list = (struct List  *)(o + 0x2a);
    n = list->top;
    if (n == line)
        return;
    off = list->topOff;
    s = base = f_171C_1B84((*sim_window_list_text_slot(list)));
    if (line < n) {
        n = 0;
        off = 0;
    } else
        base += off;
    while (n < line) {
        if (*s == 0)
            break;
        n++;
        off += _fstrlen(s) + 1;
        s = base + off;
    }
    list->top = n;
    list->topOff = off;
    f_23E6_0392(o);
    f_171C_1BBA((*sim_window_list_text_slot(list)));
}

extern void ( *  g_9188)(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t x, int16_t y);

int16_t  f_23E6_07A2(char  *o)
{
    struct List  *list;
    struct Rect r;
    char  *base;
    int16_t h;

    list = (struct List  *)(o + 0x2a);
    if (list->top + list->visible >= list->count)
        return 0;
    r = *(struct Rect  *)o;
    base = f_171C_1B84((*sim_window_list_text_slot(list)));
    f_24AB_02AD(o[0x28]);
    h = f_24AB_030B();
    clip_Push();
    clip_SubInclude(&r);
    g_9188(r.left, r.top + h, r.right, r.bottom, r.left, r.top);
    list->top++;
    list->topOff += _fstrlen(base + list->topOff) + 1;
    base += list->endOff;
    win_SetColorNum((*base & 1) ? o[0x27] : o[0x26]);
    f_24AB_042B(&r, r.bottom - h, base + 1);
    list->endOff += _fstrlen(base) + 1;
    clip_Pop();
    f_171C_1BBA((*sim_window_list_text_slot(list)));
}

extern char  *  f_24FA_0004(char  *p, char c, uint16_t n);

int16_t  PrevListLine(char  *o)
{
    struct List  *list;
    struct Rect r;
    char  *base;
    char  *s;
    int16_t h;

    list = (struct List  *)(o + 0x2a);
    if (list->top == 0)
        return 0;
    r = *(struct Rect  *)o;
    base = f_171C_1B84((*sim_window_list_text_slot(list)));
    f_24AB_02AD(o[0x28]);
    h = f_24AB_030B();
    clip_Push();
    clip_SubInclude(&r);
    g_9188(r.left, r.top - 1, r.right, r.bottom - h - 1, r.left, h + r.top - 1);
    if (--list->top) {
        s = f_24FA_0004(base + list->topOff - 2, 0, 0xffff);
        if (s == 0)
            Punt("PrevListLine punt");
        s++;
        goto found;
    }
    s = base;
found:
    list->topOff = s - base;
    win_SetColorNum((*s & 1) ? o[0x27] : o[0x26]);
    f_24AB_042B(&r, r.top, s + 1);
    list->endOff = f_24FA_0004(base + list->endOff - 2, 0, 0xffff) - base + 1;
    clip_Pop();
    f_171C_1BBA((*sim_window_list_text_slot(list)));
}

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

void  f_23E6_0A53(struct Event  *ev)
{
    char  *o;
    struct List  *list;
    int16_t h;
    int16_t line;
    int16_t sel;

    o = win_ObjAddr(ev->code);
    list = (struct List  *)(o + 0x2a);
    f_24AB_02AD(o[0x28]);
    h = f_24AB_030B();
    line = (ev->v - ((struct Rect  *)o)->top) / h + list->top;
    sel = f_23E6_009F(ev->code, line);
    WinPrintf("\nSS=%d, line=%d", sel, line);
    if (*(int16_t  *)(o + 0x24) & 0x20) {
        if ((*(int16_t  *)(o + 0x24) & 0x400) && sel)
            return;
        f_23E6_016B(ev->code);
    }
    if (sel == 0)
        f_23E6_01DC(ev->code, line, 1);
    f_23E6_0392(o);
}

extern void  f_1F80_0081(int16_t ticks);
extern int16_t  StillDown(void);

void  win_ProcSliderEvent(struct Event  *ev)
{
    char  *o;
    int16_t link;
    char  *lo;
    struct List  *list;
    struct Rect r;

    o = win_ObjAddr(ev->code);
    if (o[0x21] != 8)
        Punt("Bad object type in win_ProcSliderEvent");
    link = *(int16_t  *)(o + 0x28);
    if (link <= 0)
        return;
    lo = win_ObjAddr(link);
    list = (struct List  *)(lo + 0x2a);
    if (list->count <= list->visible)
        return;
    r = *(struct Rect  *)o;
    if (fd_50F6_47DA.y + r.top > ev->v) {
        if (ev->modifiers & 0x6800) {
            f_23E6_06F1(0, lo);
            win_DrawElevator(o);
        } else {
            do {
                PrevListLine(lo);
                win_DrawElevator(o);
                f_1F80_0081(1);
            } while (StillDown());
        }
    } else if (r.bottom - fd_50F6_47DA.y < ev->v) {
        if (ev->modifiers & 0x6800) {
            f_23E6_06F1(list->count - list->visible, lo);
            win_DrawElevator(o);
        } else {
            do {
                f_23E6_07A2(lo);
                win_DrawElevator(o);
                f_1F80_0081(1);
            } while (StillDown());
        }
    }
}

#pragma pack(pop)
