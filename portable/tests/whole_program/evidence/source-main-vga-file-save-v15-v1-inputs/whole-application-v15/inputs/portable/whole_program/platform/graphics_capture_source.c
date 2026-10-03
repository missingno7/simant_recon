#include "graphics_capture_source.h"
#include "graphics_cursor_hooks.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"
#include "portable/whole_program/platform/handles.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

SimGraphicsCaptureSizeCallback g_9140;
SimGraphicsCaptureSizeCallback g_9144;
SimGraphicsCaptureCallback g_9148;

static uint8_t *s_cursor_capture_buffer;
static size_t s_cursor_capture_capacity;

static int32_t s00_sar3(uint16_t word)
{
    int32_t signed_word = word < 0x8000u ? (int32_t)word :
                                           (int32_t)word - 0x10000;
    int32_t quotient = signed_word / 8;
    if (signed_word < 0 && signed_word % 8 != 0)
        --quotient;
    return quotient;
}

static void s00_source_dimensions(int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  uint16_t *columns_out,
                                  uint16_t *height_out)
{
    uint16_t right_minus_one = (uint16_t)((uint16_t)right - 1u);
    uint16_t first_column = (uint16_t)s00_sar3((uint16_t)left);
    uint16_t last_column = (uint16_t)s00_sar3(right_minus_one);
    *columns_out = (uint16_t)(last_column - first_column + 1u);
    *height_out = (uint16_t)((uint16_t)bottom - (uint16_t)top);
}

uint16_t sim_graphics_s00_capture_size_word(int16_t left, int16_t top,
                                           int16_t right, int16_t bottom)
{
    uint16_t columns, height;
    uint32_t bytes;
    s00_source_dimensions(left, top, right, bottom, &columns, &height);
    /* Source L0537 uses 16-bit SAR coordinates, MUL BX and 32-bit shifts;
     * the function returns AX, so preserve the low source word. */
    bytes = 4u * (uint32_t)columns * (uint32_t)height + 4u;
    return (uint16_t)bytes;
}

uint16_t sim_graphics_s00_mask_capture_size_word(int16_t left, int16_t top,
                                                 int16_t right, int16_t bottom)
{
    uint16_t columns, height;
    uint32_t bytes;
    s00_source_dimensions(left, top, right, bottom, &columns, &height);
    bytes = (uint32_t)columns * (uint32_t)height + 4u;
    return (uint16_t)bytes;
}

