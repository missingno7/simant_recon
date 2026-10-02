#include "interaction.h"

#include <limits.h>
#include <string.h>

static int contains(const PortableMenuDropdownRect *rect, int32_t x, int32_t y)
{
    return rect->left <= x && x < rect->right &&
           rect->top <= y && y < rect->bottom;
}

static int selectable(const PortableMenuInteraction *interaction, size_t index)
{
    const PortableMenuItemSpan *item = &interaction->items[index];
    if (item->length < 1 || item->bytes == NULL) return 0;
    return item->length < 2 ||
           (item->bytes[1] != (uint8_t)'-' && (item->bytes[0] & 0x80u) == 0);
}

static void finish(PortableMenuInteraction *interaction, int mouse_down)
{
    interaction->completed = 1;
    interaction->active = 0;
    interaction->returned = (uint8_t)(!mouse_down &&
                                      interaction->menu_index != -1);
    if (interaction->current_item >= 0) {
        interaction->selection = (uint8_t)(interaction->current_item + 1);
        interaction->selection_written = 1;
        if (interaction->menu_index != -1) {
            int command = ((int)interaction->menu_index << 4) +
                          interaction->current_item - 0x2ff;
            interaction->command_id = (int16_t)command;
            interaction->command_dispatched = interaction->returned;
        }
    }
}

PortableMenuInteractionStatus portable_menu_interaction_init(
    PortableMenuInteraction *interaction,
    const PortableMenuItemSpan *items, size_t item_count,
    int16_t menu_index, int32_t title_x, size_t title_length,
    int16_t screen_width, int16_t screen_height,
    int16_t line_height, int16_t char_width,
    uint8_t initial_selection)
{
    size_t i, max_length = 0;
    int32_t x, y, width, height, delta, half_chars;
    PortableMenuDropdownRect inner;
    if (interaction == NULL || items == NULL || item_count > 16 ||
        menu_index < 0 || screen_width <= 0 || screen_height <= 0 ||
        line_height <= 0 || char_width <= 0 || title_x < INT16_MIN ||
        title_x > INT16_MAX || title_length > (size_t)INT16_MAX)
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    memset(interaction, 0, sizeof(*interaction));
    interaction->item_count = item_count;
    interaction->menu_index = menu_index;
    interaction->current_item = -1;
    interaction->initial_selection = initial_selection;
    interaction->selection = initial_selection;
    interaction->active = 1;
    interaction->line_height = line_height;
    interaction->char_width = char_width;
    interaction->last_x = interaction->last_y = -1;
    if (item_count == 0) {
        interaction->selection = 0;
        interaction->selection_written = 1;
        interaction->returned = 1;
        interaction->active = 0;
        interaction->completed = 1;
        return PORTABLE_MENU_INTERACTION_NO_ITEMS;
    }
    for (i = 0; i < item_count; ++i) {
        if (items[i].bytes == NULL || items[i].length == 0)
            return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
        interaction->items[i] = items[i];
        if (items[i].length > max_length) max_length = items[i].length;
    }
    if (max_length > (size_t)INT32_MAX / (size_t)char_width)
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    /* In title-menu mode t == 1, so maxLen is the longest stored item string. */
    width = (int32_t)max_length * char_width;
    half_chars = (int32_t)title_length - (int32_t)max_length;
    /* MSC's signed SAR rounds negative odd values toward negative infinity. */
    if (half_chars < 0)
        half_chars = -(((-half_chars) + 1) / 2);
    else
        half_chars /= 2;
    x = title_x + half_chars * char_width;
    if (x < 0) x = 0;
    y = line_height + 1;
    interaction->saved_rect.left = x;
    interaction->saved_rect.top = y;
    interaction->saved_rect.right = x + width + 16;
    interaction->saved_rect.bottom = y + line_height * (int32_t)item_count + 6;
    if (interaction->saved_rect.right > screen_width) {
        delta = interaction->saved_rect.right - screen_width;
        interaction->saved_rect.right -= delta;
        interaction->saved_rect.left -= delta;
    }
    if (line_height + 5 > interaction->saved_rect.top)
        interaction->saved_rect.top = line_height + 5;
    interaction->saved_rect.bottom = line_height * (int32_t)item_count +
                                     interaction->saved_rect.top + 6;
    if (interaction->saved_rect.bottom > screen_height - 5) {
        delta = interaction->saved_rect.bottom - screen_height + 5;
        interaction->saved_rect.top -= delta;
        interaction->saved_rect.bottom -= delta;
    }
    inner = interaction->saved_rect;
    inner.left += char_width;
    inner.right -= char_width;
    inner.top += 3;
    inner.bottom -= 3;
    interaction->inner_rect = inner;
    height = line_height;
    for (i = 0; i < item_count; ++i) {
        interaction->row_rects[i] = (PortableMenuDropdownRect){
            inner.left, inner.top + (int32_t)i * height,
            inner.right, inner.top + ((int32_t)i + 1) * height};
        interaction->row_separator[i] = (uint8_t)(items[i].length >= 2 &&
                                                   items[i].bytes[1] == '-');
        interaction->row_enabled[i] = (uint8_t)selectable(interaction, i);
    }
    return PORTABLE_MENU_INTERACTION_RUNNING;
}

