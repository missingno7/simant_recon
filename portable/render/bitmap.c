#include "bitmap.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

typedef struct PortableLzss {
    const uint8_t *source;
    size_t source_size;
    size_t source_pos;
    uint8_t ring[4096];
    size_t ring_pos;
    uint8_t flags;
    unsigned flag_bits;
    size_t match_pos;
    size_t match_left;
} PortableLzss;

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int bit_at(const uint8_t *row, size_t bit)
{
    return (row[bit >> 3] >> (7u - (unsigned)(bit & 7u))) & 1;
}

static void lzss_init(PortableLzss *state, const uint8_t *source, size_t size)
{
    memset(state, 0, sizeof(*state));
    state->source = source;
    state->source_size = size;
    memset(state->ring, 0x20, 0xfee);
    state->ring_pos = 0xfee;
}

static PortableRenderStatus lzss_read(PortableLzss *state, uint8_t *out, size_t size)
{
    size_t written = 0;
    while (written < size) {
        uint8_t value;
        if (state->match_left != 0) {
            value = state->ring[state->match_pos & 0x0fffu];
            state->match_pos = (state->match_pos + 1u) & 0x0fffu;
            state->ring[state->ring_pos] = value;
            state->ring_pos = (state->ring_pos + 1u) & 0x0fffu;
            out[written++] = value;
            --state->match_left;
            continue;
        }
        if (state->flag_bits == 0) {
            if (state->source_pos >= state->source_size)
                return PORTABLE_RENDER_TRUNCATED_DATA;
            state->flags = state->source[state->source_pos++];
            state->flag_bits = 8;
        }
        if ((state->flags & 1u) != 0) {
            if (state->source_pos >= state->source_size)
                return PORTABLE_RENDER_TRUNCATED_DATA;
            value = state->source[state->source_pos++];
            state->ring[state->ring_pos] = value;
            state->ring_pos = (state->ring_pos + 1u) & 0x0fffu;
            out[written++] = value;
        } else {
            uint8_t lo, hi;
            if (state->source_size - state->source_pos < 2u)
                return PORTABLE_RENDER_TRUNCATED_DATA;
            lo = state->source[state->source_pos++];
            hi = state->source[state->source_pos++];
            state->match_pos = (size_t)lo | ((size_t)(hi & 0xf0u) << 4);
            /* The DOS decoder's inclusive jns loop emits nibble + 3 bytes. */
            state->match_left = (size_t)(hi & 0x0fu) + 3u;
        }
        state->flags >>= 1;
        --state->flag_bits;
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_bitmap_view(const uint8_t *bytes,
                                          size_t size,
                                          PortableBitmap *out)
{
    uint16_t width, height;
    size_t row_bytes, required;
    int16_t type;
    if (bytes == NULL || out == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (size < 12)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    type = (int16_t)read_le16(bytes);
    width = read_le16(bytes + 8);
    height = read_le16(bytes + 10);
    if (width == 0 || height == 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    out->type = type;
    out->mode = bytes[2];
    out->width = width;
    out->height = height;
    out->pixels = bytes + 12;
    out->pixels_size = size - 12;

    if (type == 0 || type == 3) {
        row_bytes = ((size_t)width + 7u) / 8u;
        if (row_bytes > SIZE_MAX / (type == 3 ? 5u : 4u) ||
            (size_t)height > SIZE_MAX / (row_bytes * (type == 3 ? 5u : 4u)))
            return PORTABLE_RENDER_INVALID_RESOURCE;
        required = row_bytes * (type == 3 ? 5u : 4u) * height;
        if (type == 0 && out->mode == 1)
            required = row_bytes * height;
        if (out->pixels_size < required)
            return PORTABLE_RENDER_TRUNCATED_DATA;
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_bitmap_draw(PortableFramebuffer *fb,
                                          int32_t x,
                                          int32_t y,
                                          const PortableBitmap *bitmap)
{
    size_t row_bytes, required;
    uint16_t sx, sy;
    if (fb == NULL || fb->pixels == NULL || bitmap == NULL || bitmap->pixels == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (bitmap->type == -1 || (uint16_t)bitmap->type == 0x8000u)
        return PORTABLE_RENDER_UNSUPPORTED_CODEC;
    if (bitmap->type == 3)
        return portable_bitmap_merge_ega4(fb, x, y, bitmap->width, bitmap->height,
                                          bitmap->pixels, bitmap->pixels_size,
                                          ((size_t)bitmap->width + 7u) / 8u);
    if (bitmap->type != 0)
        return PORTABLE_RENDER_UNSUPPORTED_CODEC;
    if (bitmap->width == 0 || bitmap->height == 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    row_bytes = ((size_t)bitmap->width + 7u) / 8u;
    if (bitmap->mode == 1) {
        required = row_bytes * bitmap->height;
        if (required > bitmap->pixels_size)
            return PORTABLE_RENDER_TRUNCATED_DATA;
        for (sy = 0; sy < bitmap->height; ++sy) {
            const uint8_t *row = bitmap->pixels + (size_t)sy * row_bytes;
            for (sx = 0; sx < bitmap->width; ++sx)
                portable_put_pixel(fb, (int32_t)((int64_t)x + sx),
                                   (int32_t)((int64_t)y + sy),
                                   (uint8_t)bit_at(row, sx));
        }
        return PORTABLE_RENDER_OK;
    }
    if (row_bytes > SIZE_MAX / 4u || (size_t)bitmap->height > SIZE_MAX / (row_bytes * 4u))
        return PORTABLE_RENDER_INVALID_RESOURCE;
    required = row_bytes * 4u * bitmap->height;
    if (required > bitmap->pixels_size)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    for (sy = 0; sy < bitmap->height; ++sy) {
        const uint8_t *row = bitmap->pixels + (size_t)sy * row_bytes * 4u;
        for (sx = 0; sx < bitmap->width; ++sx) {
            uint8_t c = (uint8_t)(bit_at(row, sx) |
                                  (bit_at(row + row_bytes, sx) << 1) |
                                  (bit_at(row + row_bytes * 2u, sx) << 2) |
                                  (bit_at(row + row_bytes * 3u, sx) << 3));
            portable_put_pixel(fb, (int32_t)((int64_t)x + sx),
                               (int32_t)((int64_t)y + sy), c);
        }
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_bitmap_draw_resource(PortableFramebuffer *fb,
                                                    int32_t x,
                                                    int32_t y,
                                                    const uint8_t *resource,
                                                    size_t resource_size)
{
    int16_t type;
    PortableBitmap bitmap;
    PortableRenderStatus status;
    uint8_t *decoded;
    size_t decoded_size;
    if (fb == NULL || fb->pixels == NULL || resource == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (resource_size < 2)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    type = (int16_t)read_le16(resource);
    if (type != -1 && (uint16_t)type != 0x8000u) {
        status = portable_bitmap_view(resource, resource_size, &bitmap);
        if (status != PORTABLE_RENDER_OK)
            return status;
        return portable_bitmap_draw(fb, x, y, &bitmap);
    }
    status = portable_bitmap_decode_packed(resource, resource_size, &decoded,
                                           &decoded_size);
    if (status != PORTABLE_RENDER_OK)
        return status;
    status = portable_bitmap_view(decoded, decoded_size, &bitmap);
    if (status == PORTABLE_RENDER_OK)
        status = portable_bitmap_draw(fb, x, y, &bitmap);
    free(decoded);
    return status;
}

PortableRenderStatus portable_bitmap_decode_packed(const uint8_t *resource,
                                                    size_t resource_size,
                                                    uint8_t **decoded_out,
                                                    size_t *decoded_size_out)
{
    int16_t type;
    PortableLzss state;
    uint8_t pack_header[12];
    uint16_t width, height;
    uint8_t depth;
    size_t row_bytes, planes, image_size, full_size;
    uint8_t *decoded;
    PortableRenderStatus status;
    if (resource == NULL || decoded_out == NULL || decoded_size_out == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    *decoded_out = NULL;
    *decoded_size_out = 0;
    if (resource_size < 2)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    type = (int16_t)read_le16(resource);
    if (type != -1 && (uint16_t)type != 0x8000u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    if (resource_size < 4)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    lzss_init(&state, resource + 4, resource_size - 4u);
    status = lzss_read(&state, pack_header, sizeof(pack_header));
    if (status != PORTABLE_RENDER_OK)
        return status;
    if (read_le16(pack_header) != 0 && read_le16(pack_header) != 3)
        return PORTABLE_RENDER_UNSUPPORTED_CODEC;
    depth = pack_header[2];
    if (depth != 4)
        return PORTABLE_RENDER_UNSUPPORTED_MODE;
    width = read_le16(pack_header + 8);
    height = read_le16(pack_header + 10);
    if (width == 0 || height == 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    row_bytes = ((size_t)width + 7u) / 8u;
    planes = read_le16(pack_header) == 3 ? 5u : 4u;
    if (row_bytes > SIZE_MAX / planes ||
        (size_t)height > SIZE_MAX / (row_bytes * planes))
        return PORTABLE_RENDER_INVALID_RESOURCE;
    image_size = row_bytes * planes * (size_t)height;
    if (image_size > SIZE_MAX - 12u || image_size > 128u * 1024u * 1024u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    full_size = image_size + 12u;
    decoded = (uint8_t *)malloc(full_size);
    if (decoded == NULL)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    memcpy(decoded, pack_header, sizeof(pack_header));
    status = lzss_read(&state, decoded + 12, image_size);
    if (status != PORTABLE_RENDER_OK) {
        free(decoded);
        return status;
    }
    *decoded_out = decoded;
    *decoded_size_out = full_size;
    return PORTABLE_RENDER_OK;
}

void portable_bitmap_release_decoded(uint8_t *decoded)
{
    free(decoded);
}

PortableRenderStatus portable_bitmap_merge_ega4(PortableFramebuffer *fb,
                                                int32_t x,
                                                int32_t y,
                                                uint16_t width,
                                                uint16_t height,
                                                const uint8_t *mask_and_planes,
                                                size_t source_size,
                                                size_t source_stride)
{
    size_t plane_stride, needed;
    uint16_t sx, sy;
    if (fb == NULL || fb->pixels == NULL || mask_and_planes == NULL ||
        width == 0 || height == 0)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    plane_stride = ((size_t)width + 7u) / 8u;
    if (source_stride < plane_stride || source_stride > SIZE_MAX / 5u ||
        (size_t)height > SIZE_MAX / (source_stride * 5u))
        return PORTABLE_RENDER_INVALID_RESOURCE;
    needed = source_stride * 5u * height;
    if (needed > source_size)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    for (sy = 0; sy < height; ++sy) {
        const uint8_t *row = mask_and_planes + (size_t)sy * source_stride * 5u;
        for (sx = 0; sx < width; ++sx) {
            uint8_t mask = (uint8_t)bit_at(row, sx);
            uint8_t c;
            int64_t dx = (int64_t)x + sx, dy = (int64_t)y + sy;
            if (!mask || dx < fb->clip.left || dx >= fb->clip.right ||
                dy < fb->clip.top || dy >= fb->clip.bottom)
                continue;
            c = (uint8_t)(bit_at(row + source_stride, sx) |
                          (bit_at(row + source_stride * 2u, sx) << 1) |
                          (bit_at(row + source_stride * 3u, sx) << 2) |
                          (bit_at(row + source_stride * 4u, sx) << 3));
            fb->pixels[(size_t)dy * fb->stride + (size_t)dx] = c;
        }
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_bitmap_draw_interleaved_ega4(
    PortableFramebuffer *fb,
    int32_t x,
    int32_t y,
    uint16_t width,
    uint16_t height,
    const uint8_t *source,
    size_t source_size,
    size_t bytes_per_plane_row,
    size_t row_stride)
{
    size_t needed;
    uint16_t sx, sy;
    if (fb == NULL || fb->pixels == NULL || source == NULL || width == 0 || height == 0)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (bytes_per_plane_row < ((size_t)width + 7u) / 8u ||
        bytes_per_plane_row > SIZE_MAX / 4u || row_stride < bytes_per_plane_row * 4u ||
        row_stride > SIZE_MAX / (size_t)height)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    needed = row_stride * (size_t)height;
    if (needed > source_size)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    for (sy = 0; sy < height; ++sy) {
        const uint8_t *row = source + (size_t)sy * row_stride;
        for (sx = 0; sx < width; ++sx) {
            size_t byte_in_plane = (size_t)sx >> 3;
            unsigned shift = 7u - ((unsigned)sx & 7u);
            const uint8_t *group = row + byte_in_plane * 4u;
            uint8_t color = (uint8_t)(((group[0] >> shift) & 1u) |
                                      (((group[1] >> shift) & 1u) << 1) |
                                      (((group[2] >> shift) & 1u) << 2) |
                                      (((group[3] >> shift) & 1u) << 3));
            portable_put_pixel(fb, (int32_t)((int64_t)x + sx),
                               (int32_t)((int64_t)y + sy), color);
        }
    }
    return PORTABLE_RENDER_OK;
}

