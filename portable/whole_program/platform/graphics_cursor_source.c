#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics_cursor_source.h"

#include "graphics_bitmap_source.h"
#include "graphics_capture_source.h"
#include "graphics_entry_source.h"
#include "graphics_source_clip.h"
#include "m1b73_mouse_state.h"
#include "portable/whole_program/state/asm_display_data_v1.h"
#include "portable/whole_program/window_source_rects.h"

#include <string.h>

/* These are the four Handle globals defined by the actual root:m1B28 source
 * module. Their pointee data remains owned by the database handle manager. */
extern char **g_3D10;
extern char **g_3D14;
extern char **g_3D18;
extern char **g_3D1C;

extern uint8_t SaveUnder[
    SIM_GRAPHICS_SOURCE_CURSOR_SAVE_UNDER_BYTES];

static SimGraphicsCursorSource *active_cursor;

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int16_t signed_word(uint16_t bits)
{
    int16_t result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}

static int add_source_words(int16_t a, uint16_t b, uint16_t c,
                            int16_t *out)
{
    uint16_t bits = (uint16_t)((uint16_t)a + b + c);
    *out = signed_word(bits);
    return 1;
}

static int bitmap_extent(const uint8_t *resource, size_t resource_size,
                         unsigned planes, uint16_t *width_out,
                         uint16_t *height_out)
{
    uint16_t width, height;
    size_t row_bytes, required;
    if (resource == NULL || resource_size < 4u)
        return 0;
    width = read_u16(resource);
    height = read_u16(resource + 2);
    if (width == 0 || height == 0)
        return 0;
    row_bytes = ((size_t)width + 7u) / 8u;
    if ((planes != 1u && planes != 4u) ||
        row_bytes > (SIZE_MAX - 4u) / planes / height)
        return 0;
    required = 4u + row_bytes * planes * height;
    if (required > resource_size)
        return 0;
    *width_out = width;
    *height_out = height;
    return 1;
}

static int resolve_source_handle(SimGraphicsCursorSource *cursor,
                                 char **handle,
                                 const uint8_t **resource,
                                 size_t *resource_size)
{
    if (handle == NULL || *handle == NULL || resource == NULL ||
        resource_size == NULL || cursor->bindings.resolve_handle == NULL)
        return 0;
    return cursor->bindings.resolve_handle(cursor->bindings.context, handle,
                                            resource, resource_size) &&
           *resource != NULL;
}

SimGraphicsStatus sim_graphics_source_cursor_bind(
    SimGraphicsCursorSource *cursor,
    const SimGraphicsCursorSourceBindings *bindings)
{
    if (cursor == NULL || bindings == NULL || active_cursor != NULL ||
        bindings->graphics == NULL ||
        bindings->graphics != sim_graphics_source_owner() ||
        bindings->graphics->pixel_storage == NULL ||
        bindings->source_shift_state == NULL ||
        bindings->hide_rectangle_active == NULL ||
        bindings->hide_rectangle == NULL ||
        bindings->resolve_handle == NULL ||
        bindings->measure_active_resource == NULL ||
        (*( SimGraphicsCaptureSizeCallback *)(void *)&driver_callback_table[6]) == NULL || (*( SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8]) == NULL ||
        (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9]) == NULL || (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[11]) == NULL || (*( SimGraphicsAttrCallback *)(void *)&driver_callback_table[0]) == NULL || (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[14]) == NULL ||
        (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[15]) == NULL || (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[16]) == NULL || (*( SimGraphicsLogicOperationCallback *)(void *)&driver_callback_table[23]) == NULL ||
        sim_graphics_source_clip_owner() != bindings->graphics)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    memset(cursor, 0, sizeof(*cursor));
    cursor->bindings = *bindings;
    cursor->bound = 1;
    active_cursor = cursor;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_cursor_unbind(SimGraphicsCursorSource *cursor)
{
    if (cursor == NULL || active_cursor != cursor)
        return;
    active_cursor = NULL;
    memset(cursor, 0, sizeof(*cursor));
}

