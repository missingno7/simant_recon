#include "line16b5.h"

#include <string.h>

PortableSpiderLineBuffer portable_line16b5_source_buffer;

typedef struct LinePoint {
    int32_t x;
    int32_t y;
} LinePoint;

static PortableLine16B5 legacy_state;

static uint16_t word_add(uint16_t a, uint16_t b)
{
    return (uint16_t)(a + b);
}

static int16_t signed_word(uint16_t value)
{
    int32_t extended = (int32_t)value;
    if ((value & UINT16_C(0x8000)) != 0)
        extended -= INT32_C(0x10000);
    return (int16_t)extended;
}

static int32_t sar_one(int32_t value)
{
    /* The source SAR is floor division by two, including negative odd values. */
    return value >= 0 ? value / 2 : -(((-value) + 1) / 2);
}

static unsigned outcode(const PortableLine16B5 *state, LinePoint point)
{
    unsigned code = 0;
    /* f_04D8 names the register pair (SI,DI) as the clipping axes. f_0008
     * enters with (SI,DI)=(y,x), so its width comparison applies to y and its
     * height comparison applies to x. DrawSpider uses square scratch images;
     * keep this source ordering for rectangular diagnostic inputs too. */
    if (point.y < 0)
        code |= 8u;
    else if (point.y > (int32_t)state->width - 1)
        code |= 4u;
    if (point.x < 0)
        code |= 1u;
    else if (point.x > (int32_t)state->height - 1)
        code |= 2u;
    return code;
}

static LinePoint midpoint(LinePoint a, LinePoint b)
{
    uint16_t xsum = word_add((uint16_t)a.x, (uint16_t)b.x);
    uint16_t ysum = word_add((uint16_t)a.y, (uint16_t)b.y);
    LinePoint middle;
    middle.x = sar_one(signed_word(xsum));
    middle.y = sar_one(signed_word(ysum));
    return middle;
}

/* A structured translation of f_16B5_04D8. The boundary search is the
 * original midpoint procedure (including its signed-word midpoint), rather
 * than a floating-point line clip. */
static int clip_line(const PortableLine16B5 *state, LinePoint *first,
                     LinePoint *second)
{
    unsigned swapped = 0;
    unsigned iterations = 0;

    for (;;) {
        unsigned first_code = outcode(state, *first);
        unsigned second_code = outcode(state, *second);
        LinePoint temporary;
        LinePoint middle;
        unsigned boundary;
        int clip_first;

        if ((first_code & second_code) != 0)
            return 0;
        if ((first_code | second_code) == 0) {
            if (swapped != 0) {
                temporary = *first;
                *first = *second;
                *second = temporary;
            }
            return 1;
        }

        if (first->x >= second->x) {
            temporary = *first;
            *first = *second;
            *second = temporary;
            temporary.x = (int32_t)first_code;
            first_code = second_code;
            second_code = (unsigned)temporary.x;
            swapped ^= 1u;
        }
        if ((first_code & 1u) != 0) {
            boundary = 1;
            clip_first = 1;
        } else if ((second_code & 2u) != 0) {
            boundary = 2;
            clip_first = 0;
        } else {
            boundary = 0;
            clip_first = 0;
        }
        if (boundary == 0 && first->y >= second->y) {
            temporary = *first;
            *first = *second;
            *second = temporary;
            temporary.x = (int32_t)first_code;
            first_code = second_code;
            second_code = (unsigned)temporary.x;
            swapped ^= 1u;
        }

        if (boundary == 0) {
            if ((first_code & 8u) != 0) {
                boundary = 3;
                clip_first = 1;
            } else if ((second_code & 4u) != 0) {
                boundary = 4;
                clip_first = 0;
            } else {
                return 0;
            }
        }

        if (boundary == 1 || boundary == 2) {
            int32_t x_boundary = boundary == 1 ? 0 : (int32_t)state->height - 1;
            LinePoint low = *first;
            LinePoint high = *second;
            for (;;) {
                middle = midpoint(low, high);
                if (middle.x == x_boundary)
                    break;
                if (middle.x < x_boundary) {
                    low = middle;
                    low.x++;
                } else {
                    high = middle;
                }
            }
        } else {
            int32_t y_boundary = boundary == 3 ? 0 : (int32_t)state->width - 1;
            LinePoint low = *first;
            LinePoint high = *second;
            for (;;) {
                middle = midpoint(low, high);
                if (middle.y == y_boundary)
                    break;
                if (middle.y < y_boundary) {
                    low = middle;
                    low.y++;
                } else {
                    high = middle;
                }
            }
        }
        if (clip_first)
            *first = middle;
        else
            *second = middle;
        if (++iterations > 256u)
            return 0;
    }
}

