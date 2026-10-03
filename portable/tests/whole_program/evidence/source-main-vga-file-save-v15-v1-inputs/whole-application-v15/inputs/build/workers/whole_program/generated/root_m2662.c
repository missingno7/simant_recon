#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_slots.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
/* Root module 2662: animation object sets (ANIM.C; Win16 hanim_* unit). */

typedef char  *  *Handle;

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Size {
    int16_t w;
    int16_t h;
};

struct AnimObj {
    char show;          /* 00 */
    char drawn;         /* 01 */
    char wasDrawn;      /* 02 */
    char dirty;         /* 03 */
    char moved;         /* 04 */
    char dos_remove;        /* 05 */
    struct Rect old;    /* 06 */
    struct Rect rect;   /* 0E */
    int16_t x;              /* 16 */
    int16_t y;              /* 18 */
    int16_t w;              /* 1A */
    int16_t h;              /* 1C */
    uint16_t size;      /* 1E */
    int16_t id;             /* 20 */
    Handle buf;         /* 22 */
    int16_t pri;            /* 26 */
    int16_t pic;            /* 28 */
    char  *bufp;     /* 2A */
};

struct AnimSet {
    int16_t count;
    Handle objs;
    int16_t max;
    int16_t nextId;
};

extern char  *  f_171C_1B84(Handle);
extern int16_t  WinPrintf(char  *, ...);
extern int16_t  f_171C_1686(Handle);
extern void  f_1F58_0090(void);
extern Handle  f_171C_1BBA(Handle);
extern int32_t  f_171C_1C1C(Handle);
extern void  Punt(char  *, ...);
extern void ( *  g_9148)(int16_t, int16_t, int16_t, int16_t, char  *);
extern Handle  f_171C_1B2C(Handle, int32_t, int16_t);
extern void  f_208F_0419(struct Size  *, int16_t);

extern struct AnimObj  *  fd_50F6_4A42;
extern Handle  f_171C_1A9E(int32_t, int16_t, char  *);

extern void  f_171C_1C0A(Handle);
extern Handle  f_1A53_00F0(int16_t, int16_t, int16_t);
extern void  f_171C_1C82(Handle);
extern void  clip_Push(void);
extern void  clip_SubExclude(struct Rect  *);
extern void  f_1B4E_003B(int16_t, int16_t, char  *);
extern void  clip_Pop(void);



static int16_t g_67D8 = 15;
static int16_t g_67DA = ~7;
static int16_t g_67DC = 7;
static int16_t g_67DE = 8;

void  hanim_PrintSet(Handle h, char  *name)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;
    int16_t t;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    WinPrintf("\nPrintset @ %s  %d objects", name, set->count);
    for (i = 0; i < set->count; i++, obj++) {
        WinPrintf("\nObject @%p: %d, buf=%p, htype=%d pri=%d, show=%d,remove=%d",
                  obj, obj->id, obj->buf, f_171C_1686(obj->buf), obj->pri, obj->show, obj->dos_remove);
        t = obj->show | obj->dos_remove;
        if ((t != 0 && t != 1) || f_171C_1686(obj->buf) != 1)
            f_1F58_0090();
    }
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}


struct AnimSet  *  f_2662_0100(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->bufp = f_171C_1B84(obj->buf);
        if (f_171C_1C1C(obj->buf) < obj->size * 3)
            Punt("Buffer in set too small!!");
    }
    f_171C_1BBA(set->objs);
    return set;
}

void  f_2662_01B5(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        f_171C_1BBA(obj->buf);
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
    f_171C_1BBA(h);
}


void  f_2662_023F(struct Rect  *r, char  *buf)
{
    (*g_9148)(r->left, r->top, r->right, r->bottom, buf);
}


