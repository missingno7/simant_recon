#ifndef SIMANT_PORTABLE_RESOURCES_FONTS_H
#define SIMANT_PORTABLE_RESOURCES_FONTS_H

#include "../../render/font.h"

/* Original font IDs 2..5 map to FONT1..FONT4. Owns decoded font storage. */
typedef struct PortableFontSet {
    PortableFont fonts[4];
    uint8_t loaded;
    char error[192];
} PortableFontSet;

void portable_fonts_init(PortableFontSet *set);
void portable_fonts_destroy(PortableFontSet *set);
PortableRenderStatus portable_fonts_load(PortableFontSet *set, const char *asset_dir);
const PortableFont *portable_fonts_get(const PortableFontSet *set, unsigned source_id);

#endif