static SimGraphicsStatus checked_shape(const SimGraphicsDriver *graphics,
                                       int16_t left, int16_t top,
                                       int16_t right, int16_t bottom,
                                       uint16_t *columns, uint16_t *height,
                                       size_t *size, int allow_exterior)
{
    if (graphics == NULL || graphics->pixel_storage == NULL ||
        left < 0 || top < 0 || right <= left || bottom <= top ||
        (!allow_exterior && (right > graphics->g_3DB2 ||
                             bottom > graphics->g_3DB4)) ||
        (allow_exterior && (left >= graphics->g_3DB2 ||
                            top >= graphics->g_3DB4)))
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s00_source_dimensions(left, top, right, bottom, columns, height);
    if (*columns == 0 || *height == 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    *size = 4u + (size_t)*columns * (size_t)*height * 4u;
    if (*size > UINT16_MAX || *size != sim_graphics_s00_capture_size_word(
            left, top, right, bottom))
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_capture_size_checked(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, size_t *size_out)
{
    uint16_t columns, height;
    size_t size;
    SimGraphicsStatus status;
    if (size_out == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    status = checked_shape(graphics, left, top, right, bottom,
                           &columns, &height, &size, 0);
    (void)columns;
    (void)height;
    if (status == SIM_GRAPHICS_OK)
        *size_out = size;
    return status;
}

static SimGraphicsStatus capture_rect_impl(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size,
    int allow_exterior)
{
    uint16_t columns, height;
    size_t required, row_bytes;
    int32_t aligned_left;
    unsigned y, plane, byte_x;
    SimGraphicsStatus status;
    if (buffer == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    status = checked_shape(graphics, left, top, right, bottom,
                           &columns, &height, &required, allow_exterior);
    if (status != SIM_GRAPHICS_OK)
        return status;
    if (buffer_size < required)
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    row_bytes = columns;
    aligned_left = ((int32_t)left >> 3) * 8;
    buffer[0] = (uint8_t)(columns * 8u);
    buffer[1] = (uint8_t)((columns * 8u) >> 8);
    buffer[2] = (uint8_t)height;
    buffer[3] = (uint8_t)(height >> 8);
    for (y = 0; y < height; ++y) {
        for (plane = 0; plane < 4; ++plane) {
            for (byte_x = 0; byte_x < columns; ++byte_x) {
                uint8_t packed = 0;
                unsigned bit;
                for (bit = 0; bit < 8; ++bit) {
                    size_t pixel_index = (size_t)(top + (int32_t)y) *
                                         graphics->framebuffer.stride +
                                         (size_t)(aligned_left +
                                                  (int32_t)(byte_x * 8u + bit));
                    int32_t pixel_x = aligned_left +
                                      (int32_t)(byte_x * 8u + bit);
                    int32_t pixel_y = (int32_t)top + (int32_t)y;
                    if (pixel_x >= 0 && pixel_x < graphics->g_3DB2 &&
                        pixel_y >= 0 && pixel_y < graphics->g_3DB4 &&
                        (graphics->pixel_storage[pixel_index] &
                         (1u << plane)) != 0)
                        packed |= (uint8_t)(0x80u >> bit);
                }
                buffer[4u + (size_t)y * row_bytes * 4u +
                       (size_t)plane * row_bytes + byte_x] = packed;
            }
        }
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_capture_rect(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    return capture_rect_impl(graphics, left, top, right, bottom,
                             buffer, buffer_size, 0);
}

SimGraphicsStatus sim_graphics_s00_capture_rect_source_aperture(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    uint16_t columns, height;
    uint32_t first_column, last_column;
    size_t required;
    int32_t aligned_left;
    const uint8_t *planes[4];
    unsigned y, plane, byte_x;

    if (graphics == NULL || graphics != sim_graphics_source_owner() ||
        graphics->pixel_storage == NULL || buffer == NULL ||
        left < 0 || top < 0 || right <= left || bottom <= top ||
        right > graphics->g_3DB2 || graphics->g_3DB6 <= 0 ||
        graphics->g_3DB2 <= 0 || graphics->g_3DB4 <= 0 ||
        (graphics->video_mode != SIM_GRAPHICS_MODE_EGA_640X350 &&
         graphics->video_mode != SIM_GRAPHICS_MODE_VGA_640X480))
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    s00_source_dimensions(left, top, right, bottom, &columns, &height);
    if (columns == 0 || height == 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    required = 4u + (size_t)columns * (size_t)height * 4u;
    if (required > UINT16_MAX || required !=
        sim_graphics_s00_capture_size_word(left, top, right, bottom) ||
        buffer_size < required)
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    aligned_left = ((int32_t)left / 8) * 8;
    first_column = (uint32_t)aligned_left / 8u;
    last_column = first_column + columns;
    if (last_column > (uint32_t)graphics->g_3DB6)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    if (graphics->framebuffer.stride < (size_t)graphics->g_3DB2 ||
        graphics->pixel_storage_size <
            graphics->framebuffer.stride * (size_t)graphics->g_3DB4)
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    /* S00 addresses each row as y*g3DB6 + (left>>3). Bound the final byte
     * against the same 64 KiB aperture exposed by the existing tile owner. */
    {
        uint64_t end = ((uint64_t)(uint16_t)(bottom - 1) *
                        (uint16_t)graphics->g_3DB6) + last_column;
        if (end > SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
            return SIM_GRAPHICS_INVALID_ARGUMENT;
    }
    for (plane = 0; plane < 4; ++plane) {
        size_t plane_size = 0;
        planes[plane] = sim_graphics_tile_upload_plane(plane, &plane_size);
        if (planes[plane] == NULL ||
            plane_size != SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
            return SIM_GRAPHICS_UNSUPPORTED_MODE;
    }

    buffer[0] = (uint8_t)(columns * 8u);
    buffer[1] = (uint8_t)((columns * 8u) >> 8);
    buffer[2] = (uint8_t)height;
    buffer[3] = (uint8_t)(height >> 8);
    for (y = 0; y < height; ++y) {
        const int32_t pixel_y = (int32_t)top + (int32_t)y;
        for (plane = 0; plane < 4; ++plane) {
            for (byte_x = 0; byte_x < columns; ++byte_x) {
                uint8_t packed = 0;
                unsigned bit;
                for (bit = 0; bit < 8; ++bit) {
                    const int32_t pixel_x = aligned_left +
                        (int32_t)(byte_x * 8u + bit);
                    int set;
                    if (pixel_y < graphics->g_3DB4) {
                        const size_t pixel_index =
                            (size_t)pixel_y * graphics->framebuffer.stride +
                            (size_t)pixel_x;
                        if (pixel_x < 0 || pixel_x >= graphics->g_3DB2 ||
                            pixel_index >= graphics->pixel_storage_size)
                            return SIM_GRAPHICS_INVALID_ARGUMENT;
                        set = (graphics->pixel_storage[pixel_index] &
                               (1u << plane)) != 0;
                    } else {
                        const size_t source_offset =
                            (size_t)pixel_y * (size_t)graphics->g_3DB6 +
                            (size_t)pixel_x / 8u;
                        set = (planes[plane][source_offset] &
                               (uint8_t)(0x80u >> (pixel_x & 7))) != 0;
                    }
                    if (set)
                        packed |= (uint8_t)(0x80u >> bit);
                }
                buffer[4u + (size_t)y * (size_t)columns * 4u +
                       (size_t)plane * columns + byte_x] = packed;
            }
        }
    }
    return SIM_GRAPHICS_OK;
}

static SimGraphicsStatus capture_cursor_rect(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer != s_cursor_capture_buffer ||
        buffer_size != s_cursor_capture_capacity)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    return capture_rect_impl(graphics, left, top, right, bottom,
                             buffer, buffer_size, 1);
}

static SimGraphicsDriver *capture_owner(void)
{
    return sim_graphics_source_owner();
}

static int16_t source_g9140_size(int16_t left, int16_t top,
                                 int16_t right, int16_t bottom)
{
    return (int16_t)sim_graphics_s00_capture_size_word(left, top, right, bottom);
}

static int16_t source_g9144_size(int16_t left, int16_t top,
                                 int16_t right, int16_t bottom)
{
    /* S00 _11FB is L0537+4, the 1-plane/mask save-size variant. */
    return (int16_t)sim_graphics_s00_mask_capture_size_word(left, top,
                                                            right, bottom);
}

static void source_g9148_capture(int16_t left, int16_t top,
                                 int16_t right, int16_t bottom, char *buffer)
{
    SimGraphicsDriver *graphics = capture_owner();
    size_t required;
    SimGraphicsStatus status;
    uint8_t *display_busy = (uint8_t *)&g_3DD4;

    if (graphics == NULL || display_busy == NULL)
        abort();
    /* S00 _0550 increments the low byte of g3DD4 before any cursor work and
     * decrements it after the post-capture mouse branch. It does not alter
     * the high byte of this shared source word. */
    ++*display_busy;

    /* Preserve the source's inclusive overlap test and callback order:
     * g4344 is the cursor bottom, g4346 its right edge. */
    if (g_4333 == 0 && top <= (int16_t)g_4344 &&
        bottom >= (int16_t)g_4342 && left <= (int16_t)g_4346 &&
        right >= (int16_t)g_4340) {
        if (!sim_graphics_cursor_hooks_hide()) {
            graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
            fprintf(stderr, "S00 capture requires bound source cursor-hide service\n");
            exit(70);
        }
    }
    if (buffer == NULL) {
        graphics->last_status = SIM_GRAPHICS_INVALID_ARGUMENT;
        fprintf(stderr, "S00 capture received a null source buffer\n");
        exit(70);
    }
    if ((uint8_t *)buffer == s_cursor_capture_buffer) {
        status = capture_cursor_rect(graphics, left, top, right, bottom,
                                     (uint8_t *)buffer,
                                     s_cursor_capture_capacity);
    } else {
        if (bottom <= graphics->g_3DB4) {
            status = sim_graphics_s00_capture_size_checked(graphics, left, top,
                                                           right, bottom,
                                                           &required);
            if (status == SIM_GRAPHICS_OK)
                status = sim_graphics_s00_capture_rect(graphics, left, top,
                                                       right, bottom,
                                                       (uint8_t *)buffer,
                                                       required);
        } else {
            size_t remaining = 0;
            if (!sim_handles_global_measure_payload(buffer, &remaining))
                status = SIM_GRAPHICS_INVALID_ARGUMENT;
            else
                status = sim_graphics_s00_capture_rect_source_aperture(
                    graphics, left, top, right, bottom,
                    (uint8_t *)buffer, remaining);
        }
    }
    graphics->last_status = status;
    if (status != SIM_GRAPHICS_OK) {
        fprintf(stderr, "S00 source capture outside the supported framebuffer contract\n");
        exit(70);
    }

    /* The source checks these fields after the copy, independently of the
     * pre-capture overlap decision. The callbacks retain m1B73's actual
     * show-level, mouse-event, hot-box, and redraw side effects. */
    if (g_4333 == 0) {
        if (g_4365 != 0) {
            if (g_4331 != 0 && !sim_graphics_cursor_hooks_redraw_if_shown()) {
                graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
                fprintf(stderr, "S00 capture requires bound source cursor-redraw service\n");
                exit(70);
            }
        } else if (g_4366 == 0 && !sim_graphics_cursor_hooks_update()) {
            graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
            fprintf(stderr, "S00 capture requires bound source cursor-update service\n");
            exit(70);
        }
    }

    --*display_busy;
}

SimGraphicsStatus sim_graphics_source_capture_bind(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics != sim_graphics_source_owner() ||
        graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    g_9140 = source_g9140_size;
    g_9144 = source_g9144_size;
    g_9148 = source_g9148_capture;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_source_capture_cursor_buffer(
    uint8_t *buffer, size_t capacity)
{
    if (buffer == NULL || capacity == 0 || g_9148 == NULL ||
        capture_owner() == NULL || s_cursor_capture_buffer != NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s_cursor_capture_buffer = buffer;
    s_cursor_capture_capacity = capacity;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_capture_cursor_buffer_clear(uint8_t *buffer)
{
    if (buffer != NULL && buffer == s_cursor_capture_buffer) {
        s_cursor_capture_buffer = NULL;
        s_cursor_capture_capacity = 0;
    }
}

void sim_graphics_source_capture_unbind(void)
{
    s_cursor_capture_buffer = NULL;
    s_cursor_capture_capacity = 0;
    g_9140 = NULL;
    g_9144 = NULL;
    g_9148 = NULL;
}
