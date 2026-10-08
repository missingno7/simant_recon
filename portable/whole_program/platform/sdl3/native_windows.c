#include "native_windows.h"
#include "../window_hosting.h"
#include "host_modes.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Win16 win_Open builds each logical window as a real window: the record's
 * 18-px title strip becomes the native caption, flag 4 gives the close box
 * (WM_CLOSE -> win_Close), flag 8 a sizing frame (WM_SIZE -> record rect,
 * win_Recalc). Here every hosted window is an owned top-level SDL window; the
 * close box and the sizing frame act through the game's own chrome objects
 * (close box 0xf083, resize icon 0xf084), so window state stays canonical. */

enum { SYNTHETIC_CAPACITY = 16 };

typedef struct NativeWindow {
    SimHostedWindowView view;      /* last presented logical state */
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint8_t *indexed, *rgba;
    int width, height;             /* logical client size (rect minus title strip) */
    int strip;                     /* title strip replaced by the native caption */
    int shown;
    char title[64];
    Uint8 raise_button;            /* button whose down was turned into a raise */
    int16_t raise_x, raise_y;
    int close_pending;
    int resize_w, resize_h;        /* requested logical client size, 0: none */
} NativeWindow;

typedef struct Synthetic {
    uint64_t due_ns;
    HostEvent event;
} Synthetic;

static struct {
    int active;
    int scale;
    Host *host;
    SDL_Window *root;
    NativeWindow windows[SIM_HOSTING_SLOTS];
    unsigned count;
    Uint8 root_dropped_button;
    Synthetic synthetic[SYNTHETIC_CAPACITY];
    unsigned synthetic_count;
} n;

int native_windows_active(void) { return n.active; }
int native_windows_scale(void) { return n.scale ? n.scale : 1; }

int native_windows_init(Host *host, SDL_Window *root)
{
    if (host == NULL || root == NULL || !sim_window_hosting_enabled()) return 0;
    memset(&n, 0, sizeof(n));
    n.host = host;
    n.root = root;
    n.scale = host_window_scale(host);
    n.count = sim_window_hosting_count();
    n.active = 1;
    return 1;
}

void native_windows_shutdown(void)
{
    unsigned i;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SDL_DestroyTexture(w->texture);
        SDL_DestroyRenderer(w->renderer);
        SDL_DestroyWindow(w->window);
        free(w->indexed);
        free(w->rgba);
    }
    memset(&n, 0, sizeof(n));
}

static NativeWindow *by_sdl_id(SDL_WindowID id)
{
    unsigned i;
    for (i = 0; i < n.count; ++i)
        if (n.windows[i].window && SDL_GetWindowID(n.windows[i].window) == id)
            return &n.windows[i];
    return NULL;
}

static NativeWindow *by_logical_id(int16_t id)
{
    unsigned i;
    for (i = 0; i < n.count; ++i)
        if (n.windows[i].view.id == (int16_t)(id & 0xff00)) return &n.windows[i];
    return NULL;
}

/* ---- synthetic chrome input, delivered through host_poll_event in order ---- */

static void synthesize(uint64_t delay_ms, HostEventKind kind, int x, int y)
{
    Synthetic *e;
    uint64_t base = n.synthetic_count ? n.synthetic[n.synthetic_count - 1].due_ns : host_time_ns();
    if (n.synthetic_count == SYNTHETIC_CAPACITY) return;
    e = &n.synthetic[n.synthetic_count++];
    memset(e, 0, sizeof(*e));
    e->due_ns = base + delay_ms * 1000000u;
    e->event.kind = kind;
    e->event.button = kind == HOST_EVENT_MOUSE_MOVE ? 0 : SDL_BUTTON_LEFT;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x > 636) x = 636;
    if (y > 476) y = 476;
    e->event.x = (int16_t)x;
    e->event.y = (int16_t)y;
}

int native_windows_next_synthetic(HostEvent *event)
{
    if (!n.active || n.synthetic_count == 0 || host_time_ns() < n.synthetic[0].due_ns) return 0;
    *event = n.synthetic[0].event;
    memmove(n.synthetic, n.synthetic + 1, (n.synthetic_count - 1) * sizeof(n.synthetic[0]));
    --n.synthetic_count;
    return 1;
}

