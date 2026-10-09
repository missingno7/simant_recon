#include "modern_game_view.h"
#include "portable/whole_program/modern/camera.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* The game's scroll: Bresenham steps of MapPnt, clamp, UpdateEdit
 * (m0250.c:537-592; CenterEdit, edge and Ctrl+arrow scrolling use it). */
extern int16_t f_0250_0D10(int16_t dx, int16_t dy);

enum {
    WORLD_COLUMNS = 128, WORLD_ROWS = 64,
    WORLD_WIDTH = WORLD_COLUMNS * MODERN_TILE_SIZE,
    WORLD_HEIGHT = WORLD_ROWS * MODERN_TILE_SIZE,
    KEY_NONE = 0xffffffffu, KEY_OVERLAY = 0xfffffffeu,
    INCLUDE_MARGIN = 1
};
#define MIN_ZOOM 0.25
#define MAX_ZOOM 8.0
#define FOLLOW_NS 70000000.0     /* camera follow time constant */

static struct {
    int ready;                     /* camera initialised from the canonical view */
    ModernCamera target, shown;    /* requested and displayed camera */
    int plane, terrain, origin_x, origin_y;   /* canonical state last observed */
    int columns, rows;
    int sync;                      /* camera moved by the user: re-centre MapPnt */
    int pan_active;
    float pan_x, pan_y;
    int hold_active;
    double hold_x, hold_y;         /* world pixels */
    int include_pending, include_settled;
    double include_x, include_y;
    int pumping;
    uint64_t last_ns;
    int smooth;
    /* World image */
    SDL_Renderer *renderer;
    SDL_Texture *texture, *status;
    uint8_t *indexed, *rgba;
    uint8_t status_rgba[640 * 20 * 4];
    uint32_t keys[WORLD_COLUMNS * WORLD_ROWS];
    HostPalette palette;
    int palette_valid;
    int dirty_left, dirty_top, dirty_right, dirty_bottom;   /* world pixels */
} g;

/* ---- canonical <-> modern camera ---- */

static double rect_width(const ModernWorldView *v) { return v->view_rect.right - v->view_rect.left; }
static double rect_height(const ModernWorldView *v) { return v->view_rect.bottom - v->view_rect.top; }

static void clamp_cameras(void)
{
    double w = (double)g.columns * MODERN_TILE_SIZE, h = (double)g.rows * MODERN_TILE_SIZE;
    modern_camera_clamp(&g.target, w, h);
    modern_camera_clamp(&g.shown, w, h);
}

static void invalidate_world(void)
{
    memset(g.keys, 0xff, sizeof(g.keys));
}

/* Canonical -> modern. A changed plane (SetMapPlane) shows another world:
 * re-centre on the edit view. A moved MapPnt on the same plane (goto, edge
 * or key scroll, overview click, auto-track) moves the camera by the same
 * amount, keeping any offset the larger modern view has. */
static void observe(void)
{
    ModernWorldView v;
    modern_world_view(&v);
    if (v.tile_width != MODERN_TILE_SIZE || v.tile_height != MODERN_TILE_SIZE) return;
    if (!g.ready || v.plane != g.plane) {
        double x, y;
        modern_camera_canonical_center(v.origin_x, v.origin_y, (int)rect_width(&v),
                                       (int)rect_height(&v), MODERN_TILE_SIZE, &x, &y);
        g.target.center_x = g.shown.center_x = x;
        g.target.center_y = g.shown.center_y = y;
        g.plane = v.plane;
        g.columns = v.columns;
        g.rows = v.rows;
        g.ready = 1;
        g.sync = 0;
        invalidate_world();
    } else if (v.origin_x != g.origin_x || v.origin_y != g.origin_y) {
        g.target.center_x += (double)(v.origin_x - g.origin_x) * MODERN_TILE_SIZE;
        g.target.center_y += (double)(v.origin_y - g.origin_y) * MODERN_TILE_SIZE;
    }
    if (v.terrain_set != g.terrain) invalidate_world();
    g.terrain = v.terrain_set;
    g.origin_x = v.origin_x;
    g.origin_y = v.origin_y;
}

