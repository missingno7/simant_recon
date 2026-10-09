#include "native_windows.h"
#include "../window_hosting.h"
#include "host_modes.h"
#include "modern_game_view.h"
#include "native_menu.h"

#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include <stdlib.h>
#include <string.h>

/* Win16 win_Open builds each logical window as a real window: the record's
 * title strip becomes the native caption, flag 4 gives the close box
 * (WM_CLOSE -> win_Close), flag 8 a sizing frame (WM_SIZE -> record rect,
 * win_Recalc); a click on a background window raises it (WM_MOUSEACTIVATE)
 * unless the top window is modal (+0x1C & 0x40); popups are native popup
 * windows (PopUpInfoWindow). Here every hosted window is an owned top-level
 * SDL window, every save-under box a native popup, and native actions run in
 * the game's event pump (window_hosting.h), like Win16 message dispatch.
 *
 * The Game Window (logical window 0) is the first modern window: its map
 * area (editTileRect) is drawn by modern_game_view at any size and zoom; the
 * rest of its client still shows the hosted canonical controls. */

enum { POPUP_DEPTH = 4, DEFERRED_DEPTH = 16 };
#define DEFERRED_TIMEOUT_NS 300000000ull

typedef struct Surface {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint8_t *indexed, *rgba;
    int width, height;             /* logical size */
} Surface;

typedef struct NativeWindow {
    SimHostedWindowView view;      /* last presented logical state */
    Surface surface;
    int strip;                     /* title strip replaced by the native caption */
    int shown;
    int modern;                    /* the Game Window: native size is the user's */
    char title[64];
    Uint8 eaten_button;            /* a background click: raise only */
    int close_pending, raise_pending;
    int resize_w, resize_h;        /* requested logical client size, 0: none */
} NativeWindow;

typedef struct NativePopup {
    SimHostedPopupView view;
    Surface surface;
    int x, y;                      /* client position in desktop coordinates */
} NativePopup;

extern struct Rect { int16_t left, top, right, bottom; } fd_50F6_393C; /* game menu bar */

static struct {
    int active;
    int scale;
    int crop;                      /* main window starts below the game menu bar */
    Host *host;
    SDL_Window *root;
    NativeWindow windows[SIM_HOSTING_SLOTS];
    unsigned count;
    NativePopup popups[POPUP_DEPTH];
    unsigned popup_count, popup_serial;
    Uint8 root_dropped_button;
    struct {                       /* mouse input held while the edit view scrolls */
        SDL_Event events[DEFERRED_DEPTH];
        unsigned count;
        int waiting, replaying;
        uint64_t since;
    } deferred;
} n;

int native_windows_active(void) { return n.active; }
int native_windows_scale(void) { return n.scale ? n.scale : 1; }

static void destroy_surface(Surface *s)
{
    SDL_DestroyTexture(s->texture);
    SDL_DestroyRenderer(s->renderer);
    SDL_DestroyWindow(s->window);
    free(s->indexed);
    free(s->rgba);
    memset(s, 0, sizeof(*s));
}

static NativeWindow *by_logical_id(int16_t id)
{
    unsigned i;
    for (i = 0; i < n.count; ++i)
        if (n.windows[i].view.id == (int16_t)(id & 0xff00)) return &n.windows[i];
    return NULL;
}

/* ---- actions in the game's event pump ---- */

static void pump(void)
{
    unsigned i;
    native_menu_pump();
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        if (!w->view.open) continue;
        if (w->close_pending) {
            w->close_pending = 0;
            sim_window_hosting_close(w->view.id);
            continue;
        }
        if (w->raise_pending || w->resize_w) {
            w->raise_pending = 0;
            sim_window_hosting_raise(w->view.id);
        }
        if (w->resize_w) {
            int width = w->resize_w, height = w->resize_h + w->strip;
            w->resize_w = w->resize_h = 0;
            sim_window_hosting_resize(w->view.id, width, height);
        }
        if (w->modern) modern_game_view_pump();
    }
}

int native_windows_init(Host *host, SDL_Window *root)
{
    if (host == NULL || root == NULL || !sim_window_hosting_enabled()) return 0;
    memset(&n, 0, sizeof(n));
    n.host = host;
    n.root = root;
    n.scale = host_window_scale(host);
    n.count = sim_window_hosting_count();
    n.active = 1;
    /* Showing or raising a game window must not take activation: a prox menu
     * opens while the button is still held in another window, and activation
     * would end that drag. Keys reach the game from any SimAnt window. */
    SDL_SetHint(SDL_HINT_WINDOW_ACTIVATE_WHEN_SHOWN, "0");
    SDL_SetHint(SDL_HINT_WINDOW_ACTIVATE_WHEN_RAISED, "0");
    sim_window_hosting_set_pump(pump);
    /* The overview indicator shows the modern Game Window's area. */
    if (sim_window_hosting_is_hosted(0)) sim_window_hosting_own_map_cursor(1);
    if (!native_menu_init(root))
        fprintf(stderr, "Native menu bar unavailable (no native main window)\n");
    return 1;
}

void native_windows_shutdown(void)
{
    unsigned i;
    sim_window_hosting_set_pump(NULL);
    sim_window_hosting_own_map_cursor(0);
    modern_game_view_shutdown();
    for (i = 0; i < n.count; ++i) destroy_surface(&n.windows[i].surface);
    for (i = 0; i < POPUP_DEPTH; ++i) destroy_surface(&n.popups[i].surface);
    memset(&n, 0, sizeof(n));
}

