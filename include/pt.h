/* DOS horizontal-first pair. GetMousePos, gr_BitMapSize and TrapFill establish order.
 * No universal origin or range: this record is also used for dimensions.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef PT_H
#define PT_H

struct Pt {
    int x; /* Horizontal coordinate or width; pixels in graphics, caller units otherwise. */
    int y; /* Vertical coordinate or height; written by mouse/bitmap-size/geometry helpers. */
};

#endif