/* Shift so world point (x, y) lies on a whole cell inside the edit view. */
static int include_shift(const ModernWorldView *v, double x, double y, int *dx, int *dy)
{
    int tx = (int)floor(x / MODERN_TILE_SIZE), ty = (int)floor(y / MODERN_TILE_SIZE);
    int cols = (int)rect_width(v) / MODERN_TILE_SIZE, rows = (int)rect_height(v) / MODERN_TILE_SIZE;
    int margin_x = cols > 2 * INCLUDE_MARGIN ? INCLUDE_MARGIN : 0;
    int margin_y = rows > 2 * INCLUDE_MARGIN ? INCLUDE_MARGIN : 0;
    *dx = *dy = 0;
    if (tx < 0 || ty < 0 || tx >= v->columns || ty >= v->rows || cols <= 0 || rows <= 0) return 0;
    if (tx < v->origin_x + margin_x) *dx = tx - margin_x - v->origin_x;
    else if (tx >= v->origin_x + cols - margin_x) *dx = tx + margin_x + 1 - cols - v->origin_x;
    if (ty < v->origin_y + margin_y) *dy = ty - margin_y - v->origin_y;
    else if (ty >= v->origin_y + rows - margin_y) *dy = ty + margin_y + 1 - rows - v->origin_y;
    return 1;
}

void modern_game_view_pump(void)
{
    ModernWorldView v;
    int dx = 0, dy = 0;
    if (!g.ready || g.pumping) return;
    observe();
    modern_world_view(&v);
    if (g.include_pending) include_shift(&v, g.include_x, g.include_y, &dx, &dy);
    else if (g.hold_active) include_shift(&v, g.hold_x, g.hold_y, &dx, &dy);
    else if (g.sync) {
        int x, y;
        modern_camera_canonical_origin(&g.target, (int)rect_width(&v), (int)rect_height(&v),
                                       MODERN_TILE_SIZE, &x, &y);
        dx = x - v.origin_x;
        dy = y - v.origin_y;
    }
    g.sync = 0;
    if (dx || dy) {
        /* One axis per call: the scroll's XOR-error stepping under-steps the
         * minor axis of a diagonal (5,4 moves 5,3); each call clamps. */
        g.pumping = 1;
        if (dx) f_0250_0D10((int16_t)dx, 0);
        if (dy) f_0250_0D10(0, (int16_t)dy);
        g.pumping = 0;
        /* Our own request: the modern camera already shows this. */
        modern_world_view(&v);
        g.origin_x = v.origin_x;
        g.origin_y = v.origin_y;
    }
    if (g.include_pending) {
        g.include_pending = 0;
        g.include_settled = 1;
    }
}

/* ---- input ---- */

static void to_world(float vx, float vy, double *wx, double *wy)
{
    modern_camera_to_world(&g.shown, vx, vy, wx, wy);
}

int modern_game_view_in_world(float vx, float vy)
{
    double wx, wy;
    if (!g.ready) return 0;
    to_world(vx, vy, &wx, &wy);
    return wx >= 0 && wy >= 0 && wx < g.columns * MODERN_TILE_SIZE && wy < g.rows * MODERN_TILE_SIZE;
}

/* The edit view shows world pixel (MapPnt*16 + dx) at editTileRect.left + dx;
 * processEdit and the other event readers invert exactly that. */
int modern_game_view_to_logical(float vx, float vy, float *lx, float *ly)
{
    ModernWorldView v;
    double wx, wy;
    if (!g.ready) return 0;
    modern_world_view(&v);
    to_world(vx, vy, &wx, &wy);
    *lx = (float)(v.view_rect.left + wx - (double)v.origin_x * MODERN_TILE_SIZE);
    *ly = (float)(v.view_rect.top + wy - (double)v.origin_y * MODERN_TILE_SIZE);
    return *lx >= v.view_rect.left && *ly >= v.view_rect.top &&
           *lx < v.view_rect.right && *ly < v.view_rect.bottom &&
           modern_game_view_in_world(vx, vy);
}

void modern_game_view_clamp_logical(float *lx, float *ly)
{
    ModernWorldView v;
    modern_world_view(&v);
    if (*lx < v.view_rect.left) *lx = v.view_rect.left;
    if (*lx > v.view_rect.right - 1) *lx = (float)(v.view_rect.right - 1);
    if (*ly < v.view_rect.top) *ly = v.view_rect.top;
    if (*ly > v.view_rect.bottom - 1) *ly = (float)(v.view_rect.bottom - 1);
}

