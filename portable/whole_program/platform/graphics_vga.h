#ifndef SIMANT_GRAPHICS_VGA_H
#define SIMANT_GRAPHICS_VGA_H
#include <stddef.h>
#include <stdint.h>

typedef uint8_t SimVgaPlanes[4][65536];

/* One aperture byte's pixels held by one plane set (mask bit 7 = leftmost). */
typedef struct SimVgaSpan {
    SimVgaPlanes *planes;
    uint8_t mask;
} SimVgaSpan;

/* Presentation hook: returns the plane sets owning the eight pixels of the
 * aperture byte at `offset`, or 0 for the card's own planes. */
typedef unsigned (*SimVgaRoute)(void *context, uint16_t offset, SimVgaSpan spans[8]);

/* Mode 10h/12h CPU aperture. Display geometry never bounds these addresses. */
typedef struct SimVga {
    uint8_t planes[4][65536];
    uint8_t latch[4];
    uint8_t sequencer_index, graphics_index;
    uint8_t map_mask, set_reset, enable_set_reset, color_compare;
    uint8_t data_rotate, read_map, mode, color_dont_care, bit_mask;
    uint8_t written; /* CPU stores since the last presented refresh */
    SimVgaRoute route;
    void *route_context;
} SimVga;

void sim_vga_reset(SimVga *vga);
void sim_vga_set_router(SimVga *vga, SimVgaRoute route, void *context);
void sim_vga_out(SimVga *vga, uint16_t port, uint8_t value);
uint8_t sim_vga_read(SimVga *vga, uint16_t offset);
void sim_vga_write(SimVga *vga, uint16_t offset, uint8_t value);
uint16_t sim_vga_pixel_offset(int16_t x, int16_t y, uint16_t stride);
uint8_t sim_vga_color(const SimVga *vga, uint16_t offset, unsigned bit);
void sim_vga_store_color(SimVga *vga, uint16_t offset, unsigned bit, uint8_t color);
void sim_vga_present_planes(const SimVgaPlanes *planes, uint8_t *pixels, size_t stride,
                            int left, int top, int width, int height);
void sim_vga_present(const SimVga *vga, uint8_t *pixels, size_t stride, unsigned height);
#endif
