#include "dropdown_render.h"

#include <limits.h>
#include <string.h>

static int mode_arguments(int mode, int16_t g5fea, int16_t g5fec,
                          int16_t g5fee, int16_t *foreground,
                          int16_t *background, int16_t *pattern)
{
    switch (mode) {
    case 0: *foreground = g5fec; *background = g5fea; *pattern = 0; return 1;
    case 1: *foreground = g5fea; *background = g5fec; *pattern = 0x00c0; return 1;
    case 2: *foreground = g5fee; *background = g5fea; *pattern = 0x0030; return 1;
    case 3: *foreground = g5fee; *background = g5fec; *pattern = 0x0030; return 1;
    default: return 0;
    }
}

void portable_menu_dropdown_source_pen_colors(
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    int16_t mode_pen_color[4])
{
    if (mode_pen_color == NULL) return;
    mode_pen_color[0] = (uint8_t)source_g5fec;
    mode_pen_color[1] = (uint8_t)source_g5fea;
    mode_pen_color[2] = (uint8_t)source_g5fee;
    mode_pen_color[3] = (uint8_t)source_g5fee;
}

static PortableRect intersect_rect(PortableRect a, PortableRect b)
{
    PortableRect result = {
        a.left > b.left ? a.left : b.left,
        a.top > b.top ? a.top : b.top,
        a.right < b.right ? a.right : b.right,
        a.bottom < b.bottom ? a.bottom : b.bottom
    };
    if (result.right < result.left) result.right = result.left;
    if (result.bottom < result.top) result.bottom = result.top;
    return result;
}

static int valid_font(const PortableBiosFontBitmap *font)
{
    if (font == NULL || font->glyph_rows == NULL || font->glyph_width != 8 ||
        (font->glyph_height != 8 && font->glyph_height != 14))
        return 0;
    return font->glyph_rows_size >= (size_t)256 * font->glyph_height;
}

static void raster_text(PortableFramebuffer *framebuffer,
                        const PortableBiosFontBitmap *font,
                        const PortableMenuDropdownDrawCommand *command,
                        uint8_t foreground, uint8_t background)
{
    size_t character;
    for (character = 0; character < command->text_length; ++character) {
        uint8_t code = command->text[character];
        int64_t x0 = (int64_t)command->x + (int64_t)character * 8;
        unsigned y, x;
        if (character == 0 && command->clear_first_high_bit)
            code = (uint8_t)(code & 0x7fu);
        for (y = 0; y < font->glyph_height; ++y) {
            uint8_t bits = font->glyph_rows[(size_t)code * font->glyph_height + y];
            int64_t dy = (int64_t)command->y + y;
            for (x = 0; x < 8; ++x) {
                int64_t dx = x0 + x;
                uint8_t color = (bits & (uint8_t)(0x80u >> x))
                    ? foreground : background;
                if (dx >= INT32_MIN && dx <= INT32_MAX &&
                    dy >= INT32_MIN && dy <= INT32_MAX)
                    portable_put_pixel(framebuffer, (int32_t)dx,
                                       (int32_t)dy, color);
            }
        }
    }
}

PortableMenuDropdownRenderStatus portable_menu_dropdown_rasterize(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    PortableMenuDropdownRect saved_rect,
    const PortableMenuDropdownDrawCommand *commands, size_t command_count)
{
    PortableRect old_clip, clip;
    uint8_t foreground = 0, background = 0;
    int mode_ready = 0;
    size_t i;
    PortableMenuDropdownRenderStatus status = PORTABLE_DROPDOWN_RENDER_OK;
    if (framebuffer == NULL || framebuffer->pixels == NULL || commands == NULL ||
        command_count == 0 || saved_rect.left > saved_rect.right ||
        saved_rect.top > saved_rect.bottom)
        return PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
    if (!valid_font(font)) return PORTABLE_DROPDOWN_RENDER_INVALID_FONT;
    old_clip = framebuffer->clip;
    clip = intersect_rect(old_clip,
        (PortableRect){saved_rect.left, saved_rect.top,
                       saved_rect.right, saved_rect.bottom});
    portable_framebuffer_set_clip(framebuffer, clip);
    for (i = 0; i < command_count; ++i) {
        const PortableMenuDropdownDrawCommand *command = &commands[i];
        if (command->kind == PORTABLE_DROPDOWN_SET_MODE) {
            if (command->mode < 0 || command->mode > 3) {
                status = PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
                break;
            }
            /* DOS EGA font drawing uses the low four planes of g_3DE0 and
             * g_3DE2. The source glyph path does not consult g_3DE4. */
            foreground = (uint8_t)command->attribute_foreground & 0x0fu;
            background = (uint8_t)command->attribute_background & 0x0fu;
            mode_ready = 1;
        } else if (command->kind == PORTABLE_DROPDOWN_FILL_PRIMITIVE) {
            portable_fill_rect(framebuffer,
                (PortableRect){command->rect.left, command->rect.top,
                               command->rect.right, command->rect.bottom},
                (uint8_t)command->primitive_color & 0x0fu);
        } else if (command->kind == PORTABLE_DROPDOWN_TEXT) {
            if (!mode_ready || command->text == NULL || command->text_length == 0 ||
                (command->clear_first_high_bit &&
                 (command->text[0] & 0x80u) == 0)) {
                status = PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
                break;
            }
            raster_text(framebuffer, font, command, foreground, background);
        } else {
            status = PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
            break;
        }
    }
    portable_framebuffer_set_clip(framebuffer, old_clip);
    return status;
}

