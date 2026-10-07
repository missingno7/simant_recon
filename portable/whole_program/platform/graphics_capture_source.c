#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics_capture_source.h"
#include "graphics_cursor_hooks.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"
#include "portable/whole_program/platform/handles.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
                                       size_t *size)
{
    if (!graphics || !graphics->pixel_storage || right <= left || bottom <= top)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s00_source_dimensions(left,top,right,bottom,columns,height);
    *size = 4u+(size_t)*columns*(size_t)*height*4u;
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
                           &columns, &height, &size);
    (void)columns;
    (void)height;
    if (status == SIM_GRAPHICS_OK)
        *size_out = size;
    return status;
}

static SimGraphicsStatus capture_rect_impl(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    uint16_t columns, height, si;
    size_t required;
    unsigned row, plane, byte;
    SimVga *vga;
    SimGraphicsStatus status;
    if (!buffer) return SIM_GRAPHICS_INVALID_ARGUMENT;
    status=checked_shape(graphics,left,top,right,bottom,&columns,&height,&required);
    if (status != SIM_GRAPHICS_OK) return status;
    if (buffer_size < required) return SIM_GRAPHICS_INVALID_ARGUMENT;
    vga = (SimVga *)&graphics->vga;
    /* m31AD:L058A/L05C7/L05CA: MUL row stride, SAR left, header STOSW,
     * then four read-map selections and forward byte copies per scanline. */
    si=sim_vga_pixel_offset(left,top,(uint16_t)g_3DB6);
    buffer[0]=(uint8_t)(columns*8u); buffer[1]=(uint8_t)((columns*8u)>>8);
    buffer[2]=(uint8_t)height; buffer[3]=(uint8_t)(height>>8);
    for (row=0;row<height;++row) {
        for (plane=0;plane<4;++plane) {
            sim_vga_out(vga,0x3ce,4); sim_vga_out(vga,0x3cf,(uint8_t)plane);
            for (byte=0;byte<columns;++byte)
                buffer[4u+row*columns*4u+plane*columns+byte]=sim_vga_read(vga,(uint16_t)(si+byte));
        }
        si=(uint16_t)(si+(uint16_t)g_3DB6);
    }
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_s00_capture_rect(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    return capture_rect_impl(graphics, left, top, right, bottom,
                             buffer, buffer_size);
}

static SimGraphicsStatus capture_cursor_rect(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer != s_cursor_capture_buffer ||
        buffer_size != s_cursor_capture_capacity)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    return capture_rect_impl(graphics, left, top, right, bottom,
                             buffer, buffer_size);
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
        status = sim_graphics_s00_capture_size_checked(graphics,left,top,right,bottom,&required);
        if (status == SIM_GRAPHICS_OK)
            status = sim_graphics_s00_capture_rect(graphics,left,top,right,bottom,
                                                  (uint8_t *)buffer,required);
    }
    graphics->last_status = status;
    if (status != SIM_GRAPHICS_OK) {
        fprintf(stderr, "S00 source capture received invalid RAM storage\n");
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
    (*( SimGraphicsCaptureSizeCallback *)(void *)&driver_callback_table[6]) = source_g9140_size;
    (*( SimGraphicsCaptureSizeCallback *)(void *)&driver_callback_table[7]) = source_g9144_size;
    (*( SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8]) = source_g9148_capture;
    return SIM_GRAPHICS_OK;
}

SimGraphicsStatus sim_graphics_source_capture_cursor_buffer(
    uint8_t *buffer, size_t capacity)
{
    if (buffer == NULL || capacity == 0 || (*( SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8]) == NULL ||
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
    (*( SimGraphicsCaptureSizeCallback *)(void *)&driver_callback_table[6]) = NULL;
    (*( SimGraphicsCaptureSizeCallback *)(void *)&driver_callback_table[7]) = NULL;
    (*( SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8]) = NULL;
}
