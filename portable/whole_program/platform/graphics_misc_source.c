#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics_misc_source.h"
#include "graphics_source_clip.h"
#include <stdlib.h>
#include <string.h>
static SimGraphicsDriver *owner;
static SimGraphicsRetireDisplay retire;
static void *retire_context;

extern void f_1D8E_0435(char *, int16_t, int16_t, int16_t, int16_t, int16_t);
extern void f_1D8E_0384(SimGraphicsPatternRectCallback, int16_t, int16_t,
    int16_t, int16_t, int16_t, int16_t, int16_t);

SimGraphicsStatus sim_graphics_s00_masked_rect(SimGraphicsDriver *g,
    int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t pattern)
{
    int32_t x, y, l = left, t = top, r = right, b = bottom;
    unsigned operation;
    if (!g || !g->pixel_storage) return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (!g->pattern_source || g->pattern_source_size < 256)
        return SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND;
    operation = (uint16_t)g_3DD2;
    if (operation != 0 && operation != 8 && operation != 16 && operation != 24)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    if (l > r) { x = l; l = r; r = x; }
    if (t > b) { y = t; t = b; b = y; }
    if (l < g->framebuffer.clip.left) l = g->framebuffer.clip.left;
    if (t < g->framebuffer.clip.top) t = g->framebuffer.clip.top;
    if (r > g->framebuffer.clip.right) r = g->framebuffer.clip.right;
    if (b > g->framebuffer.clip.bottom) b = g->framebuffer.clip.bottom;
    for (y = t; y < b; ++y) {
        /* _001C starts at (pattern&15)*16 + (top&3)*2 and cycles
         * SI with AND F7h. Each screen byte uses that same even table byte. */
        uint8_t mask = g->pattern_source[((uint16_t)pattern & 15u) * 16u +
                                         ((uint32_t)y & 3u) * 2u];
        for (x = l; x < r; ++x) {
            uint8_t *p;
            uint8_t color = (uint8_t)g_3DE0 & 15u;
            if (!(mask & (0x80u >> ((uint32_t)x & 7u)))) continue;
            p = &g->pixel_storage[(size_t)y * g->framebuffer.stride + (size_t)x];
            if (operation == 8) *p &= color;
            else if (operation == 16) *p |= color;
            else if (operation == 24) *p ^= color;
            else *p = color;
        }
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_screen_copy(SimGraphicsDriver *g,
    int16_t left, int16_t top, int16_t right, int16_t bottom,
    int16_t destination_x, int16_t destination_y)
{
    int32_t source_byte = (uint16_t)left >> 3;
    int32_t destination_byte = (uint16_t)destination_x >> 3;
    int32_t bytes = ((uint16_t)right >> 3) - source_byte;
    int32_t rows = (int32_t)bottom - top;
    int32_t sy = top, dy = destination_y, step = 1, row;
    if (!g || !g->pixel_storage || bytes < 0 || rows < 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (!bytes || !rows) return SIM_GRAPHICS_OK;
    /* Preserve the original _1950 reverse-copy starting rows, including its
     * bottom/destination+height convention. Do not rewrite as generic blit. */
    if (top < destination_y) { sy = bottom; dy += rows; step = -1; }
    if (source_byte + bytes > g_3DB6 ||
        destination_byte + bytes > g_3DB6 ||
        sy < 0 || dy < 0 || sy >= g->framebuffer.height || dy >= g->framebuffer.height ||
        sy + (rows - 1) * step < 0 || dy + (rows - 1) * step < 0 ||
        sy + (rows - 1) * step >= g->framebuffer.height ||
        dy + (rows - 1) * step >= g->framebuffer.height)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    for (row = 0; row < rows; ++row, sy += step, dy += step)
        memmove(g->pixel_storage + (size_t)dy * g->framebuffer.stride + destination_byte * 8,
                g->pixel_storage + (size_t)sy * g->framebuffer.stride + source_byte * 8,
                (size_t)bytes * 8u);
    return SIM_GRAPHICS_OK;
}

static SimGraphicsDriver *required(void)
{
    if (!owner || owner != sim_graphics_source_owner()) abort();
    return owner;
}
static void raw_mask(int16_t l, int16_t t, int16_t r, int16_t b, int16_t p)
{
    SimGraphicsDriver *g = required();
    g->last_status = sim_graphics_s00_masked_rect(g, l, t, r, b, p);
}
static void clipped_mask(int16_t l, int16_t t, int16_t r, int16_t b, int16_t p)
{
    if (sim_graphics_source_clip_active())
        f_1D8E_0384(raw_mask, 0, 0, l, t, r, b, p);
    else raw_mask(l, t, r, b, p);
}
static void clipped_line(int16_t x, int16_t y, int16_t x1, int16_t y1, int16_t c)
{
    SimGraphicsDriver *g = required();
    if (sim_graphics_source_clip_active()) f_1D8E_0435(NULL, x, y, x1, y1, c);
    else g->last_status = sim_graphics_g9170_line(g, x, y, x1, y1, c);
}
static void copy_screen(int16_t l, int16_t t, int16_t r, int16_t b, int16_t x, int16_t y)
{
    SimGraphicsDriver *g = required();
    g->last_status = sim_graphics_s00_screen_copy(g, l, t, r, b, x, y);
    if (g->last_status != SIM_GRAPHICS_OK) abort();
}
static void retire_display(void)
{
    (void)required();
    if (!retire) abort();
    retire(retire_context);
}
SimGraphicsStatus sim_graphics_source_misc_bind(SimGraphicsDriver *g,
    SimGraphicsRetireDisplay retirement, void *context)
{
    if (!g || g != sim_graphics_source_owner() || !retirement)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    owner = g; retire = retirement; retire_context = context;
    (*( SimGraphicsLineCallback *)(void *)&driver_callback_table[17]) = clipped_line; (*( SimGraphicsPatternRectCallback *)(void *)&driver_callback_table[19]) = clipped_mask;
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[20]) = retire_display; (*( SimGraphicsScreenCopyCallback *)(void *)&driver_callback_table[24]) = copy_screen;
    return SIM_GRAPHICS_OK;
}
void sim_graphics_source_misc_unbind(void)
{
    owner = NULL; retire = NULL; retire_context = NULL;
    (*( SimGraphicsLineCallback *)(void *)&driver_callback_table[17]) = NULL; (*( SimGraphicsPatternRectCallback *)(void *)&driver_callback_table[19]) = NULL; (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[20]) = NULL; (*( SimGraphicsScreenCopyCallback *)(void *)&driver_callback_table[24]) = NULL;
}
