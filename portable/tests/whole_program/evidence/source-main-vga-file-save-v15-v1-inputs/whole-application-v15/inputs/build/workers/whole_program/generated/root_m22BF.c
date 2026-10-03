#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 22BF: window object attribute and drawing helpers. */

struct Pt {
    int16_t x;
    int16_t y;
};

struct Rect { int16_t left; int16_t top; int16_t right; int16_t bottom; };

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

extern int16_t  f_24AB_0329(char  *text);
extern int16_t  f_24AB_030B(void);
extern void  win_LockWin(int16_t win);
extern char  *  f_2505_0006(int16_t win);
extern void  win_UnlockWin(int16_t win);
extern char  *  win_ObjAddr(int16_t obj);
extern int16_t g_5702[];
extern void  f_1FD2_03EB(char  *obj, int16_t objNum);
extern void  f_1FD2_0438(int16_t objNum);
extern void  f_1CE2_0430(char  *rect);
int16_t  win_IsWinOpen(int16_t win);
extern void  win_DrawBitMapAtObj(int16_t id, char  *obj);
extern void  win_DrawObject(char  *obj);
void  win_SetGroupSelectedState(int16_t win, int16_t group, int16_t selected);


extern int16_t  WinPrintf(char  *format, ...);

extern char  *  *  f_171C_18A6(char  *  *handle, int32_t size, int16_t flags);
extern char  *  *  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  clip_Push(void);
extern void  clip_SubInclude(struct Rect  *rect);
extern void  f_208F_011F(struct Rect  *rect, char  *text);
extern void  clip_Pop(void);
extern void  f_24AB_02AD(int16_t font);
extern char  *  *  db_LoadObject(int16_t object, int16_t kind);

extern void  f_1B4E_01A1(char  *pal, int16_t count);
extern void  f_1B4E_01AE(char  *pal, int16_t count);
extern void  db_ReleaseObject(int16_t object, int16_t kind);
extern void  Punt(char  *format, ...);

extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;
extern void  _win_SetProxItem(int16_t obj);
extern void  ButtonHeldInit(void);
extern int16_t  ButtonHeld(void);
extern int16_t  win_GetProxEvent(void);
extern int16_t  win_GetEvent(struct Event  *ev);
extern void  win_Close(int16_t win);
extern int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];
extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);
extern void  win_Recalc(int16_t win);

struct Pt  win_StringSize(char  *);
void  win_GetObjSize(int16_t, struct Pt  *);
void  f_22BF_00AA(int16_t, struct Rect  *);
void  f_22BF_00DD(int16_t, struct Rect  *);
void  win_SetObjSelectableState(int16_t, int16_t);
void  win_MakeObjSelectable(int16_t);
void  win_MakeObjUnselectable(int16_t);
void  win_SetGroupSelectableState(int16_t, int16_t, int16_t);
void  win_MakeGroupSelectable(int16_t, int16_t);
void  win_MakeGroupUnselectable(int16_t, int16_t);
void  win_ObjInv(int16_t);
void  win_SetObjSelectedStateI(int16_t, int16_t);
void  win_SetObjSelectedState(int16_t, int16_t);
void  win_MakeObjSelected(int16_t);
void  win_MakeObjUnselected(int16_t);
void  win_SetGroupSelectedState(int16_t, int16_t, int16_t);
void  win_MakeGroupSelected(int16_t, int16_t);
void  win_MakeGroupUnselected(int16_t, int16_t);
void  win_SetObjVisibleState(int16_t, int16_t);
void  win_MakeObjVisible(int16_t);
void  win_MakeObjInvisible(int16_t);
void  win_SetGroupVisibleState(int16_t, int16_t, int16_t);
void  win_MakeGroupVisible(int16_t, int16_t);
void  win_MakeGroupInvisible(int16_t, int16_t);
void  f_22BF_0555(int16_t, char  *);
void  win_SetObjFormatStr(int32_t _dos_obj_wide, ...);
void  win_CenterStrAtObj(int16_t, char  *);
void  win_ObjFormatPrint(int32_t _dos_obj_wide, ...);
int16_t  win_SetPalette(int16_t);
void  f_22BF_094F(int16_t, int16_t);
void  win_SetObjBitmap(int16_t, int16_t);
int16_t  win_IsWinOpen(int16_t);
int16_t  win_IsWinInFront(int16_t);
int16_t  f_22BF_0A34(int16_t);
int16_t  f_22BF_0A65(int16_t);
int16_t  f_22BF_0A97(int16_t);
int16_t  f_22BF_0AC5(int16_t);
int16_t  f_22BF_0AEF(int16_t);
int16_t  f_22BF_0B25(int16_t);
void  f_22BF_0B5B(struct Rect  *, struct Rect  *, int16_t, int16_t, int16_t, int16_t);
int16_t win_DoProxMenu(int16_t win, int16_t item, int16_t supplied_count, int16_t p0, int16_t p1) ;
void  f_22BF_0C38(int16_t);
void  f_22BF_0CDD(int16_t);
void  win_PrintfAtObj(int16_t, char  *, ...);
void  win_DrawHBar(int16_t, int32_t);
void  win_DrawVBar(int16_t, int32_t);
void  f_22BF_0E83(int16_t, int16_t);