PortableMenuInteractionStatus portable_menu_interaction_init_from_bar(
    PortableMenuInteraction *interaction,
    const PortableMenuBar *menu, const PortableMenuLayout *layout,
    size_t menu_index, int16_t screen_width, int16_t screen_height,
    int16_t line_height, int16_t char_width, uint8_t initial_selection)
{
    PortableMenuItemSpan spans[16];
    const PortableMenuString *title;
    const uint8_t *title_bytes;
    size_t i, count;
    if (interaction == NULL || menu == NULL || layout == NULL ||
        !menu->loaded || menu_index >= menu->menu_count ||
        menu_index >= layout->title_count)
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    title = portable_menu_title(menu, menu_index);
    title_bytes = portable_menu_string_bytes(menu, title);
    if (title == NULL || title_bytes == NULL || title->length == 0)
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    if ((title_bytes[0] & 0x80u) != 0)
        return PORTABLE_MENU_INTERACTION_DISABLED_TITLE;
    count = menu->items[menu_index].count;
    if (count > sizeof(spans) / sizeof(spans[0]))
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    for (i = 0; i < count; ++i) {
        const PortableMenuString *string = portable_menu_item(menu, menu_index, i);
        if (string == NULL)
            return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
        spans[i] = (PortableMenuItemSpan){
            portable_menu_string_bytes(menu, string), string->length};
    }
    return portable_menu_interaction_init(interaction, spans, count,
        (int16_t)menu_index, layout->title_x[menu_index], title->length,
        screen_width, screen_height, line_height, char_width, initial_selection);
}

int portable_menu_title_hit(const PortableMenuBar *menu,
                            const PortableMenuLayout *layout,
                            int32_t x, int32_t y)
{
    size_t i;
    if (menu == NULL || layout == NULL || !menu->loaded ||
        layout->title_count > menu->titles.count)
        return -1;
    for (i = 0; i < layout->title_count; ++i) {
        const PortableMenuString *title = &menu->titles.strings[i];
        const uint8_t *bytes = portable_menu_string_bytes(menu, title);
        if (bytes == NULL || title->length == 0 || (bytes[0] & 0x80u) != 0)
            continue;
        if (layout->title_rects[i].left <= x &&
            x < layout->title_rects[i].right &&
            layout->title_rects[i].top <= y &&
            y < layout->title_rects[i].bottom)
            return (int)i;
    }
    return -1;
}

static int advance_item(const PortableMenuInteraction *interaction,
                        int current, int direction)
{
    size_t tries;
    int candidate = current;
    for (tries = 0; tries < interaction->item_count + 1; ++tries) {
        if (direction > 0) {
            candidate = (candidate + 1) % (int)interaction->item_count;
        } else {
            candidate = (candidate > 0 ? candidate : (int)interaction->item_count) - 1;
        }
        if (selectable(interaction, (size_t)candidate)) return candidate;
    }
    return current;
}

static int alpha_key(uint16_t key)
{
    return !(key & 0x800u) &&
           ((key >= 'A' && key <= 'Z') || (key >= 'a' && key <= 'z'));
}