void  f_2662_0262(struct AnimObj  *obj, int16_t from, int16_t to, int16_t which, struct Rect  *clip, char  *save)
{
    struct Rect  *r;
    int16_t back;
    int16_t n;

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

struct AnimObj  *  _hanim_FindObject(struct AnimObj  *obj, int16_t  *count, int16_t id, int16_t  *index)
{
    int16_t i;

    for (i = 0; i < *count; i++, obj++) {
        if (obj->id == id) {
            *index = i;
            return obj;
        }
    }
    return 0L;
}


int16_t  hanim_AddAnimObject(Handle h, int16_t x, int16_t y, int16_t pic, int16_t pri)
{
    struct AnimSet  *set;
    Handle objsH;
    struct AnimObj  *objs;
    struct AnimObj  *obj;
    int16_t n;
    int16_t id;
    int16_t i;
    struct Size size;
    int16_t right;
    int16_t max;

    set = (struct AnimSet  *)f_171C_1B84(h);
    objsH = set->objs;
    n = set->count;
    if (set->max == n) {
        max = n + 2;
        set->max = max;
        set->objs = f_171C_1B2C(objsH, (int32_t)(max * (int16_t)sizeof(struct AnimObj)), 1);
        objsH = set->objs;
    }
    objs = (struct AnimObj  *)f_171C_1B84(objsH);
    do {
        id = set->nextId & 0x7fff;
        set->nextId++;
    } while (_hanim_FindObject(objs, &set->count, id, &i));
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
    obj->dos_remove = obj->drawn = obj->moved = 0;
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

void  hanim_RemoveAnimObject(Handle h, int16_t id)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_Remove objects not found");
    obj->dos_remove = 1;
    obj->show = 0;
    for (; i < set->count; i++, obj++)
        obj->dirty = 1;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

void  hanim_RemoveAllAnimObjects(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->dos_remove = obj->dirty = 1;
        obj->show = 0;
    }
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}


void  hanim_ActuallyRemoveAnimObjects(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *objs;
    struct AnimObj  *obj;
    struct AnimObj  *p;
    int16_t n;
    int16_t i;
    int16_t j;

    set = (struct AnimSet  *)f_171C_1B84(h);
    objs = (struct AnimObj  *)f_171C_1B84(set->objs);
    n = set->count;
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        if (obj->dos_remove) {
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

void  hanim_HideObject(Handle h, int16_t id)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 0;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

void  hanim_ShowObject(Handle h, int16_t id)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 1;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

/* The two prototypes below (named parameters) precede hanim_SetObjectPos, which calls both functions.
 * They add seven identifiers before it: hanim_SetObjectPos's operand order (width-mask comparison,
 * pri = y + size.h) is exact only at this identifier count (see promotion --steered). */
int16_t  hanim_AddAnimObject(Handle h, int16_t x, int16_t y, int16_t pic, int16_t pri);
void  hanim_RemoveAnimObject(Handle h, int16_t id);

void  hanim_SetObjectPos(int16_t x, int16_t y, int16_t pic, Handle h, int16_t id, int16_t pri)
{
    int16_t reinsert;
    struct AnimSet  *set;
    struct AnimObj  *objs;
    struct AnimObj  *obj;
    int16_t n;
    int16_t i;
    struct Size size;

    reinsert = 0;
    set = (struct AnimSet  *)f_171C_1B84(h);
    n = set->count;
    objs = (struct AnimObj  *)f_171C_1B84(set->objs);
    obj = _hanim_FindObject(objs, &set->count, id, &i);
    if (!obj)
        Punt("anim_Remove objects not found");
    if (x != (int16_t)0x8000)
        obj->x = x;
    else
        x = obj->x;
    if (y != (int16_t)0x8000)
        obj->y = y;
    else
        y = obj->y;
    if (pic == (int16_t)0x8000)
        pic = obj->pic;
    if (pri == (int16_t)0x8000)
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
    hanim_RemoveAnimObject(h, id);
    n = hanim_AddAnimObject(h, x, y, pic, pri);
    set = (struct AnimSet  *)f_171C_1B84(h);
    objs = (struct AnimObj  *)f_171C_1B84(set->objs);
    _hanim_FindObject(objs, &set->count, id, &i)->id = n;
    fd_50F6_4A42->id = id;
    f_171C_1BBA(set->objs);
    f_171C_1BBA(h);
}

static int16_t s_688A = 0;

Handle  hanim_MakeAnimSet(void)
{
    Handle h;
    struct AnimSet  *set;

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
    set = (struct AnimSet  *)f_171C_1B84(h);
    set->max = 0;
    set->count = 0;
    set->objs = f_171C_1A9E(4, 1, "animobjs");
    f_171C_1BBA(h);
    return h;
}

void  hanim_RemoveAnimSet(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *obj;
    int16_t i;

    set = (struct AnimSet  *)f_171C_1B84(h);
    obj = (struct AnimObj  *)f_171C_1B84(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        f_171C_1C0A(obj->buf);
    f_171C_1BBA(set->objs);
    f_171C_1C0A(set->objs);
    f_171C_1BBA(h);
    f_171C_1C0A(h);
}


void  hanim_RenderAnimSet(Handle h)
{
    struct AnimSet  *set;
    struct AnimObj  *objs;
    struct AnimObj  *obj;
    struct Rect  *r;
    int16_t  *pic;
    Handle pich;
    int16_t n;
    int16_t i;

    if (g_5A97 & 1)
        f_171C_1C0A(f_171C_1A9E(6000, 1, "to flush"));
    set = f_2662_0100(h);
    n = set->count;
    objs = (struct AnimObj  *)f_171C_1B84(set->objs);
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
        pic = (int16_t  *)f_171C_1B84(pich);
        if (*pic != 3 && g_5A97 != 2) {
            if (*pic == 0)
                (*fd_50F6_3B58)((char  *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
            else
                Punt("Bad pic type in ANIM.C");
        } else
            (*fd_50F6_37EA)((char  *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
        f_171C_1BBA(pich);
        if (obj->pic < 30000)
            f_171C_1C82(pich);
            obj->drawn = 1;
        } else
            obj->drawn = 0;
    }
    clip_Push();
    clip_Push();
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if (obj->show)
            clip_SubExclude(r);
    }
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if ((!obj->show || _fmemcmp(r, &obj->old, 8)) && obj->wasDrawn) {
            f_1B4E_003B(obj->old.left, obj->old.top, obj->bufp);
            clip_SubExclude(r);
        }
        obj->old = *r;
        _fmemcpy(obj->bufp, obj->bufp + obj->size * 2, obj->size);
    }
    clip_Pop();
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        r = &obj->rect;
        if (obj->show) {
            if (obj->dirty)
                f_1B4E_003B(r->left, r->top, obj->bufp + obj->size);
            clip_SubExclude(r);
        }
    }
    f_171C_1BBA(set->objs);
    f_2662_01B5(h);
    hanim_ActuallyRemoveAnimObjects(h);
    clip_Pop();
}

void  f_2662_1120(int16_t shift, int16_t flag, char  *dest, int16_t pic)
{
    Handle h;
    int16_t  *p;

    h = f_1A53_00F0(pic, 2, 1);
    p = (int16_t  *)f_171C_1B84(h);
    if (*p == 3)
        (*fd_50F6_37EA)((char  *)p + 8, dest, shift, flag);
    else if (*p == 0)
        (*fd_50F6_3B58)((char  *)p + 8, dest, shift, flag);
    f_171C_1BBA(h);
    if (pic < 30000)
        f_171C_1C82(h);
}

#pragma pack(pop)
