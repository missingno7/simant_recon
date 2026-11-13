#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics.h"
#include "graphics_line_1499.h"
#include "graphics_source_clip.h"
#include "graphics_source_cursor_effects.h"
#include "portable/whole_program/state/font_pointer_state_v1.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>
static SimGraphicsDriver *s_source_owner;
static struct Rect *const *s_source_g_5AAC;

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

extern void clip_dispatch_rect(SimGraphicsPatternRectCallback callback,
                        int16_t unused1, int16_t unused2,
                        int16_t left, int16_t top, int16_t right,
                        int16_t bottom, int16_t color);
extern void clip_blit_mono_indexed(char *port, int16_t x, int16_t y, char *bits,
                        int16_t width, int16_t height);

static SimGraphicsDriver *require_source_owner(void)
{
    if (s_source_owner == NULL)
        abort();
    return s_source_owner;
}

static const SimGraphicsSlotInfo s00_slots[SIM_GRAPHICS_DRIVER_ENTRY_COUNT] = {
    { SIM_GFX_ENTRY_G9128, "gfx_planar_gsetattrib", 1 },
    { SIM_GFX_ENTRY_G912C, "gfx_planar_select_small_font", 1 },
    { SIM_GFX_ENTRY_G9130, "gfx_planar_select_big_font", 1 },
    { SIM_GFX_ENTRY_G9134, "gfx_planar_gboxfill", 1 },
    { SIM_GFX_ENTRY_G9138, "gfx_planar_gpatbox", 1 },
    { SIM_GFX_ENTRY_G913C, "gfx_planar_ginvbox", 1 },
    { SIM_GFX_ENTRY_G9140, "gfx_planar_gpicsize", 0 },
    { SIM_GFX_ENTRY_G9144, "gfx_planar_gimgsize", 0 },
    { SIM_GFX_ENTRY_G9148, "gfx_planar_capture_box", 0 },
    { SIM_GFX_ENTRY_G914C, "gfx_planar_gputpics", 1 },
    { SIM_GFX_ENTRY_G9150, "gfx_planar_put_picture_raw", 1 },
    { SIM_GFX_ENTRY_G9154, "gfx_planar_gputimgs", 1 },
    { SIM_GFX_ENTRY_G9158, "gfx_planar_put_image_raw", 1 },
    { SIM_GFX_ENTRY_G915C, "gfx_planar_set_or", 0 },
    { SIM_GFX_ENTRY_G9160, "gfx_planar_set_xor", 0 },
    { SIM_GFX_ENTRY_G9164, "gfx_planar_set_and", 0 },
    { SIM_GFX_ENTRY_G9168, "gfx_planar_set_copy", 0 },
    { SIM_GFX_ENTRY_G916C, "gfx_planar_gline", 0 },
    { SIM_GFX_ENTRY_G9170, "gfx_planar_draw_line_raw", 1 },
    { SIM_GFX_ENTRY_G9174, "gfx_planar_dither_box", 0 },
    { SIM_GFX_ENTRY_G9178, "gfx_planar_restore_text_mode", 0 },
    { SIM_GFX_ENTRY_G917C, "gfx_planar_put_cached_tile", 0 },
    { SIM_GFX_ENTRY_G9180, "gfx_planar_upload_tiles", 0 },
    { SIM_GFX_ENTRY_G9184, "gfx_planar_set_raster_op", 0 },
    { SIM_GFX_ENTRY_G9188, "gfx_planar_move_box", 0 }
};

static const char *const s01_targets[SIM_GRAPHICS_DRIVER_ENTRY_COUNT] = {
    "gfx_mono_gsetattrib", "gfx_mono_select_small_font", "gfx_mono_select_big_font", "gfx_mono_fill_or_pattern_box",
    "gfx_mono_fill_or_pattern_box", "gfx_mono_ginvbox", "gfx_mono_picture_size", "gfx_mono_picture_size",
    "gfx_mono_capture_box", "gfx_mono_gputpics", "gfx_mono_put_picture_raw", "gfx_mono_gputimgs",
    "gfx_mono_put_image_raw", "gfx_mono_set_or", "gfx_mono_set_xor", "gfx_mono_set_and",
    "gfx_mono_set_copy", "gfx_mono_gline", "gfx_mono_draw_line_raw", "gfx_mono_dither_box",
    "gfx_mono_restore_text_mode", "gfx_mono_tile_noop", "gfx_mono_reserved_noop", "gfx_mono_set_raster_op",
    "gfx_mono_move_box"
};