static void key_input(PortableMenuInteraction *interaction, uint16_t key)
{
    int candidate, original, current, seen;
    uint8_t hotkey;
    if (!(key & 0x800u) && key >= 'a' && key <= 'z') key -= 0x20;
    switch (key) {
    case 10: case 13: case ' ': case 0x852: case 0x853:
        finish(interaction, 0);
        return;
    case 27:
        interaction->current_item = -1;
        finish(interaction, 0);
        return;
    case '+': case 0x850:
        candidate = advance_item(interaction, interaction->current_item, 1);
        if (candidate >= 0) {
            interaction->current_item = (int16_t)candidate;
            interaction->warp_x = (int16_t)(interaction->inner_rect.left +
                                             interaction->char_width * 3);
            interaction->warp_y = (int16_t)(interaction->line_height / 2 +
                                             interaction->line_height * candidate +
                                             interaction->inner_rect.top);
            interaction->warped_pointer = 1;
        }
        return;
    case '-': case 0x848:
        candidate = advance_item(interaction, interaction->current_item, -1);
        if (candidate >= 0) {
            interaction->current_item = (int16_t)candidate;
            interaction->warp_x = (int16_t)(interaction->inner_rect.left +
                                             interaction->char_width * 3);
            interaction->warp_y = (int16_t)(interaction->line_height / 2 +
                                             interaction->line_height * candidate +
                                             interaction->inner_rect.top);
            interaction->warped_pointer = 1;
        }
        return;
    default:
        break;
    }
    if (key & 0x800u) {
        interaction->flushed_key = (int16_t)(key & 0xffu);
        interaction->current_item = -1;
        finish(interaction, 0);
        return;
    }
    original = interaction->current_item;
    current = original;
    seen = 0;
    if (alpha_key(key)) {
        hotkey = (uint8_t)key;
        do {
            current = (current + 1) % (int)interaction->item_count;
            ++seen;
            if (interaction->items[current].length >= 2) {
                uint8_t character = interaction->items[current].bytes[1];
                if (character >= 'a' && character <= 'z') character -= 32;
                if (character == hotkey) {
                    interaction->current_item = (int16_t)current;
                    interaction->warp_x = (int16_t)(
                        interaction->inner_rect.left + interaction->char_width * 3);
                    interaction->warp_y = (int16_t)(
                        interaction->line_height / 2 + interaction->line_height * current +
                        interaction->inner_rect.top);
                    interaction->warped_pointer = 1;
                    return;
                }
            }
        } while (seen < (int)interaction->item_count);
    }
    interaction->current_item = (int16_t)original;
}

PortableMenuInteractionStatus portable_menu_interaction_step(
    PortableMenuInteraction *interaction, const PortableMenuInput *input)
{
    if (interaction == NULL || input == NULL || !interaction->active)
        return interaction != NULL && interaction->completed
            ? PORTABLE_MENU_INTERACTION_COMPLETE
            : PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    if (input->kind == PORTABLE_MENU_INPUT_POINTER_POLL) {
        if (interaction->button_down && !input->button_down) {
            interaction->button_down = 0;
            finish(interaction, 0);
            return PORTABLE_MENU_INTERACTION_COMPLETE;
        }
        if (!interaction->button_down && input->button_down)
            interaction->button_down = 1;
        if (interaction->button_down &&
            (interaction->last_x != input->x || interaction->last_y != input->y)) {
            int candidate = -1;
            size_t i;
            interaction->last_x = input->x;
            interaction->last_y = input->y;
            for (i = 0; i < interaction->item_count; ++i) {
                if (contains(&interaction->row_rects[i], input->x, input->y)) {
                    if (interaction->row_enabled[i]) candidate = (int)i;
                    break;
                }
            }
            interaction->current_item = (int16_t)candidate;
        }
    } else if (input->kind == PORTABLE_MENU_INPUT_KEY) {
        if (!interaction->button_down) key_input(interaction, input->key);
    } else if (input->kind == PORTABLE_MENU_INPUT_WINDOW_EVENT) {
        if ((input->event_code >> 8) == 0xfe &&
            (input->event_code & 0xffu) != (uint16_t)interaction->menu_index) {
            interaction->forwarded_event = 1;
            interaction->forwarded_event_words[0] = input->event_code;
            interaction->forwarded_event_words[1] = input->event_xe;
            interaction->forwarded_event_words[2] = input->event_h;
            interaction->forwarded_event_words[3] = input->event_v;
            interaction->forwarded_event_words[4] = 0;
            finish(interaction, interaction->button_down);
        }
    } else {
        return PORTABLE_MENU_INTERACTION_BAD_ARGUMENT;
    }
    return interaction->completed ? PORTABLE_MENU_INTERACTION_COMPLETE
                                  : PORTABLE_MENU_INTERACTION_RUNNING;
}

const char *portable_menu_interaction_status_string(
    PortableMenuInteractionStatus status)
{
    switch (status) {
    case PORTABLE_MENU_INTERACTION_RUNNING: return "running";
    case PORTABLE_MENU_INTERACTION_COMPLETE: return "complete";
    case PORTABLE_MENU_INTERACTION_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_MENU_INTERACTION_NO_ITEMS: return "no menu items";
    case PORTABLE_MENU_INTERACTION_DISABLED_TITLE: return "disabled menu title";
    }
    return "unknown menu interaction status";
}
