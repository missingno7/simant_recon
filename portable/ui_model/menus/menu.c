#include "menu.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

enum { MENU_RESOURCE_KIND = 6, MENU_WIDTH_320 = 320, MENU_MAX_TABLES = 17 };

static uint32_t read_u32le(const uint8_t *bytes)
{
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static void free_list(PortableMenuStringList *list)
{
    free(list->strings);
    list->strings = NULL;
    list->count = 0;
}

void portable_menu_init(PortableMenuBar *menu)
{
    if (menu != NULL)
        memset(menu, 0, sizeof(*menu));
}

void portable_menu_release(PortableMenuBar *menu)
{
    size_t i;
    if (menu == NULL)
        return;
    free_list(&menu->titles);
    for (i = 0; i < sizeof(menu->items) / sizeof(menu->items[0]); ++i)
        free_list(&menu->items[i]);
    portable_db_record_free(&menu->record);
    memset(menu, 0, sizeof(*menu));
}

static PortableMenuStatus parse_string_table(PortableMenuBar *menu,
                                             uint32_t table_offset,
                                             PortableMenuStringList *list)
{
    size_t cursor = table_offset;
    size_t count = 0;
    size_t capacity = 0;
    if (table_offset > menu->record.size)
        return PORTABLE_MENU_INVALID_RESOURCE;
    for (;;) {
        uint32_t string_offset;
        const uint8_t *terminator;
        PortableMenuString *grown;
        if (cursor > menu->record.size || menu->record.size - cursor < 4)
            return PORTABLE_MENU_INVALID_RESOURCE;
        string_offset = read_u32le(menu->record.data + cursor);
        cursor += 4;
        if (string_offset == 0)
            break;
        if (string_offset >= menu->record.size || count >= 16)
            return PORTABLE_MENU_INVALID_RESOURCE;
        terminator = (const uint8_t *)memchr(menu->record.data + string_offset,
                                             0, menu->record.size - string_offset);
        if (terminator == NULL)
            return PORTABLE_MENU_INVALID_RESOURCE;
        if (count == capacity) {
            size_t next_capacity = capacity == 0 ? 4 : capacity * 2;
            if (next_capacity > 16)
                next_capacity = 16;
            grown = (PortableMenuString *)realloc(list->strings,
                             next_capacity * sizeof(*list->strings));
            if (grown == NULL)
                return PORTABLE_MENU_OUT_OF_MEMORY;
            list->strings = grown;
            capacity = next_capacity;
        }
        list->strings[count].offset = string_offset;
        list->strings[count].length = (size_t)(terminator -
                                               (menu->record.data + string_offset));
        list->strings[count].capacity = 0;
        ++count;
    }
    list->count = count;
    return count == 0 ? PORTABLE_MENU_INVALID_RESOURCE : PORTABLE_MENU_OK;
}

static PortableMenuStatus parse_resource(PortableMenuBar *menu)
{
    uint32_t table_offsets[MENU_MAX_TABLES];
    size_t table_count = 0;
    size_t cursor = 0;
    size_t table_index;
    PortableMenuStatus status;
    if (menu->record.data == NULL || menu->record.size < 8 ||
        menu->record.kind != MENU_RESOURCE_KIND)
        return PORTABLE_MENU_INVALID_RESOURCE;
    for (;;) {
        uint32_t table_offset;
        if (cursor > menu->record.size || menu->record.size - cursor < 4)
            return PORTABLE_MENU_INVALID_RESOURCE;
        table_offset = read_u32le(menu->record.data + cursor);
        cursor += 4;
        if (table_offset == 0)
            break;
        if (table_offset >= menu->record.size || table_count >= MENU_MAX_TABLES)
            return PORTABLE_MENU_INVALID_RESOURCE;
        table_offsets[table_count++] = table_offset;
    }
    if (table_count < 2 || table_count > MENU_MAX_TABLES)
        return PORTABLE_MENU_INVALID_RESOURCE;
    status = parse_string_table(menu, table_offsets[0], &menu->titles);
    if (status != PORTABLE_MENU_OK)
        return status;
    menu->menu_count = (uint8_t)(table_count - 1);
    if (menu->titles.count != menu->menu_count)
        return PORTABLE_MENU_INVALID_RESOURCE;
    for (table_index = 1; table_index < table_count; ++table_index) {
        status = parse_string_table(menu, table_offsets[table_index],
                                    &menu->items[table_index - 1]);
        if (status != PORTABLE_MENU_OK)
            return status;
    }
    /* The loader's strings live in one relocated block. Bound mutations by
     * the next referenced string so _fstrcpy cannot overwrite another label. */
    for (table_index = 0; table_index < (size_t)menu->menu_count + 1;
         ++table_index) {
        PortableMenuStringList *list = table_index == 0
            ? &menu->titles : &menu->items[table_index - 1];
        size_t string_index;
        for (string_index = 0; string_index < list->count; ++string_index) {
            PortableMenuString *string = &list->strings[string_index];
            size_t next_offset = menu->record.size;
            size_t other_table;
            for (other_table = 0; other_table < (size_t)menu->menu_count + 1;
                 ++other_table) {
                PortableMenuStringList *other = other_table == 0
                    ? &menu->titles : &menu->items[other_table - 1];
                size_t other_index;
                for (other_index = 0; other_index < other->count; ++other_index) {
                    size_t offset = other->strings[other_index].offset;
                    if (offset > string->offset && offset < next_offset)
                        next_offset = offset;
                }
            }
            string->capacity = next_offset - string->offset;
            if (string->length + 1 > string->capacity)
                return PORTABLE_MENU_INVALID_RESOURCE;
        }
    }
    menu->loaded = 1;
    return PORTABLE_MENU_OK;
}

static PortableMenuStatus load_record(PortableMenuBar *menu,
                                      PortableDatabase *database,
                                      int16_t resource_id, int *missing)
{
    PortableDbStatus status = portable_db_load(database, resource_id,
                                                MENU_RESOURCE_KIND,
                                                &menu->record);
    if (missing != NULL)
        *missing = status == PORTABLE_DB_NOT_FOUND;
    if (status != PORTABLE_DB_OK)
        return status == PORTABLE_DB_OUT_OF_MEMORY
            ? PORTABLE_MENU_OUT_OF_MEMORY : PORTABLE_MENU_DATABASE_ERROR;
    menu->resource_id = resource_id;
    return parse_resource(menu);
}

PortableMenuStatus portable_menu_load(PortableMenuBar *menu,
                                     PortableDatabase *shared_database,
                                     uint16_t screen_width)
{
    PortableMenuBar loaded;
    PortableMenuStatus status;
    int missing = 0;
    if (menu == NULL || shared_database == NULL || screen_width == 0)
        return PORTABLE_MENU_BAD_ARGUMENT;
    portable_menu_init(&loaded);
    if (screen_width == MENU_WIDTH_320) {
        status = load_record(&loaded, shared_database, 0, NULL);
    } else {
        status = load_record(&loaded, shared_database, 1, &missing);
        if (missing)
            status = load_record(&loaded, shared_database, 0, NULL);
    }
    if (status != PORTABLE_MENU_OK) {
        portable_menu_release(&loaded);
        return status;
    }
    portable_menu_release(menu);
    *menu = loaded;
    return PORTABLE_MENU_OK;
}

const uint8_t *portable_menu_string_bytes(const PortableMenuBar *menu,
                                          const PortableMenuString *string)
{
    if (menu == NULL || string == NULL || !menu->loaded ||
        string->offset >= menu->record.size)
        return NULL;
    return menu->record.data + string->offset;
}

const PortableMenuString *portable_menu_title(const PortableMenuBar *menu,
                                               size_t title_index)
{
    if (menu == NULL || !menu->loaded || title_index >= menu->titles.count)
        return NULL;
    return &menu->titles.strings[title_index];
}

const PortableMenuString *portable_menu_item(const PortableMenuBar *menu,
                                              size_t menu_index,
                                              size_t item_index)
{
    if (menu == NULL || !menu->loaded || menu_index >= menu->menu_count ||
        item_index >= menu->items[menu_index].count)
        return NULL;
    return &menu->items[menu_index].strings[item_index];
}

static PortableMenuString *id_minus_one_string(PortableMenuBar *menu, int id)
{
    size_t menu_index, string_index;
    if (id < 0)
        return NULL;
    if ((id & 15) == 0) {
        menu_index = (size_t)(id >> 4);
        return menu_index < menu->titles.count
            ? &menu->titles.strings[menu_index] : NULL;
    }
    menu_index = (size_t)(id >> 4);
    string_index = (size_t)((id - 1) & 15);
    if (menu_index >= menu->menu_count ||
        string_index >= menu->items[menu_index].count)
        return NULL;
    return &menu->items[menu_index].strings[string_index];
}

PortableMenuStatus portable_menu_set_item_state(PortableMenuBar *menu,
                                                int id, uint8_t state)
{
    size_t menu_index, string_index;
    PortableMenuString *item;
    if (menu == NULL || !menu->loaded || id < 0)
        return PORTABLE_MENU_BAD_ARGUMENT;
    menu_index = (size_t)(id >> 4);
    string_index = (size_t)(id & 15);
    if (menu_index >= menu->menu_count ||
        string_index >= menu->items[menu_index].count)
        return PORTABLE_MENU_INDEX_OUT_OF_RANGE;
    item = &menu->items[menu_index].strings[string_index];
    menu->record.data[item->offset] = state;
    return PORTABLE_MENU_OK;
}

PortableMenuStatus portable_menu_set_text_by_id(PortableMenuBar *menu,
                                                int id, const char *text)
{
    PortableMenuString *string;
    size_t length;
    if (menu == NULL || !menu->loaded || text == NULL)
        return PORTABLE_MENU_BAD_ARGUMENT;
    string = id_minus_one_string(menu, id);
    if (string == NULL)
        return PORTABLE_MENU_INDEX_OUT_OF_RANGE;
    length = strlen(text);
    if (length + 1 > string->capacity)
        return PORTABLE_MENU_TEXT_TOO_LONG;
    memcpy(menu->record.data + string->offset, text, length + 1);
    string->length = length;
    return PORTABLE_MENU_OK;
}

PortableMenuStatus portable_menu_set_highlight_by_id(PortableMenuBar *menu,
                                                     int id, int highlighted)
{
    PortableMenuString *string;
    uint8_t *first;
    if (menu == NULL || !menu->loaded)
        return PORTABLE_MENU_BAD_ARGUMENT;
    string = id_minus_one_string(menu, id);
    if (string == NULL)
        return PORTABLE_MENU_INDEX_OUT_OF_RANGE;
    first = &menu->record.data[string->offset];
    if (highlighted)
        *first = (uint8_t)(*first | 0x80u);
    else
        *first = (uint8_t)(*first & 0x7fu);
    return PORTABLE_MENU_OK;
}

static const PortableMenuString *layout_string(const PortableMenuBar *menu,
                                                size_t index)
{
    return &menu->titles.strings[index];
}

PortableMenuStatus portable_menu_build_draw_plan(
    const PortableMenuBar *menu, int draw, PortableMenuRect screen_rect,
    int32_t screen_width, int32_t cell_width, int32_t cell_height,
    uint8_t fill_color, PortableMenuLayout *layout,
    PortableMenuDrawCommand *commands, size_t command_capacity,
    size_t *command_count)
{
    size_t needed = 1;
    size_t i;
    size_t count = 0;
    int64_t total_chars = 0;
    int32_t gap = 0;
    int32_t x = 0;
    if (menu == NULL || !menu->loaded || layout == NULL || commands == NULL ||
        command_count == NULL || screen_width <= 0 || cell_width <= 0 ||
        cell_height <= 0 || menu->titles.count > 16)
        return PORTABLE_MENU_BAD_ARGUMENT;
    if (draw) {
        needed += 1;
        if (menu->titles.count > 1)
            needed += menu->titles.count;
    }
    if (command_capacity < needed)
        return PORTABLE_MENU_OUTPUT_TOO_SMALL;
    memset(layout, 0, sizeof(*layout));
    layout->bar_rect = screen_rect;
    layout->bar_rect.bottom = screen_rect.top + cell_height + 3;
    memset(&commands[count], 0, sizeof(commands[count]));
    commands[count].kind = PORTABLE_MENU_DRAW_SET_COLOR_MODE;
    commands[count].source_color_mode = 1;
    ++count;
    if (draw) {
        memset(&commands[count], 0, sizeof(commands[count]));
        commands[count].kind = PORTABLE_MENU_DRAW_FILL_RECT;
        commands[count].rect = layout->bar_rect;
        commands[count].fill_color = fill_color;
        ++count;
    }
    layout->title_count = menu->titles.count;
    if (menu->titles.count > 1) {
        for (i = 0; i < menu->titles.count; ++i)
            total_chars += (int64_t)layout_string(menu, i)->length;
        gap = (int32_t)(((int64_t)(screen_width / cell_width) - total_chars) /
                        (int64_t)(menu->titles.count - 1));
        if (gap > 3) gap = 3;
        else if (gap < 1) gap = 1;
        for (i = 0; i < menu->titles.count; ++i) {
            const PortableMenuString *string = layout_string(menu, i);
            const uint8_t *text = portable_menu_string_bytes(menu, string);
            int32_t width;
            uint8_t highlighted;
            if (string->length > (size_t)(INT32_MAX / cell_width))
                return PORTABLE_MENU_INVALID_RESOURCE;
            width = (int32_t)string->length * cell_width;
            layout->title_x[i] = x;
            layout->title_region_ids[i] = (int16_t)i - 0x0200;
            layout->title_rects[i].left = x;
            layout->title_rects[i].top = 1;
            layout->title_rects[i].right = x + width;
            layout->title_rects[i].bottom = cell_height + 1;
            if (draw) {
                highlighted = (uint8_t)((text[0] & 0x80u) != 0);
                memset(&commands[count], 0, sizeof(commands[count]));
                commands[count].kind = PORTABLE_MENU_DRAW_TEXT;
                commands[count].source_color_mode = highlighted ? 3 : 1;
                commands[count].x = x;
                commands[count].y = 1;
                commands[count].text = text;
                commands[count].text_length = string->length;
                commands[count].clear_first_high_bit = highlighted;
                ++count;
            }
            x += ((int32_t)string->length + gap) * cell_width;
        }
    }
    layout->gap_cells = gap;
    *command_count = count;
    return PORTABLE_MENU_OK;
}

const char *portable_menu_status_string(PortableMenuStatus status)
{
    switch (status) {
    case PORTABLE_MENU_OK: return "ok";
    case PORTABLE_MENU_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_MENU_DATABASE_ERROR: return "database error";
    case PORTABLE_MENU_INVALID_RESOURCE: return "invalid menu resource";
    case PORTABLE_MENU_OUT_OF_MEMORY: return "out of memory";
    case PORTABLE_MENU_INDEX_OUT_OF_RANGE: return "menu index out of range";
    case PORTABLE_MENU_TEXT_TOO_LONG: return "menu text exceeds source storage";
    case PORTABLE_MENU_OUTPUT_TOO_SMALL: return "draw plan buffer too small";
    default: return "unknown";
    }
}
