#ifndef SIMANT_WHOLE_LINE16B5_H
#define SIMANT_WHOLE_LINE16B5_H

#include <stddef.h>
#include <stdint.h>

#define PORTABLE_LINE16B5_MAX_HEIGHT 200u
#define PORTABLE_LINE16B5_MAX_INLINE_WIDTH 112u
#define PORTABLE_LINE16B5_MAX_INLINE_HEIGHT 112u
#define PORTABLE_LINE16B5_MAX_INLINE_BYTES 6272u

/* Single native backing for the source root:m0250 DrawSpider scratch image.
 * The recovered DOS object had a two-word Pnt prefix followed by inline
 * pixel bytes. Its full historical allocation is unknown; the 6272-byte
 * payload is the maximum extent required by the source-proved 112x112,
 * mode-1/mode-2 use. */
typedef struct PortableSpiderLineBuffer {
    int16_t x;
    int16_t y;
    uint8_t pixels[PORTABLE_LINE16B5_MAX_INLINE_BYTES];
} PortableSpiderLineBuffer;

extern PortableSpiderLineBuffer fd_50F6_1F26;

#if defined(__cplusplus)
static_assert(offsetof(PortableSpiderLineBuffer, pixels) == 4,
              "spider prefix must be 4 bytes");
static_assert(sizeof(PortableSpiderLineBuffer) == 6276,
              "spider line buffer must be 6276 bytes");
#else
_Static_assert(offsetof(PortableSpiderLineBuffer, pixels) == 4,
               "spider prefix must be 4 bytes");
_Static_assert(sizeof(PortableSpiderLineBuffer) == 6276,
               "spider line buffer must be 6276 bytes");
#endif

/* Native typed view of the pixels addressed by root:m16B5. The two-word
 * source prefix is kept separate from the payload; source modes are 0=1bpp,
 * 1=packed 4bpp, and 2=4-plane 4bpp. */
typedef struct PortableLine16B5 {
    uint16_t width;
    uint16_t height;
    uint16_t mode;
    uint16_t row_offset[PORTABLE_LINE16B5_MAX_HEIGHT];
    uint16_t plane_stride;
    uint8_t *pixels;
    size_t pixels_size;
    int initialized;
} PortableLine16B5;

typedef struct PortableLine16B5InlineBuffer {
    int16_t width;
    int16_t height;
    uint8_t pixels[];
} PortableLine16B5InlineBuffer;

/* Rejects invalid source geometry, undersized payloads, and unsafe address
 * extents. Successful initialization matches f_16B5_0033's table setup. */
int portable_line16b5_init(PortableLine16B5 *state, uint16_t width,
                           uint16_t height, uint16_t mode,
                           uint8_t *pixels, size_t pixels_size);

/* Draws the source f_16B5_0008 line into an initialized native view. Signed
 * word coordinates and color are interpreted as DOS 16-bit values. */
int portable_line16b5_draw(PortableLine16B5 *state, int16_t x0, int16_t y0,
                           int16_t x1, int16_t y1, int16_t color);

/* Inline legacy adapter for callers preserving the m0250 Pnt prefix followed
 * immediately by pixels. The original far ABI has no capacity argument; this
 * adapter is restricted to the source-proved 84/112-pixel DrawSpider buffers
 * and records the derived capacity. */
/* `void *` preserves the source far-pointer machine ABI for TU-local Pnt *
 * declarations; the pointed-to native object still has the inline 2-word
 * prefix documented above. */
void f_16B5_0033(void *source_prefix_and_pixels, int16_t mode);
void f_16B5_0008(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                 int16_t color);
void portable_line16b5_unbind(void);

#endif
