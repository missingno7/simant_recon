#include "../../ui_model/menus/menu.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void assert_text(const PortableMenuBar *menu,
                        const PortableMenuString *string,
                        const char *text)
{
    const uint8_t *bytes = portable_menu_string_bytes(menu, string);
    assert(bytes != NULL);
    assert(string->length == strlen(text));
    assert(memcmp(bytes, text, string->length + 1) == 0);
}

int main(int argc, char **argv)
{
    PortableDatabase shared = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[20];
    PortableMenuRect screen = {0, 0, 640, 350};
    size_t command_count = 0;
    const PortableMenuString *string;
    const uint8_t *bytes;
    size_t expected_items[] = {8, 7, 8, 6, 6};
    size_t i;
    const PortableDbIndexEntry *entry = NULL;
    char shared_path[1024];
    assert(argc == 2);
    portable_menu_init(&menu);
    assert(snprintf(shared_path, sizeof(shared_path), "%s/SHARED", argv[1]) <
           (int)sizeof(shared_path));
    assert(portable_db_open(&shared, shared_path) == PORTABLE_DB_OK);
    assert(portable_db_lookup(&shared, 1, 6, &entry, NULL) == PORTABLE_DB_NOT_FOUND);
    assert(entry == NULL);
    /* S20 tries id 1 at this width, sees it missing in this pinned asset set,
     * then loads the actual id 0 kind-6 fallback. */
    assert(portable_menu_load(&menu, &shared, 640) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.record.kind == 6 &&
           menu.record.size == 514 && menu.menu_count == 5);
    assert(menu.titles.count == 5);
    for (i = 0; i < 5; ++i) {
        assert(menu.items[i].count == expected_items[i]);
        assert(portable_menu_item(&menu, i, menu.items[i].count) == NULL);
    }
    assert_text(&menu, portable_menu_title(&menu, 0), " File");
    assert_text(&menu, portable_menu_title(&menu, 1), " Window");
    assert_text(&menu, portable_menu_title(&menu, 2), " View");
    assert_text(&menu, portable_menu_title(&menu, 3), " Options");
    assert_text(&menu, portable_menu_title(&menu, 4), " Speed");
    assert_text(&menu, portable_menu_item(&menu, 4, 0), " Pause  ");
    assert(portable_menu_item(&menu, 4, 0)->capacity == 9);
    assert_text(&menu, portable_menu_item(&menu, 4, 1), "---");
    assert_text(&menu, portable_menu_item(&menu, 4, 2), " Slow");

    /* The source state setter indexes [id >> 4][id & 15] directly, while the
     * text/highlight helpers use [id >> 4][(id - 1) & 15]. */
    string = portable_menu_item(&menu, 4, 0);
    bytes = portable_menu_string_bytes(&menu, string);
    assert(portable_menu_set_item_state(&menu, 0x41, 0x20) == PORTABLE_MENU_OK);
    assert(portable_menu_string_bytes(&menu, portable_menu_item(&menu, 4, 0))[0] == ' ');
    assert(portable_menu_string_bytes(&menu, portable_menu_item(&menu, 4, 1))[0] == 0x20);
    assert(bytes == portable_menu_string_bytes(&menu, string));
    assert(portable_menu_set_item_state(&menu, 0x42, 0x10) == PORTABLE_MENU_OK);
    assert(portable_menu_string_bytes(&menu, portable_menu_item(&menu, 4, 2))[0] == 0x10);
    assert(portable_menu_set_item_state(&menu, 0x46, 0x10) ==
           PORTABLE_MENU_INDEX_OUT_OF_RANGE);
    assert(portable_menu_set_text_by_id(&menu, 0x41, " Unpause") == PORTABLE_MENU_OK);
    assert_text(&menu, portable_menu_item(&menu, 4, 0), " Unpause");
    assert(portable_menu_string_bytes(&menu, portable_menu_item(&menu, 4, 1))[0] == 0x20);
    assert(portable_menu_set_text_by_id(&menu, 0x41,
               " string longer than allocated source slot") ==
           PORTABLE_MENU_TEXT_TOO_LONG);
    assert_text(&menu, portable_menu_item(&menu, 4, 0), " Unpause");
    assert(portable_menu_set_highlight_by_id(&menu, 0x41, 1) == PORTABLE_MENU_OK);
    assert((portable_menu_string_bytes(&menu,
            portable_menu_item(&menu, 4, 0))[0] & 0x80u) != 0);
    assert(portable_menu_set_highlight_by_id(&menu, 0x41, 0) == PORTABLE_MENU_OK);

    assert(portable_menu_set_highlight_by_id(&menu, 0x00, 1) == PORTABLE_MENU_OK);
    assert(portable_menu_build_draw_plan(&menu, 1, screen, 640, 8, 14,
                 0x0f, &layout, commands, 20, &command_count) == PORTABLE_MENU_OK);
    assert(command_count == 7 && layout.title_count == 5 && layout.gap_cells == 3);
    assert(layout.bar_rect.left == 0 && layout.bar_rect.top == 0 &&
           layout.bar_rect.right == 640 && layout.bar_rect.bottom == 17);
    assert(layout.title_x[0] == 0 && layout.title_x[1] == 64 &&
           layout.title_x[2] == 144 && layout.title_x[3] == 208 &&
           layout.title_x[4] == 296);
    assert(layout.title_region_ids[0] == -0x200 &&
           layout.title_region_ids[4] == -0x1fc);
    assert(layout.title_rects[0].left == 0 && layout.title_rects[0].top == 1 &&
           layout.title_rects[0].right == 40 && layout.title_rects[0].bottom == 15);
    assert(commands[0].kind == PORTABLE_MENU_DRAW_SET_COLOR_MODE &&
           commands[0].source_color_mode == 1);
    assert(commands[1].kind == PORTABLE_MENU_DRAW_FILL_RECT &&
           commands[1].fill_color == 0x0f);
    assert(commands[2].kind == PORTABLE_MENU_DRAW_TEXT &&
           commands[2].source_color_mode == 3 &&
           commands[2].clear_first_high_bit && commands[2].x == 0 &&
           commands[2].y == 1);
    assert(commands[2].text == portable_menu_string_bytes(&menu,
                                             portable_menu_title(&menu, 0)));
    assert(portable_menu_build_draw_plan(&menu, 0, screen, 640, 8, 14,
                 0x0f, &layout, commands, 20, &command_count) == PORTABLE_MENU_OK);
    assert(command_count == 1 && commands[0].kind == PORTABLE_MENU_DRAW_SET_COLOR_MODE);
    assert(portable_menu_build_draw_plan(&menu, 1, screen, 640, 8, 14,
                 0x0f, &layout, commands, 1, &command_count) ==
           PORTABLE_MENU_OUTPUT_TOO_SMALL);

    portable_menu_release(&menu);
    portable_menu_init(&menu);
    assert(portable_menu_load(&menu, &shared, 320) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.menu_count == 5);
    portable_menu_release(&menu);
    portable_db_close(&shared);
    puts("menu resource/state/layout tests passed");
    return 0;
}
