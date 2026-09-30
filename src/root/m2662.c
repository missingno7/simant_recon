/* Root module 2662: animation object sets (ANIM.C; Win16 hanim_* unit). */

typedef char far * far *Handle;

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Size {
    int w;
    int h;
};

struct AnimObj {
    char show;          /* 00 */
    char drawn;         /* 01 */
    char wasDrawn;      /* 02 */
    char dirty;         /* 03 */
    char moved;         /* 04 */
    char remove;        /* 05 */
    struct Rect old;    /* 06 */
    struct Rect rect;   /* 0E */
    int x;              /* 16 */
    int y;              /* 18 */
    int w;              /* 1A */
    int h;              /* 1C */
    unsigned size;      /* 1E */
    int id;             /* 20 */
    Handle buf;         /* 22 */
    int pri;            /* 26 */
    int pic;            /* 28 */
    char far *bufp;     /* 2A */
};

struct AnimSet {
    int count;
    Handle objs;
    int max;
    int nextId;
};

extern char far * far f_171C_1B84(Handle);
extern int far WinPrintf(char far *, ...);
extern int far f_171C_1686(Handle);
extern void far f_1F58_0090(void);
extern Handle far f_171C_1BBA(Handle);
extern long far f_171C_1C1C(Handle);
extern void far Punt(char far *, ...);
extern void (far * near g_9148)(int, int, int, int, char far *);
extern void (far * far fd_50F6_37EE)(struct Rect far *, char far *, struct Rect far *, char far *);
extern Handle far f_171C_1B2C(Handle, long, int);
extern void far f_208F_0419(struct Size far *, int);
extern char near g_5A97;
extern struct AnimObj far * far fd_50F6_4A42;
extern Handle far f_171C_1A9E(long, int, char far *);
extern void far * far _fmemmove(void far *, void far *, unsigned);
extern void far f_171C_1C0A(Handle);
extern Handle far f_1A53_00F0(int, int, int);
extern void (far * far fd_50F6_3B58)(char far *, char far *, int, int);
extern void (far * far fd_50F6_37EA)(char far *, char far *, int, int);
extern void far f_171C_1C82(Handle);
extern void far f_1E57_0DAA(void);
extern void far f_1E57_0AAF(struct Rect far *);
extern void far f_1B4E_003B(int, int, char far *);
extern void far f_1E57_0EB9(void);
extern int far _fmemcmp(void far *, void far *, unsigned);
extern void far * far _fmemcpy(void far *, void far *, unsigned);

static int g_67D8 = 15;
static int g_67DA = ~7;
static int g_67DC = 7;
static int g_67DE = 8;

void far f_2662_0008(Handle h, char far *name)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;
    int t;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    WinPrintf("\nPrintset @ %s  %d objects", name, set->count);
    for (i = 0; i < set->count; i++, obj++) {
        WinPrintf("\nObject @%p: %d, buf=%p, htype=%d pri=%d, show=%d,remove=%d",
                  obj, obj->id, obj->buf, f_171C_1686(obj->buf), obj->pri, obj->show, obj->remove);
        t = obj->show | obj->remove;
        if ((t != 0 && t != 1) || f_171C_1686(obj->buf) != 1)
            f_1F58_0090();
    }
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}


struct AnimSet far * far f_2662_0100(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->bufp = f_171C_1B84(obj->buf);
        if (f_171C_1C1C(obj->buf) < obj->size * 3)
            Punt("Buffer in set too small!!");
    }
    f_171C_1BBA(set->objs);
    return set;
}

void far f_2662_01B5(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        f_171C_1BBA(obj->buf);
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
    f_171C_1BBA(h);
}


void far f_2662_023F(struct Rect far *r, char far *buf)
{
    (*g_9148)(r->left, r->top, r->right, r->bottom, buf);
}


void far f_2662_0262(struct AnimObj far *obj, int from, int to, int which, struct Rect far *clip, char far *save)
{
    struct Rect far *r;
    int back;
    int n;

    if (to < from) {
        back = 1;
        n = from - to + 1;
    } else {
        back = 0;
        n = to - from + 1;
    }
    obj += from;
    while (n) {
        if (obj->drawn) {
            if (which == 0)
                r = &obj->old;
            else
                r = &obj->rect;
            (*fd_50F6_37EE)(r, obj->bufp + obj->size * which, clip, save);
        }
        if (back)
            obj--;
        else
            obj++;
        n--;
    }
}

struct AnimObj far * far f_2662_030C(struct AnimObj far *obj, int far *count, int id, int far *index)
{
    int i;

    for (i = 0; i < *count; i++, obj++) {
        if (obj->id == id) {
            *index = i;
            return obj;
        }
    }
    return 0L;
}


