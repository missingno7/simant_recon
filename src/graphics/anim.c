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

extern char far * far mem_Lock(Handle);
extern int far WinPrintf(char far *, ...);
extern int far RallocType(Handle);
extern void far kbd_read_key_code(void);
extern Handle far mem_Unlock(Handle);
extern long far mem_Size(Handle);
extern void far Punt(char far *, ...);
extern void (far * near g_9148)(int, int, int, int, char far *);
extern void (far * far fd_50F6_37EE)(struct Rect far *, char far *, struct Rect far *, char far *);
extern Handle far mem_Realloc(Handle, long, int);
extern void far gr_BitMapSize(struct Size far *, int);
extern char near g_5A97;
extern struct AnimObj far * far fd_50F6_4A42;
extern Handle far mem_Alloc(long, int, char far *);
extern void far * far _fmemmove(void far *, void far *, unsigned);
extern void far mem_Free(Handle);
extern Handle far res_load_with_alloc_type(int, int, int);
extern void (far * far fd_50F6_3B58)(char far *, char far *, int, int);
extern void (far * far fd_50F6_37EA)(char far *, char far *, int, int);
extern void far mem_mark_discardable_1c82(Handle);
extern void far clip_Push(void);
extern void far clip_SubExclude(struct Rect far *);
extern void far GPutPic(int, int, char far *);
extern void far clip_Pop(void);
extern int far _fmemcmp(void far *, void far *, unsigned);
extern void far * far _fmemcpy(void far *, void far *, unsigned);

static int g_67D8 = 15;
static int g_67DA = ~7;
static int g_67DC = 7;
static int g_67DE = 8;

void far hanim_PrintSet(Handle h, char far *name)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;
    int t;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    WinPrintf("\nPrintset @ %s  %d objects", name, set->count);
    for (i = 0; i < set->count; i++, obj++) {
        WinPrintf("\nObject @%p: %d, buf=%p, htype=%d pri=%d, show=%d,remove=%d",
                  obj, obj->id, obj->buf, RallocType(obj->buf), obj->pri, obj->show, obj->remove);
        t = obj->show | obj->remove;
        if ((t != 0 && t != 1) || RallocType(obj->buf) != 1)
            kbd_read_key_code();
    }
    mem_Unlock(set->objs);
    mem_Unlock(h);
}


struct AnimSet far * far anim_lock_render_buffers(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->bufp = mem_Lock(obj->buf);
        if (mem_Size(obj->buf) < obj->size * 3)
            Punt("Buffer in set too small!!");
    }
    mem_Unlock(set->objs);
    return set;
}

void far anim_unlock_render_buffers(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        mem_Unlock(obj->buf);
    mem_Unlock(set->objs);
    mem_Unlock(h);
    mem_Unlock(h);
}


void far anim_capture_screen_rect(struct Rect far *r, char far *buf)
{
    (*g_9148)(r->left, r->top, r->right, r->bottom, buf);
}


void far anim_compose_object_range(struct AnimObj far *obj, int from, int to, int which, struct Rect far *clip, char far *save)
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

struct AnimObj far * far _hanim_FindObject(struct AnimObj far *obj, int far *count, int id, int far *index)
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


int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri)
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

    set = (struct AnimSet far *)mem_Lock(h);
    objsH = set->objs;
    n = set->count;
    if (set->max == n) {
        max = n + 2;
        set->max = max;
        set->objs = mem_Realloc(objsH, (long)(max * (int)sizeof(struct AnimObj)), 1);
        objsH = set->objs;
    }
    objs = (struct AnimObj far *)mem_Lock(objsH);
    do {
        id = set->nextId & 0x7fff;
        set->nextId++;
    } while (_hanim_FindObject(objs, &set->count, id, &i));
    gr_BitMapSize(&size, pic);
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
    obj->buf = mem_Alloc(obj->size * 3, 1, "animbufs");
    mem_Unlock(objsH);
    mem_Unlock(h);
    return id;
}

void far hanim_RemoveAnimObject(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_Remove objects not found");
    obj->remove = 1;
    obj->show = 0;
    for (; i < set->count; i++, obj++)
        obj->dirty = 1;
    mem_Unlock(set->objs);
    mem_Unlock(h);
}

void far hanim_RemoveAllAnimObjects(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    for (i = 0; i < set->count; i++, obj++) {
        obj->remove = obj->dirty = 1;
        obj->show = 0;
    }
    mem_Unlock(set->objs);
    mem_Unlock(h);
}


void far hanim_ActuallyRemoveAnimObjects(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    struct AnimObj far *p;
    int n;
    int i;
    int j;

    set = (struct AnimSet far *)mem_Lock(h);
    objs = (struct AnimObj far *)mem_Lock(set->objs);
    n = set->count;
    obj = objs + n - 1;
    for (i = n - 1; i >= 0; i--, obj--) {
        if (obj->remove) {
            mem_Free(obj->buf);
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
    mem_Unlock(set->objs);
    mem_Unlock(h);
}

void far hanim_HideObject(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 0;
    mem_Unlock(set->objs);
    mem_Unlock(h);
}

void far hanim_ShowObject(Handle h, int id)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    obj = _hanim_FindObject(obj, &set->count, id, &i);
    if (!obj)
        Punt("anim_hide object not found");
    obj->show = 1;
    mem_Unlock(set->objs);
    mem_Unlock(h);
}

/* The two prototypes below (named parameters) precede hanim_SetObjectPos, which calls both functions.
 * They add seven identifiers before it: hanim_SetObjectPos's operand order (width-mask comparison,
 * pri = y + size.h) is exact only at this identifier count (see promotion --steered). */
int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri);
void far hanim_RemoveAnimObject(Handle h, int id);

