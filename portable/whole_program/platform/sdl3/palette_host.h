#ifndef SIMANT_WHOLE_SDL3_PALETTE_HOST_H
#define SIMANT_WHOLE_SDL3_PALETTE_HOST_H

#include "../graphics_entry_source.h"
#include "../native_video_profile.h"
#include "portable/platform/host.h"

/* One presentation palette. The indexed framebuffer still belongs to the
 * graphics driver. Source attribute/DAC writes update this borrowed projection;
 * mode 12h starts with captured BIOS defaults in slots 16..255: RGB6 table
 * values in 16..63 and zero values in the remaining slots. */
typedef struct SimSdlPaletteHost {
    HostPalette presentation;
    uint8_t attribute[17];
    uint8_t dac6[256][3];
    uint8_t dac_written[256];
    SimNativeVideoProfile profile;
    uint8_t attribute_written;
    uint8_t ready;
} SimSdlPaletteHost;

int sim_sdl_palette_init(SimSdlPaletteHost *palette, SimNativeVideoProfile profile);
int sim_sdl_palette_bind(SimSdlPaletteHost *palette);
const HostPalette *sim_sdl_palette_view(const SimSdlPaletteHost *palette);

#endif