/* ---- geometry ---- */

static int strip_of(const SimHostedWindowView *view)
{
    if (view->drag_bottom <= view->drag_top || view->drag_top < view->top_y ||
        view->drag_bottom >= view->bottom)
        return 0;
    return view->drag_bottom - view->top_y;
}

static void client_size(const NativeWindow *w, int *width, int *height)
{
    *width = w->surface.width * n.scale;
    *height = w->surface.height * n.scale;
    if (w->modern) SDL_GetWindowSize(w->surface.window, width, height);
}

/* The Game Window's map area in client pixels: editTileRect's insets from the
 * logical client edges kept, the remainder of the native client filled. It
 * may start above the client: editTileRect's first row lies under the title
 * strip that the native caption replaces, as in the hosted view. */
static int map_area(const NativeWindow *w, SDL_FRect *area)
{
    ModernWorldView v;
    int cw, ch;
    if (!w->modern || !w->view.open) return 0;
    modern_world_view(&v);
    if (v.view_rect.right <= v.view_rect.left || v.view_rect.bottom <= v.view_rect.top ||
        v.view_rect.right > w->view.right || v.view_rect.bottom > w->view.bottom ||
        v.view_rect.left < w->view.left || v.view_rect.top < w->view.top_y)
        return 0;
    client_size(w, &cw, &ch);
    area->x = (float)((v.view_rect.left - w->view.left) * n.scale);
    area->y = (float)((v.view_rect.top - w->view.top_y - w->strip) * n.scale);
    area->w = (float)(cw - (w->view.right - v.view_rect.right) * n.scale) - area->x;
    area->h = (float)(ch - (w->view.bottom - v.view_rect.bottom) * n.scale) - area->y;
    return area->w > 0 && area->h > 0;
}

static int in_area(const SDL_FRect *a, float x, float y)
{
    return x >= a->x && y >= a->y && x < a->x + a->w && y < a->y + a->h;
}

/* Client pixel of a logical screen point shown by window `w`. */
static void logical_to_client(const NativeWindow *w, int lx, int ly, int *cx, int *cy)
{
    SDL_FRect area;
    float vx, vy;
    if (map_area(w, &area) && modern_game_view_to_view((float)lx, (float)ly, &vx, &vy)) {
        *cx = (int)(area.x + vx);
        *cy = (int)(area.y + vy);
        return;
    }
    *cx = (lx - w->view.left) * n.scale;
    *cy = (ly - w->view.top_y - w->strip) * n.scale;
}

/* ---- presentation ---- */

static int size_surface(Surface *s, int width, int height)
{
    if (width == s->width && height == s->height && s->texture) return 1;
    SDL_DestroyTexture(s->texture);
    free(s->indexed);
    free(s->rgba);
    s->texture = SDL_CreateTexture(s->renderer, SDL_PIXELFORMAT_RGBA32,
                                   SDL_TEXTUREACCESS_STREAMING, width, height);
    s->indexed = malloc((size_t)width * (size_t)height);
    s->rgba = malloc((size_t)width * (size_t)height * 4u);
    s->width = width;
    s->height = height;
    return s->texture && s->indexed && s->rgba &&
           SDL_SetTextureScaleMode(s->texture, SDL_SCALEMODE_NEAREST);
}

/* GRectInvOutline(rect, 2) at the presentation: invert a 2-pixel frame. */
static void invert_outline(Surface *s, const ModernRect *r, int left, int top)
{
    int x, y;
    for (y = r->top; y < r->bottom; ++y)
        for (x = r->left; x < r->right; ++x) {
            int px = x - left, py = y - top;
            if (px < 0 || py < 0 || px >= s->width || py >= s->height) continue;
            if (y < r->top + 2 || y >= r->bottom - 2 || x < r->left + 2 || x >= r->right - 2)
                s->indexed[py * s->width + px] ^= 15u;
        }
}

static int upload_surface(Surface *s, const SimVgaPlanes *planes, int left, int top,
                          const HostPalette *palette, const ModernRect *indicator)
{
    int x, y;
    sim_vga_present_planes(planes, s->indexed, (size_t)s->width, left, top, s->width, s->height);
    if (indicator) invert_outline(s, indicator, left, top);
    for (y = 0; y < s->height; ++y)
        for (x = 0; x < s->width; ++x) {
            uint8_t index = s->indexed[y * s->width + x] & 15u;
            uint8_t *out = s->rgba + ((size_t)y * (size_t)s->width + (size_t)x) * 4u;
            memcpy(out, palette->rgb[index], 3);
            out[3] = 255;
        }
    return SDL_UpdateTexture(s->texture, NULL, s->rgba, s->width * 4);
}

/* Draw 1:1 at the global scale; a frame larger than the logical size (while
 * the user is still sizing it) shows the game's background, never a stretch. */
static int draw_surface(Surface *s, const SimVgaPlanes *planes, int left, int top,
                        const HostPalette *palette, const ModernRect *indicator)
{
    SDL_FRect target;
    target.x = target.y = 0;
    target.w = (float)(s->width * n.scale);
    target.h = (float)(s->height * n.scale);
    return upload_surface(s, planes, left, top, palette, indicator) &&
           SDL_SetRenderDrawColor(s->renderer, palette->rgb[7][0], palette->rgb[7][1],
                                  palette->rgb[7][2], 255) &&
           SDL_RenderClear(s->renderer) &&
           SDL_RenderTexture(s->renderer, s->texture, NULL, &target) &&
           SDL_RenderPresent(s->renderer);
}

