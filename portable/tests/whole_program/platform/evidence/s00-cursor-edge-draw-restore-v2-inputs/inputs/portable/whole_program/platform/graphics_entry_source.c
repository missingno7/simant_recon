#include "graphics_entry_source.h"

#include "graphics_bitmap_source.h"

#include <string.h>

SimGraphicsFontCallback g_915C;
SimGraphicsFontCallback g_9160;
SimGraphicsFontCallback g_9164;
SimGraphicsFontCallback g_9168;
SimGraphicsLogicOperationCallback g_9184;

static SimGraphicsPaletteServices s_palette_services;
static uint8_t s_palette_bound;

static void set_operation_low_byte(uint8_t value)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    uint16_t bits;
    memcpy(&bits, &graphics->g_3DD2, sizeof(bits));
    bits = (uint16_t)((bits & 0xff00u) | value);
    memcpy(&graphics->g_3DD2, &bits, sizeof(bits));
    graphics->last_status = SIM_GRAPHICS_OK;
}

static void source_g915c_or(void) { set_operation_low_byte(0x10); }
static void source_g9160_xor(void) { set_operation_low_byte(0x18); }
static void source_g9164_and(void) { set_operation_low_byte(0x08); }
static void source_g9168_replace(void) { set_operation_low_byte(0x00); }
static void source_g9184_restore(int16_t mode)
{
    set_operation_low_byte((uint8_t)mode);
}

SimGraphicsStatus sim_graphics_source_entry_bind(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics != sim_graphics_source_owner() ||
        graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    g_915C = source_g915c_or;
    g_9160 = source_g9160_xor;
    g_9164 = source_g9164_and;
    g_9168 = source_g9168_replace;
    g_9184 = source_g9184_restore;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_entry_unbind(void)
{
    g_915C = NULL;
    g_9160 = NULL;
    g_9164 = NULL;
    g_9168 = NULL;
    g_9184 = NULL;
}

SimGraphicsStatus sim_graphics_source_palette_bind(
    const SimGraphicsPaletteServices *services)
{
    if (services == NULL || services->set_attribute_palette == NULL ||
        services->set_dac_range == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s_palette_services = *services;
    s_palette_bound = 1;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_palette_unbind(void)
{
    memset(&s_palette_services, 0, sizeof(s_palette_services));
    s_palette_bound = 0;
}

static uint16_t little_u16(const uint8_t *bytes)
{
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8));
}

static void bitmap_call(SimGraphicsBitmapCallback callback, int16_t x,
                        int16_t y, char *image)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    if (image == NULL || callback == NULL) {
        graphics->last_status = image == NULL ? SIM_GRAPHICS_INVALID_ARGUMENT :
                                                 SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    callback(x, y, image + 4, (int16_t)little_u16((const uint8_t *)image),
             (int16_t)little_u16((const uint8_t *)image + 2));
}

void f_1B4E_003B(int16_t x, int16_t y, char *image)
{
    bitmap_call(g_914C, x, y, image);
}

void f_1B4E_005E(int16_t x, int16_t y, char *image)
{
    bitmap_call(g_9154, x, y, image);
}

void f_1B4E_0110(int16_t x, int16_t y, int16_t character)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    graphics->last_status = sim_graphics_f_1B4E_0110(graphics, x, y, character);
}

void f_1B4E_01A1(char *palette17, int16_t count)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    (void)count; /* Original INT 10h AX=1002h ignores this C-side word. */
    if (!s_palette_bound || palette17 == NULL ||
        !s_palette_services.set_attribute_palette(s_palette_services.context,
                                                   (const uint8_t *)palette17)) {
        graphics->last_status = palette17 == NULL ? SIM_GRAPHICS_INVALID_ARGUMENT :
                                                    SIM_GRAPHICS_UNSUPPORTED_MODE;
        return;
    }
    graphics->last_status = SIM_GRAPHICS_OK;
}

void f_1B4E_01AE(char *rgb_palette, int16_t count)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    uint16_t remaining;
    uint16_t first = 0;
    const uint8_t *source = (const uint8_t *)rgb_palette;
    if (!s_palette_bound || rgb_palette == NULL || count < 0) {
        graphics->last_status = (!s_palette_bound || count < 0) ?
            SIM_GRAPHICS_UNSUPPORTED_MODE : SIM_GRAPHICS_INVALID_ARGUMENT;
        return;
    }
    remaining = count == 0 ? 256u : (uint16_t)count;
    if (remaining == 16u) {
        uint8_t defaults[17];
        unsigned i;
        for (i = 0; i < 16; ++i)
            defaults[i] = (uint8_t)i;
        defaults[16] = 0;
        if (!s_palette_services.set_attribute_palette(
                s_palette_services.context, defaults)) {
            graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
            return;
        }
    }
    while (remaining != 0) {
        uint8_t converted[16u * 3u];
        uint16_t chunk = remaining > 16u ? 16u : remaining;
        uint16_t i;
        for (i = 0; i < chunk * 3u; ++i)
            converted[i] = (uint8_t)(source[i] >> 2);
        if (!s_palette_services.set_dac_range(s_palette_services.context,
                                               first, chunk, converted)) {
            graphics->last_status = SIM_GRAPHICS_UNSUPPORTED_MODE;
            return;
        }
        source += (size_t)chunk * 3u;
        remaining = (uint16_t)(remaining - chunk);
        first = (uint16_t)(first + chunk);
    }
    graphics->last_status = SIM_GRAPHICS_OK;
}
