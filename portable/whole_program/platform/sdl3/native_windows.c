#include "native_windows.h"
#include "../window_hosting.h"
#include "host_modes.h"
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
 * the game's event pump (window_hosting.h), like Win16 message dispatch. */

enum { POPUP_DEPTH = 4 };

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
    if (!native_menu_init(root))
        fprintf(stderr, "Native menu bar unavailable (no native main window)\n");
    return 1;
}

void native_windows_shutdown(void)
{
    unsigned i;
    sim_window_hosting_set_pump(NULL);
    for (i = 0; i < n.count; ++i) destroy_surface(&n.windows[i].surface);
    for (i = 0; i < POPUP_DEPTH; ++i) destroy_surface(&n.popups[i].surface);
    memset(&n, 0, sizeof(n));
}

/* ---- presentation ---- */

static int strip_of(const SimHostedWindowView *view)
{
    if (view->drag_bottom <= view->drag_top || view->drag_top < view->top_y ||
        view->drag_bottom >= view->bottom)
        return 0;
    return view->drag_bottom - view->top_y;
}

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

/* Draw 1:1 at the global scale; a frame larger than the logical size (while
 * the user is still sizing it) shows the game's background, never a stretch. */
static int draw_surface(Surface *s, const SimVgaPlanes *planes, int left, int top,
                        const HostPalette *palette)
{
    SDL_FRect target;
    int x, y;
    sim_vga_present_planes(planes, s->indexed, (size_t)s->width, left, top, s->width, s->height);
    for (y = 0; y < s->height; ++y)
        for (x = 0; x < s->width; ++x) {
            uint8_t index = s->indexed[y * s->width + x] & 15u;
            uint8_t *out = s->rgba + ((size_t)y * (size_t)s->width + (size_t)x) * 4u;
            memcpy(out, palette->rgb[index], 3);
            out[3] = 255;
        }
    target.x = target.y = 0;
    target.w = (float)(s->width * n.scale);
    target.h = (float)(s->height * n.scale);
    return SDL_UpdateTexture(s->texture, NULL, s->rgba, s->width * 4) &&
           SDL_SetRenderDrawColor(s->renderer, palette->rgb[7][0], palette->rgb[7][1],
                                  palette->rgb[7][2], 255) &&
           SDL_RenderClear(s->renderer) &&
           SDL_RenderTexture(s->renderer, s->texture, NULL, &target) &&
           SDL_RenderPresent(s->renderer);
}

static void place(NativeWindow *w, const SimHostedWindowView *view, int strip);

static int ensure_window(NativeWindow *w, const SimHostedWindowView *view)
{
    int strip = strip_of(view);
    int width = view->right - view->left, height = view->bottom - view->top_y - strip;
    if (width <= 0 || height <= 0) return 1;
    if (w->surface.window == NULL) {
        int rx = 0, ry = 0;
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
        (void)rx; (void)ry;
        w->strip = strip;
        place(w, view, strip);
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        fprintf(stderr, "Native window for %04X \"%s\": client %dx%d, scale %d, flags %04X\n",
                (unsigned)(uint16_t)view->id, view->title, width, height, n.scale,
                (unsigned)view->flags);
    }
    if (strcmp(w->title, view->title)) {
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        SDL_SetWindowTitle(w->surface.window, w->title);
    }
    if (width != w->surface.width || height != w->surface.height || strip != w->strip) {
        if (!size_surface(&w->surface, width, height)) return 0;
        /* The game's result is the size. */
        SDL_SetWindowSize(w->surface.window, width * n.scale, height * n.scale);
        if (view->flags & 8)
            SDL_SetWindowMinimumSize(w->surface.window, 48 * n.scale, 48 * n.scale);
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
 * that logically holds it (another than `self`), else to the main window. */
static void desktop_point(int lx, int ly, int16_t self, int *dx, int *dy)
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
        SDL_GetWindowPosition(best->surface.window, &wx, &wy);
        *dx = wx + (lx - best->view.left) * n.scale;
        *dy = wy + (ly - best->view.top_y - best->strip) * n.scale;
    } else {
        SDL_GetWindowPosition(n.root, &wx, &wy);
        *dx = wx + lx * n.scale;
        *dy = wy + (ly - n.crop) * n.scale;
    }
}