/* The Game Window: hosted controls, then the modern map area over them. */
static int render_game_window(NativeWindow *w, const HostPalette *palette)
{
    Surface *s = &w->surface;
    SDL_FRect target, area;
    const uint8_t *fill;
    target.x = target.y = 0;
    target.w = (float)(s->width * n.scale);
    target.h = (float)(s->height * n.scale);
    if (!upload_surface(s, w->view.planes, w->view.left, w->view.top_y + w->strip, palette, NULL))
        return 0;
    /* Client beyond the logical window continues the control column's background. */
    fill = palette->rgb[s->indexed[(s->height > 4 ? s->height - 4 : 0) * s->width + (s->width > 10 ? 10 : 0)] & 15u];
    if (!SDL_SetRenderDrawColor(s->renderer, fill[0], fill[1], fill[2], 255) ||
        !SDL_RenderClear(s->renderer) ||
        !SDL_RenderTexture(s->renderer, s->texture, NULL, &target))
        return 0;
    return !map_area(w, &area) ||
           modern_game_view_render(s->renderer, &area, n.scale, palette, w->view.planes);
}

static void place(NativeWindow *w, const SimHostedWindowView *view, int strip);

static int ensure_window(NativeWindow *w, const SimHostedWindowView *view)
{
    int strip = strip_of(view);
    int width = view->right - view->left, height = view->bottom - view->top_y - strip;
    if (width <= 0 || height <= 0) return 1;
    if (w->surface.window == NULL) {
        SDL_WindowFlags flags = SDL_WINDOW_HIDDEN | ((view->flags & 8) ? SDL_WINDOW_RESIZABLE : 0) |
                                (strip ? 0 : SDL_WINDOW_BORDERLESS); /* Win16 WS_DLGFRAME */
        if (!SDL_CreateWindowAndRenderer(view->title, width * n.scale, height * n.scale,
                                         flags, &w->surface.window, &w->surface.renderer)) {
            fprintf(stderr, "Native window for %04X failed: %s\n",
                    (unsigned)(uint16_t)view->id, SDL_GetError());
            return 0;
        }
        /* Owned by the main window: above it, minimized with it, one taskbar
         * entry. Video drivers without ownership (headless) keep it top-level. */
        if (!SDL_SetWindowParent(w->surface.window, n.root))
            fprintf(stderr, "Native window for %04X is not owned: %s\n",
                    (unsigned)(uint16_t)view->id, SDL_GetError());
        w->modern = view->id == 0;
        w->strip = strip;
        place(w, view, strip);
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        fprintf(stderr, "Native window for %04X \"%s\": client %dx%d, scale %d, flags %04X%s\n",
                (unsigned)(uint16_t)view->id, view->title, width, height, n.scale,
                (unsigned)view->flags, w->modern ? ", modern map view" : "");
        if (view->flags & 8)
            SDL_SetWindowMinimumSize(w->surface.window, 48 * n.scale, 48 * n.scale);
    } else if (w->modern && (width != w->surface.width || height != w->surface.height)) {
        /* The Game Window's native size is the user's: a canonical size is
         * clamped to the logical screen, the modern view fills the rest. */
        if (!size_surface(&w->surface, width, height)) return 0;
        w->strip = strip;
    }
    if (strcmp(w->title, view->title)) {
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        SDL_SetWindowTitle(w->surface.window, w->title);
    }
    if (width != w->surface.width || height != w->surface.height || strip != w->strip) {
        if (!size_surface(&w->surface, width, height)) return 0;
        /* The game's result is the size. */
        SDL_SetWindowSize(w->surface.window, width * n.scale, height * n.scale);
        w->strip = strip;
    }
    return 1;
}

static NativeWindow *parent_at(int x, int y)
{
    NativeWindow *w = by_logical_id(sim_window_hosting_owner_at((int16_t)x, (int16_t)y));
    return w && w->shown && y >= w->view.top_y + w->strip ? w : NULL;
}

/* Desktop position of a logical point: relative to the shown native window
 * that logically holds it (another than `self`), else to the main window.
 * A window opened at a supplied point (object 0 anchored, e.g. a prox menu at
 * the mouse) follows the Game Window's map there; others keep their logical
 * placement. */
static void desktop_point(int lx, int ly, int16_t self, int at_point, int *dx, int *dy)
{
    unsigned i;
    NativeWindow *best = NULL;
    int wx = 0, wy = 0;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        if (!w->shown || w->view.id == self || lx < w->view.left || lx >= w->view.right ||
            ly < w->view.top_y + w->strip || ly >= w->view.bottom)
            continue;
        if (best == NULL || w->view.top) best = w;
    }
    if (best) {
        int cx, cy;
        SDL_GetWindowPosition(best->surface.window, &wx, &wy);
        if (at_point) logical_to_client(best, lx, ly, &cx, &cy);
        else {
            cx = (lx - best->view.left) * n.scale;
            cy = (ly - best->view.top_y - best->strip) * n.scale;
        }
        *dx = wx + cx;
        *dy = wy + cy;
    } else {
        SDL_GetWindowPosition(n.root, &wx, &wy);
        *dx = wx + lx * n.scale;
        *dy = wy + (ly - n.crop) * n.scale;
    }
}

