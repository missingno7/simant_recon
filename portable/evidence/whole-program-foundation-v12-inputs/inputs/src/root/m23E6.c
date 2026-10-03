/* Root module 23E6: list-box and slider window objects. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct List {
    int visible;
    int count;
    int top;
    int topOff;
    int endOff;
    char far * far *text;
};

extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern unsigned int far _fstrlen(char far *s);

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_23E6_0000 (list line address): best draft is 3 bytes short; the original
 * reloads the string segment (mov cx,[bp-0Ah]) after "s += _fstrlen(s) + 1". */
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
    s = f_171C_1B84(list->text) + off;
    while (n < line) {
        if (*s == 0)
            break;
        s += _fstrlen(s) + 1;
        n++;
    }
    f_171C_1BBA(list->text);
    return s;
}
/* SCAFFOLD END */

extern void _fastcall f_23AE_0377(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall f_23AE_01DB(int win);

int _fastcall f_23E6_009F(int obj, int line)
{
    struct List far *list;
    int sel;

    f_23AE_0377(obj);
    list = (struct List far *)(win_ObjAddr(obj) + 0x2a);
    f_171C_1B84(list->text);
    sel = *f_23E6_0000(line, list) & 1;
    f_171C_1BBA(list->text);
    f_23AE_01DB(obj);
    return sel;
}

int _fastcall f_23E6_0109(int obj)
{
    int count;

    f_23AE_0377(obj);
    count = ((struct List far *)(win_ObjAddr(obj) + 0x2a))->count;
    f_23AE_01DB(obj);
    return count;
}

char far * _fastcall f_23E6_0132(int obj, int line)
{
    char far *s;

    f_23AE_0377(obj);
    s = f_23E6_0000(line, (struct List far *)(win_ObjAddr(obj) + 0x2a));
    f_23AE_01DB(obj);
    return s;
}

void _fastcall f_23E6_016B(int obj)
{
    char far *o;
    struct List far *list;
    char far *s;

    f_23AE_0377(obj);
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    for (s = f_171C_1B84(list->text); *s; s += _fstrlen(s) + 1)
        *s &= ~1;
    f_171C_1BBA(list->text);
    f_23AE_01DB(obj);
}

void _fastcall f_23E6_01DC(int obj, int line, int sel)
{
    char far *o;
    struct List far *list;
    char far *s;

    f_23AE_0377(obj);
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    if (list->text) {
        f_171C_1B84(list->text);
        if (list->count > line) {
            s = f_23E6_0000(line, list);
            if (sel)
                *s |= 1;
            else
                *s &= ~1;
            f_23AE_01DB(obj);
        }
        f_171C_1BBA(list->text);
    }
}

extern char far * far * far f_171C_18A6(char far * far *handle, long size, int flags);
extern char far * far * far f_171C_13CA(long size, int flags, char far *name);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned int n);
extern void far f_24AB_02AD(int font);

void _fastcall f_23E6_0266(int obj, char far *text)
{
    char far *p;
    int n;
    int len;
    char far *o;
    struct List far *list;
    char far * far *h;
    struct Rect r;

    f_23AE_0377(obj);
    for (n = len = 0; *(p = text + len); n++)
        len += _fstrlen(p) + 1;
    len++;
    o = win_ObjAddr(obj);
    list = (struct List far *)(o + 0x2a);
    h = list->text;
    if (h)
        h = f_171C_18A6(h, (long)len, 1);
    else
        h = f_171C_13CA((long)len, 1, "list");
    _fmemcpy(f_171C_1B84(h), text, len);
    f_171C_1BBA(h);
    r = *(struct Rect far *)o;
    f_24AB_02AD(o[0x28]);
    list->count = n;
    list->top = 0;
    list->topOff = 0;
    list->endOff = -1;
    list->text = h;
    f_24AB_02AD(0);
    f_23AE_01DB(obj);
}

extern void far clip_Push(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far f_24AB_030B(void);
extern void _fastcall f_21FA_00EE(int color);
extern void far f_24AB_042B(struct Rect far *rect, int y, char far *text);
extern int near g_3DE2;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
extern void far clip_Pop(void);

void _fastcall f_23E6_0392(char far *o)
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
    f_24AB_02AD(o[0x28]);
    clip_Push();
    r = (struct Rect far *)o;
    clip_SubInclude(r);
    base = f_171C_1B84(list->text);
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
                f_21FA_00EE(sel ? color1 : color0);
                cur = sel;
            }
            f_24AB_042B(r, y, s + 1);
            s += _fstrlen(s) + 1;
        } else {
            if (cur)
                f_21FA_00EE(color0);
            g_9134(r->left, y, r->right, y + h, g_3DE2);
        }
        y += h;
    }
    list->endOff = s - base;
    f_24AB_02AD(0);
    clip_Pop();
    f_171C_1BBA(list->text);
}

