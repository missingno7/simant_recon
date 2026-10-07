#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics_misc_source.h"
#include "graphics_source_clip.h"
#include "graphics_source_cursor_effects.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static SimGraphicsDriver *owner;
static SimGraphicsRetireDisplay retire;
static void *retire_context;

static int16_t source_word_from_u16(uint16_t value)
{
    int16_t result;
    memcpy(&result, &value, sizeof(result));
    return result;
}

static int16_t source_word_add(int16_t left, int16_t right)
{
    return source_word_from_u16((uint16_t)((uint16_t)left + (uint16_t)right));
}

static int16_t source_word_sub(int16_t left, int16_t right)
{
    return source_word_from_u16((uint16_t)((uint16_t)left - (uint16_t)right));
}

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
    for (y = t; y < b; ++y) {
        /* _001C starts at (pattern&15)*16 + (top&3)*2 and cycles
         * SI with AND F7h. Each screen byte uses that same even table byte. */
        uint8_t mask = g->pattern_source[((uint16_t)pattern & 15u) * 16u +
                                         ((uint32_t)y & 3u) * 2u];
        for (x = l; x < r; ++x) {
            uint8_t old, next;
            uint8_t color = (uint8_t)g_3DE0 & 15u;
            if (!(mask & (0x80u >> ((uint32_t)x & 7u)))) continue;
            old = sim_graphics_vga_get(g,x,y);
            next = operation == 8 ? (old & color) : operation == 16 ? (old | color) :
                   operation == 24 ? (old ^ color) : color;
            sim_graphics_vga_put(g,x,y,next);
        }
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_screen_copy(SimGraphicsDriver *g,
    int16_t left, int16_t top, int16_t right, int16_t bottom,
    int16_t destination_x, int16_t destination_y)
{
    SimVga *vga;
    uint16_t si, di, rows = (uint16_t)(bottom-top);
    uint16_t width = (uint16_t)(((uint16_t)right>>3)-((uint16_t)left>>3));
    int16_t source_y = top, target_y = destination_y, stride;
    int direction;
    unsigned row, byte;
    if (!g || !g->pixel_storage) return SIM_GRAPHICS_INVALID_ARGUMENT;
    vga = &g->vga;
    stride = g_3DB6;
    /* m31AD:L19F6/L1A38/L1A48: reverse rows and/or bytes independently.
     * Preserve the historical bottom/destination+height start convention. */
    if (top < destination_y) {
        source_y = bottom; target_y = (int16_t)((uint16_t)destination_y+rows); stride = (int16_t)-stride;
    }
    direction = ((uint16_t)left>>3) < ((uint16_t)destination_x>>3) ? -1 : 1;
    si = (uint16_t)((uint16_t)source_y*(uint16_t)g_3DB6+((uint16_t)left>>3));
    di = (uint16_t)((uint16_t)target_y*(uint16_t)g_3DB6+((uint16_t)destination_x>>3));
    if (direction < 0) { si = (uint16_t)(si+width-1u); di = (uint16_t)(di+width-1u); }
    sim_vga_out(vga,0x3ce,8); sim_vga_out(vga,0x3cf,255);
    sim_vga_out(vga,0x3c4,2); sim_vga_out(vga,0x3c5,15);
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,1);
    for (row = 0; row < rows; ++row) {
        for (byte = 0; byte < width; ++byte) {
            uint8_t cpu = sim_vga_read(vga,(uint16_t)(si+direction*(int)byte));
            sim_vga_write(vga,(uint16_t)(di+direction*(int)byte),cpu);
        }
        si = (uint16_t)(si+stride); di = (uint16_t)(di+stride);
    }
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,0);
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
    if (!sim_graphics_source_cursor_effects_begin(l, t, r, b)) {
        g->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    g->last_status = sim_graphics_s00_masked_rect(g, l, t, r, b, p);
    if (!sim_graphics_source_cursor_effects_end())
        g->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
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
    if (!sim_graphics_source_cursor_effects_begin_pair(
            l, t, r, b, x, y, source_word_sub(source_word_add(x, r), l),
            source_word_sub(source_word_add(y, b), t))) {
        g->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    g->last_status = sim_graphics_s00_screen_copy(g, l, t, r, b, x, y);
    if (!sim_graphics_source_cursor_effects_end())
        g->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
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