int modern_game_view_to_view(float lx, float ly, float *vx, float *vy)
{
    ModernWorldView v;
    double x, y;
    if (!g.ready) return 0;
    modern_world_view(&v);
    if (lx < v.view_rect.left || ly < v.view_rect.top ||
        lx >= v.view_rect.right || ly >= v.view_rect.bottom)
        return 0;
    modern_camera_to_view(&g.shown, (double)v.origin_x * MODERN_TILE_SIZE + (lx - v.view_rect.left),
                          (double)v.origin_y * MODERN_TILE_SIZE + (ly - v.view_rect.top), &x, &y);
    *vx = (float)x;
    *vy = (float)y;
    return 1;
}

static void user_moved(void)
{
    clamp_cameras();
    g.shown.center_x = g.target.center_x;
    g.shown.center_y = g.target.center_y;
    g.sync = 1;
}

void modern_game_view_wheel(float vx, float vy, float steps)
{
    double zoom;
    if (!g.ready || steps == 0) return;
    zoom = g.target.zoom * pow(1.25, steps);
    if (zoom < MIN_ZOOM) zoom = MIN_ZOOM;
    if (zoom > MAX_ZOOM) zoom = MAX_ZOOM;
    g.target.center_x = g.shown.center_x;
    g.target.center_y = g.shown.center_y;
    modern_camera_zoom_at(&g.target, vx, vy, zoom);
    g.shown.zoom = zoom;
    user_moved();
}

void modern_game_view_pan(int phase, float vx, float vy)
{
    if (!g.ready) return;
    if (phase > 0) {
        g.pan_active = 1;
    } else if (phase == 0 && g.pan_active) {
        g.target.center_x = g.shown.center_x - (vx - g.pan_x) / g.shown.zoom;
        g.target.center_y = g.shown.center_y - (vy - g.pan_y) / g.shown.zoom;
        user_moved();
    } else if (phase < 0) {
        g.pan_active = 0;
    }
    g.pan_x = vx;
    g.pan_y = vy;
}

void modern_game_view_hold(int held, float vx, float vy)
{
    if (!g.ready) return;
    if (held) {
        g.hold_active = 1;
        to_world(vx, vy, &g.hold_x, &g.hold_y);
    } else if (g.hold_active) {
        g.hold_active = 0;
        g.sync = 1;      /* back to the edit view centred on the camera */
    }
}

void modern_game_view_hold_move(float vx, float vy)
{
    if (g.hold_active) to_world(vx, vy, &g.hold_x, &g.hold_y);
}

void modern_game_view_request_include(float vx, float vy)
{
    if (!g.ready) { g.include_settled = 1; return; }
    to_world(vx, vy, &g.include_x, &g.include_y);
    g.include_pending = 1;
    g.include_settled = 0;
}

int modern_game_view_include_settled(void)
{
    if (!g.include_settled) return 0;
    g.include_settled = 0;
    return 1;
}

void modern_game_view_set_smooth(int smooth) { g.smooth = smooth != 0; }

/* ---- overview ---- */

int modern_game_view_overview(ModernRect *indicator)
{
    ModernOverviewView o;
    double left, top, right, bottom, cw, ch, x0, y0;
    if (!g.ready) return 0;
    modern_overview_view(&o);
    if (o.cell_width <= 0 || o.cell_height <= 0) return 0;
    modern_camera_visible(&g.shown, &left, &top, &right, &bottom);
    if (left < 0) left = 0;
    if (top < 0) top = 0;
    if (right > g.columns * MODERN_TILE_SIZE) right = g.columns * MODERN_TILE_SIZE;
    if (bottom > g.rows * MODERN_TILE_SIZE) bottom = g.rows * MODERN_TILE_SIZE;
    cw = (double)o.cell_width / MODERN_TILE_SIZE;
    ch = (double)o.cell_height / MODERN_TILE_SIZE;
    x0 = o.tiles.left + o.pad;
    y0 = o.tiles.top;
    indicator->left = (int16_t)floor(x0 + left * cw + 0.5);
    indicator->top = (int16_t)floor(y0 + top * ch + 0.5);
    indicator->right = (int16_t)floor(x0 + right * cw + 0.5);
    indicator->bottom = (int16_t)floor(y0 + bottom * ch + 0.5);
    return indicator->right > indicator->left && indicator->bottom > indicator->top;
}

/* ---- rendering ---- */

