/* Native declarations for actual canonical src/root/m195A.asm DATA cells. */
#ifndef SIMANT_ASM_SHARED_STATE_H
#define SIMANT_ASM_SHARED_STATE_H
#include <stdint.h>
_Static_assert(sizeof(int8_t) == 1, "8-bit state");
_Static_assert(sizeof(int16_t) == 2, "DOS word state");
extern int8_t fd_55B3_360C;
extern int16_t fd_55B3_3612;
extern int16_t fd_55B3_3614;
#endif
