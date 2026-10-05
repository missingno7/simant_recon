#include "m1b73_mouse_state.h"

/* Native scalar owners lift the declarations from m1B73.asm. This keeps the
 * recovered field values and their source aliases in one storage location;
 * DOS interrupt-vector words and stacks are intentionally not allocated. */
extern uint8_t g_4331 ;
extern uint8_t g_4332 ;
extern uint8_t g_4333 ;
extern uint8_t g_433E ;
extern uint16_t g_4334 ;
extern int16_t g_4336[4] ;
extern uint16_t g_4340 ;
extern uint16_t g_4342 ;
extern uint16_t g_4344 ;
extern uint16_t g_4346 ;
extern uint16_t g_4348 ;
extern uint16_t g_434A ;
extern uint32_t g_4352 ;
extern uint32_t g_4356 ;
extern uint16_t g_435A ;
extern uint8_t g_4365 ;
extern uint8_t g_4366 ;
extern uint8_t g_4DA4 ;
extern uint8_t g_53BC ;

/* These DGROUP fields are source-defined shared state from the native data
 * owner, initialized to BSS zero by the original program. */
extern uint16_t g_9120 ;
extern int16_t g_9122 ;
extern int16_t g_9124 ;

uint8_t portable_m1b73_g9120_low_byte(void)
{
    return ((const uint8_t *)&g_9120)[0];
}

static const uint8_t *cursor_image;
static const uint8_t *cursor_mask;

PortableM1B73MouseAsmState portable_m1b73_mouse_asm_state = {
    &g_4331, &g_4332, &g_4333, &g_9120, &g_9122, &g_9124,
    &g_4340, &g_4342, &g_4346, &g_4344, &g_4348, &g_434A,
    &g_4352, &g_4356, &g_435A, &g_433E, &g_4365, &g_53BC, &g_4DA4,
    &cursor_image, &cursor_mask, 0
};
