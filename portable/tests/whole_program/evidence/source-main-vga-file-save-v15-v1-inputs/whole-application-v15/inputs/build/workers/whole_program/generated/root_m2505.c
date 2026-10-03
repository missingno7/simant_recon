#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#pragma pack(push, 2)
extern int32_t  f_171C_1C1C(char  *  *handle);
extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 2505: DOS window-object engine (partial). */

extern void  Punt(char  *format, ...);
extern int16_t  WinPrintf(char  *format, ...);

extern int16_t  win_IsWinLocked(int16_t win);
extern void  win_LockWin(int16_t win);
extern void  win_UnlockWin(int16_t win);

struct Rect { int16_t left; int16_t top; int16_t right; int16_t bottom; };

struct Pt {
    int16_t x;
    int16_t y;
};

struct Win {
    struct Rect rect;
    char pad08[4];
    int16_t count;
    char pad0E[0x1c - 0x0e];
    int16_t flags;
    char pad1E[0x2c - 0x1e];
    uint8_t object_table_wire[4];
};

extern struct Pt  win_StringSize(char  *text);
extern void  f_208F_0419(struct Pt  *size, int16_t id);

extern int16_t g_6300;
extern int16_t g_5702;


char  *  f_2505_0006(int16_t win)
{
    if (g_6300 == 0 && !win_IsWinLocked(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO GETWINPTR!!", win);
    return *win_handles[win >> 8];
}

void  RepointObjects(int16_t win)
{
    char  *w;
    int16_t n;
    int16_t i;
    char  *p;

        int16_t window_index;

    window_index = (int16_t)((uint16_t)win >> 8);
    if (window_index >= 45) {
        Punt("window sidecar index out of range");
        return;
    }
w = f_2505_0006(win);
    if (sim_window_ref_registry_repoint_handle_signed(&sim_window_ref_registry, (uint16_t)window_index, win_handles[window_index],
            (int64_t)f_171C_1C1C(win_handles[window_index])) !=
        SIM_WINDOW_REFS_OK) {
        Punt("window object sidecar bind failed");
        return;
    }

    n = sim_window_wire_read_i16(w, 0x0c);
    p = w + n * 4 + 0x2c;
    for (i = 0; i < n; i++) {
        sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i] = p;
        p += sim_window_wire_read_i16(p, 0x22);
    }
}

int16_t  f_2505_00AA(int16_t type)
{
    switch (type) {
    case 5:
    case 9:
    case 12:
    case 16:
    case 17:
    case 18:
        return 1;
    }
    return 0;
}

int16_t  f_2505_00DD(char  *obj)
{
    int16_t size;

    size = 0x28;
    switch (obj[0x21]) {
    case 0:
    case 2:
    case 15:
    case 19:
    case 20:
    case 21:
    case 22:
        size = 0x29;
        break;
    case 4:
        size = 0x38;
        break;
    case 5:
    case 9:
    case 12:
        size = _fstrlen(obj + 0x2a) + 0x2d;
        break;
    case 6:
    case 7:
    case 8:
        size = 0x2a;
        break;
    case 13:
        size = 0x2c;
        break;
    case 16:
    case 17:
    case 18:
        size = _fstrlen(obj + 0x2e) + 0x31;
        break;
    }
    return size;
}

struct Pt  win_AutoSize(char  *obj)
{
    static struct Pt size;

    switch (obj[0x21]) {
    default:
        size.x = *(int16_t  *)(obj + 4) - *(int16_t  *)obj;
        size.y = *(int16_t  *)(obj + 6) - *(int16_t  *)(obj + 2);
        break;
    case 5:
    case 12:
        size = win_StringSize(obj + 0x28);
        size.x += 8;
        size.y += 8;
        break;
    case 6:
    case 13:
        f_208F_0419(&size, *(int16_t  *)(obj + 0x28));
        break;
    case 9:
        size = win_StringSize(obj + 0x28);
        break;
    case 16:
    case 18:
        size = win_StringSize(obj + 0x2c);
        break;
    case 17:
        size = win_StringSize(obj + 0x2c);
        size.x += 8;
        size.y += 8;
        break;
    }
    return size;
}

char  *  win_WinRectAddr(int16_t win)
{
    if (!win_IsWinLocked(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinRectAddr!!", win);
    return f_2505_0006(win);
}

void  win_GetObjRect(int16_t obj, struct Rect  *rect)
{
    char  *w;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    *rect = *((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[obj & 0xff]);
    win_UnlockWin(obj);
}

char  *  win_ObjAddr(int16_t obj)
{
    if (!win_IsWinLocked(obj))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_ObjAddr!!", obj);
    if (*(int16_t  *)(f_2505_0006(obj) + 0xc) <= (uint8_t)obj)
        Punt("Attempt to get obj address outsize window");
    return ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)f_2505_0006(obj))[obj & 0xff]);
}

char  *  f_2505_033C(int16_t win, int16_t obj)
{
    return win_ObjAddr((win & 0xff00) + obj);
}

char  *  win_WinAddr(int16_t win)
{
    if (!win_IsWinLocked(win))
        WinPrintf("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinAddr!!", win);
    return f_2505_0006(win);
}

int16_t  f_2505_036E(void)
{
    if (g_5702 != (int16_t)0x8000)
        return 1;
    return 0;
}

void  f_2505_0382(struct Pt  *center, struct Rect  *rect)
{
    center->x = (rect->right + rect->left) / 2;
    center->y = (rect->top + rect->bottom) / 2;
}

extern void  f_1F58_0090(void);
int16_t  f_2505_0453(int16_t obj, int16_t kind);
int16_t  f_2505_04D7(int16_t win, int16_t idx);

int16_t  f_2505_03B9(int16_t axis, int16_t win, char  *obj)
{
    int16_t v;
    int16_t kind;

    switch (((int16_t  *)(obj + 0x18))[axis]) {
    default:
        f_1F58_0090();
        return 1;
    case 0:
        v = 0;
        break;
    case 1:
        kind = 0;
        goto get;
    case 2:
        kind = 1;
        goto get;
    case 3:
        kind = 2;
        goto get;
    case 4:
        kind = 3;
    get:
        v = f_2505_0453(((int16_t  *)(obj + 0x10))[axis], kind);
        break;
    case 5:
        v = f_2505_04D7(win, ((int16_t  *)(obj + 0x10))[axis]);
        break;
    }
    if (v != (int16_t)0x8000)
        return v + ((int16_t  *)(obj + 8))[axis];
    return 0x8000;
}



int16_t  f_2505_0453(int16_t obj, int16_t kind)
{
    int16_t win;
    int16_t idx;
    char  *w;
    int16_t  *r;

    win = obj & 0xff00;
    if ((win >> 8) < win_numOfWindows || win >= 0x2800) {
        win_LockWin(win);
        idx = obj & 0xff;
        w = f_2505_0006(win);
        if (sim_window_wire_read_i16(w, 0x0c) > idx) {
            r = ((int16_t *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[idx]);
            win_UnlockWin(win);
            return r[kind];
        }
        win_UnlockWin(win);
    }
    return 0x8000;
}

int16_t  f_2505_04D7(int16_t win, int16_t idx)
{
    if (win_numOfWindows <= (win >> 8) && win < 0x2800)
        return 0x8000;
    return ((int16_t  *)(f_2505_0006(win) + 0x10))[idx];
}

void  f_2505_0511(struct Rect  *r)
{
    int16_t t;

    t = r->left;
    if (t > r->right) {
        r->left = r->right;
        r->right = t;
    }
    t = r->top;
    if (t > r->bottom) {
        r->top = r->bottom;
        r->bottom = t;
    }
}

void  win_Recalc(int16_t win);
void  f_2505_06B9(int16_t flag, char  *w);
void  f_2505_0831(int16_t win);
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);

void  win_Recalc(int16_t win)
{
    char  *  *handle;
    char  *w;
    int16_t n;
    int16_t i;
    int16_t changed;
    int16_t unresolved;
    char  *obj;
    struct Pt size;
    int16_t  *p;
    int16_t k;
    int16_t v;
    struct Rect  *r;

    handle = (char  *  *)win_handles[win >> 8];
    w = f_171C_1B84(handle);
    n = sim_window_wire_read_i16(w, 0x0c);
    for (i = 0; i < n; i++) {
        r = ((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        r->left = r->right = r->top = r->bottom = 0x8000;
    }
    changed = 1;
    while (changed) {
        unresolved = 0;
        changed = 0;
        for (i = 0; i < n; i++) {
            obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
            if (obj[0x24] & 0x40) {
                size = win_AutoSize(obj);
                ((int16_t  *)obj)[6] = size.x;
                ((int16_t  *)obj)[7] = size.y;
            }
            p = (int16_t  *)obj;
            for (k = 0; k < 4; k++, p++) {
                v = f_2505_03B9(k, win, obj);
                if (*p != v) {
                    *p = v;
                    changed++;
                }
                if (v == (int16_t)0x8000)
                    unresolved++;
            }
        }
    }
    for (i = 0; i < n; i++)
        f_2505_0511(((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]));
    *(struct Rect  *)w = *((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]);
    f_171C_1BBA(handle);
}

extern void  f_1FD2_0883(int16_t x, int16_t y, int16_t id, int16_t mode, int16_t flag);

void  f_2505_06B9(int16_t flag, char  *w)
{
    int16_t m;
    struct Pt size;
    struct Rect rect;

    rect = *(struct Rect  *)w;
    m = sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0][0x28];
    rect.left += m;
    rect.right -= m;
    rect.top += m;
    rect.bottom -= m;
    if (*(int16_t  *)(w + 0x1c) & 4) {
        f_1FD2_0883(rect.left, rect.top, 0x64, 0xf083, flag);
        f_208F_0419(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int16_t  *)(w + 0x1c) & 8) {
        f_208F_0419(&size, 0x70);
        f_1FD2_0883(rect.right - size.x, rect.bottom - size.y, 0x70, 0xf084, flag);
    }
    if (*(int16_t  *)(w + 0x1c) & 0x100) {
        if (*(int16_t  *)(w + 0x1c) & 0x80) {
            f_208F_0419(&size, 0x66);
            f_1FD2_0883(rect.right -= size.x, rect.top, 0x66, 0xf085, flag);
        } else {
            f_208F_0419(&size, 0x67);
            f_1FD2_0883(rect.right -= size.x, rect.top, 0x67, 0xf085, flag);
        }
    }
    if (*(int16_t  *)(w + 0x1c) & 0x10)
        f_1FD2_0883(rect.left, rect.top, 0x65, 0xf088, flag);
    if (*(int16_t  *)(w + 0x1c) & 0x400) {
        f_208F_0419(&size, 0x69);
        f_1FD2_0883(rect.right -= size.x, rect.top, 0x69, 0xf082, flag);
    }
}

extern void  f_1FD2_03EB(char  *obj, int16_t objNum);
extern void  f_1FD2_044F(char  *w, int16_t id);
extern void  f_218D_01EB(void);

void  f_2505_0831(int16_t win)
{
    struct Win  *w;
    char  *obj;
    int16_t dirty;
    int16_t n;
    int16_t i;

    win &= 0xff00;
    win_LockWin(win);
    w = (struct Win  *)f_2505_0006(win);
    n = w->count;
    dirty = 0;
    for (i = 0; i < n; i++) {
        obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (obj[0x24] & 2)
            f_1FD2_03EB(obj, win + i);
        if (obj[0x24] & 0x10)
            dirty = 1;
    }
    f_2505_06B9(1, (char  *)w);
    if (dirty)
        f_1FD2_044F((char  *)w, (win >> 8) - 0x500);
    f_218D_01EB();
    win_UnlockWin(win);
}

extern void  f_1FD2_0438(int16_t objNum);
extern void  f_1FD2_049C(int16_t id);

void  f_2505_08EA(int16_t win)
{
    struct Win  *w;
    char  *obj;
    int16_t dirty;
    int16_t n;
    int16_t i;

    win &= 0xff00;
    win_LockWin(win);
    w = (struct Win  *)f_2505_0006(win);
    n = w->count;
    for (i = 0; i < n; i++) {
        obj = ((char *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
        if (obj[0x24] & 2)
            f_1FD2_0438(win + i);
        if (obj[0x24] & 0x10)
            dirty = 1;
    }
    f_2505_06B9(0, (char  *)w);
    if (dirty)
        f_1FD2_049C((win >> 8) - 0x500);
    win_UnlockWin(win);
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");
_Static_assert(offsetof(struct Win, count) == 0x0c, "Win count offset");
_Static_assert(offsetof(struct Win, flags) == 0x1c, "Win flags offset");
_Static_assert(offsetof(struct Win, object_table_wire) == 0x2c, "Win table offset");
_Static_assert(sizeof(struct Win) == 0x30, "Win fixed header width");

#pragma pack(pop)
