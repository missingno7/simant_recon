#include "../../ui_model/menus/interaction.h"

#include <assert.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    PortableDatabase shared = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[20];
    PortableMenuInteraction interaction;
    PortableMenuInteractionStatus status;
    size_t command_count = 0, item, i;
    int16_t original_title_state;
    int hit;
    if (argc != 2) {
        fprintf(stderr, "usage: test-menu-interaction asset-directory\n");
        return 2;
    }
    if (portable_db_open(&shared, argv[1]) != PORTABLE_DB_OK) {
        fprintf(stderr, "SHARED open failed: %s\n", portable_db_error(&shared));
        return 1;
    }
    portable_menu_init(&menu);
    assert(portable_menu_load(&menu, &shared, 640) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.menu_count > 0);
    assert(portable_menu_build_draw_plan(&menu, 1,
        (PortableMenuRect){0, 0, 640, 350}, 640, 8, 14, 0,
        &layout, commands, sizeof(commands) / sizeof(commands[0]),
        &command_count) == PORTABLE_MENU_OK);
    assert(command_count > 2 && layout.title_count == menu.titles.count);
    hit = portable_menu_title_hit(&menu, &layout,
        (layout.title_rects[0].left + layout.title_rects[0].right) / 2,
        (layout.title_rects[0].top + layout.title_rects[0].bottom) / 2);
    assert(hit == 0);
    assert(portable_menu_title_hit(&menu, &layout,
        layout.title_rects[0].left, layout.title_rects[0].top) == 0);
    assert(portable_menu_title_hit(&menu, &layout,
        layout.title_rects[0].right, layout.title_rects[0].top) == -1);
    assert(portable_menu_title_hit(&menu, &layout,
        layout.title_rects[0].left, layout.title_rects[0].bottom) == -1);
    original_title_state = menu.record.data[menu.titles.strings[0].offset];
    menu.record.data[menu.titles.strings[0].offset] |= 0x80u;
    assert(portable_menu_title_hit(&menu, &layout,
        (layout.title_rects[0].left + layout.title_rects[0].right) / 2,
        (layout.title_rects[0].top + layout.title_rects[0].bottom) / 2) == -1);
    assert(portable_menu_interaction_init_from_bar(&interaction, &menu, &layout,
        0, 640, 350, 14, 8, 0) ==
        PORTABLE_MENU_INTERACTION_DISABLED_TITLE);
    menu.record.data[menu.titles.strings[0].offset] = (uint8_t)original_title_state;

    item = menu.items[0].count;
    assert(item > 0 && item <= 16);
    status = portable_menu_interaction_init_from_bar(&interaction, &menu,
        &layout, 0, 640, 350, 14, 8, 0);
    assert(status == PORTABLE_MENU_INTERACTION_RUNNING);
    for (i = 0; i < item && interaction.current_item == -1; ++i) {
        PortableMenuInput input = {PORTABLE_MENU_INPUT_KEY, 0, 0, 0,
                                   '+', 0, 0, 0, 0};
        assert(portable_menu_interaction_step(&interaction, &input) ==
               PORTABLE_MENU_INTERACTION_RUNNING);
    }
    if (interaction.current_item >= 0) {
        PortableMenuInput enter = {PORTABLE_MENU_INPUT_KEY, 0, 0, 0,
                                   13, 0, 0, 0, 0};
        assert(portable_menu_interaction_step(&interaction, &enter) ==
               PORTABLE_MENU_INTERACTION_COMPLETE);
        assert(interaction.returned && interaction.selection_written &&
               interaction.command_dispatched);
        assert(interaction.command_id == interaction.current_item - 0x2ff);
    }
    printf("actual SHARED menu id %d: %u titles, %zu first-menu items, title-hit and state gating verified\n",
           menu.resource_id, menu.menu_count, item);
    portable_menu_release(&menu);
    portable_db_close(&shared);
    return 0;
}