static void write_pixel(PortableLine16B5 *state, uint16_t x, uint16_t y,
                        uint16_t color)
{
    size_t address = state->row_offset[y];
    uint8_t value;

    if (state->mode == 0) {
        unsigned shift = 7u - (unsigned)(x & 7u);
        uint8_t mask = (uint8_t)(1u << shift);
        address += x >> 3;
        value = state->pixels[address];
        if ((color & 1u) != 0)
            value |= mask;
        else
            value &= (uint8_t)~mask;
        state->pixels[address] = value;
    } else if (state->mode == 2) {
        unsigned shift = 7u - (unsigned)(x & 7u);
        uint8_t mask = (uint8_t)(1u << shift);
        address += x >> 3;
        for (unsigned plane = 0; plane < 4; ++plane) {
            size_t plane_address = address + (size_t)plane * state->plane_stride;
            value = state->pixels[plane_address];
            if (((color >> plane) & 1u) != 0)
                value |= mask;
            else
                value &= (uint8_t)~mask;
            state->pixels[plane_address] = value;
        }
    } else {
        unsigned shift = (x & 1u) == 0 ? 4u : 0u;
        uint8_t mask = (uint8_t)(15u << shift);
        address += x >> 1;
        value = state->pixels[address];
        value = (uint8_t)((value & (uint8_t)~mask) |
                          (uint8_t)((color & 15u) << shift));
        state->pixels[address] = value;
    }
}

int portable_line16b5_init(PortableLine16B5 *state, uint16_t width,
                           uint16_t height, uint16_t mode,
                           uint8_t *pixels, size_t pixels_size)
{
    uint32_t row_step;
    uint32_t plane_stride;
    uint32_t last_row;
    uint32_t last_byte;
    uint32_t required;

    if (state == NULL || pixels == NULL || width == 0 || width != height ||
        height > PORTABLE_LINE16B5_MAX_HEIGHT || mode > 2)
        return 0;
    row_step = mode == 0 ? (uint32_t)(width >> 3) : (uint32_t)(width >> 1);
    plane_stride = (uint32_t)(width >> 3);
    last_row = (uint32_t)(height - 1u) * row_step;
    if (mode == 0)
        last_byte = (uint32_t)((width - 1u) >> 3);
    else if (mode == 1)
        last_byte = (uint32_t)((width - 1u) >> 1);
    else
        last_byte = 3u * plane_stride + (uint32_t)((width - 1u) >> 3);
    required = last_row + last_byte + 1u;
    if (last_row > UINT16_MAX || required > pixels_size || required > 65536u)
        return 0;

    memset(state, 0, sizeof(*state));
    state->width = width;
    state->height = height;
    state->mode = mode;
    state->plane_stride = (uint16_t)plane_stride;
    state->pixels = pixels;
    state->pixels_size = pixels_size;
    for (uint16_t row = 0; row < height; ++row)
        state->row_offset[row] = (uint16_t)((uint32_t)row * row_step);
    state->initialized = 1;
    return 1;
}

