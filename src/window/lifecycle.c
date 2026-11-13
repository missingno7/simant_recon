/*
 * Loads window resources and opens or closes windows. It manages window stacking, swapping and
 * draw hook installation.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 20E8; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

#include "flags_ids.h"
#include "windows_ids.h"

#include "rect.h"

void far f_20E8_0000(void);

void (far *g_62E0)(int win) = f_20E8_0000;
void (far *g_62E4)(void) = f_20E8_0000;
void (far *g_62E8)(void) = f_20E8_0000;
void (far *g_62EC)(void) = f_20E8_0000;
void (far *g_62F0)(void) = f_20E8_0000;
void (far *g_62F4)(int win) = f_20E8_0000;
int g_62F8 = 0;
int g_62FA = -1;
int g_62FC = 0;
int g_62FE = 0;
int g_6300 = 0;

void far f_20E8_0000(void)
{
}

extern char far * far * far res_load_with_alloc_type(int object, int kind, int type);
extern void far Punt(char far *format, ...);
extern char far * far * near win_handles[];
extern void _fastcall win_LockWin(int win);
extern void _fastcall RepointObjects(int win);
extern struct Rect far win_offsets[];
extern void _fastcall win_UnlockWin(int win);

void far win_LoadWindow(int win)
{
    char far * far *h;
    char far *obj;
    int i;
    char far *w;

    h = res_load_with_alloc_type((char)(win >> 8), 0, 1);
    if (h == 0)
        Punt("CANNOT LOAD WINDOW %03x", win);
    win_handles[(char)(win >> 8)] = h;
    w = *h;
    win_LockWin(win);
    RepointObjects(win);
    obj = ((char far * far *)(w + 0x2c))[0]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    if (win_offsets[(char)(win >> 8)].left != (int)0x8000)
        *(struct Rect far *)(obj + 8) = win_offsets[(char)(win >> 8)]; /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    else
        win_offsets[(char)(win >> 8)] = *(struct Rect far *)(obj + 8); /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    for (i = 0; i < *(int far *)(w + 0xc); i++) { /* Known Win.count; earlier shared tag changes exact code or original declaration context is unresolved. */
        obj = ((char far * far *)(w + 0x2c))[i]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (i == 0)
            *(struct Rect far *)w = *(struct Rect far *)obj;
        switch (obj[0x21]) { /* Known Obj.type; earlier shared tag changes exact code or original declaration context is unresolved. */
        case 4:
            _fmemset(obj + 0x2a, 0, 14);
            break;
        case 16:
        case 17:
        case 18:
            *(char far * far *)(obj + 0x2a) = 0; /* Known type-dependent Obj payload (formatted-text handle for types 16..18); earlier shared tag changes exact code or original declaration context is unresolved. */
            break;
        }
    }
    win_UnlockWin(win);
}


struct Rect g_635C = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };

extern void far font_InitFonts(void);
extern void far win_LockInit(void);
extern void (far * far win_drawHooks[])(int phase);
extern char near gfx_display_mode;
extern char far * far * far db_LoadObject(int object, int kind);
extern char far * far mem_Lock(char far * far *handle);
extern void far mem_Unlock(char far * far *handle);
extern void far db_PurgeObject(int object, int kind);
#include "pt.h"
extern void far gr_BitMapSize(struct Pt far *size, int id);
extern struct Pt far window_scroll_arrow_size;
extern int far win_numOfWindows;
extern int far win_numOfColors;
extern int far win_numOfGroups;
extern char far win_colors[][6];
extern void far db_UnhookObject(int object, int kind);

