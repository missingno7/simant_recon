#ifndef SIMANT_PORTABLE_RENDER_BITMAP_H
#define SIMANT_PORTABLE_RENDER_BITMAP_H

#include "primitives.h"

typedef struct PortableBitmap {
    int16_t type;
    uint8_t mode;
    uint16_t width;
    uint16_t height;
    const uint8_t *pixels;
    size_t pixels_size;
} PortableBitmap;

/* The resource byte span remains owned by its caller for the lifetime of the view. */
PortableRenderStatus portable_bitmap_view(const uint8_t *bytes,
                                          size_t size,
                                          PortableBitmap *out);

/* EGA color mode: four MSB-first bitplanes, stored plane-major within each scanline. */
PortableRenderStatus portable_bitmap_draw(PortableFramebuffer *fb,
                                          int32_t x,
                                          int32_t y,
                                          const PortableBitmap *bitmap);

/* Draw a complete kind-2 record: raw/type-3 envelopes or source packed wrappers. */
PortableRenderStatus portable_bitmap_draw_resource(PortableFramebuffer *fb,
                                                    int32_t x,
                                                    int32_t y,
                                                    const uint8_t *resource,
                                                    size_t resource_size);

/* Decode a packed kind-2 record into a normalized 12-byte bitmap header and
 * its planar payload. The caller owns the result and releases it with the
 * paired function below. */
PortableRenderStatus portable_bitmap_decode_packed(const uint8_t *resource,
                                                    size_t resource_size,
                                                    uint8_t **decoded,
                                                    size_t *decoded_size);
void portable_bitmap_release_decoded(uint8_t *decoded);

/* Apply an EGA type-3 transparency mask and four color planes to indexed pixels. */
PortableRenderStatus portable_bitmap_merge_ega4(PortableFramebuffer *fb,
                                                int32_t x,
                                                int32_t y,
                                                uint16_t width,
                                                uint16_t height,
                                                const uint8_t *mask_and_planes,
                                                size_t source_size,
                                                size_t source_stride);

/* Draw four EGA planes stored in byte-interleaved order per scanline: for each
 * 8-pixel group, two bytes from plane 0, then plane 1, plane 2, and plane 3.
 * `row_stride` and `bytes_per_plane_row` come from the kind-9 tile metadata. */
PortableRenderStatus portable_bitmap_draw_interleaved_ega4(
    PortableFramebuffer *fb,
    int32_t x,
    int32_t y,
    uint16_t width,
    uint16_t height,
    const uint8_t *source,
    size_t source_size,
    size_t bytes_per_plane_row,
    size_t row_stride);

#endif
