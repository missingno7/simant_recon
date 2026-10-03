#include "map_render_selectors.h"

_Static_assert(sizeof(uint16_t) == 2, "DOS unsigned int selector width");
_Static_assert(sizeof(uint8_t) == 1, "DOS unsigned char selector width");

/* Both original data-image values are zero. root:m0250:f_0250_1018 writes
 * these selectors from the active map/life arrays before drawing each cell. */
uint16_t g_9126 = 0;
uint8_t g_94E4 = 0;
