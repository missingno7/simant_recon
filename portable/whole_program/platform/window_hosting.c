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
extern struct Rect fd_50F6_393C;           /* menu bar; windows stay below it */
extern void (*g_62EC)(int16_t win);         /* window geometry changed hook */
extern Handle f_171C_1A9E(int32_t size, int16_t flags, char *name);
extern char *f_171C_1B84(Handle h);
extern Handle f_171C_1BBA(Handle h);
extern struct Rect *f_1D8E_02BD(struct Rect *c, struct Rect *list,
                                struct Rect *in, struct Rect *out);
extern void win_GetObjRect(int16_t obj, struct Rect *rect);
extern char *win_WinAddr(int16_t win);
extern char *win_ObjAddr(int16_t obj);
extern struct Rect *win_WinRectAddr(int16_t win);
extern void win_LockWin(int16_t win);
extern void win_UnlockWin(int16_t win);
extern void win_Recalc(int16_t win);
extern void win_Close(int16_t win);
extern void f_20E8_0725(int16_t win);       /* activate: close auto-close top, open */
extern void f_1E57_038E(void);
extern void f_21FA_0B4B(struct Rect *rect);  /* redraw what a rect exposed */
extern void f_2505_08EA(int16_t win);
extern void f_2505_0831(int16_t win);

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
extern void __real_f_1B28_0069(void);
extern char *__real_GSaveRect(struct Rect *r);
extern void __real_f_1CE2_056C(struct Rect *r, char *buf);

#define END ((int16_t)(uint16_t)0x8000)

enum ClipContext { CONTEXT_SCREEN, CONTEXT_WINDOW, CONTEXT_DESKTOP };
enum { POPUP_DEPTH = 4 };

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
        int16_t min_width, min_height;
        int anchored;          /* object 0 anchors +0x18..+0x1E name another owner */
        char title[64];
    } info[SIM_HOSTING_SLOTS];
    unsigned generation;
    enum ClipContext context;
    int16_t context_window;
    struct { enum ClipContext context; int16_t window; } saved[32];
    unsigned saved_count;
    struct Popup {
        struct Rect rect;
        char *buffer;          /* GSaveRect result: pairs the restore */
        SimVgaPlanes *planes;
    } popup[POPUP_DEPTH];
    SimVgaPlanes *popup_planes[POPUP_DEPTH];
    unsigned popup_count, popup_serial;
    void (*pump)(void);
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
void sim_window_hosting_set_pump(void (*pump)(void)) { s.pump = pump; }

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

static SimVgaPlanes *popup_planes_at(int x, int y)
{
    unsigned i = s.popup_count;
    while (i--)
        if (contains(&s.popup[i].rect, x, y)) return s.popup[i].planes;
    return NULL;
}

/* One aperture byte: which plane set holds each of its pixels.
 *  - a hosted window's clip_SetWin drawing: that window's own planes;
 *  - inside an open save-under popup (GSaveRect): the popup's planes;
 *  - the desktop list: the shared planes (the main/desktop window);
 *  - otherwise, including no clip list (text and animation that dialogs draw
 *    after clearing g_5AAC) and full-screen lists (top-window object feedback,
 *    outlines): the logical topmost window at each pixel. */
