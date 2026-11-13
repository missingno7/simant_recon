/*
 * Updates window object selection, visibility, formatting and bitmaps. It also draws object
 * text, bars and proximity menus.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 22BF; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

#include "pt.h"

#include "rect.h"

#include "event.h"

extern int far font_StringWidth(char far *text);
extern int far font_FontHeight(void);
extern void _fastcall win_LockWin(int win);
extern char far * far win_locked_resource_ptr(int win);
extern void _fastcall win_UnlockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern int clip_window_z_order[];
extern void far input_register_object_rect(char far *obj, int objNum);
extern void far input_remove_object_rect(int objNum);
extern void far GRectInv(char far *rect);
int _fastcall win_IsWinOpen(int win);
extern void _fastcall win_DrawBitMapAtObj(int id, char far *obj);
extern void _fastcall win_DrawObject(char far *obj);
void _fastcall win_SetGroupSelectedState(int win, int group, int selected);
extern char far * far _fstrrchr(char far *s, int c);
extern char far * far _fstrcpy(char far *dst, char far *src);
extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern int far WinPrintf(char far *format, ...);
extern unsigned int far _fstrlen(char far *s);
extern char far * far * far RallocRealloc(char far * far *handle, long size, int flags);
extern char far * far * far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(char far * far *handle);
extern void far mem_Unlock(char far * far *handle);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern void far gr_CenterStrInRectClear(struct Rect far *rect, char far *text);
extern void far clip_Pop(void);
extern void far font_SetFont(int font);
extern char far * far * far db_LoadObject(int object, int kind);
extern char near gfx_display_mode;
extern void far gfx_set_ega_palette(char far *pal, int count);
extern void far gfx_set_dac_palette(char far *pal, int count);
extern void far db_ReleaseObject(int object, int kind);
extern void far Punt(char far *format, ...);
extern char far * far * near win_handles[];
extern void far win_Open(int win, int p0, int p1);
extern void _fastcall _win_SetProxItem(int obj);
extern void far ButtonHeldInit(void);
extern int far ButtonHeld(void);
extern int far win_GetProxEvent(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern void _fastcall win_Close(int win);
extern char far win_colors[][6];
extern struct Pt gfx_text_pen_x;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
extern void far GRectFill(struct Rect far *rect, int color);
extern int near _foreColor;
extern int near g_3DE2;
extern void _fastcall win_Recalc(int win);

struct Pt _fastcall win_StringSize(char far *);
void _fastcall win_GetObjSize(int, struct Pt far *);
void _fastcall win_get_obj_layout_rect(int, struct Rect far *);
void _fastcall win_set_obj_layout_rect(int, struct Rect far *);
void _fastcall win_SetObjSelectableState(int, int);
void _fastcall win_MakeObjSelectable(int);
void _fastcall win_MakeObjUnselectable(int);
void _fastcall win_SetGroupSelectableState(int, int, int);
void _fastcall win_MakeGroupSelectable(int, int);
void _fastcall win_MakeGroupUnselectable(int, int);
void _fastcall win_ObjInv(int);
void _fastcall win_SetObjSelectedStateI(int, int);
void _fastcall win_SetObjSelectedState(int, int);
void _fastcall win_MakeObjSelected(int);
void _fastcall win_MakeObjUnselected(int);
void _fastcall win_SetGroupSelectedState(int, int, int);
void _fastcall win_MakeGroupSelected(int, int);
void _fastcall win_MakeGroupUnselected(int, int);
void _fastcall win_SetObjVisibleState(int, int);
void _fastcall win_MakeObjVisible(int);
void _fastcall win_MakeObjInvisible(int);
void _fastcall win_SetGroupVisibleState(int, int, int);
void _fastcall win_MakeGroupVisible(int, int);
void _fastcall win_MakeGroupInvisible(int, int);
void _fastcall win_replace_obj_text_suffix(int, char far *);
void far win_SetObjFormatStr(int, ...);
void far win_CenterStrAtObj(int, char far *);
void far win_ObjFormatPrint(int, ...);
int _fastcall win_SetPalette(int);
void _fastcall win_set_obj_colour_index(int, int);
void _fastcall win_SetObjBitmap(int, int);
int _fastcall win_IsWinOpen(int);
int _fastcall win_IsWinInFront(int);
int _fastcall f_22BF_0A34(int);
int _fastcall win_is_zoomed(int);
int _fastcall win_is_obj_selectable(int);
int _fastcall win_object_count(int);
int _fastcall win_set_flag_0040(int);
int _fastcall win_clear_flag_0040(int);
void _fastcall win_offset_rect_edges(struct Rect far *, struct Rect far *, int, int, int, int);
int far win_DoProxMenu(int, int, ...);
void far win_ClearObjToEOL(int);
void far win_clear_obj_rect(int);
void far win_PrintfAtObj(int, char far *, ...);
void far win_DrawHBar(int, long);
void far win_DrawVBar(int, long);
void far win_copy_obj_layout_origin(int, int);

struct Pt _fastcall win_StringSize(char far *text)
{
    struct Pt size;

    size.x = font_StringWidth(text);
    size.y = font_FontHeight();
    return size;
}

void _fastcall win_GetObjSize(int obj, struct Pt far *size)
{
    char far *w;
    struct Rect r;

    win_LockWin(obj);
    w = win_locked_resource_ptr(obj);
    r = *((struct Rect far * far *)(w + 0x2c))[obj & 0xff]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    size->x = r.right - r.left;
    size->y = r.bottom - r.top;
    win_UnlockWin(obj);
}

void _fastcall win_get_obj_layout_rect(int obj, struct Rect far *r)
{
    win_LockWin(obj);
    *r = *(struct Rect far *)(win_ObjAddr(obj) + 8); /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(obj);
}

void _fastcall win_set_obj_layout_rect(int obj, struct Rect far *r)
{
    win_LockWin(obj);
    *(struct Rect far *)(win_ObjAddr(obj) + 8) = *r; /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectableState(int obj, int state)
{
    unsigned char far *o;

    win_LockWin(obj);
    o = (unsigned char far *)win_ObjAddr(obj);
    if (clip_window_z_order[0] == (obj & 0xff00)) {
        if (state == 1) {
            if (!(o[0x24] & 2)) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
                input_register_object_rect((char far *)o, obj);
        } else if (o[0x24] & 2) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            input_remove_object_rect(obj);
        }
    }
    *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2; /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(obj);
}

void _fastcall win_MakeObjSelectable(int obj)
{
    win_SetObjSelectableState(obj, 1);
}

void _fastcall win_MakeObjUnselectable(int obj)
{
    win_SetObjSelectableState(obj, 0);
}

void _fastcall win_SetGroupSelectableState(int win, int group, int state)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    win_LockWin(win);
    objNum = win & 0xff00;
    w = win_locked_resource_ptr(win);
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) { /* Known Win.count; earlier shared tag changes exact code or original declaration context is unresolved. */
        o = ((unsigned char far * far *)(w + 0x2c))[i]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (o[0x20] == group) { /* Known Obj.group; earlier shared tag changes exact code or original declaration context is unresolved. */
            if (clip_window_z_order[0] == win) {
                if (state == 1) {
                    if (!(o[0x24] & 2)) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
                        input_register_object_rect((char far *)o, objNum);
                } else if (o[0x24] & 2) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
                    input_remove_object_rect(objNum);
                }
            }
            *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2; /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        }
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupSelectable(int win, int group)
{
    win_SetGroupSelectableState(win, group, 1);
}

