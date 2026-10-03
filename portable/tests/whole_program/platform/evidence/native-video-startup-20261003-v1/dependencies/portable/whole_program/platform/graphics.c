#include "graphics.h"
#include "graphics_line_1499.h"
#include "graphics_source_clip.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>


SimGraphicsAttrCallback g_9128;
SimGraphicsFontCallback g_912C;
SimGraphicsFontCallback g_9130;
SimGraphicsRectCallback g_9134;
SimGraphicsPatternRectCallback g_9138;
SimGraphicsRectOperationCallback g_913C;
SimGraphicsBitmapCallback g_9154;
SimGraphicsBitmapCallback g_9158;
SimGraphicsLineCallback g_9170;

static SimGraphicsDriver *s_source_owner;
static struct Rect *const *s_source_g_5AAC;

static SimGraphicsDriver *require_source_owner(void)
{
    if (s_source_owner == NULL)
        abort();
    return s_source_owner;
}

static const SimGraphicsSlotInfo s00_slots[SIM_GRAPHICS_DRIVER_ENTRY_COUNT] = {
    { SIM_GFX_ENTRY_G9128, "o00_31AD_1659", 1 },
    { SIM_GFX_ENTRY_G912C, "o00_31AD_166A", 1 },
    { SIM_GFX_ENTRY_G9130, "o00_31AD_168C", 1 },
    { SIM_GFX_ENTRY_G9134, "o00_31AD_16A9", 1 },
    { SIM_GFX_ENTRY_G9138, "o00_31AD_0122", 1 },
    { SIM_GFX_ENTRY_G913C, "o00_31AD_037C", 1 },
    { SIM_GFX_ENTRY_G9140, "o00_31AD_0522", 0 },
    { SIM_GFX_ENTRY_G9144, "o00_31AD_11FB", 0 },
    { SIM_GFX_ENTRY_G9148, "o00_31AD_0550", 0 },
    { SIM_GFX_ENTRY_G914C, "o00_31AD_0CF9", 1 },
    { SIM_GFX_ENTRY_G9150, "o00_31AD_0D06", 1 },
    { SIM_GFX_ENTRY_G9154, "o00_31AD_1206", 1 },
    { SIM_GFX_ENTRY_G9158, "o00_31AD_1213", 1 },
    { SIM_GFX_ENTRY_G915C, "o00_31AD_062A", 0 },
    { SIM_GFX_ENTRY_G9160, "o00_31AD_062E", 0 },
    { SIM_GFX_ENTRY_G9164, "o00_31AD_0632", 0 },
    { SIM_GFX_ENTRY_G9168, "o00_31AD_0636", 0 },
    { SIM_GFX_ENTRY_G916C, "o00_31AD_148C", 0 },
    { SIM_GFX_ENTRY_G9170, "o00_31AD_1499", 1 },
    { SIM_GFX_ENTRY_G9174, "o00_31AD_0004", 0 },
    { SIM_GFX_ENTRY_G9178, "o00_31AD_1481", 0 },
    { SIM_GFX_ENTRY_G917C, "o00_31AD_0647", 0 },
    { SIM_GFX_ENTRY_G9180, "o00_31AD_18BA", 0 },
    { SIM_GFX_ENTRY_G9184, "o00_31AD_063C", 0 },
    { SIM_GFX_ENTRY_G9188, "o00_31AD_1950", 0 }
};

