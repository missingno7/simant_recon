#include "text_bitmap_bridge.h"

#include "platform/graphics.h"

#include <string.h>

static struct {
    uint8_t bound;
    uint8_t hardware_profile;
    const uint8_t *fold_window;
    size_t fold_window_size;
    PortableTextBitmapStatus status;
    PortableTextBitmapState state;
    uint8_t bitmap[4u + PORTABLE_TEXT_BITMAP_CAPACITY];
} source_bridge;

static void write_word(uint8_t *destination, uint16_t value)
{
    destination[0] = (uint8_t)value;
    destination[1] = (uint8_t)(value >> 8);
}

static PortableTextBitmapStatus convert_graphics_status(SimGraphicsStatus status)
{
    switch (status) {
    case SIM_GRAPHICS_OK:
        return PORTABLE_TEXT_BITMAP_OK;
    case SIM_GRAPHICS_FONT_UNBOUND:
    case SIM_GRAPHICS_FONT_SPAN_INVALID:
        return PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT;
    case SIM_GRAPHICS_UNSUPPORTED_GLYPH_FOLD:
        return PORTABLE_TEXT_BITMAP_UNSUPPORTED_CHARACTER;
    case SIM_GRAPHICS_INVALID_ARGUMENT:
        return PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;
    default:
        return PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT;
    }
}

PortableTextBitmapStatus portable_text_bitmap_bind_source(
    uint8_t hardware_profile,
    const uint8_t *fold_lookup_window,
    size_t fold_lookup_window_size)
{
    if (fold_lookup_window == NULL && fold_lookup_window_size != 0)
        return PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;
    if (fold_lookup_window != NULL && fold_lookup_window_size < 256u)
        return PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;
    source_bridge.bound = 1;
    source_bridge.hardware_profile = hardware_profile;
    source_bridge.fold_window = fold_lookup_window;
    source_bridge.fold_window_size = fold_lookup_window_size;
    source_bridge.status = PORTABLE_TEXT_BITMAP_OK;
    return PORTABLE_TEXT_BITMAP_OK;
}

void portable_text_bitmap_unbind_source(void)
{
    source_bridge.bound = 0;
    source_bridge.hardware_profile = 0;
    source_bridge.fold_window = NULL;
    source_bridge.fold_window_size = 0;
    source_bridge.status = PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;
}

PortableTextBitmapStatus portable_text_bitmap_source_status(void)
{
    return source_bridge.status;
}

const PortableTextBitmapState *portable_text_bitmap_source_state(void)
{
    return &source_bridge.state;
}

void f_1FBD_0000(int16_t x, int16_t y, char *text)
{
    SimGraphicsDriver *graphics;
    uint8_t bounded_text[PORTABLE_TEXT_BITMAP_TEXT_CAPACITY];
    size_t text_size = 0;
    PortableTextBitmapInput input;
    PortableTextBitmapResult result;
    PortableTextBitmapStatus status;
    SimGraphicsStatus graphics_status;
    size_t i;

    if (!source_bridge.bound || text == NULL ||
        sim_graphics_source_last_status() != SIM_GRAPHICS_OK) {
        source_bridge.status = PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;
        return;
    }
    graphics = sim_graphics_source_owner();
    if (source_bridge.hardware_profile == 6u) {
        graphics_status = sim_graphics_f_1B4E_0081(graphics, x, y, text);
        source_bridge.status = convert_graphics_status(graphics_status);
        return;
    }
    for (i = 0; i < sizeof(bounded_text); ++i) {
        bounded_text[i] = (uint8_t)text[i];
        text_size = i + 1u;
        if (bounded_text[i] == 0)
            break;
    }

    memset(&input, 0, sizeof(input));
    input.hardware_profile = source_bridge.hardware_profile;
    input.character_width = (uint8_t)graphics->g_3DDE;
    input.cell_height = (uint8_t)graphics->g_3DDC;
    input.glyph_height = (uint16_t)graphics->g_3DDA;
    input.glyph_rows = graphics->glyph_source;
    input.glyph_rows_size = graphics->glyph_source_size;
    input.fold_lookup_window = source_bridge.fold_window;
    input.fold_lookup_window_size = source_bridge.fold_window_size;
    input.text = bounded_text;
    input.text_size = text_size;
    input.x = x;
    input.y = y;
    status = portable_text_bitmap_prepare(&input, &source_bridge.state, &result);
    if (status != PORTABLE_TEXT_BITMAP_OK) {
        source_bridge.status = status;
        return;
    }
    if (result.draw_kind == PORTABLE_TEXT_BITMAP_NO_DRAW) {
        source_bridge.status = PORTABLE_TEXT_BITMAP_OK;
        return;
    }
    if (result.draw_kind == PORTABLE_TEXT_BITMAP_DRAW_DIRECT_TEXT) {
        graphics_status = sim_graphics_f_1B4E_0081(
            graphics, x, y, text);
        source_bridge.status = convert_graphics_status(graphics_status);
        return;
    }

    if (g_9154 == NULL) {
        source_bridge.status = PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT;
        return;
    }
    write_word(source_bridge.bitmap, result.drawn_width);
    write_word(source_bridge.bitmap + 2, result.drawn_height);
    memcpy(source_bridge.bitmap + 4, source_bridge.state.pixels,
           sizeof(source_bridge.state.pixels));
    /* Match the source f_1B4E_005E boundary: it reads the two-word bitmap
     * header, then advances the far pointer by four bytes before calling
     * g_9154(x, y, pixels, width, height).  This bridge already passes the
     * dimensions explicitly, so g_9154 must receive the pixel payload. */
    g_9154(x, y, (char *)(source_bridge.bitmap + 4),
           (int16_t)result.drawn_width, (int16_t)result.drawn_height);
    graphics_status = sim_graphics_source_last_status();
    if (graphics_status != SIM_GRAPHICS_OK) {
        source_bridge.status = convert_graphics_status(graphics_status);
        return;
    }
    graphics->g_3DA0 = (int16_t)source_bridge.state.pen_x;
    graphics->g_3DA2 = (int16_t)source_bridge.state.pen_y;
    source_bridge.status = PORTABLE_TEXT_BITMAP_OK;
}
