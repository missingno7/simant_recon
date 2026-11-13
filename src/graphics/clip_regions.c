/*
 * Maintains window clip regions and their rectangle lists. It implements include, exclude and
 * push or pop operations on the clip stack.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1E57; complete original translation unit.
 * Statement layout is inferred from relocation order; original formatting is unknown.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

typedef char far * far *Handle;

#include "rect.h"

/*
 * Window ids in front-to-back clipping order, terminated by 0x8000.
 */
int clip_window_z_order[32] = { (int)0x8000 };
Handle g_5742 = 0;
Handle g_5746 = 0;
/*
 * Handle for regions outside windows, or the screen-list sentinel handle.
 */
Handle clip_outside_windows_handle = 0;
extern struct Rect far gfx_screen_clip_list;
/*
 * Pointer to screen bounds used as a synthetic whole-screen clip handle.
 */
char far *clip_screen_list_pointer = (char far *)&gfx_screen_clip_list;
int g_5752[2] = { 0 };
/*
 * Saved clipping-stack depth; push checks a limit of twenty.
 */
int clip_saved_state_depth = 0;
/*
 * Accumulated count of rectangles copied by clip_Push, including terminators.
 */
int clip_saved_rectangle_total = 0;
int g_575A[12] = { 0 };

void far f_1E57_0006(int n, int kind)
{
}

void far f_1E57_0007(void)
{
}

/* A third empty function; no reference to it was found.  The parameter list is a
 * hypothesis. */
void far f_1E57_0008(void)
{
}

extern void far mem_Free(Handle h);
extern struct Rect far * near clip_active_list_offset;

void far clip_reset_temporary_state(void)
{
    if (g_5742) {
        mem_Free(g_5742);
        g_5742 = 0;
    }
    if (g_5746)
        g_5746 = 0;
    clip_active_list_offset = 0;
}

void far win_raise_and_reclip(int win);

/*
 * Raise the window and rebuild its visibility clips.
 */
void far clip_raise_window(int win)
{
    win_raise_and_reclip(win);
}

void far win_rebuild_visible_clips(void);

/*
 * Move the window to the bottom of the stacking list and rebuild visibility clips.
 */
void far clip_lower_window(int win)
{
    int i;
    int j;

    win &= 0xff00;
    for (i = j = 0; j < 31; i++, j++) {
        if (clip_window_z_order[i] == (int)0x8000)
            break;
        if (clip_window_z_order[j] == win)
            i++;
        clip_window_z_order[j] = clip_window_z_order[i];
    }
    clip_window_z_order[j] = win;
    clip_window_z_order[j + 1] = 0x8000;
    win_rebuild_visible_clips();
}

extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);

void far win_raise_and_reclip(int win)
{
    int buf[32];
    int i;
    int j;

    buf[0] = win &= 0xff00;
    for (i = 0, j = 1; j < 31; i++, j++) {
        if (clip_window_z_order[i] == (int)0x8000)
            break;
        buf[j] = clip_window_z_order[i];
        if (clip_window_z_order[i] == win)
            j--;
    }
    buf[j] = 0x8000;
    _fmemcpy(clip_window_z_order, buf, sizeof(buf));
    win_rebuild_visible_clips();
}

extern int far WinPrintf(char far *format, ...);

void far clip_KillWin(int win)
{
    int i;
    int j;

    win &= 0xff00;
    for (j = i = 0; i < 31; j++, i++) {
        if (clip_window_z_order[i] == (int)0x8000)
            break;
        if (clip_window_z_order[i] == win)
            j++;
        clip_window_z_order[i] = clip_window_z_order[j];
    }
    if (i >= 31)
        WinPrintf("\nWARNING: i>=MAXWINDOWS-1 in KillWin(%d)", win);
    win_rebuild_visible_clips();
}

extern int _fastcall win_IsWinOpen(int win);
extern Handle far clip_window_list_handles[45];
extern void far Punt(char far *format, ...);
extern char far * far mem_Lock(Handle h);
extern struct Rect far clip_rectangle_workspace[];
extern Handle far mem_Unlock(Handle h);

