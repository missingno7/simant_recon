#ifndef SIMANT_PORTABLE_RENDER_PRIMITIVES_H
#define SIMANT_PORTABLE_RENDER_PRIMITIVES_H

#include <stddef.h>
#include <stdint.h>

typedef struct PortableRect {
    int32_t left;
    int32_t top;
    int32_t right;
    int32_t bottom;
} PortableRect;

typedef struct PortableFramebuffer {
    int32_t width;
    int32_t height;
    size_t stride;
    uint8_t *pixels;
    PortableRect clip;
} PortableFramebuffer;

typedef enum PortableRenderStatus {
    PORTABLE_RENDER_OK = 0,
    PORTABLE_RENDER_INVALID_ARGUMENT,
    PORTABLE_RENDER_TRUNCATED_DATA,
    PORTABLE_RENDER_UNSUPPORTED_CODEC,
    PORTABLE_RENDER_UNSUPPORTED_MODE,
    PORTABLE_RENDER_INVALID_RESOURCE
} PortableRenderStatus;

PortableRenderStatus portable_framebuffer_init(PortableFramebuffer *fb,
                                               int32_t width,
                                               int32_t height,
                                               size_t stride,
                                               uint8_t *pixels);
void portable_framebuffer_set_clip(PortableFramebuffer *fb, PortableRect clip);
void portable_framebuffer_reset_clip(PortableFramebuffer *fb);
void portable_put_pixel(PortableFramebuffer *fb, int32_t x, int32_t y, uint8_t color);
void portable_fill_rect(PortableFramebuffer *fb, PortableRect rect, uint8_t color);
/* Apply an MSB-first 8x8 one-bit pattern; each set bit selects foreground. */
void portable_fill_pattern_1bpp(PortableFramebuffer *fb,
                                PortableRect rect,
                                const uint8_t pattern[8],
                                uint8_t foreground,
                                uint8_t background);
void portable_xor_rect(PortableFramebuffer *fb, PortableRect rect, uint8_t mask);
void portable_blit_indexed(PortableFramebuffer *fb,
                           int32_t x,
                           int32_t y,
                           const uint8_t *source,
                           size_t source_size,
                           int32_t width,
                           int32_t height,
                           size_t source_stride,
                           int transparent,
                           uint8_t transparent_index);

#endif
