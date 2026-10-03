#include "menu_bar_rect.h"

#include <stddef.h>
#include <stdint.h>

/* This spelling matches the source Rect used by all four declaring TUs.
 * It is a native runtime owner, not a claim about DOS segment placement or
 * an initialized historical value. */
struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

_Static_assert(sizeof(struct Rect) == 8, "source Rect is four words");
_Static_assert(offsetof(struct Rect, bottom) == 6, "Rect.bottom is word four");

static struct Rect menu_bar_rect;

struct Rect *sim_source_menu_bar_rect(void)
{
    return &menu_bar_rect;
}