struct Pt  win_StringSize(char  *text)
{
    struct Pt size;

    size.x = f_24AB_0329(text);
    size.y = f_24AB_030B();
    return size;
}

void  win_GetObjSize(int16_t obj, struct Pt  *size)
{
    char  *w;
    struct Rect r;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    r = *((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[obj & 0xff]);
    size->x = r.right - r.left;
    size->y = r.bottom - r.top;
    win_UnlockWin(obj);
}

void  f_22BF_00AA(int16_t obj, struct Rect  *r)
{
    win_LockWin(obj);
    *r = *(struct Rect  *)(win_ObjAddr(obj) + 8);
    win_UnlockWin(obj);
}

void  f_22BF_00DD(int16_t obj, struct Rect  *r)
{
    win_LockWin(obj);
    *(struct Rect  *)(win_ObjAddr(obj) + 8) = *r;
    win_UnlockWin(obj);
}

void  win_SetObjSelectableState(int16_t obj, int16_t state)
{
    uint8_t  *o;

    win_LockWin(obj);
    o = (uint8_t  *)win_ObjAddr(obj);
    if (g_5702[0] == (obj & 0xff00)) {
        if (state == 1) {
            if (!(o[0x24] & 2))
                f_1FD2_03EB((char  *)o, obj);
        } else if (o[0x24] & 2) {
            f_1FD2_0438(obj);
        }
    }
    *(uint16_t  *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2;
    win_UnlockWin(obj);
}

void  win_MakeObjSelectable(int16_t obj)
{
    win_SetObjSelectableState(obj, 1);
}

void  win_MakeObjUnselectable(int16_t obj)
{
    win_SetObjSelectableState(obj, 0);
}

void  win_SetGroupSelectableState(int16_t win, int16_t group, int16_t state)
{
    char  *w;
    int16_t i;
    int16_t objNum;
    uint8_t  *o;

    win_LockWin(win);
    objNum = win & 0xff00;
    w = f_2505_0006(win);
    for (i = 0; i < sim_window_wire_read_i16(w, 0x0c); i++, objNum++) {
        o = ((uint8_t *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (o[0x20] == group) {
            if (g_5702[0] == win) {
                if (state == 1) {
                    if (!(o[0x24] & 2))
                        f_1FD2_03EB((char  *)o, objNum);
                } else if (o[0x24] & 2) {
                    f_1FD2_0438(objNum);
                }
            }
            *(uint16_t  *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2;
        }
    }
    win_UnlockWin(win);
}

void  win_MakeGroupSelectable(int16_t win, int16_t group)
{
    win_SetGroupSelectableState(win, group, 1);
}

void  win_MakeGroupUnselectable(int16_t win, int16_t group)
{
    win_SetGroupSelectableState(win, group, 0);
}

void  win_ObjInv(int16_t obj)
{
    char  *w;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    f_1CE2_0430(((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[obj & 0xff]));
    win_UnlockWin(obj);
}

void  win_SetObjSelectedStateI(int16_t obj, int16_t selected)
{
    char  *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (win_IsWinOpen(obj) && ((*(uint16_t  *)(o + 0x24) & 4) >> 2) != selected) {
        *(uint16_t  *)(o + 0x24) ^= (*(uint16_t  *)(o + 0x24) ^ (selected << 2)) & 4;
        if (*(uint16_t  *)(o + 0x24) & 1) {
            if (o[0x21] == 13)
                win_DrawBitMapAtObj(*(int16_t  *)(o + 0x26 + ((*(uint16_t  *)(o + 0x24) & 4) == 0 ? 4 : 2)), o);
            else if (o[0x21] == 5 || o[0x21] == 17)
                win_DrawObject(o);
            else
                f_1CE2_0430(o);
        }
    }
    *(uint16_t  *)(o + 0x24) ^= (*(uint16_t  *)(o + 0x24) ^ (selected << 2)) & 4;
    win_UnlockWin(obj);
}

void  win_SetObjSelectedState(int16_t obj, int16_t selected)
{
    uint8_t  *o;

    win_LockWin(obj);
    o = (uint8_t  *)win_ObjAddr(obj);
    if (o[0x24] & 0x20)
        win_SetGroupSelectedState(obj, o[0x20], 0);
    win_SetObjSelectedStateI(obj, selected);
    win_UnlockWin(obj);
}

void  win_MakeObjSelected(int16_t obj)
{
    win_SetObjSelectedState(obj, 1);
}

void  win_MakeObjUnselected(int16_t obj)
{
    win_SetObjSelectedState(obj, 0);
}

void  win_SetGroupSelectedState(int16_t win, int16_t group, int16_t selected)
{
    char  *w;
    int16_t i;
    int16_t objNum;

    win_LockWin(win);
    w = f_2505_0006(win);
    objNum = win & 0xff00;
    for (i = 0; i < sim_window_wire_read_i16(w, 0x0c); i++, objNum++) {
        if (((uint8_t *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i])[0x20] == group)
            win_SetObjSelectedStateI(objNum, selected);
    }
    win_UnlockWin(win);
}

void  win_MakeGroupSelected(int16_t win, int16_t group)
{
    win_SetGroupSelectedState(win, group, 1);
}

void  win_MakeGroupUnselected(int16_t win, int16_t group)
{
    win_SetGroupSelectedState(win, group, 0);
}

void  win_SetObjVisibleState(int16_t obj, int16_t visible)
{
    uint8_t  *o;

    o = (uint8_t  *)win_ObjAddr(obj);
    if ((o[0x24] & 1) != visible) {
        *(uint16_t  *)(o + 0x24) ^= (o[0x24] ^ visible) & 1;
        if ((o[0x24] & 4) && o[0x21] == 1)
            f_1CE2_0430((char  *)o);
    }
}

void  win_MakeObjVisible(int16_t obj)
{
    win_SetObjVisibleState(obj, 1);
}

void  win_MakeObjInvisible(int16_t obj)
{
    win_SetObjVisibleState(obj, 0);
}

void  win_SetGroupVisibleState(int16_t win, int16_t group, int16_t visible)
{
    char  *w;
    int16_t i;
    int16_t objNum;
    uint8_t  *o;

    win_LockWin(win);
    w = f_2505_0006(win);
    objNum = win;
    for (i = 0; i < sim_window_wire_read_i16(w, 0x0c); i++, objNum++) {
        o = ((uint8_t *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (o[0x20] == group && (o[0x24] & 1) != visible) {
            *(uint16_t  *)(o + 0x24) ^= (o[0x24] ^ visible) & 1;
            if ((o[0x24] & 4) && o[0x21] != 13 && o[0x21] != 5)
                f_1CE2_0430((char  *)o);
        }
    }
    win_UnlockWin(win);
}

void  win_MakeGroupVisible(int16_t win, int16_t group)
{
    win_SetGroupVisibleState(win, group, 1);
}

void  win_MakeGroupInvisible(int16_t win, int16_t group)
{
    win_SetGroupVisibleState(win, group, 0);
}

void  f_22BF_0555(int16_t obj, char  *text)
{
    char  *p;

    p = _fstrrchr(win_ObjAddr(obj) + 0x28, ' ');
    if (p)
        _fstrcpy(p + 1, text);
}

void  win_SetObjFormatStr(int32_t _dos_obj_wide, ...)
{
    int16_t obj = (int16_t)_dos_obj_wide;
    va_list _dos_va_args;
    va_start(_dos_va_args, _dos_obj_wide);
    va_list _dos_va_copy;

    char  *o;
    char buf[100];
    int16_t len;
    char  *  *rec;

    win_LockWin(obj);
    va_copy(_dos_va_copy, _dos_va_args);
    dos_vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, _dos_va_copy);
    va_end(_dos_va_copy);
    WinPrintf("\n= %s", (char  *)buf);
    va_copy(_dos_va_copy, _dos_va_args);
    dos_vsprintf(buf, o + 0x2e, _dos_va_copy);
    va_end(_dos_va_copy);
    len = _fstrlen(buf) + 1;
    if ((rec = *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a)) != 0) {
        if (_fstrlen(*rec) + 1 < len) {
            rec = f_171C_18A6(rec, (int32_t)(len + 4), 1);
            *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a) = rec;
        }
    } else {
        rec = f_171C_13CA((int32_t)(len + 8), 1, "formatStr");
        *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a) = rec;
    }
    _fstrcpy(f_171C_1B84(rec), buf);
    f_171C_1BBA(rec);
    win_UnlockWin(obj);

    va_end(_dos_va_args);
}

void  win_CenterStrAtObj(int16_t obj, char  *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    clip_Push();
    clip_SubInclude(&r);
    f_208F_011F(&r, text);
    clip_Pop();
}

void  win_ObjFormatPrint(int32_t _dos_obj_wide, ...)
{
    int16_t obj = (int16_t)_dos_obj_wide;
    va_list _dos_va_args;
    va_start(_dos_va_args, _dos_obj_wide);
    va_list _dos_va_copy;

    char  *o;
    char buf[100];
    int16_t len;
    char  *  *rec;

    win_LockWin(obj);
    va_copy(_dos_va_copy, _dos_va_args);
    dos_vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, _dos_va_copy);
    va_end(_dos_va_copy);
    WinPrintf("\n= %s", (char  *)buf);
    va_copy(_dos_va_copy, _dos_va_args);
    dos_vsprintf(buf, o + 0x2e, _dos_va_copy);
    va_end(_dos_va_copy);
    len = _fstrlen(buf) + 1;
    if ((rec = *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a)) != 0) {
        if (_fstrlen(*rec) + 2 < len) {
            rec = f_171C_18A6(rec, (int32_t)(len + 4), 1);
            *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a) = rec;
        }
    } else {
        rec = f_171C_13CA((int32_t)(len + 8), 1, "formatStr");
        *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)o, 0x2a) = rec;
    }
    _fstrcpy(f_171C_1B84(rec), buf);
    f_24AB_02AD(o[0x28]);
    win_CenterStrAtObj(obj, buf);
    f_24AB_02AD(0);
    f_171C_1BBA(rec);
    win_UnlockWin(obj);

    va_end(_dos_va_args);
}

