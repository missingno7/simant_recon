/*
 * Defines the functional spider composition bitmap for the supported VGA view. The object
 * contains dimensions followed by the pixel buffer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef struct Point {
    int x;
    int y;
} Point;

typedef struct SpiderImage {
    Point dimensions;
    unsigned char pixels[6272];
} SpiderImage;

SpiderImage far fd_50F6_1F26;
