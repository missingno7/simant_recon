#include "native_windows.h"
#include "../window_hosting.h"
#include "host_modes.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct NativeWindow {
    SimHostedWindowView view;      /* last presented logical state */
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint8_t *indexed, *rgba;
    int width, height;             /* logical client size */
    int shown;
    Uint8 raise_button;            /* button whose down was turned into a raise */
    int16_t raise_x, raise_y;
} NativeWindow;

static struct {
    int active;
    Host *host;
    SDL_Window *root;
    NativeWindow windows[SIM_HOSTING_SLOTS];
    unsigned count;
    Uint8 root_dropped_button;
} n;

int native_windows_active(void) { return n.active; }

static int scale_factor(void)
{
    int w = 640, h = 480;
    if (n.root == NULL || !SDL_GetWindowSize(n.root, &w, &h)) return 1;
    return w >= 1280 ? w / 640 : 1;
}

int native_windows_init(Host *host, SDL_Window *root)
{
    if (host == NULL || root == NULL || !sim_window_hosting_enabled()) return 0;
    memset(&n, 0, sizeof(n));
    n.host = host;
    n.root = root;
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

/* The DOS title object (o26_39C7_040F's object 1) moves the native window;
 * its ends keep the close and zoom boxes clickable for the game. */
static SDL_HitTestResult hit_test(SDL_Window *window, const SDL_Point *area, void *data)
{
    NativeWindow *w = data;
    int scale = scale_factor();
    int x = w->view.left + area->x / scale, y = w->view.top_y + area->y / scale;
    (void)window;
    if (w->view.drag_right > w->view.drag_left &&
        x >= w->view.drag_left + 16 && x < w->view.drag_right - 16 &&
        y >= w->view.drag_top && y < w->view.drag_bottom)
        return SDL_HITTEST_DRAGGABLE;
    return SDL_HITTEST_NORMAL;
}

static int ensure_window(NativeWindow *w, const SimHostedWindowView *view)
{
    int width = view->right - view->left, height = view->bottom - view->top_y;
    int scale = scale_factor();
    if (width <= 0 || height <= 0) return 1;
    if (w->window == NULL) {
        char title[32];
        int rx = 0, ry = 0;
        SDL_snprintf(title, sizeof(title), "SimAnt window %04X", (unsigned)(uint16_t)view->id);
        if (!SDL_CreateWindowAndRenderer(title, width * scale, height * scale,
                SDL_WINDOW_BORDERLESS | SDL_WINDOW_HIDDEN, &w->window, &w->renderer))
            return 0;
        SDL_GetWindowPosition(n.root, &rx, &ry);
        SDL_SetWindowPosition(w->window, rx + view->left * scale, ry + view->top_y * scale);
        SDL_SetWindowHitTest(w->window, hit_test, w);
        fprintf(stderr, "Native window for %04X: %dx%d at scale %d, drag bar (%d,%d,%d,%d)\n",
                (unsigned)(uint16_t)view->id, width, height, scale, view->drag_left,
                view->drag_top, view->drag_right, view->drag_bottom);
    }
    if (width != w->width || height != w->height) {
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
                                              SDL_LOGICAL_PRESENTATION_INTEGER_SCALE))
            return 0;
        if (w->width) SDL_SetWindowSize(w->window, width * scale, height * scale);
        w->width = width;
        w->height = height;
    } else if (w->view.open && (view->left != w->view.left || view->top_y != w->view.top_y)) {
        /* The game moved the logical window (zoom, keyboard move): follow it. */
        int x = 0, y = 0;
        SDL_GetWindowPosition(w->window, &x, &y);
        SDL_SetWindowPosition(w->window, x + (view->left - w->view.left) * scale,
                              y + (view->top_y - w->view.top_y) * scale);
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
            w->view = view;
            continue;
        }
        if (!ensure_window(w, &view)) return 0;
        w->view = view;
        if (w->width <= 0) continue;
        sim_vga_present_planes(view.planes, w->indexed, (size_t)w->width,
                               view.left, view.top_y, w->width, w->height);
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
            !SDL_RenderPresent(w->renderer))
            return 0;
        if (!w->shown) { SDL_ShowWindow(w->window); w->shown = 1; }
    }
    return 1;
}

static void to_logical(NativeWindow *w, float *x, float *y)
{
    *x += (float)w->view.left;
    *y += (float)w->view.top_y;
    if (*x < w->view.left) *x = w->view.left;
    if (*y < w->view.top_y) *y = w->view.top_y;
    if (*x > w->view.right - 1) *x = (float)(w->view.right - 1);
    if (*y > w->view.bottom - 1) *y = (float)(w->view.bottom - 1);
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
        /* Native chrome is not used; the game's own close box closes windows. */
        return by_sdl_id(event->window.windowID) ? -1 : 0;
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
        /* DOS: a click outside the top window's hot boxes raises the window
         * under it (f_218D_0451); Win16 raises the clicked window and eats
         * the click. Click at a point where this window is logically on top. */
        if (!sim_window_hosting_visible_point(w->view.id, &w->raise_x, &w->raise_y)) {
            w->raise_x = (int16_t)((w->view.left + w->view.right) / 2);
            w->raise_y = (int16_t)((w->view.top_y + w->view.bottom) / 2);
        }
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

/* Replay/test input: a pointer transition at window-local logical coordinates
 * of hosted window `id`, through SDL's queue like a real event. */
int native_windows_push_pointer(int16_t id, const HostEvent *event)
{
    unsigned i;
    SDL_Event raw = {0};
    float x, y;
    for (i = 0; i < n.count; ++i)
        if (n.windows[i].view.id == (int16_t)(id & 0xff00)) break;
    if (!n.active || i == n.count || n.windows[i].window == NULL || event == NULL ||
        !SDL_RenderCoordinatesToWindow(n.windows[i].renderer, (float)event->x,
                                       (float)event->y, &x, &y))
        return 0;
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        raw.type = SDL_EVENT_MOUSE_MOTION;
        raw.motion.windowID = SDL_GetWindowID(n.windows[i].window);
        raw.motion.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.motion.x = x;
        raw.motion.y = y;
    } else if (event->kind == HOST_EVENT_MOUSE_DOWN || event->kind == HOST_EVENT_MOUSE_UP) {
        raw.type = event->kind == HOST_EVENT_MOUSE_DOWN ?
                   SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
        raw.button.windowID = SDL_GetWindowID(n.windows[i].window);
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
    *top = w->view.top_y;
    return 1;
}
