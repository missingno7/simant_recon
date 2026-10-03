#include "minimap_rects.h"

#include <stddef.h>
#include <stdint.h>

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

_Static_assert(sizeof(struct Rect) == 8, "source Rect is four words");
_Static_assert(offsetof(struct Rect, bottom) == 6, "Rect.bottom is word four");

static struct Rect minimap_rects[2];

struct Rect *sim_source_minimap_rect(unsigned int index)
{
    return index < 2u ? &minimap_rects[index] : NULL;
}
