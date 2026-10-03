/* Native borrowed-font view contract, shared with the selected renderer's
 * portable_bios_font_provider_init. This lane does not link that renderer. */
#include "../../ui_model/windows/render.h"

PortableRenderStatus portable_bios_font_provider_init(
    PortableBiosFontProvider *provider,
    const uint8_t *font_8x8, size_t font_8x8_size,
    const uint8_t *font_8x14, size_t font_8x14_size,
    const char *provider_id)
{
    if (provider == NULL || provider_id == NULL || provider_id[0] == '\0')
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if (font_8x8 == NULL || font_8x8_size != 256u * 8u ||
        font_8x14 == NULL || font_8x14_size != 256u * 14u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    provider->font_8x8 = (PortableBiosFontBitmap){
        font_8x8, font_8x8_size, 8, 8, provider_id};
    provider->font_8x14 = (PortableBiosFontBitmap){
        font_8x14, font_8x14_size, 8, 14, provider_id};
    return PORTABLE_RENDER_OK;
}
