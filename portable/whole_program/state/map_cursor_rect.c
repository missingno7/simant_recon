#include "map_cursor_rect.h"

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

static struct Rect map_cursor_rect;

struct Rect *sim_source_map_cursor_rect(void)
{
    return &map_cursor_rect;
}
