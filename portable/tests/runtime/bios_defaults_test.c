#include "portable/whole_program/platform/sdl3/palette_host.h"

#include <stdio.h>
#include <string.h>

SimGraphicsStatus sim_graphics_source_palette_bind(
    const SimGraphicsPaletteServices *services)
{
    (void)services;
    return SIM_GRAPHICS_OK;
}

static int check_palette(const char *path)
{
    uint8_t expected[48u * 3u];
    SimSdlPaletteHost palette;
    FILE *file = fopen(path, "rb");
    unsigned i;
    if (file == NULL) return 2;
    {
        size_t read_size = fread(expected, 1, sizeof(expected), file);
        int has_extra = fgetc(file) != EOF;
        int close_status = fclose(file);
        if (read_size != sizeof(expected) || has_extra || close_status != 0)
            return 2;
    }
    if (!sim_sdl_palette_init(&palette, SIM_NATIVE_VIDEO_VGA_PROFILE_8))
        return 2;
    for (i = 0; i < 256u; ++i) {
        unsigned channel;
        int should_be_known = i >= 16u;
        if (palette.dac_written[i] != (uint8_t)should_be_known) {
            fprintf(stderr, "DAC validity mismatch at slot %u\n", i);
            return 1;
        }
        for (channel = 0; channel < 3u; ++channel) {
            uint8_t value = 0;
            if (i >= 16u && i < 64u)
                value = expected[(i - 16u) * 3u + channel];
            if (palette.dac6[i][channel] != value) {
                fprintf(stderr, "DAC RGB6 mismatch at slot %u channel %u\n",
                        i, channel);
                return 1;
            }
        }
    }
    if (!sim_sdl_palette_init(&palette, SIM_NATIVE_VIDEO_EGA_PROFILE_0))
        return 2;
    for (i = 0; i < 256u; ++i) {
        if (palette.dac_written[i] != 0 || palette.dac6[i][0] != 0 ||
            palette.dac6[i][1] != 0 || palette.dac6[i][2] != 0) {
            fprintf(stderr, "mode-12h DAC defaults leaked into EGA slot %u\n", i);
            return 1;
        }
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    return check_palette(argv[1]);
}
