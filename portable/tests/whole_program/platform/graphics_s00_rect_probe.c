#include "portable/whole_program/platform/graphics.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

int sim_graphics_s00_pattern_probe(const uint8_t *pattern_source,
                                  size_t pattern_source_size,
                                  int16_t left, int16_t top,
                                  int16_t right, int16_t bottom,
                                  int16_t pattern_word,
                                  uint8_t foreground, uint8_t background,
                                  uint8_t *output, size_t output_size)
{
    SimGraphicsDriver graphics;
    SimGraphicsStatus status;
    if (output == NULL || output_size < 640u * 480u)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    status = sim_graphics_init(&graphics);
    if (status != SIM_GRAPHICS_OK)
        return status;
    status = sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_VGA_640X480);
    if (status != SIM_GRAPHICS_OK) {
        sim_graphics_destroy(&graphics);
        return status;
    }
    status = sim_graphics_set_pattern_source(&graphics, pattern_source,
                                             pattern_source_size);
    if (status == SIM_GRAPHICS_OK) {
        graphics.g_3DE0 = foreground;
        graphics.g_3DE2 = background;
        status = sim_graphics_g9138_pattern_rect(&graphics, left, top,
                                                  right, bottom, pattern_word);
    }
    if (status == SIM_GRAPHICS_OK)
        memcpy(output, graphics.pixel_storage, 640u * 480u);
    sim_graphics_destroy(&graphics);
    return status;
}

int sim_graphics_s00_xor_probe(int16_t left, int16_t top,
                               int16_t right, int16_t bottom,
                               uint8_t *output, size_t output_size)
{
    SimGraphicsDriver graphics;
    SimGraphicsStatus status;
    if (output == NULL || output_size < 640u * 480u)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    status = sim_graphics_init(&graphics);
    if (status != SIM_GRAPHICS_OK)
        return status;
    status = sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_VGA_640X480);
    if (status == SIM_GRAPHICS_OK)
        status = sim_graphics_g913C_xor_rect(&graphics, left, top, right, bottom);
    if (status == SIM_GRAPHICS_OK)
        memcpy(output, graphics.pixel_storage, 640u * 480u);
    sim_graphics_destroy(&graphics);
    return status;
}
