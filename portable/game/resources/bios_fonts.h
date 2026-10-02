#ifndef SIMANT_PORTABLE_GAME_RESOURCES_BIOS_FONTS_H
#define SIMANT_PORTABLE_GAME_RESOURCES_BIOS_FONTS_H

#include "../../ui_model/windows/render.h"

typedef enum PortableBiosFontsStatus {
    PORTABLE_BIOS_FONTS_OK = 0,
    PORTABLE_BIOS_FONTS_INVALID_ARGUMENT,
    PORTABLE_BIOS_FONTS_IO_ERROR,
    PORTABLE_BIOS_FONTS_SIZE_MISMATCH,
    PORTABLE_BIOS_FONTS_HASH_MISMATCH,
    PORTABLE_BIOS_FONTS_PROVIDER_ERROR
} PortableBiosFontsStatus;

/* Owns generated reference font bytes and the identity string borrowed by its
 * provider. This is a host presentation reference, not an original BIOS ROM. */
typedef struct PortableBiosFonts {
    uint8_t *font_8x8;
    size_t font_8x8_size;
    uint8_t *font_8x14;
    size_t font_8x14_size;
    char provider_id[96];
    PortableBiosFontProvider provider;
    char error[192];
} PortableBiosFonts;

/* Call once before first load/free, or initialize the structure with {0}. */
void portable_bios_fonts_init(PortableBiosFonts *fonts);
/* directory may be NULL, selecting build/bios-reference/dosbox-staging-v0.83.0.
 * The loader accepts only the pinned manifest and the exact extracted tables. */
PortableBiosFontsStatus portable_bios_fonts_load(PortableBiosFonts *fonts,
                                                 const char *directory);
void portable_bios_fonts_free(PortableBiosFonts *fonts);
const char *portable_bios_fonts_error(const PortableBiosFonts *fonts);
const char *portable_bios_fonts_status_string(PortableBiosFontsStatus status);

#endif
