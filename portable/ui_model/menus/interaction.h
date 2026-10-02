#ifndef SIMANT_PORTABLE_UI_MODEL_MENUS_INTERACTION_H
#define SIMANT_PORTABLE_UI_MODEL_MENUS_INTERACTION_H

#include "menu.h"

typedef struct PortableMenuItemSpan {
    const uint8_t *bytes; /* Actual source string, including state byte. */
    size_t length;        /* Length excluding its NUL terminator. */
} PortableMenuItemSpan;

typedef struct PortableMenuDropdownRect {
    int32_t left, top, right, bottom;
} PortableMenuDropdownRect;

typedef enum PortableMenuInputKind {
    PORTABLE_MENU_INPUT_POINTER_POLL = 1,
    PORTABLE_MENU_INPUT_KEY,
    PORTABLE_MENU_INPUT_WINDOW_EVENT
} PortableMenuInputKind;

typedef struct PortableMenuInput {
    PortableMenuInputKind kind;
    int32_t x, y;
    int button_down;
    uint16_t key;       /* f_1F58_0090 logical key code. */
    uint16_t event_code;
    uint16_t event_xe, event_h, event_v;
} PortableMenuInput;

typedef enum PortableMenuInteractionStatus {
    PORTABLE_MENU_INTERACTION_RUNNING = 0,
    PORTABLE_MENU_INTERACTION_COMPLETE,
    PORTABLE_MENU_INTERACTION_BAD_ARGUMENT,
    PORTABLE_MENU_INTERACTION_NO_ITEMS,
    PORTABLE_MENU_INTERACTION_DISABLED_TITLE
} PortableMenuInteractionStatus;

typedef struct PortableMenuInteraction {
    PortableMenuItemSpan items[16];
    size_t item_count;
    int16_t menu_index;
    int16_t current_item;
    uint8_t initial_selection;
    uint8_t selection;
    uint8_t selection_written;
    uint8_t active;
    uint8_t button_down;
    uint8_t completed;
    uint8_t returned;
    uint8_t command_dispatched;
    uint8_t forwarded_event;
    int16_t command_id;
    uint16_t forwarded_event_words[5];
    int16_t flushed_key;
    int16_t warp_x, warp_y;
    uint8_t warped_pointer;
    PortableMenuDropdownRect saved_rect;
    PortableMenuDropdownRect inner_rect;
    PortableMenuDropdownRect row_rects[16];
    uint8_t row_enabled[16];
    uint8_t row_separator[16];
    int32_t line_height;
    int32_t char_width;
    int32_t last_x, last_y;
} PortableMenuInteraction;

/* Build the title-targeted pull-down geometry and hit rows using the exact
 * S10 o10_35F5_0384 equations. Current-menu selection is limited to actual
 * resource-backed menus; popup/context menus (menu_index == -1) stay outside
 * this API until their caller contract is recovered. */
PortableMenuInteractionStatus portable_menu_interaction_init(
    PortableMenuInteraction *interaction,
    const PortableMenuItemSpan *items, size_t item_count,
    int16_t menu_index, int32_t title_x, size_t title_length,
    int16_t screen_width, int16_t screen_height,
    int16_t line_height, int16_t char_width,
    uint8_t initial_selection);

/* Resource-backed convenience entry: borrows menu strings for the lifetime
 * of `menu` and copies item spans into the interaction state. */
PortableMenuInteractionStatus portable_menu_interaction_init_from_bar(
    PortableMenuInteraction *interaction,
    const PortableMenuBar *menu, const PortableMenuLayout *layout,
    size_t menu_index, int16_t screen_width, int16_t screen_height,
    int16_t line_height, int16_t char_width, uint8_t initial_selection);

/* Title hit follows f_1FD2_03EB's inclusive/exclusive region and the
 * high-bit title suppression in o10_35F5_01C3. Returns a title index or -1. */
int portable_menu_title_hit(const PortableMenuBar *menu,
                            const PortableMenuLayout *layout,
                            int32_t x, int32_t y);

/* One source menu-loop input step. Keyboard movement skips separators and
 * high-bit disabled items; activation returns the DOS menu command ID. */
PortableMenuInteractionStatus portable_menu_interaction_step(
    PortableMenuInteraction *interaction,
    const PortableMenuInput *input);

const char *portable_menu_interaction_status_string(
    PortableMenuInteractionStatus status);

#endif