static const char *const s01_targets[SIM_GRAPHICS_DRIVER_ENTRY_COUNT] = {
    "o01_3126_0167", "o01_3126_019A", "o01_3126_01B2", "o01_3126_024C",
    "o01_3126_024C", "o01_3126_0414", "o01_3126_0437", "o01_3126_0437",
    "o01_3126_045D", "o01_3126_073C", "o01_3126_0749", "o01_3126_0516",
    "o01_3126_0523", "o01_3126_0B26", "o01_3126_0A20", "o01_3126_0ACC",
    "o01_3126_0A7A", "o01_3126_0C7A", "o01_3126_0C87", "o01_3126_01CA",
    "o01_3126_0F78", "o01_3126_0F66", "o01_3126_0F6F", "o01_3126_0C53",
    "o01_3126_109D"
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
    size_t i;
    if (graphics == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    memset(graphics, 0, sizeof(*graphics));
    if (sim_graphics_set_mode(graphics, SIM_GRAPHICS_MODE_EGA_640X350) != SIM_GRAPHICS_OK)
        return graphics->last_status;
    graphics->g_3DDE = 8;
    graphics->g_3DE0 = 15;
    for (i = 0; i < 16; ++i)
        graphics->color_map[i] = (uint8_t)i;
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
    graphics->g_3DB2 = (int16_t)width;
    graphics->g_3DB4 = (int16_t)height;
    graphics->g_3DB6 = 80; /* DOS planar stride for both supported 640-wide modes */
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
    return graphics != NULL ? graphics->pixel_storage : NULL;
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
    mapped = (uint16_t)((bits & 0xfff0u) | graphics->color_map[bits & 0x0fu]);
    return wrap16(mapped);
}

SimGraphicsStatus sim_graphics_g9128(SimGraphicsDriver *graphics,
                                     int16_t foreground,
                                     int16_t background,
                                     int16_t source_pattern_word)
{
    (void)source_pattern_word; /* target o00_31AD_1659 never reads [bp+10]. */
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->g_3DE0 = (uint8_t)foreground;
    graphics->g_3DE2 = (uint8_t)background;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g9134(SimGraphicsDriver *graphics,
                                     int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t color)
{
    PortableRect rect;
    uint8_t pixel_color;
    uint8_t operation;
    int32_t x, y;
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    rect.left = left;
    rect.top = top;
    rect.right = right;
    rect.bottom = bottom;
    if (rect.left > rect.right) { int32_t t = rect.left; rect.left = rect.right; rect.right = t; }
    if (rect.top > rect.bottom) { int32_t t = rect.top; rect.top = rect.bottom; rect.bottom = t; }
    /* f_1B4E_000D owns source palette remapping; S00 consumes these bits as-is. */
    pixel_color = (uint8_t)((uint16_t)color & 0x0fu);
    operation = (uint8_t)graphics->g_3DD2;
    if (operation == 0) {
        portable_fill_rect(&graphics->framebuffer, rect, pixel_color);
        return SIM_GRAPHICS_OK;
    }
    if (operation == 0x18u) {
        portable_xor_rect(&graphics->framebuffer, rect, pixel_color);
        return SIM_GRAPHICS_OK;
    }
    if (operation != 0x08u && operation != 0x10u)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    if (rect.left < graphics->framebuffer.clip.left) rect.left = graphics->framebuffer.clip.left;
    if (rect.top < graphics->framebuffer.clip.top) rect.top = graphics->framebuffer.clip.top;
    if (rect.right > graphics->framebuffer.clip.right) rect.right = graphics->framebuffer.clip.right;
    if (rect.bottom > graphics->framebuffer.clip.bottom) rect.bottom = graphics->framebuffer.clip.bottom;
    for (y = rect.top; y < rect.bottom; ++y) {
        for (x = rect.left; x < rect.right; ++x) {
            uint8_t *dst = &graphics->pixel_storage[(size_t)y * graphics->framebuffer.stride + (size_t)x];
            uint8_t result = operation == 0x08u ? (uint8_t)(*dst & pixel_color) :
                                                   (uint8_t)(*dst | pixel_color);
            portable_put_pixel(&graphics->framebuffer, x, y, result);
        }
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
    if (x0 < graphics->framebuffer.clip.left) x0 = graphics->framebuffer.clip.left;
    if (y0 < graphics->framebuffer.clip.top) y0 = graphics->framebuffer.clip.top;
    if (x1 > graphics->framebuffer.clip.right) x1 = graphics->framebuffer.clip.right;
    if (y1 > graphics->framebuffer.clip.bottom) y1 = graphics->framebuffer.clip.bottom;
    pattern = (uint16_t)pattern_word & 0x0fu;
    for (y = y0; y < y1; ++y) {
        size_t row = (size_t)pattern * 16u + (size_t)(y & 7) * 2u;
        for (x = x0; x < x1; ++x) {
            size_t byte_in_row = (size_t)(((uint32_t)x >> 3) & 1u);
            uint8_t bits = graphics->pattern_source[row + byte_in_row];
            uint8_t bit = (uint8_t)((bits >> (7u - ((uint32_t)x & 7u))) & 1u);
            portable_put_pixel(&graphics->framebuffer, x, y,
                               bit ? (uint8_t)(graphics->g_3DE0 & 0x0fu) :
                                     (uint8_t)(graphics->g_3DE2 & 0x0fu));
        }
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_g913C_xor_rect(SimGraphicsDriver *graphics,
                                               int16_t left, int16_t top,
                                               int16_t right, int16_t bottom)
{
    PortableRect rect;
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    rect.left = left;
    rect.top = top;
    rect.right = right;
    rect.bottom = bottom;
    if (rect.left > rect.right) { int32_t t = rect.left; rect.left = rect.right; rect.right = t; }
    if (rect.top > rect.bottom) { int32_t t = rect.top; rect.top = rect.bottom; rect.bottom = t; }
    /* `_0394` selects GFX Set/Reset=0x0f, then data-rotate XOR (0x18). */
    portable_xor_rect(&graphics->framebuffer, rect, 0x0fu);
    return SIM_GRAPHICS_OK;
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
    graphics->g_3DDA = wrap16(glyph_stride);
    graphics->g_3DDC = glyph_height;
    graphics->g_3DDE = advance;
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
                     (uint8_t)graphics->g_3DDE);
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
    SimGraphicsDriver *graphics = raster->graphics;
    uint8_t *destination;
    uint8_t result;

    /* Keep source iteration complete; clip only the bounded native storage
     * write, matching the host framebuffer's half-open clip rectangle. */
    if (x < graphics->framebuffer.clip.left || x >= graphics->framebuffer.clip.right ||
        y < graphics->framebuffer.clip.top || y >= graphics->framebuffer.clip.bottom)
        return;
    destination = &graphics->pixel_storage[(size_t)y * graphics->framebuffer.stride +
                                           (size_t)x];
    result = raster->color;
    if (raster->operation == 0x08u)
        result = (uint8_t)(*destination & raster->color);
    else if (raster->operation == 0x10u)
        result = (uint8_t)(*destination | raster->color);
    else if (raster->operation == 0x18u)
        result = (uint8_t)(*destination ^ raster->color);
    portable_put_pixel(&graphics->framebuffer, x, y, result);
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
    if (graphics->g_3DD2 != 0 && graphics->g_3DD2 != 0x08 &&
        graphics->g_3DD2 != 0x10 && graphics->g_3DD2 != 0x18)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    /* S00 receives an already mapped source color and does not read g_41C0. */
    raster.graphics = graphics;
    raster.color = (uint8_t)((uint16_t)color & 0x0fu);
    raster.operation = (uint8_t)graphics->g_3DD2;
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
    graphics->g_3DDA = (int16_t)glyph_bytes_per_character;
    graphics->glyph_width = width;
    graphics->glyph_height = height;
    graphics->g_3DDE = width;
    graphics->g_3DDC = height;
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
    if (graphics == NULL || graphics->pixel_storage == NULL || bitmap == NULL ||
        width == 0 || height == 0 || row_bytes > SIZE_MAX / height)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    required = row_bytes * height;
    if (required > bitmap_size)
        return SIM_GRAPHICS_FONT_SPAN_INVALID;
    for (py = 0; py < height; ++py) {
        for (px = 0; px < width; ++px) {
            uint8_t row = bitmap[(size_t)py * row_bytes + px / 8u];
            uint8_t bit = (uint8_t)((row >> (7u - (px & 7u))) & 1u);
            portable_put_pixel(&graphics->framebuffer, (int32_t)x + (int32_t)px,
                               (int32_t)y + (int32_t)py,
                               bit ? graphics->g_3DE0 : graphics->g_3DE2);
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

static void source_g9134_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  int16_t color)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL || *s_source_g_5AAC != NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status = sim_graphics_g9134(s_source_owner, left, top,
                                                    right, bottom, color);
}

static void source_g9138_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  int16_t pattern_word)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL || *s_source_g_5AAC != NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status =
        sim_graphics_g9138_pattern_rect(s_source_owner, left, top,
                                        right, bottom, pattern_word);
}

static void source_g913C_callback(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL || *s_source_g_5AAC != NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    s_source_owner->last_status =
        sim_graphics_g913C_xor_rect(s_source_owner, left, top,
                                    right, bottom);
}

static void source_g9170_callback(int16_t x0, int16_t y0,
                                  int16_t x1, int16_t y1,
                                  int16_t color)
{
    (void)require_source_owner();
    s_source_owner->last_status = sim_graphics_g9170_line(s_source_owner,
                                                           x0, y0, x1, y1,
                                                           color);
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
    s_source_owner->last_status = sim_graphics_g9154(s_source_owner, x, y,
                                                      bitmap, span,
                                                      (uint16_t)width,
                                                      (uint16_t)height);
}

static void source_g9154_callback(int16_t x, int16_t y, char *bitmap,
                                  int16_t width, int16_t height)
{
    (void)require_source_owner();
    if (s_source_g_5AAC == NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    /* o00_31AD_1206 dispatches to a distinct firmware glyph path when set. */
    if (*s_source_g_5AAC != NULL) {
        s_source_owner->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
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
        g_9128 = NULL;
        g_912C = NULL;
        g_9130 = NULL;
        g_9134 = NULL;
        g_9138 = NULL;
        g_913C = NULL;
        g_9154 = NULL;
        g_9158 = NULL;
        g_9170 = NULL;
        return SIM_GRAPHICS_OK;
    }
    if (graphics->pixel_storage == NULL || source_g_5AAC == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (sim_graphics_source_clip_bind(graphics) != SIM_GRAPHICS_OK)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s_source_owner = graphics;
    s_source_g_5AAC = source_g_5AAC;
    g_9128 = source_g9128_callback;
    /* Initial S00 table copy: slots 1/2 are BIOS 8x8/8x14. */
    g_912C = source_g9130_8x8_font_callback;
    g_9130 = source_g9130_8x14_font_callback;
    g_9134 = source_g9134_callback;
    g_9138 = source_g9138_callback;
    g_913C = source_g913C_callback;
    g_9154 = source_g9154_callback;
    g_9158 = source_g9158_callback;
    g_9170 = source_g9170_callback;
    graphics->last_status = SIM_GRAPHICS_OK;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_apply_cga_font_overrides(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics != s_source_owner)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    /* S00 o00_31AD_1AE7 writes slot1=1AC4 and slot2=166A. */
    g_912C = source_g912C_custom_font_callback;
    g_9130 = source_g9130_8x8_font_callback;
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

void f_1B4E_015B(int16_t mode)
{
    (void)require_source_owner();
    s_source_owner->last_status = sim_graphics_set_mode(s_source_owner, mode);
}

int16_t f_1B4E_000D(int16_t color)
{
    return sim_graphics_f_1B4E_000D(require_source_owner(), color);
}

void f_1B4E_0228(int16_t color)
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
    if (graphics->g_3DDA == 6 && (ch & 0x80u) != 0)
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
    pen = wrap16((int32_t)x - graphics->g_3DDE);
    for (i = 0; i < 65535u && text[i] != '\0'; ++i) {
        int8_t signed_character = (int8_t)(uint8_t)text[i];
        SimGraphicsStatus status;
        pen = wrap16((int32_t)pen + graphics->g_3DDE);
        if (signed_character < 0 || pen < 0)
            continue;
        status = sim_graphics_f_1B4E_0110(graphics, pen, y,
                                         (uint8_t)signed_character);
        if (status != SIM_GRAPHICS_OK)
            return status;
        if (pen >= graphics->g_3DB2)
            break;
    }
    if (i == 65535u && text[i] != '\0')
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    graphics->g_3DA0 = wrap16((int32_t)pen + graphics->g_3DDE);
    graphics->g_3DA2 = y;
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
