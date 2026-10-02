#include "input.h"

#include <string.h>

typedef struct KeyBinding {
    uint16_t key;
    uint16_t source_code;
} KeyBinding;

/* Exact g_2CBE table from S19:m384C.c. */
static const KeyBinding key_bindings[] = {
    {0x821, 0xfe00}, {0x811, 0xfe01}, {0x82f, 0xfe02},
    {0x818, 0xfe03}, {0x81f, 0xfe04}, {0x83c, 0xfe00},
    {0x83d, 0xfe01}, {0x83e, 0xfe02}, {0x83f, 0xfe03},
    {0x840, 0xfe04}, {0x29, 0xfd41}, {0x21, 0xfd43},
    {0x40, 0xfd44}, {0x23, 0xfd45}, {0x24, 0xfd46},
    {0x0e, 0xfd03}, {0x13, 0xfd05}, {0x01, 0xfd06},
    {0x0c, 0xfd04}, {0x05, 0xfd11}, {0x0d, 0xfd12},
    {0x02, 0xfd13}, {0x03, 0xfd14}, {0x14, 0xfd17},
    {0x07, 0xfd31}, {0x0a, 0xfd32}, {0x0b, 0xfd33},
    {0x18, 0xfd08}, {0x11, 0xfd08}, {0x19, 0xfd21}
};