static void place(NativeWindow *w, const SimHostedWindowView *view, int strip)
{
    int x, y;
    desktop_point(view->left, view->top_y + strip, view->id, &x, &y);
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
            int ox = owner ? v->left - owner->view.left : v->left;
            int oy = owner ? v->top - (owner->view.top_y + owner->strip) : v->top - n.crop;
            if (width <= 0 || height <= 0) continue;
            p->view = *v;
            if (owner) SDL_GetWindowPosition(owner->surface.window, &p->x, &p->y);
            else SDL_GetWindowPosition(n.root, &p->x, &p->y);
            p->x += ox * n.scale;
            p->y += oy * n.scale;
            p->surface.window = SDL_CreatePopupWindow(parent, ox * n.scale, oy * n.scale,
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
    if (!n.active) return 1;
    /* Win16 InitMenu: the native bar replaces the game-drawn one; the main
     * window then starts below the game's menu bar rows. */
    if (native_menu_sync() && !n.crop && fd_50F6_393C.bottom > 0 &&
        host_set_top_crop(n.host, fd_50F6_393C.bottom))
        n.crop = fd_50F6_393C.bottom;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SimHostedWindowView view;
        int raise;
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
        if (!draw_surface(&w->surface, view.planes, view.left, view.top_y + w->strip, palette)) {
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
        if (!draw_surface(&p->surface, p->view.planes, p->view.left, p->view.top, palette)) {
            fprintf(stderr, "Native popup present: %s\n", SDL_GetError());
            return 0;
        }
    }
    return 1;
}

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

static void to_logical(const Origin *o, float *x, float *y)
{
    *x = (float)o->left + *x / (float)n.scale;
    *y = (float)o->top + *y / (float)n.scale;
    if (*x < 0) *x = 0;
    if (*y < 0) *y = 0;
    if (*x > 639) *x = 639;
    if (*y > 479) *y = 479;
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
        int wx, wy;
        if (!w->shown || !SDL_GetWindowPosition(w->surface.window, &wx, &wy) ||
            x < wx || y < wy || x >= wx + w->surface.width * n.scale ||
            y >= wy + w->surface.height * n.scale)
            continue;
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
    w->resize_w = width;
    w->resize_h = height;
    return 1;
}

static NativeWindow *modal_top(void)
{
    NativeWindow *top = by_logical_id(sim_window_hosting_top());
    return top && top->view.open && (top->view.flags & 0x40) ? top : NULL;
}

int native_windows_translate(SDL_Event *event)
{
    Origin o;
    SDL_WindowID id;
    int kind;
    if (!n.active) return 0;
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
            native_windows_request_resize(o.window->view.id, event->window.data1 / n.scale,
                                          event->window.data2 / n.scale);
        return 1;
    } else return 0;
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
        to_logical(&o, &event->motion.x, &event->motion.y);
        return 1;
    }
    to_logical(&o, &event->button.x, &event->button.y);
    if (o.window) {
        NativeWindow *w = o.window, *modal = modal_top();
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
    }
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
    *x = gx - (float)wx;
    *y = gy - (float)wy;
    to_logical(&o, x, y);
    return 1;
}

static int save_surface(const Surface *s, const char *path)
{
    SDL_Surface *surface;
    int okay;
    if (s->rgba == NULL) return 1;
    surface = SDL_CreateSurfaceFrom(s->width, s->height, SDL_PIXELFORMAT_RGBA32, s->rgba, s->width * 4);
    if (surface == NULL) return 0;
    okay = SDL_SaveBMP(surface, path);
    SDL_DestroySurface(surface);
    return okay;
}

int native_windows_save_frames(const char *base_path)
{
    unsigned i;
    char path[1024];
    if (!n.active) return 1;
    for (i = 0; i < n.count; ++i) {
        if (!n.windows[i].shown) continue;
        SDL_snprintf(path, sizeof(path), "%s.%04X.bmp", base_path, (unsigned)(uint16_t)n.windows[i].view.id);
        if (!save_surface(&n.windows[i].surface, path)) return 0;
    }
    for (i = 0; i < n.popup_count; ++i) {
        SDL_snprintf(path, sizeof(path), "%s.popup%u.bmp", base_path, i);
        if (!save_surface(&n.popups[i].surface, path)) return 0;
    }
    return 1;
}

/* Replay/test input: a pointer transition at window-local logical client
 * coordinates of hosted window `id`, through SDL's queue like a real event. */
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

int native_windows_event_origin(SDL_WindowID window, int16_t *id, int16_t *left, int16_t *top)
{
    Origin o;
    if (!n.active || origin_of(window, &o) <= 0 || o.window == NULL) return 0;
    *id = o.window->view.id;
    *left = (int16_t)o.left;
    *top = (int16_t)o.top;
    return 1;
}
