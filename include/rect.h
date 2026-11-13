/*
 * Screen and window rectangle, in pixels. Rectangles are half-open: left and top are inside,
 * right and bottom are the first column and row outside (clip_point_outcode treats a point
 * with x >= right or y >= bottom as outside). A top of 0x8000 ends a rectangle list
 * (window clip lists, the screen clip list).
 *
 * Shared header (organisation ours). The compiler counts struct tags as declarations, so a
 * file includes this header exactly where it defines struct Rect; it holds no other tag.
 */
#ifndef RECT_H
#define RECT_H

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

#endif