static void mark_dirty(int x, int y)
{
    int l = x * MODERN_TILE_SIZE, t = y * MODERN_TILE_SIZE;
    if (g.dirty_right <= g.dirty_left) {
        g.dirty_left = l; g.dirty_top = t;
        g.dirty_right = l + MODERN_TILE_SIZE; g.dirty_bottom = t + MODERN_TILE_SIZE;
        return;
    }
    if (l < g.dirty_left) g.dirty_left = l;
    if (t < g.dirty_top) g.dirty_top = t;
    if (l + MODERN_TILE_SIZE > g.dirty_right) g.dirty_right = l + MODERN_TILE_SIZE;
    if (t + MODERN_TILE_SIZE > g.dirty_bottom) g.dirty_bottom = t + MODERN_TILE_SIZE;
}

static void put_cell(int x, int y, const uint8_t pixels[256])
{
    int row;
    for (row = 0; row < MODERN_TILE_SIZE; ++row)
        memcpy(g.indexed + (size_t)(y * MODERN_TILE_SIZE + row) * WORLD_WIDTH + (size_t)x * MODERN_TILE_SIZE,
               pixels + row * MODERN_TILE_SIZE, MODERN_TILE_SIZE);
    mark_dirty(x, y);
}

static int ensure_world(SDL_Renderer *renderer)
{
    if (g.renderer != renderer) {
        if (g.texture) SDL_DestroyTexture(g.texture);
        if (g.status) SDL_DestroyTexture(g.status);
        g.texture = g.status = NULL;
        g.renderer = renderer;
        g.palette_valid = 0;
    }
    if (!g.indexed && !(g.indexed = calloc(WORLD_WIDTH, WORLD_HEIGHT))) return 0;
    if (!g.rgba && !(g.rgba = calloc((size_t)WORLD_WIDTH * WORLD_HEIGHT, 4))) return 0;
    if (!g.texture) {
        g.texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STREAMING,
                                      WORLD_WIDTH, WORLD_HEIGHT);
        if (!g.texture) return 0;
        g.palette_valid = 0;
    }
    return SDL_SetTextureScaleMode(g.texture, g.smooth ? SDL_SCALEMODE_LINEAR : SDL_SCALEMODE_NEAREST);
}

/* Cells drawn by not-yet-modern canonical overlays (the spider composite):
 * the hosted edit view's own pixels for those cells. */
static void canonical_overlays(const SimVgaPlanes *planes)
{
    ModernWorldView v;
    int left, top, i, j;
    uint8_t pixels[256];
    if (planes == NULL || !modern_world_spider_cells(&left, &top)) return;
    modern_world_view(&v);
    for (j = top; j < top + 7; ++j)
        for (i = left; i < left + 7; ++i) {
            int lx = v.view_rect.left + i * MODERN_TILE_SIZE, ly = v.view_rect.top + j * MODERN_TILE_SIZE;
            int wx = v.origin_x + i, wy = v.origin_y + j;
            if (i < 0 || j < 0 || lx + MODERN_TILE_SIZE > v.view_rect.right ||
                ly + MODERN_TILE_SIZE > v.view_rect.bottom || wx >= g.columns || wy >= g.rows)
                continue;
            sim_vga_present_planes(planes, pixels, MODERN_TILE_SIZE, lx, ly, MODERN_TILE_SIZE, MODERN_TILE_SIZE);
            for (lx = 0; lx < 256; ++lx) pixels[lx] &= 15u;
            put_cell(wx, wy, pixels);
            g.keys[wy * WORLD_COLUMNS + wx] = KEY_OVERLAY;
        }
}

static void update_world(int x0, int y0, int x1, int y1);

/* The edit view's status message (f_15D9_0006: an opaque text box centred in
 * editTileRect at top+4) belongs to the view: its pixels are taken from the
 * hosted canonical view where they differ from the world under them, and
 * shown at the same place relative to the top centre of the modern view. */
