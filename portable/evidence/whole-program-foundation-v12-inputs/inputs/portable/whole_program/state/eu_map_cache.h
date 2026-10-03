/* Source-shaped native owner for root:m0250's 30x40 signed edit tile cache.
 * The flat view represents source expressions [0][i], which linearly address
 * cache words beyond the first 40-word row in the DOS implementation. */
#ifndef SIMANT_WHOLE_EU_MAP_CACHE_H
#define SIMANT_WHOLE_EU_MAP_CACHE_H

#include <stdint.h>

typedef union PortableEuMapCache {
    int16_t rows[30][40];
    int16_t linear[30 * 40];
} PortableEuMapCache;

extern PortableEuMapCache portable_eu_map_cache;

_Static_assert(sizeof(PortableEuMapCache) == 2400,
               "EU map cache has exactly 30x40 DOS words");
_Static_assert(sizeof(((PortableEuMapCache *)0)->rows[0]) == 80,
               "EU map cache row stride is 40 DOS words");

#endif