extern void far Punt(char far *format, ...);
struct Pt {
    int x;
    int y;
};

extern struct Pt far fd_50F6_47DA;
extern int far WinPrintf(char far *format, ...);
extern int near g_3DE0;

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
    f_21FA_00EE(o[0x26]);
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
        g_9134(r.left, r.top, r.right, r.top + eleTop, g_3DE2);
    WinPrintf(" eleTop= %d", eleTop);
    g_9134(r.left, r.top + eleTop, r.right, eleTop + eleHeight + r.top, g_3DE0);
    if (eleTop + eleHeight < height)
        g_9134(r.left, eleTop + eleHeight + r.top, r.right, r.bottom, g_3DE2);
}

extern int _fastcall win_DrawBitMap(int x, int y, int id);

void _fastcall f_23E6_066C(char far *o)
{
    struct Rect r;

    r = *(struct Rect far *)o;
    if (o[0x21] == 8) {
        win_DrawBitMap(r.left, r.top, 0x6d);
        win_DrawBitMap(r.left, r.bottom - fd_50F6_47DA.y, 0x6f);
        g_9134(r.left, fd_50F6_47DA.y + r.top, r.right, r.bottom - fd_50F6_47DA.y, g_3DE2);
        win_DrawElevator(o);
    }
}

void _fastcall f_23E6_06F1(int line, char far *o)
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
    s = base = f_171C_1B84(list->text);
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
    f_171C_1BBA(list->text);
}

extern void (far * near g_9188)(int left, int top, int right, int bottom, int x, int y);

int _fastcall f_23E6_07A2(char far *o)
{
    struct List far *list;
    struct Rect r;
    char far *base;
    int h;

    list = (struct List far *)(o + 0x2a);
    if (list->top + list->visible >= list->count)
        return 0;
    r = *(struct Rect far *)o;
    base = f_171C_1B84(list->text);
    f_24AB_02AD(o[0x28]);
    h = f_24AB_030B();
    clip_Push();
    clip_SubInclude(&r);
    g_9188(r.left, r.top + h, r.right, r.bottom, r.left, r.top);
    list->top++;
    list->topOff += _fstrlen(base + list->topOff) + 1;
    base += list->endOff;
    f_21FA_00EE((*base & 1) ? o[0x27] : o[0x26]);
    f_24AB_042B(&r, r.bottom - h, base + 1);
    list->endOff += _fstrlen(base) + 1;
    clip_Pop();
    f_171C_1BBA(list->text);
}

extern char far * far f_24FA_0004(char far *p, char c, unsigned int n);

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
    base = f_171C_1B84(list->text);
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
    f_21FA_00EE((*s & 1) ? o[0x27] : o[0x26]);
    f_24AB_042B(&r, r.top, s + 1);
    list->endOff = f_24FA_0004(base + list->endOff - 2, 0, 0xffff) - base + 1;
    clip_Pop();
    f_171C_1BBA(list->text);
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

void _fastcall f_23E6_0A53(struct Event far *ev)
{
    char far *o;
    struct List far *list;
    int h;
    int line;
    int sel;

    o = win_ObjAddr(ev->code);
    list = (struct List far *)(o + 0x2a);
    f_24AB_02AD(o[0x28]);
    h = f_24AB_030B();
    line = (ev->v - ((struct Rect far *)o)->top) / h + list->top;
    sel = f_23E6_009F(ev->code, line);
    WinPrintf("\nSS=%d, line=%d", sel, line);
    if (*(int far *)(o + 0x24) & 0x20) {
        if ((*(int far *)(o + 0x24) & 0x400) && sel)
            return;
        f_23E6_016B(ev->code);
    }
    if (sel == 0)
        f_23E6_01DC(ev->code, line, 1);
    f_23E6_0392(o);
}

extern void far f_1F80_0081(int ticks);
extern int far f_1FD2_0542(void);

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
    if (fd_50F6_47DA.y + r.top > ev->v) {
        if (ev->modifiers & 0x6800) {
            f_23E6_06F1(0, lo);
            win_DrawElevator(o);
        } else {
            do {
                PrevListLine(lo);
                win_DrawElevator(o);
                f_1F80_0081(1);
            } while (f_1FD2_0542());
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
            } while (f_1FD2_0542());
        }
    }
}