static unsigned route(void *context, uint16_t offset, SimVgaSpan spans[8])
{
    const StackEntry *target = NULL;
    unsigned bit, n = 0, stride = (uint16_t)g_3DB6;
    int x, y, desktop;
    (void)context;
    if (!s.enabled || stride == 0) return 0;
    y = offset / stride;
    if (y >= g_3DB4 || (s.stack_count == 0 && s.popup_count == 0)) return 0;
    x = (int)(offset % stride) * 8;
    if (s.context == CONTEXT_WINDOW && g_5AAC != NULL)
        target = stack_entry(s.context_window);
    desktop = g_5AAC != NULL && s.context == CONTEXT_DESKTOP;
    for (bit = 0; bit < 8; ++bit) {
        int px = x + (int)bit;
        SimVgaPlanes *planes = NULL;
        if (target && target->planes && contains(&target->rect, px, y)) planes = target->planes;
        else if (s.popup_count && (planes = popup_planes_at(px, y)) != NULL) ;
        else if (target && contains(&target->rect, px, y)) planes = target->planes;
        else if (!desktop) planes = owner_planes(px, y);
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
    for (i = 0; i < POPUP_DEPTH; ++i)
        if ((s.popup_planes[i] = calloc(1, sizeof(SimVgaPlanes))) == NULL) return 0;
    s.hosted_count = count;
    s.vga = vga;
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
 * handle text), flags +0x1C, minimum size +0x18/+0x1A, chrome inset
 * object 0 +0x28. */
static void read_info(int16_t id)
{
    struct WindowInfo *info = &s.info[(uint16_t)id >> 8];
    char *w, *o, *text = NULL, **handle = NULL;
    win_LockWin(id);
    w = win_WinAddr(id);
    memset(&info->drag, 0, sizeof(info->drag));
    info->flags = *(uint16_t *)(w + 0x1c);
    info->min_width = *(int16_t *)(w + 0x18);
    info->min_height = *(int16_t *)(w + 0x1a);
    info->margin = (unsigned char)win_ObjAddr(id)[0x28];
    {
        /* Win16 win_Open re-places a hidden window from its record only when
         * object 0 is anchored to something else (fields +0x18..+0x1E). */
        const int16_t *mode = (const int16_t *)(win_ObjAddr(id) + 0x18);
        int k;
        info->anchored = 0;
        for (k = 0; k < 4; ++k)
            if (mode[k] != 0 && mode[k] != (int16_t)(id & 0xff00)) info->anchored = 1;
    }
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

/* Win16 erases a window with its class brush (GenericWindow: COLOR_WINDOW,
 * white) before WM_PAINT, on win_Open and on WM_SIZE; a hosted window's own
 * planes start the same way, so never-drawn areas show no stale pixels. */
static void erase(SimVgaPlanes *planes, const struct Rect *r)
{
    int x, y, plane;
    for (y = r->top < 0 ? 0 : r->top; y < r->bottom && y < g_3DB4; ++y)
        for (x = r->left < 0 ? 0 : r->left; x < r->right && x < 640; ++x) {
            uint16_t offset = (uint16_t)(y * 80 + x / 8);
            for (plane = 0; plane < 4; ++plane)
                (*planes)[plane][offset] |= (uint8_t)(0x80u >> (x & 7));
        }
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
            if (s.stack[i].planes) erase(s.stack[i].planes, &s.stack[i].rect);
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

/* Save-under popups (info and choice boxes, popup menus): DOS saves the
 * screen under the box, draws it, and restores the saved pixels. Win16 shows
 * these as native popup windows; the saved rect is their lifetime. */
char *__wrap_GSaveRect(struct Rect *r)
{
    struct Popup *p;
    if (!s.enabled || r == NULL || s.popup_count == POPUP_DEPTH) return __real_GSaveRect(r);
    p = &s.popup[s.popup_count];
    p->rect = *r;
    p->planes = s.popup_planes[s.popup_count];
    memset(p->planes, 0, sizeof(*p->planes));
    ++s.popup_count;
    ++s.popup_serial;
    p->buffer = __real_GSaveRect(r);
    return p->buffer;
}

void __wrap_f_1CE2_056C(struct Rect *r, char *buf)
{
    __real_f_1CE2_056C(r, buf);
    if (s.enabled && s.popup_count && s.popup[s.popup_count - 1].buffer == buf) {
        --s.popup_count;
        ++s.popup_serial;
    }
}

unsigned sim_window_hosting_popups(SimHostedPopupView *views, unsigned capacity)
{
    unsigned i;
    for (i = 0; i < s.popup_count && i < capacity; ++i) {
        views[i].left = s.popup[i].rect.left;
        views[i].top = s.popup[i].rect.top;
        views[i].right = s.popup[i].rect.right;
        views[i].bottom = s.popup[i].rect.bottom;
        views[i].planes = s.popup[i].planes;
    }
    return s.popup_count;
}

unsigned sim_window_hosting_popup_serial(void) { return s.popup_serial; }

/* The game's event pump (f_218D_02D5 calls this empty stub first): native
 * window actions run here, where Win16 dispatched window messages. */
void __wrap_f_1B28_0069(void)
{
    __real_f_1B28_0069();
    if (s.enabled && s.pump) s.pump();
}

/* ---- native window actions, called only from the pump ---- */

int sim_window_hosting_close(int16_t id)
{
    if (!stack_entry(id)) return 0;
    win_Close(id);                    /* Win16 WM_CLOSE -> win_Close(INDEX) */
    return 1;
}

int sim_window_hosting_raise(int16_t id)
{
    if (!stack_entry(id)) return 0;
    if (s.stack[0].id != (int16_t)(id & 0xff00))
        f_20E8_0725(id);              /* DOS f_218D_0451's activation */
    return 1;
}

/* Win16 WM_SIZE (MAINWNDPROC 2A64): rewrite the record rect and the first
 * object by the size delta, win_Recalc, then DOS's own geometry-change tail
 * (o26_39C7_0671: clip lists, hook, exposed redraw, top-window hot boxes).
 * The logical origin shifts when the size needs room on the 640x480 screen;
 * the native window does not move. */
int sim_window_hosting_resize(int16_t id, int width, int height)
{
    struct WindowInfo *info = &s.info[(uint16_t)id >> 8];
    struct Rect orig, r, exposed;
    char *w, *o;
    int top_limit = fd_50F6_393C.bottom + 1;
    if (!stack_entry(id)) return 0;
    if (width < (info->min_width > 0 ? info->min_width : 48)) width = info->min_width > 0 ? info->min_width : 48;
    if (height < (info->min_height > 0 ? info->min_height : 48)) height = info->min_height > 0 ? info->min_height : 48;
    if (width > g_5A9C[0].right) width = g_5A9C[0].right;
    if (height > g_5A9C[0].bottom - top_limit) height = g_5A9C[0].bottom - top_limit;
    win_LockWin(id);
    w = win_WinAddr(id);
    *(uint16_t *)(w + 0x1c) &= (uint16_t)~0x80u;   /* no longer zoomed */
    orig = *(struct Rect *)w;
    r = orig;
    if (r.left + width > g_5A9C[0].right) r.left = (int16_t)(g_5A9C[0].right - width);
    if (r.top + height > g_5A9C[0].bottom) r.top = (int16_t)(g_5A9C[0].bottom - height);
    if (r.top < top_limit) r.top = (int16_t)top_limit;
    r.right = (int16_t)(r.left + width);
    r.bottom = (int16_t)(r.top + height);
    if (!memcmp(&r, &orig, sizeof(r))) {
        win_UnlockWin(id);
        return 1;
    }
    o = win_ObjAddr(id);
    *(int16_t *)(o + 0x08) += (int16_t)(r.left - orig.left);
    *(int16_t *)(o + 0x0a) += (int16_t)(r.top - orig.top);
    *(int16_t *)(o + 0x0c) += (int16_t)((r.right - r.left) - (orig.right - orig.left));
    *(int16_t *)(o + 0x0e) += (int16_t)((r.bottom - r.top) - (orig.bottom - orig.top));
    *win_WinRectAddr(id) = r;
    if (r.left != orig.left || r.top != orig.top)
        win_offsets[(uint16_t)id >> 8] = *(struct Rect *)(o + 0x08);
    win_Recalc(id);
    win_UnlockWin(id);
    f_1E57_038E();
    (*g_62EC)(id);
    exposed.left = orig.left < r.left ? orig.left : r.left;
    exposed.top = orig.top < r.top ? orig.top : r.top;
    exposed.right = orig.right > r.right ? orig.right : r.right;
    exposed.bottom = orig.bottom > r.bottom ? orig.bottom : r.bottom;
    {
        SimVgaPlanes *planes = hosted_planes(id);
        if (planes) erase(planes, &r);
    }
    f_21FA_0B4B(&exposed);
    if (s.stack_count && s.stack[0].id == (int16_t)(id & 0xff00)) {
        f_2505_08EA(id);
        f_2505_0831(id);
    }
    return 1;
}

/* ---- queries for presentation and input routing ---- */

int16_t sim_window_hosting_owner_at(int16_t x, int16_t y)
{
    unsigned i;
    for (i = 0; i < s.stack_count; ++i)
        if (contains(&s.stack[i].rect, x, y)) return s.stack[i].id;
    return END;
}

int16_t sim_window_hosting_top(void) { return s.stack_count ? s.stack[0].id : END; }

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
    view->anchored = info->anchored;
    memcpy(view->title, info->title, sizeof(view->title));
    return 1;
}
