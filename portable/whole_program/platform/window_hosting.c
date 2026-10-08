#include "window_hosting.h"
#include "graphics_source_clip.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/window_runtime_owner.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef char **Handle;

/* Canonical owners (root m1E57 and friends). */
extern int16_t g_5702[32];
extern Handle fd_50F6_3B60[45];
extern int16_t g_3DB4;
extern int16_t g_3DB6;
extern Handle f_171C_1A9E(int32_t size, int16_t flags, char *name);
extern char *f_171C_1B84(Handle h);
extern Handle f_171C_1BBA(Handle h);
extern struct Rect *f_1D8E_02BD(struct Rect *c, struct Rect *list,
                                struct Rect *in, struct Rect *out);
extern void win_GetObjRect(int16_t obj, struct Rect *rect);
extern char *win_WinAddr(int16_t win);
extern char *win_ObjAddr(int16_t obj);
extern void win_LockWin(int16_t win);
extern void win_UnlockWin(int16_t win);

/* The linker routes cross-module calls to these canonical entry points
 * through the wrappers below (-Wl,--wrap); the canonical bodies are unchanged. */
extern void __real_clip_SetWin(int16_t win);
extern void __real_clip_Off(void);
extern void __real_f_1E57_0296(void);
extern void __real_f_1E57_0351(void);
extern void __real_f_1E57_0FDC(struct Rect *r);
extern void __real_clip_Push(void);
extern void __real_clip_Pop(void);
extern void __real_f_1E57_038E(void);
extern void __real_f_1E57_0052(int16_t win);
extern void __real_f_1E57_00B1(int16_t win);
extern void __real_clip_KillWin(int16_t win);
extern void __real_win_DrawTitle(int16_t win);

#define END ((int16_t)(uint16_t)0x8000)

enum ClipContext { CONTEXT_SCREEN, CONTEXT_WINDOW, CONTEXT_DESKTOP };

typedef struct Hosted {
    int16_t id;
    SimVgaPlanes *planes;
} Hosted;

typedef struct StackEntry {
    int16_t id;
    struct Rect rect;
    SimVgaPlanes *planes;  /* NULL: shared card planes */
} StackEntry;

static struct {
    int enabled;
    SimVga *vga;
    Hosted hosted[SIM_HOSTING_SLOTS];
    unsigned hosted_count;
    StackEntry stack[32];
    unsigned stack_count;
    struct WindowInfo {
        struct Rect drag;      /* object 1 when it is the title (0x0c/0x12) */
        uint16_t flags;        /* record +0x1C */
        int16_t margin;        /* object 0 +0x28: frame inset of the chrome */
        char title[64];
    } info[SIM_HOSTING_SLOTS];
    unsigned generation;
    enum ClipContext context;
    int16_t context_window;
    struct { enum ClipContext context; int16_t window; } saved[32];
    unsigned saved_count;
    int cursor_depth;
    int16_t pointer_window;        /* native window under the mouse, or END */
    SimVgaPlanes *cursor_planes;   /* where the visible cursor was drawn */
} s;

static SimVgaPlanes *hosted_planes(int16_t id)
{
    unsigned i;
    for (i = 0; i < s.hosted_count; ++i)
        if (s.hosted[i].id == (int16_t)(id & 0xff00)) return s.hosted[i].planes;
    return NULL;
}

int sim_window_hosting_is_hosted(int16_t id) { return hosted_planes(id) != NULL; }
int sim_window_hosting_enabled(void) { return s.enabled; }
unsigned sim_window_hosting_generation(void) { return s.generation; }
unsigned sim_window_hosting_count(void) { return s.hosted_count; }

static int contains(const struct Rect *r, int x, int y)
{
    return x >= r->left && x < r->right && y >= r->top && y < r->bottom;
}

static SimVgaPlanes *owner_planes(int x, int y)
{
    unsigned i;
    for (i = 0; i < s.stack_count; ++i)
        if (contains(&s.stack[i].rect, x, y)) return s.stack[i].planes;
    return NULL;
}

