#ifndef SIMANT_PORTABLE_UI_MODEL_INPUT_INPUT_H
#define SIMANT_PORTABLE_UI_MODEL_INPUT_INPUT_H

#include <stddef.h>
#include <stdint.h>

enum {
    PORTABLE_INPUT_MAX_EFFECTS = 3,
    PORTABLE_INPUT_EDIT_WINDOW = 0,
    PORTABLE_INPUT_MAP_WINDOW = 0x0100,
    PORTABLE_INPUT_MODE_WINDOW = 0x1200,
    PORTABLE_INPUT_CASTE_WINDOW = 0x1300,
    PORTABLE_INPUT_KEY_CTRL = 0x1d,
    PORTABLE_INPUT_SCAN_NW = 0x47,
    PORTABLE_INPUT_SCAN_NE = 0x49,
    PORTABLE_INPUT_SCAN_SW = 0x4f,
    PORTABLE_INPUT_SCAN_SE = 0x51,
    PORTABLE_INPUT_SCAN_E = 0x4d,
    PORTABLE_INPUT_SCAN_W = 0x4b,
    PORTABLE_INPUT_SCAN_N = 0x48,
    PORTABLE_INPUT_SCAN_S = 0x50
};

typedef enum PortableInputStatus {
    PORTABLE_INPUT_OK = 0,
    PORTABLE_INPUT_BAD_ARGUMENT,
    PORTABLE_INPUT_NO_KEY,
    PORTABLE_INPUT_MODIFIER_ONLY,
    PORTABLE_INPUT_UNBOUND,
    PORTABLE_INPUT_UNSUPPORTED_ACTION,
    PORTABLE_INPUT_INVALID_STATE,
    PORTABLE_INPUT_INVALID_PAN
} PortableInputStatus;

typedef enum PortableInputEffectKind {
    PORTABLE_INPUT_EFFECT_SET_PAUSED = 1,
    PORTABLE_INPUT_EFFECT_SET_SPEED,
    PORTABLE_INPUT_EFFECT_SET_MAP_PLANE,
    PORTABLE_INPUT_EFFECT_SET_YARD_MODE,
    PORTABLE_INPUT_EFFECT_OPEN_EDIT,
    PORTABLE_INPUT_EFFECT_OPEN_MAP_YARD,
    PORTABLE_INPUT_EFFECT_OPEN_MODE,
    PORTABLE_INPUT_EFFECT_OPEN_CASTE,
    PORTABLE_INPUT_EFFECT_ENSURE_YARD_VIEW
} PortableInputEffectKind;

typedef struct PortableInputEffect {
    PortableInputEffectKind kind;
    int16_t value;
} PortableInputEffect;

typedef struct PortableInputEffects {
    PortableInputEffect items[PORTABLE_INPUT_MAX_EFFECTS];
    size_t count;
} PortableInputEffects;

/* Convert the host's BIOS word (scan in AH, ASCII in AL) to the logical key
 * returned by f_1F58_0090. Modifier-only BIOS words are consumed separately
 * by the host and produce PORTABLE_INPUT_MODIFIER_ONLY. */
PortableInputStatus portable_input_decode_bios_key(
    uint16_t bios_key, int16_t *logical_key);

/* Input key is the source's returned key code from f_1F58_0090. */
PortableInputStatus portable_input_key(
    uint16_t key, int16_t paused, int16_t map_plane, int16_t yard_mode,
    int16_t yard_window_open,
    PortableInputEffects *effects);

/* Apply the source ProcMenu switch to an item number, without running game or
 * host services. Unsupported menu items are explicit failures. */
PortableInputStatus portable_input_menu_item(
    uint8_t item, int16_t paused, int16_t map_plane, int16_t yard_mode,
    int16_t yard_window_open,
    PortableInputEffects *effects);

/* Source object-code branches retained from ProcEditEvent and ProcMapEvent. */
PortableInputStatus portable_input_edit_event(
    uint16_t object_code, int16_t paused, PortableInputEffects *effects);
PortableInputStatus portable_input_map_event(
    uint16_t object_code, PortableInputEffects *effects);

/* Held keyboard camera movement from the main event pump. The keypad scan
 * codes are combined in source order and are active only while Control is held. */
PortableInputStatus portable_input_camera_delta(
    int control_down, const uint16_t *held_scan_codes, size_t held_count,
    int16_t *dx, int16_t *dy);

/* Edge scrolling in f_00F8_01BE. Set movement_blocked when the original
 * f_1B73_0EEE helper reports a blocking input state. */
PortableInputStatus portable_input_mouse_edge_delta(
    int movement_blocked, int16_t cursor_x, int16_t cursor_y,
    int16_t screen_width, int16_t screen_height,
    int16_t *dx, int16_t *dy);

/* Source f_0250_0D10 Bresenham-like camera step followed by f_0250_0F2C
 * bounds. The viewport dimensions are source cell counts (10E0/10DE). */
PortableInputStatus portable_input_pan_camera(
    int16_t plane, int16_t camera_x, int16_t camera_y,
    int16_t viewport_columns, int16_t viewport_rows,
    int16_t dx, int16_t dy, int16_t *out_x, int16_t *out_y);

const char *portable_input_status_string(PortableInputStatus status);

#endif