static void click(uint64_t delay_ms, int x, int y)
{
    synthesize(delay_ms, HOST_EVENT_MOUSE_MOVE, x, y);
    synthesize(30, HOST_EVENT_MOUSE_DOWN, x, y);
    synthesize(60, HOST_EVENT_MOUSE_UP, x, y);
}

/* DOS f_218D_0451 / Win16 WM_MOUSEACTIVATE: a click where the window is on
 * top raises it; the click itself is eaten. */
static void raise_point(NativeWindow *w, int16_t *x, int16_t *y)
{
    if (!sim_window_hosting_visible_point(w->view.id, x, y)) {
        *x = (int16_t)((w->view.left + w->view.right) / 2);
        *y = (int16_t)((w->view.top_y + w->view.bottom) / 2);
    }
}

static void run_chrome_actions(NativeWindow *w)
{
    int16_t x, y;
    if (n.synthetic_count || (!w->close_pending && !w->resize_w)) return;
    if (!host_virtual_clock_enabled() && (SDL_GetGlobalMouseState(NULL, NULL) & SDL_BUTTON_LMASK))
        return; /* the user is still dragging the frame */
    if (!w->view.top) {
        raise_point(w, &x, &y);
        click(0, x, y);
        return;
    }
    if (w->close_pending) {
        w->close_pending = 0;
        /* f_2505_06B9: close box 0x64 at the chrome inset of the top-left corner. */
        click(0, w->view.left + w->view.margin + 4, w->view.top_y + w->view.margin + 4);
        return;
    }
    {
        /* f_2505_06B9: resize icon 0x70 in the bottom-right inset corner;
         * o26_39C7_0671 moves the corner with the pointer while held. */
        int sx = w->view.right - w->view.margin - 4, sy = w->view.bottom - w->view.margin - 4;
        int dx = w->resize_w - w->width, dy = w->resize_h - w->height;
        w->resize_w = w->resize_h = 0;
        if (!dx && !dy) return;
        synthesize(0, HOST_EVENT_MOUSE_MOVE, sx, sy);
        synthesize(30, HOST_EVENT_MOUSE_DOWN, sx, sy);
        synthesize(150, HOST_EVENT_MOUSE_MOVE, sx + dx / 2, sy + dy / 2);
        synthesize(150, HOST_EVENT_MOUSE_MOVE, sx + dx, sy + dy);
        synthesize(200, HOST_EVENT_MOUSE_UP, sx + dx, sy + dy);
    }
}

/* ---- presentation ---- */

static int strip_of(const SimHostedWindowView *view)
{
    if (view->drag_bottom <= view->drag_top || view->drag_top < view->top_y ||
        view->drag_bottom >= view->bottom)
        return 0;
    return view->drag_bottom - view->top_y;
}

