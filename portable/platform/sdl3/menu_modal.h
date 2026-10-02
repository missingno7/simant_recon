#ifndef SIMANT_PORTABLE_SDL3_MENU_MODAL_H
#define SIMANT_PORTABLE_SDL3_MENU_MODAL_H

#include "../host.h"
#include "../../ui_model/menus/dropdown_render.h"
#include "../../ui_model/menus/render.h"

/* Optional bridge for the original window-event queue. It must return a
 * complete, source-normalized code/xE/h/v event; this SDL layer cannot derive
 * xE from HostEvent. Return 1 for an event, 0 for empty, and -1 on failure. */
typedef int (*PortableMenuModalSourceEventPoll)(
    void *context, PortableMenuInput *event);

typedef enum PortableMenuModalStatus {
    PORTABLE_MENU_MODAL_COMMAND = 0,
    PORTABLE_MENU_MODAL_RETURNED,
    PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT,
    PORTABLE_MENU_MODAL_PHYSICAL_TITLE_EVENT,
    PORTABLE_MENU_MODAL_QUIT,
    PORTABLE_MENU_MODAL_BAD_ARGUMENT,
    PORTABLE_MENU_MODAL_INTERACTION_ERROR,
    PORTABLE_MENU_MODAL_RENDER_ERROR,
    PORTABLE_MENU_MODAL_HOST_ERROR,
    PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT,
    PORTABLE_MENU_MODAL_RESTORE_ERROR
} PortableMenuModalStatus;

typedef struct PortableMenuModalRequest {
    const PortableMenuBar *menu;
    const PortableMenuLayout *layout;
    PortableFramebuffer *framebuffer;
    const PortableBiosFontBitmap *font;
    const HostPalette *host_palette;
    int16_t screen_width, screen_height;
    int16_t line_height, char_width;
    int16_t source_g5fea, source_g5fec, source_g5fee;
    size_t menu_index;
    uint8_t initial_selection;
    int initial_left_button_down;
    int32_t initial_x, initial_y;
    PortableMenuModalSourceEventPoll poll_source_event;
    void *source_event_context;
    volatile int *quit_flag;
} PortableMenuModalRequest;

typedef struct PortableMenuModalResult {
    int16_t command_id;
    uint8_t selection;
    uint8_t selection_written;
    uint8_t returned;
    int16_t flushed_key;
    uint8_t forwarded_event;
    uint16_t forwarded_event_words[5];
    uint8_t physical_title_index_valid;
    uint8_t physical_title_index;
    int16_t physical_title_x, physical_title_y;
    uint8_t input_state_valid;
    int16_t pointer_x, pointer_y;
    uint8_t left_button_down;
    uint8_t observed_dos_modifiers;
} PortableMenuModalResult;

/* Runs one source title-targeted dropdown over an already loaded SHARED menu.
 * The caller owns the menu bar and its prior title rendering. The modal saves
 * only the popup rectangle, handles SDL keyboard/pointer input, and restores
 * those pixels before returning. Physical clicks on a different title return
 * their title index and coordinates for the caller's source event translator;
 * this host adapter does not invent the source event xE field. */
PortableMenuModalStatus portable_menu_modal_run(
    Host *host, const PortableMenuModalRequest *request,
    PortableMenuModalResult *result);

const char *portable_menu_modal_status_string(PortableMenuModalStatus status);

#endif