void _fastcall win_MakeGroupUnselectable(int win, int group)
{
    win_SetGroupSelectableState(win, group, 0);
}

void _fastcall win_ObjInv(int obj)
{
    char far *w;

    win_LockWin(obj);
    w = win_locked_resource_ptr(obj);
    GRectInv(((char far * far *)(w + 0x2c))[obj & 0xff]); /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectedStateI(int obj, int selected)
{
    char far *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (win_IsWinOpen(obj) && ((*(unsigned far *)(o + 0x24) & 4) >> 2) != selected) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4; /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (*(unsigned far *)(o + 0x24) & 1) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            if (o[0x21] == 13) /* Known Obj.type; earlier shared tag changes exact code or original declaration context is unresolved. */
                win_DrawBitMapAtObj(*(int far *)(o + 0x26 + ((*(unsigned far *)(o + 0x24) & 4) == 0 ? 4 : 2)), o); /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            else if (o[0x21] == 5 || o[0x21] == 17) /* Known Obj.type; earlier shared tag changes exact code or original declaration context is unresolved. */
                win_DrawObject(o);
            else
                GRectInv(o);
        }
    }
    *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4; /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectedState(int obj, int selected)
{
    unsigned char far *o;

    win_LockWin(obj);
    o = (unsigned char far *)win_ObjAddr(obj);
    if (o[0x24] & 0x20) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        win_SetGroupSelectedState(obj, o[0x20], 0); /* Known Obj.group; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_SetObjSelectedStateI(obj, selected);
    win_UnlockWin(obj);
}

void _fastcall win_MakeObjSelected(int obj)
{
    win_SetObjSelectedState(obj, 1);
}

void _fastcall win_MakeObjUnselected(int obj)
{
    win_SetObjSelectedState(obj, 0);
}

void _fastcall win_SetGroupSelectedState(int win, int group, int selected)
{
    char far *w;
    int i;
    int objNum;

    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    objNum = win & 0xff00;
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) { /* Known Win.count; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (((unsigned char far * far *)(w + 0x2c))[i][0x20] == group) /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
            win_SetObjSelectedStateI(objNum, selected);
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupSelected(int win, int group)
{
    win_SetGroupSelectedState(win, group, 1);
}

void _fastcall win_MakeGroupUnselected(int win, int group)
{
    win_SetGroupSelectedState(win, group, 0);
}

#include "obj.h"

void _fastcall win_SetObjVisibleState(int obj, int visible)
{
    unsigned char far *o;

    o = (unsigned char far *)win_ObjAddr(obj);
    if ((*(unsigned char far *)&((struct Obj far *)o)->flags & 1) != visible) {
        ((struct Obj far *)o)->flags ^= (*(unsigned char far *)&((struct Obj far *)o)->flags ^ visible) & 1;
        if ((*(unsigned char far *)&((struct Obj far *)o)->flags & 4) && ((struct Obj far *)o)->type == 1)
            GRectInv((char far *)o);
    }
}

void _fastcall win_MakeObjVisible(int obj)
{
    win_SetObjVisibleState(obj, 1);
}

void _fastcall win_MakeObjInvisible(int obj)
{
    win_SetObjVisibleState(obj, 0);
}

#include "win.h"

void _fastcall win_SetGroupVisibleState(int win, int group, int visible)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    objNum = win;
    for (i = 0; i < ((struct Win far *)w)->count; i++, objNum++) {
        o = (unsigned char far *)((struct Win far *)w)->objs[i]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (((struct Obj far *)o)->group == group && (*(unsigned char far *)&((struct Obj far *)o)->flags & 1) != visible) { /* Known Obj.group; earlier shared tag changes exact code or original declaration context is unresolved. */
            ((struct Obj far *)o)->flags ^= (*(unsigned char far *)&((struct Obj far *)o)->flags ^ visible) & 1;
            if ((*(unsigned char far *)&((struct Obj far *)o)->flags & 4) && ((struct Obj far *)o)->type != 13 && ((struct Obj far *)o)->type != 5)
                GRectInv((char far *)o);
        }
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupVisible(int win, int group)
{
    win_SetGroupVisibleState(win, group, 1);
}