static int ensure_window(NativeWindow *w, const SimHostedWindowView *view)
{
    int strip = strip_of(view);
    int width = view->right - view->left, height = view->bottom - view->top_y - strip;
    if (width <= 0 || height <= 0) return 1;
    if (w->window == NULL) {
        int rx = 0, ry = 0;
        SDL_WindowFlags flags = SDL_WINDOW_HIDDEN | ((view->flags & 8) ? SDL_WINDOW_RESIZABLE : 0);
        if (!SDL_CreateWindowAndRenderer(view->title, width * n.scale, height * n.scale,
                                         flags, &w->window, &w->renderer)) {
            fprintf(stderr, "Native window for %04X failed: %s\n",
                    (unsigned)(uint16_t)view->id, SDL_GetError());
            return 0;
        }
        /* Owned by the main window: above it, minimized with it, one taskbar
         * entry. Video drivers without ownership (headless) keep it top-level. */
        if (!SDL_SetWindowParent(w->window, n.root))
            fprintf(stderr, "Native window for %04X is not owned: %s\n",
                    (unsigned)(uint16_t)view->id, SDL_GetError());
        SDL_GetWindowPosition(n.root, &rx, &ry);
        SDL_SetWindowPosition(w->window, rx + view->left * n.scale,
                              ry + (view->top_y + strip) * n.scale);
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        fprintf(stderr, "Native window for %04X \"%s\": client %dx%d, scale %d, flags %04X\n",
                (unsigned)(uint16_t)view->id, view->title, width, height, n.scale,
                (unsigned)view->flags);
    }
    if (strcmp(w->title, view->title)) {
        snprintf(w->title, sizeof(w->title), "%s", view->title);
        SDL_SetWindowTitle(w->window, w->title);
    }
    if (width != w->width || height != w->height || strip != w->strip) {
        SDL_DestroyTexture(w->texture);
        free(w->indexed);
        free(w->rgba);
        w->texture = SDL_CreateTexture(w->renderer, SDL_PIXELFORMAT_RGBA32,
                                       SDL_TEXTUREACCESS_STREAMING, width, height);
        w->indexed = malloc((size_t)width * (size_t)height);
        w->rgba = malloc((size_t)width * (size_t)height * 4u);
        if (w->texture == NULL || w->indexed == NULL || w->rgba == NULL ||
            !SDL_SetTextureScaleMode(w->texture, SDL_SCALEMODE_NEAREST) ||
            !SDL_SetRenderLogicalPresentation(w->renderer, width, height,
                                              SDL_LOGICAL_PRESENTATION_STRETCH))
            return 0;
        /* The game's result is the size (o26_39C7_022F constraints, grid). */
        SDL_SetWindowSize(w->window, width * n.scale, height * n.scale);
        if (view->flags & 8) {
            SDL_SetWindowMinimumSize(w->window, 48 * n.scale, 48 * n.scale);
            SDL_SetWindowMaximumSize(w->window, (640 - view->left) * n.scale,
                                     (480 - view->top_y - strip) * n.scale);
        }
        w->width = width;
        w->height = height;
        w->strip = strip;
    }
    return 1;
}

int native_windows_present(const HostPalette *palette)
{
    unsigned i;
    int x, y;
    if (!n.active) return 1;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SimHostedWindowView view;
        if (!sim_window_hosting_view(i, &view)) continue;
        if (!view.open) {
            if (w->shown) { SDL_HideWindow(w->window); w->shown = 0; }
            w->close_pending = 0;
            w->resize_w = w->resize_h = 0;
            w->view = view;
            continue;
        }
        if (!ensure_window(w, &view)) {
            fprintf(stderr, "Native window %04X: %s" "%c", (unsigned)(uint16_t)view.id, SDL_GetError(), 10);
            return 0;
        }
        w->view = view;
        if (w->width <= 0) continue;
        sim_vga_present_planes(view.planes, w->indexed, (size_t)w->width,
                               view.left, view.top_y + w->strip, w->width, w->height);
        for (y = 0; y < w->height; ++y)
            for (x = 0; x < w->width; ++x) {
                uint8_t index = w->indexed[y * w->width + x] & 15u;
                uint8_t *out = w->rgba + ((size_t)y * (size_t)w->width + (size_t)x) * 4u;
                memcpy(out, palette->rgb[index], 3);
                out[3] = 255;
            }
        if (!SDL_UpdateTexture(w->texture, NULL, w->rgba, w->width * 4) ||
            !SDL_RenderClear(w->renderer) ||
            !SDL_RenderTexture(w->renderer, w->texture, NULL, NULL) ||
            !SDL_RenderPresent(w->renderer)) {
            fprintf(stderr, "Native window %04X present: %s%c", (unsigned)(uint16_t)view.id, SDL_GetError(), 10);
            return 0;
        }
        if (!w->shown) { SDL_ShowWindow(w->window); w->shown = 1; }
        run_chrome_actions(w);
    }
    return 1;
}

/* ---- input ---- */

static void to_logical(NativeWindow *w, float *x, float *y)
{
    *x += (float)w->view.left;
    *y += (float)(w->view.top_y + w->strip);
    if (*x < w->view.left) *x = w->view.left;
    if (*y < w->view.top_y + w->strip) *y = (float)(w->view.top_y + w->strip);
    if (*x > w->view.right - 1) *x = (float)(w->view.right - 1);
    if (*y > w->view.bottom - 1) *y = (float)(w->view.bottom - 1);
}

