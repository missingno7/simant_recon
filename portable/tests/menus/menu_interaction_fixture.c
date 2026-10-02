#include "../../ui_model/menus/interaction.h"

#include <stddef.h>
#include <stdint.h>

typedef struct PortableMenuInteractionFixtureResult {
    int32_t saved_rect[4];
    int32_t inner_rect[4];
    int16_t current_item;
    int16_t command_id;
    int16_t flushed_key;
    int16_t warp_x, warp_y;
    uint16_t init_status;
    uint16_t final_status;
    uint16_t returned;
    uint16_t selection_written;
    uint16_t selection;
    uint16_t command_dispatched;
    uint16_t forwarded_event;
    uint16_t warped_pointer;
    uint16_t forwarded_event_words[5];
} PortableMenuInteractionFixtureResult;

int portable_menu_interaction_fixture_run(
    const PortableMenuItemSpan *items, size_t item_count, int16_t menu_index,
    int32_t title_x, size_t title_length,
    int16_t screen_width, int16_t screen_height,
    int16_t line_height, int16_t char_width, uint8_t initial_selection,
    const PortableMenuInput *inputs, size_t input_count,
    PortableMenuInteractionFixtureResult *result)
{
    PortableMenuInteraction interaction;
    PortableMenuInteractionStatus status;
    size_t i;
    if (result == NULL || (input_count != 0 && inputs == NULL)) return -1;
    status = portable_menu_interaction_init(&interaction, items, item_count,
        menu_index, title_x, title_length, screen_width, screen_height,
        line_height, char_width, initial_selection);
    result->init_status = (uint16_t)status;
    if (status == PORTABLE_MENU_INTERACTION_RUNNING) {
        for (i = 0; i < input_count && status ==
             PORTABLE_MENU_INTERACTION_RUNNING; ++i)
            status = portable_menu_interaction_step(&interaction, &inputs[i]);
    }
    result->final_status = (uint16_t)status;
    result->saved_rect[0] = interaction.saved_rect.left;
    result->saved_rect[1] = interaction.saved_rect.top;
    result->saved_rect[2] = interaction.saved_rect.right;
    result->saved_rect[3] = interaction.saved_rect.bottom;
    result->inner_rect[0] = interaction.inner_rect.left;
    result->inner_rect[1] = interaction.inner_rect.top;
    result->inner_rect[2] = interaction.inner_rect.right;
    result->inner_rect[3] = interaction.inner_rect.bottom;
    result->current_item = interaction.current_item;
    result->command_id = interaction.command_id;
    result->flushed_key = interaction.flushed_key;
    result->warp_x = interaction.warp_x;
    result->warp_y = interaction.warp_y;
    result->returned = interaction.returned;
    result->selection_written = interaction.selection_written;
    result->selection = interaction.selection;
    result->command_dispatched = interaction.command_dispatched;
    result->forwarded_event = interaction.forwarded_event;
    result->warped_pointer = interaction.warped_pointer;
    for (i = 0; i < 5; ++i)
        result->forwarded_event_words[i] = interaction.forwarded_event_words[i];
    return 0;
}