static void place(NativeWindow *w, const SimHostedWindowView *view, int strip)
{
    int x, y;
    desktop_point(view->left, view->top_y + strip, view->id, view->anchored, &x, &y);
    SDL_SetWindowPosition(w->surface.window, x, y);
}

/* Save-under boxes become native popups over the window they appear on. */
static int sync_popups(void)
{
    SimHostedPopupView views[POPUP_DEPTH];
    unsigned i, count;
    if (sim_window_hosting_popup_serial() == n.popup_serial) return 1;
    n.popup_serial = sim_window_hosting_popup_serial();
    count = sim_window_hosting_popups(views, POPUP_DEPTH);
    for (i = 0; i < POPUP_DEPTH; ++i) {
        NativePopup *p = &n.popups[i];
        int same = i < count && p->surface.window && !memcmp(&p->view, &views[i], sizeof(views[i]));
        if (same) continue;
        destroy_surface(&p->surface);
        memset(&p->view, 0, sizeof(p->view));
        if (i < count) {
            const SimHostedPopupView *v = &views[i];
            int width = v->right - v->left, height = v->bottom - v->top;
            NativeWindow *owner = parent_at((v->left + v->right) / 2, (v->top + v->bottom) / 2);
            SDL_Window *parent = owner ? owner->surface.window : n.root;
            int ox, oy;
            if (width <= 0 || height <= 0) continue;
            /* A box opened at a point of the modern map stays at that point. */
            if (owner) logical_to_client(owner, v->left, v->top, &ox, &oy);
            else { ox = v->left * n.scale; oy = (v->top - n.crop) * n.scale; }
            p->view = *v;
            if (owner) SDL_GetWindowPosition(owner->surface.window, &p->x, &p->y);
            else SDL_GetWindowPosition(n.root, &p->x, &p->y);
            p->x += ox;
            p->y += oy;
            p->surface.window = SDL_CreatePopupWindow(parent, ox, oy,
                                                      width * n.scale, height * n.scale,
                                                      SDL_WINDOW_POPUP_MENU);
            if (p->surface.window == NULL &&
                (p->surface.window = SDL_CreateWindow("SimAnt", width * n.scale, height * n.scale,
                                                      SDL_WINDOW_BORDERLESS)) != NULL) {
                /* Drivers without popup windows (headless): a raised borderless one. */
                SDL_SetWindowPosition(p->surface.window, p->x, p->y);
                SDL_RaiseWindow(p->surface.window);
            }
            if (p->surface.window == NULL ||
                (p->surface.renderer = SDL_CreateRenderer(p->surface.window, NULL)) == NULL ||
                !size_surface(&p->surface, width, height)) {
                fprintf(stderr, "Native popup failed: %s\n", SDL_GetError());
                destroy_surface(&p->surface);
                continue;
            }
        }
    }
    n.popup_count = count;
    return 1;
}

int native_windows_present(const HostPalette *palette)
{
    unsigned i;
    ModernRect indicator;
    int has_indicator;
    if (!n.active) return 1;
    /* Win16 InitMenu: the native bar replaces the game-drawn one; the main
     * window then starts below the game's menu bar rows. */
    if (native_menu_sync() && !n.crop && fd_50F6_393C.bottom > 0 &&
        host_set_top_crop(n.host, fd_50F6_393C.bottom))
        n.crop = fd_50F6_393C.bottom;
    has_indicator = sim_window_hosting_map_cursor_shown() && modern_game_view_overview(&indicator);
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SimHostedWindowView view;
        int raise, okay;
        if (!sim_window_hosting_view(i, &view)) continue;
        if (!view.open) {
            if (w->shown) { SDL_HideWindow(w->surface.window); w->shown = 0; }
            w->close_pending = w->raise_pending = 0;
            w->resize_w = w->resize_h = 0;
            w->view = view;
            continue;
        }
        /* Win16 win_Open: BringWindowToTop; the logical top is the native top. */
        raise = !w->shown || (view.top && !w->view.top);
        if (!w->shown && w->surface.window && view.anchored) place(w, &view, w->strip);
        if (!ensure_window(w, &view)) {
            fprintf(stderr, "Native window %04X: %s\n", (unsigned)(uint16_t)view.id, SDL_GetError());
            return 0;
        }
        w->view = view;
        if (w->surface.width <= 0) continue;
        if (w->modern)
            okay = render_game_window(w, palette) && SDL_RenderPresent(w->surface.renderer);
        else
            okay = draw_surface(&w->surface, view.planes, view.left, view.top_y + w->strip, palette,
                                view.id == 0x100 && has_indicator ? &indicator : NULL);
        if (!okay) {
            fprintf(stderr, "Native window %04X present: %s\n", (unsigned)(uint16_t)view.id, SDL_GetError());
            return 0;
        }
        if (!w->shown) { SDL_ShowWindow(w->surface.window); w->shown = 1; }
        if (raise) SDL_RaiseWindow(w->surface.window);
    }
    if (!sync_popups()) return 0;
    for (i = 0; i < n.popup_count; ++i) {
        NativePopup *p = &n.popups[i];
        if (p->surface.window == NULL) continue;
        if (!draw_surface(&p->surface, p->view.planes, p->view.left, p->view.top, palette, NULL)) {
            fprintf(stderr, "Native popup present: %s\n", SDL_GetError());
            return 0;
        }
    }
    return 1;
}