int far f_2662_0348(Handle h, int x, int y, int pic, int pri)
{
    struct AnimSet far *set;
    Handle objsH;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    int n;
    int id;
    int i;
    struct Size size;
    int right;
    int max;

    set = (struct AnimSet far *)f_171C_1B84(h);
    objsH = set->objs;
    n = set->count;
    if (set->max == n) {
        max = n + 2;
        set->max = max;
        set->objs = f_171C_1B2C(objsH, (long)(max * (int)sizeof(struct AnimObj)), 1);
        objsH = set->objs;
    }
    objs = (struct AnimObj far *)f_171C_1B84(objsH);
    do {
        id = set->nextId & 0x7fff;
        set->nextId++;
    } while (f_2662_030C(objs, &set->count, id, &i));
    f_208F_0419(&size, pic);
    if (pri == -1)
        pri = y + size.h;
    obj = objs;
    for (i = 0; n > i; i++, obj++)
        if (obj->pri > pri)
            break;
    if (n != i)
        _fmemmove(obj + 1, obj, (n - i) * sizeof(struct AnimObj));
    set->count++;
    fd_50F6_4A42 = obj;
    obj->show = obj->dirty = 1;
    obj->remove = obj->drawn = obj->moved = 0;
    obj->pri = pri;
    obj->w = size.w;
    obj->h = size.h;
    obj->x = x;
    obj->y = y;
    obj->id = id;
    x &= g_67DA;
    obj->rect.left = x;
    right = (x + g_67D8 + size.w) & g_67DA;
    obj->rect.right = right;
    obj->rect.top = y;
    obj->rect.bottom = y + size.h;
    if (g_5A97 & 1)
        obj->size = (right - x) / 8 * size.h + 4;
    else if (g_5A97 == 2)
        obj->size = (right - x) / 2 * size.h + 4;
    else
        obj->size = ((right - x) / 8 * size.h + 1) * 4;
    obj->pic = pic;
    obj->buf = f_171C_1A9E(obj->size * 3, 1, "animbufs");
    f_171C_1BBA(objsH);
    f_171C_1BBA(h);
    return id;
}

