/*
 * Fetches and dispatches window events. It handles proximity events, queues and event flushing.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 218D; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

#include "events_ids.h"
#include "flags_ids.h"
#include "windows_ids.h"

#include "event.h"

long g_6364 = -1;
int lastProxObj = -1;
static char g_8CEC;

extern void _fastcall win_LockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall list_process_click(struct Event far *ev);
extern void _fastcall win_ProcSliderEvent(struct Event far *ev);
extern char far * _fastcall win_WinAddr(int win);
extern void _fastcall win_track_move(struct Event far *ev);
extern void far clip_Push(void);
extern void far clip_set_screen_region(void);
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern void far timer_wait_countdown(int ticks);
extern void far clip_Pop(void);
extern struct Event far window_current_event;
extern struct Event far window_previous_event;
extern long far TickCount(void);
extern void _fastcall win_UnlockWin(int win);

/*
 * Dispatch an object event, update selection feedback, and classify repeated clicks.
 */
void _fastcall win_dispatch_object_event(struct Event far *ev)
{
    char far *obj;

    win_LockWin(ev->code);
    obj = win_ObjAddr(ev->code);
    switch (obj[0x21]) { /* Known Obj.type; earlier shared tag changes exact code or original declaration context is unresolved. */
    case 4:
        list_process_click(ev);
        goto check;
    case 7:
    case 8:
        win_ProcSliderEvent(ev);
        goto check;
    case 12:
    case 18:
        if (*(int far *)(win_WinAddr(ev->code) + 0x1c) & WIN_FLAG_TITLE_DRAG) /* Known Win.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            win_track_move(ev);
        break;
    }
    if (*(int far *)(obj + 0x24) & OBJ_FLAG_CLICK_FEEDBACK) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        clip_Push();
        clip_set_screen_region();
        if (*(int far *)(obj + 0x24) & OBJ_FLAG_TOGGLE_SELECT) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            if (!(*(int far *)(obj + 0x24) & OBJ_FLAG_EXCLUSIVE_GROUP) || !(*(int far *)(obj + 0x24) & OBJ_FLAG_STICKY_SELECTION) || !(*(int far *)(obj + 0x24) & OBJ_FLAG_SELECTED)) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
                win_SetObjSelectedState(ev->code, !(*(int far *)(obj + 0x24) & OBJ_FLAG_SELECTED)); /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        } else if (*(int far *)(obj + 0x24) & OBJ_FLAG_VISIBLE) { /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            win_SetObjSelectedState(ev->code, !(*(int far *)(obj + 0x24) & OBJ_FLAG_SELECTED)); /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            timer_wait_countdown(5);
            win_SetObjSelectedState(ev->code, !(*(int far *)(obj + 0x24) & OBJ_FLAG_SELECTED)); /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
        }
        clip_Pop();
    }
check:
    if (window_previous_event.code == window_current_event.code && TickCount() - 10 < g_6364) {
        if (((window_previous_event.modifiers ^ window_current_event.modifiers) & EVENT_MOD_CLICK_MASK) == 0) {
            window_current_event.modifiers &= ~EVENT_MOD_CLICK_MASK;
            if (window_previous_event.modifiers & 0x0800)
                window_current_event.modifiers |= 0x4000;
            if (window_previous_event.modifiers & 0x0200)
                window_current_event.modifiers |= 0x2000;
            g_6364 = -1;
            goto done;
        }
    }
    g_6364 = TickCount();
    window_previous_event = window_current_event;
done:
    win_UnlockWin(ev->code);
}

/*
 * Clear the remembered proximity object.
 */
void far win_reset_proximity_object(void)
{
    lastProxObj = -1;
}

int far win_GetProxEvent(void)
{
    return lastProxObj;
}

extern void far clip_restrict_rect(char far *p);
extern char gfx_screen_clip_list[];
extern void _fastcall win_ObjInv(int obj);

void _fastcall _win_SetProxItem(int obj)
{
    clip_Push();
    clip_restrict_rect(gfx_screen_clip_list);
    if (lastProxObj != -1)
        win_ObjInv(lastProxObj);
    if (obj != -1)
        win_ObjInv(obj);
    lastProxObj = obj;
    clip_Pop();
}

extern int clip_window_z_order[];
extern int far hotbox_pointer_hit_id(void);

/*
 * Update front-window proximity highlighting from a pointer-region event.
 */
void _fastcall win_update_proximity_event(struct Event far *ev)
{
    int obj;

    if ((char)(clip_window_z_order[0] >> 8) == (unsigned char)ev->code) {
        win_LockWin(clip_window_z_order[0]);
        obj = hotbox_pointer_hit_id();
        if (obj != 0 && (obj & WIN_ID_MASK) == clip_window_z_order[0] && lastProxObj != obj &&
            (*(int far *)(win_ObjAddr(obj) + 0x24) & OBJ_FLAG_PROXIMITY)) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            _win_SetProxItem(obj);
        else if (lastProxObj != -1 && !(*(int far *)(win_ObjAddr(lastProxObj) + 0x24) & OBJ_FLAG_STICKY_SELECTION) && obj != lastProxObj) /* Known Obj.flags; earlier shared tag changes exact code or original declaration context is unresolved. */
            _win_SetProxItem(-1);
        win_UnlockWin(clip_window_z_order[0]);
    }
}

extern void far f_1B28_0069(void);
extern void far snd_service_pending(void);
extern int far input_event_count(void);
extern void far input_pop_event(struct Event far *ev);
void _fastcall win_dispatch_desktop_click(struct Event far *ev);
extern void _fastcall win_lower_or_dismiss(int win);
void far win_FlushEvents(void);
extern void _fastcall win_Close(int win);
extern void _fastcall win_track_resize(struct Event far *ev);
extern void _fastcall win_toggle_zoom(int win);
void _fastcall win_step_object_focus(int dir);

void far win_translate_pending_event(void)
{
    f_1B28_0069();
    snd_service_pending();
    if (g_8CEC != 0 || !input_event_count())
        return;
    input_pop_event(&window_current_event);
    if (window_current_event.code == (int)EVENT_DESKTOP_CLICK) {
        win_dispatch_desktop_click(&window_current_event);
    } else if ((char)(window_current_event.code >> 8) == (char)0xfb) {
        win_update_proximity_event(&window_current_event);
    } else {
        if (clip_window_z_order[0] != (int)0x8000) {
            switch (window_current_event.code) {
            case EVENT_WINDOW_MOVE:
                win_track_move(0L);
                break;
            case EVENT_WINDOW_LOWER:
                win_lower_or_dismiss(clip_window_z_order[0]);
                win_FlushEvents();
                return;
            case EVENT_WINDOW_CLOSE:
                win_Close(clip_window_z_order[0]);
                win_FlushEvents();
                return;
            case EVENT_WINDOW_RESIZE:
                win_track_resize(0L);
                return;
            case EVENT_WINDOW_ZOOM:
                win_toggle_zoom(clip_window_z_order[0]);
                win_FlushEvents();
                return;
            case EVENT_FOCUS_NEXT:
                if (clip_window_z_order[0] != (int)0x8000)
                    win_step_object_focus(1);
                break;
            case EVENT_FOCUS_PREVIOUS:
                if (clip_window_z_order[0] != (int)0x8000)
                    win_step_object_focus(-1);
                break;
            default:
                if (!(window_current_event.code & 0x8000)) {
                    if ((window_current_event.code & WIN_ID_MASK) != clip_window_z_order[0])
                        return;
                    win_dispatch_object_event(&window_current_event);
                }
                break;
            }
        }
    }
    g_8CEC = 1;
}

int far win_Events(void)
{
    win_translate_pending_event();
    return g_8CEC;
}

int _fastcall win_GetEvent(struct Event far *ev)
{
    win_translate_pending_event();
    if (g_8CEC) {
        g_8CEC = 0;
        *ev = window_current_event;
        win_translate_pending_event();
        return 1;
    }
    return 0;
}

void far win_FlushEvents(void)
{
    struct Event ev;

    while (input_event_count())
        input_pop_event(&ev);
    g_8CEC = 0;
}

#include "rect.h"
#include "obj.h"
#include "win.h"

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far PointInRect(int far *pt, struct Rect far *rect);
extern void _fastcall win_ToTop(int win);

/*
 * Handle a desktop click by dismissing or raising windows according to their flags.
 */
void _fastcall win_dispatch_desktop_click(struct Event far *ev)
{
    int top;
    int noClose;
    struct Rect r;
    int i;

    top = clip_window_z_order[0];
    if (top == (int)0x8000)
        return;
    win_GetObjRect(top, &r);
    win_LockWin(top);
    noClose = (*(unsigned far *)&((struct Win far *)win_WinAddr(top))->flags & 0x40) >> 6;
    if (!PointInRect(&ev->h, &r) && (((struct Win far *)win_WinAddr(top))->flags & 1))
        win_Close(top);
    win_UnlockWin(top);
    if (noClose == 0) {
        for (i = 0; clip_window_z_order[i] != (int)0x8000; i++) {
            win_GetObjRect(clip_window_z_order[i], &r);
            if (PointInRect(&ev->h, &r)) {
                win_ToTop(clip_window_z_order[i]);
                break;
            }
        }
    }
}

#include "pt.h"

extern char far * far win_locked_resource_ptr(int win);
extern void far GetMousePos(struct Pt far *pt);
extern void far hotbox_center_pointer(int obj);

/*
 * Return the selectable object under the pointer, or move to a nearest candidate and return
 * -1.
 */
int far win_focus_nearest_object(void)
{
    unsigned long d;
    unsigned long best;
    int top;
    int found;
    char far *obj;
    char far *w;
    struct Pt pt;
    int i;
    int dx;
    int dy;

    found = -1;
    top = clip_window_z_order[0];
    best = 0xffffffffL;
    win_LockWin(top);
    w = win_locked_resource_ptr(top);
    GetMousePos(&pt);
    for (i = 1; i < ((struct Win far *)w)->count; i++) {
        obj = ((struct Win far *)w)->objs[i];
        if (*(int far *)&((struct Obj far *)obj)->flags & 2) {
            if (PointInRect((int far *)&pt, (struct Rect far *)obj)) {
                win_UnlockWin(top);
                return top + i;
            }
            dy = pt.y - (((struct Rect far *)obj)->top + ((struct Rect far *)obj)->top) / 2;
            dx = pt.x - (((struct Rect far *)obj)->right + ((struct Rect far *)obj)->left) / 2;
            d = (long)dy * dy + (long)dx * dx;
            if (d < best) {
                best = d;
                found = top + i;
            }
        }
    }
    if (found != -1)
        hotbox_center_pointer(found);
    win_UnlockWin(top);
    return -1;
}

extern int _fastcall win_object_count(int win);
extern int _fastcall win_is_obj_selectable(int obj);

/*
 * Move pointer focus through selectable objects in the front window, wrapping by direction.
 */
void _fastcall win_step_object_focus(int dir)
{
    int start;
    int last;
    int cur;

    if (clip_window_z_order[0] == (int)0x8000)
        return;
    cur = start = win_focus_nearest_object();
    last = clip_window_z_order[0] + win_object_count(clip_window_z_order[0]);
    if (start == -1)
        return;
    do {
        cur += dir;
        if (clip_window_z_order[0] + 1 > cur)
            cur = last - 1;
        else if (last <= cur)
            cur = clip_window_z_order[0] + 1;
        if (win_is_obj_selectable(cur)) {
            hotbox_center_pointer(cur);
            return;
        }
    } while (start != cur);
}
