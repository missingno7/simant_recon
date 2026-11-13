/*
 * Implements list box and slider window objects. It calculates elevator geometry, draws controls
 * and handles list movement and slider events.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 23E6; partial original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Functions not yet exact: f_23E6_0000.
 */

#include "rect.h"

struct List {
    int visible;
    int count;
    int top;
    int topOff;
    int endOff;
    char far * far *text;
};

extern char far * far mem_Lock(char far * far *handle);
extern void far mem_Unlock(char far * far *handle);
extern unsigned int far _fstrlen(char far *s);


char far * _fastcall f_23E6_0000(int line, struct List far *list)
{
    int n;
    int off;
    char far *s;

    n = list->top;
    if (n <= line) {
        if (list->visible + n <= line) {
            off = list->endOff;
            n = list->visible + n;
        } else
            off = list->topOff;
    } else
        off = n = 0;
    s = mem_Lock(list->text) + off;
    while (n < line) {
        if (*s == 0)
            break;
        s += _fstrlen(s);
        s++;
        n++;
    }
    mem_Unlock(list->text);
    return s;
}


extern void _fastcall win_LockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall win_UnlockWin(int win);

int _fastcall list_is_line_selected(int obj, int line)
{
    struct List far *list;
    int sel;

    win_LockWin(obj);
    list = (struct List far *)(win_ObjAddr(obj) + 0x2a);
    mem_Lock(list->text);
    sel = *f_23E6_0000(line, list) & 1;
    mem_Unlock(list->text);
    win_UnlockWin(obj);
    return sel;
}

int _fastcall list_line_count(int obj)
{
    int count;

    win_LockWin(obj);
    count = ((struct List far *)(win_ObjAddr(obj) + 0x2a))->count;
    win_UnlockWin(obj);
    return count;
}

char far * _fastcall list_line_record(int obj, int line)
{
    char far *s;

    win_LockWin(obj);
    s = f_23E6_0000(line, (struct List far *)(win_ObjAddr(obj) + 0x2a));
    win_UnlockWin(obj);
    return s;
}

void _fastcall list_clear_selection(int obj)
{
    char far *o;
    struct List far *list;
    char far *s;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    for (s = mem_Lock(list->text); *s; s += _fstrlen(s) + 1)
        *s &= ~1;
    mem_Unlock(list->text);
    win_UnlockWin(obj);
}

/*
 * Set a list line's selection bit without redrawing it.
 */
void _fastcall list_set_line_selected(int obj, int line, int sel)
{
    char far *o;
    struct List far *list;
    char far *s;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    if (list->text) {
        mem_Lock(list->text);
        if (list->count > line) {
            s = f_23E6_0000(line, list);
            if (sel)
                *s |= 1;
            else
                *s &= ~1;
            win_UnlockWin(obj);
        }
        mem_Unlock(list->text);
    }
}

extern char far * far * far RallocRealloc(char far * far *handle, long size, int flags);
extern char far * far * far Ralloc(long size, int flags, char far *name);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned int n);
extern void far font_SetFont(int font);

void _fastcall list_replace_text(int obj, char far *text)
{
    char far *p;
    int n;
    int len;
    char far *o;
    struct List far *list;
    char far * far *h;
    struct Rect r;

    win_LockWin(obj);
    for (n = len = 0; *(p = text + len); n++)
        len += _fstrlen(p) + 1;
    len++;
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    h = list->text;
    if (h)
        h = RallocRealloc(h, (long)len, 1);
    else
        h = Ralloc((long)len, 1, "list");
    _fmemcpy(mem_Lock(h), text, len);
    mem_Unlock(h);
    r = *(struct Rect far *)o;
    font_SetFont(o[0x28]);
    list->count = n;
    list->top = 0;
    list->topOff = 0;
    list->endOff = -1;
    list->text = h;
    font_SetFont(0);
    win_UnlockWin(obj);
}