int16_t  win_SetPalette(int16_t id)
{
    char  *  *h;
    char  *p;
    char  *q;
    int16_t i;
    char pal[18];

    h = db_LoadObject(id, 0xf);
    if (h == 0)
        return 0;
    p = *h;
    switch (p[1]) {
    case 0:
        if (g_5A97 == 0) {
            q = p + 2;
            for (i = 0; i < 16; q += 3, i++)
                pal[i] = ((((q[0] & 0x10) | ((((q[1] & 0x10) | ((q[2] & 0x10) >> 1)) >> 1) | (q[2] & 0x20))) >> 1 | (q[1] & 0x20)) >> 1) | (q[0] & 0x20);
            pal[17] = 0;
            f_1B4E_01A1(pal, p[0]);
        } else if (g_5A97 == 8) {
            f_1B4E_01AE(p + 2, p[0]);
        }
        break;
    case 1:
        f_1B4E_01A1(p + 2, p[0]);
        break;
    }
    db_ReleaseObject(id, 0xf);
}

void  f_22BF_094F(int16_t obj, int16_t color)
{
    win_ObjAddr(obj)[0x26] = color;
}

void  win_SetObjBitmap(int16_t obj, int16_t bitmap)
{
    char  *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (o[0x21] != 6)
        Punt("Attempt to set bitmap on non-bitmap object");
    *(int16_t  *)(o + 0x28) = bitmap;
    win_UnlockWin(obj);
}