void native_windows_set_smooth_zoom(int smooth) { modern_game_view_set_smooth(smooth); }

/* ---- input ---- */

typedef struct Origin {
    NativeWindow *window;
    int left, top, right, bottom;  /* logical client rect */
} Origin;

static int origin_of(SDL_WindowID id, Origin *o)
{
    unsigned i;
    memset(o, 0, sizeof(*o));
    for (i = 0; i < n.popup_count; ++i)
        if (n.popups[i].surface.window && SDL_GetWindowID(n.popups[i].surface.window) == id) {
            o->left = n.popups[i].view.left; o->top = n.popups[i].view.top;
            o->right = n.popups[i].view.right; o->bottom = n.popups[i].view.bottom;
            return 1;
        }
    for (i = 0; i < n.count; ++i)
        if (n.windows[i].surface.window && SDL_GetWindowID(n.windows[i].surface.window) == id) {
            NativeWindow *w = &n.windows[i];
            if (!w->view.open) return -1;
            o->window = w;
            o->left = w->view.left; o->top = w->view.top_y + w->strip;
            o->right = w->view.right; o->bottom = w->view.bottom;
            return 1;
        }
    return id == SDL_GetWindowID(n.root) ? 0 : -1;
}

static void clamp_logical(float *x, float *y)
{
    if (*x < 0) *x = 0;
    if (*y < 0) *y = 0;
    if (*x > 639) *x = 639;
    if (*y > 479) *y = 479;
}

/* Client pixels -> logical screen. In the Game Window's map area the modern
 * camera decides which world point is under the pointer; the game sees that
 * point where the canonical edit view shows it.
 *
 * f_00F8_01BE scrolls the edit map while the pointer is at a screen edge
 * (x <= 1, x >= g_3DB2-4, y < 1, y >= g_3DB4-4). The edit view's own window
 * is that screen here: its client edges are the edge zone. */
static int to_logical(const Origin *o, float cx, float cy, float *x, float *y, int pointer)
{
    SDL_FRect area;
    int inside = 1, cw, ch;
    if (o->window && map_area(o->window, &area) && in_area(&area, cx, cy)) {
        inside = modern_game_view_to_logical(cx - area.x, cy - area.y, x, y);
        /* Only the native client edges scroll (below): a point the canonical
         * edit view does not show must not land in the logical screen's edge
         * zone, so it is kept inside the edit view's own rectangle. */
        if (!inside) modern_game_view_clamp_logical(x, y);
        native_windows_root_pointer(x, y);
    } else {
        *x = (float)o->left + cx / (float)n.scale;
        *y = (float)o->top + cy / (float)n.scale;
    }
    clamp_logical(x, y);
    if (pointer && o->window && o->window->view.id == 0) {
        client_size(o->window, &cw, &ch);
        if (cx <= (float)n.scale) *x = 0;
        else if (cx >= (float)(cw - 2 * n.scale)) *x = 639;
        if (cy <= 0) *y = 0;
        else if (cy >= (float)(ch - 2 * n.scale)) *y = 479;
    }
    return inside;
}

/* The main window is only the desktop: no edge zone there. */
void native_windows_root_pointer(float *x, float *y)
{
    if (!n.active) return;
    if (*x < 2) *x = 2;
    if (*x > 635) *x = 635;
    if (*y < 1) *y = 1;
    if (*y > 475) *y = 475;
}

static int window_position(SDL_WindowID id, int *x, int *y)
{
    unsigned i;
    for (i = 0; i < n.popup_count; ++i)
        if (n.popups[i].surface.window && SDL_GetWindowID(n.popups[i].surface.window) == id) {
            *x = n.popups[i].x;
            *y = n.popups[i].y;
            return 1;
        }
    return SDL_GetWindowPosition(SDL_GetWindowFromID(id), x, y);
}

/* The SDL window under a desktop point: Windows' own answer (z-order, other
 * applications), else (headless) the logical stack's top-most native window. */
static SDL_WindowID window_under(int x, int y)
{
    unsigned i;
    NativeWindow *best = NULL;
#ifdef _WIN32
    POINT point;
    HWND hwnd;
    point.x = x;
    point.y = y;
    hwnd = WindowFromPoint(point);
    if (hwnd) hwnd = GetAncestor(hwnd, GA_ROOT);
    if (hwnd) {
        int count = 0;
        SDL_Window **windows = SDL_GetWindows(&count);
        SDL_WindowID found = 0;
        int k;
        for (k = 0; windows && k < count && !found; ++k)
            if (SDL_GetPointerProperty(SDL_GetWindowProperties(windows[k]),
                                       SDL_PROP_WINDOW_WIN32_HWND_POINTER, NULL) == hwnd)
                found = SDL_GetWindowID(windows[k]);
        SDL_free(windows);
        if (found) return found;
    }
#endif
    i = n.popup_count;
    while (i--) {
        NativePopup *p = &n.popups[i];
        if (p->surface.window && x >= p->x && y >= p->y &&
            x < p->x + p->surface.width * n.scale && y < p->y + p->surface.height * n.scale)
            return SDL_GetWindowID(p->surface.window);
    }
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        int wx, wy, cw, ch;
        if (!w->shown || !SDL_GetWindowPosition(w->surface.window, &wx, &wy)) continue;
        client_size(w, &cw, &ch);
        if (x < wx || y < wy || x >= wx + cw || y >= wy + ch) continue;
        if (best == NULL || w->view.top) best = w;
    }
    return best ? SDL_GetWindowID(best->surface.window) : SDL_GetWindowID(n.root);
}