void far f_2662_059C(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    obj = f_2662_030C(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_Remove objects not found");
    obj->remove = 1;
    obj->show = 0;
    for (; i < set->count; i++, obj++)
        obj->dirty = 1;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

void far f_2662_064E(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->remove = obj->dirty = 1;
        obj->show = 0;
    }
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}


void far f_2662_06CB(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    struct AnimObj far *p;
    int n;
    int i;
    int j;

    set = (struct AnimSet far *)f_171C_1B84(h);
    objs = (struct AnimObj far *)f_171C_1B84(set->objs);
    n = set->count;
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        if (obj->remove) {
            f_171C_1C0A(obj->buf);
            n--;
            if (n != i) {
                _fmemmove(obj, obj + 1, (n - i) * sizeof(struct AnimObj));
                for (p = obj, j = i; j < n; j++, p++)
                    p->dirty = 1;
                obj++;
            }
        }
    }
    set->count = n;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

void far f_2662_07E9(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    obj = f_2662_030C(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 0;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

void far f_2662_087B(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    obj = f_2662_030C(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 1;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

/* The two prototypes below (named parameters) precede f_2662_090D, which calls both functions.
 * They add seven identifiers before it: f_2662_090D's operand order (width-mask comparison,
 * pri = y + size.h) is exact only at this identifier count (see promotion --steered). */
int far f_2662_0348(Handle h, int x, int y, int pic, int pri);
void far f_2662_059C(Handle h, int id);

void far f_2662_090D(int x, int y, int pic, Handle h, int id, int pri)
{
    int reinsert;
    struct AnimSet far *set;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    int n;
    int i;
    struct Size size;

    reinsert = 0;
    set = (struct AnimSet far *)f_171C_1B84(h);
    n = set->count;
    objs = (struct AnimObj far *)f_171C_1B84(set->objs);
    obj = f_2662_030C(objs, &set->count, id, &i);
    if (!obj)
        Punt("anim_Remove objects not found");
    if (x != (int)0x8000)
        obj->x = x;
    else
        x = obj->x;
    if (y != (int)0x8000)
        obj->y = y;
    else
        y = obj->y;
    if (pic == (int)0x8000)
        pic = obj->pic;
    if (pri == (int)0x8000)
        pri = obj->pri;
    if (pri == -1) {
        f_208F_0419(&size, pic);
        pri = y + size.h;
    }
    if (obj->pri == pri) {
        if (obj->pic != pic) {
            obj->pic = pic;
            f_208F_0419(&size, pic);
            if (reinsert || (obj->w & g_67DA) != (size.w & g_67DA) || obj->h != size.h)
                goto again;
        }
        x &= g_67DA;
        obj->rect.left = x;
        obj->rect.right = (x + obj->w + g_67D8) & g_67DA;
        obj->rect.top = y;
        obj->rect.bottom = y + obj->h;
        obj->moved = 1;
        for (; i < n; i++, obj++)
            obj->dirty = 1;
        f_171C_1BBA(set->objs);
        f_171C_1BBA(h);
        return;
    }
again:
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
    f_2662_059C(h, id);
    n = f_2662_0348(h, x, y, pic, pri);
    set = (struct AnimSet far *)f_171C_1B84(h);
    objs = (struct AnimObj far *)f_171C_1B84(set->objs);
    f_2662_030C(objs, &set->count, id, &i)->id = n;
    fd_50F6_4A42->id = id;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

static int s_688A = 0;

Handle far hanim_MakeAnimSet(void)
{
    Handle h;
    struct AnimSet far *set;

    if (!s_688A) {
        if (g_5A97 == 2) {
            g_67D8 = 3;
            g_67DA = ~1;
            g_67DC = 1;
            g_67DE = 2;
        }
        s_688A = 1;
    }
    h = f_171C_1A9E(sizeof(struct AnimSet), 1, "animHandle");
    set = (struct AnimSet far *)f_171C_1B84(h);
    set->max = 0;
    set->count = 0;
    set->objs = f_171C_1A9E(4, 1, "animobjs");
    f_171C_1BBA(h);
    return h;
}

void far f_2662_0C06(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)f_171C_1B84(h);
    obj = (struct AnimObj far *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        f_171C_1C0A(obj->buf);
    f_171C_1BBA(set->objs);
    f_171C_1C0A(set->objs);
    f_171C_1BBA(h);
    f_171C_1C0A(h);
}


void far f_2662_0CA2(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    struct Rect far *r;
    int far *pic;
    Handle pich;
    int n;
    int i;

    if (g_5A97 & 1)
        f_171C_1C0A(f_171C_1A9E(6000, 1, "to flush"));
    set = f_2662_0100(h);
    n = set->count;
    objs = (struct AnimObj far *)f_171C_1B84(set->objs);
    obj = objs;
    for (i = 0; i < n; i++, obj++) {
        if (!obj->dirty)
            continue;
        if ((obj->moved && _fmemcmp(&obj->rect, &obj->old, 8)) || (obj->show && !obj->drawn)) {
            f_2662_023F(&obj->rect, obj->bufp + obj->size * 2);
            f_2662_0262(objs, n - 1, 0, 0, &obj->rect, obj->bufp + obj->size * 2);
        } else
            _fmemcpy(obj->bufp + obj->size * 2, obj->bufp, obj->size);
    }
    obj = objs;
    for (i = 0; i < n; i++, obj++) {
        obj->wasDrawn = obj->drawn;
        if (obj->show) {
            if (!obj->dirty)
                continue;
        _fmemcpy(obj->bufp + obj->size, obj->bufp + obj->size * 2, obj->size);
        if (i)
            f_2662_0262(objs, 0, i - 1, 1, &obj->rect, obj->bufp + obj->size);
        pich = f_1A53_00F0(obj->pic, 2, 1);
        pic = (int far *)f_171C_1B84(pich);
        if (*pic != 3 && g_5A97 != 2) {
            if (*pic == 0)
                (*fd_50F6_3B58)((char far *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
            else
                Punt("Bad pic type in ANIM.C");
        } else
            (*fd_50F6_37EA)((char far *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
        f_171C_1BBA(pich);
        if (obj->pic < 30000)
            f_171C_1C82(pich);
            obj->drawn = 1;
        } else
            obj->drawn = 0;
    }
    f_1E57_0DAA();
    f_1E57_0DAA();
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if (obj->show)
            f_1E57_0AAF(r);
    }
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if ((!obj->show || _fmemcmp(r, &obj->old, 8)) && obj->wasDrawn) {
            f_1B4E_003B(obj->old.left, obj->old.top, obj->bufp);
            f_1E57_0AAF(r);
        }
        obj->old = *r;
        _fmemcpy(obj->bufp, obj->bufp + obj->size * 2, obj->size);
    }
    f_1E57_0EB9();
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if (obj->show) {
            if (obj->dirty)
                f_1B4E_003B(r->left, r->top, obj->bufp + obj->size);
            f_1E57_0AAF(r);
        }
    }
    f_171C_1BBA(set->objs);
    f_2662_01B5(h);
    f_2662_06CB(h);
    f_1E57_0EB9();
}

void far f_2662_1120(int shift, int flag, char far *dest, int pic)
{
    Handle h;
    int far *p;

    h = f_1A53_00F0(pic, 2, 1);
    p = (int far *)f_171C_1B84(h);
    if (*p == 3)
        (*fd_50F6_37EA)((char far *)p + 8, dest, shift, flag);
    else if (*p == 0)
        (*fd_50F6_3B58)((char far *)p + 8, dest, shift, flag);
    f_171C_1BBA(h);
    if (pic < 30000)
        f_171C_1C82(h);
}