int far win_LoadAllWindows(void)
{
    char purge[0x28];
    int i;
    char far * far *h;
    int far *p;
    char far *q;

    font_InitFonts();
    win_LockInit();
    _fmemset(win_drawHooks, 0, 0xb4);
    for (i = 0; i < 45; i++) win_offsets[i] = g_635C;
    h = db_LoadObject(gfx_display_mode, 9);
    if (h) {
        _fmemcpy(win_offsets, mem_Lock(h), 0x140);
        mem_Unlock(h);
        db_PurgeObject(gfx_display_mode, 9);
    }
    gr_BitMapSize(&window_scroll_arrow_size, 0x6f);
    h = db_LoadObject(0x80, 0);
    if (h == 0) {
        Punt("Cannot load resource\nplease try another");
    } else {
        p = (int far *)*h;
        win_numOfWindows = p[0];
        win_numOfColors = p[1];
        win_numOfGroups = p[2];
        db_PurgeObject(0x80, 0);
    }
    h = db_LoadObject(0x81, 0);
    _fmemcpy(win_colors, *h, win_numOfColors * 6);
    db_PurgeObject(0x81, 0);
    h = db_LoadObject(0x83, 0);
    q = *h;
    if (h == 0)
        Punt("Could not load purge list");
    _fmemcpy(purge, q, 0x28);
    db_PurgeObject(0x83, 0);
    for (i = 0; i < win_numOfWindows; i++) {
        if (purge[i] == 0) {
            win_LoadWindow(i << 8);
            db_UnhookObject(i, 0);
        }
    }
    return 1;
}

extern char far * far win_locked_resource_ptr(int win);
extern int clip_window_z_order[];
extern void _fastcall win_deactivate_pointer_regions(int win);
extern void far clip_KillWin(int win);
extern void _fastcall win_Recalc(int win);
extern void far win_raise_and_reclip(int win);
extern void _fastcall win_activate_pointer_regions(int win);
extern void far clip_SetWin(int win);
extern void _fastcall win_DrawWindow(int win);
extern void far clip_Off(void);

void far win_Swap(int from, int to, int unused, int p0, int p1, int p2, int p3)
{
    char far *w;
    struct Rect origin;
    struct Rect rect;
    char far *obj;

    win_LockWin(from);
    w = win_locked_resource_ptr(from);
    origin = *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8); /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    rect = *(struct Rect far *)w;
    if (clip_window_z_order[0] != 0)
        win_deactivate_pointer_regions(clip_window_z_order[0]);
    if (*(int far *)(w + 0x1c) & WIN_FLAG_OPEN) { /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        (*g_62E4)();
        (*g_62F4)(from);
        clip_KillWin(from);
        *(int far *)(w + 0x1c) &= ~WIN_FLAG_OPEN; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        (*g_62E0)(from);
    }
    win_UnlockWin(from);
    win_LockWin(to);
    w = win_locked_resource_ptr(to);
    obj = ((char far * far *)(w + 0x2c))[0]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    *(int far *)(obj + 8) = origin.left; /* Known Obj x/y/width/height layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
    *(int far *)(obj + 0xa) = origin.top; /* Known Obj.y; original shared-tag declaration context remains unresolved. */
    *(struct Rect far *)w = rect;
    *(struct Rect far *)obj = *(struct Rect far *)w;
    ((int far *)(w + 0x10))[0] = p0;
    ((int far *)(w + 0x10))[1] = p1;
    ((int far *)(w + 0x10))[2] = p2;
    ((int far *)(w + 0x10))[3] = p3;
    win_Recalc(to);
    (*g_62E0)(to);
    *(int far *)(win_locked_resource_ptr(to) + 0x1c) |= WIN_FLAG_OPEN; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
    if (clip_window_z_order[0] != (int)0x8000)
        win_deactivate_pointer_regions(clip_window_z_order[0]);
    win_raise_and_reclip(to);
    win_activate_pointer_regions(to);
    clip_SetWin(to);
    win_DrawWindow(to);
    (*g_62E8)();
    win_UnlockWin(to);
    clip_Off();
}