static int append_mode(PortableMenuDropdownDrawCommand *commands,
                       size_t capacity, size_t *count, int mode,
                       int16_t g5fea, int16_t g5fec, int16_t g5fee,
                       const int16_t mode_pen_color[4])
{
    PortableMenuDropdownDrawCommand *command;
    if (*count >= capacity) return 0;
    command = &commands[(*count)++];
    memset(command, 0, sizeof(*command));
    command->kind = PORTABLE_DROPDOWN_SET_MODE;
    command->mode = (int16_t)mode;
    command->primitive_color = mode_pen_color[mode];
    return mode_arguments(mode, g5fea, g5fec, g5fee,
                          &command->attribute_foreground,
                          &command->attribute_background,
                          &command->attribute_pattern);
}

static int append_primitive(PortableMenuDropdownDrawCommand *commands,
                            size_t capacity, size_t *count,
                            int32_t left, int32_t top, int32_t right,
                            int32_t bottom, int16_t color)
{
    PortableMenuDropdownDrawCommand *command;
    if (*count >= capacity) return 0;
    command = &commands[(*count)++];
    memset(command, 0, sizeof(*command));
    command->kind = PORTABLE_DROPDOWN_FILL_PRIMITIVE;
    command->rect = (PortableMenuDropdownRect){left, top, right, bottom};
    command->primitive_color = color;
    return 1;
}

/* Exact four calls made by root:m1CE2:f_1CE2_01F8, including negative-width
 * coordinates and their order. The installed g_9134 sink decides raster edge
 * conventions, but the source argument tuples remain unchanged here. */
static int append_outline(PortableMenuDropdownDrawCommand *commands,
                          size_t capacity, size_t *count,
                          PortableMenuDropdownRect rect, int width,
                          int16_t color)
{
    int64_t l1 = (int64_t)rect.left + width;
    int64_t t1 = (int64_t)rect.top + width;
    int64_t r1 = (int64_t)rect.right - width;
    int64_t b1 = (int64_t)rect.bottom - width;
    if (l1 < INT32_MIN || l1 > INT32_MAX || t1 < INT32_MIN || t1 > INT32_MAX ||
        r1 < INT32_MIN || r1 > INT32_MAX || b1 < INT32_MIN || b1 > INT32_MAX)
        return -1;
    return append_primitive(commands, capacity, count,
                            (int32_t)l1, (int32_t)t1, (int32_t)r1,
                            rect.top, color) &&
           append_primitive(commands, capacity, count,
                            (int32_t)l1, (int32_t)b1, (int32_t)r1,
                            rect.bottom, color) &&
           append_primitive(commands, capacity, count,
                            (int32_t)l1, rect.top, rect.left,
                            rect.bottom, color) &&
           append_primitive(commands, capacity, count,
                            rect.right, rect.top, (int32_t)r1,
                            rect.bottom, color);
}

static size_t max_item_length(const PortableMenuInteraction *interaction)
{
    size_t i, length = 0;
    for (i = 0; i < interaction->item_count; ++i)
        if (interaction->items[i].length > length)
            length = interaction->items[i].length;
    return length;
}