int native_windows_request_close(int16_t id)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    if (w == NULL || !w->view.open) return 0;
    /* Win16: only windows with a system menu (+0x1C & 4) have a close box. */
    if (w->view.flags & 4) w->close_pending = 1;
    return 1;
}

int native_windows_request_resize(int16_t id, int width, int height)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    if (w == NULL || !w->view.open || !(w->view.flags & 8) || width <= 0 || height <= 0) return 0;
    /* The Game Window's native client is the user's size (a replayed request
     * sizes it as the frame would); the record follows, clamped by the game. */
    if (w->modern) {
        int cw, ch;
        client_size(w, &cw, &ch);
        if (cw != width * n.scale || ch != height * n.scale)
            SDL_SetWindowSize(w->surface.window, width * n.scale, height * n.scale);
    }
    w->resize_w = width;
    w->resize_h = height;
    return 1;
}

static NativeWindow *modal_top(void)
{
    NativeWindow *top = by_logical_id(sim_window_hosting_top());
    return top && top->view.open && (top->view.flags & 0x40) ? top : NULL;
}

/* Mouse input held back while the edit view scrolls to include a clicked
 * point of the modern map; it is delivered in order afterwards. */
static int defer(const SDL_Event *event)
{
    if (n.deferred.count == DEFERRED_DEPTH) {
        if (event->type == SDL_EVENT_MOUSE_MOTION) return 1;
        --n.deferred.count;  /* keep buttons: replace the newest motion */
    }
    n.deferred.events[n.deferred.count++] = *event;
    return 1;
}

int native_windows_take_deferred(SDL_Event *event)
{
    if (!n.active || n.deferred.count == 0) return 0;
    if (n.deferred.waiting) {
        if (!modern_game_view_include_settled() &&
            SDL_GetTicksNS() - n.deferred.since < DEFERRED_TIMEOUT_NS)
            return 0;
        n.deferred.waiting = 0;
    }
    *event = n.deferred.events[0];
    memmove(n.deferred.events, n.deferred.events + 1, (--n.deferred.count) * sizeof(SDL_Event));
    n.deferred.replaying = 1;
    return 1;
}

/* Wheel zoom and middle-button pan in the Game Window's map area; neither
 * reaches the game (the DOS game ignores both). Returns 1 when consumed. */
static int modern_navigation(SDL_Event *event)
{
    unsigned i;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SDL_FRect area;
        SDL_WindowID id;
        float x, y;
        if (!w->modern || !w->shown || !map_area(w, &area)) continue;
        id = SDL_GetWindowID(w->surface.window);
        if (event->type == SDL_EVENT_MOUSE_WHEEL && event->wheel.windowID == id) {
            x = event->wheel.mouse_x; y = event->wheel.mouse_y;
            if (!in_area(&area, x, y)) return 1;
            modern_game_view_wheel(x - area.x, y - area.y,
                                   event->wheel.direction == SDL_MOUSEWHEEL_FLIPPED ? -event->wheel.y : event->wheel.y);
            return 1;
        }
        if ((event->type == SDL_EVENT_MOUSE_BUTTON_DOWN || event->type == SDL_EVENT_MOUSE_BUTTON_UP) &&
            event->button.button == SDL_BUTTON_MIDDLE && event->button.windowID == id) {
            modern_game_view_pan(event->type == SDL_EVENT_MOUSE_BUTTON_DOWN && in_area(&area, event->button.x, event->button.y) ? 1 : -1,
                                 event->button.x - area.x, event->button.y - area.y);
            return 1;
        }
        if (event->type == SDL_EVENT_MOUSE_MOTION && event->motion.windowID == id)
            modern_game_view_pan(0, event->motion.x - area.x, event->motion.y - area.y);
    }
    return 0;
}