static const StackEntry *stack_entry(int16_t id)
{
    unsigned i;
    for (i = 0; i < s.stack_count; ++i)
        if (s.stack[i].id == (int16_t)(id & 0xff00)) return &s.stack[i];
    return NULL;
}

/* One aperture byte: which plane set holds each of its pixels.
 *  - no clip list (clip_Off, dialogs that clear g_5AAC) or the desktop
 *    list: the shared planes, which present as the root/desktop window;
 *  - a window's clip_SetWin list: that window's pixels go to its planes;
 *  - otherwise (full-screen lists used for top-window object feedback,
 *    outlines and the cursor): the logical topmost window at each pixel. */
static unsigned route(void *context, uint16_t offset, SimVgaSpan spans[8])
{
    const StackEntry *target = NULL;
    unsigned bit, n = 0, stride = (uint16_t)g_3DB6;
    int x, y;
    (void)context;
    if (!s.enabled || s.stack_count == 0 || stride == 0) return 0;
    y = offset / stride;
    if (s.cursor_depth) {
        /* The whole cursor (save-under, image, restore) stays on one surface. */
        if (y >= g_3DB4 || s.cursor_planes == NULL) return 0;
        spans[0].planes = s.cursor_planes;
        spans[0].mask = 255;
        return 1;
    }
    if (g_5AAC == NULL || s.context == CONTEXT_DESKTOP) return 0;
    if (y >= g_3DB4) return 0;
    x = (int)(offset % stride) * 8;
    if (s.context == CONTEXT_WINDOW)
        target = stack_entry(s.context_window);
    for (bit = 0; bit < 8; ++bit) {
        SimVgaPlanes *planes = target && contains(&target->rect, x + (int)bit, y) ?
            target->planes : owner_planes(x + (int)bit, y);
        if (planes == NULL) planes = (SimVgaPlanes *)&s.vga->planes;
        if (n && spans[n - 1].planes == planes)
            spans[n - 1].mask |= (uint8_t)(0x80u >> bit);
        else {
            spans[n].planes = planes;
            spans[n].mask = (uint8_t)(0x80u >> bit);
            ++n;
        }
    }
    return n == 1 && spans[0].planes == (SimVgaPlanes *)&s.vga->planes ? 0 : n;
}

int sim_window_hosting_enable(SimVga *vga, const int16_t *ids, unsigned count)
{
    unsigned i;
    if (vga == NULL || count > SIM_HOSTING_SLOTS || s.enabled) return 0;
    memset(&s, 0, sizeof(s));
    for (i = 0; i < count; ++i) {
        s.hosted[i].id = (int16_t)(ids[i] & 0xff00);
        s.hosted[i].planes = calloc(1, sizeof(SimVgaPlanes));
        if (s.hosted[i].planes == NULL) return 0;
    }
    s.hosted_count = count;
    s.vga = vga;
    s.pointer_window = END;
    s.enabled = 1;
    sim_vga_set_router(vga, route, NULL);
    return 1;
}

static void hosted_clip_list(int16_t id)
{
    struct Rect r, screen[2], tmp[2];
    struct Rect *end;
    Handle h;
    int16_t n;
    /* f_1E57_038E's per-window list shape, without occlusion by others. */
    screen[0] = g_5A9C[0];
    screen[1].top = END;
    win_GetObjRect(id, &r);
    end = f_1D8E_02BD(&r, screen, tmp, NULL);
    n = (int16_t)((end - tmp + 1) * (int)sizeof(struct Rect));
    h = f_171C_1A9E(n, 1, "winClipList");
    memcpy(f_171C_1B84(h), tmp, (size_t)n);
    f_171C_1BBA(h);
    fd_50F6_3B60[(uint16_t)id >> 8] = h;
}

static int was_open(int16_t id)
{
    unsigned i;
    for (i = 0; i < s.stack_count; ++i)
        if (s.stack[i].id == id) return 1;
    return 0;
}

/* Native caption and close box come from the record, as Win16 win_Open
 * builds them: title object 1 (type 0x0C inline text, type 0x12 inline or
 * handle text), flags +0x1C, chrome inset object 0 +0x28. */
