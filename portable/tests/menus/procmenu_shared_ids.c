#include "../../ui_model/menus/menu.h"

#include <inttypes.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    PortableDatabase database = {0};
    PortableMenuBar menu;
    size_t menu_index;
    if (argc != 2) return 2;
    if (portable_db_open(&database, argv[1]) != PORTABLE_DB_OK) return 3;
    portable_menu_init(&menu);
    if (portable_menu_load(&menu, &database, 640) != PORTABLE_MENU_OK) return 4;
    printf("resource_id=%d menu_count=%u\n", menu.resource_id,
           (unsigned)menu.menu_count);
    for (menu_index = 0; menu_index < menu.menu_count; ++menu_index) {
        size_t item_index;
        const PortableMenuString *title = portable_menu_title(&menu, menu_index);
        const uint8_t *title_bytes = portable_menu_string_bytes(&menu, title);
        printf("title|%zu|", menu_index);
        for (size_t i = 0; i < title->length; ++i)
            printf("%02x", title_bytes[i]);
        putchar('\n');
        for (item_index = 0; item_index < menu.items[menu_index].count;
             ++item_index) {
            const PortableMenuString *item = portable_menu_item(&menu,
                menu_index, item_index);
            const uint8_t *bytes = portable_menu_string_bytes(&menu, item);
            unsigned command_id = (unsigned)((menu_index * 16 + item_index + 1) & 0xffu);
            printf("item|%zu|%zu|%u|", menu_index, item_index, command_id);
            for (size_t i = 0; i < item->length; ++i)
                printf("%02x", bytes[i]);
            putchar('\n');
        }
    }
    portable_menu_release(&menu);
    portable_db_close(&database);
    return 0;
}