static int append_row(PortableMenuDropdownDrawCommand *commands,
                      size_t capacity, size_t *count,
                      uint8_t *storage, size_t storage_capacity,
                      size_t *storage_used,
                      const PortableMenuInteraction *interaction,
                      size_t row, int highlighted,
                      int16_t g5fea, int16_t g5fec, int16_t g5fee,
                      const int16_t mode_pen_color[4])
{
    size_t max_length = max_item_length(interaction), i;
    const PortableMenuItemSpan *item = &interaction->items[row];
    size_t needed;
    int color = highlighted ? 0 : 1;
    int mode;
    uint8_t *text;
    PortableMenuDropdownDrawCommand *command;
    if (max_length == 0 || max_length > SIZE_MAX - 1 ||
        *storage_used > storage_capacity || max_length + 1 > storage_capacity - *storage_used)
        return 0;
    needed = max_length + 1;
    text = storage + *storage_used;
    memset(text, ' ', max_length);
    if (item->length >= 2 && item->bytes[1] == '-') {
        if (max_length >= 2) {
            memset(text + 1, '-', max_length - 2);
            text[max_length - 1] = ' ';
        }
        text[0] = ' ';
    } else {
        memcpy(text, item->bytes, item->length);
    }
    text[max_length] = 0;
    mode = color + ((text[0] & 0x80u) != 0 ? 2 : 0);
    if (!append_mode(commands, capacity, count, mode, g5fea, g5fec,
                     g5fee, mode_pen_color))
        return 0;
    if (*count >= capacity) return 0;
    command = &commands[(*count)++];
    memset(command, 0, sizeof(*command));
    command->kind = PORTABLE_DROPDOWN_TEXT;
    command->mode = (int16_t)mode;
    command->x = interaction->inner_rect.left;
    command->y = interaction->inner_rect.top + (int32_t)row * interaction->line_height;
    command->text = text;
    command->text_length = max_length;
    command->clear_first_high_bit = (uint8_t)((text[0] & 0x80u) != 0);
    for (i = item->length; i < max_length; ++i)
        if (!(item->length >= 2 && item->bytes[1] == '-'))
            text[i] = ' ';
    *storage_used += needed;
    return 1;
}

static PortableMenuDropdownRenderStatus build_plan(
    const PortableMenuInteraction *interaction, int highlighted_item,
    int old_highlight, int do_outline,
    int16_t g5fea, int16_t g5fec, int16_t g5fee,
    const int16_t mode_pen_color[4],
    PortableMenuDropdownDrawCommand *commands, size_t capacity,
    uint8_t *storage, size_t storage_size,
    size_t *command_count, size_t *storage_used)
{
    size_t count = 0, used = 0, i;
    int32_t left, top, right, bottom;
    int outlined;
    if (interaction == NULL || mode_pen_color == NULL || commands == NULL ||
        command_count == NULL || storage_used == NULL ||
        (interaction->item_count != 0 && storage == NULL) ||
        interaction->item_count > 16 ||
        interaction->saved_rect.right < interaction->saved_rect.left ||
        interaction->saved_rect.bottom < interaction->saved_rect.top)
        return PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
    if (highlighted_item < -1 || highlighted_item >= (int)interaction->item_count ||
        old_highlight < -1 || old_highlight >= (int)interaction->item_count)
        return PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
    {
        int16_t source_pens[4];
        portable_menu_dropdown_source_pen_colors(g5fea, g5fec, g5fee,
                                                  source_pens);
        if (memcmp(source_pens, mode_pen_color, sizeof(source_pens)) != 0)
            return PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT;
    }
    if (do_outline) {
        if (!append_mode(commands, capacity, &count, 1, g5fea, g5fec, g5fee,
                         mode_pen_color)) goto too_small;
        left = interaction->saved_rect.left + interaction->char_width;
        right = interaction->saved_rect.right - interaction->char_width;
        top = interaction->saved_rect.top + 3;
        bottom = interaction->saved_rect.bottom - 3;
        if (left < INT32_MIN || left > INT32_MAX || right < INT32_MIN || right > INT32_MAX ||
            top < INT32_MIN || top > INT32_MAX || bottom < INT32_MIN || bottom > INT32_MAX)
            return PORTABLE_DROPDOWN_RENDER_COORDINATE_OVERFLOW;
        outlined = append_outline(commands, capacity, &count,
            (PortableMenuDropdownRect){left, top, right, bottom}, -3,
            mode_pen_color[1]);
        if (outlined < 0) return PORTABLE_DROPDOWN_RENDER_COORDINATE_OVERFLOW;
        if (!outlined) goto too_small;
        if (!append_mode(commands, capacity, &count, 0, g5fea, g5fec, g5fee,
                         mode_pen_color)) goto too_small;
        outlined = append_outline(commands, capacity, &count,
            (PortableMenuDropdownRect){left, top, right, bottom}, -1,
            mode_pen_color[0]);
        if (outlined < 0) return PORTABLE_DROPDOWN_RENDER_COORDINATE_OVERFLOW;
        if (!outlined) goto too_small;
        if (!append_mode(commands, capacity, &count, 1, g5fea, g5fec, g5fee,
                         mode_pen_color)) goto too_small;
        for (i = 0; i < interaction->item_count; ++i) {
            if (!append_row(commands, capacity, &count, storage, storage_size,
                            &used, interaction, i, (int)i == highlighted_item,
                            g5fea, g5fec, g5fee, mode_pen_color))
                goto too_small;
        }
    } else {
        if (old_highlight == highlighted_item) {
            *command_count = 0;
            *storage_used = 0;
            return PORTABLE_DROPDOWN_RENDER_OK;
        }
        if (old_highlight >= 0 &&
            !append_row(commands, capacity, &count, storage, storage_size,
                        &used, interaction, (size_t)old_highlight, 0,
                        g5fea, g5fec, g5fee, mode_pen_color))
            goto too_small;
        if (highlighted_item >= 0 &&
            !append_row(commands, capacity, &count, storage, storage_size,
                        &used, interaction, (size_t)highlighted_item, 1,
                        g5fea, g5fec, g5fee, mode_pen_color))
            goto too_small;
    }
    *command_count = count;
    *storage_used = used;
    return PORTABLE_DROPDOWN_RENDER_OK;

too_small:
    return PORTABLE_DROPDOWN_RENDER_OUTPUT_TOO_SMALL;
}