int portable_line16b5_draw(PortableLine16B5 *state, int16_t x0, int16_t y0,
                           int16_t x1, int16_t y1, int16_t color)
{
    LinePoint first = {x0, y0};
    LinePoint second = {x1, y1};
    int32_t delta_x;
    int32_t delta_y;
    int32_t step_y = 1;
    int32_t step_x = 1;
    uint32_t count;
    uint32_t fraction;
    uint32_t accumulator = UINT16_MAX;

    if (state == NULL || state->initialized == 0 ||
        x0 < -4096 || x0 > 4096 || x1 < -4096 || x1 > 4096 ||
        y0 < -4096 || y0 > 4096 || y1 < -4096 || y1 > 4096)
        return 0;
    if (!clip_line(state, &first, &second))
        return 1;

    delta_y = second.y - first.y;
    if (delta_y < 0) {
        delta_y = -delta_y;
        step_y = -1;
    }
    delta_x = second.x - first.x;
    if (delta_x < 0) {
        delta_x = -delta_x;
        step_x = -1;
    }

    /* The assembly makes equal slopes x-major by incrementing its x delta.
     * Its discarded AX value has no later consumer; retain the resulting word. */
    if (delta_x == delta_y)
        ++delta_x;

    if (delta_x > delta_y) {
        int32_t major = delta_x;
        if (step_x < 0) {
            LinePoint temporary = first;
            first = second;
            second = temporary;
            step_y = -step_y;
        }
        if (major <= 0 || major > 65535 || delta_y > 65535)
            return 0;
        fraction = (uint32_t)(((uint64_t)(uint32_t)delta_y << 16) /
                             (uint32_t)major);
        if (fraction > UINT16_MAX)
            return 0;
        count = (uint32_t)major;
        while (count-- != 0) {
            write_pixel(state, (uint16_t)first.x, (uint16_t)first.y,
                        (uint16_t)color);
            ++first.x;
            accumulator += fraction;
            if (accumulator > UINT16_MAX) {
                accumulator &= UINT16_MAX;
                first.y += step_y;
            }
        }
    } else {
        int32_t major = delta_y;
        if (step_y < 0) {
            LinePoint temporary = first;
            first = second;
            second = temporary;
            step_x = -step_x;
        }
        if (major <= 0 || major > 65534 || delta_x > 65535)
            return 0;
        fraction = (uint32_t)(((uint64_t)(uint32_t)delta_x << 16) /
                             (uint32_t)major);
        if (fraction > UINT16_MAX)
            return 0;
        count = (uint32_t)major + 1u;
        while (count-- != 0) {
            write_pixel(state, (uint16_t)first.x, (uint16_t)first.y,
                        (uint16_t)color);
            ++first.y;
            accumulator += fraction;
            if (accumulator > UINT16_MAX) {
                accumulator &= UINT16_MAX;
                first.x += step_x;
            }
        }
    }
    return 1;
}

void f_16B5_0033(void *source_prefix_and_pixels, int16_t mode)
{
    uint8_t *prefix = (uint8_t *)source_prefix_and_pixels;
    uint16_t width;
    uint16_t height;
    uint32_t row_step;
    uint32_t plane_stride;
    uint32_t required;
    uint32_t last_byte;

    portable_line16b5_unbind();
    if (prefix == NULL || mode < 0 || mode > 2)
        return;
    memcpy(&width, prefix, sizeof(width));
    memcpy(&height, prefix + 2, sizeof(height));
    if (width == 0 || width > PORTABLE_LINE16B5_MAX_INLINE_WIDTH ||
        height == 0 || height > PORTABLE_LINE16B5_MAX_INLINE_HEIGHT)
        return;
    row_step = mode == 0 ? (uint32_t)(width >> 3) : (uint32_t)(width >> 1);
    plane_stride = (uint32_t)(width >> 3);
    if (mode == 0)
        last_byte = (uint32_t)((width - 1u) >> 3);
    else if (mode == 1)
        last_byte = (uint32_t)((width - 1u) >> 1);
    else
        last_byte = 3u * plane_stride + (uint32_t)((width - 1u) >> 3);
    required = (uint32_t)(height - 1u) * row_step + last_byte + 1u;
    if (required > PORTABLE_LINE16B5_MAX_INLINE_BYTES)
        return;
    (void)portable_line16b5_init(&legacy_state, width, height,
                                (uint16_t)mode, prefix + 4, required);
}

void f_16B5_0008(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                 int16_t color)
{
    (void)portable_line16b5_draw(&legacy_state, x0, y0, x1, y1, color);
}

void portable_line16b5_unbind(void)
{
    memset(&legacy_state, 0, sizeof(legacy_state));
}