void far clip_SetWin(int win)
{
    struct Rect far *p;
    int size;

    clip_reset_temporary_state();
    win &= 0xff00;
    if (win_IsWinOpen(win)) {
        g_5746 = clip_window_list_handles[win >> 8];
        if (!g_5746)
            Punt("SetWin: Window open but clip is NULL");
        p = (struct Rect far *)mem_Lock(g_5746);
        clip_active_list_offset = p;
        for (size = 8; clip_active_list_offset->top != (int)0x8000; size += 8, clip_active_list_offset++)
            ;
        _fmemcpy(clip_rectangle_workspace, p, size);
        mem_Unlock(g_5746);
        clip_active_list_offset = clip_rectangle_workspace;
    } else
        clip_active_list_offset = 0;
}

/*
 * Report whether the window clip list contains a visible rectangle.
 */
int far clip_window_has_visible_rect(int win)
{
    Handle h;
    struct Rect far *p;
    int r;

    h = clip_window_list_handles[win >> 8];
    p = (struct Rect far *)mem_Lock(h);
    if (h && p->top != (int)0x8000)
        r = 1;
    else
        r = 0;
    mem_Unlock(h);
    return r;
}

/*
 * Select the screen area left uncovered by the window stack.
 */
void far clip_set_desktop_region(void)
{
    struct Rect far *p;
    int size;

    clip_reset_temporary_state();
    if (clip_outside_windows_handle == &clip_screen_list_pointer) {
        clip_active_list_offset = &gfx_screen_clip_list;
        return;
    }
    g_5746 = clip_outside_windows_handle;
    if (!g_5746)
        Punt("\n\aERROR MEMNULL winClipHandle");
    p = (struct Rect far *)mem_Lock(g_5746);
    if (p) {
        for (size = 8, clip_active_list_offset = p; clip_active_list_offset->top != (int)0x8000; size += 8, clip_active_list_offset++)
            ;
        _fmemcpy(clip_rectangle_workspace, p, size);
        clip_active_list_offset = clip_rectangle_workspace;
        mem_Unlock(g_5746);
    }
}

/*
 * Reset temporary clipping and select the screen rectangle.
 */
void far clip_set_screen_region(void)
{
    clip_reset_temporary_state();
    clip_active_list_offset = &gfx_screen_clip_list;
}

void far clip_Off(void)
{
    clip_reset_temporary_state();
    clip_active_list_offset = 0;
}

/*
 * Count rectangles up to the 0x8000 top-coordinate sentinel.
 */
int far clip_count_rects(struct Rect far *r)
{
    int n;

    for (n = 0; r->top != (int)0x8000; r++, n++)
        ;
    return n;
}

int s_584C = 0;

extern void far * far _fmemset(void far *dst, int c, unsigned n);
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern struct Rect far * far clip_split_rect_list(struct Rect far *c, struct Rect far *list,
                                         struct Rect far *in, struct Rect far *out);
extern Handle far mem_Realloc(Handle h, long size, int flags);