static int status_overlay(SDL_Renderer *renderer, const SDL_FRect *area, int scale,
                          const SimVgaPlanes *planes)
{
    enum { BAND = 20 };
    ModernWorldView v;
    uint8_t canonical[640 * BAND];
    int width, drawn, x, y, left = 640, right = -1, top = BAND, bottom = -1;
    SDL_FRect dst;
    if (planes == NULL || modern_world_status_message() == NULL) return 1;
    modern_world_view(&v);
    width = v.view_rect.right - v.view_rect.left;
    if (width <= 0 || width > 640) return 1;
    /* Only whole cells are drawn (editWidth is a floor); the rest of the
     * rectangle never holds world pixels. */
    drawn = v.view_columns * MODERN_TILE_SIZE < width ? v.view_columns * MODERN_TILE_SIZE : width;
    update_world(v.origin_x, v.origin_y, v.origin_x + (width + 15) / 16 < g.columns ?
                 v.origin_x + (width + 15) / 16 : g.columns,
                 v.origin_y + 2 < g.rows ? v.origin_y + 2 : g.rows);
    sim_vga_present_planes(planes, canonical, (size_t)width, v.view_rect.left, v.view_rect.top,
                           width, BAND);
    for (y = 0; y < BAND; ++y)
        for (x = 0; x < width; ++x) {
            int wx = v.origin_x * MODERN_TILE_SIZE + x, wy = v.origin_y * MODERN_TILE_SIZE + y;
            uint8_t *out = g.status_rgba + ((size_t)y * 640 + (size_t)x) * 4u;
            uint8_t index = canonical[y * width + x] & 15u;
            int text = x < drawn && wx < WORLD_WIDTH && wy < WORLD_HEIGHT &&
                       g.indexed[(size_t)wy * WORLD_WIDTH + (size_t)wx] != index;
            memcpy(out, g.palette.rgb[index], 3);
            out[3] = text ? 255 : 0;
            if (text) {
                if (x < left) left = x;
                if (x > right) right = x;
                if (y < top) top = y;
                if (y > bottom) bottom = y;
            }
        }
    if (right < left) return 1;
    if (!g.status && (!(g.status = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA32,
                                                     SDL_TEXTUREACCESS_STREAMING, 640, BAND)) ||
                      !SDL_SetTextureBlendMode(g.status, SDL_BLENDMODE_BLEND) ||
                      !SDL_SetTextureScaleMode(g.status, SDL_SCALEMODE_NEAREST)))
        return 0;
    if (!SDL_UpdateTexture(g.status, NULL, g.status_rgba, 640 * 4)) return 0;
    {
        SDL_FRect src;
        src.x = (float)left; src.y = (float)top;
        src.w = (float)(right + 1 - left); src.h = (float)(bottom + 1 - top);
        dst.w = src.w * scale;
        dst.h = src.h * scale;
        dst.x = area->x + (area->w - (float)width * scale) / 2 + (float)left * scale;
        dst.y = area->y + (float)top * scale;
        return SDL_RenderTexture(renderer, g.status, &src, &dst);
    }
}

static void update_world(int x0, int y0, int x1, int y1)
{
    int x, y;
    uint8_t pixels[256];
    for (y = y0; y < y1; ++y)
        for (x = x0; x < x1; ++x) {
            ModernCell cell;
            uint32_t key;
            modern_world_cell(x, y, &cell);
            key = modern_world_cell_key(&cell);
            if (key == g.keys[y * WORLD_COLUMNS + x]) continue;
            if (!modern_world_cell_pixels(&cell, pixels)) continue;
            put_cell(x, y, pixels);
            g.keys[y * WORLD_COLUMNS + x] = key;
        }
}

static int upload(const HostPalette *palette)
{
    int x, y;
    SDL_Rect r;
    if (!g.palette_valid || memcmp(&g.palette, palette, sizeof(*palette))) {
        g.palette = *palette;
        g.palette_valid = 1;
        g.dirty_left = g.dirty_top = 0;
        g.dirty_right = WORLD_WIDTH;
        g.dirty_bottom = WORLD_HEIGHT;
    }
    if (g.dirty_right <= g.dirty_left) return 1;
    for (y = g.dirty_top; y < g.dirty_bottom; ++y)
        for (x = g.dirty_left; x < g.dirty_right; ++x) {
            uint8_t *out = g.rgba + ((size_t)y * WORLD_WIDTH + (size_t)x) * 4u;
            memcpy(out, g.palette.rgb[g.indexed[(size_t)y * WORLD_WIDTH + (size_t)x] & 15u], 3);
            out[3] = 255;
        }
    r.x = g.dirty_left; r.y = g.dirty_top;
    r.w = g.dirty_right - g.dirty_left; r.h = g.dirty_bottom - g.dirty_top;
    g.dirty_left = g.dirty_top = g.dirty_right = g.dirty_bottom = 0;
    return SDL_UpdateTexture(g.texture, &r, g.rgba + ((size_t)r.y * WORLD_WIDTH + (size_t)r.x) * 4u,
                             WORLD_WIDTH * 4);
}