extern void far clip_Push(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far font_FontHeight(void);
extern void _fastcall win_SetColorNum(int color);
extern void far font_print_and_clear_row(struct Rect far *rect, int y, char far *text);
extern int near g_3DE2;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
extern void far clip_Pop(void);

void _fastcall list_draw_visible_rows(char far *o)
{
    struct List far *list;
    struct Rect far *r;
    char far *base;
    char far *s;
    int color0;
    int color1;
    int cur;
    int y;
    int h;
    int i;
    int sel;

    list = (struct List far *)(o + 0x2a);
    if (list->text == 0)
        return;
    font_SetFont(o[0x28]);
    clip_Push();
    r = (struct Rect far *)o;
    clip_SubInclude(r);
    base = mem_Lock(list->text);
    s = base + list->topOff;
    color0 = o[0x26];
    color1 = o[0x27];
    cur = -1;
    y = r->top;
    h = font_FontHeight();
    list->visible = (r->bottom - r->top) / font_FontHeight();
    for (i = 0; i < list->visible; i++) {
        if (*s) {
            sel = *s & 1;
            if (sel != cur) {
                win_SetColorNum(sel ? color1 : color0);
                cur = sel;
            }
            font_print_and_clear_row(r, y, s + 1);
            s += _fstrlen(s) + 1;
        } else {
            if (cur)
                win_SetColorNum(color0);
            gfx_fill_rect_hook(r->left, y, r->right, y + h, g_3DE2);
        }
        y += h;
    }
    list->endOff = s - base;
    font_SetFont(0);
    clip_Pop();
    mem_Unlock(list->text);
}

extern void far Punt(char far *format, ...);
struct Pt {
    int x;
    int y;
};

extern struct Pt far window_scroll_arrow_size;
extern int far WinPrintf(char far *format, ...);
extern int near _foreColor;

void _fastcall win_DrawElevator(char far *o)
{
    struct Rect r;
    int link;
    char far *lo;
    struct List far *list;
    int height;
    int eleHeight;
    int eleTop;

    if (o[0x21] != 8)
        Punt("Bad object type in win_DrawElevator");
    r = *(struct Rect far *)o;
    link = *(int far *)(o + 0x28);
    if (link <= 0)
        return;
    lo = win_ObjAddr(link);
    list = (struct List far *)(lo + 0x2a);
    if (list->count <= list->visible)
        return;
    win_SetColorNum(o[0x26]);
    r.left++;
    r.right--;
    r.top += window_scroll_arrow_size.y + 1;
    r.bottom -= window_scroll_arrow_size.y + 1;
    height = r.bottom - r.top;
    eleHeight = height * list->visible / list->count;
    WinPrintf("SliderHeight=%d, eleHeight=%d", height, eleHeight);
    if (eleHeight < 10)
        eleHeight = 10;
    eleTop = list->top * (height - eleHeight) / (list->count - list->visible);
    if (eleTop > 0)
        gfx_fill_rect_hook(r.left, r.top, r.right, r.top + eleTop, g_3DE2);
    WinPrintf(" eleTop= %d", eleTop);
    gfx_fill_rect_hook(r.left, r.top + eleTop, r.right, eleTop + eleHeight + r.top, _foreColor);
    if (eleTop + eleHeight < height)
        gfx_fill_rect_hook(r.left, eleTop + eleHeight + r.top, r.right, r.bottom, g_3DE2);
}

extern int _fastcall win_DrawBitMap(int x, int y, int id);

void _fastcall win_draw_vertical_slider(char far *o)
{
    struct Rect r;

    r = *(struct Rect far *)o;
    if (o[0x21] == 8) {
        win_DrawBitMap(r.left, r.top, 0x6d);
        win_DrawBitMap(r.left, r.bottom - window_scroll_arrow_size.y, 0x6f);
        gfx_fill_rect_hook(r.left, window_scroll_arrow_size.y + r.top, r.right, r.bottom - window_scroll_arrow_size.y, g_3DE2);
        win_DrawElevator(o);
    }
}

void _fastcall list_scroll_to_line(int line, char far *o)
{
    struct List far *list;
    int n;
    int off;
    char far *base;
    char far *s;

    list = (struct List far *)(o + 0x2a);
    n = list->top;
    if (n == line)
        return;
    off = list->topOff;
    s = base = mem_Lock(list->text);
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
    list_draw_visible_rows(o);
    mem_Unlock(list->text);
}

extern void (far * near gfx_copy_screen_rect_hook)(int left, int top, int right, int bottom, int x, int y);

int _fastcall list_scroll_forward_line(char far *o)
{
    struct List far *list;
    struct Rect r;
    char far *base;
    int h;

    list = (struct List far *)(o + 0x2a);
    if (list->top + list->visible >= list->count)
        return 0;
    r = *(struct Rect far *)o;
    base = mem_Lock(list->text);
    font_SetFont(o[0x28]);
    h = font_FontHeight();
    clip_Push();
    clip_SubInclude(&r);
    gfx_copy_screen_rect_hook(r.left, r.top + h, r.right, r.bottom, r.left, r.top);
    list->top++;
    list->topOff += _fstrlen(base + list->topOff) + 1;
    base += list->endOff;
    win_SetColorNum((*base & 1) ? o[0x27] : o[0x26]);
    font_print_and_clear_row(&r, r.bottom - h, base + 1);
    list->endOff += _fstrlen(base) + 1;
    clip_Pop();
    mem_Unlock(list->text);
}

extern char far * far MemRChr(char far *p, char c, unsigned int n);

int _fastcall PrevListLine(char far *o)
{
    struct List far *list;
    struct Rect r;
    char far *base;
    char far *s;
    int h;

    list = (struct List far *)(o + 0x2a);
    if (list->top == 0)
        return 0;
    r = *(struct Rect far *)o;
    base = mem_Lock(list->text);
    font_SetFont(o[0x28]);
    h = font_FontHeight();
    clip_Push();
    clip_SubInclude(&r);
    gfx_copy_screen_rect_hook(r.left, r.top - 1, r.right, r.bottom - h - 1, r.left, h + r.top - 1);
    if (--list->top) {
        s = MemRChr(base + list->topOff - 2, 0, 0xffff);
        if (s == 0)
            Punt("PrevListLine punt");
        s++;
        goto found;
    }
    s = base;
found:
    list->topOff = s - base;
    win_SetColorNum((*s & 1) ? o[0x27] : o[0x26]);
    font_print_and_clear_row(&r, r.top, s + 1);
    list->endOff = MemRChr(base + list->endOff - 2, 0, 0xffff) - base + 1;
    clip_Pop();
    mem_Unlock(list->text);
}

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

/*
 * Apply a click to list selection and repaint its visible rows.
 */
void _fastcall list_process_click(struct Event far *ev)
{
    char far *o;
    struct List far *list;
    int h;
    int line;
    int sel;

    o = win_ObjAddr(ev->code);
    list = (struct List far *)(o + 0x2a);
    font_SetFont(o[0x28]);
    h = font_FontHeight();
    line = (ev->v - ((struct Rect far *)o)->top) / h + list->top;
    sel = list_is_line_selected(ev->code, line);
    WinPrintf("\nSS=%d, line=%d", sel, line);
    if (*(int far *)(o + 0x24) & 0x20) {
        if ((*(int far *)(o + 0x24) & 0x400) && sel)
            return;
        list_clear_selection(ev->code);
    }
    if (sel == 0)
        list_set_line_selected(ev->code, line, 1);
    list_draw_visible_rows(o);
}

extern void far timer_wait_double_ticks(int ticks);
extern int far StillDown(void);

void _fastcall win_ProcSliderEvent(struct Event far *ev)
{
    char far *o;
    int link;
    char far *lo;
    struct List far *list;
    struct Rect r;

    o = win_ObjAddr(ev->code);
    if (o[0x21] != 8)
        Punt("Bad object type in win_ProcSliderEvent");
    link = *(int far *)(o + 0x28);
    if (link <= 0)
        return;
    lo = win_ObjAddr(link);
    list = (struct List far *)(lo + 0x2a);
    if (list->count <= list->visible)
        return;
    r = *(struct Rect far *)o;
    if (window_scroll_arrow_size.y + r.top > ev->v) {
        if (ev->modifiers & 0x6800) {
            list_scroll_to_line(0, lo);
            win_DrawElevator(o);
        } else {
            do {
                PrevListLine(lo);
                win_DrawElevator(o);
                timer_wait_double_ticks(1);
            } while (StillDown());
        }
    } else if (r.bottom - window_scroll_arrow_size.y < ev->v) {
        if (ev->modifiers & 0x6800) {
            list_scroll_to_line(list->count - list->visible, lo);
            win_DrawElevator(o);
        } else {
            do {
                list_scroll_forward_line(lo);
                win_DrawElevator(o);
                timer_wait_double_ticks(1);
            } while (StillDown());
        }
    }
}
