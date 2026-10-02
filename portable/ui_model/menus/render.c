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
    uint8_t foreground, background;
    switch (mode) {
    case 0:
        foreground = colors->background;
        background = colors->normal_foreground;
        break;
    case 1:
        foreground = colors->normal_foreground;
        background = colors->background;
        break;
    case 2:
        foreground = colors->highlighted_foreground;
        background = colors->normal_foreground;
        break;
    default: /* mode 3 */
        foreground = colors->highlighted_foreground;
        background = colors->background;
        break;
    }
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
                    ? foreground : background;
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
            if (command->source_color_mode < 0 || command->source_color_mode > 3)
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
            if (mode < 0 || mode > 3)
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

PortableRenderStatus portable_menu_render_active_title(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    const PortableMenuRasterColors *colors,
    const PortableMenuBar *menu,
    const PortableMenuLayout *layout,
    size_t title_index)
{
    const PortableMenuString *title;
    const uint8_t *bytes;
    PortableMenuDrawCommand command;
    if (menu == NULL || layout == NULL || title_index >= menu->titles.count ||
        title_index >= layout->title_count)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    title = portable_menu_title(menu, title_index);
    bytes = portable_menu_string_bytes(menu, title);
    if (title == NULL || bytes == NULL || title->length == 0)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    command = (PortableMenuDrawCommand){0};
    command.kind = PORTABLE_MENU_DRAW_TEXT;
    command.source_color_mode = (bytes[0] & 0x80u) != 0 ? 2 : 0;
    command.x = layout->title_x[title_index];
    command.y = 1;
    command.text = bytes;
    command.text_length = title->length;
    command.clear_first_high_bit = (uint8_t)((bytes[0] & 0x80u) != 0);
    return portable_menu_render_draw_plan(framebuffer, font, colors,
                                           &command, 1);
}
