#include "elevator_thumb_size.h"

#include <stddef.h>
#include <stdint.h>

/* Runtime-owned size populated by f_208F_0419 from resource 0x6f. */
struct Pt {
    int16_t x;
    int16_t y;
};

_Static_assert(sizeof(struct Pt) == 4, "source Pt occupies two words");
_Static_assert(offsetof(struct Pt, y) == 2, "Pt.y is word two");

static struct Pt elevator_thumb_size;

struct Pt *sim_source_elevator_thumb_size(void)
{
    return &elevator_thumb_size;
}