void far win_rebuild_visible_clips(void)
{
    int i;
    int next;
    int n;
    int win;
    struct Rect far *end;
    struct Rect far *list;
    struct Rect r;
    Handle tmpH;
    struct Rect far *tmp;

    clip_reset_temporary_state();
    if (!s_584C) {
        _fmemset(clip_window_list_handles, 0, sizeof(clip_window_list_handles));
        s_584C = 1;
    }
    if (clip_outside_windows_handle && clip_outside_windows_handle != &clip_screen_list_pointer)
        mem_Free(clip_outside_windows_handle);
    win = clip_window_z_order[0];
    if (win == (int)0x8000) {
        clip_outside_windows_handle = &clip_screen_list_pointer;
        return;
    }
    tmpH = mem_Alloc(256 * sizeof(struct Rect), 0, "tmprects");
    tmp = (struct Rect far *)mem_Lock(tmpH);
    clip_outside_windows_handle = mem_Alloc(256 * sizeof(struct Rect), 0, "clipout");
    for (i = 0; i < 45; i++) {
        if (clip_window_list_handles[i]) {
            mem_Free(clip_window_list_handles[i]);
            clip_window_list_handles[i] = 0;
        }
    }
    list = (struct Rect far *)mem_Lock(clip_outside_windows_handle);
    *list = gfx_screen_clip_list;
    list[1].top = 0x8000;
    win_GetObjRect(win, &r);
    clip_window_list_handles[win >> 8] = mem_Alloc(n = (clip_split_rect_list(&r, list, tmp, 0L) - tmp + 1) * sizeof(struct Rect), 1, "winClipList");
    _fmemcpy(mem_Lock(clip_window_list_handles[win >> 8]), tmp, n);
    mem_Unlock(clip_window_list_handles[win >> 8]);
    for (i = 1; i < 32; i++) {
        next = clip_window_z_order[i];
        if (next == (int)0x8000)
            break;
        win_GetObjRect(win, &r);
        end = clip_split_rect_list(&r, list, 0L, tmp);
        if ((n = end - tmp) >= 256)
            Punt("C097: Clip overflow %d", (end - tmp));
        _fmemcpy(list, tmp, ((end - tmp) + 1) * sizeof(struct Rect));
        win_GetObjRect(next, &r);
        end = clip_split_rect_list(&r, list, tmp, 0L);
        if ((n = end - tmp) >= 256)
            Punt("C098: Clip overflow %d", (end - tmp));
        f_1E57_0006(n, 0);
        clip_window_list_handles[next >> 8] = mem_Alloc(n = (n + 1) * sizeof(struct Rect), 1, "winClipList");
        _fmemcpy(mem_Lock(clip_window_list_handles[next >> 8]), tmp, n);
        mem_Unlock(clip_window_list_handles[next >> 8]);
        win = next;
    }
    win_GetObjRect(win, &r);
    end = clip_split_rect_list(&r, list, 0L, tmp);
    n = end - tmp;
    if (n >= 256) Punt("C099: Clip overflow %d", n);
    f_1E57_0006(n, 0);
    n = (n + 1) * sizeof(struct Rect);
    _fmemcpy(list, tmp, n);
    mem_Unlock(clip_outside_windows_handle);
    clip_outside_windows_handle = mem_Realloc(clip_outside_windows_handle, n, 1);
    mem_Unlock(tmpH);
    mem_Free(tmpH);
    f_1E57_0007();
}


extern struct Rect far * far clip_split_rect(struct Rect far *r, struct Rect far *c,
                                         struct Rect far *in, struct Rect far *out);