void _fastcall win_MakeGroupInvisible(int win, int group)
{
    win_SetGroupVisibleState(win, group, 0);
}

/*
 * Replace the text after the object's last space; do nothing when no space exists.
 */
void _fastcall win_replace_obj_text_suffix(int obj, char far *text)
{
    char far *p;

    p = _fstrrchr(win_ObjAddr(obj) + 0x28, ' ');
    if (p)
        _fstrcpy(p + 1, text);
}

void far win_SetObjFormatStr(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    win_LockWin(obj);
    vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, (char far *)(&obj + 1));
    WinPrintf("\n= %s", (char far *)buf);
    vsprintf(buf, o + 0x2e, (char far *)(&obj + 1));
    len = _fstrlen(buf) + 1;
    if ((rec = ((struct Obj far *)o)->text_handle) != 0) {
        if (_fstrlen(*rec) + 1 < len) {
            rec = RallocRealloc(rec, (long)(len + 4), 1);
            ((struct Obj far *)o)->text_handle = rec;
        }
    } else {
        rec = Ralloc((long)(len + 8), 1, "formatStr");
        ((struct Obj far *)o)->text_handle = rec;
    }
    _fstrcpy(mem_Lock(rec), buf);
    mem_Unlock(rec);
    win_UnlockWin(obj);
}

void far win_CenterStrAtObj(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    clip_Push();
    clip_SubInclude(&r);
    gr_CenterStrInRectClear(&r, text);
    clip_Pop();
}

