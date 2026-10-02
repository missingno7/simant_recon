#include "../../ui_model/menus/interaction.h"

#include <stdio.h>
#include <string.h>

static void print_text(const PortableMenuBar *menu,
                       const PortableMenuString *string)
{
    const uint8_t *bytes = portable_menu_string_bytes(menu, string);
    size_t i;
    for (i = 0; bytes != NULL && i < string->length; ++i)
        putchar(bytes[i] & 0x7fu);
}

int main(int argc, char **argv)
{
    PortableDatabase database = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand draw[32];
    PortableMenuInteraction interaction;
    size_t command_count = 0, title, row;
    if (argc != 2 || portable_db_open(&database, argv[1]) != PORTABLE_DB_OK)
        return 2;
    portable_menu_init(&menu);
    if (portable_menu_load(&menu, &database, 640) != PORTABLE_MENU_OK ||
        portable_menu_build_draw_plan(&menu, 1,
            (PortableMenuRect){0, 0, 640, 350}, 640, 8, 14, 0,
            &layout, draw, 32, &command_count) != PORTABLE_MENU_OK)
        return 3;
    printf("resource_id=%d title_count=%zu\n", menu.resource_id,
           menu.titles.count);
    for (title = 0; title < menu.titles.count; ++title) {
        const PortableMenuString *title_string = portable_menu_title(&menu, title);
        printf("title %zu x=%d rect=%d,%d,%d,%d text=\"", title,
               layout.title_x[title], layout.title_rects[title].left,
               layout.title_rects[title].top, layout.title_rects[title].right,
               layout.title_rects[title].bottom);
        print_text(&menu, title_string);
        puts("\"");
        if (portable_menu_interaction_init_from_bar(&interaction, &menu,
                &layout, title, 640, 350, 14, 8, 0) !=
            PORTABLE_MENU_INTERACTION_RUNNING)
            continue;
        for (row = 0; row < interaction.item_count; ++row) {
            const PortableMenuString *string = portable_menu_item(&menu,
                                                                  title, row);
            printf("  row %zu rect=%d,%d,%d,%d enabled=%u text=\"",
                   row, interaction.row_rects[row].left,
                   interaction.row_rects[row].top,
                   interaction.row_rects[row].right,
                   interaction.row_rects[row].bottom,
                   interaction.row_enabled[row]);
            print_text(&menu, string);
            puts("\"");
        }
    }
    portable_menu_release(&menu);
    portable_db_close(&database);
    return 0;
}