PortableInputStatus portable_input_decode_bios_key(
    uint16_t bios_key, int16_t *logical_key)
{
    uint8_t scan = (uint8_t)(bios_key >> 8);
    uint8_t ascii = (uint8_t)bios_key;
    if (logical_key == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    *logical_key = 0;
    if (ascii != 0) {
        /* CBW in f_1F58_005A sign-extends the low BIOS ASCII byte. */
        *logical_key = (ascii & 0x80u) != 0
            ? (int16_t)((int)ascii - 256) : (int16_t)ascii;
        return PORTABLE_INPUT_OK;
    }
    if (scan == 0) return PORTABLE_INPUT_NO_KEY;
    if (scan == 0x1d || scan == 0x2a || scan == 0x36 || scan == 0x38)
        return PORTABLE_INPUT_MODIFIER_ONLY;
    /* f_1F58_0090's second f_1F58_005A call returns the pending scan
     * with AH set to 8. */
    *logical_key = (int16_t)(0x0800u | scan);
    return PORTABLE_INPUT_OK;
}

static PortableInputStatus add(PortableInputEffects *effects,
                               PortableInputEffectKind kind, int16_t value)
{
    if (effects == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    if (effects->count >= PORTABLE_INPUT_MAX_EFFECTS)
        return PORTABLE_INPUT_INVALID_STATE;
    effects->items[effects->count].kind = kind;
    effects->items[effects->count].value = value;
    effects->count++;
    return PORTABLE_INPUT_OK;
}

PortableInputStatus portable_input_menu_item(
    uint8_t item, int16_t paused, int16_t map_plane, int16_t yard_mode,
    int16_t yard_window_open,
    PortableInputEffects *effects)
{
    PortableInputStatus status;
    if (effects == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    memset(effects, 0, sizeof(*effects));
    if ((paused != 0 && paused != 1) || map_plane < 0 || map_plane > 3 ||
        yard_mode < 0 || yard_mode > 3 ||
        (yard_window_open != 0 && yard_window_open != 1))
        return PORTABLE_INPUT_INVALID_STATE;
    switch (item) {
    case 0x11:
        return add(effects, PORTABLE_INPUT_EFFECT_OPEN_EDIT, 0);
    case 0x12:
        return add(effects, PORTABLE_INPUT_EFFECT_OPEN_MAP_YARD, 0);
    case 0x13:
        return add(effects, PORTABLE_INPUT_EFFECT_OPEN_MODE, 0);
    case 0x14:
        return add(effects, PORTABLE_INPUT_EFFECT_OPEN_CASTE, 0);
    case 0x21: case 0x22: case 0x23: case 0x24:
        if (item - 0x21 != yard_mode) {
            status = add(effects, PORTABLE_INPUT_EFFECT_SET_YARD_MODE,
                         (int16_t)(item - 0x21));
            if (status != PORTABLE_INPUT_OK) return status;
        }
        if (map_plane != 0)
            status = add(effects, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE, 0);
        else
            status = PORTABLE_INPUT_OK;
        if (status != PORTABLE_INPUT_OK) return status;
        if (!yard_window_open)
            return add(effects, PORTABLE_INPUT_EFFECT_ENSURE_YARD_VIEW, 0);
        return PORTABLE_INPUT_OK;
    case 0x26: case 0x27: case 0x28:
        return add(effects, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE,
                   (int16_t)(item - 0x25));
    case 0x41:
        return add(effects, PORTABLE_INPUT_EFFECT_SET_PAUSED,
                   (int16_t)!paused);
    case 0x43: case 0x44: case 0x45: case 0x46:
        return add(effects, PORTABLE_INPUT_EFFECT_SET_SPEED,
                   (int16_t)(item - 0x43));
    default:
        return PORTABLE_INPUT_UNSUPPORTED_ACTION;
    }
}

PortableInputStatus portable_input_key(
    uint16_t key, int16_t paused, int16_t map_plane, int16_t yard_mode,
    int16_t yard_window_open,
    PortableInputEffects *effects)
{
    size_t i;
    if (effects == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    memset(effects, 0, sizeof(*effects));
    for (i = 0; i < sizeof(key_bindings) / sizeof(key_bindings[0]); ++i) {
        if (key_bindings[i].key != key) continue;
        if ((key_bindings[i].source_code & 0xff00u) == 0xfd00u)
            return portable_input_menu_item(
                (uint8_t)key_bindings[i].source_code, paused,
                map_plane, yard_mode, yard_window_open, effects);
        return PORTABLE_INPUT_UNSUPPORTED_ACTION;
    }
    return PORTABLE_INPUT_UNBOUND;
}

PortableInputStatus portable_input_edit_event(
    uint16_t object_code, int16_t paused, PortableInputEffects *effects)
{
    if (effects == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    memset(effects, 0, sizeof(*effects));
    if (paused != 0 && paused != 1) return PORTABLE_INPUT_INVALID_STATE;
    switch (object_code) {
    case 8: case 9: case 10:
        return add(effects, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE,
                   (int16_t)(object_code - 7));
    case 15:
        return add(effects, PORTABLE_INPUT_EFFECT_SET_PAUSED,
                   (int16_t)!paused);
    default:
        return PORTABLE_INPUT_UNSUPPORTED_ACTION;
    }
}

PortableInputStatus portable_input_map_event(
    uint16_t object_code, PortableInputEffects *effects)
{
    if (effects == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    memset(effects, 0, sizeof(*effects));
    if (object_code >= 0x106 && object_code <= 0x108)
        return add(effects, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE,
                   (int16_t)(object_code - 0x105));
    return PORTABLE_INPUT_UNSUPPORTED_ACTION;
}

PortableInputStatus portable_input_camera_delta(
    int control_down, const uint16_t *held_scan_codes, size_t held_count,
    int16_t *dx, int16_t *dy)
{
    size_t i;
    int x = 0, y = 0;
    if (dx == NULL || dy == NULL || (held_count != 0 && held_scan_codes == NULL))
        return PORTABLE_INPUT_BAD_ARGUMENT;
    *dx = *dy = 0;
    if (!control_down) return PORTABLE_INPUT_OK;
    for (i = 0; i < held_count; ++i) {
        switch (held_scan_codes[i]) {
        case PORTABLE_INPUT_SCAN_NW: --x; --y; break;
        case PORTABLE_INPUT_SCAN_NE: ++x; --y; break;
        case PORTABLE_INPUT_SCAN_SW: --x; ++y; break;
        case PORTABLE_INPUT_SCAN_SE: ++x; ++y; break;
        case PORTABLE_INPUT_SCAN_E: ++x; break;
        case PORTABLE_INPUT_SCAN_W: --x; break;
        case PORTABLE_INPUT_SCAN_N: --y; break;
        case PORTABLE_INPUT_SCAN_S: ++y; break;
        default: break;
        }
    }
    if (x < -32768 || x > 32767 || y < -32768 || y > 32767)
        return PORTABLE_INPUT_INVALID_STATE;
    *dx = (int16_t)x;
    *dy = (int16_t)y;
    return PORTABLE_INPUT_OK;
}

PortableInputStatus portable_input_mouse_edge_delta(
    int movement_blocked, int16_t cursor_x, int16_t cursor_y,
    int16_t screen_width, int16_t screen_height,
    int16_t *dx, int16_t *dy)
{
    if (dx == NULL || dy == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    *dx = *dy = 0;
    if (screen_width <= 0 || screen_height <= 0)
        return PORTABLE_INPUT_INVALID_STATE;
    if (movement_blocked) return PORTABLE_INPUT_OK;
    if (cursor_x <= 1) *dx = -1;
    else if (cursor_x >= screen_width - 4) *dx = 1;
    if (cursor_y < 1) *dy = -1;
    else if (cursor_y >= screen_height - 4) *dy = 1;
    return PORTABLE_INPUT_OK;
}

static void clamp_camera(int16_t plane, int16_t columns, int16_t rows,
                         int32_t *x, int32_t *y)
{
    int32_t map_width = (plane == 0 || plane == 1) ? 0x80 : 0x40;
    if (*x < 0) *x = 0;
    else if (*x + columns > map_width) *x = map_width - columns;
    if (*y < 0) *y = 0;
    else if (*y + rows > 0x40) *y = 0x40 - rows;
}

PortableInputStatus portable_input_pan_camera(
    int16_t plane, int16_t camera_x, int16_t camera_y,
    int16_t viewport_columns, int16_t viewport_rows,
    int16_t dx, int16_t dy, int16_t *out_x, int16_t *out_y)
{
    int32_t x = camera_x, y = camera_y;
    int32_t x_distance = dx, y_distance = dy;
    int32_t x_step = 1, y_step = 1;
    uint32_t error = 0, fraction;
    int32_t i;
    if (out_x == NULL || out_y == NULL) return PORTABLE_INPUT_BAD_ARGUMENT;
    if (plane < 0 || plane > 3 || viewport_columns <= 0 || viewport_rows <= 0 ||
        viewport_columns > ((plane <= 1) ? 0x80 : 0x40) || viewport_rows > 0x40)
        return PORTABLE_INPUT_INVALID_PAN;
    if (x_distance < 0) { x_distance = -x_distance; x_step = -1; }
    if (y_distance < 0) { y_distance = -y_distance; y_step = -1; }
    if (x_distance == 0 && y_distance == 0) {
        clamp_camera(plane, viewport_columns, viewport_rows, &x, &y);
        *out_x = (int16_t)x;
        *out_y = (int16_t)y;
        return PORTABLE_INPUT_OK;
    }
    if (y_distance >= x_distance) {
        fraction = (uint32_t)(((uint64_t)(uint32_t)x_distance << 16) /
                              (uint32_t)y_distance);
        for (i = 0; i < y_distance; ++i) {
            y += y_step;
            error += fraction;
            if ((error >> 16) & 1u) {
                x += x_step;
                error ^= 0x10000u;
            }
        }
    } else {
        fraction = (uint32_t)(((uint64_t)(uint32_t)y_distance << 16) /
                              (uint32_t)x_distance);
        for (i = 0; i < x_distance; ++i) {
            x += x_step;
            error += fraction;
            if ((error >> 16) & 1u) {
                y += y_step;
                error ^= 0x10000u;
            }
        }
    }
    clamp_camera(plane, viewport_columns, viewport_rows, &x, &y);
    *out_x = (int16_t)x;
    *out_y = (int16_t)y;
    return PORTABLE_INPUT_OK;
}

const char *portable_input_status_string(PortableInputStatus status)
{
    switch (status) {
    case PORTABLE_INPUT_OK: return "ok";
    case PORTABLE_INPUT_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_INPUT_NO_KEY: return "no BIOS key";
    case PORTABLE_INPUT_MODIFIER_ONLY: return "modifier-only BIOS key";
    case PORTABLE_INPUT_UNBOUND: return "unbound key";
    case PORTABLE_INPUT_UNSUPPORTED_ACTION: return "unsupported source action";
    case PORTABLE_INPUT_INVALID_STATE: return "invalid source state";
    case PORTABLE_INPUT_INVALID_PAN: return "unsupported camera pan";
    }
    return "unknown input model error";
}