static int16_t wrap16(int32_t value)
{
    uint16_t bits = (uint16_t)value;
    int16_t result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}

SimGraphicsStatus sim_graphics_init(SimGraphicsDriver *graphics)
{
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    memset(graphics, 0, sizeof(*graphics));
    if (sim_graphics_set_mode(graphics, SIM_GRAPHICS_MODE_EGA_640X350) != SIM_GRAPHICS_OK)
        return graphics->last_status;
    /* Canonical ASM definitions supply font advance, pen and palette initializers. */
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_set_mode(SimGraphicsDriver *graphics, int16_t mode)
{
    int32_t width = SIM_GRAPHICS_SOURCE_WIDTH;
    int32_t height;
    size_t size;
    uint8_t *pixels;
    PortableFramebuffer next_framebuffer;
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (mode == SIM_GRAPHICS_MODE_EGA_640X350)
        height = SIM_GRAPHICS_SOURCE_EGA_HEIGHT;
    else if (mode == SIM_GRAPHICS_MODE_VGA_640X480)
        height = SIM_GRAPHICS_SOURCE_VGA_HEIGHT;
    else
        return graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
    size = (size_t)width * (size_t)height;
    pixels = (uint8_t *)calloc(size, 1);
    if (pixels == NULL)
        return graphics->last_status = SIM_GRAPHICS_NO_MEMORY;
    if (portable_framebuffer_init(&next_framebuffer, width, height,
                                  (size_t)width, pixels) != PORTABLE_RENDER_OK) {
        free(pixels);
        return graphics->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
    }
    if (graphics->mode_changed != NULL) {
        SimGraphicsStatus mode_status = graphics->mode_changed(
            graphics->mode_changed_context, width, height);
        if (mode_status != SIM_GRAPHICS_OK) {
            free(pixels);
            return graphics->last_status = mode_status;
        }
    }
    free(graphics->pixel_storage);
    graphics->pixel_storage = pixels;
    graphics->pixel_storage_size = size;
    graphics->framebuffer = next_framebuffer;
    graphics->video_mode = (SimGraphicsVideoMode)mode;
    sim_vga_reset(&graphics->vga);
    gfx_screen_width_pixels = (int16_t)width;
    gfx_screen_height_pixels = (int16_t)height;
    gfx_screen_row_bytes = 80; /* DOS planar stride for both supported 640-wide modes */
    return graphics->last_status = SIM_GRAPHICS_OK;
}

void sim_graphics_set_mode_changed_callback(SimGraphicsDriver *graphics,
                                            SimGraphicsModeChangedCallback callback,
                                            void *context)
{
    if (graphics == NULL)
        return;
    graphics->mode_changed = callback;
    graphics->mode_changed_context = context;
}

void sim_graphics_destroy(SimGraphicsDriver *graphics)
{
    if (graphics == NULL)
        return;
    free(graphics->pixel_storage);
    memset(graphics, 0, sizeof(*graphics));
    if (s_source_owner == graphics)
        (void)sim_graphics_bind_source_abi(NULL, NULL);
}

uint8_t *sim_graphics_pixels(SimGraphicsDriver *graphics, size_t *size_out)
{
    if (size_out != NULL)
        *size_out = graphics != NULL ? graphics->pixel_storage_size : 0;
    if (graphics != NULL) sim_graphics_vga_sync(graphics);
    return graphics != NULL ? graphics->pixel_storage : NULL;
}

/* Pixel projections address the CPU aperture, including nonvisible rows and
 * horizontal spill. Canonical m1D8E owns clipping before these raw entries. */
uint8_t sim_graphics_vga_get(const SimGraphicsDriver *g, int32_t x, int32_t y)
{
    return sim_vga_color(&g->vga, sim_vga_pixel_offset((int16_t)x, (int16_t)y,
                         (uint16_t)gfx_screen_row_bytes), (unsigned)x);
}

void sim_graphics_vga_put(SimGraphicsDriver *g, int32_t x, int32_t y, uint8_t color)
{
    uint16_t offset = sim_vga_pixel_offset((int16_t)x, (int16_t)y, (uint16_t)gfx_screen_row_bytes);
    sim_vga_store_color(&g->vga, offset, (unsigned)x, color);
    /* Keep the presentation view current for read-only debugger observers. */
    if ((unsigned)offset < (unsigned)g->framebuffer.height * 80u) {
        unsigned px = (unsigned)offset * 8u + ((unsigned)x & 7u);
        g->pixel_storage[px] = color & 15u;
    }
}

void sim_graphics_vga_sync(SimGraphicsDriver *g)
{
    sim_vga_present(&g->vga, g->pixel_storage, g->framebuffer.stride,
                    (unsigned)g->framebuffer.height);
}

SimGraphicsStatus sim_graphics_clip_push(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (graphics->clip_depth >= SIM_GRAPHICS_CLIP_DEPTH)
        return SIM_GRAPHICS_CLIP_STACK_OVERFLOW;
    graphics->clip_stack[graphics->clip_depth++] = graphics->framebuffer.clip;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_clip_set(SimGraphicsDriver *graphics, PortableRect clip)
{
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    portable_framebuffer_set_clip(&graphics->framebuffer, clip);
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_clip_pop(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (graphics->clip_depth == 0)
        return SIM_GRAPHICS_CLIP_STACK_UNDERFLOW;
    portable_framebuffer_set_clip(&graphics->framebuffer,
                                  graphics->clip_stack[--graphics->clip_depth]);
    return SIM_GRAPHICS_OK;
}

int16_t sim_graphics_f_1B4E_000D(SimGraphicsDriver *graphics, int16_t color)
{
    uint16_t bits = (uint16_t)color;
    uint16_t mapped;
    if (graphics == NULL)
        return color;
    mapped = (uint16_t)((bits & 0xfff0u) | gfx_colour_translation[bits & 0x0fu]);
    return wrap16(mapped);
}

SimGraphicsStatus sim_graphics_g9128(SimGraphicsDriver *graphics,
                                     int16_t foreground,
                                     int16_t background,
                                     int16_t source_pattern_word)
{
    (void)source_pattern_word; /* target gfx_planar_gsetattrib never reads [bp+10]. */
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    _foreColor = (uint8_t)foreground;
    g_3DE2 = (uint8_t)background;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g9134(SimGraphicsDriver *graphics,
                                     int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t color)
{
    int32_t x, y, l = left, r = right, top_y = top, b = bottom;
    uint8_t op = (uint8_t)g_3DD2, c = (uint8_t)color & 15u;
    if (!graphics || !graphics->pixel_storage) return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (l > r) { x = l; l = r; r = x; }
    if (top_y > b) { y = top_y; top_y = b; b = y; }
    for (y = top_y; y < b; ++y) for (x = l; x < r; ++x) {
        uint8_t old = sim_graphics_vga_get(graphics, x, y);
        uint8_t next = op == 8 ? (old & c) : op == 16 ? (old | c) : op == 24 ? (old ^ c) : c;
        sim_graphics_vga_put(graphics, x, y, next);
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_set_pattern_source(SimGraphicsDriver *graphics,
                                                  const uint8_t *bytes,
                                                  size_t size)
{
    if (graphics == NULL || bytes == NULL || size < 256u)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->pattern_source = bytes;
    graphics->pattern_source_size = size;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g9138_pattern_rect(SimGraphicsDriver *graphics,
                                                   int16_t left, int16_t top,
                                                   int16_t right, int16_t bottom,
                                                   int16_t pattern_word)
{
    int32_t x0, y0, x1, y1, x, y;
    uint16_t pattern;
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (graphics->pattern_source == NULL || graphics->pattern_source_size < 256u)
        return SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND;

    x0 = left < right ? left : right;
    x1 = left < right ? right : left;
    y0 = top < bottom ? top : bottom;
    y1 = top < bottom ? bottom : top;
    pattern = (uint16_t)pattern_word & 0x0fu;
    for (y = y0; y < y1; ++y) {
        size_t row = (size_t)pattern * 16u + (size_t)(y & 7) * 2u;
        for (x = x0; x < x1; ++x) {
            size_t byte_in_row = (size_t)(((uint32_t)x >> 3) & 1u);
            uint8_t bits = graphics->pattern_source[row + byte_in_row];
            uint8_t bit = (uint8_t)((bits >> (7u - ((uint32_t)x & 7u))) & 1u);
            sim_graphics_vga_put(graphics, x, y,
                               bit ? (uint8_t)(_foreColor & 0x0fu) :
                                     (uint8_t)(g_3DE2 & 0x0fu));
        }
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g913C_xor_rect(SimGraphicsDriver *graphics,
                                               int16_t left, int16_t top,
                                               int16_t right, int16_t bottom)
{
    int16_t old = g_3DD2;
    SimGraphicsStatus result;
    g_3DD2 = 24;
    result = sim_graphics_g9134(graphics, left, top, right, bottom, 15);
    g_3DD2 = old;
    return result;
}

SimGraphicsStatus sim_graphics_set_custom_font_source(SimGraphicsDriver *graphics,
                                                      const uint8_t *bytes,
                                                      size_t size)
{
    if (graphics == NULL || bytes == NULL || size == 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->custom_font_source = bytes;
    graphics->custom_font_source_size = size;
    graphics->custom_font_present = 1;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_set_bios_font_sources(SimGraphicsDriver *graphics,
                                                     const uint8_t *font_8x8,
                                                     size_t font_8x8_size,
                                                     const uint8_t *font_8x14,
                                                     size_t font_8x14_size)
{
    if (graphics == NULL || ((font_8x8 == NULL) != (font_8x8_size == 0)) ||
        ((font_8x14 == NULL) != (font_8x14_size == 0)))
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->bios_8x8_source = font_8x8;
    graphics->bios_8x8_source_size = font_8x8_size;
    graphics->bios_8x14_source = font_8x14;
    graphics->bios_8x14_source_size = font_8x14_size;
    return SIM_GRAPHICS_OK;
}

static void select_font_view(SimGraphicsDriver *graphics, const uint8_t *bytes,
                             size_t size, uint16_t glyph_stride,
                             uint8_t glyph_width, uint8_t glyph_height,
                             uint8_t advance)
{
    graphics->glyph_source = bytes;
    graphics->glyph_source_size = size;
    graphics->glyph_bytes_per_character = glyph_stride;
    graphics->glyph_width = glyph_width;
    graphics->glyph_height = glyph_height;
    gfx_font_glyph_stride = wrap16(glyph_stride);
    gfx_font_height_pixels = glyph_height;
    fontWidth = advance;
    graphics->font_is_bound = bytes != NULL && size != 0;
}

SimGraphicsStatus sim_graphics_g912C_select_custom_font(SimGraphicsDriver *graphics)
{
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    /* `_1AC4` returns without writes when the source far pointer is null. */
    if (!graphics->custom_font_present)
        return SIM_GRAPHICS_OK;
    select_font_view(graphics, graphics->custom_font_source,
                     graphics->custom_font_source_size, 6, 4, 6, 4);
    return graphics->font_is_bound ? SIM_GRAPHICS_OK : SIM_GRAPHICS_FONT_UNBOUND;
}

SimGraphicsStatus sim_graphics_g9130_select_bios_8x8(SimGraphicsDriver *graphics)
{
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    select_font_view(graphics, graphics->bios_8x8_source,
                     graphics->bios_8x8_source_size, 8, 8, 8, 8);
    return graphics->font_is_bound ? SIM_GRAPHICS_OK : SIM_GRAPHICS_FONT_UNBOUND;
}

SimGraphicsStatus sim_graphics_g9130_select_bios_8x14(SimGraphicsDriver *graphics)
{
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    select_font_view(graphics, graphics->bios_8x14_source,
                     graphics->bios_8x14_source_size, 14, 8, 14,
                     (uint8_t)fontWidth);
    return graphics->font_is_bound ? SIM_GRAPHICS_OK : SIM_GRAPHICS_FONT_UNBOUND;
}

typedef struct SimGraphics1499RasterContext {
    SimGraphicsDriver *graphics;
    uint8_t color;
    uint8_t operation;
} SimGraphics1499RasterContext;

static void sim_graphics_1499_put_pixel(void *context, int16_t x, int16_t y)
{
    SimGraphics1499RasterContext *raster = (SimGraphics1499RasterContext *)context;
    /* L15E9/L1620/L1641 skip negative byte columns before aperture access. */
    if (x < 0) return;
    uint8_t old = sim_graphics_vga_get(raster->graphics, x, y);
    uint8_t c = raster->color;
    uint8_t op = raster->operation;
    uint8_t next = op == 8 ? (old & c) : op == 16 ? (old | c) : op == 24 ? (old ^ c) : c;
    sim_graphics_vga_put(raster->graphics, x, y, next);
}

SimGraphicsStatus sim_graphics_g9170_line(SimGraphicsDriver *graphics,
                                          int16_t x0, int16_t y0,
                                          int16_t x1, int16_t y1,
                                          int16_t color)
{
    SimGraphics1499RasterContext raster;
    int written;
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (g_3DD2 != 0 && g_3DD2 != 0x08 &&
        g_3DD2 != 0x10 && g_3DD2 != 0x18)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    /* S00 receives an already mapped source color and does not read gfx_colour_translation. */
    raster.graphics = graphics;
    raster.color = (uint8_t)((uint16_t)color & 0x0fu);
    raster.operation = (uint8_t)g_3DD2;
    written = sim_graphics_line_1499_pixels(x0, y0, x1, y1,
                                             sim_graphics_1499_put_pixel,
                                             &raster);
    return written < 0 ? SIM_GRAPHICS_UNSUPPORTED_MODE : SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_set_glyph_source(SimGraphicsDriver *graphics,
                                                const uint8_t *bytes,
                                                size_t size,
                                                uint16_t glyph_bytes_per_character,
                                                uint8_t width,
                                                uint8_t height)
{
    if (graphics == NULL || bytes == NULL || glyph_bytes_per_character == 0 ||
        glyph_bytes_per_character > INT16_MAX ||
        width == 0 || height == 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->glyph_source = bytes;
    graphics->glyph_source_size = size;
    graphics->glyph_bytes_per_character = glyph_bytes_per_character;
    gfx_font_glyph_stride = (int16_t)glyph_bytes_per_character;
    graphics->glyph_width = width;
    graphics->glyph_height = height;
    fontWidth = width;
    gfx_font_height_pixels = height;
    graphics->font_is_bound = 1;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g9154(SimGraphicsDriver *graphics,
                                     int16_t x, int16_t y,
                                     const uint8_t *bitmap, size_t bitmap_size,
                                     uint16_t width, uint16_t height)
{
    size_t row_bytes = ((size_t)width + 7u) / 8u;
    size_t required;
    unsigned py, px;
    unsigned first_x, end_x;
    uint8_t operation;
    if (graphics == NULL || graphics->pixel_storage == NULL || bitmap == NULL ||
        width == 0 || height == 0 || row_bytes > SIZE_MAX / height)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    operation = (uint8_t)g_3DD2;
    if (operation != 0 && operation != 0x08u && operation != 0x10u &&
        operation != 0x18u)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    required = row_bytes * height;
    if (required > bitmap_size)
        return SIM_GRAPHICS_FONT_SPAN_INVALID;
    first_x = (unsigned)(uint16_t)gfx_clip_left_pixels;
    end_x = (unsigned)width - (unsigned)(uint16_t)gfx_clip_right_pixels;
    if (first_x > width || end_x > width || first_x > end_x)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    for (py = 0; py < height; ++py) {
        for (px = first_x; px < end_x; ++px) {
            uint8_t row = bitmap[(size_t)py * row_bytes + px / 8u];
            uint8_t bit = (uint8_t)((row >> (7u - (px & 7u))) & 1u);
            int32_t dx = (int32_t)x + (int32_t)px;
            int32_t dy = (int32_t)y + (int32_t)py;
            uint8_t color = bit ? _foreColor : g_3DE2;
            if (operation != 0) {
                uint8_t old = sim_graphics_vga_get(graphics, dx, dy);
                color = operation == 8 ? (old & color) : operation == 16 ? (old | color) : (old ^ color);
            }
            sim_graphics_vga_put(graphics, (int32_t)x + (int32_t)px,
                               (int32_t)y + (int32_t)py, color);
        }
    }
    return SIM_GRAPHICS_OK;
}

static void source_g9128_callback(int16_t foreground, int16_t background,
                                  int16_t pattern_word)
{
    (void)require_source_owner();
    s_source_owner->last_status = sim_graphics_g9128(s_source_owner, foreground,
                                                    background, pattern_word);
}

static void source_g912C_custom_font_callback(void)
{
    (void)require_source_owner();
    /* S20's global source pointer is the live resource view. If it is null,
     * S00's custom-font selector preserves its source no-op behavior. */
    if (gfx_primary_font_offset != NULL) {
        s_source_owner->last_status =
            sim_source_font_bind_driver_view_v1(s_source_owner);
        if (s_source_owner->last_status != SIM_GRAPHICS_OK)
            return;
    }
    s_source_owner->last_status =
        sim_graphics_g912C_select_custom_font(s_source_owner);
}

static void source_g9130_8x8_font_callback(void)
{
    (void)require_source_owner();
    s_source_owner->last_status =
        sim_graphics_g9130_select_bios_8x8(s_source_owner);
}

static void source_g9130_8x14_font_callback(void)
{
    (void)require_source_owner();
    s_source_owner->last_status =
        sim_graphics_g9130_select_bios_8x14(s_source_owner);
}

static void source_g9134_callback_raw(int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t color)
{
    (void)require_source_owner();
    if (!sim_graphics_source_cursor_effects_begin(left, top, right, bottom)) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status = sim_graphics_g9134(s_source_owner, left, top,
                                                    right, bottom, color);
    if (!sim_graphics_source_cursor_effects_end())
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
}

static void source_g9138_callback_raw(int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t pattern_word)
{
    (void)require_source_owner();
    if (!sim_graphics_source_cursor_effects_begin(
            left < right ? left : right, top < bottom ? top : bottom,
            left < right ? right : left, top < bottom ? bottom : top)) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status =
        sim_graphics_g9138_pattern_rect(s_source_owner, left, top,
                                        right, bottom, pattern_word);
    if (!sim_graphics_source_cursor_effects_end())
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
}

static void source_g913C_callback_raw(int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t ignored)
{
    (void)ignored; /* clip_dispatch_rect's fifth word is ignored by g913C. */
    (void)require_source_owner();
    if (!sim_graphics_source_cursor_effects_begin(left, top, right, bottom)) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status =
        sim_graphics_g913C_xor_rect(s_source_owner, left, top, right, bottom);
    if (!sim_graphics_source_cursor_effects_end())
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
}

static void source_g9134_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  int16_t color)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    s_source_owner->last_status = SIM_GRAPHICS_OK;
    if (*s_source_g_5AAC != NULL)
        clip_dispatch_rect(source_g9134_callback_raw, 0, 0, left, top, right, bottom, color);
    else
        source_g9134_callback_raw(left, top, right, bottom, color);
}

static void source_g9138_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  int16_t pattern_word)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    s_source_owner->last_status = SIM_GRAPHICS_OK;
    if (*s_source_g_5AAC != NULL)
        clip_dispatch_rect(source_g9138_callback_raw, 0, 0, left, top, right, bottom,
                    pattern_word);
    else
        source_g9138_callback_raw(left, top, right, bottom, pattern_word);
}

static void source_g913C_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    s_source_owner->last_status = SIM_GRAPHICS_OK;
    if (*s_source_g_5AAC != NULL)
        clip_dispatch_rect(source_g913C_callback_raw, 0, 0, left, top, right, bottom, 0);
    else
        source_g913C_callback_raw(left, top, right, bottom, 0);
}

static void source_g9170_callback(int16_t x0, int16_t y0,
                                  int16_t x1, int16_t y1,
                                  int16_t color)
{
    (void)require_source_owner();
    if (!sim_graphics_source_cursor_effects_begin(
            x0 < x1 ? x0 : x1, y0 < y1 ? y0 : y1,
            x0 < x1 ? x1 : x0, y0 < y1 ? y1 : y0)) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status = sim_graphics_g9170_line(s_source_owner,
                                                           x0, y0, x1, y1,
                                                           color);
    if (!sim_graphics_source_cursor_effects_end())
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
}

static void source_g9154_common(int16_t x, int16_t y, char *source_bitmap,
                                int16_t width, int16_t height)
{
    const uint8_t *bitmap = (const uint8_t *)source_bitmap;
    size_t row_bytes;
    size_t span;
    (void)require_source_owner();
    if (bitmap == NULL || width <= 0 || height <= 0) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    row_bytes = ((size_t)(uint16_t)width + 7u) / 8u;
    if ((size_t)(uint16_t)height > SIZE_MAX / row_bytes) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    span = row_bytes * (size_t)(uint16_t)height;
    if (!sim_graphics_source_cursor_effects_begin(
            source_word_add(x, gfx_clip_left_pixels), y,
            source_word_sub(source_word_add(x, width), gfx_clip_right_pixels),
            source_word_add(y, height))) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status = sim_graphics_g9154(s_source_owner, x, y,
                                                      bitmap, span,
                                                      (uint16_t)width,
                                                      (uint16_t)height);
    if (!sim_graphics_source_cursor_effects_end())
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
}

static void source_g9154_callback(int16_t x, int16_t y, char *bitmap,
                                  int16_t width, int16_t height)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    /* gfx_planar_gputimgs dispatches through the generated clipping body when set. */
    if (*s_source_g_5AAC != NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_OK;
        clip_blit_mono_indexed(NULL, x, y, bitmap, width, height);
        return;
    }
    source_g9154_common(x, y, bitmap, width, height);
}

static void source_g9158_callback(int16_t x, int16_t y, char *bitmap,
                                  int16_t width, int16_t height)
{
    source_g9154_common(x, y, bitmap, width, height);
}

SimGraphicsStatus sim_graphics_bind_source_abi(SimGraphicsDriver *graphics,
                                               struct Rect *const *source_g_5AAC)
{
    if (graphics == NULL) {
        s_source_owner = NULL;
        s_source_g_5AAC = NULL;
        sim_graphics_source_clip_unbind();
        (*( SimGraphicsAttrCallback *)(void *)&driver_callback_table[0]) = NULL;
        (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[1]) = NULL;
        (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[2]) = NULL;
        (*( SimGraphicsRectCallback *)(void *)&driver_callback_table[3]) = NULL;
        (*( SimGraphicsPatternRectCallback *)(void *)&driver_callback_table[4]) = NULL;
        (*( SimGraphicsRectOperationCallback *)(void *)&driver_callback_table[5]) = NULL;
        (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[11]) = NULL;
        (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[12]) = NULL;
        (*( SimGraphicsLineCallback *)(void *)&driver_callback_table[18]) = NULL;
        return SIM_GRAPHICS_OK;
    }
    if (graphics->pixel_storage == NULL || source_g_5AAC == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (sim_graphics_source_clip_bind(graphics) != SIM_GRAPHICS_OK)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s_source_owner = graphics;
    s_source_g_5AAC = source_g_5AAC;
    (*( SimGraphicsAttrCallback *)(void *)&driver_callback_table[0]) = source_g9128_callback;
    /* Initial S00 table copy: slots 1/2 are BIOS 8x8/8x14. */
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[1]) = source_g9130_8x8_font_callback;
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[2]) = source_g9130_8x14_font_callback;
    (*( SimGraphicsRectCallback *)(void *)&driver_callback_table[3]) = source_g9134_callback;
    (*( SimGraphicsPatternRectCallback *)(void *)&driver_callback_table[4]) = source_g9138_callback;
    (*( SimGraphicsRectOperationCallback *)(void *)&driver_callback_table[5]) = source_g913C_callback;
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[11]) = source_g9154_callback;
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[12]) = source_g9158_callback;
    (*( SimGraphicsLineCallback *)(void *)&driver_callback_table[18]) = source_g9170_callback;
    graphics->last_status = SIM_GRAPHICS_OK;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_apply_cga_font_overrides(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics != s_source_owner)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    /* S00 gfx_planar_init_320x200 writes slot1=1AC4 and slot2=166A. */
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[1]) = source_g912C_custom_font_callback;
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[2]) = source_g9130_8x8_font_callback;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_source_last_status(void)
{
    return s_source_owner != NULL ? s_source_owner->last_status :
                                    SIM_GRAPHICS_INVALID_ARGUMENT;
}

SimGraphicsDriver *sim_graphics_source_owner(void)
{
    return require_source_owner();
}

void gfx_video_bios_ax(int16_t mode)
{
    (void)require_source_owner();
    s_source_owner->last_status = sim_graphics_set_mode(s_source_owner, mode);
}

int16_t ConvColor(int16_t color)
{
    return sim_graphics_f_1B4E_000D(require_source_owner(), color);
}

void gfx_set_border_colour(int16_t color)
{
    (void)require_source_owner();
    /* Source AX=1001h uses BH; preserve that byte as the host palette request. */
    s_source_owner->overscan_color = (uint8_t)color;
    s_source_owner->last_status = SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_f_1B4E_0110(SimGraphicsDriver *graphics,
                                           int16_t x, int16_t y,
                                           int16_t character)
{
    size_t offset;
    uint8_t ch;
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (graphics->glyph_source == NULL)
        return SIM_GRAPHICS_FONT_UNBOUND;
    ch = (uint8_t)character;
    if (gfx_font_glyph_stride == 6 && (ch & 0x80u) != 0)
        return SIM_GRAPHICS_UNSUPPORTED_GLYPH_FOLD;
    offset = (size_t)ch * graphics->glyph_bytes_per_character;
    if (offset > graphics->glyph_source_size ||
        graphics->glyph_bytes_per_character > graphics->glyph_source_size - offset)
        return SIM_GRAPHICS_FONT_SPAN_INVALID;
    return sim_graphics_g9154(graphics, x, y, graphics->glyph_source + offset,
                              graphics->glyph_bytes_per_character,
                              graphics->glyph_width, graphics->glyph_height);
}

SimGraphicsStatus sim_graphics_f_1B4E_0081(SimGraphicsDriver *graphics,
                                           int16_t x, int16_t y,
                                           const char *text)
{
    int16_t pen;
    size_t i;
    if (graphics == NULL || text == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    pen = wrap16((int32_t)x - fontWidth);
    for (i = 0; i < 65535u && text[i] != '\0'; ++i) {
        int8_t signed_character = (int8_t)(uint8_t)text[i];
        SimGraphicsStatus status;
        pen = wrap16((int32_t)pen + fontWidth);
        if (signed_character < 0 || pen < 0)
            continue;
        status = sim_graphics_f_1B4E_0110(graphics, pen, y,
                                         (uint8_t)signed_character);
        if (status != SIM_GRAPHICS_OK)
            return status;
        if (pen >= gfx_screen_width_pixels)
            break;
    }
    if (i == 65535u && text[i] != '\0')
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    gfx_text_pen_x.x = wrap16((int32_t)pen + fontWidth);
    gfx_text_pen_x.y = y;
    return SIM_GRAPHICS_OK;
}

const SimGraphicsSlotInfo *sim_graphics_driver_slots(size_t *count_out)
{
    if (count_out != NULL)
        *count_out = SIM_GRAPHICS_DRIVER_ENTRY_COUNT;
    return s00_slots;
}

int sim_graphics_driver_entry_is_provided(SimGraphicsDriverEntry entry)
{
    return entry == SIM_GFX_ENTRY_G9128 || entry == SIM_GFX_ENTRY_G9134 ||
           entry == SIM_GFX_ENTRY_G912C || entry == SIM_GFX_ENTRY_G9130 ||
           entry == SIM_GFX_ENTRY_G9138 || entry == SIM_GFX_ENTRY_G913C ||
           entry == SIM_GFX_ENTRY_G914C || entry == SIM_GFX_ENTRY_G9150 ||
           entry == SIM_GFX_ENTRY_G9154 || entry == SIM_GFX_ENTRY_G9158 ||
           entry == SIM_GFX_ENTRY_G9170;
}

const char *const *sim_graphics_s01_source_targets(size_t *count_out)
{
    if (count_out != NULL)
        *count_out = SIM_GRAPHICS_DRIVER_ENTRY_COUNT;
    return s01_targets;
}
