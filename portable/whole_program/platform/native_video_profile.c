#include "native_video_profile.h"
#include "graphics_bitmap_source.h"

#include <stdlib.h>

typedef struct SimNativeVideoBinding {
    SimGraphicsDriver *graphics;
    SimNativeVideoStatus status;
    uint8_t bound;
    uint8_t source_abi_bound;
    uint8_t clip_bound;
} SimNativeVideoBinding;

static SimNativeVideoBinding s_binding;
static SimNativeVideoInstallServices s_install_services;
static SimNativeVideoUninstallServices s_uninstall_services;
static void *s_services_context;
static uint8_t s_services_installed;

SimNativeVideoStatus sim_native_video_set_mode_services(
    SimNativeVideoInstallServices install, SimNativeVideoUninstallServices uninstall,
    void *context)
{
    if (s_services_installed || (install == NULL) != (uninstall == NULL))
        return SIM_NATIVE_VIDEO_INVALID_ARGUMENT;
    s_install_services = install;
    s_uninstall_services = uninstall;
    s_services_context = context;
    return SIM_NATIVE_VIDEO_OK;
}

static void uninstall_services(void)
{
    if (s_services_installed) {
        s_uninstall_services(s_services_context);
        s_services_installed = 0;
    }
}

SimNativeVideoStatus sim_native_video_startup_bind(SimGraphicsDriver *graphics)
{
    uninstall_services();
    s_binding.bound = 0;
    s_binding.graphics = NULL;
    s_binding.source_abi_bound = 0;
    s_binding.clip_bound = 0;
    s_binding.status = SIM_NATIVE_VIDEO_NOT_BOUND;

    if (graphics == NULL || graphics->pixel_storage == NULL ||
        graphics->bios_8x14_source == NULL || graphics->bios_8x14_source_size < 256u * 14u)
        return s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY;
    if (sim_graphics_source_clip_bind(graphics) != SIM_GRAPHICS_OK)
        return s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY;

    s_binding.graphics = graphics;
    s_binding.clip_bound = 1;
    s_binding.status = SIM_NATIVE_VIDEO_OK;
    s_binding.bound = 1;
    return s_binding.status;
}

void sim_native_video_startup_unbind(void)
{
    uninstall_services();
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
    (void)require_binding();
    /* The virtual adapter can provide VGA. f_205F uses this descriptor only
     * when canonical ReadConfig/argv leave g_5A97 in autodetect mode. A
     * configured or command-line source mode remains authoritative. */
    return (int16_t)0x0305;
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
    uninstall_services();
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
    SimNativeVideoProfile profile;
    SimGraphicsStatus graphics_status;
    if (mode == 0x10)
        profile = SIM_NATIVE_VIDEO_EGA_PROFILE_0;
    else if (mode == 0x12)
        profile = SIM_NATIVE_VIDEO_VGA_PROFILE_8;
    else {
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
    if (s_install_services != NULL) {
        if (!s_install_services(s_services_context, binding->graphics, profile)) {
            s_binding.status = SIM_NATIVE_VIDEO_GRAPHICS_FAILURE;
            abort();
        }
        s_services_installed = 1;
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
