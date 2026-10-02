#ifndef SIMANT_PORTABLE_UI_MODEL_MENUS_MENU_H
#define SIMANT_PORTABLE_UI_MODEL_MENUS_MENU_H

#include "../../game/resources/database.h"

typedef struct PortableMenuString {
    uint32_t offset;
    size_t length;   /* Source _fstrlen, including the leading state glyph. */
    size_t capacity; /* Bounded by the next referenced string in the resource. */
} PortableMenuString;

typedef struct PortableMenuStringList {
    PortableMenuString *strings;
    size_t count;
} PortableMenuStringList;

typedef struct PortableMenuBar {
    PortableDbRecord record; /* Owns the original SHARED kind-6 resource. */
    PortableMenuStringList titles;
    PortableMenuStringList items[16];
    int16_t resource_id;
    uint8_t menu_count;
    uint8_t loaded;
} PortableMenuBar;

typedef struct PortableMenuRect {
    int32_t left, top, right, bottom;
} PortableMenuRect;

typedef struct PortableMenuLayout {
    PortableMenuRect bar_rect;
    PortableMenuRect title_rects[16];
    int32_t title_x[16];
    int16_t title_region_ids[16]; /* S17 calls f_1FD2_03EB with i - 0x200. */
    int32_t gap_cells;
    size_t title_count;
} PortableMenuLayout;

typedef enum PortableMenuDrawCommandKind {
    PORTABLE_MENU_DRAW_SET_COLOR_MODE = 0,
    PORTABLE_MENU_DRAW_FILL_RECT,
    PORTABLE_MENU_DRAW_TEXT
} PortableMenuDrawCommandKind;

typedef struct PortableMenuDrawCommand {
    PortableMenuDrawCommandKind kind;
    int16_t source_color_mode; /* f_1FD2_02B1 argument for text selection. */
    PortableMenuRect rect;
    int32_t x, y;
    uint8_t fill_color;
    const uint8_t *text; /* Borrowed from menu; leading high bit is source state. */
    size_t text_length;
    uint8_t clear_first_high_bit; /* f_1FD2_0008 strips this in its private copy. */
} PortableMenuDrawCommand;

typedef enum PortableMenuStatus {
    PORTABLE_MENU_OK = 0,
    PORTABLE_MENU_BAD_ARGUMENT,
    PORTABLE_MENU_DATABASE_ERROR,
    PORTABLE_MENU_INVALID_RESOURCE,
    PORTABLE_MENU_OUT_OF_MEMORY,
    PORTABLE_MENU_INDEX_OUT_OF_RANGE,
    PORTABLE_MENU_TEXT_TOO_LONG,
    PORTABLE_MENU_OUTPUT_TOO_SMALL
} PortableMenuStatus;

void portable_menu_init(PortableMenuBar *menu);
void portable_menu_release(PortableMenuBar *menu);

/* Source S20 tries SHARED kind 6/id 1 outside 320-pixel mode, then falls back
 * to id 0. At 320 pixels it loads id 0 directly. Initialize the destination
 * with portable_menu_init before first load/release. */
PortableMenuStatus portable_menu_load(PortableMenuBar *menu,
                                     PortableDatabase *shared_database,
                                     uint16_t screen_width);

const uint8_t *portable_menu_string_bytes(const PortableMenuBar *menu,
                                          const PortableMenuString *string);
const PortableMenuString *portable_menu_title(const PortableMenuBar *menu,
                                               size_t title_index);
const PortableMenuString *portable_menu_item(const PortableMenuBar *menu,
                                              size_t menu_index,
                                              size_t item_index);

/* Source SetMenuItemState uses items[id >> 4][id & 15] directly. */
PortableMenuStatus portable_menu_set_item_state(PortableMenuBar *menu,
                                                int id, uint8_t state);
/* Source f_1FD2_0135 uses title[index] for a low nibble of zero, otherwise
 * items[id >> 4][(id - 1) & 15], then performs _fstrcpy. */
PortableMenuStatus portable_menu_set_text_by_id(PortableMenuBar *menu,
                                                int id, const char *text);
/* Source f_1FD2_0198/f_1FD2_021B toggle bit 7 on the id-minus-one address. */
PortableMenuStatus portable_menu_set_highlight_by_id(PortableMenuBar *menu,
                                                     int id, int highlighted);

/* Source f_1FD2_0663/f_1FD2_0008 menu-bar order, geometry and style contract.
 * screen_rect and cell sizes are the values returned by the original window
 * and font services; fill_color is g_3DE2 | g_3DE4 from the active renderer. */
PortableMenuStatus portable_menu_build_draw_plan(
    const PortableMenuBar *menu, int draw, PortableMenuRect screen_rect,
    int32_t screen_width, int32_t cell_width, int32_t cell_height,
    uint8_t fill_color, PortableMenuLayout *layout,
    PortableMenuDrawCommand *commands, size_t command_capacity,
    size_t *command_count);

const char *portable_menu_status_string(PortableMenuStatus status);

#endif