int native_windows_request_close(int16_t id)
{
    NativeWindow *w = n.active ? by_logical_id(id) : NULL;
    if (w == NULL || !w->view.open) return 0;
    /* Win16 WM_CLOSE -> win_Close; DOS reaches it through the close box. */
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

int native_windows_translate(SDL_Event *event)
{
    NativeWindow *w;
    SDL_WindowID id;
    if (!n.active) return 0;
    if (event->type == SDL_EVENT_MOUSE_MOTION) id = event->motion.windowID;
    else if (event->type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
             event->type == SDL_EVENT_MOUSE_BUTTON_UP) id = event->button.windowID;
    else if (event->type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
        w = by_sdl_id(event->window.windowID);
        if (w == NULL) return 0;
        native_windows_request_close(w->view.id);
        return 1;
    } else if (event->type == SDL_EVENT_WINDOW_RESIZED) {
        w = by_sdl_id(event->window.windowID);
        if (w == NULL) return 0;
        if (event->window.data1 != w->width * n.scale || event->window.data2 != w->height * n.scale)
            native_windows_request_resize(w->view.id, (event->window.data1 + n.scale / 2) / n.scale,
                                          (event->window.data2 + n.scale / 2) / n.scale);
        return 1;
    } else return 0;
    w = by_sdl_id(id);
    sim_window_hosting_set_pointer_window(w ? w->view.id : (int16_t)(uint16_t)0x8000);
    if (w == NULL) return 0;
    if (!w->view.open || !SDL_ConvertEventToRenderCoordinates(w->renderer, event)) return -1;
    if (event->type == SDL_EVENT_MOUSE_MOTION) {
        to_logical(w, &event->motion.x, &event->motion.y);
        return 1;
    }
    to_logical(w, &event->button.x, &event->button.y);
    if (event->type == SDL_EVENT_MOUSE_BUTTON_DOWN && !w->view.top) {
        raise_point(w, &w->raise_x, &w->raise_y);
        w->raise_button = event->button.button;
    }
    if (w->raise_button && w->raise_button == event->button.button) {
        event->button.x = w->raise_x;
        event->button.y = w->raise_y;
        if (event->type == SDL_EVENT_MOUSE_BUTTON_UP) w->raise_button = 0;
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
    SDL_Window *focus = SDL_GetMouseFocus();
    NativeWindow *w;
    float wx, wy;
    if (!n.active || focus == NULL) return 0;
    w = by_sdl_id(SDL_GetWindowID(focus));
    if (w == NULL || !w->view.open) return 0;
    SDL_GetMouseState(&wx, &wy);
    if (!SDL_RenderCoordinatesFromWindow(w->renderer, wx, wy, x, y)) return 0;
    to_logical(w, x, y);
    return 1;
}

int native_windows_save_frames(const char *base_path)
{
    unsigned i;
    char path[1024];
    if (!n.active) return 1;
    for (i = 0; i < n.count; ++i) {
        NativeWindow *w = &n.windows[i];
        SDL_Surface *surface;
        int okay;
        if (!w->shown || w->rgba == NULL) continue;
        SDL_snprintf(path, sizeof(path), "%s.%04X.bmp", base_path, (unsigned)(uint16_t)w->view.id);
        surface = SDL_CreateSurfaceFrom(w->width, w->height, SDL_PIXELFORMAT_RGBA32, w->rgba, w->width * 4);
        if (surface == NULL) return 0;
        okay = SDL_SaveBMP(surface, path);
        SDL_DestroySurface(surface);
        if (!okay) return 0;
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
    if (w == NULL || w->window == NULL || event == NULL ||
        !SDL_RenderCoordinatesToWindow(w->renderer, (float)event->x, (float)event->y, &x, &y))
        return 0;
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        raw.type = SDL_EVENT_MOUSE_MOTION;
        raw.motion.windowID = SDL_GetWindowID(w->window);
        raw.motion.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.motion.x = x;
        raw.motion.y = y;
    } else if (event->kind == HOST_EVENT_MOUSE_DOWN || event->kind == HOST_EVENT_MOUSE_UP) {
        raw.type = event->kind == HOST_EVENT_MOUSE_DOWN ?
                   SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
        raw.button.windowID = SDL_GetWindowID(w->window);
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
    NativeWindow *w = n.active ? by_sdl_id(window) : NULL;
    if (w == NULL) return 0;
    *id = w->view.id;
    *left = w->view.left;
    *top = (int16_t)(w->view.top_y + w->strip);
    return 1;
}
