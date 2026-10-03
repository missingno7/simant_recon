#include "graphics_s00_raster_source.h"

#include <stdlib.h>
#include <string.h>

extern char g_3D20[128];

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static uint16_t ror16(uint16_t value, unsigned count)
{
    count &= 15u;
    if (count == 0)
        return value;
    return (uint16_t)((value >> count) | (uint16_t)(value << (16u - count)));
}

static int checked_extent(size_t base, size_t count, size_t *out)
{
    if (count != 0 && base > (SIZE_MAX - count))
        return 0;
    *out = base + count;
    return 1;
}

static int valid_rect(const SimS00SourceRect *rect)
{
    return rect != NULL && rect->right >= rect->left &&
           rect->bottom >= rect->top;
}

SimS00RasterStatus sim_s00_raster_copy_rect(
    const SimS00SourceRect *source_rect, const uint8_t *source,
    size_t source_size, const SimS00SourceRect *clip_rect,
    uint8_t *destination, size_t destination_size)
{
    int32_t x0, x1, y0, y1;
    int32_t source_width, destination_width;
    size_t source_stride, destination_stride, copy_bytes, rows;
    int32_t row;
    unsigned plane;

    if (!valid_rect(source_rect) || !valid_rect(clip_rect) ||
        source == NULL || destination == NULL || source_size < 4 ||
        destination_size < 4)
        return SIM_S00_RASTER_INVALID_ARGUMENT;

    x0 = source_rect->left > clip_rect->left ? source_rect->left : clip_rect->left;
    x1 = source_rect->right < clip_rect->right ? source_rect->right : clip_rect->right;
    y0 = source_rect->top > clip_rect->top ? source_rect->top : clip_rect->top;
    y1 = source_rect->bottom < clip_rect->bottom ? source_rect->bottom : clip_rect->bottom;
    if (x0 >= x1 || y0 >= y1)
        return SIM_S00_RASTER_OK;

    source_width = read_u16(source);
    destination_width = read_u16(destination);
    if (source_width == 0 || destination_width == 0 ||
        source_rect->left < 0 || source_rect->top < 0 ||
        clip_rect->left < 0 || clip_rect->top < 0 ||
        (source_rect->right - source_rect->left) != source_width ||
        (clip_rect->right - clip_rect->left) != destination_width)
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;

    /* The assembly copies whole planar bytes and has no edge-bit rotate. The
     * source callback contract therefore requires byte-aligned overlap. */
    if (((x0 - source_rect->left) & 7) != 0 ||
        ((x0 - clip_rect->left) & 7) != 0 ||
        ((x1 - x0) & 7) != 0)
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;

    source_stride = ((size_t)(uint16_t)source_width + 7u) >> 3;
    destination_stride = ((size_t)(uint16_t)destination_width + 7u) >> 3;
    copy_bytes = (size_t)(x1 - x0) >> 3;
    rows = (size_t)(y1 - y0);
    {
        size_t source_extent, destination_extent;
        size_t source_rows = (size_t)(uint16_t)read_u16(source + 2);
        size_t destination_rows = (size_t)(uint16_t)read_u16(destination + 2);
        if (!checked_extent(4u, source_rows * source_stride * 4u, &source_extent) ||
            !checked_extent(4u, destination_rows * destination_stride * 4u,
                            &destination_extent))
            return SIM_S00_RASTER_INVALID_ARGUMENT;
        if (source_extent > source_size || destination_extent > destination_size)
            return SIM_S00_RASTER_BUFFER_TOO_SMALL;
    }
    if ((size_t)(x0 - source_rect->left) / 8u + copy_bytes > source_stride ||
        (size_t)(x0 - clip_rect->left) / 8u + copy_bytes > destination_stride ||
        (size_t)(y0 - source_rect->top) + rows > (size_t)read_u16(source + 2) ||
        (size_t)(y0 - clip_rect->top) + rows > (size_t)read_u16(destination + 2))
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;

    for (row = 0; row < (int32_t)rows; ++row) {
        size_t source_row = 4u + ((size_t)(y0 - source_rect->top + row) * 4u *
                                  source_stride);
        size_t destination_row = 4u + ((size_t)(y0 - clip_rect->top + row) * 4u *
                                       destination_stride);
        for (plane = 0; plane < 4; ++plane) {
            size_t source_at = source_row + plane * source_stride +
                               (size_t)(x0 - source_rect->left) / 8u;
            size_t destination_at = destination_row + plane * destination_stride +
                                    (size_t)(x0 - clip_rect->left) / 8u;
            memcpy(destination + destination_at, source + source_at, copy_bytes);
        }
    }
    return SIM_S00_RASTER_OK;
}

