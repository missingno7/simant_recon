#include "m1b73_mouse_state.h"

/* Native scalar owners lift the declarations from m1B73.asm. This keeps the
 * recovered field values and their source aliases in one storage location;
 * DOS interrupt-vector words and stacks are intentionally not allocated. */
uint8_t g_4331 = 0;
uint8_t g_4332 = 0;
uint8_t g_4333 = 0;
uint8_t g_433E = 0;
uint16_t g_4334 = 0;
int16_t g_4336[4] = { 0, 0, 0, 0 };
uint16_t g_4340 = 0;
uint16_t g_4342 = 0;
uint16_t g_4344 = 0;
uint16_t g_4346 = 0;
uint16_t g_4348 = 0x16;
uint16_t g_434A = 0x16;
uint32_t g_4352 = 0;
uint32_t g_4356 = 0;
uint16_t g_435A = 0;
uint8_t g_4365 = 0;
uint8_t g_4366 = 0;
uint8_t g_4DA4 = 0;
uint8_t g_53BC = 0;

/* These DGROUP fields are source-defined shared state from the native data
 * owner, initialized to BSS zero by the original program. */
uint16_t g_9120 = 0;
int16_t g_9122 = 0;
int16_t g_9124 = 0;

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
