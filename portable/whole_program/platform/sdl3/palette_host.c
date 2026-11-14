#include "palette_host.h"

#include <string.h>

/* DOSBox-X v2026.08.31 US BIOS mode 12h leaves DAC slots 16..63 at these
 * six-bit RGB values after the game's palette setup writes slots 0..15; the
 * captured slots 64..255 are zero. The latter are also initialized as known
 * entries so the native palette matches the DOS checkpoint's full DAC view.
 * Captured from the original DOS new-game-save v7 entry-1 screen checkpoint;
 * the byte table is pinned as mode-12-dac-defaults-16-63.bin. */
static const uint8_t mode_12_dac_defaults[48][3] = {
    {0x00u, 0x15u, 0x00u}, {0x00u, 0x15u, 0x2au}, {0x00u, 0x3fu, 0x00u}, {0x00u, 0x3fu, 0x2au},
    {0x2au, 0x15u, 0x00u}, {0x2au, 0x15u, 0x2au}, {0x2au, 0x3fu, 0x00u}, {0x2au, 0x3fu, 0x2au},
    {0x00u, 0x15u, 0x15u}, {0x00u, 0x15u, 0x3fu}, {0x00u, 0x3fu, 0x15u}, {0x00u, 0x3fu, 0x3fu},
    {0x2au, 0x15u, 0x15u}, {0x2au, 0x15u, 0x3fu}, {0x2au, 0x3fu, 0x15u}, {0x2au, 0x3fu, 0x3fu},
    {0x15u, 0x00u, 0x00u}, {0x15u, 0x00u, 0x2au}, {0x15u, 0x2au, 0x00u}, {0x15u, 0x2au, 0x2au},
    {0x3fu, 0x00u, 0x00u}, {0x3fu, 0x00u, 0x2au}, {0x3fu, 0x2au, 0x00u}, {0x3fu, 0x2au, 0x2au},
    {0x15u, 0x00u, 0x15u}, {0x15u, 0x00u, 0x3fu}, {0x15u, 0x2au, 0x15u}, {0x15u, 0x2au, 0x3fu},
    {0x3fu, 0x00u, 0x15u}, {0x3fu, 0x00u, 0x3fu}, {0x3fu, 0x2au, 0x15u}, {0x3fu, 0x2au, 0x3fu},
    {0x15u, 0x15u, 0x00u}, {0x15u, 0x15u, 0x2au}, {0x15u, 0x3fu, 0x00u}, {0x15u, 0x3fu, 0x2au},
    {0x3fu, 0x15u, 0x00u}, {0x3fu, 0x15u, 0x2au}, {0x3fu, 0x3fu, 0x00u}, {0x3fu, 0x3fu, 0x2au},
    {0x15u, 0x15u, 0x15u}, {0x15u, 0x15u, 0x3fu}, {0x15u, 0x3fu, 0x15u}, {0x15u, 0x3fu, 0x3fu},
    {0x3fu, 0x15u, 0x15u}, {0x3fu, 0x15u, 0x3fu}, {0x3fu, 0x3fu, 0x15u}, {0x3fu, 0x3fu, 0x3fu}
};

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
    unsigned i;
    if (palette == NULL || (profile != SIM_NATIVE_VIDEO_EGA_PROFILE_0 &&
                           profile != SIM_NATIVE_VIDEO_VGA_PROFILE_8)) return 0;
    memset(palette, 0, sizeof(*palette));
    palette->profile = profile;
    if (profile == SIM_NATIVE_VIDEO_VGA_PROFILE_8) {
        for (i = 16u; i < 256u; ++i) {
            if (i < 64u)
                memcpy(palette->dac6[i], mode_12_dac_defaults[i - 16u], 3u);
            palette->dac_written[i] = 1;
        }
    }
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
