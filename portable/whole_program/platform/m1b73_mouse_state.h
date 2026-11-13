#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_STATE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_STATE_H

#include <stdint.h>

/* Native owner for the ASM-owned cursor and mouse fields used by the SDL
 * adapter. The pointed-to image/mask resources are borrowed from the active
 * database/session and never outlive that owner. */
typedef struct PortableM1B73MouseAsmState {
    uint8_t *cursor_drawn;          /* source cursor_drawn_flag */
    uint8_t *cursor_event_pending;  /* source g_4332 */
    uint8_t *cursor_update_lock;    /* source cursor_update_lock */
    uint16_t *button_state;         /* shared source mouse_button_state word */
    int16_t *x;                     /* shared source mouse_x_pixels */
    int16_t *y;                     /* shared source mouse_y_pixels */
    uint16_t *cursor_x, *cursor_y;  /* source cursor_drawn_left/cursor_drawn_top */
    uint16_t *cursor_right; /* source cursor_drawn_right; _0DA4's right edge */
    uint16_t *cursor_bottom; /* source cursor_drawn_bottom; _0DA4's bottom edge */
    uint16_t *cursor_width, *cursor_height; /* source cursor_bitmap_width/cursor_bitmap_height */
    uint32_t *callback_count;       /* source g_4352 */
    uint32_t *mouse_event_count;    /* source g_4356 */
    uint16_t *cursor_initialized;   /* source g_435A */
    uint8_t *saved_keyboard_flags;  /* source g_433E, NumLock bit is used */
    uint8_t *cursor_show_level;     /* source cursor_show_level */
    uint8_t *hook_depth;            /* source g_53BC */
    uint8_t *mouse_mode;            /* source g_4DA4 */
    const uint8_t **cursor_image;   /* sidecar for source far pointer cursor_putimg_bitmap_pointer */
    const uint8_t **cursor_mask;    /* sidecar for source far pointer cursor_putpic_bitmap_pointer */
    uint32_t active_hotbox_token; /* native token replacing a far record pointer */
} PortableM1B73MouseAsmState;

/* Source initializers from m1B73.asm: zeroed fields above are `db/dw/dd 0`;
 * cursor dimensions alone begin at 0x16 by 0x16. */
extern PortableM1B73MouseAsmState portable_m1b73_mouse_asm_state;

/* The converted C callers also observe these same coordinate/modifier owners.
 * They are aliases exposed from the typed owner rather than a second copy. */
extern uint16_t mouse_button_state;
extern int16_t mouse_x_pixels;
extern int16_t mouse_y_pixels;
/* Read-only adapter for original C declarations that observe the low byte of
 * the ASM-owned status word; it avoids a cross-TU uint8_t/uint16_t object type
 * mismatch while retaining the single uint16_t owner. */
uint8_t portable_m1b73_g9120_low_byte(void);
extern uint8_t cursor_drawn_flag, g_4332, cursor_update_lock, g_433E, cursor_show_level, g_53BC, g_4DA4;
extern uint16_t cursor_alternate_rect_active; /* source hide-rectangle active word */
extern int16_t cursor_alternate_rect_left[4]; /* contiguous left,top,right,bottom source words */
extern uint16_t cursor_drawn_left, cursor_drawn_top, cursor_drawn_bottom, cursor_drawn_right, cursor_bitmap_width, cursor_bitmap_height, g_435A;
extern uint32_t g_4352, g_4356;
extern uint8_t g_4366;

#endif
