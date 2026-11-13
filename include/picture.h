/* Serialized raster resource prefix, distinct from the pointer-based Bitmap.
 * pictures.c's Pic and balloons.c's Mask describe this same twelve-byte prefix.
 * Organisation and names are ours. No total raster allocation size is implied.
 */
#ifndef PICTURE_H
#define PICTURE_H
struct Pic {
    int type; /* +00 blitter/format selector: balloon generation writes 3. */
    unsigned char mode; /* +02 mode/flag byte; balloon generation writes 1. */
    char pad03[5]; /* +03 unknown format-dependent bytes; not claimed to be unused. */
    int width; /* +08 pixel columns; balloons/font bitmap generation write it. */
    int height; /* +0A pixel rows; balloon generator adjusts final displayed height. */
};
#endif
