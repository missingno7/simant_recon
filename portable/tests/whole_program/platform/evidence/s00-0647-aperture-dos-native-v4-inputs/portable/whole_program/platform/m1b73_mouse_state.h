#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_STATE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_STATE_H

#include <stdint.h>

/* Native owner for the ASM-owned cursor and mouse fields used by the SDL
 * adapter. The pointed-to image/mask resources are borrowed from the active
 * database/session and never outlive that owner. */
typedef struct PortableM1B73MouseAsmState {
    uint8_t *cursor_drawn;          /* source g_4331 */
    uint8_t *cursor_event_pending;  /* source g_4332 */
    uint8_t *cursor_update_lock;    /* source g_4333 */
    uint16_t *button_state;         /* shared source g_9120 word */
    int16_t *x;                     /* shared source g_9122 */
    int16_t *y;                     /* shared source g_9124 */
    uint16_t *cursor_x, *cursor_y;  /* source g_4340/g_4342 */
    uint16_t *cursor_right; /* source g_4346; _0DA4's right edge */
    uint16_t *cursor_bottom; /* source g_4344; _0DA4's bottom edge */
    uint16_t *cursor_width, *cursor_height; /* source g_4348/g_434A */
    uint32_t *callback_count;       /* source g_4352 */
    uint32_t *mouse_event_count;    /* source g_4356 */
    uint16_t *cursor_initialized;   /* source g_435A */
    uint8_t *saved_keyboard_flags;  /* source g_433E, NumLock bit is used */
    uint8_t *cursor_show_level;     /* source g_4365 */
    uint8_t *hook_depth;            /* source g_53BC */
    uint8_t *mouse_mode;            /* source g_4DA4 */
    const uint8_t **cursor_image;   /* sidecar for source far pointer g_4D8E */
    const uint8_t **cursor_mask;    /* sidecar for source far pointer g_4D92 */
    uint32_t active_hotbox_token; /* native token replacing a far record pointer */
} PortableM1B73MouseAsmState;

/* Source initializers from m1B73.asm: zeroed fields above are `db/dw/dd 0`;
 * cursor dimensions alone begin at 0x16 by 0x16. */
extern PortableM1B73MouseAsmState portable_m1b73_mouse_asm_state;

/* The converted C callers also observe these same coordinate/modifier owners.
 * They are aliases exposed from the typed owner rather than a second copy. */
extern uint16_t g_9120;
extern int16_t g_9122;
extern int16_t g_9124;
/* Read-only adapter for original C declarations that observe the low byte of
 * the ASM-owned status word; it avoids a cross-TU uint8_t/uint16_t object type
 * mismatch while retaining the single uint16_t owner. */
uint8_t portable_m1b73_g9120_low_byte(void);
extern uint8_t g_4331, g_4332, g_4333, g_433E, g_4365, g_53BC, g_4DA4;
extern uint16_t g_4334; /* source hide-rectangle active word */
extern int16_t g_4336[4]; /* contiguous left,top,right,bottom source words */
extern uint16_t g_4340, g_4342, g_4344, g_4346, g_4348, g_434A, g_435A;
extern uint32_t g_4352, g_4356;
extern uint8_t g_4366;

#endif