int native_windows_translate(SDL_Event *event)
{
    Origin o;
    SDL_WindowID id;
    SDL_Event raw = *event;
    int kind, replaying = n.deferred.replaying;
    float cx, cy;
    if (!n.active) return 0;
    n.deferred.replaying = 0;
    if (modern_navigation(event)) return -1;
    if (event->type == SDL_EVENT_MOUSE_MOTION) id = event->motion.windowID;
    else if (event->type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
             event->type == SDL_EVENT_MOUSE_BUTTON_UP) id = event->button.windowID;
    else if (event->type == SDL_EVENT_WINDOW_CLOSE_REQUESTED ||
             event->type == SDL_EVENT_WINDOW_RESIZED) {
        if (origin_of(event->window.windowID, &o) <= 0 || o.window == NULL) return 0;
        if (event->type == SDL_EVENT_WINDOW_CLOSE_REQUESTED)
            native_windows_request_close(o.window->view.id);
        else if (event->window.data1 != o.window->surface.width * n.scale ||
                 event->window.data2 != o.window->surface.height * n.scale)
            /* Win16 WM_SIZE: the record follows the native client (the
             * Game Window's canonical size stops at the logical screen). */
            native_windows_request_resize(o.window->view.id, event->window.data1 / n.scale,
                                          event->window.data2 / n.scale);
        return 1;
    } else if (event->type == SDL_EVENT_WINDOW_MOUSE_LEAVE) {
        /* Leaving the edit window ends edge scrolling: the game sees the
         * pointer back inside, away from every edge. */
        SDL_WindowID left_window = event->window.windowID;
        SDL_FRect area;
        if (origin_of(left_window, &o) <= 0 || o.window == NULL || o.window->view.id != 0 ||
            (SDL_GetGlobalMouseState(NULL, NULL) & SDL_BUTTON_LMASK))
            return 0;
        memset(event, 0, sizeof(*event));
        event->type = SDL_EVENT_MOUSE_MOTION;
        event->motion.windowID = left_window;
        if (map_area(o.window, &area)) {
            event->motion.x = area.x + area.w / 2;
            event->motion.y = area.y + area.h / 2;
        } else {
            event->motion.x = (float)(o.window->surface.width * n.scale / 2);
            event->motion.y = (float)(o.window->surface.height * n.scale / 2);
        }
        id = left_window;
        raw = *event;
    } else return 0;
    if (n.deferred.count && !replaying) {
        defer(&raw);
        return -1;
    }
    {
        /* A held button keeps delivering to the window where it was pressed
         * (capture); map through the native window actually under the pointer. */
        float *ex = event->type == SDL_EVENT_MOUSE_MOTION ? &event->motion.x : &event->button.x;
        float *ey = event->type == SDL_EVENT_MOUSE_MOTION ? &event->motion.y : &event->button.y;
        int wx, wy;
        SDL_WindowID under;
        if (event->type != SDL_EVENT_MOUSE_BUTTON_DOWN && window_position(id, &wx, &wy) &&
            (under = window_under(wx + (int)*ex, wy + (int)*ey)) != id &&
            origin_of(under, &o) > 0 && window_position(under, &wx, &wy) == 1) {
            int gx = 0, gy = 0;
            window_position(id, &gx, &gy);
            *ex += (float)(gx - wx);
            *ey += (float)(gy - wy);
            id = under;
        }
    }
    kind = origin_of(id, &o);
    if (kind <= 0) return kind;   /* main window (0) or a window being torn down */
    if (event->type == SDL_EVENT_MOUSE_MOTION) {
        SDL_FRect area;
        cx = event->motion.x; cy = event->motion.y;
        if (o.window && map_area(o.window, &area) && in_area(&area, cx, cy))
            modern_game_view_hold_move(cx - area.x, cy - area.y);
        to_logical(&o, cx, cy, &event->motion.x, &event->motion.y, 1);
        return 1;
    }
    cx = event->button.x; cy = event->button.y;
    if (o.window) {
        NativeWindow *w = o.window, *modal = modal_top();
        SDL_FRect area;
        if (event->type == SDL_EVENT_MOUSE_BUTTON_DOWN && !w->view.top) {
            /* Win16 WM_MOUSEACTIVATE: raise and eat; with a modal window on
             * top the click is ignored and the modal window comes forward. */
            w->eaten_button = event->button.button;
            if (modal) SDL_RaiseWindow(modal->surface.window);
            else w->raise_pending = 1;
            return -1;
        }
        if (event->type == SDL_EVENT_MOUSE_BUTTON_UP && w->eaten_button == event->button.button) {
            w->eaten_button = 0;
            return -1;
        }
        if (map_area(w, &area) && in_area(&area, cx, cy)) {
            float lx, ly;
            if (event->type == SDL_EVENT_MOUSE_BUTTON_DOWN && !replaying &&
                !modern_game_view_to_logical(cx - area.x, cy - area.y, &lx, &ly)) {
                if (!modern_game_view_in_world(cx - area.x, cy - area.y)) {
                    w->eaten_button = event->button.button;   /* outside the world */
                    return -1;
                }
                /* The edit view does not show this tile: scroll it there in the
                 * pump, then deliver the click where it shows it. */
                modern_game_view_request_include(cx - area.x, cy - area.y);
                n.deferred.waiting = 1;
                n.deferred.since = SDL_GetTicksNS();
                defer(&raw);
                return -1;
            }
            if (event->button.button == SDL_BUTTON_LEFT)
                modern_game_view_hold(event->type == SDL_EVENT_MOUSE_BUTTON_DOWN, cx - area.x, cy - area.y);
        } else if (event->type == SDL_EVENT_MOUSE_BUTTON_UP && event->button.button == SDL_BUTTON_LEFT)
            modern_game_view_hold(0, 0, 0);
    }
    to_logical(&o, cx, cy, &event->button.x, &event->button.y, 0);
    return 1;
}

int native_windows_filter_root(SDL_Event *event)
{
    int16_t owner;
    if (!n.active || (event->type != SDL_EVENT_MOUSE_BUTTON_DOWN &&
                      event->type != SDL_EVENT_MOUSE_BUTTON_UP))
        return 0;
    if (event->type == SDL_EVENT_MOUSE_BUTTON_UP) {
        if (n.root_dropped_button != event->button.button) return 0;
        n.root_dropped_button = 0;
        return -1;
    }
    owner = sim_window_hosting_owner_at((int16_t)event->button.x, (int16_t)event->button.y);
    if (owner == (int16_t)(uint16_t)0x8000 || !sim_window_hosting_is_hosted(owner)) return 0;
    n.root_dropped_button = event->button.button;
    return -1;
}

int native_windows_pointer(float *x, float *y)
{
    Origin o;
    float gx, gy;
    int wx, wy;
    SDL_WindowID under;
    if (!n.active) return 0;
    SDL_GetGlobalMouseState(&gx, &gy);
    under = window_under((int)gx, (int)gy);
    if (origin_of(under, &o) <= 0 || !window_position(under, &wx, &wy)) return 0;
    to_logical(&o, gx - (float)wx, gy - (float)wy, x, y, 1);
    return 1;
}