extern void _fastcall win_LockWinHigh(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int near gfx_screen_height_pixels;
extern struct Rect far menu_bar_rect;
extern int near gfx_screen_width_pixels;
extern void far win_FlushEvents(void);

void far win_Open(int win, ...)
{
    char far *w;
    int dx;
    int dy;
    struct Rect r;
    int far *origin;

    if (clip_window_z_order[0] != win) {
        win_LockWinHigh(win);
        (*g_62E4)();
        w = win_locked_resource_ptr(win);
        ((int far *)(w + 0x10))[0] = (&win)[1];
        ((int far *)(w + 0x10))[1] = (&win)[2];
        ((int far *)(w + 0x10))[2] = (&win)[3];
        ((int far *)(w + 0x10))[3] = (&win)[4];
        win_Recalc(win);
        w = win_locked_resource_ptr(win);
        if (*(int far *)(w + 0x1c) & WIN_FLAG_KEEP_ON_SCREEN) { /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            dx = dy = 0;
            win_GetObjRect(win, &r);
            if (r.bottom > gfx_screen_height_pixels)
                dy = gfx_screen_height_pixels - r.bottom;
            else if (r.top <= menu_bar_rect.bottom)
                dy = menu_bar_rect.bottom - r.top;
            if (r.left < 0)
                dx = -r.left;
            else if (r.right >= gfx_screen_width_pixels)
                dx = gfx_screen_width_pixels - r.right;
            origin = (int far *)(((char far * far *)(w + 0x2c))[0] + 8); /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
            win_offsets[win >> 8] = *(struct Rect far *)origin;
            origin[0] += dx;
            origin[1] += dy;
            win_Recalc(win);
        }
        (*g_62E0)(win);
        *(int far *)(win_locked_resource_ptr(win) + 0x1c) |= WIN_FLAG_OPEN; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (clip_window_z_order[0] != (int)0x8000)
            win_deactivate_pointer_regions(clip_window_z_order[0]);
        win_raise_and_reclip(win);
        win_activate_pointer_regions(win);
        clip_SetWin(win);
        win_DrawWindow(win);
        (*g_62E8)();
        clip_Off();
        win_UnlockWin(win);
    }
    win_FlushEvents();
}

extern void _fastcall win_redraw_exposed_windows(struct Rect far *rect);

void _fastcall win_Close(int win)
{
    char far *w;
    struct Rect r;

    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    if (*(int far *)(w + 0x1c) & WIN_FLAG_OPEN) { /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        (*g_62E4)();
        (*g_62F4)(win);
        if (clip_window_z_order[0] == win) {
            win_deactivate_pointer_regions(win);
            clip_KillWin(win);
            if (clip_window_z_order[0] != (int)0x8000)
                win_activate_pointer_regions(clip_window_z_order[0]);
        } else {
            clip_KillWin(win);
        }
        *(int far *)(w + 0x1c) &= ~WIN_FLAG_OPEN; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        if (*(int far *)(w + 0x1c) & WIN_FLAG_KEEP_ON_SCREEN) /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8) = win_offsets[(char)(win >> 8)]; /* Known Win.objs and/or Obj layout overlay; earlier shared tag changes exact code or original declaration context is unresolved. */
        (*g_62E0)(win);
        r = *(struct Rect far *)w;
        win_UnlockWin(win);
        win_redraw_exposed_windows(&r);
        (*g_62E8)();
        clip_Off();
    } else {
        win_UnlockWin(win);
    }
}

extern char far * _fastcall win_WinAddr(int win);

void _fastcall win_ToTop(int win)
{
    int top;
    int flag;

    top = clip_window_z_order[0];
    if (top != win) {
        if (top != (int)0x8000) {
            win_LockWin(top);
            flag = *(int far *)(win_WinAddr(top) + 0x1c) & WIN_FLAG_AUTO_DISMISS; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            win_UnlockWin(top);
            if (flag)
                win_Close(top);
        }
        win_Open(win);
    }
}

