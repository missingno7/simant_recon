#include "m1b73_mouse_state.h"

/* Native scalar owners lift the declarations from m1B73.asm. This keeps the
 * recovered field values and their source aliases in one storage location;
 * DOS interrupt-vector words and stacks are intentionally not allocated. */
extern uint8_t cursor_drawn_flag ;
extern uint8_t g_4332 ;
extern uint8_t cursor_update_lock ;
extern uint8_t g_433E ;
extern uint16_t cursor_alternate_rect_active ;
extern int16_t cursor_alternate_rect_left[4] ;
extern uint16_t cursor_drawn_left ;
extern uint16_t cursor_drawn_top ;
extern uint16_t cursor_drawn_bottom ;
extern uint16_t cursor_drawn_right ;
extern uint16_t cursor_bitmap_width ;
extern uint16_t cursor_bitmap_height ;
extern uint32_t g_4352 ;
extern uint32_t g_4356 ;
extern uint16_t g_435A ;
extern uint8_t cursor_show_level ;
extern uint8_t g_4366 ;
extern uint8_t g_4DA4 ;
extern uint8_t g_53BC ;

/* These DGROUP fields are source-defined shared state from the native data
 * owner, initialized to BSS zero by the original program. */
extern uint16_t mouse_button_state ;
extern int16_t mouse_x_pixels ;
extern int16_t mouse_y_pixels ;

uint8_t portable_m1b73_g9120_low_byte(void)
{
    return ((const uint8_t *)&mouse_button_state)[0];
}

static const uint8_t *cursor_image;
static const uint8_t *cursor_mask;

PortableM1B73MouseAsmState portable_m1b73_mouse_asm_state = {
    &cursor_drawn_flag, &g_4332, &cursor_update_lock, &mouse_button_state, &mouse_x_pixels, &mouse_y_pixels,
    &cursor_drawn_left, &cursor_drawn_top, &cursor_drawn_right, &cursor_drawn_bottom, &cursor_bitmap_width, &cursor_bitmap_height,
    &g_4352, &g_4356, &g_435A, &g_433E, &cursor_show_level, &g_53BC, &g_4DA4,
    &cursor_image, &cursor_mask, 0
};