static void read_info(int16_t id)
{
    struct WindowInfo *info = &s.info[(uint16_t)id >> 8];
    char *w, *o, *text = NULL, **handle = NULL;
    win_LockWin(id);
    w = win_WinAddr(id);
    memset(&info->drag, 0, sizeof(info->drag));
    info->flags = *(uint16_t *)(w + 0x1c);
    info->margin = (unsigned char)win_ObjAddr(id)[0x28];
    if (*(int16_t *)(w + 0x0c) >= 2) {
        o = win_ObjAddr((int16_t)(id + 1));
        if (o[0x21] == 0x0c || o[0x21] == 0x12) {
            win_GetObjRect((int16_t)(id + 1), &info->drag);
            if (o[0x21] == 0x0c) text = o + 0x2a;
            else if ((handle = *sim_window_ref_registry_handle_slot_for_object(
                          &sim_window_ref_registry, o, 0x2a)) == NULL) {
                text = o + 0x2e;
                if (strchr(text, '%')) text = NULL;
            } else text = f_171C_1B84(handle);
        }
    }
    snprintf(info->title, sizeof(info->title), "%s", text && text[0] ? text : "SimAnt");
    if (handle) f_171C_1BBA(handle);
    win_UnlockWin(id);
}

static void cache_stack(void)
{
    StackEntry previous[32];
    unsigned i, j, previous_count = s.stack_count;
    memcpy(previous, s.stack, sizeof(previous));
    s.stack_count = 0;
    for (i = 0; i < 32 && g_5702[i] != END; ++i) {
        StackEntry *e = &s.stack[s.stack_count++];
        int16_t id = g_5702[i];
        e->id = id;
        win_GetObjRect(id, &e->rect);
        e->planes = hosted_planes(id);
        if (e->planes) read_info(id);
    }
    /* Window inventory for playtest reports: logical opens and closes. */
    for (i = 0; i < s.stack_count; ++i) {
        for (j = 0; j < previous_count && previous[j].id != s.stack[i].id; ++j)
            ;
        if (j == previous_count) {
            char *w;
            uint16_t flags;
            win_LockWin(s.stack[i].id);
            w = win_WinAddr(s.stack[i].id);
            flags = *(uint16_t *)(w + 0x1c);
            win_UnlockWin(s.stack[i].id);
            fprintf(stderr, "Logical window %04X opened rect=(%d,%d,%d,%d) flags=%04X %s\n",
                    (unsigned)(uint16_t)s.stack[i].id, s.stack[i].rect.left, s.stack[i].rect.top,
                    s.stack[i].rect.right, s.stack[i].rect.bottom, (unsigned)flags,
                    s.stack[i].planes ? "hosted" : "shared");
        }
    }
    for (j = 0; j < previous_count; ++j)
        if (!was_open(previous[j].id))
            fprintf(stderr, "Logical window %04X closed\n", (unsigned)(uint16_t)previous[j].id);
    ++s.generation;
}

/* Recompute after the canonical lists: m1E57 occlusion among the windows that
 * share the card (the canonical algorithm, over that sub-stack), and an
 * unoccluded list for each hosted window. */
static void restack(void)
{
    int16_t saved[32], shared[32];
    unsigned i, j, hosted_open = 0;
    if (!s.enabled) return;
    memcpy(saved, g_5702, sizeof(saved));
    for (i = j = 0; i < 32 && saved[i] != END; ++i) {
        if (hosted_planes(saved[i])) ++hosted_open;
        else shared[j++] = saved[i];
    }
    if (hosted_open) {
        for (; j < 32; ++j) shared[j] = END;
        memcpy(g_5702, shared, sizeof(shared));
        __real_f_1E57_038E();
        memcpy(g_5702, saved, sizeof(saved));
        for (i = 0; i < 32 && saved[i] != END; ++i)
            if (hosted_planes(saved[i])) hosted_clip_list(saved[i]);
    }
    cache_stack();
}

