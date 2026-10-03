#ifndef SIMANT_YARD_CACHE_GLOBALS_V1_H
#define SIMANT_YARD_CACHE_GLOBALS_V1_H

#include <stdint.h>

/* Source handle values used by the yard display and by root's cache hooks.
 * A cached resource value is a native relocatable-handle master pointer, not
 * a DOS long and not the resource payload pointer. */
typedef char **SimYardCacheHandle;

extern SimYardCacheHandle fd_55B3_2A36;
extern SimYardCacheHandle fd_55B3_2A3A;

/* S13's source table contains four (x,y) points.  The startup projection in
 * startup_globals_v1 currently exposes only the first point; this owner is
 * the complete 8-word source view. */
extern int16_t fd_55B3_2A42[8];

#endif