static SimS00RasterStatus shifted_blit(const uint8_t *image, size_t image_size,
                                      uint8_t *buffer, size_t buffer_size,
                                      int16_t shift, int16_t flag,
                                      int use_source_mask)
{
    static const uint8_t opaque_edge_mask[8] = {
        0xff, 0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe
    };
    uint16_t image_width, image_height, buffer_width, buffer_height;
    size_t source_stride, destination_stride, source_row_stride;
    size_t source_need, destination_need;
    size_t destination_base = 4;
    size_t count, row, column;
    unsigned bit_shift;

    if (image == NULL || buffer == NULL || image_size < 4 || buffer_size < 4 ||
        shift < 0 || shift > 15 || (flag != 0 && flag != 1))
        return SIM_S00_RASTER_INVALID_ARGUMENT;
    image_width = read_u16(image);
    image_height = read_u16(image + 2);
    buffer_width = read_u16(buffer);
    buffer_height = read_u16(buffer + 2);
    if (image_width == 0 || image_height == 0 || buffer_width == 0 ||
        buffer_height == 0)
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;

    source_stride = ((size_t)image_width + 7u) >> 3;
    destination_stride = ((size_t)buffer_width + 7u) >> 3;
    /* The source routines advance five byte-rows per image row. The masked
     * entry consumes a mask plus four color rows; the opaque entry consumes
     * four color rows and preserves the fifth-row spacing. */
    source_row_stride = source_stride * (use_source_mask ? 5u : 4u);
    if (use_source_mask) {
        if (!checked_extent(4u, (size_t)image_height * source_row_stride,
                            &source_need))
            return SIM_S00_RASTER_INVALID_ARGUMENT;
    } else {
        size_t last_row = (size_t)(image_height - 1u) * source_row_stride;
        size_t last_column = source_stride - 1u;
        if (!checked_extent(4u, last_row + last_column + 3u * source_stride + 1u,
                            &source_need))
            return SIM_S00_RASTER_INVALID_ARGUMENT;
    }
    if (
        !checked_extent(4u, (size_t)buffer_height * destination_stride * 4u,
                        &destination_need))
        return SIM_S00_RASTER_INVALID_ARGUMENT;
    if (source_need > image_size || destination_need > buffer_size)
        return SIM_S00_RASTER_BUFFER_TOO_SMALL;
    if ((uint16_t)flag >= buffer_height)
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;

    count = image_height;
    if (count > (size_t)buffer_height - (size_t)flag)
        count = (size_t)buffer_height - (size_t)flag;
    destination_base += (size_t)destination_stride * 4u * (size_t)flag;
    bit_shift = (unsigned)shift & 7u;
    destination_base += (unsigned)shift >> 3;

    for (row = 0; row < count; ++row) {
        size_t src_row = 4u + row * source_row_stride;
        size_t dst_row = destination_base + row * destination_stride * 4u;
        for (column = 0; column < source_stride; ++column) {
            uint16_t mask = 0x00ffu;
            unsigned plane;
            if (use_source_mask) {
                mask = ror16((uint16_t)image[src_row + column], bit_shift);
            } else {
                uint8_t mask_byte = column + 1u == source_stride
                    ? opaque_edge_mask[image_width & 7u] : 0xffu;
                mask = ror16((uint16_t)mask_byte, bit_shift);
            }
            for (plane = 0; plane < 4; ++plane) {
                size_t source_at = src_row +
                    column +
                    (use_source_mask ? (plane + 1u) : plane) * source_stride;
                size_t destination_at = dst_row + (size_t)plane * destination_stride + column;
                if (source_at >= image_size)
                    return SIM_S00_RASTER_BUFFER_TOO_SMALL;
                uint16_t data = use_source_mask
                    ? ror16((uint16_t)image[source_at], bit_shift)
                    : ror16((uint16_t)image[source_at], bit_shift);
                uint16_t old_value;
                uint16_t next_value;
                if (destination_at + 1u >= buffer_size)
                    return SIM_S00_RASTER_BUFFER_TOO_SMALL;
                old_value = read_u16(buffer + destination_at);
                next_value = (uint16_t)(old_value ^
                    ((uint16_t)(old_value ^ data) & mask));
                buffer[destination_at] = (uint8_t)next_value;
                buffer[destination_at + 1u] = (uint8_t)(next_value >> 8);
            }
        }
    }
    return SIM_S00_RASTER_OK;
}

SimS00RasterStatus sim_s00_raster_masked_blit(
    const uint8_t *image, size_t image_size, uint8_t *buffer,
    size_t buffer_size, int16_t shift, int16_t flag)
{
    return shifted_blit(image, image_size, buffer, buffer_size,
                        shift, flag, 1);
}

SimS00RasterStatus sim_s00_raster_opaque_blit(
    const uint8_t *image, size_t image_size, uint8_t *buffer,
    size_t buffer_size, int16_t shift, int16_t flag)
{
    return shifted_blit(image, image_size, buffer, buffer_size,
                        shift, flag, 0);
}

