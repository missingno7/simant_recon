/* Native declarations for actual canonical src/memory/ems.asm DATA cells. */
#ifndef SIMANT_ASM_SHARED_STATE_H
#define SIMANT_ASM_SHARED_STATE_H
#include <stdint.h>
_Static_assert(sizeof(int8_t) == 1, "8-bit state");
_Static_assert(sizeof(int16_t) == 2, "DOS word state");
extern int8_t ems_version;
extern int16_t ems_free_page_count;
extern int16_t ems_total_page_count;
#endif
