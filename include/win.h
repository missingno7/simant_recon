/* Merged partial window header. Requires rect.h to have been included by the module.
 * objs[1] describes a variable tail, not a proven one-object capacity or total size.
 * char* avoids adding an Obj forward tag where no such declaration existed.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef WIN_H
#define WIN_H

struct Win {
    struct Rect rect; /* +00 cached outer screen rectangle; Recalc copies object zero bounds. */
    char pad08[4]; /* +08 unknown window header words; resource owns initial contents. */
    int count; /* +0C number of trailing object pointers; RepointObjects traverses this many. */
    char pad0E[0x18 - 0x0E]; /* Unknown header span; +10 also addressed as win_GetArg's variable arguments. */
    int minWidth; /* +18 minimum resize width in pixels, consumed by win_constrain_drag_rect. */
    int minHeight; /* +1A minimum resize height in pixels, consumed by win_constrain_drag_rect. */
    int flags; /* +1C resource/window state bits; lifecycle toggles 0x200, zoom toggles 0x80. */
    char pad1E[2]; /* +1E unknown word; no interpretation established. */
    int gridX; /* +20 horizontal resize/move increment in pixels (zero handled by constrain helper). */
    int gridY; /* +22 vertical resize/move increment in pixels. */
    struct Rect zoomRect; /* +24 saved object-zero x,y,width,height tuple, overlaid as Rect during zoom. */
    char far *objs[1]; /* +2C variable tail of count object pointers; RepointObjects writes it. */
};

#endif
