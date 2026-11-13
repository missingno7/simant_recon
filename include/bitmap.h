/* Font output raster descriptor, not the 12-byte serialized bitmap resource header.
 * See font_resources.c:font_MakeImage and font_output.c:font_make_display_bitmap.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef BITMAP_H
#define BITMAP_H

struct Bitmap {
    int width; /* Used pixel columns; font_MakeImage writes the text advance. */
    int height; /* Used pixel rows; font_MakeImage writes font height minus one. */
    char far *bits; /* Raster storage, assigned by font_output; mono rows use ceil(width/8) bytes. */
};

#endif