int16_t  win_IsWinOpen(int16_t win)
{
    int16_t dos_open;
    char  *  *h;
    char  *w;

    dos_open = 0;
    if ((h = win_handles[win >> 8]) != 0) {
        if ((w = f_171C_1B84(h)) != 0) {
            dos_open = (*(uint16_t  *)(w + 0x1c) & 0x200) >> 9;
            f_171C_1BBA(h);
        } else {
            win_handles[win >> 8] = 0;
        }
    }
    return dos_open;
}

int16_t  win_IsWinInFront(int16_t win)
{
    if (g_5702[0] == win)
        return 1;
    return 0;
}

int16_t  f_22BF_0A34(int16_t win)
{
    int16_t r;

    win_LockWin(win);
    r = (*(uint16_t  *)(f_2505_0006(win) + 0x1c) & 0x40) >> 6;
    win_UnlockWin(win);
    return r;
}

int16_t  f_22BF_0A65(int16_t win)
{
    int16_t r;

    win_LockWin(win);
    r = (*(uint16_t  *)(f_2505_0006(win) + 0x1c) & 0x80) >> 7;
    win_UnlockWin(win);
    return r;
}

int16_t  f_22BF_0A97(int16_t obj)
{
    int16_t r;

    win_LockWin(obj);
    r = (*(uint16_t  *)(win_ObjAddr(obj) + 0x24) & 2) >> 1;
    win_UnlockWin(obj);
    return r;
}

