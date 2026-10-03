#include "tri_control_state.h"

#include <stddef.h>
#include <stdint.h>

struct Pt {
    int16_t x;
    int16_t y;
};

struct TriPoints {
    int16_t apexX;
    int16_t apexY;
    int16_t leftX;
    int16_t leftY;
    int16_t rightX;
    int16_t rightY;
};

_Static_assert(sizeof(struct Pt) == 4, "source Pt is two words");
_Static_assert(offsetof(struct Pt, y) == 2, "Pt.y is word two");
_Static_assert(sizeof(struct TriPoints) == 12, "source TriPoints is six words");
_Static_assert(offsetof(struct TriPoints, rightY) == 10, "TriPoints field six offset");

static struct Pt tri_control_points[3];
static struct TriPoints tri_control_triangles[2];

struct Pt *sim_source_tri_control_point(unsigned int index)
{
    return index < 3u ? &tri_control_points[index] : NULL;
}

struct TriPoints *sim_source_tri_control_triangle(unsigned int index)
{
    return index < 2u ? &tri_control_triangles[index] : NULL;
}