static int select_cursor_bitmaps(SimGraphicsCursorSource *cursor,
                                 const uint8_t **first,
                                 size_t *first_size,
                                 const uint8_t **second,
                                 size_t *second_size)
{
    PortableM1B73MouseAsmState *mouse = &portable_m1b73_mouse_asm_state;
    const int16_t *hide = cursor->bindings.hide_rectangle;
    const int16_t x = *mouse->x;
    const int16_t y = *mouse->y;

    /* _0DA4 first selects the hide-rectangle pair when an alternate mask is
     * loaded, no hot-box owns the pointer, and the pointer lies in that rect.
     * Its machine-code order is important: [first,second] feed AND then XOR. */
    if (g_3D1C != NULL && *cursor->bindings.hide_rectangle_active != 0 &&
        mouse->active_hotbox_token == 0 && x >= hide[0] && x <= hide[2] &&
        y >= hide[1] && y <= hide[3]) {
        if (!resolve_source_handle(cursor, g_3D1C, first, first_size) ||
            !resolve_source_handle(cursor, g_3D18, second, second_size))
            return 0;
    } else {
        if (mouse->cursor_image == NULL || *mouse->cursor_image == NULL ||
            mouse->cursor_mask == NULL || *mouse->cursor_mask == NULL)
            return 0;
        *first = *mouse->cursor_image;
        *second = *mouse->cursor_mask;
        if (!cursor->bindings.measure_active_resource(
                cursor->bindings.context, *first, first_size) ||
            !cursor->bindings.measure_active_resource(
                cursor->bindings.context, *second, second_size))
            return 0;
    }

    /* Shift-state resources override the hide-rectangle selection. This is
     * the exact final branch in _0DA4 (g_3D14 -> AND, g_3D10 -> XOR). */
    if (*cursor->bindings.source_shift_state != 0 && g_3D14 != NULL) {
        if (!resolve_source_handle(cursor, g_3D14, first, first_size) ||
            !resolve_source_handle(cursor, g_3D10, second, second_size))
            return 0;
    }
    return 1;
}

static int source_status_ok(SimGraphicsCursorSource *cursor)
{
    return cursor->bindings.graphics->last_status == SIM_GRAPHICS_OK;
}

static int draw_saved_cursor(SimGraphicsCursorSource *cursor)
{
    PortableM1B73MouseAsmState *mouse = &portable_m1b73_mouse_asm_state;
    uint8_t old_display_lock = (uint8_t)g_21A4;
    g_21A4 = 1;
    f_1B4E_003B((int16_t)mouse->cursor_x[0], (int16_t)mouse->cursor_y[0],
                (char *)SaveUnder);
    g_21A4 = (char)old_display_lock;
    return source_status_ok(cursor);
}

