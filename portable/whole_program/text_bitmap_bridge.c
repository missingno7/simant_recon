#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "text_bitmap_bridge.h"

#include "platform/graphics.h"

#include <string.h>

static struct {
    uint8_t bound;
    uint8_t hardware_profile;
    const uint8_t *fold_window;
    size_t fold_window_size;
    PortableTextBitmapStatus status;
} source_bridge;

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

void f_1FBD_0000(int16_t x, int16_t y, char *text)
{
    SimGraphicsDriver *graphics;
    uint8_t bounded_text[PORTABLE_TEXT_BITMAP_TEXT_CAPACITY];
    size_t text_size = 0;
    PortableTextBitmapInput input;
    PortableTextBitmapOwnerView owners;
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
    input.character_width = (uint8_t)g_3DDE;
    input.cell_height = (uint8_t)g_3DDC;
    input.glyph_height = (uint16_t)g_3DDA;
    input.glyph_rows = graphics->glyph_source;
    input.glyph_rows_size = graphics->glyph_source_size;
    input.fold_lookup_window = source_bridge.fold_window;
    input.fold_lookup_window_size = source_bridge.fold_window_size;
    input.text = bounded_text;
    input.text_size = text_size;
    input.x = x;
    input.y = y;
    owners.width = &g_5ABA;
    owners.height = &g_5ABC;
    owners.pixels = CANONICAL_TEXT_BITMAP_PIXELS;
    owners.pixels_capacity = sizeof(CANONICAL_TEXT_BITMAP_PIXELS);
    owners.copied_text = CANONICAL_TEXT_BITMAP_STRING;
    owners.copied_text_capacity = sizeof(CANONICAL_TEXT_BITMAP_STRING);
    owners.copied_text_terminator = CANONICAL_TEXT_BITMAP_TERMINATOR;
    status = portable_text_bitmap_prepare(&input, &owners, &result);
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

    if ((*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[11]) == NULL) {
        source_bridge.status = PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT;
        return;
    }
    /* Match the source f_1B4E_005E boundary: it reads the two-word bitmap
     * header, then advances the far pointer by four bytes before calling
     * g_9154(x, y, pixels, width, height). Dimensions are explicit here, and
     * the payload pointer is the canonical g_5ABE owner itself. */
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[11])(x, y, (char *)owners.pixels,
           (int16_t)result.drawn_width, (int16_t)result.drawn_height);
    graphics_status = sim_graphics_source_last_status();
    if (graphics_status != SIM_GRAPHICS_OK) {
        source_bridge.status = convert_graphics_status(graphics_status);
        return;
    }
    g_3DA0.x = (int16_t)(uint16_t)((uint16_t)x + result.drawn_width);
    g_3DA0.y = y;
    source_bridge.status = PORTABLE_TEXT_BITMAP_OK;
}