void far win_ObjFormatPrint(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    win_LockWin(obj);
    vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, (char far *)(&obj + 1));
    WinPrintf("\n= %s", (char far *)buf);
    vsprintf(buf, o + 0x2e, (char far *)(&obj + 1));
    len = _fstrlen(buf) + 1;
    if ((rec = ((struct Obj far *)o)->text_handle) != 0) {
        if (_fstrlen(*rec) + 2 < len) {
            rec = RallocRealloc(rec, (long)(len + 4), 1);
            ((struct Obj far *)o)->text_handle = rec;
        }
    } else {
        rec = Ralloc((long)(len + 8), 1, "formatStr");
        ((struct Obj far *)o)->text_handle = rec;
    }
    _fstrcpy(mem_Lock(rec), buf);
    font_SetFont(o[0x28]);
    win_CenterStrAtObj(obj, buf);
    font_SetFont(0);
    mem_Unlock(rec);
    win_UnlockWin(obj);
}

int _fastcall win_SetPalette(int id)
{
    char far * far *h;
    char far *p;
    char far *q;
    int i;
    char pal[18];

    h = db_LoadObject(id, 0xf);
    if (h == 0)
        return 0;
    p = *h;
    switch (p[1]) {
    case 0:
        if (gfx_display_mode == 0) {
            q = p + 2;
            for (i = 0; i < 16; q += 3, i++)
                pal[i] = ((((q[0] & 0x10) | ((((q[1] & 0x10) | ((q[2] & 0x10) >> 1)) >> 1) | (q[2] & 0x20))) >> 1 | (q[1] & 0x20)) >> 1) | (q[0] & 0x20);
            pal[17] = 0;
            gfx_set_ega_palette(pal, p[0]);
        } else if (gfx_display_mode == 8) {
            gfx_set_dac_palette(p + 2, p[0]);
        }
        break;
    case 1:
        gfx_set_ega_palette(p + 2, p[0]);
        break;
    }
    db_ReleaseObject(id, 0xf);
}

/*
 * Set the object's primary color-table index; the caller must hold its window lock.
 */
void _fastcall win_set_obj_colour_index(int obj, int color)
{
    ((struct Obj far *)win_ObjAddr(obj))->palette = color;
}

void _fastcall win_SetObjBitmap(int obj, int bitmap)
{
    char far *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (((struct Obj far *)o)->type != 6)
        Punt("Attempt to set bitmap on non-bitmap object");
    ((struct Obj far *)o)->payload28 = bitmap;
    win_UnlockWin(obj);
}

int _fastcall win_IsWinOpen(int win)
{
    int open;
    char far * far *h;
    char far *w;

    open = 0;
    if ((h = win_handles[win >> 8]) != 0) {
        if ((w = mem_Lock(h)) != 0) {
            open = (*(unsigned far *)&((struct Win far *)w)->flags & 0x200) >> 9;
            mem_Unlock(h);
        } else {
            win_handles[win >> 8] = 0;
        }
    }
    return open;
}

int _fastcall win_IsWinInFront(int win)
{
    if (clip_window_z_order[0] == win)
        return 1;
    return 0;
}

int _fastcall f_22BF_0A34(int win)
{
    int r;

    win_LockWin(win);
    r = (*(unsigned far *)&((struct Win far *)win_locked_resource_ptr(win))->flags & 0x40) >> 6;
    win_UnlockWin(win);
    return r;
}

int _fastcall win_is_zoomed(int win)
{
    int r;

    win_LockWin(win);
    r = (*(unsigned far *)&((struct Win far *)win_locked_resource_ptr(win))->flags & 0x80) >> 7;
    win_UnlockWin(win);
    return r;
}

/*
 * Return whether the object is selectable.
 */
int _fastcall win_is_obj_selectable(int obj)
{
    int r;

    win_LockWin(obj);
    r = (((struct Obj far *)win_ObjAddr(obj))->flags & 2) >> 1;
    win_UnlockWin(obj);
    return r;
}

/*
 * Return the number of objects in a window resource.
 */
int _fastcall win_object_count(int win)
{
    int n;

    win_LockWin(win);
    n = ((struct Win far *)win_locked_resource_ptr(win))->count;
    win_UnlockWin(win);
    return n;
}

int _fastcall win_set_flag_0040(int win)
{
    char far *w;
    int r;

    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    r = (*(unsigned far *)&((struct Win far *)w)->flags & 0x40) >> 6;
    *(unsigned far *)&((struct Win far *)w)->flags |= 0x40;
    win_UnlockWin(win);
    return r;
}

