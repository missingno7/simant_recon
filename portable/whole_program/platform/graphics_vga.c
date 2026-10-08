#include "graphics_vga.h"
#include <string.h>

void sim_vga_reset(SimVga *vga)
{
    memset(vga, 0, sizeof(*vga));
    vga->map_mask = 15;
    vga->bit_mask = 255;
    vga->color_dont_care = 15;
}

void sim_vga_out(SimVga *vga, uint16_t port, uint8_t value)
{
    if (port == 0x3c4) vga->sequencer_index = value;
    else if (port == 0x3c5 && vga->sequencer_index == 2) vga->map_mask = value & 15;
    else if (port == 0x3ce) vga->graphics_index = value;
    else if (port == 0x3cf) {
        switch (vga->graphics_index) {
        case 0: vga->set_reset = value & 15; break;
        case 1: vga->enable_set_reset = value & 15; break;
        case 2: vga->color_compare = value & 15; break;
        case 3: vga->data_rotate = value; break;
        case 4: vga->read_map = value & 3; break;
        case 5: vga->mode = value; break;
        case 7: vga->color_dont_care = value & 15; break;
        case 8: vga->bit_mask = value; break;
        }
    }
}

uint8_t sim_vga_read(SimVga *vga, uint16_t offset)
{
    unsigned plane;
    uint8_t compare = 255;
    for (plane = 0; plane < 4; ++plane) {
        vga->latch[plane] = vga->planes[plane][offset];
        if (vga->color_dont_care & (1u << plane))
            compare &= (uint8_t)(vga->latch[plane] ^
                ((vga->color_compare & (1u << plane)) ? 0 : 255));
    }
    return (vga->mode & 8) ? compare : vga->latch[vga->read_map];
}

static uint8_t rotate(uint8_t value, unsigned count)
{
    count &= 7;
    return count ? (uint8_t)((value >> count) | (value << (8 - count))) : value;
}

void sim_vga_write(SimVga *vga, uint16_t offset, uint8_t value)
{
    unsigned plane, mode = vga->mode & 3;
    uint8_t rotated = rotate(value, vga->data_rotate);
    if (vga->map_mask & 15u) vga->written = 1;
    for (plane = 0; plane < 4; ++plane) {
        uint8_t data, mask = vga->bit_mask;
        if (!(vga->map_mask & (1u << plane))) continue;
        if (mode == 1) {
            vga->planes[plane][offset] = vga->latch[plane];
            continue;
        }
        if (mode == 2) data = (value & (1u << plane)) ? 255 : 0;
        else if (mode == 3 || (vga->enable_set_reset & (1u << plane)))
            data = (vga->set_reset & (1u << plane)) ? 255 : 0;
        else data = rotated;
        if (mode == 3) mask &= rotated;
        switch (vga->data_rotate & 0x18) {
        case 8: data &= vga->latch[plane]; break;
        case 16: data |= vga->latch[plane]; break;
        case 24: data ^= vga->latch[plane]; break;
        }
        vga->planes[plane][offset] = (uint8_t)((data & mask) | (vga->latch[plane] & ~mask));
    }
}

uint16_t sim_vga_pixel_offset(int16_t x, int16_t y, uint16_t stride)
{
    /* MUL's low AX plus SAR x,3; native signed division alone truncates wrong. */
    int32_t column = x >= 0 ? x / 8 : -((-(int32_t)x + 7) / 8);
    return (uint16_t)((uint16_t)y * (uint32_t)stride + column);
}

uint8_t sim_vga_color(const SimVga *vga, uint16_t offset, unsigned bit)
{
    unsigned plane;
    uint8_t color = 0, mask = (uint8_t)(0x80u >> (bit & 7));
    for (plane = 0; plane < 4; ++plane)
        if (vga->planes[plane][offset] & mask) color |= (uint8_t)(1u << plane);
    return color;
}

void sim_vga_store_color(SimVga *vga, uint16_t offset, unsigned bit, uint8_t color)
{
    unsigned plane;
    uint8_t mask = (uint8_t)(0x80u >> (bit & 7));
    vga->written = 1;
    for (plane = 0; plane < 4; ++plane) {
        uint8_t *byte = &vga->planes[plane][offset];
        *byte = (uint8_t)((*byte & ~mask) | ((color & (1u << plane)) ? mask : 0));
    }
}

void sim_vga_present(const SimVga *vga, uint8_t *pixels, size_t stride, unsigned height)
{
    unsigned y, x;
    for (y = 0; y < height; ++y)
        for (x = 0; x < 640; ++x)
            pixels[y * stride + x] = sim_vga_color(vga, (uint16_t)(y * 80 + x / 8), x);
}