void far hanim_SetObjectPos(int x, int y, int pic, Handle h, int id, int pri)
{
    int reinsert;
    struct AnimSet far *set;
    struct AnimObj far *objs;
    struct AnimObj far *obj;
    int n;
    int i;
    struct Size size;

    reinsert = 0;
    set = (struct AnimSet far *)mem_Lock(h);
    n = set->count;
    objs = (struct AnimObj far *)mem_Lock(set->objs);
    obj = _hanim_FindObject(objs, &set->count, id, &i);
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
        gr_BitMapSize(&size, pic);
        pri = y + size.h;
    }
    if (obj->pri == pri) {
        if (obj->pic != pic) {
            obj->pic = pic;
            gr_BitMapSize(&size, pic);
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
        mem_Unlock(set->objs);
        mem_Unlock(h);
        return;
    }
again:
    mem_Unlock(set->objs);
    mem_Unlock(h);
    hanim_RemoveAnimObject(h, id);
    n = hanim_AddAnimObject(h, x, y, pic, pri);
    set = (struct AnimSet far *)mem_Lock(h);
    objs = (struct AnimObj far *)mem_Lock(set->objs);
    _hanim_FindObject(objs, &set->count, id, &i)->id = n;
    fd_50F6_4A42->id = id;
    mem_Unlock(set->objs);
    mem_Unlock(h);
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
    h = mem_Alloc(sizeof(struct AnimSet), 1, "animHandle");
    set = (struct AnimSet far *)mem_Lock(h);
    set->max = 0;
    set->count = 0;
    set->objs = mem_Alloc(4, 1, "animobjs");
    mem_Unlock(h);
    return h;
}

void far hanim_RemoveAnimSet(Handle h)
{
    struct AnimSet far *set;
    struct AnimObj far *obj;
    int i;

    set = (struct AnimSet far *)mem_Lock(h);
    obj = (struct AnimObj far *)mem_Lock(set->objs);
    for (i = 0; i < set->count; i++, obj++)
        mem_Free(obj->buf);
    mem_Unlock(set->objs);
    mem_Free(set->objs);
    mem_Unlock(h);
    mem_Free(h);
}


void far hanim_RenderAnimSet(Handle h)
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
        mem_Free(mem_Alloc(6000, 1, "to flush"));
    set = anim_lock_render_buffers(h);
    n = set->count;
    objs = (struct AnimObj far *)mem_Lock(set->objs);
    obj = objs;
    for (i = 0; i < n; i++, obj++) {
        if (!obj->dirty)
            continue;
        if ((obj->moved && _fmemcmp(&obj->rect, &obj->old, 8)) || (obj->show && !obj->drawn)) {
            anim_capture_screen_rect(&obj->rect, obj->bufp + obj->size * 2);
            anim_compose_object_range(objs, n - 1, 0, 0, &obj->rect, obj->bufp + obj->size * 2);
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
            anim_compose_object_range(objs, 0, i - 1, 1, &obj->rect, obj->bufp + obj->size);
        pich = res_load_with_alloc_type(obj->pic, 2, 1);
        pic = (int far *)mem_Lock(pich);
        if (*pic != 3 && g_5A97 != 2) {
            if (*pic == 0)
                (*fd_50F6_3B58)((char far *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
            else
                Punt("Bad pic type in ANIM.C");
        } else
            (*fd_50F6_37EA)((char far *)pic + 8, obj->bufp + obj->size, obj->x & g_67DC, 0);
        mem_Unlock(pich);
        if (obj->pic < 30000)
            mem_mark_discardable_1c82(pich);
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
            GPutPic(obj->old.left, obj->old.top, obj->bufp);
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
                GPutPic(r->left, r->top, obj->bufp + obj->size);
            clip_SubExclude(r);
        }
    }
    mem_Unlock(set->objs);
    anim_unlock_render_buffers(h);
    hanim_ActuallyRemoveAnimObjects(h);
    clip_Pop();
}

void far anim_bitmap_to_buffer(int shift, int flag, char far *dest, int pic)
{
    Handle h;
    int far *p;

    h = res_load_with_alloc_type(pic, 2, 1);
    p = (int far *)mem_Lock(h);
    if (*p == 3)
        (*fd_50F6_37EA)((char far *)p + 8, dest, shift, flag);
    else if (*p == 0)
        (*fd_50F6_3B58)((char far *)p + 8, dest, shift, flag);
    mem_Unlock(h);
    if (pic < 30000)
        mem_mark_discardable_1c82(h);
}