int _fastcall win_clear_flag_0040(int win)
{
    char far *w;
    int r;

    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    r = (*(unsigned far *)&((struct Win far *)w)->flags & 0x40) >> 6;
    *(unsigned far *)&((struct Win far *)w)->flags &= ~0x40;
    win_UnlockWin(win);
    return r;
}

/*
 * Copy rectangle bounds with independent offsets for all four edges.
 */
void _fastcall win_offset_rect_edges(struct Rect far *dst, struct Rect far *src, int l, int t, int r, int b)
{
    dst->left = src->left + l;
    dst->right = src->right + r;
    dst->top = src->top + t;
    dst->bottom = src->bottom + b;
}

int far win_DoProxMenu(int win, int item, ...)
{
    int result;
    int last;
    struct Event ev;

    result = -1;
    win_Open(win, (&item)[1], (&item)[2]);
    if (item != -1)
        _win_SetProxItem(win + item + 2);
    ButtonHeldInit();
    last = -1;
    for (;;) {
        if (!win_IsWinOpen(win))
            break;
        if (!ButtonHeld())
            ev.code = win_GetProxEvent();
        else if (!win_GetEvent(&ev))
            continue;
        if ((unsigned)ev.code < (unsigned)win || (unsigned)win + 0x100 <= (unsigned)ev.code)
            continue;
        if ((unsigned)win + 2 <= (unsigned)ev.code)
            result = ev.code - win - 2;
        break;
    }
    win_Close(win);
    return result;
}

void far win_ClearObjToEOL(int obj)
{
    struct Rect r;
    int c;
    int top;
    int left;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = ((struct Obj far *)win_ObjAddr(obj))->palette;
    if (gfx_display_mode & 1)
        c = win_colors[c][3];
    else
        c = win_colors[c][2];
    c = (c << 8) | (c & 0xff);
    top = gfx_text_pen_x.y;
    if (top < r.top)
        top = r.top;
    if (r.bottom > top && (left = gfx_text_pen_x.x) >= r.left && r.right > left)
        (*gfx_fill_rect_hook)(left, top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

/*
 * Fill the object's rectangle using its primary color's color-mode background entry.
 */
void far win_clear_obj_rect(int obj)
{
    struct Rect r;
    int c;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = ((struct Obj far *)win_ObjAddr(obj))->palette;
    c = win_colors[c][2];
    c = (c & 0xf) | (((c & 0xf) << 4) | (c << 8));
    (*gfx_fill_rect_hook)(r.left, r.top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

void far win_PrintfAtObj(int obj, char far *format, ...)
{
    char buf[100];

    vsprintf(buf, format, (char far *)(&format + 1));
    win_CenterStrAtObj(obj, buf);
}

/* The label below is inferred from the relocation order (ZI-2): the original has a
   record break at 0DDD.  More counted line entries before it would explain it too. */
void far win_DrawHBar(int obj, long fraction)
{
    struct Rect r;
    int right;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int end = r.right;
        long extent = (long)(end - r.left);
        right = end;
        r.right = r.left + (int)((extent * fraction) / 65536L);
    }
    if (r.right <= r.left)
        goto rest;
    GRectFill(&r, _foreColor);
rest:
    if (r.right < right) {
        r.left = r.right;
        r.right = right;
        GRectFill(&r, g_3DE2);
    }
}

void far win_DrawVBar(int obj, long fraction)
{
    struct Rect r;
    int top;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int end = r.bottom;
        int start = r.top;
        int height = end - start;
        top = start;
        r.top = end - (int)(((long)height * fraction) / 65536L);
    }
    if (r.top < r.bottom)
        GRectFill(&r, _foreColor);
    if (r.top > top) {
        r.bottom = r.top;
        r.top = top;
        GRectFill(&r, g_3DE2);
    }
}

void far win_copy_obj_layout_origin(int src, int dst)
{
    int far *o;
    struct Rect r;

    win_LockWin(src);
    win_LockWin(dst);
    o = (int far *)(win_ObjAddr(dst) + 8); /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    r = *(struct Rect far *)&((struct Obj far *)win_ObjAddr(src))->x;
    o[0] = r.left;
    o[1] = r.top;
    win_Recalc(dst);
    win_UnlockWin(src);
    win_UnlockWin(dst);
}
