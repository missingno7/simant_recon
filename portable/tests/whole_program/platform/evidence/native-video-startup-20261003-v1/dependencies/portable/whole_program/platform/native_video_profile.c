#include "native_video_profile.h"
#include "graphics_bitmap_source.h"

#include <stdlib.h>

typedef struct SimNativeVideoBinding {
    SimNativeVideoProfileInfo info;
    SimGraphicsDriver *graphics;
    SimNativeVideoStatus status;
    uint8_t bound;
    uint8_t source_abi_bound;
    uint8_t clip_bound;
} SimNativeVideoBinding;

static SimNativeVideoBinding s_binding;

SimNativeVideoStatus sim_native_video_profile_info(int16_t source_profile,
                                                    SimNativeVideoProfileInfo *out)
{
    SimNativeVideoProfileInfo info;
    if (out == NULL)
        return SIM_NATIVE_VIDEO_INVALID_ARGUMENT;
    if (source_profile == SIM_NATIVE_VIDEO_EGA_PROFILE_0) {
        info.profile = SIM_NATIVE_VIDEO_EGA_PROFILE_0;
        /* Adapter 3, display 3 makes the source switch select profile 0. */
        info.source_bios_descriptor = 0x0303;
        info.source_mode = 0x10;
        info.database_prefix = "hcega";
    } else if (source_profile == SIM_NATIVE_VIDEO_VGA_PROFILE_8) {
        info.profile = SIM_NATIVE_VIDEO_VGA_PROFILE_8;
        /* Adapter 5, display 3 makes the source switch select profile 8. */
        info.source_bios_descriptor = 0x0305;
        info.source_mode = 0x12;
        info.database_prefix = "hcega";
    } else {
        return SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE;
    }
    *out = info;
    return SIM_NATIVE_VIDEO_OK;
}

SimNativeVideoStatus sim_native_video_startup_bind(int16_t source_profile,
                                                    SimGraphicsDriver *graphics)
{
    SimNativeVideoProfileInfo info;
    SimNativeVideoStatus status;
    s_binding.bound = 0;
    s_binding.graphics = NULL;
    s_binding.source_abi_bound = 0;
    s_binding.clip_bound = 0;
    s_binding.status = SIM_NATIVE_VIDEO_NOT_BOUND;

    status = sim_native_video_profile_info(source_profile, &info);
    if (status != SIM_NATIVE_VIDEO_OK)
        return s_binding.status = status;
    if (graphics == NULL || graphics->pixel_storage == NULL ||
        graphics->bios_8x14_source == NULL || graphics->bios_8x14_source_size < 256u * 14u)
        return s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY;
    if (sim_graphics_source_clip_bind(graphics) != SIM_GRAPHICS_OK)
        return s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY;

    s_binding.info = info;
    s_binding.graphics = graphics;
    s_binding.clip_bound = 1;
    s_binding.status = SIM_NATIVE_VIDEO_OK;
    s_binding.bound = 1;
    return s_binding.status;
}

void sim_native_video_startup_unbind(void)
{
    if (s_binding.source_abi_bound) {
        sim_graphics_source_bitmap_unbind();
        (void)sim_graphics_bind_source_abi(NULL, NULL);
    }
    if (s_binding.clip_bound)
        sim_graphics_source_clip_unbind();
    s_binding.bound = 0;
    s_binding.source_abi_bound = 0;
    s_binding.clip_bound = 0;
    s_binding.graphics = NULL;
    s_binding.status = SIM_NATIVE_VIDEO_NOT_BOUND;
}

SimNativeVideoStatus sim_native_video_startup_status(void)
{
    return s_binding.status;
}

static SimNativeVideoBinding *require_binding(void)
{
    if (!s_binding.bound || s_binding.graphics == NULL ||
        !s_binding.clip_bound) {
        s_binding.status = SIM_NATIVE_VIDEO_NOT_BOUND;
        abort();
    }
    return &s_binding;
}

int16_t o21_39C7_0000(void)
{
    return (int16_t)require_binding()->info.source_bios_descriptor;
}

int16_t o21_39C7_016D(void)
{
    /* A selected supported descriptor cannot reach the Tandy BIOS query.
     * Returning false here would invent a hardware observation. */
    (void)require_binding();
    s_binding.status = SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE;
    abort();
}

void f_1B4E_0025(void)
{
    (void)require_binding();
    /* The source resets its 25-entry table to the empty entry. The native
     * graphics owner exposes the same reset operation by unbinding its typed
     * source callback table; the selected S00 adapter binds supported entries
     * again immediately before selecting the mode. */
    if (sim_graphics_bind_source_abi(NULL, NULL) != SIM_GRAPHICS_OK) {
        s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_FAILURE;
        abort();
    }
    sim_graphics_source_bitmap_unbind();
    s_binding.source_abi_bound = 0;
}

static void install_source_mode(int16_t mode)
{
    SimNativeVideoBinding *binding = require_binding();
    SimGraphicsStatus graphics_status;
    if (binding->info.source_mode != mode) {
        s_binding.status = SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE;
        abort();
    }
    if (sim_graphics_bind_source_abi(binding->graphics,
                                     sim_graphics_source_clip_slot()) != SIM_GRAPHICS_OK ||
        sim_graphics_source_bitmap_bind(binding->graphics) != SIM_GRAPHICS_OK) {
        s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_FAILURE;
        abort();
    }
    s_binding.source_abi_bound = 1;
    f_1B4E_015B(mode);
    graphics_status = sim_graphics_source_last_status();
    if (graphics_status != SIM_GRAPHICS_OK) {
        s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_FAILURE;
        abort();
    }
    s_binding.status = SIM_NATIVE_VIDEO_OK;
}

void o00_31AD_2AB4(void)
{
    install_source_mode(0x10);
}

void o00_31AD_2AE5(void)
{
    install_source_mode(0x12);
}