static int draw_active_cursor(SimGraphicsCursorSource *cursor)
{
    PortableM1B73MouseAsmState *mouse = &portable_m1b73_mouse_asm_state;
    const uint8_t *first, *second;
    size_t first_size, second_size;
    uint16_t width, height, second_width, second_height;
    int16_t x, y, right, bottom;
    uint8_t old_display_lock;

    if (!select_cursor_bitmaps(cursor, &first, &first_size,
                               &second, &second_size) ||
        !bitmap_extent(first, first_size, 1u, &width, &height) ||
        !bitmap_extent(second, second_size, 4u, &second_width, &second_height) ||
        width != second_width || height != second_height)
        return 0;

    /* S00 aligns the cursor left edge down to an 8-pixel byte boundary. The
     * source rectangles use low-word arithmetic, including their +7 margin. */
    x = signed_word((uint16_t)mouse->x[0] & UINT16_C(0xfff8));
    y = mouse->y[0];
    add_source_words(x, width, 7u, &right);
    add_source_words(y, height, 0u, &bottom);
    *mouse->cursor_x = (uint16_t)x;
    *mouse->cursor_y = (uint16_t)y;
    *mouse->cursor_right = (uint16_t)right;
    *mouse->cursor_bottom = (uint16_t)bottom;
    old_display_lock = (uint8_t)g_21A4;
    g_21A4 = 1;
    if (sim_graphics_source_capture_cursor_buffer(
            SaveUnder,
            sizeof(SaveUnder)) != SIM_GRAPHICS_OK) {
        g_21A4 = (char)old_display_lock;
        cursor->bindings.graphics->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        return 0;
    }
    (*( SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8])(x, y, right, bottom,
           (char *)SaveUnder);
    sim_graphics_source_capture_cursor_buffer_clear(
        SaveUnder);
    if (!source_status_ok(cursor)) {
        g_21A4 = (char)old_display_lock;
        return 0;
    }
    (*( SimGraphicsAttrCallback *)(void *)&driver_callback_table[0])((int16_t)UINT16_C(0xff0f), 0, 0);
    if (!source_status_ok(cursor)) {
        g_21A4 = (char)old_display_lock;
        return 0;
    }
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[15])();
    g_21A4 = 0;
    f_1B4E_005E(x, y, (char *)first);
    if (!source_status_ok(cursor)) {
        g_21A4 = (char)old_display_lock;
        return 0;
    }
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[14])();
    f_1B4E_003B(x, y, (char *)second);
    g_21A4 = (char)old_display_lock;
    return source_status_ok(cursor);
}

int portable_m1b73_graphics_cursor_mode(void *context, uint8_t mode,
                                        int16_t *source_ax)
{
    SimGraphicsCursorSource *cursor = (SimGraphicsCursorSource *)context;
    SimGraphicsDriver *graphics;
    struct Rect **clip_slot;
    struct Rect *old_clip;
    struct Rect full_screen_clip_list[2];
    int16_t old_left_cut, old_right_cut, old_logic;
    uint8_t old_foreground, old_background, old_pattern;
    int ok;
    if (cursor == NULL || cursor != active_cursor || !cursor->bound ||
        source_ax == NULL || (mode != 1 && mode != 2))
        return 0;
    graphics = cursor->bindings.graphics;
    clip_slot = &g_5AAC;
    old_clip = *clip_slot;
    old_left_cut = fd_55B3_3DE6;
    old_right_cut = fd_55B3_3DE8;
    old_logic = g_3DD2;
    old_foreground = g_3DE0;
    old_background = g_3DE2;
    old_pattern = g_3DE4;

    /* `_0122` temporarily makes g5A9C the active full-screen clip entry.
     * Its native owner is one Rect, while m1D8E walks a sentinel-terminated
     * list, so adapt that single source entry to a one-entry call-local list. */
    full_screen_clip_list[0] = g_5A9C[0];
    full_screen_clip_list[1] = (struct Rect){ 0, INT16_MIN, 0, 0 };
    *clip_slot = full_screen_clip_list;
    (*( SimGraphicsFontCallback *)(void *)&driver_callback_table[16])();
    ok = mode == 1 ? draw_active_cursor(cursor) : draw_saved_cursor(cursor);
    (*( SimGraphicsAttrCallback *)(void *)&driver_callback_table[0])((int16_t)old_foreground, (int16_t)old_background,
           (int16_t)old_pattern);
    (*( SimGraphicsLogicOperationCallback *)(void *)&driver_callback_table[23])(old_logic);
    *clip_slot = old_clip;
    fd_55B3_3DE6 = old_left_cut;
    fd_55B3_3DE8 = old_right_cut;
    if (!ok) {
        graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
        return 0;
    }
    /* _0DA4 explicitly clears AX. Mode 2's far C-wrapper return register is
     * not a source-level result; D4B does not consume it after dispatch. */
    *source_ax = 0;
    cursor->bindings.graphics->last_status = SIM_GRAPHICS_OK;
    return 1;
}