SimS00RasterStatus sim_s00_raster_pattern_transfer(
    const uint8_t pattern[128], uint8_t *destination,
    size_t destination_size, uint16_t width)
{
    size_t stride;
    size_t last;
    unsigned row;
    if (pattern == NULL || destination == NULL || width < 16u ||
        (width & 7u) != 0)
        return SIM_S00_RASTER_UNSUPPORTED_DOMAIN;
    stride = width >> 3;
    if (!checked_extent(0, 63u * stride + 2u, &last) || last > destination_size)
        return SIM_S00_RASTER_BUFFER_TOO_SMALL;
    for (row = 0; row < 64u; ++row)
        memcpy(destination + (size_t)row * stride, pattern + row * 2u, 2u);
    return SIM_S00_RASTER_OK;
}

/* These source-compatible leaves use the source buffers supplied by the
 * callers. Bounds-aware callers should use the explicit-size APIs above. */
void o00_35A6_02FD(void *source_rect_arg, void *source_arg,
                    void *clip_rect_arg, void *destination_arg)
{
    SimS00SourceRect *source_rect = (SimS00SourceRect *)source_rect_arg;
    const uint8_t *source = (const uint8_t *)source_arg;
    SimS00SourceRect *clip_rect = (SimS00SourceRect *)clip_rect_arg;
    uint8_t *destination = (uint8_t *)destination_arg;
    size_t source_size, destination_size;
    size_t source_stride, destination_stride;
    SimS00RasterStatus status;
    if (source_rect == NULL || clip_rect == NULL || source == NULL || destination == NULL)
        abort();
    source_stride = ((size_t)(uint16_t)(source_rect->right - source_rect->left) + 7u) >> 3;
    destination_stride = ((size_t)(uint16_t)(clip_rect->right - clip_rect->left) + 7u) >> 3;
    source_size = 4u + (size_t)read_u16(source + 2) * source_stride * 4u;
    destination_size = 4u + (size_t)read_u16(destination + 2) *
                       destination_stride * 4u;
    status = sim_s00_raster_copy_rect(source_rect, source,
                                      source_size, clip_rect,
                                      destination, destination_size);
    if (status != SIM_S00_RASTER_OK)
        abort();
}

void o00_35A6_0007(void *image_arg, void *buffer_arg, int16_t shift, int16_t flag)
{
    const uint8_t *image = (const uint8_t *)image_arg;
    uint8_t *buffer = (uint8_t *)buffer_arg;
    size_t image_stride, buffer_stride, image_size, buffer_size;
    SimS00RasterStatus status;
    if (image == NULL || buffer == NULL)
        abort();
    image_stride = ((size_t)read_u16(image) + 7u) >> 3;
    buffer_stride = ((size_t)read_u16(buffer) + 7u) >> 3;
    image_size = 4u + (size_t)read_u16(image + 2) * image_stride * 5u;
    buffer_size = 4u + (size_t)read_u16(buffer + 2) * buffer_stride * 4u;
    status = sim_s00_raster_masked_blit(image, image_size,
                                        buffer, buffer_size,
                                        shift, flag);
    if (status != SIM_S00_RASTER_OK)
        abort();
}

void o00_35A6_0177(void *image_arg, void *buffer_arg, int16_t shift, int16_t flag)
{
    const uint8_t *image = (const uint8_t *)image_arg;
    uint8_t *buffer = (uint8_t *)buffer_arg;
    size_t image_stride, buffer_stride, image_size, buffer_size;
    SimS00RasterStatus status;
    if (image == NULL || buffer == NULL)
        abort();
    image_stride = ((size_t)read_u16(image) + 7u) >> 3;
    buffer_stride = ((size_t)read_u16(buffer) + 7u) >> 3;
    image_size = 4u + (size_t)read_u16(image + 2) * image_stride * 5u;
    buffer_size = 4u + (size_t)read_u16(buffer + 2) * buffer_stride * 4u;
    status = sim_s00_raster_opaque_blit(image, image_size,
                                        buffer, buffer_size,
                                        shift, flag);
    if (status != SIM_S00_RASTER_OK)
        abort();
}

void o00_35A6_0406(void *destination_arg, int16_t width)
{
    uint8_t *destination = (uint8_t *)destination_arg;
    size_t destination_size;
    size_t stride;
    SimS00RasterStatus status;
    if (destination == NULL || width <= 0)
        abort();
    stride = ((size_t)(uint16_t)width) >> 3;
    destination_size = 31u * stride + 2u;
    status = sim_s00_raster_pattern_transfer((const uint8_t *)g_3D20,
                                             destination,
                                             destination_size,
                                             (uint16_t)width);
    if (status != SIM_S00_RASTER_OK)
        abort();
}