void far clip_SubInclude(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subinclude");
        buf = (struct Rect far *)mem_Lock(h);
        p = buf;
        if (!clip_active_list_offset) {
            n = 1;
            *p = *r;
        } else {
            for (; clip_active_list_offset->top != (int)0x8000; clip_active_list_offset++)
                p = clip_split_rect(clip_active_list_offset, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    clip_active_list_offset = clip_rectangle_workspace;
    _fmemcpy(clip_active_list_offset, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    g_5742 = h;
    f_1E57_0006(n, 1);
}

/*
 * Intersect clipping with a rectangle list, or copy that list when clipping is off.
 */
void far clip_intersect_rect_list(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    struct Rect far *c;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subinclude");
        buf = (struct Rect far *)mem_Lock(h);
        p = buf;
        if (!clip_active_list_offset) {
            for (n = 0; r->top != (int)0x8000; n++) {
                *p = *r;
                p++;
                r++;
            }
        } else {
            for (; r->top != (int)0x8000; r++)
                for (c = clip_active_list_offset; c->top != (int)0x8000; c++)
                    p = clip_split_rect(c, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    clip_active_list_offset = clip_rectangle_workspace;
    _fmemcpy(clip_active_list_offset, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    mem_Free(h);
    f_1E57_0006(n, 1);
}

void far clip_restrict_rect(struct Rect far *r)
{
    clip_SubInclude(r);
}

void far clip_SubExclude(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subexclude");
        buf = (struct Rect far *)mem_Lock(h);
        if (!clip_active_list_offset)
            clip_active_list_offset = &gfx_screen_clip_list;
        for (p = buf; clip_active_list_offset->top != (int)0x8000; clip_active_list_offset++)
            p = clip_split_rect(clip_active_list_offset, r, 0L, p);
        if ((n = p - buf) >= 256)
            Punt("CL074:Temp clip overflow in SubExclude");
    } else
        Punt("Sub exclude NULL rect!!");
    f_1E57_0006(n, 1);
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    clip_active_list_offset = clip_rectangle_workspace;
    _fmemcpy(clip_active_list_offset, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    g_5742 = h;
}

/*
 * Subtract the rectangle from the current clip region.
 */
void far clip_exclude_rect(struct Rect far *r)
{
    clip_SubExclude(r);
}

/*
 * Append the rectangle's separate outside pieces against each current clip rectangle.
 */
void far clip_append_rect_remainders(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    struct Rect far *c;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "include");
        buf = (struct Rect far *)mem_Lock(h);
        if (clip_active_list_offset && clip_active_list_offset->top != (int)0x8000) {
            for (c = clip_active_list_offset, p = buf; c->top != (int)0x8000;) {
                *p = *c;
                c++;
                p++;
            }
            for (; clip_active_list_offset->top != (int)0x8000;) {
                p = clip_split_rect(r, clip_active_list_offset, 0L, p);
                clip_active_list_offset++;
            }
            if ((n = p - buf) >= 256)
                Punt("CL174:Temp clip overflow in SubExclude");
        } else {
            n = 1;
            *buf = *r;
        }
    } else
        Punt("include NULL rect!!");
    f_1E57_0006(n, 1);
    buf[n].top = 0x8000;
    clip_reset_temporary_state();
    clip_active_list_offset = clip_rectangle_workspace;
    _fmemcpy(clip_active_list_offset, buf, (n + 1) << 3);
    mem_Unlock(h);
    mem_Free(h);
}

/*
 * Expand clipping through the rectangle-remainder helper; pieces are not normalized.
 */
void far clip_expand_by_rect(struct Rect far *r)
{
    clip_append_rect_remainders(r);
}

extern Handle far clip_saved_state_stack;

void far clip_Push(void)
{
    struct Rect far *p;
    int size;
    Handle h;
    Handle far *node;

    size = 0;
    if ((p = clip_active_list_offset) != 0) {
        for (; p->top != (int)0x8000; p++)
            ;
        size = (char far *)p - (char far *)clip_active_list_offset + sizeof(struct Rect);
        clip_saved_rectangle_total += size / (int)sizeof(struct Rect);
    }
    if (!(h = mem_Alloc(size + 8L, 1, "clip_Push")))
        Punt("Cannot allocate memory in clip_Push");
    node = (Handle far *)mem_Lock(h);
    if (size)
        _fmemcpy(node + 2, clip_active_list_offset, size);
    node[0] = clip_saved_state_stack;
    ((struct Rect far * far *)node)[1] = clip_active_list_offset;
    clip_saved_state_stack = h;
    if (++clip_saved_state_depth > 20)
        Punt("Error CL98463: Pushed it too far");
    mem_Unlock(h);
}

/* Pushes the clip state and turns clipping off.  No reference to this function was
 * found; the parameter list is a hypothesis. */
/*
 * Save the current clip state, then turn clipping off.
 */
void far clip_push_and_disable(void)
{
    clip_Push();
    clip_Off();
}

void far clip_Pop(void)
{
    Handle far *node;
    struct Rect far *p;
    int size;

    if (!clip_saved_state_depth)
        Punt("Clip_Pop w/ nothing on the stack: E9073");
    clip_reset_temporary_state();
    g_5742 = clip_saved_state_stack;
    node = (Handle far *)mem_Lock(g_5742);
    clip_saved_state_stack = node[0];
    if (!((struct Rect far * far *)node)[1])
        clip_active_list_offset = 0;
    else if ((p = clip_active_list_offset = (struct Rect far *)(node + 2)) != 0) {
        for (; p->top != (int)0x8000; p++)
            ;
        size = (char far *)p - (char far *)clip_active_list_offset + sizeof(struct Rect);
        _fmemcpy(clip_rectangle_workspace, clip_active_list_offset, size);
        clip_active_list_offset = clip_rectangle_workspace;
    }
    clip_saved_state_depth--;
    mem_Unlock(g_5742);
}

/*
 * Disable clipping for a screen-contained rectangle; otherwise select the screen clip.
 */
void far clip_screen_if_rect_outside(struct Rect far *r)
{
    if (r->top >= gfx_screen_clip_list.top && r->bottom <= gfx_screen_clip_list.bottom &&
        r->left >= gfx_screen_clip_list.left && r->right <= gfx_screen_clip_list.right)
        clip_Off();
    else
        clip_set_screen_region();
}


void far clip_set_screen_intersection(struct Rect far *r)
{
    if (r) {
        clip_reset_temporary_state();
        clip_active_list_offset = clip_rectangle_workspace;
        clip_split_rect(r, &gfx_screen_clip_list, clip_rectangle_workspace, 0L);
    }
}
