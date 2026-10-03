#include "eu_map_cache.h"

/* The recovered TU has only an extern source view; native C static storage
 * supplies its initial zero state. Source routines explicitly invalidate the
 * cache to -1 before redraw. No extra gap or padding bytes are modeled. */
PortableEuMapCache portable_eu_map_cache;