static int save_rgba(const uint8_t *rgba, int width, int height, const char *path)
{
    SDL_Surface *surface;
    int okay;
    if (rgba == NULL) return 1;
    surface = SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_RGBA32, (void *)rgba, width * 4);
    if (surface == NULL) return 0;
    okay = SDL_SaveBMP(surface, path);
    SDL_DestroySurface(surface);
    return okay;
}

/* The Game Window as presented, in logical pixels like every other window
 * (client / scale; exact at the default zoom), plus its hosted canonical view
 * as <path>.hosted.bmp. */
static int save_game_window(NativeWindow *w, const char *path)
{
    HostPalette palette;
    SDL_Surface *frame, *scaled;
    char hosted[1024];
    int okay;
    if (!host_presented_palette(n.host, &palette) || !render_game_window(w, &palette) ||
        (frame = SDL_RenderReadPixels(w->surface.renderer, NULL)) == NULL)
        return 0;
    scaled = SDL_ScaleSurface(frame, frame->w / n.scale, frame->h / n.scale, SDL_SCALEMODE_NEAREST);
    SDL_DestroySurface(frame);
    if (scaled == NULL) return 0;
    frame = SDL_ConvertSurface(scaled, SDL_PIXELFORMAT_RGBA32);
    SDL_DestroySurface(scaled);
    if (frame == NULL) return 0;
    okay = SDL_SaveBMP(frame, path);
    SDL_DestroySurface(frame);
    SDL_RenderPresent(w->surface.renderer);
    SDL_snprintf(hosted, sizeof(hosted), "%s.hosted.bmp", path);
    return okay && save_rgba(w->surface.rgba, w->surface.width, w->surface.height, hosted);
}

int native_windows_save_frames(const char *base_path)
{
    unsigned i;
    char path[1024];
    if (!n.active) return 1;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        if (!w->shown) continue;
        SDL_snprintf(path, sizeof(path), "%s.%04X.bmp", base_path, (unsigned)(uint16_t)w->view.id);
        if (!(w->modern ? save_game_window(w, path)
                        : save_rgba(w->surface.rgba, w->surface.width, w->surface.height, path)))
            return 0;
    }
    for (i = 0; i < n.popup_count; ++i) {
        SDL_snprintf(path, sizeof(path), "%s.popup%u.bmp", base_path, i);
        if (!save_rgba(n.popups[i].surface.rgba, n.popups[i].surface.width,
                       n.popups[i].surface.height, path))
            return 0;
    }
    return 1;
}

/* Replay/test input: a pointer transition at window-local client coordinates
 * of hosted window `id` (logical pixels: multiplied by the scale), through
 * SDL's queue like a real event. */
int native_windows_push_pointer(int16_t id, const HostEvent *event)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    SDL_Event raw = {0};
    float x, y;
    if (w == NULL || w->surface.window == NULL || event == NULL) return 0;
    x = (float)(event->x * n.scale);
    y = (float)(event->y * n.scale);
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        raw.type = SDL_EVENT_MOUSE_MOTION;
        raw.motion.windowID = SDL_GetWindowID(w->surface.window);
        raw.motion.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.motion.x = x;
        raw.motion.y = y;
    } else if (event->kind == HOST_EVENT_MOUSE_DOWN || event->kind == HOST_EVENT_MOUSE_UP) {
        raw.type = event->kind == HOST_EVENT_MOUSE_DOWN ?
                   SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
        raw.button.windowID = SDL_GetWindowID(w->surface.window);
        raw.button.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.button.button = event->button;
        raw.button.down = event->kind == HOST_EVENT_MOUSE_DOWN;
        raw.button.clicks = 1;
        raw.button.x = x;
        raw.button.y = y;
    } else return 0;
    return SDL_PushEvent(&raw);
}

/* Replay/test: mouse wheel over hosted window `id` at client point (x, y). */
int native_windows_push_wheel(int16_t id, int x, int y, float steps)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    SDL_Event raw = {0};
    if (w == NULL || w->surface.window == NULL) return 0;
    raw.type = SDL_EVENT_MOUSE_WHEEL;
    raw.wheel.windowID = SDL_GetWindowID(w->surface.window);
    raw.wheel.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
    raw.wheel.y = steps;
    raw.wheel.direction = SDL_MOUSEWHEEL_NORMAL;
    raw.wheel.mouse_x = (float)(x * n.scale);
    raw.wheel.mouse_y = (float)(y * n.scale);
    return SDL_PushEvent(&raw);
}

/* Replay/test: set the native client size of hosted window `id` (logical
 * pixels), as the user's sizing frame does. */
int native_windows_push_native_size(int16_t id, int width, int height)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    if (w == NULL || w->surface.window == NULL) return 0;
    return SDL_SetWindowSize(w->surface.window, width * n.scale, height * n.scale);
}

int native_windows_event_origin(SDL_WindowID window, int16_t *id, int16_t *left, int16_t *top)
{
    Origin o;
    if (!n.active || origin_of(window, &o) <= 0 || o.window == NULL) return 0;
    *id = o.window->view.id;
    *left = (int16_t)o.left;
    *top = (int16_t)o.top;
    return 1;
}
