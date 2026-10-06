#ifndef SIMANT_WHOLE_POINTER_GLOBALS_H
#define SIMANT_WHOLE_POINTER_GLOBALS_H

#include <stdint.h>
#include "../types/fonts.h"

enum { SIM_SOURCE_DATABASE_COUNT = 4, SIM_SOURCE_FONT_COUNT = 4 };

/* GetFreeHandle and the adjacent 3B58 symbol bound the DOS int table to four
 * entries (3B50..3B57). */
extern int16_t db_handles[SIM_SOURCE_DATABASE_COUNT];

/* `db_cacheTable` and current-font selection are defined by their original
 * source TUs. These declarations centralize their native pointee types only. */
extern void *db_cacheTable;
extern struct Font *fd_55B3_65A4;

/* font_InitFonts writes slots 0..3; f_24AB_02AD clamps every source read to
 * those four entries. The remaining DOS bytes through 4A41 are not modeled as
 * additional host pointers. */
extern struct Font *fd_50F6_4A1A[SIM_SOURCE_FONT_COUNT];

#endif