PortableMenuDropdownRenderStatus portable_menu_dropdown_build_open_plan(
    const PortableMenuInteraction *interaction, int highlighted_item,
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    const int16_t mode_pen_color[4],
    PortableMenuDropdownDrawCommand *commands, size_t command_capacity,
    uint8_t *text_storage, size_t text_storage_size,
    size_t *command_count, size_t *text_storage_used)
{
    if (interaction != NULL && interaction->item_count != 0 &&
        max_item_length(interaction) * (interaction->item_count + 1) > 4000)
        return PORTABLE_DROPDOWN_RENDER_TEXT_TOO_LONG;
    return build_plan(interaction, highlighted_item, -1, 1,
                      source_g5fea, source_g5fec, source_g5fee,
                      mode_pen_color, commands, command_capacity,
                      text_storage, text_storage_size,
                      command_count, text_storage_used);
}

PortableMenuDropdownRenderStatus portable_menu_dropdown_build_highlight_plan(
    const PortableMenuInteraction *interaction,
    int old_highlight, int new_highlight,
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    const int16_t mode_pen_color[4],
    PortableMenuDropdownDrawCommand *commands, size_t command_capacity,
    uint8_t *text_storage, size_t text_storage_size,
    size_t *command_count, size_t *text_storage_used)
{
    return build_plan(interaction, new_highlight, old_highlight, 0,
                      source_g5fea, source_g5fec, source_g5fee,
                      mode_pen_color, commands, command_capacity,
                      text_storage, text_storage_size,
                      command_count, text_storage_used);
}

const char *portable_menu_dropdown_render_status_string(
    PortableMenuDropdownRenderStatus status)
{
    switch (status) {
    case PORTABLE_DROPDOWN_RENDER_OK: return "ok";
    case PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_DROPDOWN_RENDER_OUTPUT_TOO_SMALL: return "output too small";
    case PORTABLE_DROPDOWN_RENDER_TEXT_TOO_LONG: return "menu text exceeds source buffer";
    case PORTABLE_DROPDOWN_RENDER_COORDINATE_OVERFLOW: return "coordinate overflow";
    case PORTABLE_DROPDOWN_RENDER_INVALID_FONT: return "invalid BIOS reference font";
    }
    return "unknown status";
}