void __wrap_f_1E57_038E(void) { __real_f_1E57_038E(); restack(); }
void __wrap_f_1E57_0052(int16_t win) { __real_f_1E57_0052(win); restack(); }
void __wrap_f_1E57_00B1(int16_t win) { __real_f_1E57_00B1(win); restack(); }
void __wrap_clip_KillWin(int16_t win) { __real_clip_KillWin(win); restack(); }
/* Win16 win_DrawTitle also sets the native caption (SetWindowText). */
void __wrap_win_DrawTitle(int16_t win)
{
    __real_win_DrawTitle(win);
    if (s.enabled && hosted_planes(win) && stack_entry(win)) { read_info(win); ++s.generation; }
}

void __wrap_clip_SetWin(int16_t win)
{
    __real_clip_SetWin(win);
    s.context = CONTEXT_WINDOW;
    s.context_window = (int16_t)(win & 0xff00);
}
void __wrap_clip_Off(void) { __real_clip_Off(); s.context = CONTEXT_SCREEN; }
void __wrap_f_1E57_0296(void) { __real_f_1E57_0296(); s.context = CONTEXT_DESKTOP; }
void __wrap_f_1E57_0351(void) { __real_f_1E57_0351(); s.context = CONTEXT_SCREEN; }
void __wrap_f_1E57_0FDC(struct Rect *r) { __real_f_1E57_0FDC(r); s.context = CONTEXT_SCREEN; }
void __wrap_clip_Push(void)
{
    __real_clip_Push();
    if (s.saved_count < 32) {
        s.saved[s.saved_count].context = s.context;
        s.saved[s.saved_count].window = s.context_window;
    }
    ++s.saved_count;
}
void __wrap_clip_Pop(void)
{
    __real_clip_Pop();
    if (s.saved_count && --s.saved_count < 32) {
        s.context = s.saved[s.saved_count].context;
        s.context_window = s.saved[s.saved_count].window;
    }
}

void sim_window_hosting_cursor_scope(int mode)
{
    if (mode == 0) {
        if (s.cursor_depth) --s.cursor_depth;
        return;
    }
    /* Show: the surface of the native window the mouse is in (the root for
     * the desktop). Hide: the surface that received the last show. */
    if (mode == 1 || s.cursor_planes == NULL)
        s.cursor_planes = s.pointer_window != END && hosted_planes(s.pointer_window) &&
                          stack_entry(s.pointer_window) ?
            hosted_planes(s.pointer_window) : (SimVgaPlanes *)&s.vga->planes;
    ++s.cursor_depth;
}

void sim_window_hosting_set_pointer_window(int16_t id) { s.pointer_window = id; }

int16_t sim_window_hosting_owner_at(int16_t x, int16_t y)
{
    unsigned i;
    for (i = 0; i < s.stack_count; ++i)
        if (contains(&s.stack[i].rect, x, y)) return s.stack[i].id;
    return END;
}

int sim_window_hosting_visible_point(int16_t id, int16_t *x, int16_t *y)
{
    const StackEntry *e = stack_entry(id);
    int px, py;
    if (e == NULL) return 0;
    for (py = e->rect.top + 2; py < e->rect.bottom; py += 4)
        for (px = e->rect.left + 2; px < e->rect.right; px += 4)
            if (sim_window_hosting_owner_at((int16_t)px, (int16_t)py) == e->id) {
                *x = (int16_t)px;
                *y = (int16_t)py;
                return 1;
            }
    return 0;
}

int sim_window_hosting_view(unsigned index, SimHostedWindowView *view)
{
    const StackEntry *e;
    const struct WindowInfo *info;
    if (index >= s.hosted_count || view == NULL) return 0;
    memset(view, 0, sizeof(*view));
    view->id = s.hosted[index].id;
    view->planes = s.hosted[index].planes;
    e = stack_entry(view->id);
    if (e == NULL) return 1;
    info = &s.info[(uint16_t)view->id >> 8];
    view->open = 1;
    view->top = s.stack_count && s.stack[0].id == view->id;
    view->left = e->rect.left; view->top_y = e->rect.top;
    view->right = e->rect.right; view->bottom = e->rect.bottom;
    view->drag_left = info->drag.left; view->drag_top = info->drag.top;
    view->drag_right = info->drag.right; view->drag_bottom = info->drag.bottom;
    view->flags = info->flags;
    view->margin = info->margin;
    memcpy(view->title, info->title, sizeof(view->title));
    return 1;
}
