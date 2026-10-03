#include "primitives.h"

#include <limits.h>

static PortableRect framebuffer_bounds(const PortableFramebuffer *fb)
{
    PortableRect r = {0, 0, fb->width, fb->height};
    return r;
}

static PortableRect intersect_rect(PortableRect a, PortableRect b)
{
    PortableRect r;
    r.left = a.left > b.left ? a.left : b.left;
    r.top = a.top > b.top ? a.top : b.top;
    r.right = a.right < b.right ? a.right : b.right;
    r.bottom = a.bottom < b.bottom ? a.bottom : b.bottom;
    if (r.right < r.left)
        r.right = r.left;
    if (r.bottom < r.top)
        r.bottom = r.top;
    return r;
}

static PortableRect normalize_rect(PortableRect r)
{
    int32_t swap;
    if (r.left > r.right) {
        swap = r.left;
        r.left = r.right;
        r.right = swap;
    }
    if (r.top > r.bottom) {
        swap = r.top;
        r.top = r.bottom;
        r.bottom = swap;
    }
    return r;
}

PortableRenderStatus portable_framebuffer_init(PortableFramebuffer *fb,
                                               int32_t width,
                                               int32_t height,
                                               size_t stride,
                                               uint8_t *pixels)
{
    if (fb == NULL || pixels == NULL || width <= 0 || height <= 0 ||
        stride < (size_t)width || (size_t)height > SIZE_MAX / stride)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    fb->width = width;
    fb->height = height;
    fb->stride = stride;
    fb->pixels = pixels;
    fb->clip = framebuffer_bounds(fb);
    return PORTABLE_RENDER_OK;
}

void portable_framebuffer_set_clip(PortableFramebuffer *fb, PortableRect clip)
{
    if (fb != NULL && fb->pixels != NULL)
        fb->clip = intersect_rect(framebuffer_bounds(fb), clip);
}

void portable_framebuffer_reset_clip(PortableFramebuffer *fb)
{
    if (fb != NULL && fb->pixels != NULL)
        fb->clip = framebuffer_bounds(fb);
}

void portable_put_pixel(PortableFramebuffer *fb, int32_t x, int32_t y, uint8_t color)
{
    if (fb == NULL || fb->pixels == NULL || x < fb->clip.left || x >= fb->clip.right ||
        y < fb->clip.top || y >= fb->clip.bottom)
        return;
    fb->pixels[(size_t)y * fb->stride + (size_t)x] = color;
}

static PortableRect clipped(PortableFramebuffer *fb, PortableRect rect)
{
    return intersect_rect(fb->clip, rect);
}

void portable_fill_rect(PortableFramebuffer *fb, PortableRect rect, uint8_t color)
{
    int32_t x, y;
    if (fb == NULL || fb->pixels == NULL)
        return;
    rect = clipped(fb, normalize_rect(rect));
    for (y = rect.top; y < rect.bottom; ++y)
        for (x = rect.left; x < rect.right; ++x)
            fb->pixels[(size_t)y * fb->stride + (size_t)x] = color;
}

void portable_fill_pattern_1bpp(PortableFramebuffer *fb,
                                PortableRect rect,
                                const uint8_t pattern[8],
                                uint8_t foreground,
                                uint8_t background)
{
    int32_t x, y;
    if (fb == NULL || fb->pixels == NULL || pattern == NULL)
        return;
    rect = clipped(fb, normalize_rect(rect));
    for (y = rect.top; y < rect.bottom; ++y) {
        uint8_t row = pattern[(unsigned)y & 7u];
        for (x = rect.left; x < rect.right; ++x) {
            uint8_t bit = (uint8_t)((row >> (7u - ((unsigned)x & 7u))) & 1u);
            fb->pixels[(size_t)y * fb->stride + (size_t)x] = bit ? foreground : background;
        }
    }
}

void portable_xor_rect(PortableFramebuffer *fb, PortableRect rect, uint8_t mask)
{
    int32_t x, y;
    if (fb == NULL || fb->pixels == NULL)
        return;
    rect = clipped(fb, normalize_rect(rect));
    for (y = rect.top; y < rect.bottom; ++y)
        for (x = rect.left; x < rect.right; ++x)
            fb->pixels[(size_t)y * fb->stride + (size_t)x] ^= mask;
}

void portable_blit_indexed(PortableFramebuffer *fb,
                           int32_t x,
                           int32_t y,
                           const uint8_t *source,
                           size_t source_size,
                           int32_t width,
                           int32_t height,
                           size_t source_stride,
                           int transparent,
                           uint8_t transparent_index)
{
    int32_t sx, sy;
    size_t needed;
    if (fb == NULL || fb->pixels == NULL || source == NULL || width < 0 || height < 0 ||
        source_stride < (size_t)width || (height > 0 && source_stride == 0) ||
        (height > 0 && (size_t)(height - 1) > (SIZE_MAX - (size_t)width) / source_stride))
        return;
    needed = height == 0 ? 0 : (size_t)(height - 1) * source_stride + (size_t)width;
    if (needed > source_size)
        return;
    for (sy = 0; sy < height; ++sy) {
        int64_t dy = (int64_t)y + sy;
        if (dy < fb->clip.top || dy >= fb->clip.bottom)
            continue;
        for (sx = 0; sx < width; ++sx) {
            int64_t dx = (int64_t)x + sx;
            uint8_t c;
            if (dx < fb->clip.left || dx >= fb->clip.right)
                continue;
            c = source[(size_t)sy * source_stride + (size_t)sx];
            if (!transparent || c != transparent_index)
                fb->pixels[(size_t)dy * fb->stride + (size_t)dx] = c;
        }
    }
}
