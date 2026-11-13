/*
 * Defines editor and map view rectangles together with the text bitmap view used for yard
 * messages. The consumers use these geometry objects independently.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * No runtime initializer, fixed address or placement is supplied. The old
 * UIGEO scratch basename is not a recovered historical file name.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Bitmap {
    int width;
    int height;
    char far *bits;
};

/*
 * Pixel bounds used to draw the main map and locate its cursor.
 */
struct Rect far map_viewport_rect;
struct Rect far editTileRect;
struct Rect far fd_50F6_1104;
struct Bitmap far out_buffer;
