#ifndef SIMANT_WHOLE_FONTS_H
#define SIMANT_WHOLE_FONTS_H
#include <stdint.h>
#include <stddef.h>

/* The first thirteen words are the only directly read FONT wire prefix.
 * Runtime pointers are native. No runtime object is serialized with sizeof. */
#pragma pack(push, 2)
struct Font {
    int16_t fontType, firstChar, lastChar, widMax, kernMax, nDescent;
    int16_t fRectWidth, fRectHeight, owTLoc, ascent, descent, leading, rowWords;
    char *image;
    int16_t *locTable;
    int16_t *owTable;
    int16_t proportional, missing;
};
struct Bitmap {
    int16_t width, height;
    char *bits;
};
#pragma pack(pop)
_Static_assert(offsetof(struct Font, image) == 26, "thirteen source wire words");
_Static_assert(offsetof(struct Font, rowWords) == 24, "wire rowWords");
_Static_assert(offsetof(struct Bitmap, width) == 0, "S13 scalar width view");
_Static_assert(offsetof(struct Bitmap, bits) == 4, "bitmap scalar prefix");
extern struct Bitmap fd_50F6_392C;
#endif