int16_t  f_22BF_0AC5(int16_t win)
{
    int16_t n;

    win_LockWin(win);
    n = *(int16_t  *)(f_2505_0006(win) + 0xc);
    win_UnlockWin(win);
    return n;
}

int16_t  f_22BF_0AEF(int16_t win)
{
    char  *w;
    int16_t r;

    win_LockWin(win);
    w = f_2505_0006(win);
    r = (*(uint16_t  *)(w + 0x1c) & 0x40) >> 6;
    *(uint16_t  *)(w + 0x1c) |= 0x40;
    win_UnlockWin(win);
    return r;
}

int16_t  f_22BF_0B25(int16_t win)
{
    char  *w;
    int16_t r;

    win_LockWin(win);
    w = f_2505_0006(win);
    r = (*(uint16_t  *)(w + 0x1c) & 0x40) >> 6;
    *(uint16_t  *)(w + 0x1c) &= ~0x40;
    win_UnlockWin(win);
    return r;
}

void  f_22BF_0B5B(struct Rect  *dst, struct Rect  *src, int16_t l, int16_t t, int16_t r, int16_t b)
{
    dst->left = src->left + l;
    dst->right = src->right + r;
    dst->top = src->top + t;
    dst->bottom = src->bottom + b;
}

int16_t win_DoProxMenu(int16_t win, int16_t item, int16_t supplied_count, int16_t p0, int16_t p1) {
    int16_t result;
    int16_t last;
    struct Event ev;

    result = -1;
    win_Open(win, supplied_count, p0, p1, 0, 0);
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
        if ((uint16_t)ev.code < (uint16_t)win || (uint16_t)win + 0x100 <= (uint16_t)ev.code)
            continue;
        if ((uint16_t)win + 2 <= (uint16_t)ev.code)
            result = ev.code - win - 2;
        break;
    }
    win_Close(win);
    return result;
}

void  f_22BF_0C38(int16_t obj)
{
    struct Rect r;
    int16_t c;
    int16_t top;
    int16_t left;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    if (g_5A97 & 1)
        c = win_colors[c][3];
    else
        c = win_colors[c][2];
    c = (c << 8) | (c & 0xff);
    top = SIM_GRAPHICS_SOURCE_g_3DA2;
    if (top < r.top)
        top = r.top;
    if (r.bottom > top && (left = SIM_GRAPHICS_SOURCE_g_3DA0) >= r.left && r.right > left)
        (*g_9134)(left, top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

void  f_22BF_0CDD(int16_t obj)
{
    struct Rect r;
    int16_t c;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    c = win_colors[c][2];
    c = (c & 0xf) | (((c & 0xf) << 4) | (c << 8));
    (*g_9134)(r.left, r.top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

void  win_PrintfAtObj(int16_t obj, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buf[100];

    dos_vsprintf(buf, format, _dos_va_args);
    win_CenterStrAtObj(obj, buf);

    va_end(_dos_va_args);
}

/* The label below is inferred from the relocation order (ZI-2): the original has a
   record break at 0DDD.  More counted line entries before it would explain it too. */
void  win_DrawHBar(int16_t obj, int32_t fraction)
{
    struct Rect r;
    int16_t right;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int16_t end = r.right;
        int32_t extent = (int32_t)(end - r.left);
        right = end;
        r.right = r.left + (int16_t)((extent * fraction) / 65536L);
    }
    if (r.right <= r.left)
        goto rest;
    f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE0);
rest:
    if (r.right < right) {
        r.left = r.right;
        r.right = right;
        f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE2);
    }
}

void  win_DrawVBar(int16_t obj, int32_t fraction)
{
    struct Rect r;
    int16_t top;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int16_t end = r.bottom;
        int16_t start = r.top;
        int16_t height = end - start;
        top = start;
        r.top = end - (int16_t)(((int32_t)height * fraction) / 65536L);
    }
    if (r.top < r.bottom)
        f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE0);
    if (r.top > top) {
        r.bottom = r.top;
        r.top = top;
        f_1CE2_046D(&r, SIM_GRAPHICS_SOURCE_g_3DE2);
    }
}

void  f_22BF_0E83(int16_t src, int16_t dst)
{
    int16_t  *o;
    struct Rect r;

    win_LockWin(src);
    win_LockWin(dst);
    o = (int16_t  *)(win_ObjAddr(dst) + 8);
    r = *(struct Rect  *)(win_ObjAddr(src) + 8);
    o[0] = r.left;
    o[1] = r.top;
    win_Recalc(dst);
    win_UnlockWin(src);
    win_UnlockWin(dst);
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");

#pragma pack(pop)