extern void far clip_lower_window(int win);
extern void _fastcall win_redraw_rect(struct Rect far *rect);

/*
 * Lower a window, or close an auto-dismiss front window, then update affected drawing.
 */
void _fastcall win_lower_or_dismiss(int win)
{
    int flag;
    char far *w;
    struct Rect r;

    win_LockWin(win);
    win_locked_resource_ptr(win);
    flag = *(int far *)(win_WinAddr(clip_window_z_order[0]) + 0x1c) & WIN_FLAG_AUTO_DISMISS; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
    win_UnlockWin(win);
    (*g_62E4)();
    if (clip_window_z_order[0] == win) {
        if (clip_window_z_order[1] != (int)0x8000) {
            if (flag) {
                win_Close(clip_window_z_order[0]);
                return;
            }
            clip_lower_window(win);
            if (clip_window_z_order[0] != win) {
                win_deactivate_pointer_regions(win);
                win_activate_pointer_regions(clip_window_z_order[0]);
            }
        }
    } else {
        clip_lower_window(win);
    }
    win_LockWin(win);
    w = win_locked_resource_ptr(win);
    *(int far *)(w + 0x1c) |= WIN_FLAG_OPEN; /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
    r = *(struct Rect far *)w;
    win_UnlockWin(win);
    (*g_62E0)(win);
    win_redraw_rect(&r);
    (*g_62E8)();
    clip_Off();
}

void _fastcall win_SetWinDrawHook(int win, void (far *hook)(int))
{
    win_drawHooks[win >> 8] = hook;
}

void _fastcall win_set_state_change_hook(void (far *hook)(int))
{
    g_62E0 = hook;
}

void _fastcall win_set_before_close_hook(void (far *hook)(int))
{
    g_62F4 = hook;
}

/*
 * Install the callback run before window-stack drawing transitions.
 */
void _fastcall win_set_before_update_hook(void (far *hook)(void))
{
    g_62E4 = hook;
}

/*
 * Install the callback run after window-stack drawing transitions.
 */
void _fastcall win_set_after_update_hook(void (far *hook)(void))
{
    g_62E8 = hook;
}

void _fastcall win_set_layout_change_hook(void (far *hook)(void))
{
    g_62EC = hook;
}

void _fastcall f_20E8_08EF(void (far *hook)(void))
{
    g_62F0 = hook;
}


extern int far * _fastcall win_ObjAddr(int);

extern int far win_any_window_open(void);
/*
 * Code generation here depends on declaration numbers (docs/codegen-rules.md, "Declaration
 * numbers that coincide modulo 17"): whether the pointer or the doubled index goes to BX in
 * o[i], mode[i], ref[i], rect[i] and origin[i] follows the order in which those names were
 * declared, counted modulo 17 from the start of the file. The bytes need origin declared before
 * o, and four fewer identifiers before this function than our named prototypes give. The four
 * parameter names left out above (the three hook parameter lists and win_ObjAddr) stand for that
 * count; which original declarations made it up is unknown.
 */
/*
 * Set absolute object bounds by recomputing its layout offsets, including self-references.
 */
void _fastcall win_set_obj_absolute_rect(int obj, int far *rect)
{
    int j;
    int win;
    int far *origin;
    int far *o;
    int far *mode;
    int far *ref;
    int i;

    win = obj & WIN_ID_MASK;
    win_LockWin(win);
    o = win_ObjAddr(obj);
    origin = o + 4;
    mode = o + 12;
    ref = o + 8;
    for (j = 0; j < 4; j++)
        origin[j] = 0;
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = 0;
        else
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    win_UnlockWin(win);
}




#include "win.h"

void far win_close_auto_dismiss(void)
{
    int top;

    top = clip_window_z_order[0];
    if (win_any_window_open()) {
        win_LockWin(top);
        if (((struct Win far *)win_WinAddr(top))->flags & 1)
            win_Close(top);
        win_UnlockWin(top);
    }
}
