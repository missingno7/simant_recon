#include "palette_host.h"

#include <string.h>

static void project(SimSdlPaletteHost *palette)
{
    unsigned i;
    palette->ready = palette->attribute_written;
    if (!palette->ready) return;
    for (i = 0; i < 16; ++i) {
        uint8_t index = palette->attribute[i] & 63u;
        if (palette->profile == SIM_NATIVE_VIDEO_EGA_PROFILE_0) {
            /* Same six-bit EGA RGB mapping as render/palette.c. */
            palette->presentation.rgb[i][0] =
                (uint8_t)(((index & 4u) ? 170u : 0u) + ((index & 32u) ? 85u : 0u));
            palette->presentation.rgb[i][1] =
                (uint8_t)(((index & 2u) ? 170u : 0u) + ((index & 16u) ? 85u : 0u));
            palette->presentation.rgb[i][2] =
                (uint8_t)(((index & 1u) ? 170u : 0u) + ((index & 8u) ? 85u : 0u));
        } else {
            unsigned channel;
            if (!palette->dac_written[index]) {
                palette->ready = 0;
                continue;
            }
            for (channel = 0; channel < 3; ++channel)
                /* Match VGA's six-to-eight-bit DAC expansion used by the
                 * DOS scanout: replicate the two high bits into the low bits. */
                palette->presentation.rgb[i][channel] =
                    (uint8_t)((palette->dac6[index][channel] << 2) |
                              (palette->dac6[index][channel] >> 4));
        }
    }
}

static int attribute_write(void *context, const uint8_t bytes[17])
{
    SimSdlPaletteHost *palette = context;
    if (palette == NULL || bytes == NULL) return 0;
    memcpy(palette->attribute, bytes, 17);
    palette->attribute_written = 1;
    project(palette);
    return 1;
}

static int dac_write(void *context, uint16_t first, uint16_t count,
                     const uint8_t *bytes)
{
    SimSdlPaletteHost *palette = context;
    unsigned i;
    if (palette == NULL || bytes == NULL || first > 256u || count > 256u - first)
        return 0;
    for (i = 0; i < count; ++i) {
        unsigned channel;
        for (channel = 0; channel < 3; ++channel)
            palette->dac6[first + i][channel] = bytes[i * 3u + channel] & 63u;
        palette->dac_written[first + i] = 1;
    }
    project(palette);
    return 1;
}

int sim_sdl_palette_init(SimSdlPaletteHost *palette, SimNativeVideoProfile profile)
{
    if (palette == NULL || (profile != SIM_NATIVE_VIDEO_EGA_PROFILE_0 &&
                           profile != SIM_NATIVE_VIDEO_VGA_PROFILE_8)) return 0;
    memset(palette, 0, sizeof(*palette));
    palette->profile = profile;
    return 1;
}

int sim_sdl_palette_bind(SimSdlPaletteHost *palette)
{
    SimGraphicsPaletteServices services = {palette, attribute_write, dac_write};
    if (palette == NULL || (palette->profile != SIM_NATIVE_VIDEO_EGA_PROFILE_0 &&
                           palette->profile != SIM_NATIVE_VIDEO_VGA_PROFILE_8)) return 0;
    return sim_graphics_source_palette_bind(&services) == SIM_GRAPHICS_OK;
}

const HostPalette *sim_sdl_palette_view(const SimSdlPaletteHost *palette)
{
    return palette != NULL && palette->ready ? &palette->presentation : NULL;
}