static void animate(void)
{
    uint64_t now = host_time_ns();     /* virtual in deterministic runs */
    double dt = g.last_ns ? (double)(now - g.last_ns) : 0, k;
    g.last_ns = now;
    k = 1.0 - exp(-dt / FOLLOW_NS);
    g.shown.center_x += (g.target.center_x - g.shown.center_x) * k;
    g.shown.center_y += (g.target.center_y - g.shown.center_y) * k;
    if (fabs(g.target.center_x - g.shown.center_x) < 0.05) g.shown.center_x = g.target.center_x;
    if (fabs(g.target.center_y - g.shown.center_y) < 0.05) g.shown.center_y = g.target.center_y;
}

int modern_game_view_render(SDL_Renderer *renderer, const SDL_FRect *area, int scale,
                            const HostPalette *palette, const SimVgaPlanes *planes)
{
    double left, top, right, bottom;
    SDL_FRect src, dst;
    SDL_Rect clip;
    int x0, y0, x1, y1;
    if (area->w <= 0 || area->h <= 0) return 1;
    if (!g.ready) g.target.zoom = g.shown.zoom = scale;
    observe();
    if (!g.ready) return 1;
    g.target.width = g.shown.width = (int)area->w;
    g.target.height = g.shown.height = (int)area->h;
    clamp_cameras();
    animate();
    if (!ensure_world(renderer)) return 0;
    modern_camera_visible(&g.shown, &left, &top, &right, &bottom);
    x0 = (int)floor(left / MODERN_TILE_SIZE); y0 = (int)floor(top / MODERN_TILE_SIZE);
    x1 = (int)ceil(right / MODERN_TILE_SIZE); y1 = (int)ceil(bottom / MODERN_TILE_SIZE);
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > g.columns) x1 = g.columns;
    if (y1 > g.rows) y1 = g.rows;
    update_world(x0, y0, x1, y1);
    canonical_overlays(planes);
    if (!upload(palette)) return 0;
    /* The area may extend past the client (under the replaced title strip). */
    {
        int ow = 0, oh = 0;
        SDL_GetCurrentRenderOutputSize(renderer, &ow, &oh);
        clip.x = area->x < 0 ? 0 : (int)area->x;
        clip.y = area->y < 0 ? 0 : (int)area->y;
        clip.w = (int)(area->x + area->w) - clip.x;
        clip.h = (int)(area->y + area->h) - clip.y;
        if (clip.x + clip.w > ow) clip.w = ow - clip.x;
        if (clip.y + clip.h > oh) clip.h = oh - clip.y;
        if (clip.w <= 0 || clip.h <= 0) return 1;
    }
    if (!SDL_SetRenderClipRect(renderer, &clip) ||
        !SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255) || !SDL_RenderFillRect(renderer, area))
        return 0;
    src.x = (float)(left < 0 ? 0 : left);
    src.y = (float)(top < 0 ? 0 : top);
    src.w = (float)((right > g.columns * MODERN_TILE_SIZE ? g.columns * MODERN_TILE_SIZE : right) - src.x);
    src.h = (float)((bottom > g.rows * MODERN_TILE_SIZE ? g.rows * MODERN_TILE_SIZE : bottom) - src.y);
    if (src.w > 0 && src.h > 0) {
        double vx, vy;
        modern_camera_to_view(&g.shown, src.x, src.y, &vx, &vy);
        dst.x = area->x + (float)vx;
        dst.y = area->y + (float)vy;
        dst.w = (float)(src.w * g.shown.zoom);
        dst.h = (float)(src.h * g.shown.zoom);
        if (!SDL_RenderTexture(renderer, g.texture, &src, &dst)) return 0;
    }
    if (!status_overlay(renderer, area, scale, planes)) return 0;
    return SDL_SetRenderClipRect(renderer, NULL);
}

void modern_game_view_shutdown(void)
{
    if (g.texture) SDL_DestroyTexture(g.texture);
    if (g.status) SDL_DestroyTexture(g.status);
    free(g.indexed);
    free(g.rgba);
    memset(&g, 0, sizeof(g));
}
