#include "render.h"

#include <limits.h>

static int valid_font(const PortableBiosFontBitmap *font)
{
    size_t needed;
    if (font == NULL || font->glyph_rows == NULL || font->glyph_width != 8 ||
        (font->glyph_height != 8 && font->glyph_height != 14))
        return 0;
    needed = (size_t)256 * font->glyph_height;
    return font->glyph_rows_size >= needed;
}

PortableRenderStatus portable_menu_raster_colors_for_width(
    uint16_t screen_width, PortableMenuRasterColors *colors)
{
    if (colors == NULL || screen_width == 0)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (screen_width == 320) {
        colors->normal_foreground = 8;
        colors->background = 11;
        colors->highlighted_foreground = 0;
    } else {
        colors->normal_foreground = 7;
        colors->background = 14;
        colors->highlighted_foreground = 12;
    }
    return PORTABLE_RENDER_OK;
}

static void draw_text(PortableFramebuffer *framebuffer,
                      const PortableBiosFontBitmap *font,
                      const PortableMenuRasterColors *colors,
                      const PortableMenuDrawCommand *command,
                      int mode)
{
    size_t char_index;
    uint8_t foreground = mode == 3 ? colors->highlighted_foreground
                                   : colors->normal_foreground;
    for (char_index = 0; char_index < command->text_length; ++char_index) {
        uint8_t code = command->text[char_index];
        int64_t glyph_x = (int64_t)command->x + (int64_t)char_index * 8;
        unsigned row, column;
        if (char_index == 0 && command->clear_first_high_bit)
            code = (uint8_t)(code & 0x7fu);
        for (row = 0; row < font->glyph_height; ++row) {
            uint8_t bits = font->glyph_rows[(size_t)code * font->glyph_height + row];
            int64_t y = (int64_t)command->y + row;
            for (column = 0; column < 8; ++column) {
                int64_t x = glyph_x + column;
                uint8_t color = (bits & (uint8_t)(0x80u >> column))
                    ? foreground : colors->background;
                if (x >= INT32_MIN && x <= INT32_MAX &&
                    y >= INT32_MIN && y <= INT32_MAX)
                    portable_put_pixel(framebuffer, (int32_t)x, (int32_t)y, color);
            }
        }
    }
}

PortableRenderStatus portable_menu_render_draw_plan(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    const PortableMenuRasterColors *colors,
    const PortableMenuDrawCommand *commands,
    size_t command_count)
{
    size_t i;
    int mode;
    if (framebuffer == NULL || framebuffer->pixels == NULL || colors == NULL ||
        commands == NULL || command_count == 0 || !valid_font(font))
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    for (i = 0; i < command_count; ++i) {
        const PortableMenuDrawCommand *command = &commands[i];
        switch (command->kind) {
        case PORTABLE_MENU_DRAW_SET_COLOR_MODE:
            if (command->source_color_mode != 1 && command->source_color_mode != 3)
                return PORTABLE_RENDER_UNSUPPORTED_MODE;
            break;
        case PORTABLE_MENU_DRAW_FILL_RECT:
            if (command->rect.left < INT32_MIN || command->rect.left > INT32_MAX ||
                command->rect.top < INT32_MIN || command->rect.top > INT32_MAX ||
                command->rect.right < INT32_MIN || command->rect.right > INT32_MAX ||
                command->rect.bottom < INT32_MIN || command->rect.bottom > INT32_MAX)
                return PORTABLE_RENDER_INVALID_RESOURCE;
            portable_fill_rect(framebuffer,
                (PortableRect){(int32_t)command->rect.left,
                               (int32_t)command->rect.top,
                               (int32_t)command->rect.right,
                               (int32_t)command->rect.bottom},
                command->fill_color);
            break;
        case PORTABLE_MENU_DRAW_TEXT:
            mode = command->source_color_mode;
            if (mode != 1 && mode != 3)
                return PORTABLE_RENDER_UNSUPPORTED_MODE;
            if (command->text == NULL || command->text_length == 0 ||
                (command->clear_first_high_bit &&
                 (command->text[0] & 0x80u) == 0))
                return PORTABLE_RENDER_INVALID_RESOURCE;
            draw_text(framebuffer, font, colors, command, mode);
            break;
        default:
            return PORTABLE_RENDER_UNSUPPORTED_MODE;
        }
    }
    return PORTABLE_RENDER_OK;
}
