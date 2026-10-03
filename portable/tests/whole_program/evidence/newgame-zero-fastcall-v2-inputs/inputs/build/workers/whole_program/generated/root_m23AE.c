#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#pragma pack(push, 2)
extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 23AE: window lock/unlock layer. */

extern void  Punt(char  *format, ...);

static int16_t g_644C = 0;
static int16_t g_644E = 0;
static uint8_t g_8DA6[45];
static char  *g_8CF2[45];

void  win_NoWindowsShouldBeLocked(void)
{
    int16_t i;

    for (i = 0; i < 45; i++)
        if (g_8DA6[i])
            Punt("Window %d locked when it should not be!");
}

void  win_LockInit(void)
{
    _fmemset(g_8CF2, 0, sizeof g_8CF2);
    _fmemset(g_8DA6, 0, sizeof g_8DA6);
    g_644C = 1;
}

int16_t  win_IsWinLocked(int16_t win)
{
    if (g_644C == 0)
        return 1;
    return g_8DA6[win >> 8];
}


extern void  win_LoadWindow(int16_t win);
extern int16_t  f_171C_1AD4(char  *  *handle);
void  f_23AE_035D(void);
extern char  *  f_171C_1D40(char  *  *handle);
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1C0A(char  *  *handle);
extern void  f_171C_1E86(char  *  *handle, int16_t flag);
extern void  RepointObjects(int16_t win);
extern void  win_Recalc(int16_t win);

void  f_23AE_0069(int16_t win, int16_t high)
{
    int16_t loaded = 0;
    int16_t n;
    char  *  *h;
    char  *w;

    g_644E++;
    if (g_644C == 0)
        return;
    n = (char)(win >> 8);
    if (n > 40 || n < 0)
        Punt("Illegal win num %x at lock", n);
    if (win_handles[n] == 0) {
        win_LoadWindow(win);
        loaded = 1;
    }
    h = win_handles[n];
    if (g_8DA6[n] == 0) {
        g_8DA6[n]++;
        if (f_171C_1AD4(h)) {
            high = 0;
            f_23AE_035D();
        }
        if (high)
            w = f_171C_1D40(h);
        else
            w = f_171C_1B84(h);
        if (w == 0) {
            f_171C_1C0A(h);
            win_LoadWindow(win);
            h = win_handles[n];
            if (high)
                w = f_171C_1D40(h);
            else
                w = f_171C_1B84(h);
        }
        if (*(int16_t  *)(w + 0x1c) & 0x800)
            f_171C_1E86(h, 1);
        if (g_8CF2[n] != w) {
            g_8CF2[n] = w;
            RepointObjects(win);
        }
        if (loaded)
            win_Recalc(win);
    } else if (g_8DA6[n]++ > 10) {
        Punt("win_Lock > 10 levels deep!!");
    }
    g_644E--;
}



/* SCAFFOLD BEGIN: win_UnlockWin best draft (original position: after f_23AE_0069).
   Residue: the object pointer ((struct Obj *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]) is kept in es:bx and p computed as dx:ax
   (mov ax,bx; mov dx,es; add ax,34h); the original copies it to DI and uses
   lea bx,[di+34h]/[di+2Ah]; frame 20h vs 1Ch. */
struct Obj {
    char pad[0x21];
    char type;
    char pad22[0x2a - 0x22];
    uint8_t h2a_wire[4];
    char pad2e[0x34 - 0x2e];
    uint8_t h34_wire[4];
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

extern int16_t  f_171C_1686(struct Win  *  *handle);
extern void  f_171C_13E4(char  *  *handle);
extern void  f_171C_2086(struct Win  *  *handle);
extern void  f_171C_20E2(struct Win  *  *handle);
extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];

void  win_UnlockWin(int16_t win)
{
    char  *  *  *p;
    int16_t n;
    struct Win  *  *h;
    int16_t i;
    struct Obj  *obj;
    struct Win  *w;

    if (g_644C) {
        n = win >> 8;
        h = (struct Win  *  *)win_handles[n];
        if (g_8DA6[n] == 0)
            Punt("Attemp to unlock when not locked!!");
        if (f_171C_1686(h) == 5)
            Punt("Attemp to unlock when discarded win %x", win);
        if (--g_8DA6[n] == 0) {
            if (!((*h)->flags & 0x200) && ((*h)->flags & 0x800) && g_644E == 0) {
                w = *h;
                for (i = 0; i < w->count; i++) {
                    obj = ((struct Obj *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]);
                    switch (obj->type) {
                    case 4:
                    case 10:
                        p = sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)obj, 0x34);
                        break;
                    case 16:
                    case 17:
                    case 18:
                        p = sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)obj, 0x2a);
                        break;
                    default:
                        continue;
                    }
                    if (p == NULL)
                        { Punt("unresolved serialized window Handle"); return; }
                    if (*p) {
                        f_171C_13E4(*p);
                        *p = 0;
                    }
                }
                f_171C_2086(h);
                f_171C_20E2(h);
                win_handles[n] = 0;
                g_8CF2[n] = 0;
                win_offsets[n] = *(struct Rect  *)((char  *)((struct Obj *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]) + 8);
                sim_window_ref_registry_detach(&sim_window_ref_registry, (uint16_t)n);
            } else {
                f_171C_2086(h);
            }
        }
    }
}
/* SCAFFOLD END */

extern int16_t  WinPrintf(char  *format, ...);
extern void  f_24FA_00B5(void);

void  f_23AE_035D(void)
{
    WinPrintf("WINLOCKERR!! ALREADY LOCKED!!");
    f_24FA_00B5();
}

void  win_LockWinHigh(int16_t win)
{
    f_23AE_0069(win, 1);
}

void  win_LockWin(int16_t win)
{
    f_23AE_0069(win, 0);
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");
_Static_assert(offsetof(struct Win, count) == 0x0c, "Win count offset");
_Static_assert(offsetof(struct Win, flags) == 0x1c, "Win flags offset");
_Static_assert(offsetof(struct Win, object_table_wire) == 0x2c, "Win table offset");
_Static_assert(sizeof(struct Win) == 0x30, "Win fixed header width");
_Static_assert(offsetof(struct Obj, type) == 0x21, "Obj type offset");
_Static_assert(offsetof(struct Obj, h2a_wire) == 0x2a, "Obj h2a offset");
_Static_assert(offsetof(struct Obj, h34_wire) == 0x34, "Obj h34 offset");
_Static_assert(sizeof(struct Obj) == 0x38, "Obj fixed width");

#pragma pack(pop)
